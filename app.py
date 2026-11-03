from pathlib import Path
import os
import secrets
import sqlite3

from flask import Flask, g, redirect, render_template, request, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "mecanix.db"

app = Flask(__name__)
app.config["DATABASE"] = DATABASE_PATH
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY") or secrets.token_hex(32)


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
    database.execute("PRAGMA foreign_keys = ON")

    database.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            senha_hash TEXT NOT NULL,
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
            FOREIGN KEY (cliente_id)
                REFERENCES clientes (id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        );

        CREATE TABLE IF NOT EXISTS ordens_servico (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            veiculo_id INTEGER NOT NULL,
            descricao TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Aberta',
            valor REAL NOT NULL DEFAULT 0,
            data_abertura TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            data_conclusao TEXT,
            FOREIGN KEY (cliente_id)
                REFERENCES clientes (id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE,
            FOREIGN KEY (veiculo_id)
                REFERENCES veiculos (id)
                ON DELETE RESTRICT
                ON UPDATE CASCADE
        );
        """
    )

    database.commit()
    database.close()


@app.teardown_appcontext
def teardown_database(exception=None):
    close_database(exception)


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
        """
        SELECT COUNT(*) AS total
        FROM ordens_servico
        WHERE status = ?
        """,
        ("Aberta",)
    ).fetchone()["total"]

    ordens_andamento = database.execute(
        """
        SELECT COUNT(*) AS total
        FROM ordens_servico
        WHERE status = ?
        """,
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
        """
        SELECT id, nome, cpf, telefone, email, endereco, criado_em
        FROM clientes
        ORDER BY nome ASC
        """
    ).fetchall()

    return render_template(
        "clientes.html",
        clientes=clientes_lista
    )


@app.route("/clientes/novo", methods=["POST"])
def cadastrar_cliente():
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
            """
            INSERT INTO clientes (nome, cpf, telefone, email, endereco)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                nome,
                cpf or None,
                telefone or None,
                email or None,
                endereco or None
            )
        )

        database.commit()

    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("clientes"))


@app.route("/clientes/<int:cliente_id>/excluir", methods=["POST"])
def excluir_cliente(cliente_id):
    database = get_database()

    try:
        database.execute(
            "DELETE FROM clientes WHERE id = ?",
            (cliente_id,)
        )

        database.commit()

    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("clientes"))


@app.route("/veiculos")
def veiculos():
    database = get_database()

    veiculos_lista = database.execute(
        """
        SELECT
            veiculos.id,
            veiculos.placa,
            veiculos.marca,
            veiculos.modelo,
            veiculos.ano,
            clientes.id AS cliente_id,
            clientes.nome AS cliente_nome
        FROM veiculos
        INNER JOIN clientes
            ON clientes.id = veiculos.cliente_id
        ORDER BY veiculos.id DESC
        """
    ).fetchall()

    clientes_lista = database.execute(
        """
        SELECT id, nome
        FROM clientes
        ORDER BY nome ASC
        """
    ).fetchall()

    return render_template(
        "veiculos.html",
        veiculos=veiculos_lista,
        clientes=clientes_lista
    )


