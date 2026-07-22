import customtkinter as ctk
from tkinter import messagebox
import json
import os

# Configurações de Aparência do CustomTkinter
ctk.set_appearance_mode("Dark")  # Modos: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Temas: "blue", "green", "dark-blue"

ARQUIVO_DADOS = "dados.json"


def carregar_dados():
    """Carrega os dados do arquivo JSON local."""
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except Exception:
            pass
    return {"nome": "", "saldo": 0.0, "extrato": []}


def salvar_dados(dados):
    """Salva os dados no arquivo JSON."""
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)


class AppFinanceiro(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.dados = carregar_dados()

        # Configuração da Janela Principal
        self.title("Controle Financeiro Professional")
        self.geometry("500x650")
        self.resizable(False, False)

        # Se não houver nome cadastrado, solicita primeiro
        if not self.dados["nome"]:
            self.solicitar_cadastro_inicial()

        self.criar_interface()

    def solicitar_cadastro_inicial(self):
        """Janela popup simples para primeiro acesso."""
        dialogo_nome = ctk.CTkInputDialog(text="Digite seu nome:", title="Primeiro Acesso")
        nome = dialogo_nome.get_input()

        dialogo_saldo = ctk.CTkInputDialog(text="Digite seu saldo inicial (R$):", title="Primeiro Acesso")
        saldo_str = dialogo_saldo.get_input()

        try:
            saldo = float(saldo_str) if saldo_str else 0.0
        except ValueError:
            saldo = 0.0

        self.dados["nome"] = nome if nome else "Usuário"
        self.dados["saldo"] = saldo
        salvar_dados(self.dados)

    def criar_interface(self):
        """Constrói os elementos visuais na tela."""
        
        # Cabeçalho / Saudação
        self.lbl_boas_vindas = ctk.CTkLabel(
            self,
            text=f"Olá, {self.dados['nome']}! 👋",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        self.lbl_boas_vindas.pack(pady=(20, 5))

        # Card de Saldo
        self.card_saldo = ctk.CTkFrame(self, corner_radius=15, fg_color="#1f2937")
        self.card_saldo.pack(pady=10, padx=20, fill="x")

        self.lbl_titulo_saldo = ctk.CTkLabel(
            self.card_saldo,
            text="Saldo Atual Disponível",
            font=ctk.CTkFont(size=14),
            text_color="#9ca3af"
        )
        self.lbl_titulo_saldo.pack(pady=(15, 0))

        self.lbl_saldo = ctk.CTkLabel(
            self.card_saldo,
            text=f"R$ {self.dados['saldo']:.2f}",
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color="#10b981"
        )
        self.lbl_saldo.pack(pady=(5, 15))

        # Campo para digitar o valor
        self.entry_valor = ctk.CTkEntry(
            self,
            placeholder_text="Digite o valor (R$)",
            width=280,
            height=40,
            font=ctk.CTkFont(size=14)
        )
        self.entry_valor.pack(pady=15)

        # Botões de Ação (Depósito e Saque)
        self.frame_botoes = ctk.CTkFrame(self, fg_color="transparent")
        self.frame_botoes.pack(pady=5)

        self.btn_depositar = ctk.CTkButton(
            self.frame_botoes,
            text="+ Depositar",
            command=self.executar_deposito,
            fg_color="#059669",
            hover_color="#047857",
            width=135,
            height=40,
            font=ctk.CTkFont(weight="bold")
        )
        self.btn_depositar.grid(row=0, column=0, padx=5)

        self.btn_sacar = ctk.CTkButton(
            self.frame_botoes,
            text="- Sacar",
            command=self.executar_saque,
            fg_color="#dc2626",
            hover_color="#b91c1c",
            width=135,
            height=40,
            font=ctk.CTkFont(weight="bold")
        )
        self.btn_sacar.grid(row=0, column=1, padx=5)

        # Seção de Extrato / Histórico
        self.lbl_titulo_extrato = ctk.CTkLabel(
            self,
            text="Histórico de Movimentações",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.lbl_titulo_extrato.pack(pady=(20, 5))

        self.caixa_extrato = ctk.CTkTextbox(
            self,
            width=440,
            height=180,
            corner_radius=10,
            font=ctk.CTkFont(family="Consolas", size=13)
        )
        self.caixa_extrato.pack(pady=10)

        self.atualizar_extrato_tela()

    def atualizar_extrato_tela(self):
        """Atualiza o saldo e a caixa de texto do extrato."""
        self.lbl_saldo.configure(text=f"R$ {self.dados['saldo']:.2f}")
        self.caixa_extrato.configure(state="normal")
        self.caixa_extrato.delete("1.0", "end")

        if not self.dados["extrato"]:
            self.caixa_extrato.insert("1.0", "Nenhuma movimentação realizada.")
        else:
            for item in self.dados["extrato"]:
                self.caixa_extrato.insert("end", f"{item}\n")

        self.caixa_extrato.configure(state="disabled")

    def executar_deposito(self):
        try:
            valor = float(self.entry_valor.get())
            if valor > 0:
                self.dados["saldo"] += valor
                self.dados["extrato"].append(f"Depósito: + R$ {valor:.2f}")
                salvar_dados(self.dados)
                self.atualizar_extrato_tela()
                self.entry_valor.delete(0, "end")
                messagebox.showinfo("Sucesso", f"Depósito de R$ {valor:.2f} realizado!")
            else:
                messagebox.showwarning("Atenção", "Digite um valor maior que zero.")
        except ValueError:
            messagebox.showerror("Erro", "Por favor, digite um número válido.")

    def executar_saque(self):
        try:
            valor = float(self.entry_valor.get())
            if valor > 0 and valor <= self.dados["saldo"]:
                self.dados["saldo"] -= valor
                self.dados["extrato"].append(f"Saque:    - R$ {valor:.2f}")
                salvar_dados(self.dados)
                self.atualizar_extrato_tela()
                self.entry_valor.delete(0, "end")
                messagebox.showinfo("Sucesso", f"Saque de R$ {valor:.2f} realizado!")
            elif valor > self.dados["saldo"]:
                messagebox.showwarning("Saldo Insuficiente", "Você não tem saldo para essa operação.")
            else:
                messagebox.showwarning("Atenção", "Digite um valor maior que zero.")
        except ValueError:
            messagebox.showerror("Erro", "Por favor, digite um número válido.")


if __name__ == "__main__":
    app = AppFinanceiro()
    app.mainloop()