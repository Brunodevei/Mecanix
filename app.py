# ola professor, aqui esta a modificacao 

from pathlib import Path
import os
import secrets
import sqlite3
from datetime import timedelta
from flask import Flask, g, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "mecanix.db"

app = Flask(__name__)
app.config["DATABASE"] = DATABASE_PATH
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30)
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = (
    os.environ.get("HTTPS_ONLY", "false").lower() == "true"
)


def get_database():
    if "database" not in g:
        g.database = sqlite3.connect(app.config["DATABASE"])
        g.database.row_factory = sqlite3.Row
        g.database.execute("PRAGMA foreign_keys = ON")
    return g.database


def close_database(exception=None):
    database = g.pop("database", None)
    if database is not None:
        database.close()


def initialize_database():
    database = sqlite3.connect(app.config["DATABASE"])
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    database.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
            perfil TEXT NOT NULL DEFAULT 'Gerente',
            ativo INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cpf TEXT UNIQUE,
            telefone TEXT,
            email TEXT,
            endereco TEXT,
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS veiculos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            placa TEXT NOT NULL UNIQUE,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano INTEGER,
            criado_em TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT ON UPDATE CASCADE
        );

        CREATE TABLE IF NOT EXISTS pecas_veiculo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            veiculo_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            custo REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos (id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS servicos_catalogo (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            custo_mao_de_obra REAL NOT NULL DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            veiculo_id INTEGER NOT NULL,
            problemas TEXT,
            descricao TEXT NOT NULL,
            custo_total REAL NOT NULL DEFAULT 0,
            preco_final REAL NOT NULL DEFAULT 0,
            margem_lucro REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Aberta',
            valor REAL NOT NULL DEFAULT 0,
            data_abertura TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data_conclusao TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes (id) ON DELETE RESTRICT ON UPDATE CASCADE,
            FOREIGN KEY (veiculo_id) REFERENCES veiculos (id) ON DELETE RESTRICT ON UPDATE CASCADE
        );
        """
    )

    cursor = database.cursor()
    cursor.execute("SELECT COUNT(*) AS total FROM usuarios")

    if cursor.fetchone()["total"] == 0:
        senha_inicial = os.environ.get("ADMIN_INITIAL_PASSWORD")

        if not senha_inicial:
            senha_inicial = secrets.token_urlsafe(16)
            print("\n===================================")
            print("CONTA INICIAL DO MECANIX")
            print("E-mail: admin@mecanix.com")
            print(f"Senha inicial: {senha_inicial}")
            print("Guarde essa senha em local seguro.")
            print("===================================\n")

        senha_adm = generate_password_hash(senha_inicial)

        cursor.execute(
            """
            INSERT INTO usuarios (nome, email, senha_hash, perfil, ativo)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("Administrador", "admin@mecanix.com", senha_adm, "Administrador", 1)
        )
        database.commit()

    database.close()


@app.teardown_appcontext
def teardown_database(exception=None):
    close_database(exception)


@app.route("/login", methods=["GET", "POST"])
def login():
    erro = None

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "").strip()
        database = get_database()

        usuario = database.execute(
            "SELECT * FROM usuarios WHERE email = ? AND ativo = 1",
            (email,)
        ).fetchone()

        if usuario and check_password_hash(usuario["senha_hash"], senha):
            session["usuario_id"] = usuario["id"]
            session["usuario_nome"] = usuario["nome"]
            session["usuario_perfil"] = usuario["perfil"]
            session.permanent = True
            return redirect(url_for("index"))
        else:
            erro = "E-mail ou senha incorretos, ou conta desativada."

    return render_template("login.html", erro=erro)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.before_request
def verificar_autenticacao():
    rotas_livres = ["login", "status", "static"]

    if request.endpoint not in rotas_livres and "usuario_id" not in session:
        return redirect(url_for("login"))


@app.route("/")
def index():
    database = get_database()

    clientes_total = database.execute(
        "SELECT COUNT(*) AS total FROM clientes"
    ).fetchone()["total"]

    veiculos_total = database.execute(
        "SELECT COUNT(*) AS total FROM veiculos"
    ).fetchone()["total"]

    ordens_abertas = database.execute(
        "SELECT COUNT(*) AS total FROM ordens_servico WHERE status = ?",
        ("Aberta",)
    ).fetchone()["total"]

    ordens_andamento = database.execute(
        "SELECT COUNT(*) AS total FROM ordens_servico WHERE status = ?",
        ("Em andamento",)
    ).fetchone()["total"]

    return render_template(
        "index.html",
        clientes_total=clientes_total,
        veiculos_total=veiculos_total,
        ordens_abertas=ordens_abertas,
        ordens_andamento=ordens_andamento
    )


