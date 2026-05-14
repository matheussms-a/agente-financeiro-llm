# Agente Financeiro Pessoal com IA (DeepSeek + LangChain)
Este projeto é um agente de inteligência artificial capaz de analisar extratos bancários em formato PDF, categorizar transações automaticamente e gerar insights financeiros personalizados. O sistema utiliza o modelo **DeepSeek-V3** via LangChain para o processamento de linguagem natural e oferece tanto uma interface visual quanto uma API robusta.
## Funcionalidades
**Extração Inteligente**: Leitura de PDFs e extração de dados estruturados (data, descrição, valor).
**Categorização Automática**: Classificação de gastos em categorias (Alimentação, Transporte, Lazer, etc.).
**Dashboard Interativo**: Interface Streamlit para upload de arquivos e visualização de gráficos de gastos.
**API REST**: Backend construído com FastAPI para integração com outros sistemas.
**Otimização de Tokens**: Implementação de mapeamento por ID para processar grandes volumes de dados (ex: extratos de 90 dias) de forma eficiente.
## Tecnologias Utilizadas
**Linguagem**: Python 3.10+
**IA**: DeepSeek (via LangChain)
**Interface**: Streamlit
**Backend**: FastAPI
**Processamento de PDF**: PyMuPDF (fitz)
**Manipulação de Dados**: Pandas
## Exemplos Visuais
![Demonstração do Dashboard](assets/dashboard-demo.png)
## Como Executar
### Pré-requisitos
Python instalado
Chave de API
### Configuração
Clone o repositório:
```bash
git clone https://github.com/seu-usuario/agente-financeiro-llm.git
