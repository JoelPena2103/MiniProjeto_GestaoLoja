<br>

<h1 align="center"><ins><i>Mini Projeto - Gestão de Loja - InfoPorto</i></ins></h1>

<p align="center">Programa de terminal em Python para gerir os produtos, os clientes e as vendas da loja de informática InfoPorto.</p>

<br>

## Como executar

O projeto só usa módulos que já vêm com o Python (`json`, `csv`, `os`, `datetime`), por isso não é preciso instalar pacotes.

```bash
python3 -m venv .venv
source .venv/bin/activate
python main.py
```

Na primeira execução a loja começa vazia. Usa a opção **6** e escreve `produtos_iniciais.csv` para importar os produtos.

## Menu

| Opção | O que faz |
|:-----:|-----------|
| 1 | Mostra todos os produtos |
| 2 | Mostra todos os clientes |
| 3 | Pede o NIF e o nome e cria um cliente |
| 4 | Nova venda: pede o NIF e depois código e quantidade, até o código ficar vazio |
| 5 | Repõe o stock de um produto |
| 6 | Importa produtos de um ficheiro CSV |
| 7 | Gera e mostra o relatório |
| 0 | Guarda os dados e termina |

## Ficheiros do projeto

| Ficheiro | Responsabilidade | Usa |
|:--------:|------------------|:---:|
| `modelos.py` | O que é um produto, um cliente, um cliente premium e uma venda. A excepção de falta de stock. | datetime |
| `loja.py` | A classe `Loja`: guarda produtos e clientes e aplica as regras de negócio. | modelos |
| `armazenamento.py` | Ler e escrever ficheiros: JSON (produtos, clientes) e CSV (importação e histórico). | modelos, loja |
| `relatorio.py` | Calcula as estatísticas e monta o texto do relatório. | – |
| `main.py` | O menu: fala com o utilizador (`input`/`print`). É o único que se executa. | todos os outros |
| `produtos_iniciais.csv` | Os produtos da loja (fornecido). | – |

### Uma regra que atravessa todo o projeto

Só o `main.py` fala com o utilizador: é o único ficheiro que usa `input` e `print`, e é por ele que o programa arranca. Faz a ponte de ligação para os outros ficheiros, que nunca escrevem no ecrã: **devolvem resultados ou lançam erros**, e o menu decide o que mostrar.

## `modelos.py` – as classes

Este ficheiro tem as classes usadas no programa.

*Uma classe* é um molde, e damos-lhe o nome do tipo de objeto que representa.
*Um objeto* é uma coisa concreta feita a partir do molde.

Quero isto dizer que a InfoPorto pode ter vários clientes diferentes, cada um com os seus dados e cada um único, mas todos são clientes: cada cliente é um objeto, e o molde é a classe `Cliente`. O mesmo se passa com os produtos: são objetos diferentes, mas todos são um `Produto`.

As classes criam-se com `class` e o nome da classe. O método `__init__` é o construtor, onde se guardam os dados do próprio objeto em `self`:

```python
class Produto:
    def __init__(self, codigo, nome, preco, stock=0):
        self.codigo = codigo
```

**`Produto`** tem os métodos:

- `retirar()` – retira as unidades vendidas ao stock. Lança `ValueError` se a quantidade for negativa ou 0, e `StockInsuficienteError` se se retirarem mais unidades do que as que existem, para o stock nunca ficar negativo.
- `repor()` – acrescenta unidades ao stock. Lança o mesmo `ValueError` se a quantidade for negativa ou 0.
- `para_dict()` – converte o produto num dicionário (chave: valor) para guardar em JSON.

**`Cliente`** tem os dados `nif`, `nome` e `total_gasto`:

```python
class Cliente:
    def __init__(self, nif, nome, total_gasto=0.0):
        self.nif = nif
```

Tem os métodos `desconto()`, que devolve a percentagem de desconto (0.0), `tipo()`, que devolve `"normal"`, e `para_dict()`, que o converte em dicionário guardando também o tipo.

