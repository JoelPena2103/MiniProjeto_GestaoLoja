# armazenamento.py
# Leitura e escrita de ficheiros (JSON e CSV).
#
#   <prefixo>_produtos.json  -> produtos da loja
#   <prefixo>_clientes.json  -> clientes da loja
#   <prefixo>_vendas.csv     -> histórico de vendas (só se acrescenta)
#
# O prefixo, por omissão, é "loja".

import csv
import json
import os

from modelos import Produto, produto_de_dict, cliente_de_dict
from loja import Loja

PREFIXO = "loja"
FORMATO_DATA = "%Y-%m-%d %H:%M:%S"
COLUNAS_HISTORICO = ["data", "nif", "produto", "quantidade", "valor_pago"]


# ===============================================================
# Nomes dos ficheiros
# ===============================================================
def ficheiro_produtos(prefixo=PREFIXO):
    return f"{prefixo}_produtos.json"


def ficheiro_clientes(prefixo=PREFIXO):
    return f"{prefixo}_clientes.json"


def ficheiro_vendas(prefixo=PREFIXO):
    return f"{prefixo}_vendas.csv"


# ===============================================================
# JSON: guardar e carregar a loja
# ===============================================================
def guardar_loja(loja, prefixo=PREFIXO):
    """Guarda produtos e clientes em dois ficheiros JSON."""
    lista_produtos = [p.para_dict() for p in loja.produtos.values()]
    lista_clientes = [c.para_dict() for c in loja.clientes.values()]

    with open(ficheiro_produtos(prefixo), "w", encoding="utf-8") as f:
        json.dump(lista_produtos, f, ensure_ascii=False, indent=2)

    with open(ficheiro_clientes(prefixo), "w", encoding="utf-8") as f:
        json.dump(lista_clientes, f, ensure_ascii=False, indent=2)


def _ler_lista_json(nome_ficheiro, converter, avisos):
    """Lê um ficheiro JSON com uma lista de dicionários e converte cada um
    num objeto com a função 'converter'.
      - se o ficheiro não existir: devolve lista vazia (sem aviso);
      - se estiver corrompido: junta um aviso e devolve lista vazia."""
    if not os.path.exists(nome_ficheiro):
        return []

    try:
        with open(nome_ficheiro, encoding="utf-8") as f:
            dados = json.load(f)
        return [converter(item) for item in dados]
    except (json.JSONDecodeError, KeyError, TypeError, ValueError):
        avisos.append(f"O ficheiro {nome_ficheiro} está corrompido. "
                      f"Esses dados começam vazios.")
        return []


def carregar_loja(prefixo=PREFIXO):
    """Cria uma Loja com os dados guardados nos ficheiros JSON.
    Devolve a loja e uma lista de avisos (vazia se correu tudo bem)."""
    avisos = []
    loja = Loja()

    for produto in _ler_lista_json(ficheiro_produtos(prefixo), produto_de_dict, avisos):
        loja.produtos[produto.codigo] = produto

    for cliente in _ler_lista_json(ficheiro_clientes(prefixo), cliente_de_dict, avisos):
        loja.clientes[cliente.nif] = cliente

    return loja, avisos


# ===============================================================
# CSV: histórico de vendas
# ===============================================================
def registar_venda_historico(venda, prefixo=PREFIXO):
    """Acrescenta ao histórico uma linha por produto vendido.
    O cabeçalho só é escrito se o ficheiro ainda não existir (ou estiver vazio)."""
    nome = ficheiro_vendas(prefixo)
    precisa_cabecalho = not os.path.exists(nome) or os.path.getsize(nome) == 0

    desconto = venda.cliente.desconto()
    data = venda.data_hora.strftime(FORMATO_DATA)

    # "a" = append: escreve no fim, sem apagar as vendas anteriores
    with open(nome, "a", encoding="utf-8", newline="") as f:
        escritor = csv.writer(f, delimiter=";")
        if precisa_cabecalho:
            escritor.writerow(COLUNAS_HISTORICO)
        for produto, quantidade in venda.linhas:
            valor_pago = round(produto.preco * quantidade * (1 - desconto), 2)
            escritor.writerow([data, venda.cliente.nif, produto.codigo,
                               quantidade, f"{valor_pago:.2f}"])


