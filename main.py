# ===================================================
# Projeto: Controle Financeiro em Python
# Versão: 1.2 (Terminal - Refatorado com Funções)
# Autor: Klayvert
# ===================================================

def exibir_menu():
    """Exibe o menu de opções do sistema."""
    print("\n------------------------------------")
    print("MENU PRINCIPAL")
    print("1 - Ver Saldo")
    print("2 - Depositar (Receita)")
    print("3 - Sacar (Despesa)")
    print("4 - Ver Extrato")
    print("0 - Sair")
    print("------------------------------------")


def depositar(saldo, extrato):
    """Realiza a operação de depósito e atualiza o extrato."""
    valor = float(input("Digite o valor do depósito (R$): "))
    if valor > 0:
        saldo += valor
        extrato.append(f"Depósito: + R$ {valor:.2f}")
        print(f"Depósito de R$ {valor:.2f} realizado com sucesso!")
    else:
        print("Valor inválido para depósito.")
    return saldo


def sacar(saldo, extrato):
    """Realiza a operação de saque com validação de saldo."""
    valor = float(input("Digite o valor do saque (R$): "))
    if valor > 0 and valor <= saldo:
        saldo -= valor
        extrato.append(f"Saque:    - R$ {valor:.2f}")
        print(f"Saque de R$ {valor:.2f} realizado com sucesso!")
    elif valor > saldo:
        print("Saldo insuficiente para esta operação!")
    else:
        print("Valor inválido para saque.")
    return saldo


def exibir_extrato(saldo, extrato):
    """Exibe o histórico de transações registradas."""
    print("\n================ EXTRATO ================")
    if not extrato:
        print("Nenhuma movimentação realizada até o momento.")
    else:
        for transacao in extrato:
            print(transacao)
    print(f"\nSaldo atual: R$ {saldo:.2f}")
    print("=========================================")


def main():
    """Função principal que orquestra o fluxo do programa."""
    print("====================================")
    print("  SISTEMA DE CONTROLE FINANCEIRO    ")
    print("====================================")
    print()

    nome_usuario = input("Digite seu nome: ")
    saldo = float(input("Digite seu saldo inicial (R$): "))
    extrato = []

    print()
    print(f"Bem-vindo(a), {nome_usuario}! Saldo inicial: R$ {saldo:.2f}")

    opcao = ""
    while opcao != "0":
        exibir_menu()
        opcao = input("Escolha uma opção: ")

        if opcao == "1":
            print(f"\n[SALDO ATUAL]: R$ {saldo:.2f}")
        elif opcao == "2":
            saldo = depositar(saldo, extrato)
        elif opcao == "3":
            saldo = sacar(saldo, extrato)
        elif opcao == "4":
            exibir_extrato(saldo, extrato)
        elif opcao == "0":
            print("\nSaindo do sistema... Até logo!")
        else:
            print("Opção inválida! Tente novamente.")


# Ponto de entrada padrão do Python
if __name__ == "__main__":
    main()