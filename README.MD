## Como Executar

O projeto já conta com um ambiente virtual (`venv`) configurado para Python 3.14. Para rodar o programa, basta seguir os passos abaixo no seu terminal (cmd ou PowerShell):

### 1. Ative o ambiente virtual
**No Windows:**
```cmd
venv\Scripts\activate
```

### 2. Instale as dependências
Caso ainda não tenha instalado as bibliotecas necessárias (como `matplotlib` e `ttkthemes`):
```cmd
pip install -r requirements.txt
```

### 3. Inicie o Programa

Você tem duas formas de utilizar o projeto:

**Modo Interface Gráfica (Recomendado)**
Abre a janela interativa onde você pode carregar labirintos, escolher o algoritmo, ajustar a velocidade e assistir à animação do agente ao vivo. Os resultados e gráficos serão automaticamente exportados para a pasta `results/`.
```cmd
python main.py
```

**Modo Lote (Batch CLI)**
Executa todos os algoritmos (Clássicos, Locais e Online) de forma invisível e ultra-rápida no labirinto especificado, exportando diretamente todas as métricas, arquivos `.csv` e gráficos para a pasta `results/`.
```cmd
python main.py --batch mazes/maze_simple.txt
```
*(Substitua `mazes/maze_simple.txt` pelo caminho do labirinto que deseja testar)*.
