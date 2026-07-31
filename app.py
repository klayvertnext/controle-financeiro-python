from datetime import datetime
import logging
import os
import re
import secrets

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
basedir = os.path.abspath(os.path.dirname(__file__))
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql+psycopg://', 1)
elif database_url and database_url.startswith('postgresql://'):
    database_url = database_url.replace('postgresql://', 'postgresql+psycopg://', 1)

# No Render, configure DATABASE_URL com um PostgreSQL para manter os dados entre deploys.
app.config['SQLALCHEMY_DATABASE_URI'] = database_url or 'sqlite:///' + os.path.join(basedir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('RENDER') == 'true'
app.config['MAX_CONTENT_LENGTH'] = 1 * 1024 * 1024

if os.environ.get('RENDER') and not os.environ.get('SECRET_KEY'):
    logging.warning('SECRET_KEY não configurada; defina uma chave secreta no Render.')

db = SQLAlchemy(app)

# ==========================================
# MODELOS DO BANCO DE DADOS
# ==========================================

class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)   # Nome de usuário único
    email = db.Column(db.String(120), unique=True, nullable=False)  # E-mail Gmail único
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
    __table_args__ = (db.UniqueConstraint('usuario_id', 'mes_referencia', name='uq_renda_usuario_mes'),)

class Despesa(db.Model):
    __tablename__ = 'despesas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_unico = db.Column(db.BigInteger, nullable=False)
    descricao = db.Column(db.String(200), nullable=False)
    valor_parcela = db.Column(db.Float, nullable=False)
    data_compra = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    cartao = db.Column(db.String(100), default='-')
    parcela_atual = db.Column(db.Integer, default=1)
    total_parcelas = db.Column(db.Integer, default=1)
    mes_referencia = db.Column(db.String(7), nullable=False)
    pago = db.Column(db.Boolean, default=False)
    __table_args__ = (db.UniqueConstraint('usuario_id', 'id_unico', name='uq_despesa_usuario_ext'),)

class Cartao(db.Model):
    __tablename__ = 'cartoes'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cartao_id_ext = db.Column(db.String(50), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    limite = db.Column(db.Float, nullable=False)
    dia_vencimento = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('usuario_id', 'cartao_id_ext', name='uq_cartao_usuario_ext'),)

with app.app_context():
    db.create_all()


MES_RE = re.compile(r'^\d{4}-(0[1-9]|1[0-2])$')


def numero_nao_negativo(valor, campo):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f'{campo} deve ser um número válido.')
    if numero < 0 or numero != numero or numero == float('inf'):
        raise ValueError(f'{campo} deve ser um número não negativo.')
    return round(numero, 2)


def inteiro_no_intervalo(valor, campo, minimo, maximo):
    try:
        numero = int(valor)
    except (TypeError, ValueError):
        raise ValueError(f'{campo} deve ser um número inteiro.')
    if not minimo <= numero <= maximo:
        raise ValueError(f'{campo} deve estar entre {minimo} e {maximo}.')
    return numero


def mes_valido(valor):
    return isinstance(valor, str) and bool(MES_RE.fullmatch(valor))


@app.get('/healthz')
def healthcheck():
    return jsonify({'status': 'ok'}), 200


