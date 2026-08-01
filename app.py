from datetime import datetime, timedelta
import logging
import os
import re
import secrets
import time

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, abort
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
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
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)

if os.environ.get('RENDER') and not os.environ.get('SECRET_KEY'):
    logging.warning('SECRET_KEY não configurada; defina uma chave secreta no Render.')

db = SQLAlchemy(app)
login_attempts = {}

def csrf_token():
    if '_csrf_token' not in session:
        session['_csrf_token'] = secrets.token_urlsafe(32)
    return session['_csrf_token']

app.jinja_env.globals['csrf_token'] = csrf_token

@app.before_request
def proteger_requisicoes():
    if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
        recebido = request.form.get('_csrf_token') or request.headers.get('X-CSRF-Token')
        esperado = session.get('_csrf_token')
        # Sessões antigas, abertas antes desta proteção, são aceitas apenas durante a migração.
        # Assim que qualquer página nova gera o token, todas as mutações passam a exigi-lo.
        if esperado and (not recebido or not secrets.compare_digest(esperado, recebido)):
            abort(403)

@app.after_request
def impedir_cache_financeiro(response):
    if session:
        response.headers['Cache-Control'] = 'no-store, private'
        response.headers['Pragma'] = 'no-cache'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['Referrer-Policy'] = 'same-origin'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

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
    salario = db.Column(db.Numeric(14, 2), default=0)
    extra = db.Column(db.Numeric(14, 2), default=0)
    __table_args__ = (db.UniqueConstraint('usuario_id', 'mes_referencia', name='uq_renda_usuario_mes'),)

class Despesa(db.Model):
    __tablename__ = 'despesas'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    id_unico = db.Column(db.BigInteger, nullable=False)
    id_compra = db.Column(db.String(50), nullable=True)
    descricao = db.Column(db.String(200), nullable=False)
    valor_parcela = db.Column(db.Numeric(14, 2), nullable=False)
    data_compra = db.Column(db.String(20), nullable=False)
    tipo = db.Column(db.String(30), nullable=False)
    categoria = db.Column(db.String(50), nullable=False, default='Outros')
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
    limite = db.Column(db.Numeric(14, 2), nullable=False)
    dia_fechamento = db.Column(db.Integer, nullable=False, default=1)
    dia_vencimento = db.Column(db.Integer, nullable=False)
    __table_args__ = (db.UniqueConstraint('usuario_id', 'cartao_id_ext', name='uq_cartao_usuario_ext'),)

class MetaFinanceira(db.Model):
    __tablename__ = 'metas_financeiras'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    titulo = db.Column(db.String(120), nullable=False)
    valor_alvo = db.Column(db.Numeric(14, 2), nullable=False)
    valor_atual = db.Column(db.Numeric(14, 2), default=0)

class Preferencia(db.Model):
    __tablename__ = 'preferencias'
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), unique=True, nullable=False)
    moeda = db.Column(db.String(10), default='BRL')
    tema = db.Column(db.String(10), default='dark')

with app.app_context():
    db.create_all()
    if db.engine.dialect.name == 'postgresql':
        db.session.execute(text("ALTER TABLE despesas ADD COLUMN IF NOT EXISTS categoria VARCHAR(50) DEFAULT 'Outros' NOT NULL"))
        db.session.execute(text("ALTER TABLE despesas ADD COLUMN IF NOT EXISTS id_compra VARCHAR(50)"))
        db.session.execute(text("UPDATE despesas SET id_compra = id_unico::text WHERE id_compra IS NULL"))
        db.session.execute(text("ALTER TABLE cartoes ADD COLUMN IF NOT EXISTS dia_fechamento INTEGER DEFAULT 1 NOT NULL"))
        for tabela, coluna in [('rendas', 'salario'), ('rendas', 'extra'), ('despesas', 'valor_parcela'),
                               ('cartoes', 'limite'), ('metas_financeiras', 'valor_alvo'), ('metas_financeiras', 'valor_atual')]:
            tipo_atual = db.session.execute(text("SELECT data_type FROM information_schema.columns WHERE table_schema='public' AND table_name=:t AND column_name=:c"), {'t': tabela, 'c': coluna}).scalar()
            if tipo_atual != 'numeric':
                db.session.execute(text(f"ALTER TABLE {tabela} ALTER COLUMN {coluna} TYPE NUMERIC(14,2) USING ROUND({coluna}::numeric, 2)"))
        db.session.commit()


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


