from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from flask_bcrypt import Bcrypt
import json
import os
from datetime import timedelta, datetime

app = Flask(__name__)

app.secret_key = "k_financeiro_chave_secreta_super_segura_substitua_em_producao"
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=2)

bcrypt = Bcrypt(app)

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_DADOS = "dados_financeiros.json"


def carregar_json(caminho, padrao):
    if os.path.exists(caminho):
        try:
            with open(caminho, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return padrao


def salvar_json(caminho, dados):
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)


def adicionar_meses(data_str, meses_para_somar):
    try:
        dt = datetime.strptime(data_str, "%Y-%m-%d")
    except Exception:
        dt = datetime.now()
    
    ano = dt.year
    mes = dt.month + meses_para_somar
    while mes > 12:
        mes -= 12
        ano += 1
    return f"{ano}-{mes:02d}"


@app.route("/")
def index():
    if "usuario" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        data = request.get_json()
        usuario = data.get("usuario", "").strip().lower()
        senha = data.get("senha", "").strip()

        usuarios = carregar_json(ARQUIVO_USUARIOS, {})

        if usuario in usuarios and bcrypt.check_password_hash(usuarios[usuario], senha):
            session.permanent = True
            session["usuario"] = usuario
            return jsonify({"status": "sucesso", "mensagem": "Login efetuado!"})
        else:
            return jsonify({"status": "erro", "mensagem": "Usuário ou senha incorretos."}), 401

    return render_template("login.html")


@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        data = request.get_json()
        nome_usuario = data.get("usuario", "").strip()
        senha = data.get("senha", "").strip()

        if not nome_usuario or not senha:
            return jsonify({"status": "erro", "mensagem": "Preencha todos os campos."}), 400

        if not any(c.isupper() for c in nome_usuario) or not any(c.isdigit() for c in nome_usuario):
            return jsonify({
                "status": "erro",
                "mensagem": "O usuário deve conter pelo menos 1 letra maiúscula e 1 número."
            }), 400

        if len(senha) < 7:
            return jsonify({"status": "erro", "mensagem": "A senha deve ter no mínimo 7 caracteres."}), 400

        usuarios = carregar_json(ARQUIVO_USUARIOS, {})
        usuario_chave = nome_usuario.lower()

        if usuario_chave in usuarios:
            return jsonify({"status": "erro", "mensagem": "Este nome de usuário já existe."}), 400

        senha_hash = bcrypt.generate_password_hash(senha).decode('utf-8')
        usuarios[usuario_chave] = senha_hash
        salvar_json(ARQUIVO_USUARIOS, usuarios)

        session.permanent = True
        session["usuario"] = usuario_chave
        return jsonify({"status": "sucesso", "mensagem": "Conta criada com sucesso!"})

    return render_template("cadastro.html")


@app.route("/dashboard")
def dashboard():
    if "usuario" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", usuario=session["usuario"])


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


# ==========================================
# ROTAS DA API
# ==========================================

@app.route("/api/dados", methods=["GET"])
def obter_dados():
    if "usuario" not in session:
        return jsonify({"status": "erro", "mensagem": "Não autorizado"}), 401

    usuario = session["usuario"]
    todos_dados = carregar_json(ARQUIVO_DADOS, {})
    dados_user = todos_dados.get(usuario, {
        "salario": 0.0,
        "renda_extra": 0.0,
        "cartoes": [],
        "saidas": []
    })

    return jsonify(dados_user)


@app.route("/api/salvar_rendas", methods=["POST"])
def salvar_rendas():
    if "usuario" not in session:
        return jsonify({"status": "erro", "mensagem": "Não autorizado"}), 401

    usuario = session["usuario"]
    req = request.get_json() or {}

    todos_dados = carregar_json(ARQUIVO_DADOS, {})
    if usuario not in todos_dados:
        todos_dados[usuario] = {"salario": 0.0, "renda_extra": 0.0, "cartoes": [], "saidas": []}

    todos_dados[usuario]["salario"] = float(req.get("salario", 0.0))
    todos_dados[usuario]["renda_extra"] = float(req.get("renda_extra", 0.0))

    salvar_json(ARQUIVO_DADOS, todos_dados)
    return jsonify({"status": "sucesso"})