@app.route("/clientes")
def clientes():
    database = get_database()
    clientes_lista = database.execute(
        "SELECT * FROM clientes ORDER BY nome ASC"
    ).fetchall()

    return render_template("clientes.html", clientes=clientes_lista)


@app.route("/clientes/novo", methods=["POST"])
def cadastrar_cliente():
    if session.get("usuario_perfil") == "Cliente":
        return redirect(url_for("clientes"))

    nome = request.form.get("nome", "").strip()
    cpf = request.form.get("cpf", "").strip()
    telefone = request.form.get("telefone", "").strip()
    email = request.form.get("email", "").strip()
    endereco = request.form.get("endereco", "").strip()

    if not nome:
        return redirect(url_for("clientes"))

    database = get_database()

    try:
        database.execute(
            "INSERT INTO clientes (nome, cpf, telefone, email, endereco) VALUES (?, ?, ?, ?, ?)",
            (nome, cpf or None, telefone or None, email or None, endereco or None)
        )
        database.commit()
    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("clientes"))


@app.route("/clientes/<int:cliente_id>/excluir", methods=["POST"])
def excluir_cliente(cliente_id):
    if session.get("usuario_perfil") in ["Cliente", "Mecânico"]:
        return redirect(url_for("clientes"))

    database = get_database()

    try:
        database.execute("DELETE FROM clientes WHERE id = ?", (cliente_id,))
        database.commit()
    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("clientes"))


@app.route("/veiculos", methods=["GET", "POST"])
def veiculos():
    database = get_database()

    if request.method == "POST":
        if session.get("usuario_perfil") == "Cliente":
            return redirect(url_for("veiculos"))

        cliente_id = request.form.get("cliente_id")
        placa = request.form.get("placa", "").strip().upper()
        marca = request.form.get("marca", "").strip()
        modelo = request.form.get("modelo", "").strip()
        ano = request.form.get("ano")

        if cliente_id and placa and marca and modelo:
            try:
                database.execute(
                    "INSERT INTO veiculos (cliente_id, placa, marca, modelo, ano) VALUES (?, ?, ?, ?, ?)",
                    (int(cliente_id), placa, marca, modelo, int(ano) if ano else None)
                )
                database.commit()
            except sqlite3.IntegrityError:
                database.rollback()

        return redirect(url_for("veiculos"))

    veiculos_cursor = database.execute(
        """
        SELECT veiculos.*, clientes.nome AS cliente_nome
        FROM veiculos
        JOIN clientes ON clientes.id = veiculos.cliente_id
        ORDER BY veiculos.id DESC
        """
    ).fetchall()

    veiculos_lista = []

    for v in veiculos_cursor:
        v_dict = dict(v)
        pecas = database.execute(
            "SELECT * FROM pecas_veiculo WHERE veiculo_id = ?", (v["id"],)
        ).fetchall()
        v_dict["pecas"] = pecas
        veiculos_lista.append(v_dict)

    clientes_lista = database.execute(
        "SELECT id, nome FROM clientes ORDER BY nome ASC"
    ).fetchall()

    return render_template(
        "veiculos.html",
        veiculos=veiculos_lista,
        clientes=clientes_lista
    )


@app.route("/veiculos/<int:veiculo_id>/pecas", methods=["POST"])
def cadastrar_peca_veiculo(veiculo_id):
    if session.get("usuario_perfil") == "Cliente":
        return redirect(url_for("veiculos"))

    database = get_database()
    nome = request.form.get("nome", "").strip()
    custo = request.form.get("custo", "").strip().replace(",", ".")

    if nome and custo:
        try:
            database.execute(
                "INSERT INTO pecas_veiculo (veiculo_id, nome, custo) VALUES (?, ?, ?)",
                (veiculo_id, nome, float(custo))
            )
            database.commit()
        except ValueError:
            pass

    return redirect(url_for("veiculos"))


