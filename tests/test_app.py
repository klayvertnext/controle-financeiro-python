import os
import unittest

os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['SECRET_KEY'] = 'test-secret-key-only-for-automated-tests'
os.environ.pop('MIGRATE_TO_NEON', None)
os.environ.pop('NEON_DATABASE_URL', None)

from werkzeug.security import generate_password_hash

from app import Cartao, Despesa, Usuario, app, db


class FinanceiroTestCase(unittest.TestCase):
    def setUp(self):
        app.config.update(TESTING=True, SESSION_COOKIE_SECURE=False)
        self.client = app.test_client()
        with app.app_context():
            db.session.remove()
            db.drop_all()
            db.create_all()

    def tearDown(self):
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def csrf(self):
        with self.client.session_transaction() as sessao:
            token = sessao.get('_csrf_token', 'csrf-token-de-teste')
            sessao['_csrf_token'] = token
        return token

    def criar_usuario_logado(self, nome='UsuarioTeste', email='usuario@example.com'):
        with app.app_context():
            usuario = Usuario(
                nome=nome,
                email=email,
                senha=generate_password_hash('senha-segura-123'),
            )
            db.session.add(usuario)
            db.session.commit()
            usuario_id = usuario.id
        with self.client.session_transaction() as sessao:
            sessao['usuario_id'] = usuario_id
            sessao['usuario_nome'] = nome
        return usuario_id

    @staticmethod
    def despesa(id_unico, parcela=1, total=1, categoria='Outros'):
        return {
            'idUnico': id_unico,
            'idCompra': 'compra-1',
            'descricao': f'Parcela {parcela}',
            'valorParcela': 25.50,
            'dataCompra': '2026-08-01',
            'tipo': 'Pix',
            'categoria': categoria,
            'cartao': '-',
            'parcelaAtual': parcela,
            'totalParcelas': total,
            'mesReferencia': f'2026-{8 + parcela - 1:02d}',
            'pago': False,
        }

    def test_healthcheck_e_csrf(self):
        self.assertEqual(self.client.get('/healthz').status_code, 200)
        self.criar_usuario_logado()
        self.assertEqual(self.client.get('/dashboard').status_code, 200)
        resposta = self.client.post('/api/rendas', json={'mes': '2026-08', 'salario': 1, 'extra': 0})
        self.assertEqual(resposta.status_code, 403)

    def test_cadastro_valida_email_e_senha(self):
        token = self.csrf()
        invalido = self.client.post('/cadastro', data={
            '_csrf_token': token,
            'nome': 'NovoUsuario',
            'email': 'email-invalido',
            'senha': 'senha-segura-123',
        })
        self.assertEqual(invalido.status_code, 200)
        self.assertIn('e-mail v', invalido.get_data(as_text=True))

        valido = self.client.post('/cadastro', data={
            '_csrf_token': token,
            'nome': 'NovoUsuario',
            'email': 'novo@example.com',
            'senha': 'senha-segura-123',
        })
        self.assertEqual(valido.status_code, 302)
        self.assertTrue(valido.headers['Location'].endswith('/dashboard'))
        with app.app_context():
            self.assertEqual(Usuario.query.count(), 1)

    def test_lote_de_parcelas_e_atomico(self):
        self.criar_usuario_logado()
        token = self.csrf()
        itens = [self.despesa(1001, 1, 2), self.despesa(1002, 2, 2, 'Categoria inexistente')]
        resposta = self.client.post(
            '/api/despesas/lote', json={'despesas': itens}, headers={'X-CSRF-Token': token}
        )
        self.assertEqual(resposta.status_code, 400)
        with app.app_context():
            self.assertEqual(Despesa.query.count(), 0)

        itens = [self.despesa(2001, 1, 3), self.despesa(2002, 2, 3), self.despesa(2003, 3, 3)]
        resposta = self.client.post(
            '/api/despesas/lote', json={'despesas': itens}, headers={'X-CSRF-Token': token}
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(resposta.get_json()['quantidade'], 3)
        with app.app_context():
            self.assertEqual(Despesa.query.count(), 3)

    def test_cartao_nao_aceita_nome_duplicado(self):
        self.criar_usuario_logado()
        token = self.csrf()
        payload = {
            'id': 'cartao-1',
            'nome': 'Cartão principal',
            'limite': 2500,
            'dia_fechamento': 5,
            'dia_vencimento': 12,
        }
        primeira = self.client.post('/cadastrar_cartao', json=payload, headers={'X-CSRF-Token': token})
        self.assertEqual(primeira.status_code, 200)
        payload['id'] = 'cartao-2'
        segunda = self.client.post('/cadastrar_cartao', json=payload, headers={'X-CSRF-Token': token})
        self.assertEqual(segunda.status_code, 409)
        with app.app_context():
            self.assertEqual(Cartao.query.count(), 1)

    def test_alteracao_de_senha_exige_confirmacao(self):
        self.criar_usuario_logado()
        token = self.csrf()
        resposta = self.client.post('/api/alterar_senha', json={
            'senha_atual': 'senha-segura-123',
            'nova_senha': 'outra-senha-segura-123',
            'confirmacao': 'valor-diferente',
        }, headers={'X-CSRF-Token': token})
        self.assertEqual(resposta.status_code, 400)
        self.assertIn('confirma', resposta.get_json()['mensagem'].lower())


if __name__ == '__main__':
    unittest.main()
