import customtkinter as ctk
from tkinter import messagebox, ttk
import json
import os
import hashlib
from datetime import datetime
from tkcalendar import DateEntry

import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# Desativa o escalonamento automático de DPI para evitar conflitos no Python
ctk.deactivate_automatic_dpi_awareness()

# Configurações de tema
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

ARQUIVO_USUARIOS = "usuarios.json"
ARQUIVO_DADOS = "dados_financeiros.json"

# Paleta de Cores Premium (Slate Dark & Neon Accents)
COR_BG_PRINCIPAL = "#0F172A"
COR_BG_CARD = "#1E293B"
COR_AZUL_BEBE = "#0284C7"
COR_AZUL_HOVER = "#0369A1"
COR_VERDE = "#10B981"
COR_VERMELHO = "#EF4444"
COR_ROXO = "#A855F7"
COR_AMARELO_ELEGANTE = "#D97706"
COR_CINZA_TEXTO = "#94A3B8"


def hash_senha(senha):
    return hashlib.sha256(senha.encode()).hexdigest()


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


# =========================================================
# TELA DE LOGIN
# =========================================================
class TelaLogin(ctk.CTkFrame):
    def __init__(self, parent, on_login_sucesso, on_ir_para_cadastro):
        super().__init__(parent, fg_color=COR_BG_PRINCIPAL)
        self.on_login_sucesso = on_login_sucesso
        self.on_ir_para_cadastro = on_ir_para_cadastro
        self.usuarios = carregar_json(ARQUIVO_USUARIOS, {})

        self.pack(expand=True, fill="both")

        f_card = ctk.CTkFrame(
            self, width=360, height=440, corner_radius=16, 
            fg_color=COR_BG_CARD, border_width=1, border_color="#334155"
        )
        f_card.place(relx=0.5, rely=0.5, anchor="center")
        f_card.pack_propagate(False)

        lbl_logo = ctk.CTkLabel(
            f_card, text="K$", font=ctk.CTkFont(size=56, weight="bold"), text_color=COR_AZUL_BEBE
        )
        lbl_logo.pack(pady=(35, 5))

        lbl_sub = ctk.CTkLabel(
            f_card, text="Controle Financeiro Professional", font=ctk.CTkFont(size=13), text_color=COR_CINZA_TEXTO
        )
        lbl_sub.pack(pady=(0, 25))

        self.entry_user = ctk.CTkEntry(f_card, placeholder_text="Usuário", width=280, height=42, corner_radius=8)
        self.entry_user.pack(pady=8)

        self.entry_pass = ctk.CTkEntry(f_card, placeholder_text="Senha", show="*", width=280, height=42, corner_radius=8)
        self.entry_pass.pack(pady=8)

        self.entry_user.bind("<Return>", lambda event: self.fazer_login())
        self.entry_pass.bind("<Return>", lambda event: self.fazer_login())

        self.btn_entrar = ctk.CTkButton(
            f_card, text="Acessar Conta", command=self.fazer_login, fg_color=COR_AZUL_BEBE,
            hover_color=COR_AZUL_HOVER, width=280, height=42, corner_radius=8, font=ctk.CTkFont(weight="bold")
        )
        self.btn_entrar.pack(pady=(20, 10))

        self.btn_criar_conta = ctk.CTkButton(
            f_card, text="Criar nova conta", command=self.on_ir_para_cadastro,
            fg_color="transparent", text_color=COR_VERMELHO,
            hover_color=("#1e293b", "#334155"), font=ctk.CTkFont(size=13, weight="bold", underline=True)
        )
        self.btn_criar_conta.pack(pady=5)

    def fazer_login(self):
        usuario = self.entry_user.get().strip().lower()
        senha = self.entry_pass.get().strip()

        if not usuario or not senha:
            messagebox.showwarning("Atenção", "Por favor, preencha o usuário e a senha!")
            return

        if usuario in self.usuarios and self.usuarios[usuario] == hash_senha(senha):
            self.on_login_sucesso(usuario)
        else:
            messagebox.showerror("Erro de Acesso", "Usuário ou senha incorretos.")


