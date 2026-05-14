from langchain_openrouter import ChatOpenRouter
from pydantic import SecretStr
from typing import cast
from langchain_classic.chains import LLMChain
from langchain_core.prompts import PromptTemplate
from langchain_deepseek import ChatDeepSeek
from dotenv import load_dotenv
import os
import json
import fitz
import sys
print(sys.executable)


load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError(
        "DEEPSEEK_API_KEY não encontrada. Verifique seu arquivo .env.")


def extrair_transacoes_do_pdf(caminho_pdf):

    texto_bruto = ""
    try:
        with fitz.open(caminho_pdf) as doc:
            paginas_texto = []
            for pagina in doc:
                texto_pagina = pagina.get_text()
                if texto_pagina:  # Verifica se não é None ou vazio
                    paginas_texto.append(texto_pagina)
            texto_bruto = "\n".join(paginas_texto)
    except Exception as e:
        raise Exception(f"Erro ao ler o arquivo PDF: {e}")

    llm = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0,
        api_key=DEEPSEEK_API_KEY  # type: ignore


    )

    prompt_template = PromptTemplate(
        input_variables=["texto_extrato"],
        template="""
        Você é um assistente financeiro especializado em análise de extratos bancários.
        Analise o texto do extrato bancário fornecido e extraia todas as transações.

        Para cada transação, identifique a data, a descrição (ou histórico) e o valor.
        Valores de crédito (entradas) devem ser representados como números positivos.
        Valores de débito (saídas) devem ser representados como números negativos.

        Retorne APENAS uma lista de objetos JSON válida, sem comentários ou explicações adicionais.
        Siga estritamente o seguinte esquema:

        [
            {{
                "data": "DD/MM/AAAA",
                "descricao": "HISTORICO DA TRANSACAO",
                "valor": 00.00
            }},
            ...
        ]

        Se o texto não contiver transações claras, retorne uma lista vazia: []

        Texto do extrato:
        {texto_extrato}
        """
    )

    chain = LLMChain(llm=llm, prompt=prompt_template)
    resposta_str = chain.run(texto_extrato=texto_bruto)

# --- LIMPEZA PARA JSON ---
    start_index = resposta_str.find('[')
    end_index = resposta_str.rfind(']')

    if start_index != -1 and end_index != -1 and end_index > start_index:
        resposta_str = resposta_str[start_index:end_index+1]
    else:
        start_index = resposta_str.find('{')
        end_index = resposta_str.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_candidato = resposta_str[start_index:end_index+1]
            if json_candidato.count('{') > 1:
                json_candidato = '[' + json_candidato + ']'
            resposta_str = json_candidato

    if resposta_str.startswith("```json"):
        resposta_str = resposta_str[7:]
    if resposta_str.startswith("```"):
        resposta_str = resposta_str[3:]
    if resposta_str.endswith("```"):
        resposta_str = resposta_str[:-3]
    resposta_str = resposta_str.strip()

    import re
    resposta_str = re.sub(r',\s*]', ']', resposta_str)
    resposta_str = re.sub(r',\s*}', '}', resposta_str)
    # --- FIM DA LIMPEZA ---

    try:
        transacoes = json.loads(resposta_str)
        if not isinstance(transacoes, list):
            raise ValueError("A resposta da LLM não é uma lista.")
        return transacoes
    except json.JSONDecodeError as e:
        print("----- Resposta bruta que falhou no parsing -----")
        print(repr(resposta_str))
        print("-----------------------------------------------")
        raise ValueError(f"A LLM não retornou um JSON válido. Erro: {e}")