@app.route("/veiculos/novo", methods=["POST"])
def cadastrar_veiculo():
    cliente_id = request.form.get("cliente_id", "").strip()
    placa = request.form.get("placa", "").strip().upper()
    marca = request.form.get("marca", "").strip()
    modelo = request.form.get("modelo", "").strip()
    ano = request.form.get("ano", "").strip()

    if not cliente_id or not placa or not marca or not modelo:
        return redirect(url_for("veiculos"))

    try:
        cliente_id = int(cliente_id)
    except ValueError:
        return redirect(url_for("veiculos"))

    ano_valor = None

    if ano:
        try:
            ano_valor = int(ano)
        except ValueError:
            return redirect(url_for("veiculos"))

    database = get_database()

    try:
        database.execute(
            """
            INSERT INTO veiculos (
                cliente_id,
                placa,
                marca,
                modelo,
                ano
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                placa,
                marca,
                modelo,
                ano_valor
            )
        )

        database.commit()

    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("veiculos"))


@app.route("/veiculos/<int:veiculo_id>/excluir", methods=["POST"])
def excluir_veiculo(veiculo_id):
    database = get_database()

    try:
        database.execute(
            "DELETE FROM veiculos WHERE id = ?",
            (veiculo_id,)
        )

        database.commit()

    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("veiculos"))


@app.route("/ordens")
def ordens():
    database = get_database()

    ordens_lista = database.execute(
        """
        SELECT
            ordens_servico.id,
            ordens_servico.descricao,
            ordens_servico.status,
            ordens_servico.valor,
            ordens_servico.data_abertura,
            ordens_servico.data_conclusao,
            clientes.nome AS cliente_nome,
            veiculos.placa,
            veiculos.marca,
            veiculos.modelo
        FROM ordens_servico
        INNER JOIN clientes
            ON clientes.id = ordens_servico.cliente_id
        INNER JOIN veiculos
            ON veiculos.id = ordens_servico.veiculo_id
        ORDER BY ordens_servico.id DESC
        """
    ).fetchall()

    clientes_lista = database.execute(
        """
        SELECT id, nome
        FROM clientes
        ORDER BY nome ASC
        """
    ).fetchall()

    veiculos_lista = database.execute(
        """
        SELECT
            veiculos.id,
            veiculos.cliente_id,
            veiculos.placa,
            veiculos.marca,
            veiculos.modelo
        FROM veiculos
        ORDER BY veiculos.placa ASC
        """
    ).fetchall()

    return render_template(
        "ordens.html",
        ordens=ordens_lista,
        clientes=clientes_lista,
        veiculos=veiculos_lista
    )


@app.route("/ordens/novo", methods=["POST"])
def cadastrar_ordem():
    cliente_id = request.form.get("cliente_id", "").strip()
    veiculo_id = request.form.get("veiculo_id", "").strip()
    descricao = request.form.get("descricao", "").strip()
    status = request.form.get("status", "Aberta").strip()
    valor = request.form.get("valor", "").strip().replace(",", ".")

    if not cliente_id or not veiculo_id or not descricao:
        return redirect(url_for("ordens"))

    try:
        cliente_id = int(cliente_id)
        veiculo_id = int(veiculo_id)
        valor = float(valor) if valor else 0
    except ValueError:
        return redirect(url_for("ordens"))

    status_validos = {
        "Aberta",
        "Em andamento",
        "Concluída",
        "Cancelada"
    }

    if status not in status_validos:
        return redirect(url_for("ordens"))

    database = get_database()

    veiculo = database.execute(
        """
        SELECT id
        FROM veiculos
        WHERE id = ? AND cliente_id = ?
        """,
        (veiculo_id, cliente_id)
    ).fetchone()

    if veiculo is None:
        return redirect(url_for("ordens"))

    try:
        database.execute(
            """
            INSERT INTO ordens_servico (
                cliente_id,
                veiculo_id,
                descricao,
                status,
                valor
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                cliente_id,
                veiculo_id,
                descricao,
                status,
                valor
            )
        )

        database.commit()

    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("ordens"))


@app.route("/ordens/<int:ordem_id>/status", methods=["POST"])
def atualizar_status_ordem(ordem_id):
    status = request.form.get("status", "").strip()

    status_validos = {
        "Aberta",
        "Em andamento",
        "Concluída",
        "Cancelada"
    }

    if status not in status_validos:
        return redirect(url_for("ordens"))

    database = get_database()

    try:
        if status == "Concluída":
            database.execute(
                """
                UPDATE ordens_servico
                SET status = ?, data_conclusao = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (status, ordem_id)
            )
        else:
            database.execute(
                """
                UPDATE ordens_servico
                SET status = ?, data_conclusao = NULL
                WHERE id = ?
                """,
                (status, ordem_id)
            )

        database.commit()

    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("ordens"))


@app.route("/ordens/<int:ordem_id>/excluir", methods=["POST"])
def excluir_ordem(ordem_id):
    database = get_database()

    try:
        database.execute(
            "DELETE FROM ordens_servico WHERE id = ?",
            (ordem_id,)
        )

        database.commit()

    except sqlite3.IntegrityError:
        database.rollback()

    return redirect(url_for("ordens"))


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
    debug_ativado = os.environ.get("FLASK_DEBUG", "false").lower() in {
        "1",
        "true",
        "yes"
    }

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=debug_ativado
    )