# relatorio.py
# Geração do relatório da loja.
#
# O relatório usa duas fontes:
#   - a Loja (para o stock e o total gasto de cada cliente)
#   - o histórico de vendas, já lido por armazenamento.ler_historico()

from datetime import datetime


def gerar_relatorio(loja, historico):
    """Devolve o texto do relatório.
    'historico' é a lista de dicionários devolvida por ler_historico()."""
    linhas = []
    linhas.append("=" * 50)
    linhas.append("RELATÓRIO DA LOJA")
    linhas.append(f"Gerado em {datetime.now():%d/%m/%Y %H:%M}")
    linhas.append("=" * 50)

    # O valor em stock não depende das vendas, por isso aparece sempre
    linhas.append(f"Valor total em stock:      {loja.valor_total_stock():.2f} €")

    if len(historico) == 0:
        linhas.append("")
        linhas.append("Ainda não há vendas registadas.")
        return "\n".join(linhas)

    # ---------- Números gerais ----------
    numero_linhas = len(historico)

    nifs_diferentes = set()          # um set não guarda repetidos
    faturacao = 0
    for venda in historico:
        nifs_diferentes.add(venda["nif"])
        faturacao += venda["valor_pago"]

    media = faturacao / numero_linhas

    linhas.append(f"Linhas de venda:           {numero_linhas}")
    linhas.append(f"Clientes que já compraram: {len(nifs_diferentes)}")
    linhas.append(f"Faturação total:           {faturacao:.2f} €")
    linhas.append(f"Valor médio por linha:     {media:.2f} €")

    # ---------- Top 3 produtos mais vendidos ----------
    unidades_por_produto = {}        # codigo -> unidades vendidas
    for venda in historico:
        codigo = venda["produto"]
        unidades_por_produto[codigo] = unidades_por_produto.get(codigo, 0) + venda["quantidade"]

    mais_vendidos = sorted(unidades_por_produto.items(),
                           key=lambda par: par[1],
                           reverse=True)[:3]

    linhas.append("")
    linhas.append("Produtos mais vendidos:")
    for posicao, (codigo, unidades) in enumerate(mais_vendidos, start=1):
        # Se o produto ainda existir na loja, mostra também o nome
        produto = loja.produtos.get(codigo)
        nome = produto.nome if produto else "(produto removido)"
        linhas.append(f"  {posicao}. {codigo} - {nome}: {unidades} unidades")

    # ---------- Top 3 clientes que mais gastaram ----------
    linhas.append("")
    linhas.append("Clientes que mais gastaram:")
    top_clientes = [c for c in loja.clientes_que_mais_gastaram(3) if c.total_gasto > 0]
    if len(top_clientes) == 0:
        linhas.append("  (nenhum)")
    for posicao, cliente in enumerate(top_clientes, start=1):
        linhas.append(f"  {posicao}. {cliente.nome} ({cliente.nif}, {cliente.tipo()}): "
                      f"{cliente.total_gasto:.2f} €")

    return "\n".join(linhas)


def guardar_relatorio(texto, nome_ficheiro):
    """Escreve o relatório num ficheiro de texto (substitui o anterior)."""
    with open(nome_ficheiro, "w", encoding="utf-8") as f:
        f.write(texto + "\n")
        