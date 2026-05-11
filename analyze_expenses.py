# analyze_expenses.py
import os
import json
from pathlib import Path
from dotenv import load_dotenv
from pydantic import SecretStr
from langchain_deepseek import ChatDeepSeek
from collections import defaultdict

# Carrega o .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY não encontrada no arquivo .env")


def analisar_gastos_com_agente(lista_transacoes_json):
    """
    Usa a LLM apenas para classificar e gerar insights, economizando tokens.
    A matemática (resumo) e a junção dos dados são feitas no Python.
    """
    # 1. Preparar os dados com IDs para economizar tokens de saída da IA
    transacoes_com_id = []
    for i, t in enumerate(lista_transacoes_json):
        nova_t = t.copy()
        nova_t["id"] = str(i)  # Adiciona um identificador único
        transacoes_com_id.append(nova_t)

    transacoes_str = json.dumps(
        transacoes_com_id, indent=2, ensure_ascii=False)

    # LLM simples e direta
    llm = ChatDeepSeek(
        model="deepseek-chat",
        temperature=0,
        max_tokens=8000,
        api_key=SecretStr(DEEPSEEK_API_KEY)  # type: ignore
    )

    # Novo Prompt: Pedimos APENAS o mapeamento, sem reescrever o resto
    prompt_analise = f"""
Você é um assistente financeiro. Analise as transações abaixo.
Para economizar espaço, NÃO reescreva as transações inteiras. 

Sua resposta deve ser estritamente um JSON válido com o seguinte formato exato:
{{
    "mapa_categorias": {{
        "0": "Alimentação",
        "1": "Transporte",
        "2": "Lazer"
        // ... continue mapeando o ID de TODAS as transações fornecidas para a categoria correta.
    }},
    "recorrencias": ["Netflix", "Conta de Luz"], // array com descrições de cobranças recorrentes
    "insights": ["Sua maior despesa foi com X", "Dica: reduza Y"] // array com 2-3 percepções financeiras
}}

Categorias sugeridas: Alimentação, Transporte, Moradia, Lazer, Saúde, Educação, Assinaturas, Salário, Outros.

Transações para análise:
{transacoes_str}
"""

    resposta = llm.invoke(prompt_analise)
    conteudo = resposta.content

    # Tratamento para garantir string
    if isinstance(conteudo, list):
        conteudo = "".join(str(part) for part in conteudo)
    elif not isinstance(conteudo, str):
        conteudo = str(conteudo)

    texto_limpo = conteudo.strip()

    # Limpeza de markdown
    if texto_limpo.startswith("```json"):
        texto_limpo = texto_limpo[7:]
    if texto_limpo.startswith("```"):
        texto_limpo = texto_limpo[3:]
    if texto_limpo.endswith("```"):
        texto_limpo = texto_limpo[:-3]
    texto_limpo = texto_limpo.strip()

    # Tenta carregar o JSON da IA
    dados_ia = {}
    try:
        dados_ia = json.loads(texto_limpo)
    except json.JSONDecodeError:
        inicio = texto_limpo.find('{')
        fim = texto_limpo.rfind('}')
        if inicio != -1 and fim != -1:
            try:
                dados_ia = json.loads(texto_limpo[inicio:fim+1])
            except:
                return {"erro": "Falha ao processar o JSON da IA", "resposta_bruta": texto_limpo}
        else:
            return {"erro": "A IA não retornou um JSON válido", "resposta_bruta": texto_limpo}

    # 2. Reconstruir a resposta final usando Python (100% à prova de falhas matemáticas)
    transacoes_categorizadas = []
    resumo_por_categoria = defaultdict(float)
    mapa = dados_ia.get("mapa_categorias", {})

    for i, t in enumerate(lista_transacoes_json):
        # Se a IA por acaso esquecer uma transação, cai em "Outros"
        cat = mapa.get(str(i), "Outros")

        # Garante que o valor é um número float para a matemática
        valor = t.get("valor", 0.0)
        try:
            valor_float = float(valor)
        except (ValueError, TypeError):
            valor_float = 0.0

        # Monta o objeto final como o Streamlit espera
        nova_t = {
            "data": t.get("data", ""),
            "descricao": t.get("descricao", ""),
            "valor": valor_float,
            "categoria": cat
        }
        transacoes_categorizadas.append(nova_t)
        resumo_por_categoria[cat] += valor_float

    # Arredonda os valores do resumo para evitar dízimas (ex: 150.33333334)
    resumo_formatado = {k: round(v, 2)
                        for k, v in resumo_por_categoria.items()}

    # Retorna a estrutura perfeita que o app_streamlit e o FastAPI precisam
    return {
        "transacoes_categorizadas": transacoes_categorizadas,
        "resumo_por_categoria": resumo_formatado,
        "recorrencias": dados_ia.get("recorrencias", []),
        "insights": dados_ia.get("insights", [])
    }