@app.route("/api/adicionar_saida", methods=["POST"])
def adicionar_saida():
    if "usuario" not in session:
        return jsonify({"status": "erro", "mensagem": "Não autorizado"}), 401

    try:
        usuario = session["usuario"]
        req = request.get_json() or {}

        data_compra = req.get("data")
        if not data_compra:
            data_compra = datetime.now().strftime("%Y-%m-%d")

        tipo = req.get("tipo", "Débito / Pix")
        descricao = req.get("descricao", "").strip()
        valor_total = float(req.get("valor", 0.0))
        nome_cartao = req.get("cartao", "Nenhum") if tipo == "Cartão de Crédito" else "Nenhum"
        qtd_parcelas = int(req.get("parcelas", 1)) if tipo in ["Cartão de Crédito", "Boleto", "Empréstimo"] else 1

        if valor_total <= 0:
            return jsonify({"status": "erro", "mensagem": "Informe um valor válido maior que zero."}), 400

        todos_dados = carregar_json(ARQUIVO_DADOS, {})
        dados_user = todos_dados.setdefault(usuario, {"salario": 0.0, "renda_extra": 0.0, "cartoes": [], "saidas": []})

        # Validação do Limite do Cartão
        if tipo == "Cartão de Crédito" and nome_cartao != "Nenhum":
            cartao_obj = next((c for c in dados_user.get("cartoes", []) if c.get("nome", "").strip().lower() == nome_cartao.strip().lower()), None)
            if cartao_obj:
                limite = float(cartao_obj.get("limite", 0.0))
                gastos_atuais = sum(
                    float(s.get("valor_parcela", 0.0))
                    for s in dados_user.get("saidas", [])
                    if s.get("cartao", "").strip().lower() == nome_cartao.strip().lower() and s.get("tipo") == "Cartão de Crédito"
                )

                if (gastos_atuais + valor_total) > limite:
                    limite_disponivel = limite - gastos_atuais
                    return jsonify({
                        "status": "erro",
                        "mensagem": f"⚠️ Limite Excedido! Disponível no {nome_cartao}: R$ {limite_disponivel:.2f}"
                    }), 400

        valor_parcela = valor_total / qtd_parcelas
        saidas_geradas = []

        if tipo == "Débito / Pix":
            # Débito / Pix cai IMEDIATAMENTE no mês da compra
            mes_ref = data_compra[:7]
            saidas_geradas.append({
                "id_compra": datetime.now().timestamp(),
                "data_compra": data_compra,
                "mes_referencia": mes_ref,
                "tipo": tipo,
                "descricao": descricao,
                "valor_total": valor_total,
                "valor_parcela": valor_total,
                "cartao": "Nenhum",
                "parcela_atual": 1,
                "total_parcelas": 1,
                "pago": True
            })
        else:
            # Para Cartão, Boleto e Empréstimo:
            # Usamos 'p' direto em vez de 'p - 1'.
            # Na parcela 1 (p=1), soma 1 mês na data da compra.
            for p in range(1, qtd_parcelas + 1):
                mes_ref = adicionar_meses(data_compra, p)
                saidas_geradas.append({
                    "id_compra": datetime.now().timestamp(),
                    "data_compra": data_compra,
                    "mes_referencia": mes_ref,
                    "tipo": tipo,
                    "descricao": descricao,
                    "valor_total": valor_total,
                    "valor_parcela": valor_parcela,
                    "cartao": nome_cartao,
                    "parcela_atual": p,
                    "total_parcelas": qtd_parcelas,
                    "pago": False
                })

        dados_user.setdefault("saidas", []).extend(saidas_geradas)
        salvar_json(ARQUIVO_DADOS, todos_dados)
        return jsonify({"status": "sucesso"})

    except Exception as e:
        return jsonify({"status": "erro", "mensagem": f"Erro interno: {str(e)}"}), 500