@app.errorhandler(413)
def payload_muito_grande(_erro):
    return jsonify({'status': 'erro', 'mensagem': 'Requisição muito grande.'}), 413

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
    with app.app_context():
        db.create_all()

    if request.method == 'POST':
        identificador = request.form.get('identificador', '').strip()
        
        # Fallbacks de segurança
        if not identificador:
            identificador = request.form.get('email', '').strip()
        if not identificador:
            identificador = request.form.get('nome', '').strip()

        senha = request.form.get('senha', '').strip()

        if not identificador or not senha:
            return render_template('login.html', erro="Preencha todos os campos obrigatórios.")

        try:
            # Busca pelo Nome de Usuário (respeitando maiúsculas) ou E-mail (minúsculas)
            user = Usuario.query.filter(
                (Usuario.nome == identificador) | 
                (Usuario.email == identificador.lower())
            ).first()
            
            if user and check_password_hash(user.senha, senha):
                session['usuario_id'] = user.id
                session['usuario_nome'] = user.nome
                return redirect(url_for('dashboard'))
                
            return render_template('login.html', erro="Usuário/E-mail ou senha incorretos.")
        except Exception as e:
            return render_template('login.html', erro="Erro ao processar o login. Tente novamente.")
    
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    with app.app_context():
        db.create_all()

    if request.method == 'POST':
        nome_raw = request.form.get('nome', '')
        email_raw = request.form.get('email', '')
        senha_raw = request.form.get('senha', '')

        nome = nome_raw.strip() if nome_raw else ''
        email = email_raw.strip().lower() if email_raw else ''
        senha = senha_raw.strip() if senha_raw else ''

        if not nome or not email or not senha:
            return render_template('cadastro.html', erro="Preencha todos os campos obrigatórios.")

        if not email.endswith('@gmail.com'):
            return render_template('cadastro.html', erro="O e-mail precisa ser do Gmail (@gmail.com).")

        if len(senha) < 7:
            return render_template('cadastro.html', erro="A senha deve ter no mínimo 7 caracteres.")

        try:
            if Usuario.query.filter_by(nome=nome).first():
                return render_template('cadastro.html', erro="Este nome de usuário já está em uso. Escolha outro.")

            if Usuario.query.filter_by(email=email).first():
                return render_template('cadastro.html', erro="Este e-mail já está cadastrado em nosso sistema.")

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
        except Exception as e:
            db.session.rollback()
            return render_template('cadastro.html', erro="Erro interno ao realizar cadastro. Tente novamente.")
    
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
    user = db.session.get(Usuario, user_id)
    if not user:
        return jsonify({'status': 'erro', 'mensagem': 'Utilizador não encontrado'}), 404

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
    req_data = request.get_json(silent=True)

    if not req_data:
        return jsonify({'status': 'erro', 'mensagem': 'Dados inválidos'}), 400

    try:
        rendas_data = req_data.get('rendas', {})
        despesas_data = req_data.get('despesas', [])
        if not isinstance(rendas_data, dict) or not isinstance(despesas_data, list):
            raise ValueError('Formato de dados inválido.')
        if len(rendas_data) > 240 or len(despesas_data) > 5000:
            raise ValueError('Quantidade de registros acima do limite permitido.')

        rendas_validadas = []
        for mes, val in rendas_data.items():
            if not mes_valido(mes) or not isinstance(val, dict):
                raise ValueError('Mês de referência inválido.')
            rendas_validadas.append((mes, numero_nao_negativo(val.get('salario', 0), 'Salário'), numero_nao_negativo(val.get('extra', 0), 'Renda extra')))

        despesas_validadas = []
        ids_recebidos = set()
        for item in despesas_data:
            if not isinstance(item, dict):
                raise ValueError('Despesa inválida.')
            id_unico = int(item.get('idUnico'))
            if id_unico in ids_recebidos:
                raise ValueError('Existem despesas duplicadas.')
            ids_recebidos.add(id_unico)
            descricao = str(item.get('descricao', '')).strip()
            if not descricao or len(descricao) > 200:
                raise ValueError('A descrição da despesa é obrigatória e deve ter até 200 caracteres.')
            mes_ref = str(item.get('mesReferencia', '')).strip()
            if not mes_valido(mes_ref):
                raise ValueError('Mês de referência da despesa inválido.')
            data_compra = str(item.get('dataCompra', '')).strip()
            datetime.strptime(data_compra, '%Y-%m-%d')
            parcela_atual = inteiro_no_intervalo(item.get('parcelaAtual', 1), 'Parcela atual', 1, 360)
            total_parcelas = inteiro_no_intervalo(item.get('totalParcelas', 1), 'Total de parcelas', 1, 360)
            if parcela_atual > total_parcelas:
                raise ValueError('A parcela atual não pode superar o total de parcelas.')
            tipo = str(item.get('tipo', '')).strip()
            if tipo not in {'Cartao', 'Débito', 'Pix', 'Dinheiro'}:
                raise ValueError('Tipo de despesa inválido.')
            despesas_validadas.append({
                'id_unico': id_unico, 'descricao': descricao,
                'valor_parcela': numero_nao_negativo(item.get('valorParcela', 0), 'Valor da parcela'),
                'data_compra': data_compra, 'tipo': tipo,
                'cartao': str(item.get('cartao', '-')).strip()[:100] or '-',
                'parcela_atual': parcela_atual, 'total_parcelas': total_parcelas,
                'mes_referencia': mes_ref, 'pago': bool(item.get('pago', False))
            })

        for mes, salario, extra in rendas_validadas:
            r_obj = Renda.query.filter_by(usuario_id=user_id, mes_referencia=mes).first()
            if r_obj:
                r_obj.salario = salario
                r_obj.extra = extra
            else:
                nova_renda = Renda(
                    usuario_id=user_id,
                    mes_referencia=mes,
                    salario=salario,
                    extra=extra
                )
                db.session.add(nova_renda)

        Despesa.query.filter_by(usuario_id=user_id).delete()
        for dados_despesa in despesas_validadas:
            db.session.add(Despesa(usuario_id=user_id, **dados_despesa))

        db.session.commit()
        return jsonify({'status': 'sucesso', 'mensagem': 'Dados salvos com sucesso!'})
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400
    except Exception:
        db.session.rollback()
        app.logger.exception('Erro ao salvar dados financeiros')
        return jsonify({'status': 'erro', 'mensagem': 'Erro interno ao salvar os dados.'}), 500

