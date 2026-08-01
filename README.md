# K-Financeiro

Aplicativo web de controle financeiro pessoal feito com Flask. Permite criar uma conta, registrar rendas e despesas mensais, acompanhar parcelas, administrar cartões e metas, comparar os últimos meses e manter um backup dos dados.

## Executar localmente

Requer Python 3.11 ou superior.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Abra `http://localhost:5000`. Sem `DATABASE_URL`, os dados ficam em `database.db` apenas para desenvolvimento local.

## Configuração no Render

O comando de inicialização continua sendo o definido no `Procfile`:

```text
gunicorn app:app
```

Configure estas variáveis no serviço web:

- `SECRET_KEY`: uma sequência longa, aleatória e privada.
- `DATABASE_URL`: URL de conexão de um banco PostgreSQL persistente, como o Neon.

Importante: SQLite no disco temporário não é persistente no Render. Sem `DATABASE_URL`, reinícios e novos deploys podem perder os dados. Use a URL com SSL fornecida pelo PostgreSQL e mantenha essa variável somente no painel do Render.

O endpoint `GET /healthz` pode ser usado como caminho de verificação de saúde.

### Migração controlada para outro PostgreSQL

Para copiar todos os dados do banco definido em `DATABASE_URL` para um banco vazio, configure temporariamente `MIGRATE_TO_NEON=1` e `NEON_DATABASE_URL` com a conexão de destino. Na inicialização, o aplicativo recria as tabelas no destino, copia todos os registros em uma transação e confere as contagens antes de concluir. Depois da confirmação, aponte `DATABASE_URL` para o destino e remova as duas variáveis temporárias.

Mantenha o banco de origem por alguns dias como possibilidade de retorno e faça um backup antes de apagá-lo.

## Testes

```bash
python -m unittest discover -s tests -v
```

Os testes cobrem autenticação/CSRF, cadastro, parcelas atômicas, cartões duplicados e confirmação de senha. Eles também são executados automaticamente no GitHub.

## Segurança e dados

- Senhas são armazenadas com hash seguro do Werkzeug.
- Cookies de sessão usam `HttpOnly`, `SameSite=Lax` e `Secure` no Render.
- Formulários e APIs com alteração de dados usam proteção CSRF.
- O login limita tentativas repetidas e a sessão autenticada expira após oito horas.
- Entradas financeiras e cartões são validados no servidor.
- Valores monetários usam precisão decimal no PostgreSQL.
- Mensagens e dados inseridos pelo usuário são escapados antes de aparecerem no painel.
- A área de configurações permite exportar e restaurar receitas, despesas, cartões, metas e preferências.

Nunca publique `.env`, `database.db` ou valores reais de `SECRET_KEY`.