@app.route("/api/toggle_pago_saida/<int:index>", methods=["PUT"])
def toggle_pago_saida(index):
    if "usuario" not in session:
        return jsonify({"status": "erro", "mensagem": "Não autorizado"}), 401

    usuario = session["usuario"]
    todos_dados = carregar_json(ARQUIVO_DADOS, {})
    saidas = todos_dados.get(usuario, {}).get("saidas", [])

    if 0 <= index < len(saidas):
        if saidas[index].get("tipo") != "Débito / Pix":
            saidas[index]["pago"] = not saidas[index].get("pago", False)
            salvar_json(ARQUIVO_DADOS, todos_dados)
            return jsonify({"status": "sucesso", "pago": saidas[index]["pago"]})

    return jsonify({"status": "erro", "mensagem": "Índice ou tipo inválido"}), 400


@app.route("/api/remover_saida/<int:index>", methods=["DELETE"])
def remover_saida(index):
    if "usuario" not in session:
        return jsonify({"status": "erro", "mensagem": "Não autorizado"}), 401

    usuario = session["usuario"]
    todos_dados = carregar_json(ARQUIVO_DADOS, {})

    saidas = todos_dados.get(usuario, {}).get("saidas", [])
    if 0 <= index < len(saidas):
        saidas.pop(index)
        salvar_json(ARQUIVO_DADOS, todos_dados)
        return jsonify({"status": "sucesso"})

    return jsonify({"status": "erro", "mensagem": "Índice inválido"}), 400


@app.route("/api/adicionar_cartao", methods=["POST"])
def adicionar_cartao():
    if "usuario" not in session:
        return jsonify({"status": "erro", "mensagem": "Não autorizado"}), 401

    usuario = session["usuario"]
    novo_cartao = request.get_json() or {}

    novo_cartao["limite"] = float(novo_cartao.get("limite", 0.0))
    novo_cartao["vencimento"] = int(novo_cartao.get("vencimento", 1))

    todos_dados = carregar_json(ARQUIVO_DADOS, {})
    todos_dados.setdefault(usuario, {"salario": 0.0, "renda_extra": 0.0, "cartoes": [], "saidas": []})

    cartoes = todos_dados[usuario].setdefault("cartoes", [])
    if any(c["nome"].strip().lower() == novo_cartao["nome"].strip().lower() for c in cartoes):
        return jsonify({"status": "erro", "mensagem": "Já existe um cartão com esse nome."}), 400

    cartoes.append(novo_cartao)
    salvar_json(ARQUIVO_DADOS, todos_dados)
    return jsonify({"status": "sucesso"})


@app.route("/api/editar_cartao", methods=["PUT"])
def editar_cartao():
    if "usuario" not in session:
        return jsonify({"status": "erro", "mensagem": "Não autorizado"}), 401

    usuario = session["usuario"]
    dados_editados = request.get_json() or {}

    nome_original = dados_editados.get("nome_original")
    novo_nome = dados_editados.get("nome")
    novo_limite = float(dados_editados.get("limite", 0.0))
    novo_vencimento = int(dados_editados.get("vencimento", 1))

    todos_dados = carregar_json(ARQUIVO_DADOS, {})
    cartoes = todos_dados.get(usuario, {}).get("cartoes", [])

    for c in cartoes:
        if c.get("nome") == nome_original:
            c["nome"] = novo_nome
            c["limite"] = novo_limite
            c["vencimento"] = novo_vencimento

            if nome_original != novo_nome:
                for s in todos_dados.get(usuario, {}).get("saidas", []):
                    if s.get("cartao") == nome_original:
                        s["cartao"] = novo_nome

            salvar_json(ARQUIVO_DADOS, todos_dados)
            return jsonify({"status": "sucesso"})

    return jsonify({"status": "erro", "mensagem": "Cartão não encontrado."}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)