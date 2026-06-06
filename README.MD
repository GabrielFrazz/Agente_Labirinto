#  Agente de Resolução de Labirintos

Uma aplicação para visualização, simulação e análise de desempenho de algoritmos de **Busca Clássica** e **Busca Local** operando labirintos, desenvolvida para a disciplina de Inteligência Artificial.

##  Funcionalidades
- **Buscas Não-Informadas e Heurísticas:** BFS, DFS, UCS, Greedy e A*.
- **Otimização de Múltiplos Pontos (Busca Local):** Hill-Climbing e Simulated Annealing.
- **Ambiente Dinâmico:** Agente Online A* com neblina e replanejamento dinâmico.
- **Análise de Dados:** Exportação de métricas para CSV e geração de gráficos de convergência.
- **Interface Gráfica:** Controle de velocidade de animação, métricas e atalhos de usabilidade.

---

##  1. Como Executar (Versões Compiladas)

Se você não possui o Python instalado e quer apenas testar a aplicação, baixe os executáveis prontos na aba **Releases** deste repositório no GitHub.

###  Windows
Baixe o **`MazeSolver_Setup.exe`** ou o **`MazeSolver_Windows_Portable.zip`**.
> **Nota:** Por não possuir uma assinatura digital comercial, o *Windows Defender* vai bloquear a primeira execução.

###  Linux
Baixe o arquivo **`MazeSolver_Linux_Portable.tar.gz`** e extraia.
1. Abra o terminal na pasta que foi extraída.
2. Dê permissão de execução com o comando: `chmod +x MazeSolver`
3. Execute o programa: `./MazeSolver`

###  macOS
Baixe o arquivo **`MazeSolver_macOS_Portable.zip`** e extraia para obter o aplicativo nativo `MazeSolver.app`.
> **Nota** O *Gatekeeper* da Apple bloqueia a execução de apps não-assinados baixados da internet por padrão. Para liberar o aplicativo, abra o terminal na pasta onde ele foi extraído e rode o seguinte comando:
> ```bash
> xattr -cr MazeSolver.app
> ```

---

##  2. Como Executar (Código-Fonte)

### Pré-requisitos
- Python 3.10 ou superior
- *(Apenas Linux)*: Ter o pacote base de renderização de janelas instalado (Ex no Ubuntu: `sudo apt install python3-tk`)

### Passo a Passo

1. **Faça o clone ou baixe o repositório:**
   ```bash
   git clone <sua_url_do_github>
   cd TrabalhoPratico
   ```

2. **Crie o Ambiente Virtual (Recomendado):**
   - **Windows:** `python -m venv .venv`
   - **Linux / Mac:** `python3 -m venv .venv`

3. **Ative o Ambiente Virtual:**
   - **Windows:** `.venv\Scripts\activate`
   - **Linux / Mac:** `source .venv/bin/activate`

4. **Instale as dependências externas (Matplotlib, Pillow, etc):**
   ```bash
   pip install -r requirements.txt
   ```

5. **Inicie a Aplicação Gráfica:**
   ```bash
   python main.py
   ```

---

##  Formato de Labirintos Suportados

O aplicativo é capaz de ler qualquer labirinto no formato texto puro (`.txt`) mapeado em ASCII. O padrão interno que o sistema exige é o seguinte:

- `#` -> Parede (caminho bloqueado)
- `  ` (espaço) -> Caminho livre
- `A` -> Ponto de Início - *Deve haver exatamente um*
- `B` -> Objetivo Final - *Deve haver exatamente um*
- `C` -> Ponto de Coleta - *Opcional, usado pela Busca Local (Hill Climbing / SA)*

**Gerando novos labirintos:**
Se você deseja gerar labirintos gigantes e aleatórios para testar o desempenho dos algoritmos, recomendamos a utilização da ferramenta online gratuita:
 **[ASCII Maze Generator](https://www.asciiart.eu/ascii-maze-generator)**

> *Ao gerar no site, defina o "Theme" para Classic e troque os ponto inicial/final por A e B. Copie o texto gerado, cole em um arquivo `.txt`.*

**Exemplo de Labirinto Válido:**
```text
###########
#A # #    #
# ## # ## #
#    C    #
# ##   #  #
# C # #   #
###   ### #
#         #
##### # ###
#     B   #
###########
```

---

##  Onde ficam os relatórios?
Ao finalizar uma busca com sucesso, o aplicativo salva as planilhas detalhadas em `.csv` e os gráficos comparativos `.png` em um diretório chamado `MazeSolver_Results`, localizado na **Pasta Pessoal (Home)** do seu usuário no sistema operacional. 

Você pode acessar essa pasta com um clique através do botão **"Abrir"** no painel direito da própria aplicação.
Você também pode trocar diretório de salvamento na aplicação.
