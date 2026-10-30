# main.py
# O menu do programa. É o único ficheiro que se executa:  python main.py
#
# Aqui só se trata de falar com o utilizador (input/print).
# As regras estão na Loja e os ficheiros no armazenamento.

from armazenamento import (PREFIXO, carregar_loja, guardar_loja, importar_produtos_csv,
                           registar_venda_historico, ler_historico)
from modelos import Cliente, StockInsuficienteError
from relatorio import gerar_relatorio, guardar_relatorio

FICHEIRO_RELATORIO = f"{PREFIXO}_relatorio.txt"

MENU = """
========== InfoPorto ==========
1 - Mostrar todos os produtos
2 - Mostrar todos os clientes
3 - Criar cliente
4 - Nova venda
5 - Repor stock
6 - Importar produtos (CSV)
7 - Relatório
0 - Guardar e sair
==============================="""


# ===============================================================
# Funções auxiliares para pedir dados
# ===============================================================
def pedir_inteiro_positivo(pergunta):
    """Pergunta até o utilizador escrever um número inteiro maior que 0."""
    while True:
        texto = input(pergunta).strip()
        try:
            numero = int(texto)
        except ValueError:
            print("  Tem de ser um número inteiro. Tenta outra vez.")
            continue
        if numero <= 0:
            print("  Tem de ser maior que 0. Tenta outra vez.")
            continue
        return numero


def pedir_texto(pergunta):
    """Pergunta até o utilizador escrever algo que não seja vazio."""
    while True:
        texto = input(pergunta).strip()
        if texto != "":
            return texto
        print("  Não pode ficar vazio.")


def pedir_nif(pergunta="NIF: "):
    """Pergunta até o NIF ter 9 algarismos."""
    while True:
        nif = input(pergunta).strip()
        if nif.isdigit() and len(nif) == 9:
            return nif
        print("  NIF inválido: tem de ter 9 algarismos.")


# ===============================================================
# Uma função por opção do menu
# ===============================================================
def mostrar_produtos(loja):
    if len(loja.produtos) == 0:
        print("Não há produtos. Usa a opção 6 para os importar.")
        return
    for produto in loja.produtos.values():
        print(produto)
    print(f"({len(loja.produtos)} produtos)")


def mostrar_clientes(loja):
    if len(loja.clientes) == 0:
        print("Ainda não há clientes. Usa a opção 3 para criar um.")
        return
    for cliente in loja.clientes.values():
        print(cliente)


def criar_cliente(loja):
    nif = pedir_nif()
    nome = pedir_texto("Nome: ")
    loja.adicionar_cliente(Cliente(nif, nome))   # erro se o NIF já existir
    print(f"Cliente {nome} criado.")


def nova_venda(loja):
    nif = pedir_nif("NIF do cliente: ")
    cliente = loja.obter_cliente(nif)            # erro se não existir -> volta ao menu
    print(f"Cliente: {cliente.nome} ({cliente.tipo()})")
    print("Escreve os produtos. Deixa o código vazio para terminar.")

    pedidos = []
    while True:
        codigo = input("  Código: ").strip()
        if codigo == "":
            break
        try:
            produto = loja.obter_produto(codigo)
        except ValueError as erro:
            print(f"  {erro}")
            continue
        quantidade = pedir_inteiro_positivo(f"  Quantidade de {produto.nome}: ")
        pedidos.append((produto.codigo, quantidade))

    tipo_antes = cliente.tipo()
    venda = loja.registar_venda(nif, pedidos)    # valida tudo; se falhar, nada muda
    registar_venda_historico(venda)

    print()
    print(venda)

    if loja.obter_cliente(nif).tipo() != tipo_antes:
        print(f"Parabéns! {cliente.nome} passou a cliente premium (10% de desconto).")


def repor_stock(loja):
    codigo = input("Código do produto: ")
    produto = loja.obter_produto(codigo)         # erro se não existir
    quantidade = pedir_inteiro_positivo(f"Quantidade a repor de {produto.nome}: ")
    loja.repor_stock(produto.codigo, quantidade)
    print(f"Stock atualizado: {produto}")


def importar_produtos(loja):
    nome_ficheiro = pedir_texto("Nome do ficheiro CSV: ")
    try:
        produtos, avisos = importar_produtos_csv(nome_ficheiro)
    except FileNotFoundError:
        print(f"O ficheiro '{nome_ficheiro}' não existe.")
        return

    # Linhas com erros no ficheiro: mostra cada uma
    for aviso in avisos:
        print("Aviso:", aviso)

    # Produtos que já existiam na loja: mostra só quantos foram
    importados, ja_existiam = loja.importar_produtos(produtos)
    if len(ja_existiam) > 0:
        print(f"Aviso: {len(ja_existiam)} produtos já existiam na loja e foram ignorados.")
    print(f"{importados} produtos importados.")


def mostrar_relatorio(loja):
    texto = gerar_relatorio(loja, ler_historico())
    guardar_relatorio(texto, FICHEIRO_RELATORIO)
    print(texto)
    print(f"\n(Relatório guardado em {FICHEIRO_RELATORIO})")


def guardar(loja):
    try:
        guardar_loja(loja)
        print("Dados guardados.")
    except OSError as erro:
        print(f"Não foi possível guardar os dados: {erro}")


# ===============================================================
# Programa principal
# ===============================================================
OPCOES = {
    "1": mostrar_produtos,
    "2": mostrar_clientes,
    "3": criar_cliente,
    "4": nova_venda,
    "5": repor_stock,
    "6": importar_produtos,
    "7": mostrar_relatorio,
}


def main():
    loja, avisos = carregar_loja()
    for aviso in avisos:
        print("Aviso:", aviso)
    print(f"Carregados {len(loja.produtos)} produtos e {len(loja.clientes)} clientes.")

    while True:
        print(MENU)
        escolha = input("Opção: ").strip()

        if escolha == "0":
            guardar(loja)
            print("Até à próxima!")
            break

        if escolha not in OPCOES:
            print("Opção inválida.")
            continue

        funcao = OPCOES[escolha]
        try:
            funcao(loja)
        except (ValueError, StockInsuficienteError) as erro:
            # Erros previstos: dados inválidos, cliente/produto inexistente, sem stock...
            print(f"Erro: {erro}")
        except OSError as erro:
            # Problemas com ficheiros (sem permissões, disco cheio, ...)
            print(f"Erro de ficheiro: {erro}")


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        # Ctrl+C ou fim do input: sai sem mostrar um erro feio
        print("\nPrograma interrompido. Os dados desta sessão não foram guardados.")