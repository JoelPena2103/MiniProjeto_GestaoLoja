# loja.py
# A classe Loja: guarda os produtos e os clientes e aplica as regras de negócio.
#
# Quando algo não é permitido, os métodos lançam um ValueError com uma
# mensagem clara (ou StockInsuficienteError, no caso do stock).
# Quem chama (o menu) apanha o erro e mostra a mensagem.

from modelos import Venda, ClientePremium, StockInsuficienteError

LIMITE_PREMIUM = 1000.0   # a partir deste total gasto, o cliente passa a premium


class Loja:
    def __init__(self):
        # Dicionários para procurar rapidamente:
        #   produtos: código -> Produto
        #   clientes: NIF    -> Cliente
        self.produtos = {}
        self.clientes = {}

    # -----------------------------------------------------------
    # Produtos
    # -----------------------------------------------------------
    def adicionar_produto(self, produto):
        """Acrescenta um produto. Recusa códigos que já existam."""
        if produto.codigo in self.produtos:
            raise ValueError(f"Já existe um produto com o código {produto.codigo}.")
        self.produtos[produto.codigo] = produto

    def obter_produto(self, codigo):
        """Procura um produto pelo código (aceita minúsculas e espaços à volta)."""
        codigo = codigo.strip().upper()
        if codigo not in self.produtos:
            raise ValueError(f"Não existe nenhum produto com o código '{codigo}'.")
        return self.produtos[codigo]

    def importar_produtos(self, lista_produtos):
        """Adiciona vários produtos de uma vez (por ex. vindos do CSV).
        Os que já existirem na loja são ignorados.
        Devolve quantos foram importados e a lista de avisos."""
        importados = 0
        avisos = []
        for produto in lista_produtos:
            try:
                self.adicionar_produto(produto)
                importados += 1
            except ValueError as erro:
                avisos.append(f"{erro} Ignorado.")
        return importados, avisos

    def repor_stock(self, codigo, quantidade):
        """Repõe stock de um produto. Devolve o produto atualizado."""
        produto = self.obter_produto(codigo)
        produto.repor(quantidade)
        return produto

    def valor_total_stock(self):
        """Soma de preço x stock de todos os produtos."""
        total = 0
        for produto in self.produtos.values():
            total += produto.preco * produto.stock
        return total

    # -----------------------------------------------------------
    # Clientes
    # -----------------------------------------------------------
    def adicionar_cliente(self, cliente):
        """Acrescenta um cliente. Recusa NIF que já existam."""
        if cliente.nif in self.clientes:
            raise ValueError(f"Já existe um cliente com o NIF {cliente.nif}.")
        self.clientes[cliente.nif] = cliente

    def obter_cliente(self, nif):
        nif = nif.strip()
        if nif not in self.clientes:
            raise ValueError(f"Não existe nenhum cliente com o NIF '{nif}'.")
        return self.clientes[nif]

    def clientes_que_mais_gastaram(self, quantos=3):
        """Devolve os clientes ordenados do que gastou mais para o que gastou menos."""
        ordenados = sorted(self.clientes.values(),
                           key=lambda cliente: cliente.total_gasto,
                           reverse=True)
        return ordenados[:quantos]

    # -----------------------------------------------------------
    # Vendas
    # -----------------------------------------------------------
    def registar_venda(self, nif, pedidos):
        """Regista uma venda.

        nif:     NIF do cliente
        pedidos: lista de tuplos (codigo, quantidade)

        Funciona em DUAS FASES para que uma venda falhada não altere nada:
          1) valida tudo, sem mexer em nada;
          2) só se estiver tudo bem, retira o stock e atualiza o cliente.
        Devolve a Venda criada.
        """
        # ---------- Fase 1: validar ----------
        cliente = self.obter_cliente(nif)          # erro se o cliente não existir

        if len(pedidos) == 0:
            raise ValueError("A venda não tem produtos.")

        # Juntar as quantidades por produto. Se o mesmo produto aparecer
        # duas vezes (ex.: 3 ratos + 2 ratos), temos de verificar 5 de uma vez.
        quantidades = {}                           # codigo -> quantidade total
        for codigo, quantidade in pedidos:
            produto = self.obter_produto(codigo)   # erro se o produto não existir
            if quantidade <= 0:
                raise ValueError(f"Quantidade inválida para {produto.codigo}: "
                                 f"tem de ser positiva.")
            quantidades[produto.codigo] = quantidades.get(produto.codigo, 0) + quantidade

        linhas = []
        for codigo, quantidade in quantidades.items():
            produto = self.produtos[codigo]
            if quantidade > produto.stock:
                raise StockInsuficienteError(produto, quantidade)
            linhas.append((produto, quantidade))

        # ---------- Fase 2: aplicar (aqui já nada pode falhar) ----------
        venda = Venda(cliente, linhas)
        for produto, quantidade in linhas:
            produto.retirar(quantidade)

        cliente.total_gasto = round(cliente.total_gasto + venda.total(), 2)
        self._verificar_promocao(cliente)
        return venda

    def _verificar_promocao(self, cliente):
        """Se um cliente normal chegou aos 1000 €, passa a premium.
        Como não se pode mudar a classe de um objeto, cria-se um
        ClientePremium novo com os mesmos dados e substitui-se o antigo."""
        if cliente.tipo() == "normal" and cliente.total_gasto >= LIMITE_PREMIUM:
            novo = ClientePremium(cliente.nif, cliente.nome, cliente.total_gasto)
            self.clientes[cliente.nif] = novo
            return True
        return False