# =========================================================
# TELA DE CADASTRO
# =========================================================
class TelaCadastro(ctk.CTkFrame):
    def __init__(self, parent, on_cadastro_sucesso, on_voltar_login):
        super().__init__(parent, fg_color=COR_BG_PRINCIPAL)
        self.on_cadastro_sucesso = on_cadastro_sucesso
        self.on_voltar_login = on_voltar_login
        self.usuarios = carregar_json(ARQUIVO_USUARIOS, {})

        self.pack(expand=True, fill="both")

        f_card = ctk.CTkFrame(
            self, width=380, height=520, corner_radius=16, 
            fg_color=COR_BG_CARD, border_width=1, border_color="#334155"
        )
        f_card.place(relx=0.5, rely=0.5, anchor="center")
        f_card.pack_propagate(False)

        lbl_logo = ctk.CTkLabel(
            f_card, text="K$", font=ctk.CTkFont(size=42, weight="bold"), text_color=COR_AZUL_BEBE
        )
        lbl_logo.pack(pady=(20, 2))

        lbl_titulo = ctk.CTkLabel(
            f_card, text="Criar Nova Conta", font=ctk.CTkFont(size=18, weight="bold")
        )
        lbl_titulo.pack(pady=(0, 8))

        lbl_regras = ctk.CTkLabel(
            f_card, 
            text="🔒 Requisitos de Segurança:\n• Usuário: 1 maiúscula + 1 número\n• Senha: mín. 7 caracteres",
            font=ctk.CTkFont(size=11), text_color=COR_CINZA_TEXTO, justify="center"
        )
        lbl_regras.pack(pady=(0, 15))

        self.entry_nome = ctk.CTkEntry(f_card, placeholder_text="Usuário (ex: Klayvert1)", width=290, height=40, corner_radius=8)
        self.entry_nome.pack(pady=6)

        self.entry_senha = ctk.CTkEntry(f_card, placeholder_text="Senha", show="*", width=290, height=40, corner_radius=8)
        self.entry_senha.pack(pady=6)

        self.entry_confirma_senha = ctk.CTkEntry(f_card, placeholder_text="Confirme a senha", show="*", width=290, height=40, corner_radius=8)
        self.entry_confirma_senha.pack(pady=6)

        self.entry_nome.bind("<Return>", lambda event: self.realizar_cadastro())
        self.entry_senha.bind("<Return>", lambda event: self.realizar_cadastro())
        self.entry_confirma_senha.bind("<Return>", lambda event: self.realizar_cadastro())

        self.btn_cadastrar = ctk.CTkButton(
            f_card, text="Cadastrar e Entrar", command=self.realizar_cadastro,
            fg_color=COR_AZUL_BEBE, hover_color=COR_AZUL_HOVER,
            width=290, height=40, corner_radius=8, font=ctk.CTkFont(weight="bold")
        )
        self.btn_cadastrar.pack(pady=(15, 8))

        self.btn_voltar = ctk.CTkButton(
            f_card, text="Voltar ao Login", command=self.on_voltar_login,
            fg_color="transparent", text_color="gray", width=290
        )
        self.btn_voltar.pack(pady=5)

    def realizar_cadastro(self):
        nome_usuario = self.entry_nome.get().strip()
        senha = self.entry_senha.get().strip()
        confirma_senha = self.entry_confirma_senha.get().strip()

        if not nome_usuario or not senha or not confirma_senha:
            messagebox.showwarning("Atenção", "Preencha todos os campos do cadastro!")
            return

        usuario_chave = nome_usuario.lower()
        if usuario_chave in self.usuarios:
            messagebox.showwarning("Usuário Já Existe", f"O nome de usuário '{nome_usuario}' já está cadastrado!")
            return

        tem_maiuscula = any(char.isupper() for char in nome_usuario)
        tem_numero = any(char.isdigit() for char in nome_usuario)

        if not tem_maiuscula or not tem_numero:
            messagebox.showerror(
                "Segurança do Usuário", 
                "O Nome de Usuário precisa conter pelo menos:\n• 1 Letra Maiúscula (A-Z)\n• 1 Número (0-9)\n\nExemplo: Klayvert1"
            )
            return

        if len(senha) < 7:
            messagebox.showerror("Segurança da Senha", "A senha deve ter no mínimo 7 caracteres.")
            return

        if senha != confirma_senha:
            messagebox.showerror("Erro de Confirmação", "As senhas não são iguais!")
            return

        self.usuarios[usuario_chave] = hash_senha(senha)
        salvar_json(ARQUIVO_USUARIOS, self.usuarios)

        messagebox.showinfo("Sucesso!", f"Conta para '{nome_usuario}' criada com sucesso!")
        self.on_cadastro_sucesso(usuario_chave)


