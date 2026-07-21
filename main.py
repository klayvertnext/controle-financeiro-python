# projeto: Controle Financeiro em python
# Versão: 1.0 (terminal - módulo inicial)
# Autor: klayvert 

print("=================================")
print("Sistema de Controle Financeiro")
print("=================================")
print()

# captura de dados iniciais do usuario
nome = input("Digite seu nome:")
saldo = float(input("digite seu saldo inicial (R$):"))

# estrutura para armazenar o historico de transações 
extrato = []


print()
print("=================================")
print(f"Bem-vindo(a), {nome}!")
print(f"Seu saldo inicial cadastrado é: R$ {saldo:.2f}")
print("=================================")

# Menu Interativo 
opção = ""

while opção != "0":
    print()
    print("\------------------------")
    print("MENU PRINCIPAL")
    print("1 - Ver Saldo")
    print("2 - depositar (receita)")
    print("3 - sacar (despesa)")
    print("4 - extrato (historico de transações)")
    print("0 - sair")
    print("------------------------")

    opção = input("escolha uma opção: ")

    if opção == "1":
        print(f"\n[SALDO ATUAL]: R$ {saldo :.2f}")

    elif opção == "2":
        valor = float(input("Digite o valor do deposito (R$)"))
        if valor > 0:
            saldo += valor 
            # registra no historico  
            extrato.append(("deposito", valor))
            print(f"Deposito de R$ {valor:.2f} realizado com sucesso!")
        else:
            print("Valor invalido para deposito.")

    elif opção == "3":
        valor = float(input("Digite o valor do saque (R$): "))
        if valor > 0 and valor <= saldo:
            saldo -= valor 
            # registra no historico 
            extrato.append(f"saque: - R$ {valor:.2f}")
            print(f"Saque de R$ {valor:.2f} realizado com sucesso!")
        elif valor > saldo:
            print("saldo insuficiente para esta operação! ")
        else:
            print("valor invalido para saque.")

    elif opção == "4":
        print("\n=============== EXTRATO ==========")
        if not extrato: # verifica se a lista vazia
             print("Nenhuma movimentação realizada ate o momento.")
        else:
            for transação in extrato:
                 print(transação)
        print(f"\nSaldo atual: R$ {saldo:.2f}")
        print("===================================")

    elif opção == "0":
        print("\nSaindo do sistema... ate logo! ")

    else:
        print("opção invalida! tente novamente.")        

