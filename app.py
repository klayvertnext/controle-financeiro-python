from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import os

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_super_segura'

# Dicionário em memória para armazenar dados dos usuários (simulando banco de dados)
DADOS_USUARIO = {}

@app.route('/')
def index():
    if 'usuario' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Suporta tanto JSON quanto Formulário tradicional
        dados = request.get_json(silent=True) or request.form
        usuario = dados.get('usuario') or dados.get('username')
        senha = dados.get('senha') or dados.get('password')
        
        if usuario and senha:
            session['usuario'] = usuario
            if usuario not in DADOS_USUARIO:
                DADOS_USUARIO[usuario] = {
                    'rendas': {'salario': 0, 'extra': 0},
                    'despesas': [],
                    'cartoes': []
                }
            return jsonify({'status': 'sucesso', 'redirecionar': url_for('dashboard')}) if request.is_json else redirect(url_for('dashboard'))
            
        return jsonify({'status': 'erro', 'mensagem': 'Preencha todos os campos'}), 400
        
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        dados = request.get_json(silent=True) or request.form
        usuario = dados.get('usuario') or dados.get('username')
        senha = dados.get('senha') or dados.get('password')
        
        if usuario and senha:
            session['usuario'] = usuario
            if usuario not in DADOS_USUARIO:
                DADOS_USUARIO[usuario] = {
                    'rendas': {'salario': 0, 'extra': 0},
                    'despesas': [],
                    'cartoes': []
                }
            return jsonify({'status': 'sucesso', 'redirecionar': url_for('dashboard')}) if request.is_json else redirect(url_for('dashboard'))
            
        return jsonify({'status': 'erro', 'mensagem': 'Preencha todos os campos'}), 400
        
    return render_template('cadastro.html')

@app.route('/dashboard')
def dashboard():
    if 'usuario' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/api/dados', methods=['GET'])
def api_dados():
    if 'usuario' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401
        
    usuario = session['usuario']
    if usuario not in DADOS_USUARIO:
        DADOS_USUARIO[usuario] = {
            'rendas': {'salario': 0, 'extra': 0},
            'despesas': [],
            'cartoes': []
        }
        
    return jsonify({
        'status': 'sucesso',
        'usuario': usuario,
        'dados': DADOS_USUARIO[usuario]
    })

@app.route('/cadastrar_cartao', methods=['POST'])
def cadastrar_cartao():
    if 'usuario' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Usuário não autenticado.'}), 401
        
    usuario = session['usuario']
    dados = request.get_json() or {}
    
    nome = dados.get('nome')
    limite = dados.get('limite', 0)
    dia_vencimento = dados.get('dia_vencimento', 1)
    
    if not nome:
        return jsonify({'status': 'erro', 'mensagem': 'O nome do cartão é obrigatório.'}), 400
        
    if usuario not in DADOS_USUARIO:
        DADOS_USUARIO[usuario] = {
            'rendas': {'salario': 0, 'extra': 0},
            'despesas': [],
            'cartoes': []
        }
        
    novo_cartao = {
        'nome': nome,
        'limite': float(limite or 0),
        'dia_vencimento': int(dia_vencimento or 1)
    }
    
    DADOS_USUARIO[usuario]['cartoes'].append(novo_cartao)
    
    return jsonify({
        'status': 'sucesso', 
        'mensagem': 'Cartão cadastrado com sucesso!',
        'cartoes': DADOS_USUARIO[usuario]['cartoes']
    })

@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)