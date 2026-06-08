# Auditoria de Uso de IA — TP01

## 1. Ferramentas utilizadas

| Ferramenta | Versão/Modelo | Uso principal |
|------------|---------------|---------------|
| Claude (Anthropic) | claude-sonnet-4-6 | Revisão da modelagem PEAS, especificação da arquitetura do sistema e definição do passo a passo. |
| Antigravity (Google) | Gemini 3.1 Pro | Criação do esqueleto do projeto, pair programming, revisão de código e refatoração da interface legada. |

## 2. Principais prompts utilizados

### Prompt 1 — Revisão da modelagem e arquitetura (Claude)
> "Eu quero que leia esse documento PDF. Ele é a descrição de um trabalho de inteligência artificial pra faculdade. Nós já fizemos a modelagem PEAS inicial do trabalho. Quero que você revise a nossa modelagem, descreva o que é pra ser feito, o que é pra ser entregue, e me guie com um passo a passo de como fazer a arquitetura e estruturar as bibliotecas desse sistema da melhor forma possível. 
> 
> Também deixei o link de um repositório do GitHub de um trabalho que fiz em outra disciplina, que era busca em labirintos Bitmap. Quero reaproveitar pelo menos a parte da interface gráfica com Tkinter do código legado para renderizar a interface desse novo labirinto em grade de texto. Veja se isso seria possível de fato."

**Resultado:** O Claude validou a nossa modelagem PEAS, sugeriu a estrutura de pastas (`core/`, `search/`, `interface.py`) e recomendou trocar a leitura de imagens `.bmp` por `canvas.create_rectangle()` para a visualização. Forneceu também as assinaturas básicas para os algoritmos.

### Prompt 2 — Esqueleto inicial do sistema (Antigravity)
> "Vou te passar o documento de especificação gerado pelo Claude com a arquitetura do nosso projeto. Quero que atue como um engenheiro de software e crie a estrutura de pastas, os arquivos e coloque neles apenas as declarações/headers das classes e funções em Python. Configure nosso ambiente básico"

**Resultado:** O Antigravity construiu todos os arquivos `.py` baseados nos cabeçalhos e montou o esqueleto funcional do sistema.

## 3. Trechos de código sugeridos por IA

**Estrutura do Labirinto (`core/maze.py`)** (Sugerido pelo Claude)
```python
class Maze:
    def __init__(self, filepath): ...
    def _load(self, filepath): ...
    def is_free(self, r, c): ...
    def neighbors(self, r, c): ...
```
**Modificações feitas:** Nós implementamos a lógica do parser para tratar os diferentes caracteres e tratar adequadamente arquivos de mapa mal formatados.

**Refatoração de UI (`interface.py`)** (Sugerido pelo Antigravity durante *Pair Programming*)
O Antigravity nos auxiliou ativamente durante a construção de novas funções na interface gráfica e na modernização do código antigo com `ttkthemes`.

## 4. Sugestões rejeitadas

- **Funcionalidades fora do escopo:** Em determinado momento da especificação, o Claude inventou mecânicas adicionais desnecessárias e sugeriu implementações avançadas (como visualização 3D/Pygame). Mandamos ele retirar e focar apenas no Tkinter 2D puro.
- **Uso de bibliotecas externas prontas:** A IA chegou a sugerir o uso de pacotes de grafos (como o `networkx`) para facilitar as buscas locais. 
## 5. Erros cometidos pela IA

- **Heurística Inadequada:** A IA sugeriu em alguns trechos do A* o uso de distância Euclidiana. **Correção:** Nós alteramos manualmente para a distância de Manhattan (`manhattan(a, b)`), visto que as movimentações nos nossos labirintos são ortogonais.
- **Imports Circulares:** O Antigravity, ao sugerir refatorações rápidas, ocasionalmente induziu a referências circulares entre o módulo de interface e os algoritmos. Tivemos que rearranjar as importações manualmente.
- **Falta de tratamento de caminhos impossíveis:** O esqueleto inicial da Busca Local fornecido pela IA quebrava se a distância pré-computada entre dois pontos (ex: A -> C) fosse infinita (inalcançável).

## 6. Como o grupo validou a solução

- **Revisão da Especificação Arquitetural:** Para validar a arquitetura e os passos gerados pelo Claude, fizemos uma verificação cruzada lendo cada item sugerido e confrontando com os requisitos obrigatórios do PDF do trabalho.
- **Validação do Código Base (Esqueleto):** Os cabeçalhos de classes e estruturas criados pelo Antigravity foram lidos e comparados com a teoria de buscas vista em sala de aula (ex: garantindo que as assinaturas do A* ou do Hill-Climbing recebiam os parâmetros corretos exigidos).
- **Testes Manuais de Pair Programming:** Qualquer trecho de código sugerido ativamente pela IA (especialmente os da refatoração da interface Tkinter) não foi aceito ou copiado cegamente. Nós executávamos a aplicação para cada trecho novo.
- **Razão online/offline ≥ 1:** validamos que `ρ` nunca foi inferior a 1,
  o que seria matematicamente impossível e indicaria bug.

## 7. Modificações feitas pelo grupo

- A construção das `MazeView` (o estado reduzido do labirinto usado para o Agente Online).
- A função de geração aleatória de mapas integrando ao sistema.
- Por fim, a resolução de problemas de permissão no Windows, como pré compilamos versões para alguns sistemas operacionais, na hora de salvar e extrair os aplicativos (movendo os *saves* do `Program Files` para o `home` do usuário) foi uma alteração feita no final do processo de build e release.
