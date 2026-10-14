import json, os, unicodedata, uuid, csv, io, shutil, mimetypes
from functools import wraps
from io import BytesIO
import psycopg
from psycopg.types.json import Jsonb
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response, send_from_directory, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)
SECRET_KEY = os.environ.get("SECRET_KEY", "").strip()
if len(SECRET_KEY) < 32:
    raise RuntimeError("Configure SECRET_KEY no Render com uma chave aleatória de pelo menos 32 caracteres.")
app.secret_key = SECRET_KEY
app.config["MAX_CONTENT_LENGTH"] = 4 * 1024 * 1024
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "").strip()
if not ADMIN_PASSWORD or ADMIN_PASSWORD == "admin123":
    raise RuntimeError("Configure uma ADMIN_PASSWORD personalizada no Render.")
DATA_DIR = os.environ.get("DATA_DIR", os.path.dirname(__file__))
DATA_FILE = os.path.join(DATA_DIR, "votos.json")
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()
UPLOAD_FOLDER = os.path.join(DATA_DIR, "uploads")
LEGACY_DATA_FILE = os.path.join(os.path.dirname(__file__), "votos.json")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

DEFAULT = {
    "aberta": True,
    "chapas": [],
    "candidatos": [],
    "votos": {},
    "nomes_votantes": [],
    "votos_legados": {}
}

