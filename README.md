# K-Financeiro

Aplicativo web de controle financeiro pessoal feito com Flask. Permite criar uma conta, registrar rendas e despesas mensais, acompanhar parcelas e administrar cartões.

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
- `DATABASE_URL`: URL interna de um banco PostgreSQL persistente do Render.

Importante: SQLite em `/tmp` não é persistente no Render. Sem `DATABASE_URL`, reinícios e novos deploys podem perder os dados. Depois de criar o PostgreSQL no painel do Render, copie a **Internal Database URL** para `DATABASE_URL` no serviço web.

O endpoint `GET /healthz` pode ser usado como caminho de verificação de saúde.

## Segurança e dados

- Senhas são armazenadas com hash seguro do Werkzeug.
- Cookies de sessão usam `HttpOnly`, `SameSite=Lax` e `Secure` no Render.
- Entradas financeiras e cartões são validados no servidor.
- Mensagens e dados inseridos pelo usuário são escapados antes de aparecerem no painel.

Nunca publique `.env`, `database.db` ou valores reais de `SECRET_KEY`.
