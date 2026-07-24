from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'k_financeiro_secret_key_super_seguro'

# Configuração do Banco de Dados SQLite (Persistência Permanente)
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ==========================================
# MODELOS DO BANCO DE DADOS
# ==========================================

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    senha = db.Column(db.String(200), nullable=False)

    rendas = db.relationship('Renda', backref='usuario', lazy=True, cascade='all, delete-orphan')
    despesas = db.relationship('Despesa', backref='usuario', lazy=True, cascade='all, delete-orphan')
    cartoes = db.relationship('Cartao', backref='usuario', lazy=True, cascade='all, delete-orphan')

class Renda(db.Model):
    __tablename__ = 'rendas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    mes_referencia = db.Column(db.String(7), nullable=False)
    salario = db.Column(db.Float, default=0.0)
    extra = db.Column(db.Float, default=0.0)

class Despesa(db.Model):
    __tablename__ = 'despesas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_unico = db.Column(db.BigInteger, unique=True, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor_parcela = db.Column(db.Float, nullable=False)
    data_compra = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    cartao = db.Column(db.String(100), default='-')
    parcela_atual = db.Column(db.Integer, default=1)
    total_parcelas = db.Column(db.Integer, default=1)
    mes_referencia = db.Column(db.String(7), nullable=False)
    pago = db.Column(db.Boolean, default=False)

class Cartao(db.Model):
    __tablename__ = 'cartoes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cartao_id_ext = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    limite = db.Column(db.Float, nullable=False)
    dia_vencimento = db.Column(db.Integer, nullable=False)

with app.app_context():
    db.create_all()

# ==========================================
# ROTAS DE AUTENTICAÇÃO
# ==========================================

@app.route('/')
def index():
    if 'usuario_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email').strip().lower()
        senha = request.form.get('senha')

        user = Usuario.query.filter_by(email=email).first()
        if user and check_password_hash(user.senha, senha):
            session['usuario_id'] = user.id
            session['usuario_nome'] = user.nome
            return redirect(url_for('dashboard'))
        return render_template('login.html', erro="E-mail ou senha incorretos.")
    
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form.get('nome').strip()
        email = request.form.get('email').strip().lower()
        senha = request.form.get('senha')

        user_exist = Usuario.query.filter_by(email=email).first()
        if user_exist:
            return render_template('cadastro.html', erro="Este e-mail já está cadastrado.")

        novo_usuario = Usuario(
            nome=nome,
            email=email,
            senha=generate_password_hash(senha)
        )
        db.session.add(novo_usuario)
        db.session.commit()

        session['usuario_id'] = novo_usuario.id
        session['usuario_nome'] = novo_usuario.nome
        return redirect(url_for('dashboard'))
    
    return render_template('cadastro.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'usuario_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# ==========================================
# API DE DADOS E PERSISTÊNCIA
# ==========================================

@app.route('/api/dados', methods=['GET'])
def obter_dados():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401

    user_id = session['usuario_id']
    user = Usuario.query.get(user_id)

    rendas_dict = {}
    for r in user.rendas:
        rendas_dict[r.mes_referencia] = {
            'salario': r.salario,
            'extra': r.extra
        }

    despesas_list = []
    for d in user.despesas:
        despesas_list.append({
            'idUnico': d.id_unico,
            'descricao': d.descricao,
            'valorParcela': d.valor_parcela,
            'dataCompra': d.data_compra,
            'tipo': d.tipo,
            'cartao': d.cartao,
            'parcelaAtual': d.parcela_atual,
            'totalParcelas': d.total_parcelas,
            'mesReferencia': d.mes_referencia,
            'pago': d.pago
        })

    cartoes_list = []
    for c in user.cartoes:
        cartoes_list.append({
            'id': c.cartao_id_ext,
            'nome': c.nome,
            'limite': c.limite,
            'dia_vencimento': c.dia_vencimento
        })

    return jsonify({
        'status': 'sucesso',
        'usuario': user.nome,
        'dados': {
            'rendas': rendas_dict,
            'despesas': despesas_list,
            'cartoes': cartoes_list
        }
    })

@app.route('/api/salvar_dados', methods=['POST'])
def salvar_dados_completo():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401

    user_id = session['usuario_id']
    req_data = request.get_json()

    if not req_data:
        return jsonify({'status': 'erro', 'mensagem': 'Dados inválidos'}), 400

    try:
        # Sincronizar Rendas
        rendas_data = req_data.get('rendas', {})
        for mes, val in rendas_data.items():
            r_obj = Renda.query.filter_by(usuario_id=user_id, mes_referencia=mes).first()
            if r_obj:
                r_obj.salario = float(val.get('salario', 0))
                r_obj.extra = float(val.get('extra', 0))
            else:
                nova_renda = Renda(
                    usuario_id=user_id,
                    mes_referencia=mes,
                    salario=float(val.get('salario', 0)),
                    extra=float(val.get('extra', 0))
                )
                db.session.add(nova_renda)

        # Sincronizar Despesas (Substituição inteligente do histórico do usuário)
        Despesa.query.filter_by(usuario_id=user_id).delete()
        despesas_data = req_data.get('despesas', [])
        for d in despesas_data:
            nova_despesa = Despesa(
                usuario_id=user_id,
                id_unico=int(d.get('idUnico')),
                descricao=d.get('descricao'),
                valor_parcela=float(d.get('valorParcela', 0)),
                data_compra=d.get('dataCompra'),
                tipo=d.get('tipo'),
                cartao=d.get('cartao', '-'),
                parcela_atual=int(d.get('parcelaAtual', 1)),
                total_parcelas=int(d.get('totalParcelas', 1)),
                mes_referencia=d.get('mesReferencia'),
                pago=bool(d.get('pago', False))
            )
            db.session.add(nova_despesa)

        db.session.commit()
        return jsonify({'status': 'sucesso', 'mensagem': 'Dados salvos com sucesso!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500

@app.route('/cadastrar_cartao', methods=['POST'])
def cadastrar_cartao():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401

    user_id = session['usuario_id']
    data = request.get_json()

    try:
        novo_c = Cartao(
            usuario_id=user_id,
            cartao_id_ext=str(data.get('id', 'c_' + str(os.urandom(4).hex()))),
            nome=data.get('nome').strip(),
            limite=float(data.get('limite', 0)),
            dia_vencimento=int(data.get('dia_vencimento', 1))
        )
        db.session.add(novo_c)
        db.session.commit()
        return jsonify({'status': 'sucesso', 'cartao_id': novo_c.cartao_id_ext})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500

@app.route('/editar_cartao', methods=['POST'])
def editar_cartao():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401

    user_id = session['usuario_id']
    data = request.get_json()
    cartao_id = str(data.get('id'))

    c = Cartao.query.filter_by(usuario_id=user_id, cartao_id_ext=cartao_id).first()
    if not c:
        return jsonify({'status': 'erro', 'mensagem': 'Cartão não encontrado'}), 404

    try:
        c.nome = data.get('nome').strip()
        c.limite = float(data.get('limite', 0))
        c.dia_vencimento = int(data.get('dia_vencimento', 1))
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500

@app.route('/excluir_cartao', methods=['POST'])
def excluir_cartao():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401

    user_id = session['usuario_id']
    data = request.get_json()
    cartao_id = str(data.get('id'))

    c = Cartao.query.filter_by(usuario_id=user_id, cartao_id_ext=cartao_id).first()
    if c:
        db.session.delete(c)
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    return jsonify({'status': 'erro', 'mensagem': 'Cartão não encontrado'}), 404

if __name__ == '__main__':
    app.run(debug=True, port=5000)