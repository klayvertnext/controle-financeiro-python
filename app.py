from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'chave-secreta-financeiro-2026')

# BANCO DE DADOS EM MEMÓRIA (Estrutura segura para testes e persistência em sessão)
# Para produção definitiva, recomenda-se conectar ao SQLAlchemy/PostgreSQL.
USUARIOS_DB = {}   # Ex: { 'usuario': 'hash_senha' }
DADOS_USUARIO = {} # Ex: { 'usuario': { 'cartoes': [], 'despesas': [], 'rendas': {'salario': 0.0, 'extra': 0.0} } }

@app.route('/')
def index():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    dados = request.get_json(silent=True) or request.form
    usuario = dados.get('usuario') or dados.get('username')
    senha = dados.get('senha') or dados.get('password')

    if not usuario or not senha:
        return jsonify({'status': 'erro', 'mensagem': 'Preencha todos os campos.'}), 400

    if usuario in USUARIOS_DB and check_password_hash(USUARIOS_DB[usuario], senha):
        session['usuario'] = usuario
        return jsonify({'status': 'sucesso', 'redirect': '/dashboard'})
    
    return jsonify({'status': 'erro', 'mensagem': 'Usuário ou senha incorretos.'}), 401

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'GET':
        return render_template('cadastro.html')
    
    dados = request.get_json(silent=True) or request.form
    usuario = dados.get('usuario') or dados.get('username')
    senha = dados.get('senha') or dados.get('password')

    if not usuario or not senha:
        return jsonify({'status': 'erro', 'mensagem': 'Preencha todos os campos.'}), 400

    if usuario in USUARIOS_DB:
        return jsonify({'status': 'erro', 'mensagem': 'Este nome de usuário já está em uso.'}), 400

    USUARIOS_DB[usuario] = generate_password_hash(senha)
    DADOS_USUARIO[usuario] = {
        'cartoes': [], 
        'despesas': [], 
        'rendas': {'salario': 0.0, 'extra': 0.0}
    }

    session['usuario'] = usuario
    return jsonify({'status': 'sucesso', 'redirect': '/dashboard'})

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/dados', methods=['GET'])
def obter_dados():
    if 'usuario' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401
    
    usuario = session['usuario']
    dados = DADOS_USUARIO.get(usuario, {'cartoes': [], 'despesas': [], 'rendas': {'salario': 0.0, 'extra': 0.0}})
    return jsonify({'status': 'sucesso', 'dados': dados, 'usuario': usuario})

@app.route('/cadastrar_cartao', methods=['POST'])
def cadastrar_cartao():
    if 'usuario' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401

    dados = request.get_json(silent=True) or request.form
    nome = dados.get('nome')
    limite = dados.get('limite')
    dia_vencimento = dados.get('dia_vencimento')

    if not nome:
        return jsonify({'status': 'erro', 'mensagem': 'O nome do cartão é obrigatório.'}), 400

    usuario = session['usuario']
    
    if usuario not in DADOS_USUARIO:
        DADOS_USUARIO[usuario] = {'cartoes': [], 'despesas': [], 'rendas': {'salario': 0.0, 'extra': 0.0}}
    
    novo_cartao = {
        'nome': nome.strip(),
        'limite': float(limite or 0),
        'dia_vencimento': int(dia_vencimento or 1)
    }
    
    DADOS_USUARIO[usuario]['cartoes'].append(novo_cartao)
    return jsonify({'status': 'sucesso', 'mensagem': 'Cartão cadastrado com sucesso!', 'cartoes': DADOS_USUARIO[usuario]['cartoes']})

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)