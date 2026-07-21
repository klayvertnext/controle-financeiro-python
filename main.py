import json
import os

# Nome do arquivo de banco de dados local
ARQUIVO_DADOS = "dados.json"


def carregar_dados():
    """Carrega os dados do arquivo JSON. Se não existir, retorna dados padrão."""
    if os.path.exists(ARQUIVO_DADOS):
        try:
            with open(ARQUIVO_DADOS, "r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except Exception:
            print("Erro ao carregar os dados. Criando novo cadastro...")
    
    # Estrutura inicial caso seja a primeira vez rodando o programa
    return {"nome": "", "saldo": 0.0, "extrato": []}


def salvar_dados(dados):
    """Salva os dados atuais do sistema no arquivo JSON."""
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as arquivo:
        json.dump(dados, arquivo, indent=4, ensure_ascii=False)


def exibir_menu():
    """Exibe o menu principal do sistema."""
    print("\n------------------------------------")
    print("MENU PRINCIPAL")
    print("1 - Ver Saldo")
    print("2 - Depositar (Receita)")
    print("3 - Sacar (Despesa)")
    print("4 - Ver Extrato")
    print("0 - Sair")
    print("------------------------------------")


def depositar(dados):
    """Realiza a operação de depósito e salva as alterações."""
    valor = float(input("Digite o valor do depósito (R$): "))
    if valor > 0:
        dados["saldo"] += valor
        dados["extrato"].append(f"Depósito: + R$ {valor:.2f}")
        salvar_dados(dados)  # Salva automaticamente no arquivo
        print(f"Depósito de R$ {valor:.2f} realizado com sucesso!")
    else:
        print("Valor inválido para depósito.")


def sacar(dados):
    """Realiza a operação de saque com validação e salva as alterações."""
    valor = float(input("Digite o valor do saque (R$): "))
    if valor > 0 and valor <= dados["saldo"]:
        dados["saldo"] -= valor
        dados["extrato"].append(f"Saque:    - R$ {valor:.2f}")
        salvar_dados(dados)  # Salva automaticamente no arquivo
        print(f"Saque de R$ {valor:.2f} realizado com sucesso!")
    elif valor > dados["saldo"]:
        print("Saldo insuficiente para esta operação!")
    else:
        print("Valor inválido para saque.")


def exibir_extrato(dados):
    """Exibe o histórico de transações e saldo atual."""
    print("\n================ EXTRATO ================")
    if not dados["extrato"]:
        print("Nenhuma movimentação realizada até o momento.")
    else:
        for transacao in dados["extrato"]:
            print(transacao)
    print(f"\nSaldo atual: R$ {dados['saldo']:.2f}")
    print("=========================================")


def main():
    print("====================================")
    print("  SISTEMA DE CONTROLE FINANCEIRO    ")
    print("====================================")
    print()

    # Carrega dados salvos ou inicia novos
    dados = carregar_dados()

    # Se for o primeiro acesso (sem nome cadastrado)
    if not dados["nome"]:
        dados["nome"] = input("Digite seu nome: ")
        dados["saldo"] = float(input("Digite seu saldo inicial (R$): "))
        salvar_dados(dados)

    print()
    print(f"Bem-vindo(a) de volta, {dados['nome']}! Saldo atual: R$ {dados['saldo']:.2f}")

    opcao = ""
    while opcao != "0":
        exibir_menu()
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            print(f"\n[SALDO ATUAL]: R$ {dados['saldo']:.2f}")
        elif opcao == "2":
            depositar(dados)
        elif opcao == "3":
            sacar(dados)
        elif opcao == "4":
            exibir_extrato(dados)
        elif opcao == "0":
            print("\nSaindo do sistema... Dados salvos com sucesso! Até logo!")
        else:
            print("Opção inválida! Tente novamente.")


if __name__ == "__main__":
    main()