# =========================================================
# PAINEL PRINCIPAL DO APLICATIVO
# =========================================================
class PainelPrincipal(ctk.CTkFrame):
    def __init__(self, parent, usuario_atual, on_sair):
        super().__init__(parent, fg_color=COR_BG_PRINCIPAL)
        self.usuario_atual = usuario_atual
        self.on_sair = on_sair
        self.parent = parent
        
        self.pack(expand=True, fill="both")

        todos_dados = carregar_json(ARQUIVO_DADOS, {})
        self.dados = todos_dados.get(self.usuario_atual, {
            "salario": 0.0,
            "renda_extra": 0.0,
            "gastos_aleatorios": 0.0,
            "cartoes": [],
            "saidas": []
        })

        self.criar_header()
        self.criar_sistema_abas()

        # Atalhos do teclado para mudar de abas com as setas
        self.parent.bind("<Left>", lambda e: self.tabview.set("📊 Dashboard & Rendas"))
        self.parent.bind("<Right>", lambda e: self.tabview.set("💳 Cartões & Saídas"))

    def salvar_dados(self):
        todos_dados = carregar_json(ARQUIVO_DADOS, {})
        todos_dados[self.usuario_atual] = self.dados
        salvar_json(ARQUIVO_DADOS, todos_dados)

    def criar_header(self):
        f_header = ctk.CTkFrame(self, fg_color=COR_BG_CARD, height=65, corner_radius=0)
        f_header.pack(fill="x", side="top")

        lbl_logo = ctk.CTkLabel(f_header, text="K$", font=ctk.CTkFont(size=28, weight="bold"), text_color=COR_AZUL_BEBE)
        lbl_logo.pack(side="left", padx=25)

        lbl_boas_vindas = ctk.CTkLabel(
            f_header, text=f"Olá, {self.usuario_atual.capitalize()} 👋", font=ctk.CTkFont(size=16, weight="bold")
        )
        lbl_boas_vindas.pack(side="left", padx=5)

        btn_sair = ctk.CTkButton(
            f_header, text="Sair", width=70, height=32, fg_color="#dc2626", hover_color="#b91c1c",
            corner_radius=6, command=self.on_sair, font=ctk.CTkFont(size=12, weight="bold")
        )
        btn_sair.pack(side="right", padx=25)

    def criar_sistema_abas(self):
        self.tabview = ctk.CTkTabview(self, corner_radius=12, fg_color=COR_BG_PRINCIPAL)
        self.tabview.pack(expand=True, fill="both", padx=15, pady=10)

        self.tab_visao_geral = self.tabview.add("📊 Dashboard & Rendas")
        self.tab_gastos = self.tabview.add("💳 Cartões & Saídas")

        self.criar_conteudo_visao_geral(self.tab_visao_geral)
        self.criar_conteudo_cartoes_saidas(self.tab_gastos)

    def limpar_ao_clicar(self, event, entry):
        valor = entry.get().strip()
        if valor in ["0.00", "0.0", "0"]:
            entry.delete(0, "end")

    def recarregar_se_vazio(self, event, entry, valor_padrao):
        if not entry.get().strip():
            entry.insert(0, f"{valor_padrao:.2f}")

    # -----------------------------------------------------
    # ABA 1: DASHBOARD & RENDAS
    # -----------------------------------------------------
    def criar_conteudo_visao_geral(self, aba):
        scroll_frame = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        scroll_frame.pack(expand=True, fill="both")

        f_inputs = ctk.CTkFrame(scroll_frame, corner_radius=14, border_width=1, border_color="#334155", fg_color=COR_BG_CARD)
        f_inputs.pack(fill="x", pady=10, padx=2)

        f_date = ctk.CTkFrame(f_inputs, fg_color="#0F172A", corner_radius=10, border_width=1, border_color=COR_AZUL_BEBE)
        f_date.pack(side="left", padx=15, pady=15)
        
        lbl_dt = ctk.CTkLabel(f_date, text="📅 DATA DO LANÇAMENTO", font=ctk.CTkFont(size=10, weight="bold"), text_color=COR_AZUL_BEBE)
        lbl_dt.pack(anchor="w", padx=12, pady=(8, 2))

        self.cal_entry = DateEntry(
            f_date, width=12, background='#0284C7', foreground='white',
            bordercolor='#334155', headersbackground='#0369A1',
            date_pattern='dd/mm/yyyy', font=("Helvetica", 10, "bold")
        )
        self.cal_entry.pack(padx=12, pady=(0, 10), ipady=2)

        f_sal = ctk.CTkFrame(f_inputs, fg_color="transparent")
        f_sal.pack(side="left", expand=True, fill="x", padx=10, pady=15)
        ctk.CTkLabel(f_sal, text="💼 Salário (R$):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        
        val_salario = self.dados.get('salario', 0.0)
        self.ent_salario = ctk.CTkEntry(f_sal, height=38, placeholder_text="0.00", corner_radius=8)
        self.ent_salario.insert(0, f"{val_salario:.2f}")
        self.ent_salario.bind("<FocusIn>", lambda event: self.limpar_ao_clicar(event, self.ent_salario))
        self.ent_salario.bind("<FocusOut>", lambda event: self.recarregar_se_vazio(event, self.ent_salario, self.dados.get('salario', 0.0)))
        self.ent_salario.bind("<Return>", lambda event: self.salvar_rendas())
        self.ent_salario.pack(fill="x")

        f_ext = ctk.CTkFrame(f_inputs, fg_color="transparent")
        f_ext.pack(side="left", expand=True, fill="x", padx=10, pady=15)
        ctk.CTkLabel(f_ext, text="🚀 Renda Extra (R$):", font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w", pady=(0, 4))
        
        val_extra = self.dados.get('renda_extra', 0.0)
        self.ent_extra = ctk.CTkEntry(f_ext, height=38, placeholder_text="0.00", corner_radius=8)
        self.ent_extra.insert(0, f"{val_extra:.2f}")
        self.ent_extra.bind("<FocusIn>", lambda event: self.limpar_ao_clicar(event, self.ent_extra))
        self.ent_extra.bind("<FocusOut>", lambda event: self.recarregar_se_vazio(event, self.ent_extra, self.dados.get('renda_extra', 0.0)))
        self.ent_extra.bind("<Return>", lambda event: self.salvar_rendas())
        self.ent_extra.pack(fill="x")

        f_btn = ctk.CTkFrame(f_inputs, fg_color="transparent")
        f_btn.pack(side="left", padx=15, pady=15)
        
        self.lbl_status_salvar = ctk.CTkLabel(f_btn, text="", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_status_salvar.pack(anchor="w", pady=(0, 2))

        btn_salvar = ctk.CTkButton(
            f_btn, text="➕ Adicionar", fg_color=COR_AZUL_BEBE, hover_color=COR_AZUL_HOVER,
            command=self.salvar_rendas, font=ctk.CTkFont(weight="bold"), height=38, corner_radius=8
        )
        btn_salvar.pack()

        self.f_cards = ctk.CTkFrame(scroll_frame, fg_color="transparent")
        self.f_cards.pack(fill="x", pady=10)

        self.f_grafico = ctk.CTkFrame(scroll_frame, height=360, corner_radius=14, border_width=1, border_color="#334155", fg_color=COR_BG_CARD)
        self.f_grafico.pack(fill="x", pady=10, padx=2)
        self.f_grafico.pack_propagate(False)

        self.atualizar_cards()

    def salvar_rendas(self):
        try:
            txt_sal = self.ent_salario.get().strip().replace(",", ".")
            txt_ext = self.ent_extra.get().strip().replace(",", ".")

            val_salario = float(txt_sal) if txt_sal else 0.0
            val_extra = float(txt_ext) if txt_ext else 0.0

            if val_salario < 0 or val_extra < 0:
                messagebox.showwarning("Atenção", "Os valores de renda não podem ser negativos!")
                return

            self.dados["salario"] = val_salario
            self.dados["renda_extra"] = val_extra
            self.salvar_dados()
            self.atualizar_cards()

            self.lbl_status_salvar.configure(text="⏳ Gravando...", text_color=COR_AZUL_BEBE)
            self.after(300, self.mostrar_check_sucesso)

        except ValueError:
            messagebox.showerror("Erro", "Por favor, digite apenas números válidos (ex: 2500.00).")

    def mostrar_check_sucesso(self):
        self.lbl_status_salvar.configure(text="✅ Salvo!", text_color=COR_VERDE)
        self.after(1800, lambda: self.lbl_status_salvar.configure(text=""))

    def criar_card_estilizado(self, parent, titulo, valor, cor_destaque):
        card = ctk.CTkFrame(parent, corner_radius=12, border_width=1, border_color="#334155", fg_color=COR_BG_CARD)
        card.pack(side="left", expand=True, fill="both", padx=5)

        f_indicador = ctk.CTkFrame(card, width=5, fg_color=cor_destaque, corner_radius=0)
        f_indicador.pack(side="left", fill="y")

        f_conteudo = ctk.CTkFrame(card, fg_color="transparent")
        f_conteudo.pack(side="left", expand=True, fill="both", padx=15, pady=12)

        ctk.CTkLabel(f_conteudo, text=titulo, text_color=COR_CINZA_TEXTO, font=ctk.CTkFont(size=12, weight="bold")).pack(anchor="w")
        ctk.CTkLabel(f_conteudo, text=f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."), font=ctk.CTkFont(size=20, weight="bold"), text_color=cor_destaque).pack(anchor="w", pady=(4, 0))

    def atualizar_cards(self):
        for widget in self.f_cards.winfo_children():
            widget.destroy()

        for widget in self.f_grafico.winfo_children():
            widget.destroy()

        val_salario = self.dados.get("salario", 0.0)
        val_extra = self.dados.get("renda_extra", 0.0)
        renda_total = val_salario + val_extra

        saidas = self.dados.get("saidas", [])
        
        tot_cartao = sum(s.get("valor_parcela", 0.0) for s in saidas if s.get("tipo") == "Cartão de Crédito")
        tot_boletos = sum(s.get("valor_total", 0.0) for s in saidas if s.get("tipo") == "Boleto / Conta Fixa")
        tot_outros = sum(s.get("valor_total", 0.0) for s in saidas if s.get("tipo") not in ["Cartão de Crédito", "Boleto / Conta Fixa"])

        total_saidas = tot_cartao + tot_boletos + tot_outros
        saldo_livre = renda_total - total_saidas

        self.criar_card_estilizado(self.f_cards, "💰 Renda Total", renda_total, COR_VERDE)
        self.criar_card_estilizado(self.f_cards, "📄 Total Saídas Cadastradas", total_saidas, COR_VERMELHO)
        
        cor_saldo = COR_AZUL_BEBE if saldo_livre >= 0 else COR_VERMELHO
        self.criar_card_estilizado(self.f_cards, "🔹 Saldo Livre Estimado", saldo_livre, cor_saldo)

        self.gerar_grafico(val_salario, val_extra, tot_cartao, tot_boletos, tot_outros)

    def gerar_grafico(self, salario, renda_extra, cartao, boleto, outros):
        # Substituído o amarelo neon por um amarelo ouro/âmbar premium (#D97706)
        categorias_todas = {
            "Salário": (salario, "#065F46"),
            "Renda Extra": (renda_extra, "#34D399"),
            "Cartões": (cartao, "#A855F7"),
            "Boletos": (boleto, "#EF4444"),
            "Outras Saídas": (outros, COR_AMARELO_ELEGANTE)
        }

        labels = []
        valores = []
        cores = []

        for cat, (val, cor) in categorias_todas.items():
            if val > 0:
                labels.append(f"{cat}: R$ {val:,.2f}".replace(",", "X").replace(".", ",").replace("X", "."))
                valores.append(val)
                cores.append(cor)

        if not valores:
            lbl_sem_dados = ctk.CTkLabel(
                self.f_grafico, text="📊 Cadastre rendas e saídas para visualizar o gráfico",
                font=ctk.CTkFont(size=13), text_color=COR_CINZA_TEXTO
            )
            lbl_sem_dados.pack(expand=True)
            return

        plt.close('all')
        fig, ax = plt.subplots(figsize=(6, 3.2), facecolor=COR_BG_CARD)
        ax.set_facecolor(COR_BG_CARD)

        wedges, texts, autotexts = ax.pie(
            valores, 
            colors=cores, 
            autopct='%1.1f%%', 
            startangle=140, 
            pctdistance=0.75,
            textprops=dict(color="white", fontsize=9, weight="bold")
        )

        centre_circle = plt.Circle((0, 0), 0.58, fc=COR_BG_CARD)
        fig.gca().add_artist(centre_circle)

        ax.legend(
            wedges, labels,
            title="Categorias",
            loc="center left",
            bbox_to_anchor=(1, 0, 0.5, 1),
            frameon=False,
            labelcolor="white",
            fontsize=9.5,
            title_fontproperties={'weight': 'bold', 'size': 11}
        )

        ax.axis('equal')  
        plt.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=self.f_grafico)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, pady=10, padx=10)

    # -----------------------------------------------------
    # ABA 2: CARTÕES & SAÍDAS
    # -----------------------------------------------------
    def criar_conteudo_cartoes_saidas(self, aba):
        scroll_saidas = ctk.CTkScrollableFrame(aba, fg_color="transparent")
        scroll_saidas.pack(expand=True, fill="both")

        f_topo = ctk.CTkFrame(scroll_saidas, fg_color="transparent")
        f_topo.pack(fill="x", pady=5)

        # Container Esquerda: Registrar Saída
        f_reg_saida = ctk.CTkFrame(f_topo, corner_radius=14, border_width=1, border_color="#334155", fg_color=COR_BG_CARD)
        f_reg_saida.pack(side="left", expand=True, fill="both", padx=(0, 5), pady=5)

        ctk.CTkLabel(f_reg_saida, text="➕ Cadastrar Nova Saída / Despesa", font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_AZUL_BEBE).pack(anchor="w", padx=15, pady=(12, 8))

        f_inputs1 = ctk.CTkFrame(f_reg_saida, fg_color="transparent")
        f_inputs1.pack(fill="x", padx=15, pady=5)

        # Calendário de Data da Saída
        f_date_saida = ctk.CTkFrame(f_inputs1, fg_color="#0F172A", corner_radius=8, border_width=1, border_color=COR_AZUL_BEBE)
        f_date_saida.pack(side="left", padx=(0, 5))
        
        ctk.CTkLabel(f_date_saida, text="📅 DATA DO GASTO", font=ctk.CTkFont(size=9, weight="bold"), text_color=COR_AZUL_BEBE).pack(anchor="w", padx=10, pady=(4, 1))

        self.cal_saida = DateEntry(
            f_date_saida, width=11, background='#0284C7', foreground='white',
            bordercolor='#334155', headersbackground='#0369A1',
            date_pattern='dd/mm/yyyy', font=("Helvetica", 9, "bold")
        )
        self.cal_saida.pack(padx=10, pady=(0, 6))

        # Tipo
        f_tipo = ctk.CTkFrame(f_inputs1, fg_color="transparent")
        f_tipo.pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkLabel(f_tipo, text="Tipo:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.combo_tipo = ctk.CTkOptionMenu(
            f_tipo, values=["Cartão de Crédito", "Boleto / Conta Fixa", "Empréstimo", "Gasto Avulso / Pix"],
            command=self.alternar_modo_saida, height=36
        )
        self.combo_tipo.pack(fill="x", pady=(2, 0))

        # Descrição
        f_desc = ctk.CTkFrame(f_inputs1, fg_color="transparent")
        f_desc.pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkLabel(f_desc, text="Descrição / Local:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.ent_desc = ctk.CTkEntry(f_desc, placeholder_text="ex: Mercado, Aluguel", height=36)
        self.ent_desc.pack(fill="x", pady=(2, 0))

        # Valor Total
        f_val = ctk.CTkFrame(f_inputs1, fg_color="transparent")
        f_val.pack(side="left", expand=True, fill="x", padx=(5, 0))
        ctk.CTkLabel(f_val, text="Valor Total (R$):", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.ent_val_saida = ctk.CTkEntry(f_val, placeholder_text="0.00", height=36)
        self.ent_val_saida.pack(fill="x", pady=(2, 0))

        f_inputs2 = ctk.CTkFrame(f_reg_saida, fg_color="transparent")
        f_inputs2.pack(fill="x", padx=15, pady=(5, 8))

        # Seleção de Cartão
        self.f_cartao_opt = ctk.CTkFrame(f_inputs2, fg_color="transparent")
        self.f_cartao_opt.pack(side="left", expand=True, fill="x", padx=(0, 5))
        ctk.CTkLabel(self.f_cartao_opt, text="Cartão Utilizado:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.combo_cartoes = ctk.CTkOptionMenu(self.f_cartao_opt, values=["Nenhum Cartão"], height=36)
        self.combo_cartoes.pack(fill="x", pady=(2, 0))

        # Parcelas
        self.f_parc_opt = ctk.CTkFrame(f_inputs2, fg_color="transparent")
        self.f_parc_opt.pack(side="left", expand=True, fill="x", padx=5)
        ctk.CTkLabel(self.f_parc_opt, text="Parcelas:", font=ctk.CTkFont(size=11, weight="bold")).pack(anchor="w")
        self.ent_parcelas = ctk.CTkEntry(self.f_parc_opt, placeholder_text="1", height=36)
        self.ent_parcelas.insert(0, "1")
        self.ent_parcelas.pack(fill="x", pady=(2, 0))

        # Botão Lançar Centralizado na parte inferior do painel
        f_btn_center = ctk.CTkFrame(f_reg_saida, fg_color="transparent")
        f_btn_center.pack(fill="x", padx=15, pady=(0, 12))

        btn_add_saida = ctk.CTkButton(
            f_btn_center, text="➕ Registrar Saída", fg_color=COR_VERMELHO, hover_color="#dc2626",
            height=38, font=ctk.CTkFont(weight="bold", size=13), command=self.adicionar_saida
        )
        btn_add_saida.pack(expand=True, fill="x")

        self.ent_desc.bind("<Return>", lambda event: self.adicionar_saida())
        self.ent_val_saida.bind("<Return>", lambda event: self.adicionar_saida())

        # Container Direita: Gestão Rápida de Cartões
        f_gestao_cartoes = ctk.CTkFrame(f_topo, width=280, corner_radius=14, border_width=1, border_color="#334155", fg_color=COR_BG_CARD)
        f_gestao_cartoes.pack(side="right", fill="both", padx=(5, 0), pady=5)

        ctk.CTkLabel(f_gestao_cartoes, text="💳 Novo Cartão", font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_AZUL_BEBE).pack(anchor="w", padx=15, pady=(12, 8))

        self.ent_nome_cartao = ctk.CTkEntry(f_gestao_cartoes, placeholder_text="Nome (ex: Nubank)", height=32)
        self.ent_nome_cartao.pack(fill="x", padx=15, pady=4)

        self.ent_limite_cartao = ctk.CTkEntry(f_gestao_cartoes, placeholder_text="Limite (ex: 2000)", height=32)
        self.ent_limite_cartao.pack(fill="x", padx=15, pady=4)

        btn_add_cartao = ctk.CTkButton(
            f_gestao_cartoes, text="Criar Cartão", fg_color=COR_AZUL_BEBE, hover_color=COR_AZUL_HOVER,
            height=32, font=ctk.CTkFont(size=12, weight="bold"), command=self.adicionar_cartao
        )
        btn_add_cartao.pack(fill="x", padx=15, pady=(6, 12))

        self.ent_nome_cartao.bind("<Return>", lambda event: self.adicionar_cartao())
        self.ent_limite_cartao.bind("<Return>", lambda event: self.adicionar_cartao())

        # Tabela / Lista de Lançamentos
        f_lista = ctk.CTkFrame(scroll_saidas, corner_radius=14, border_width=1, border_color="#334155", fg_color=COR_BG_CARD)
        f_lista.pack(fill="x", pady=10)

        ctk.CTkLabel(f_lista, text="📋 Extrato de Saídas Cadastradas", font=ctk.CTkFont(size=14, weight="bold"), text_color=COR_AZUL_BEBE).pack(anchor="w", padx=15, pady=12)

        self.f_itens_saida = ctk.CTkFrame(f_lista, fg_color="transparent")
        self.f_itens_saida.pack(fill="x", padx=15, pady=(0, 15))

        self.atualizar_combos_cartao()
        self.atualizar_lista_saidas()

    def alternar_modo_saida(self, escolha):
        if escolha == "Cartão de Crédito":
            self.f_cartao_opt.pack(side="left", expand=True, fill="x", padx=(0, 5))
            self.f_parc_opt.pack(side="left", expand=True, fill="x", padx=5)
        else:
            self.f_cartao_opt.pack_forget()
            self.f_parc_opt.pack_forget()

    def adicionar_cartao(self):
        nome = self.ent_nome_cartao.get().strip()
        limite_txt = self.ent_limite_cartao.get().strip().replace(",", ".")

        if not nome or not limite_txt:
            messagebox.showwarning("Atenção", "Informe o nome e o limite do cartão!")
            return

        try:
            limite = float(limite_txt)
            cartoes = self.dados.get("cartoes", [])
            cartoes.append({"nome": nome, "limite": limite})
            self.dados["cartoes"] = cartoes
            self.salvar_dados()

            self.ent_nome_cartao.delete(0, "end")
            self.ent_limite_cartao.delete(0, "end")
            self.atualizar_combos_cartao()
            messagebox.showinfo("Sucesso", f"Cartão '{nome}' cadastrado com sucesso!")
        except ValueError:
            messagebox.showerror("Erro", "O valor do limite precisa ser um número!")

    def atualizar_combos_cartao(self):
        cartoes = self.dados.get("cartoes", [])
        nomes = [c["nome"] for c in cartoes] if cartoes else ["Nenhum Cartão Cadastrado"]
        self.combo_cartoes.configure(values=nomes)
        self.combo_cartoes.set(nomes[0])

    def adicionar_saida(self):
        tipo = self.combo_tipo.get()
        desc = self.ent_desc.get().strip()
        val_txt = self.ent_val_saida.get().strip().replace(",", ".")
        data_gasto = self.cal_saida.get_date().strftime("%d/%m/%Y")

        if not desc or not val_txt:
            messagebox.showwarning("Atenção", "Preencha a descrição e o valor da saída!")
            return

        try:
            val_total = float(val_txt)
            cartao_usado = self.combo_cartoes.get() if tipo == "Cartão de Crédito" else "-"
            
            parcelas = 1
            if tipo == "Cartão de Crédito":
                try:
                    parcelas = int(self.ent_parcelas.get().strip())
                except ValueError:
                    parcelas = 1

            val_parcela = val_total / parcelas if parcelas > 0 else val_total

            nova_saida = {
                "tipo": tipo,
                "descricao": desc,
                "valor_total": val_total,
                "parcelas": parcelas,
                "valor_parcela": val_parcela,
                "cartao": cartao_usado,
                "status": "Pendente",
                "data": data_gasto
            }

            self.dados.setdefault("saidas", []).append(nova_saida)
            self.salvar_dados()

            self.ent_desc.delete(0, "end")
            self.ent_val_saida.delete(0, "end")
            self.ent_parcelas.delete(0, "end")
            self.ent_parcelas.insert(0, "1")

            self.atualizar_lista_saidas()
            self.atualizar_cards()

        except ValueError:
            messagebox.showerror("Erro", "Digite um valor numérico válido!")

    def alternar_status_saida(self, index):
        saidas = self.dados.get("saidas", [])
        if 0 <= index < len(saidas):
            status_atual = saidas[index].get("status", "Pendente")
            saidas[index]["status"] = "Pago" if status_atual == "Pendente" else "Pendente"
            self.salvar_dados()
            self.atualizar_lista_saidas()
            self.atualizar_cards()

    def remover_saida(self, index):
        saidas = self.dados.get("saidas", [])
        if 0 <= index < len(saidas):
            del saidas[index]
            self.salvar_dados()
            self.atualizar_lista_saidas()
            self.atualizar_cards()

    def atualizar_lista_saidas(self):
        for widget in self.f_itens_saida.winfo_children():
            widget.destroy()

        saidas = self.dados.get("saidas", [])

        if not saidas:
            lbl_vazio = ctk.CTkLabel(self.f_itens_saida, text="Nenhuma saída cadastrada até o momento.", text_color=COR_CINZA_TEXTO)
            lbl_vazio.pack(pady=15)
            return

        # Extrato Agrupado Inteligente: Agrupa por data sem repetir
        data_atual = None

        for idx, item in enumerate(saidas):
            dt_item = item.get("data", datetime.now().strftime("%d/%m/%Y"))

            # Cria um divisor de data se for um dia diferente
            if dt_item != data_atual:
                data_atual = dt_item
                f_header_data = ctk.CTkFrame(self.f_itens_saida, fg_color="transparent")
                f_header_data.pack(fill="x", pady=(12, 4))

                lbl_dt_header = ctk.CTkLabel(
                    f_header_data, text=f"📅 {dt_item}", font=ctk.CTkFont(size=12, weight="bold"), text_color=COR_AZUL_BEBE
                )
                lbl_dt_header.pack(side="left")

                line_div = ctk.CTkFrame(f_header_data, height=1, fg_color="#334155")
                line_div.pack(side="left", expand=True, fill="x", padx=(10, 0))

            f_row = ctk.CTkFrame(self.f_itens_saida, fg_color="#0F172A", corner_radius=8)
            f_row.pack(fill="x", pady=3, ipady=4)

            # Icone por tipo
            icone = "💳" if item["tipo"] == "Cartão de Crédito" else ("📄" if item["tipo"] == "Boleto / Conta Fixa" else "💸")

            lbl_info = ctk.CTkLabel(
                f_row, 
                text=f"{icone} {item['descricao']} ({item['tipo']})", 
                font=ctk.CTkFont(weight="bold", size=13)
            )
            lbl_info.pack(side="left", padx=12)

            # Detalhes de valor com fonte ligeiramente maior
            detalhe_txt = f"R$ {item['valor_total']:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            if item["tipo"] == "Cartão de Crédito" and item["parcelas"] > 1:
                detalhe_txt += f" ({item['parcelas']}x de R$ {item['valor_parcela']:,.2f})".replace(",", "X").replace(".", ",").replace("X", ".")

            lbl_val = ctk.CTkLabel(f_row, text=detalhe_txt, font=ctk.CTkFont(weight="bold", size=14), text_color=COR_VERMELHO)
            lbl_val.pack(side="left", padx=15)

            # Botão de Ação Excluir
            btn_del = ctk.CTkButton(
                f_row, text="🗑️", width=32, height=28, fg_color="#dc2626", hover_color="#b91c1c",
                command=lambda i=idx: self.remover_saida(i)
            )
            btn_del.pack(side="right", padx=(5, 10))

            # Status Badge e Botão Pagar
            is_pago = item.get("status") == "Pago"
            cor_btn_status = COR_VERDE if is_pago else "#334155"
            txt_btn_status = "✅ Pago" if is_pago else "⏳ Quitar"

            btn_status = ctk.CTkButton(
                f_row, text=txt_btn_status, width=80, height=28, fg_color=cor_btn_status,
                command=lambda i=idx: self.alternar_status_saida(i)
            )
            btn_status.pack(side="right", padx=5)


# =========================================================
# GERENCIADOR DA APLICAÇÃO
# =========================================================
class AppFinanceiroK(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("K$ - Controle Financeiro Professional")
        self.geometry("960x780")
        self.resizable(True, True)

        self.protocol("WM_DELETE_WINDOW", self.fechar_aplicacao)

        self.usuario_atual = None
        self.mostrar_login()

    def fechar_aplicacao(self):
        plt.close('all')
        self.destroy()

    def limpar_tela(self):
        for widget in self.winfo_children():
            widget.destroy()

    def mostrar_login(self):
        self.limpar_tela()
        TelaLogin(self, on_login_sucesso=self.iniciar_sistema, on_ir_para_cadastro=self.mostrar_cadastro)

    def mostrar_cadastro(self):
        self.limpar_tela()
        TelaCadastro(self, on_cadastro_sucesso=self.iniciar_sistema, on_voltar_login=self.mostrar_login)

    def iniciar_sistema(self, usuario):
        self.usuario_atual = usuario
        self.limpar_tela()
        PainelPrincipal(self, usuario_atual=self.usuario_atual, on_sair=self.mostrar_login)


if __name__ == "__main__":
    app = AppFinanceiroK()
    app.mainloop()