**`ClientePremium`** herda de `Cliente` e só reescreve `desconto()` (0.10, ou seja 10%) e `tipo()` (`"premium"`). Ao carregar do JSON, a função `cliente_de_dict()` olha para o tipo guardado, para um cliente premium voltar a ser premium.

**`Venda`** guarda o cliente, a data e hora e as linhas (produto e quantidade), e calcula o subtotal, o desconto e o total a pagar. A venda não mexe no stock: isso é trabalho da `Loja`.

**`StockInsuficienteError`** é a excepção própria: diz qual o produto, quantas unidades foram pedidas e quantas existem.

## `loja.py` – as regras de negócio

O `loja.py` liga-se ao `modelos.py` com:

```python
from modelos import Venda, ClientePremium, StockInsuficienteError
```

A `Loja` guarda tudo em dois dicionários, para procurar produtos pelo código e clientes pelo NIF:

```python
self.produtos = {}   # código -> Produto    ex.: {"P002": <Rato>, ...}
self.clientes = {}   # NIF    -> Cliente    ex.: {"111222333": <Joel>, ...}
```

Métodos:

- `adicionar_produto()` – junta o produto. Se o código já existir → `ValueError`.
- `obter_produto()` – limpa os espaços e passa a maiúsculas (`.strip().upper()`) e procura. Se não existir → `ValueError` com mensagem clara.
- `importar_produtos()` – tenta adicionar cada produto; os que já existem são ignorados. Devolve quantos entraram e a lista de avisos.
- `repor_stock()` – procura o produto e chama `produto.repor()`.
- `valor_total_stock()` – soma preço × stock de todos os produtos.
- `adicionar_cliente()` – junta o cliente. Se o NIF já existir → `ValueError`.
- `obter_cliente()` – procura pelo NIF. Se não existir → `ValueError`.
- `clientes_que_mais_gastaram()` – ordena os clientes pelo total gasto, do maior para o menor, e devolve os 3 primeiros.
- `registar_venda()` – regista uma venda em duas fases: **primeiro valida tudo** (cliente, lista vazia, produtos, quantidades e stock) e **só depois altera** o stock e o total gasto. Assim, uma venda que não possa ser concluída não altera nada.
- `_verificar_promocao()` – quando um cliente normal chega aos 1000 € gastos, passa automaticamente a premium.

## `armazenamento.py` – ficheiros

Os nomes dos ficheiros começam pelo prefixo `loja`:

| Ficheiro | Conteúdo |
|----------|----------|
| `loja_produtos.json` | Produtos da loja |
| `loja_clientes.json` | Clientes da loja |
| `loja_vendas.csv` | Histórico de vendas, uma linha por produto vendido |
| `loja_relatorio.txt` | O último relatório gerado |

- `guardar_loja()` / `carregar_loja()` – guardam e carregam produtos e clientes em JSON. Se os ficheiros não existirem, a loja começa vazia; se estiverem corrompidos, o programa avisa e começa vazio.
- `importar_produtos_csv()` – lê o CSV de produtos. As linhas com dados inválidos (preço ou stock que não são números, campos em falta, código repetido) são ignoradas com um aviso.
- `registar_venda_historico()` – acrescenta a venda ao fim do histórico (modo `"a"`), por isso as vendas anteriores nunca se perdem. O cabeçalho só é escrito uma vez.
- `ler_historico()` – lê o histórico para o relatório.

## `relatorio.py` – o relatório

O relatório é mostrado no ecrã e guardado em `loja_relatorio.txt`. Contém:

- número de linhas de venda e de clientes diferentes que já compraram;
- faturação total e valor médio por linha de venda;
- valor total em stock;
- os 3 produtos mais vendidos (com as unidades) e os 3 clientes que mais gastaram.

Se ainda não houver vendas, o relatório diz isso mesmo.

## `main.py` – o menu

Mostra o menu e repete-o até o utilizador escolher sair. Cada opção é uma função, e um `try/except` no ciclo do menu apanha qualquer erro, mostra uma mensagem curta e volta ao menu: **o programa nunca termina com um erro**. As quantidades têm de ser números inteiros positivos; se o utilizador escrever outra coisa, o programa avisa e pede outra vez.