def ensure_database():
    if not DATABASE_URL:
        return
    with psycopg.connect(DATABASE_URL, sslmode="require", connect_timeout=10) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vota_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                data JSONB NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS vota_uploads (
                filename TEXT PRIMARY KEY,
                content BYTEA NOT NULL,
                mimetype TEXT NOT NULL
            )
        """)

def save_data(data):
    if DATABASE_URL:
        ensure_database()
        with psycopg.connect(DATABASE_URL, sslmode="require", connect_timeout=10) as conn:
            conn.execute(
                "INSERT INTO vota_state (id, data) VALUES (1, %s) "
                "ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data",
                (Jsonb(data),)
            )
        return
    os.makedirs(DATA_DIR, exist_ok=True)
    temp = DATA_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp, DATA_FILE)

def migrate_old_schema(previous):
    if "candidatos" in previous:
        return previous
    chapas = []
    for gremio in previous.get("gremios", []):
        logo = gremio.get("foto", "")
        if logo:
            old_path = os.path.join(os.path.dirname(__file__), "static", logo)
            new_path = os.path.join(DATA_DIR, logo)
            if os.path.isfile(old_path) and os.path.abspath(old_path) != os.path.abspath(new_path):
                os.makedirs(os.path.dirname(new_path), exist_ok=True)
                if not os.path.exists(new_path):
                    shutil.copy2(old_path, new_path)
        chapas.append({
            "id": gremio["id"], "nome": gremio["nome"],
            "descricao": gremio.get("descricao", ""),
            "logo": logo, "emoji": gremio.get("emoji", "🎓")
        })
    return {
        "aberta": previous.get("aberta", True),
        "chapas": chapas, "candidatos": [],
        "votos": {}, "nomes_votantes": previous.get("nomes_votantes", []),
        "votos_legados": previous.get("votos", {})
    }

def load_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if DATABASE_URL:
        ensure_database()
        with psycopg.connect(DATABASE_URL, sslmode="require", connect_timeout=10) as conn:
            row = conn.execute("SELECT data FROM vota_state WHERE id = 1").fetchone()
        if row:
            data = row[0]
        else:
            source = DATA_FILE
            if not os.path.exists(source) and os.path.abspath(DATA_FILE) != os.path.abspath(LEGACY_DATA_FILE):
                source = LEGACY_DATA_FILE
            if os.path.exists(source):
                with open(source, "r", encoding="utf-8") as f:
                    data = json.load(f)
                data = migrate_old_schema(data)
                import_local_uploads(data)
            else:
                data = dict(DEFAULT)
            save_data(data)
    else:
        if not os.path.exists(DATA_FILE) and os.path.abspath(DATA_FILE) != os.path.abspath(LEGACY_DATA_FILE) and os.path.exists(LEGACY_DATA_FILE):
            with open(LEGACY_DATA_FILE, "r", encoding="utf-8") as old:
                previous = json.load(old)
            save_data(migrate_old_schema(previous))
        if not os.path.exists(DATA_FILE):
            save_data(DEFAULT)
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if "candidatos" not in data:
            data = migrate_old_schema(data)
            save_data(data)
    data.setdefault("chapas", [])
    data.setdefault("candidatos", [])
    data.setdefault("votos", {})
    data.setdefault("nomes_votantes", [])
    data.setdefault("votos_legados", {})
    data.setdefault("aberta", True)
    return data

def import_local_uploads(data):
    if not DATABASE_URL:
        return
    paths = [c.get("foto", "") for c in data.get("candidatos", [])]
    paths += [ch.get("logo", "") for ch in data.get("chapas", [])]
    for relpath in paths:
        if not relpath or not relpath.startswith("uploads/"):
            continue
        filename = os.path.basename(relpath)
        local_path = os.path.join(DATA_DIR, relpath)
        if not os.path.isfile(local_path):
            continue
        with open(local_path, "rb") as f:
            content = f.read()
        mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        with psycopg.connect(DATABASE_URL, sslmode="require", connect_timeout=10) as conn:
            conn.execute(
                "INSERT INTO vota_uploads (filename, content, mimetype) VALUES (%s, %s, %s) "
                "ON CONFLICT (filename) DO NOTHING",
                (filename, content, mimetype)
            )

def norm_name(name):
    name = unicodedata.normalize("NFKD", name.strip().casefold())
    return " ".join("".join(c for c in name if not unicodedata.combining(c)).split())

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapper

def save_upload(file, prefix):
    if not file or not file.filename:
        return ""
    original = secure_filename(file.filename)
    ext = original.rsplit(".", 1)[-1].lower() if "." in original else ""
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError("A imagem deve estar no formato PNG, JPG ou WEBP.")
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    filename = f"{prefix}_{uuid.uuid4().hex}.{ext}"
    if DATABASE_URL:
        content = file.read()
        mimetype = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        ensure_database()
        with psycopg.connect(DATABASE_URL, sslmode="require", connect_timeout=10) as conn:
            conn.execute(
                "INSERT INTO vota_uploads (filename, content, mimetype) VALUES (%s, %s, %s)",
                (filename, content, mimetype)
            )
    else:
        file.save(os.path.join(UPLOAD_FOLDER, filename))
    return f"uploads/{filename}"

def delete_upload(relpath):
    if not relpath:
        return
    filename = os.path.basename(relpath)
    if DATABASE_URL and relpath.startswith("uploads/"):
        ensure_database()
        with psycopg.connect(DATABASE_URL, sslmode="require", connect_timeout=10) as conn:
            conn.execute("DELETE FROM vota_uploads WHERE filename = %s", (filename,))
        return
    path = os.path.join(DATA_DIR, relpath)
    if os.path.isfile(path):
        os.remove(path)

@app.get("/uploads/<path:filename>")
def uploaded_file(filename):
    if DATABASE_URL:
        ensure_database()
        with psycopg.connect(DATABASE_URL, sslmode="require", connect_timeout=10) as conn:
            row = conn.execute(
                "SELECT content, mimetype FROM vota_uploads WHERE filename = %s",
                (os.path.basename(filename),)
            ).fetchone()
        if row:
            return send_file(BytesIO(bytes(row[0])), mimetype=row[1], download_name=os.path.basename(filename))
        return "Imagem não encontrada", 404
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route("/")
def index():
    data = load_data()
    votos = data["votos"]
    candidatos = []
    for c in data["candidatos"]:
        chapa = next((x for x in data["chapas"] if x["id"] == c["chapa_id"]), None)
        candidatos.append({**c, "chapa": chapa, "votos": votos.get(str(c["id"]), 0)})

    cargos = []
    cargo_keys = set()
    for candidato in candidatos:
        cargo_nome = (candidato.get("cargo") or "").strip()
        cargo_key = cargo_nome.casefold()
        if not cargo_nome:
            continue
        if cargo_key not in cargo_keys:
            cargo_keys.add(cargo_key)
            cargos.append({"nome": cargo_nome, "candidatos": []})
        grupo = next(g for g in cargos if g["nome"].casefold() == cargo_key)
        grupo["candidatos"].append(candidato)
    return render_template("index.html", data=data, candidatos=candidatos, cargos=cargos)

@app.post("/votar")
def votar():
    data = load_data()
    eleitor = request.form.get("eleitor", "").strip()

    cargos = []
    cargo_keys = set()
    for candidato in data["candidatos"]:
        cargo_nome = (candidato.get("cargo") or "").strip()
        cargo_key = cargo_nome.casefold()
        if cargo_nome and cargo_key not in cargo_keys:
            cargo_keys.add(cargo_key)
            cargos.append(cargo_nome)

    if not data["aberta"]:
        flash("A votação está encerrada.")
    elif len(eleitor) < 2:
        flash("Informe o nome do eleitor.")
    elif norm_name(eleitor) in data["nomes_votantes"]:
        flash("Este nome já foi utilizado para votar. Peça ajuda ao responsável pela eleição.")
    elif not cargos:
        flash("Não há cargos com candidatos cadastrados.")
    else:
        escolhidos = []
        erro = None
        for indice, cargo_nome in enumerate(cargos):
            candidato_id = request.form.get(f"cargo_{indice}", "").strip()
            candidato = next(
                (c for c in data["candidatos"]
                 if str(c["id"]) == candidato_id
                 and (c.get("cargo") or "").strip().casefold() == cargo_nome.casefold()),
                None
            )
            if not candidato:
                erro = f"Selecione um candidato para o cargo: {cargo_nome}."
                break
            escolhidos.append(candidato)

        if erro:
            flash(erro)
        else:
            for candidato in escolhidos:
                key = str(candidato["id"])
                data["votos"][key] = data["votos"].get(key, 0) + 1
            data["nomes_votantes"].append(norm_name(eleitor))
            save_data(data)
            flash("Voto registrado para todos os cargos com sucesso!")
    return redirect(url_for("index"))

@app.route("/admin", methods=["GET", "POST"])
def admin_login():
    if session.get("admin"):
        return redirect(url_for("painel"))
    if request.method == "POST":
        if request.form.get("senha", "") == ADMIN_PASSWORD:
            session["admin"] = True
            return redirect(url_for("painel"))
        flash("Senha incorreta.")
    return render_template("login.html")

@app.route("/painel")
@admin_required
def painel():
    data = load_data()
    candidatos = []
    for c in data["candidatos"]:
        chapa = next((x for x in data["chapas"] if x["id"] == c["chapa_id"]), None)
        candidatos.append({**c, "chapa": chapa, "votos": data["votos"].get(str(c["id"]), 0)})
    total = sum(c["votos"] for c in candidatos)
    return render_template("painel.html", data=data, candidatos=candidatos,
                           total=total, chapas=data["chapas"])

@app.post("/admin/chapa")
@admin_required
def add_chapa():
    nome = request.form.get("nome", "").strip()
    descricao = request.form.get("descricao", "").strip()
    if not nome:
        flash("Informe o nome da chapa.")
        return redirect(url_for("painel"))
    data = load_data()
    try:
        logo = save_upload(request.files.get("logo"), "chapa")
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("painel"))
    next_id = max([x["id"] for x in data["chapas"]] or [0]) + 1
    data["chapas"].append({"id": next_id, "nome": nome[:70], "descricao": descricao[:180], "logo": logo, "emoji": "🎓"})
    save_data(data)
    flash("Chapa cadastrada com sucesso!")
    return redirect(url_for("painel"))

@app.post("/admin/candidato")
@admin_required
def add_candidato():
    numero = request.form.get("numero", "").strip()
    nome = request.form.get("nome", "").strip()
    try:
        chapa_id = int(request.form.get("chapa_id", ""))
    except ValueError:
        chapa_id = -1
    data = load_data()
    if not numero.isdigit() or not 1 <= len(numero) <= 6:
        flash("Use um número de candidato com 1 a 6 dígitos.")
        return redirect(url_for("painel"))
    if any(str(c["numero"]) == numero for c in data["candidatos"]):
        flash("Esse número já está cadastrado para outro candidato.")
        return redirect(url_for("painel"))
    if len(nome) < 2:
        flash("Informe o nome completo do candidato.")
        return redirect(url_for("painel"))
    if not any(x["id"] == chapa_id for x in data["chapas"]):
        flash("Cadastre ou selecione uma chapa válida.")
        return redirect(url_for("painel"))
    try:
        foto = save_upload(request.files.get("foto"), "candidato")
    except ValueError as e:
        flash(str(e))
        return redirect(url_for("painel"))
    next_id = max([c["id"] for c in data["candidatos"]] or [0]) + 1
    data["candidatos"].append({"id": next_id, "numero": numero, "nome": nome[:100], "cargo": request.form.get("cargo", "").strip()[:80], "chapa_id": chapa_id, "foto": foto})
    data["votos"][str(next_id)] = 0
    save_data(data)
    flash("Candidato cadastrado com sucesso!")
    return redirect(url_for("painel"))

@app.post("/admin/candidato/<int:candidato_id>/excluir")
@admin_required
def excluir_candidato(candidato_id):
    data = load_data()
    candidato = next((c for c in data["candidatos"] if c["id"] == candidato_id), None)
    if candidato is None:
        flash("Candidato não encontrado.")
    elif data["votos"].get(str(candidato_id), 0) > 0:
        flash("Não é possível excluir um candidato que já recebeu votos. Zere os votos primeiro.")
    else:
        data["candidatos"] = [c for c in data["candidatos"] if c["id"] != candidato_id]
        data["votos"].pop(str(candidato_id), None)
        delete_upload(candidato.get("foto", ""))
        save_data(data)
        flash("Candidato excluído.")
    return redirect(url_for("painel"))

@app.post("/admin/chapa/<int:chapa_id>/excluir")
@admin_required
def excluir_chapa(chapa_id):
    data = load_data()
    chapa = next((x for x in data["chapas"] if x["id"] == chapa_id), None)
    if chapa is None:
        flash("Chapa não encontrada.")
    elif any(c["chapa_id"] == chapa_id for c in data["candidatos"]):
        flash("Não é possível excluir uma chapa que tem candidatos cadastrados.")
    else:
        data["chapas"] = [x for x in data["chapas"] if x["id"] != chapa_id]
        delete_upload(chapa.get("logo", ""))
        save_data(data)
        flash("Chapa excluída.")
    return redirect(url_for("painel"))

@app.post("/admin/zerar-votos")
@admin_required
def zerar_votos():
    data = load_data()
    data["votos"] = {str(c["id"]): 0 for c in data["candidatos"]}
    data["nomes_votantes"] = []
    data["votos_legados"] = {}
    save_data(data)
    flash("Votos zerados. Os eleitores poderão votar novamente.")
    return redirect(url_for("painel"))

@app.post("/admin/estado")
@admin_required
def estado():
    data = load_data()
    data["aberta"] = request.form.get("aberta") == "sim"
    save_data(data)
    flash("Status da votação atualizado.")
    return redirect(url_for("painel"))

@app.get("/admin/exportar")
@admin_required
def exportar():
    data = load_data()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Número", "Candidato", "Cargo", "Chapa", "Votos"])
    for c in data["candidatos"]:
        chapa = next((x for x in data["chapas"] if x["id"] == c["chapa_id"]), None)
        writer.writerow([c["numero"], c["nome"], c.get("cargo", ""), chapa["nome"] if chapa else "", data["votos"].get(str(c["id"]), 0)])
    return Response("\ufeff" + output.getvalue(), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=resultados_candidatos.csv"})

@app.get("/sair")
def sair():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