@app.route('/cadastrar_cartao', methods=['POST'])
def cadastrar_cartao():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401

    user_id = session['usuario_id']
    data = request.get_json() or {}

    try:
        nome_cartao = str(data.get('nome', '')).strip()
        if not nome_cartao or len(nome_cartao) > 100:
            return jsonify({'status': 'erro', 'mensagem': 'O nome do cartão é obrigatório e deve ter até 100 caracteres.'}), 400

        limite = numero_nao_negativo(data.get('limite', 0), 'Limite')
        dia_vencimento = inteiro_no_intervalo(data.get('dia_vencimento', 1), 'Dia de vencimento', 1, 31)
        cartao_id_ext = str(data.get('id', 'c_' + str(os.urandom(4).hex())))
        if len(cartao_id_ext) > 50:
            raise ValueError('Identificador do cartão inválido.')
        novo_c = Cartao(
            usuario_id=user_id,
            cartao_id_ext=cartao_id_ext,
            nome=nome_cartao,
            limite=limite,
            dia_vencimento=dia_vencimento
        )
        db.session.add(novo_c)
        db.session.commit()
        return jsonify({'status': 'sucesso', 'cartao_id': novo_c.cartao_id_ext})
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400
    except Exception:
        db.session.rollback()
        app.logger.exception('Erro ao cadastrar cartão')
        return jsonify({'status': 'erro', 'mensagem': 'Erro interno ao cadastrar cartão.'}), 500

@app.route('/editar_cartao', methods=['POST'])
def editar_cartao():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401

    user_id = session['usuario_id']
    data = request.get_json() or {}
    cartao_id = str(data.get('id', ''))

    c = Cartao.query.filter_by(usuario_id=user_id, cartao_id_ext=cartao_id).first()
    if not c:
        return jsonify({'status': 'erro', 'mensagem': 'Cartão não encontrado'}), 404

    try:
        c.nome = str(data.get('nome', c.nome)).strip()
        if not c.nome or len(c.nome) > 100:
            raise ValueError('O nome do cartão é obrigatório e deve ter até 100 caracteres.')
        c.limite = numero_nao_negativo(data.get('limite', c.limite), 'Limite')
        c.dia_vencimento = inteiro_no_intervalo(data.get('dia_vencimento', c.dia_vencimento), 'Dia de vencimento', 1, 31)
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400
    except Exception:
        db.session.rollback()
        app.logger.exception('Erro ao editar cartão')
        return jsonify({'status': 'erro', 'mensagem': 'Erro interno ao editar cartão.'}), 500

@app.route('/excluir_cartao', methods=['POST'])
def excluir_cartao():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401

    user_id = session['usuario_id']
    data = request.get_json() or {}
    cartao_id = str(data.get('id', ''))

    c = Cartao.query.filter_by(usuario_id=user_id, cartao_id_ext=cartao_id).first()
    if c:
        db.session.delete(c)
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    return jsonify({'status': 'erro', 'mensagem': 'Cartão não encontrado'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
