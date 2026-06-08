# Agente de Resolução de Labirintos

> Aplicação para visualização, simulação e análise de algoritmos de **Busca Clássica** e **Busca Local** em labirintos, desenvolvida para a disciplina de Inteligência Artificial.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white)
![Plataforma](https://img.shields.io/badge/Plataforma-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey)
[![Releases](https://img.shields.io/badge/Download-Releases-orange?logo=github)](https://github.com/GabrielFrazz/V01_Agent/releases)

---

## Sumário

- [Funcionalidades](#funcionalidades)
- [Executando os Binários Compilados](#1-executando-os-binários-compilados)
- [Executando o Código-Fonte](#2-executando-o-código-fonte)
- [Formato de Labirintos](#formato-de-labirintos-suportados)
- [Relatórios e Exportação](#relatórios-e-exportação)

---

## Funcionalidades

| Categoria | Algoritmos / Recursos                          |
|---|------------------------------------------------|
| Busca Não-Informada | BFS, DFS, UCS                                  |
| Busca Heurística | Gulosa, A*                                     |
| Busca Local | Hill-Climbing, Simulated Annealing             |
| Ambiente Dinâmico | Replanning com A*                              |
| Análise | Exportação CSV, gráficos de convergência       |
| Interface | Controle de velocidade, métricas em tempo real |

---

## 1. Executando os Binários Compilados

Caso não possua o Python instalado, baixe o executável correspondente ao seu sistema operacional na página de **[Releases](https://github.com/GabrielFrazz/V01_Agent/releases)** deste repositório.

### Windows

Baixe o **`MazeSolver_Setup.exe`** (instalador) ou o **`MazeSolver_Windows_Portable.zip`** (versão portátil).

> **Nota:** O Windows Defender pode bloquear a execução na primeira vez por ausência de assinatura digital comercial. Clique em **"Mais informações" → "Executar assim mesmo"** para prosseguir.

### Linux

Baixe o **`MazeSolver_Linux_Portable.tar.gz`**, extraia e execute:

```bash
chmod +x MazeSolver
./MazeSolver
```

### macOS

Baixe o **`MazeSolver_macOS_Portable.zip`** e extraia o `MazeSolver.app`.

> **Nota:** O Gatekeeper da Apple bloqueia aplicativos não assinados por padrão. Para liberar a execução, rode o seguinte comando no terminal dentro da pasta onde o app foi extraído:
> ```bash
> xattr -cr MazeSolver.app
> ```

---

## 2. Executando o Código-Fonte

### Pré-requisitos

- Python **3.10 ou superior**
- *(Somente Linux)* Pacote de renderização de janelas: `sudo apt install python3-tk`

### Passo a Passo

**1. Clone o repositório:**
```bash
git clone <url_do_repositório>
cd TrabalhoPratico
```

**2. Crie e ative um ambiente virtual:**

| Sistema | Criar | Ativar |
|---|---|---|
| Windows | `python -m venv .venv` | `.venv\Scripts\activate` |
| Linux / macOS | `python3 -m venv .venv` | `source .venv/bin/activate` |

**3. Instale as dependências:**
```bash
pip install -r requirements.txt
```

**4. Inicie a aplicação:**
```bash
python main.py
```

---

## Formato de Labirintos Suportados

O aplicativo lê arquivos de texto (`.txt`). Os caracteres reconhecidos são:

| Caractere | Significado |    Obrigatório    |
|:---:|---|:-----------------:|
| `#` | Parede (caminho bloqueado) |         ✓         |
| ` ` | Caminho livre |        ✓          |
| `A` | Ponto de início | ✓ (exatamente um) |
| `B` | Objetivo final | ✓ (exatamente um) |
| `C` | Ponto de coleta (Hill Climbing / SA) |     Opcional      |

**Exemplo:**
```
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

**Dica de geração:**
Utilize o gerador [ASCII Maze Generator](https://www.asciiart.eu/ascii-maze-generator). Defina o *Theme* como **Classic** e substitua os marcadores de início/fim por `A` e `B`, depois copie e cole em um arquivo (`.txt`).

---

## Relatórios e Exportação

Ao concluir uma busca com sucesso, o aplicativo salva automaticamente:

- **Planilhas** em `.csv`
- **Gráficos comparativos** em `.png`

Os arquivos são gravados na pasta `MazeSolver`, localizada na **pasta pessoal** do usuário. Você pode acessá-la diretamente pelo botão **"Abrir"** no painel lateral da aplicação, ou alterar o diretório de destino no canto superior direito da aplicação.