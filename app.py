import json, os, unicodedata
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, Response

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "troque-esta-chave-antes-de-usar")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")
DATA_FILE = os.path.join(os.path.dirname(__file__), "votos.json")

DEFAULT = {
    "aberta": True,
    "gremios": [
        {"id": 1, "nome": "Grêmio Renovação", "descricao": "Juntos por uma escola melhor.", "emoji": "🌱"},
        {"id": 2, "nome": "Grêmio União", "descricao": "Mais participação para todos.", "emoji": "🤝"},
        {"id": 3, "nome": "Grêmio Futuro", "descricao": "Novas ideias, novas conquistas.", "emoji": "🚀"}
    ],
    "votos": {},
    "nomes_votantes": []
}

def load_data():
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT)
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    temp = DATA_FILE + ".tmp"
    with open(temp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(temp, DATA_FILE)

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

@app.route("/")
def index():
    data = load_data()
    return render_template("index.html", data=data)

@app.post("/votar")
def votar():
    data = load_data()
    nome = request.form.get("nome", "").strip()
    try:
        gremio_id = int(request.form.get("gremio_id", ""))
    except ValueError:
        gremio_id = -1
    if not data["aberta"]:
        flash("A votação está encerrada.")
    elif len(nome) < 2:
        flash("Digite seu nome para continuar.")
    elif not any(g["id"] == gremio_id for g in data["gremios"]):
        flash("Selecione um grêmio válido.")
    elif norm_name(nome) in data["nomes_votantes"]:
        flash("Este nome já foi utilizado para votar. Peça ajuda ao responsável pela eleição.")
    else:
        data["nomes_votantes"].append(norm_name(nome))
        data["votos"][str(gremio_id)] = data["votos"].get(str(gremio_id), 0) + 1
        save_data(data)
        flash("Voto registrado com sucesso! Obrigado por participar.")
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
    gremios = [{**g, "votos": data["votos"].get(str(g["id"]), 0)} for g in data["gremios"]]
    return render_template("painel.html", data=data, gremios=gremios,
                           total=sum(g["votos"] for g in gremios))

@app.post("/admin/gremio")
@admin_required
def add_gremio():
    nome = request.form.get("nome", "").strip()
    descricao = request.form.get("descricao", "").strip()
    if nome:
        data = load_data()
        next_id = max([g["id"] for g in data["gremios"]] or [0]) + 1
        data["gremios"].append({"id": next_id, "nome": nome[:70],
                                "descricao": descricao[:180], "emoji": "🎓"})
        data["votos"][str(next_id)] = 0
        save_data(data)
        flash("Grêmio cadastrado.")
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
    linhas = ["Grêmio,Votos"]
    for g in data["gremios"]:
        linhas.append('"' + g["nome"].replace('"', '""') + '",' + str(data["votos"].get(str(g["id"]), 0)))
    return Response("\ufeff" + "\n".join(linhas), mimetype="text/csv",
                    headers={"Content-Disposition": "attachment; filename=resultados_gremio.csv"})

@app.get("/sair")
def sair():
    session.clear()
    return redirect(url_for("index"))

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