def ler_historico(prefixo=PREFIXO):
    """Lê o histórico de vendas e devolve uma lista de dicionários,
    já com a quantidade e o valor convertidos em números.
    Se o ficheiro não existir, devolve lista vazia. Linhas estragadas são saltadas."""
    nome = ficheiro_vendas(prefixo)
    if not os.path.exists(nome):
        return []

    linhas = []
    with open(nome, encoding="utf-8", newline="") as f:
        for linha in csv.DictReader(f, delimiter=";"):
            try:
                linhas.append({
                    "data": linha["data"],
                    "nif": linha["nif"],
                    "produto": linha["produto"],
                    "quantidade": int(linha["quantidade"]),
                    "valor_pago": float(linha["valor_pago"]),
                })
            except (KeyError, TypeError, ValueError):
                continue
    return linhas


# ===============================================================
# CSV: importação de produtos
# ===============================================================


def importar_produtos_csv(nome_ficheiro):
    """Lê um CSV com as colunas codigo;nome;preco;stock.

    Devolve dois resultados:
      - produtos: lista de objetos Produto válidos
      - avisos:   lista de textos a explicar cada linha ignorada

    Se o ficheiro não existir, o open() lança FileNotFoundError;
    quem chama esta função (o menu) é que trata disso.
    """
    produtos = []
    avisos = []
    codigos_vistos = set()   # para detetar códigos repetidos

    # utf-8-sig lê bem os acentos e também ficheiros guardados pelo Excel
    with open(nome_ficheiro, encoding="utf-8-sig", newline="") as ficheiro:
        leitor = csv.DictReader(ficheiro, delimiter=";")

        # A linha 1 é o cabeçalho, por isso os dados começam na linha 2
        for numero_linha, linha in enumerate(leitor, start=2):
            # Linhas totalmente vazias (por ex. no fim do ficheiro) são saltadas
            if not any(linha.values()):
                continue

            # .get(...) or "" evita erro se faltar uma coluna (vem None)
            codigo = (linha.get("codigo") or "").strip().upper()
            nome = (linha.get("nome") or "").strip()
            preco_texto = (linha.get("preco") or "").strip()
            stock_texto = (linha.get("stock") or "").strip()

            # 1) Campos em falta
            if codigo == "" or nome == "" or preco_texto == "" or stock_texto == "":
                avisos.append(f"Linha {numero_linha} ({codigo or 'sem código'}): "
                              f"campos em falta - ignorada.")
                continue

            # 2) Preço tem de ser um número
            try:
                preco = float(preco_texto)
            except ValueError:
                avisos.append(f"Linha {numero_linha} ({codigo}): preço '{preco_texto}' "
                              f"não é um número - ignorada.")
                continue

            # 3) Stock tem de ser um número inteiro
            try:
                stock = int(stock_texto)
            except ValueError:
                avisos.append(f"Linha {numero_linha} ({codigo}): stock '{stock_texto}' "
                              f"não é um número inteiro - ignorada.")
                continue

            # 4) Não aceitamos valores negativos
            if preco < 0 or stock < 0:
                avisos.append(f"Linha {numero_linha} ({codigo}): preço ou stock "
                              f"negativo - ignorada.")
                continue

            # 5) Código repetido dentro do ficheiro
            if codigo in codigos_vistos:
                avisos.append(f"Linha {numero_linha} ({codigo}): código repetido - ignorada.")
                continue

            # Se chegou aqui, a linha é válida
            codigos_vistos.add(codigo)
            produtos.append(Produto(codigo, nome, preco, stock))

    return produtos, avisos