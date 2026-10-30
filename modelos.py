# modelos.py
# Classes do projeto: Produto, Cliente, ClientePremium, Venda
# e a excepção própria para falta de stock.
 
from datetime import datetime
 
 
# ===============================================================
# Excepção própria para falta de stock
# Diz qual o produto, quantas unidades foram pedidas e quantas existem.
# ===============================================================
class StockInsuficienteError(Exception):
    def __init__(self, produto, pedido):
        self.produto = produto
        self.pedido = pedido
        self.existentes = produto.stock
        mensagem = (f"Stock insuficiente para '{produto.nome}' ({produto.codigo}): "
                    f"pedidas {pedido}, existem {produto.stock}.")
        super().__init__(mensagem)
 
 
# ===============================================================
# Produto
# ===============================================================
class Produto:
    def __init__(self, codigo, nome, preco, stock=0):
        self.codigo = codigo
        self.nome = nome
        self.preco = preco
        self.stock = stock
 
    def retirar(self, quantidade):
        """Retira unidades do stock."""
        if quantidade <= 0:
            raise ValueError("A quantidade tem de ser positiva.")
        if quantidade > self.stock:
            raise StockInsuficienteError(self, quantidade)
        self.stock -= quantidade
 
    def repor(self, quantidade):
        """Acrescenta unidades ao stock."""
        if quantidade <= 0:
            raise ValueError("A quantidade tem de ser positiva.")
        self.stock += quantidade
 
    def para_dict(self):
        """Converte o produto num dicionário, para guardar em JSON."""
        return {
            "codigo": self.codigo,
            "nome": self.nome,
            "preco": self.preco,
            "stock": self.stock,
        }
 
    def __str__(self):
        return f"{self.codigo} | {self.nome:<35} | {self.preco:>8.2f} € | stock: {self.stock}"
 
 
def produto_de_dict(dados):
    """Recria um Produto a partir de um dicionário lido do JSON."""
    return Produto(dados["codigo"], dados["nome"], dados["preco"], dados["stock"])
 
 
# ===============================================================
# Cliente (normal)
# ===============================================================
class Cliente:
    def __init__(self, nif, nome, total_gasto=0.0):
        self.nif = nif
        self.nome = nome
        self.total_gasto = total_gasto
 
    def desconto(self):
        """Percentagem de desconto (0.10 = 10%)."""
        return 0.0
 
    def tipo(self):
        return "normal"
 
    def para_dict(self):
        """Converte o cliente num dicionário. Guarda o tipo para
        sabermos, ao carregar, se é normal ou premium."""
        return {
            "nif": self.nif,
            "nome": self.nome,
            "total_gasto": self.total_gasto,
            "tipo": self.tipo(),
        }
 
    def __str__(self):
        return (f"{self.nif} | {self.nome:<25} | {self.tipo():<8} | "
                f"gasto: {self.total_gasto:.2f} €")
 
 
# ===============================================================
# Cliente Premium: é um Cliente, mas com 10% de desconto
# ===============================================================
class ClientePremium(Cliente):
    def desconto(self):
        return 0.10
 
    def tipo(self):
        return "premium"
 
 
def cliente_de_dict(dados):
    """Recria um cliente a partir de um dicionário.
    Se foi guardado como premium, volta a ser ClientePremium."""
    if dados.get("tipo") == "premium":
        return ClientePremium(dados["nif"], dados["nome"], dados["total_gasto"])
    return Cliente(dados["nif"], dados["nome"], dados["total_gasto"])
 
 
# ===============================================================
# Venda
# Tem o cliente, a data/hora e uma lista de linhas (produto, quantidade).
# Nota: a Venda NÃO mexe no stock. Quem valida e retira o stock é a Loja,
# para garantir que uma venda falhada não altera nada.
# ===============================================================
class Venda:
    def __init__(self, cliente, linhas):
        self.cliente = cliente
        self.data_hora = datetime.now()
        self.linhas = linhas   # lista de tuplos (produto, quantidade)
 
    def subtotal(self):
        """Total sem desconto."""
        soma = 0
        for produto, quantidade in self.linhas:
            soma += produto.preco * quantidade
        return soma
 
    def valor_desconto(self):
        return self.subtotal() * self.cliente.desconto()
 
    def total(self):
        """Total a pagar, já com o desconto do cliente."""
        return self.subtotal() - self.valor_desconto()
 
    def __str__(self):
        texto = f"Venda de {self.data_hora:%d/%m/%Y %H:%M} - {self.cliente.nome} ({self.cliente.tipo()})\n"
        for produto, quantidade in self.linhas:
            texto += f"  {quantidade} x {produto.nome} = {produto.preco * quantidade:.2f} €\n"
        texto += f"  Subtotal: {self.subtotal():.2f} €\n"
        texto += f"  Desconto: {self.valor_desconto():.2f} €\n"
        texto += f"  Total:    {self.total():.2f} €"
        return texto
 