@app.route("/veiculos/<int:veiculo_id>/excluir", methods=["POST"])
def excluir_veiculo(veiculo_id):
    if session.get("usuario_perfil") in ["Cliente", "Mecânico"]:
        return redirect(url_for("veiculos"))

    database = get_database()

    try:
        database.execute("DELETE FROM veiculos WHERE id = ?", (veiculo_id,))
        database.commit()
    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("veiculos"))


@app.route("/ordens", methods=["GET", "POST"])
def ordens():
    database = get_database()
    alerta_margem = None
    erro_validacao = None

    if request.method == "POST":
        if session.get("usuario_perfil") == "Cliente":
            return redirect(url_for("ordens"))

        cliente_id = request.form.get("cliente_id")
        veiculo_id = request.form.get("veiculo_id")
        problemas = request.form.get("problemas", "").strip()
        descricao = request.form.get("descricao", "").strip()

        try:
            custo_total = float(request.form.get("custo_total", "0").replace(".", "").replace(",", "."))
            preco_final = float(request.form.get("preco_final", "0").replace(".", "").replace(",", "."))
        except ValueError:
            custo_total = 0.0
            preco_final = 0.0

        status = request.form.get("status", "Aberta")

        veiculo_valido = database.execute(
            "SELECT id FROM veiculos WHERE id = ? AND cliente_id = ?",
            (veiculo_id, cliente_id)
        ).fetchone()

        if not veiculo_valido:
            erro_validacao = "Erro: O veículo selecionado não pertence ao cliente informado!"
        else:
            margem = 0

            if preco_final > 0:
                margem = ((preco_final - custo_total) / preco_final) * 100

            if margem < 20:
                alerta_margem = "Aviso: A margem de lucro está abaixo de 20%!"

            database.execute(
                """
                INSERT INTO ordens_servico (cliente_id, veiculo_id, problemas, descricao, custo_total, preco_final, margem_lucro, status, valor)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (int(cliente_id), int(veiculo_id), problemas, descricao or problemas, custo_total, preco_final, margem, status, preco_final)
            )
            database.commit()
            return redirect(url_for("ordens"))

    ordens_cursor = database.execute(
        """
        SELECT ordens_servico.*, clientes.nome AS cliente_nome, veiculos.placa, veiculos.marca, veiculos.modelo, veiculos.id AS veiculo_db_id
        FROM ordens_servico
        JOIN clientes ON clientes.id = ordens_servico.cliente_id
        JOIN veiculos ON veiculos.id = ordens_servico.veiculo_id
        ORDER BY ordens_servico.id DESC
        """
    ).fetchall()

    ordens_lista = []

    for o in ordens_cursor:
        o_dict = dict(o)
        pecas = database.execute(
            "SELECT * FROM pecas_veiculo WHERE veiculo_id = ?", (o["veiculo_db_id"],)
        ).fetchall()
        o_dict["pecas"] = pecas
        ordens_lista.append(o_dict)

    clientes_lista = database.execute(
        "SELECT id, nome FROM clientes ORDER BY nome ASC"
    ).fetchall()

    veiculos_lista = database.execute(
        "SELECT * FROM veiculos ORDER BY placa ASC"
    ).fetchall()

    return render_template(
        "ordens.html",
        ordens=ordens_lista,
        clientes=clientes_lista,
        veiculos=veiculos_lista,
        alerta_margem=alerta_margem,
        erro=erro_validacao
    )


@app.route("/ordens/<int:ordem_id>/status", methods=["POST"])
def atualizar_status_ordem(ordem_id):
    if session.get("usuario_perfil") == "Cliente":
        return redirect(url_for("ordens"))

    status = request.form.get("status")
    database = get_database()

    if status == "Aprovado":
        status = "Em andamento"

    if status in ["Aberta", "Em andamento", "Recusado", "Cancelada"]:
        database.execute(
            "UPDATE ordens_servico SET status = ? WHERE id = ?",
            (status, ordem_id)
        )
        database.commit()

    return redirect(url_for("ordens"))


@app.route("/ordens/<int:ordem_id>/excluir", methods=["POST"])
def excluir_ordem(ordem_id):
    if session.get("usuario_perfil") in ["Cliente", "Mecânico"]:
        return redirect(url_for("ordens"))

    database = get_database()
    database.execute("DELETE FROM ordens_servico WHERE id = ?", (ordem_id,))
    database.commit()

    return redirect(url_for("ordens"))


@app.route("/historico", methods=["GET", "POST"])
def historico():
    database = get_database()
    veiculo_selecionado = None
    atendimentos = []

    if request.method == "POST":
        veiculo_id = request.form.get("veiculo_id")

        if veiculo_id:
            veiculo_selecionado = database.execute(
                "SELECT veiculos.*, clientes.nome AS cliente_nome FROM veiculos JOIN clientes ON clientes.id = veiculos.cliente_id WHERE veiculos.id = ?",
                (veiculo_id,)
            ).fetchone()

            atendimentos = database.execute(
                "SELECT * FROM ordens_servico WHERE veiculo_id = ? ORDER BY data_abertura DESC",
                (veiculo_id,)
            ).fetchall()

    veiculos_lista = database.execute(
        "SELECT * FROM veiculos ORDER BY placa ASC"
    ).fetchall()

    return render_template(
        "historico.html",
        veiculos=veiculos_lista,
        veiculo=veiculo_selecionado,
        atendimentos=atendimentos
    )


@app.route("/relatorios", methods=["GET", "POST"])
def relatorios():
    if session.get("usuario_perfil") in ["Cliente", "Mecânico"]:
        return redirect(url_for("index"))

    database = get_database()
    resultados = []
    tipo = request.form.get("tipo", "servicos")

    if request.method == "POST":
        if tipo == "servicos":
            resultados = database.execute(
                "SELECT ordens_servico.*, clientes.nome AS cliente_nome FROM ordens_servico JOIN clientes ON clientes.id = ordens_servico.cliente_id"
            ).fetchall()

        elif tipo == "faturamento":
            resultados = database.execute(
                "SELECT status, COUNT(*) AS qtd, SUM(valor) AS total FROM ordens_servico GROUP BY status"
            ).fetchall()

    return render_template(
        "relatorios.html",
        resultados=resultados,
        tipo=tipo
    )


@app.route("/usuarios", methods=["GET", "POST"])
def usuarios():
    if session.get("usuario_perfil") != "Administrador":
        return redirect(url_for("index"))

    database = get_database()

    if request.method == "POST":
        nome = request.form.get("nome", "").strip()
        email = request.form.get("email", "").strip()
        senha = request.form.get("senha", "").strip()
        perfil = request.form.get("perfil", "Gerente")

        if nome and email and senha:
            senha_h = generate_password_hash(senha)

            try:
                database.execute(
                    "INSERT INTO usuarios (nome, email, senha_hash, perfil) VALUES (?, ?, ?, ?)",
                    (nome, email, senha_h, perfil)
                )
                database.commit()
            except sqlite3.IntegrityError:
                database.rollback()

        return redirect(url_for("usuarios"))

    usuarios_lista = database.execute(
        "SELECT * FROM usuarios ORDER BY nome ASC"
    ).fetchall()

    return render_template("usuarios.html", usuarios=usuarios_lista)


@app.route("/usuarios/<int:usuario_id>/perfil", methods=["POST"])
def atualizar_perfil_usuario(usuario_id):
    if session.get("usuario_perfil") != "Administrador":
        return redirect(url_for("index"))

    perfil = request.form.get("perfil")
    database = get_database()

    if perfil in ["Administrador", "Gerente", "Mecânico", "Cliente"]:
        database.execute(
            "UPDATE usuarios SET perfil = ? WHERE id = ?",
            (perfil, usuario_id)
        )
        database.commit()

    return redirect(url_for("usuarios"))


@app.route("/usuarios/<int:usuario_id>/toggle", methods=["POST"])
def toggle_usuario(usuario_id):
    if session.get("usuario_perfil") != "Administrador":
        return redirect(url_for("index"))

    database = get_database()
    usuario = database.execute(
        "SELECT ativo FROM usuarios WHERE id = ?",
        (usuario_id,)
    ).fetchone()

    if usuario:
        novo_estado = 0 if usuario["ativo"] == 1 else 1

        database.execute(
            "UPDATE usuarios SET ativo = ? WHERE id = ?",
            (novo_estado, usuario_id)
        )
        database.commit()

    return redirect(url_for("usuarios"))


@app.route("/status")
def status():
    database = get_database()
    database.execute("SELECT 1").fetchone()

    return {
        "aplicacao": "Mecanix",
        "status": "operacional",
        "banco_de_dados": "conectado"
    }


initialize_database()


if __name__ == "__main__":
    modo_debug = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=modo_debug
    )