@app.errorhandler(403)
def requisicao_sem_token(_erro):
    if request.path.startswith('/api/') or request.is_json:
        return jsonify({'status': 'erro', 'mensagem': 'A sessão expirou. Atualize a página e tente novamente.'}), 403
    return render_template('login.html', erro='A sessão expirou. Tente novamente.'), 403

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

        chave_tentativa = f"{request.remote_addr}:{identificador.lower()}"
        agora = time.time()
        tentativas = [t for t in login_attempts.get(chave_tentativa, []) if agora - t < 900]
        if len(tentativas) >= 8:
            return render_template('login.html', erro="Muitas tentativas. Aguarde 15 minutos e tente novamente."), 429

        try:
            # Busca pelo Nome de Usuário (respeitando maiúsculas) ou E-mail (minúsculas)
            user = Usuario.query.filter(
                (Usuario.nome == identificador) | 
                (Usuario.email == identificador.lower())
            ).first()
            
            if user and check_password_hash(user.senha, senha):
                login_attempts.pop(chave_tentativa, None)
                session.clear()
                session.permanent = True
                session['usuario_id'] = user.id
                session['usuario_nome'] = user.nome
                return redirect(url_for('dashboard'))
                
            tentativas.append(agora)
            login_attempts[chave_tentativa] = tentativas
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

        if len(nome) < 3 or len(nome) > 100:
            return render_template('cadastro.html', erro="O nome de usuário deve ter entre 3 e 100 caracteres.")
        if '@' not in email or len(email) > 120:
            return render_template('cadastro.html', erro="Informe um endereço de e-mail válido.")
        if len(senha) < 12:
            return render_template('cadastro.html', erro="A senha deve ter no mínimo 12 caracteres.")

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

            session.clear()
            session['usuario_id'] = novo_usuario.id
            session['usuario_nome'] = novo_usuario.nome
            session.permanent = True
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            return render_template('cadastro.html', erro="Erro interno ao realizar cadastro. Tente novamente.")
    
    return render_template('cadastro.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    response = redirect(url_for('login'))
    response.headers['Clear-Site-Data'] = '"cache", "cookies", "storage"'
    return response

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
            'salario': float(r.salario or 0),
            'extra': float(r.extra or 0)
        }

    despesas_list = []
    for d in user.despesas:
        despesas_list.append({
            'idUnico': d.id_unico,
            'idCompra': d.id_compra or str(d.id_unico),
            'descricao': d.descricao,
            'valorParcela': float(d.valor_parcela or 0),
            'dataCompra': d.data_compra,
            'tipo': d.tipo,
            'categoria': d.categoria or 'Outros',
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
            'limite': float(c.limite or 0),
            'dia_fechamento': c.dia_fechamento,
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
                'categoria': str(item.get('categoria', 'Outros')).strip()[:50] or 'Outros',
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

@app.route('/api/rendas', methods=['POST'])
def salvar_renda():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro'}), 401
    data = request.get_json(silent=True) or {}
    mes = str(data.get('mes', ''))
    if not mes_valido(mes):
        return jsonify({'status': 'erro', 'mensagem': 'Mês inválido.'}), 400
    try:
        renda = Renda.query.filter_by(usuario_id=session['usuario_id'], mes_referencia=mes).first()
        if not renda:
            renda = Renda(usuario_id=session['usuario_id'], mes_referencia=mes)
            db.session.add(renda)
        renda.salario = numero_nao_negativo(data.get('salario', 0), 'Salário')
        renda.extra = numero_nao_negativo(data.get('extra', 0), 'Renda extra')
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    except ValueError as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400

@app.route('/api/despesas', methods=['POST'])
def criar_despesa():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro'}), 401
    data = request.get_json(silent=True) or {}
    try:
        valor = numero_nao_negativo(data.get('valorParcela'), 'Valor')
        if valor <= 0:
            raise ValueError('O valor deve ser maior que zero.')
        descricao = str(data.get('descricao', '')).strip()[:200]
        if not descricao:
            raise ValueError('Informe a descrição.')
        mes = str(data.get('mesReferencia', ''))
        if not mes_valido(mes):
            raise ValueError('Mês inválido.')
        data_compra = str(data.get('dataCompra', ''))
        datetime.strptime(data_compra, '%Y-%m-%d')
        tipo = str(data.get('tipo', ''))
        if tipo not in {'Cartao', 'Débito', 'Pix', 'Dinheiro'}:
            raise ValueError('Pagamento inválido.')
        despesa = Despesa(
            usuario_id=session['usuario_id'], id_unico=int(data.get('idUnico')),
            id_compra=str(data.get('idCompra') or data.get('idUnico'))[:50], descricao=descricao,
            valor_parcela=valor, data_compra=data_compra, tipo=tipo,
            categoria=str(data.get('categoria', 'Outros')).strip()[:50] or 'Outros',
            cartao=(str(data.get('cartao', '-')).strip()[:100] or '-') if tipo == 'Cartao' else '-',
            parcela_atual=inteiro_no_intervalo(data.get('parcelaAtual', 1), 'Parcela', 1, 360),
            total_parcelas=inteiro_no_intervalo(data.get('totalParcelas', 1), 'Parcelas', 1, 360),
            mes_referencia=mes, pago=bool(data.get('pago', False)))
        db.session.add(despesa)
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400

@app.route('/api/despesas/<int:id_unico>', methods=['PUT', 'DELETE'])
def alterar_despesa(id_unico):
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro'}), 401
    despesa = Despesa.query.filter_by(usuario_id=session['usuario_id'], id_unico=id_unico).first_or_404()
    if request.method == 'DELETE':
        if request.args.get('grupo') == 'true':
            Despesa.query.filter_by(usuario_id=session['usuario_id'], id_compra=despesa.id_compra).delete()
        else:
            db.session.delete(despesa)
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    data = request.get_json(silent=True) or {}
    if 'pago' in data:
        despesa.pago = bool(data['pago'])
    if 'descricao' in data:
        descricao = str(data['descricao']).strip()[:200]
        if not descricao:
            return jsonify({'status': 'erro', 'mensagem': 'Descrição obrigatória.'}), 400
        despesa.descricao = descricao
    if 'categoria' in data:
        despesa.categoria = str(data['categoria']).strip()[:50] or 'Outros'
    if 'valorParcela' in data:
        valor = numero_nao_negativo(data['valorParcela'], 'Valor')
        if valor <= 0:
            return jsonify({'status': 'erro', 'mensagem': 'O valor deve ser maior que zero.'}), 400
        despesa.valor_parcela = valor
    db.session.commit()
    return jsonify({'status': 'sucesso'})

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
        dia_fechamento = inteiro_no_intervalo(data.get('dia_fechamento', 1), 'Dia de fechamento', 1, 31)
        cartao_id_ext = str(data.get('id', 'c_' + str(os.urandom(4).hex())))
        if len(cartao_id_ext) > 50:
            raise ValueError('Identificador do cartão inválido.')
        novo_c = Cartao(
            usuario_id=user_id,
            cartao_id_ext=cartao_id_ext,
            nome=nome_cartao,
            limite=limite,
            dia_fechamento=dia_fechamento,
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
        nome_anterior = c.nome
        c.nome = str(data.get('nome', c.nome)).strip()
        if not c.nome or len(c.nome) > 100:
            raise ValueError('O nome do cartão é obrigatório e deve ter até 100 caracteres.')
        c.limite = numero_nao_negativo(data.get('limite', c.limite), 'Limite')
        c.dia_vencimento = inteiro_no_intervalo(data.get('dia_vencimento', c.dia_vencimento), 'Dia de vencimento', 1, 31)
        c.dia_fechamento = inteiro_no_intervalo(data.get('dia_fechamento', c.dia_fechamento), 'Dia de fechamento', 1, 31)
        if c.nome != nome_anterior:
            Despesa.query.filter_by(usuario_id=user_id, cartao=nome_anterior).update({'cartao': c.nome})
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

@app.route('/api/metas', methods=['GET', 'POST'])
def api_metas():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro', 'mensagem': 'Não autorizado'}), 401
    user_id = session['usuario_id']
    if request.method == 'GET':
        metas = MetaFinanceira.query.filter_by(usuario_id=user_id).order_by(MetaFinanceira.id.desc()).all()
        return jsonify({'status': 'sucesso', 'metas': [
            {'id': m.id, 'titulo': m.titulo, 'valor_alvo': float(m.valor_alvo or 0), 'valor_atual': float(m.valor_atual or 0)}
            for m in metas
        ]})
    data = request.get_json(silent=True) or {}
    try:
        titulo = str(data.get('titulo', '')).strip()[:120]
        if not titulo:
            raise ValueError('Informe o nome da meta.')
        alvo = numero_nao_negativo(data.get('valor_alvo'), 'Valor desejado')
        if alvo <= 0:
            raise ValueError('O valor desejado deve ser maior que zero.')
        meta = MetaFinanceira(usuario_id=user_id, titulo=titulo, valor_alvo=alvo,
                              valor_atual=numero_nao_negativo(data.get('valor_atual', 0), 'Valor acumulado'))
        db.session.add(meta)
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400

@app.route('/api/metas/<int:meta_id>', methods=['PUT', 'DELETE'])
def alterar_meta(meta_id):
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro'}), 401
    meta = MetaFinanceira.query.filter_by(id=meta_id, usuario_id=session['usuario_id']).first_or_404()
    try:
        if request.method == 'DELETE':
            db.session.delete(meta)
        else:
            data = request.get_json(silent=True) or {}
            if 'valor_atual' in data:
                meta.valor_atual = numero_nao_negativo(data.get('valor_atual'), 'Valor acumulado')
            if 'valor_alvo' in data:
                alvo = numero_nao_negativo(data.get('valor_alvo'), 'Valor desejado')
                if alvo <= 0:
                    raise ValueError('O valor desejado deve ser maior que zero.')
                meta.valor_alvo = alvo
            if 'titulo' in data:
                titulo = str(data.get('titulo', '')).strip()[:120]
                if not titulo:
                    raise ValueError('Informe o nome da meta.')
                meta.titulo = titulo
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400

@app.route('/api/configuracoes', methods=['GET', 'POST'])
def configuracoes():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro'}), 401
    user_id = session['usuario_id']
    pref = Preferencia.query.filter_by(usuario_id=user_id).first()
    if not pref:
        pref = Preferencia(usuario_id=user_id)
        db.session.add(pref)
        db.session.commit()
    if request.method == 'GET':
        user = db.session.get(Usuario, user_id)
        return jsonify({'status': 'sucesso', 'nome': user.nome, 'email': user.email,
                        'moeda': pref.moeda, 'tema': pref.tema})
    data = request.get_json(silent=True) or {}
    if data.get('moeda') in {'BRL', 'USD', 'EUR'}:
        pref.moeda = data['moeda']
    if data.get('tema') in {'light', 'dark'}:
        pref.tema = data['tema']
    db.session.commit()
    return jsonify({'status': 'sucesso'})

@app.route('/api/exportar')
def exportar_dados():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro'}), 401
    user = db.session.get(Usuario, session['usuario_id'])
    pref = Preferencia.query.filter_by(usuario_id=user.id).first()
    payload = {
        'usuario': {'nome': user.nome, 'email': user.email},
        'rendas': [{'mes': r.mes_referencia, 'salario': float(r.salario or 0), 'extra': float(r.extra or 0)} for r in user.rendas],
        'despesas': [{'descricao': d.descricao, 'valorParcela': float(d.valor_parcela or 0), 'dataCompra': d.data_compra,
                      'categoria': d.categoria or 'Outros', 'tipo': d.tipo, 'pago': d.pago, 'cartao': d.cartao,
                      'parcelaAtual': d.parcela_atual, 'totalParcelas': d.total_parcelas,
                      'mesReferencia': d.mes_referencia, 'idCompra': d.id_compra} for d in user.despesas],
        'cartoes': [{'nome': c.nome, 'limite': float(c.limite or 0), 'fechamento': c.dia_fechamento,
                     'vencimento': c.dia_vencimento} for c in user.cartoes],
        'metas': [{'titulo': m.titulo, 'valor_alvo': float(m.valor_alvo or 0), 'valor_atual': float(m.valor_atual or 0)}
                  for m in MetaFinanceira.query.filter_by(usuario_id=user.id).all()],
        'preferencias': {'moeda': pref.moeda if pref else 'BRL', 'tema': pref.tema if pref else 'dark'}
    }
    response = jsonify(payload)
    response.headers['Content-Disposition'] = 'attachment; filename=controle-financeiro.json'
    return response

@app.route('/api/alterar_senha', methods=['POST'])
def alterar_senha():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro'}), 401
    data = request.get_json(silent=True) or {}
    user = db.session.get(Usuario, session['usuario_id'])
    if not check_password_hash(user.senha, str(data.get('senha_atual', ''))):
        return jsonify({'status': 'erro', 'mensagem': 'Senha atual incorreta.'}), 400
    nova = str(data.get('nova_senha', ''))
    if len(nova) < 12:
        return jsonify({'status': 'erro', 'mensagem': 'A nova senha deve ter no mínimo 12 caracteres.'}), 400
    user.senha = generate_password_hash(nova)
    db.session.commit()
    return jsonify({'status': 'sucesso'})

@app.route('/api/importar', methods=['POST'])
def importar_dados():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro'}), 401
    data = request.get_json(silent=True) or {}
    listas = ('rendas', 'despesas', 'cartoes', 'metas')
    if any(not isinstance(data.get(chave, []), list) for chave in listas):
        return jsonify({'status': 'erro', 'mensagem': 'Arquivo incompatível.'}), 400
    if (len(data.get('despesas', [])) > 5000 or len(data.get('rendas', [])) > 600 or
            len(data.get('cartoes', [])) > 100 or len(data.get('metas', [])) > 500):
        return jsonify({'status': 'erro', 'mensagem': 'Arquivo excede o limite de registros.'}), 400
    user_id = session['usuario_id']
    try:
        for item in data.get('rendas', []):
            if not isinstance(item, dict):
                continue
            mes = str(item.get('mes', ''))
            if not mes_valido(mes):
                continue
            renda = Renda.query.filter_by(usuario_id=user_id, mes_referencia=mes).first() or Renda(usuario_id=user_id, mes_referencia=mes)
            renda.salario = numero_nao_negativo(item.get('salario', 0), 'Salário')
            renda.extra = numero_nao_negativo(item.get('extra', 0), 'Extra')
            db.session.add(renda)
        for indice, item in enumerate(data.get('despesas', [])):
            if not isinstance(item, dict):
                continue
            valor = numero_nao_negativo(item.get('valorParcela', item.get('valor', 0)), 'Valor')
            mes_referencia = str(item.get('mesReferencia', ''))
            if valor <= 0 or not mes_valido(mes_referencia):
                continue
            parcela_atual = inteiro_no_intervalo(item.get('parcelaAtual', 1), 'Parcela atual', 1, 360)
            total_parcelas = inteiro_no_intervalo(item.get('totalParcelas', 1), 'Total de parcelas', 1, 360)
            if parcela_atual > total_parcelas:
                continue
            id_compra = str(item.get('idCompra') or '')[:50]
            if id_compra and Despesa.query.filter_by(usuario_id=user_id, id_compra=id_compra,
                    parcela_atual=parcela_atual, mes_referencia=mes_referencia).first():
                continue
            novo_id = int(time.time() * 1000000) + indice
            db.session.add(Despesa(usuario_id=user_id, id_unico=novo_id,
                id_compra=id_compra or str(novo_id), descricao=str(item.get('descricao', 'Importado')).strip()[:200] or 'Importado',
                valor_parcela=valor, data_compra=str(item.get('dataCompra', datetime.now().strftime('%Y-%m-%d')))[:20],
                tipo=str(item.get('tipo', 'Pix')) if item.get('tipo') in {'Cartao','Débito','Pix','Dinheiro'} else 'Pix',
                categoria=str(item.get('categoria', 'Outros'))[:50], cartao=str(item.get('cartao', '-'))[:100],
                parcela_atual=parcela_atual, total_parcelas=total_parcelas,
                mes_referencia=mes_referencia, pago=bool(item.get('pago', False))))
        for item in data.get('cartoes', []):
            if not isinstance(item, dict):
                continue
            nome = str(item.get('nome', '')).strip()[:100]
            if not nome:
                continue
            cartao = Cartao.query.filter_by(usuario_id=user_id, nome=nome).first()
            if not cartao:
                cartao = Cartao(usuario_id=user_id, cartao_id_ext='import_' + secrets.token_hex(8), nome=nome)
                db.session.add(cartao)
            cartao.limite = numero_nao_negativo(item.get('limite', 0), 'Limite')
            cartao.dia_fechamento = inteiro_no_intervalo(item.get('fechamento', 1), 'Dia de fechamento', 1, 31)
            cartao.dia_vencimento = inteiro_no_intervalo(item.get('vencimento', 1), 'Dia de vencimento', 1, 31)
        for item in data.get('metas', []):
            if not isinstance(item, dict):
                continue
            titulo = str(item.get('titulo', '')).strip()[:120]
            if not titulo:
                continue
            alvo = numero_nao_negativo(item.get('valor_alvo', 0), 'Valor desejado')
            if alvo <= 0:
                continue
            meta = MetaFinanceira.query.filter_by(usuario_id=user_id, titulo=titulo).first()
            if not meta:
                meta = MetaFinanceira(usuario_id=user_id, titulo=titulo)
                db.session.add(meta)
            meta.valor_alvo = alvo
            meta.valor_atual = numero_nao_negativo(item.get('valor_atual', 0), 'Valor acumulado')
        preferencias = data.get('preferencias', {})
        if isinstance(preferencias, dict):
            pref = Preferencia.query.filter_by(usuario_id=user_id).first()
            if not pref:
                pref = Preferencia(usuario_id=user_id)
                db.session.add(pref)
            if preferencias.get('moeda') in {'BRL', 'USD', 'EUR'}:
                pref.moeda = preferencias['moeda']
            if preferencias.get('tema') in {'light', 'dark'}:
                pref.tema = preferencias['tema']
        db.session.commit()
        return jsonify({'status': 'sucesso'})
    except (ValueError, TypeError) as e:
        db.session.rollback()
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 400

@app.route('/api/excluir_conta', methods=['POST'])
def excluir_conta():
    if 'usuario_id' not in session:
        return jsonify({'status': 'erro'}), 401
    user = db.session.get(Usuario, session['usuario_id'])
    data = request.get_json(silent=True) or {}
    if not check_password_hash(user.senha, str(data.get('senha', ''))):
        return jsonify({'status': 'erro', 'mensagem': 'Senha incorreta.'}), 400
    MetaFinanceira.query.filter_by(usuario_id=user.id).delete()
    Preferencia.query.filter_by(usuario_id=user.id).delete()
    db.session.delete(user)
    db.session.commit()
    session.clear()
    return jsonify({'status': 'sucesso'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
