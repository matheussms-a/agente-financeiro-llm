# main.py
import os
import tempfile
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from extract_transactions import extrair_transacoes_do_pdf
from analyze_expenses import analisar_gastos_com_agente

app = FastAPI(
    title="Agente Financeiro Pessoal com IA",
    description="API para análise de extratos bancários em PDF.",
    version="1.0.0"
)


@app.post("/analisar-extrato/")
async def analisar_extrato(arquivo_pdf: UploadFile = File(...)):
    """
    Endpoint que recebe um extrato bancário em PDF, processa-o com IA
    e retorna uma análise detalhada dos gastos.
    """
    # Validação robusta do nome do arquivo
    if not arquivo_pdf.filename or not arquivo_pdf.filename.lower().endswith('.pdf'):
        return JSONResponse(
            status_code=400,
            content={
                "erro": "O arquivo enviado não é um PDF ou o nome do arquivo está ausente."}
        )

    # Salvar o arquivo temporariamente
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
        conteudo = await arquivo_pdf.read()
        tmp_file.write(conteudo)
        caminho_temporario = tmp_file.name

    try:
        transacoes = extrair_transacoes_do_pdf(caminho_temporario)
        if not transacoes:
            return JSONResponse(
                status_code=400,
                content={"erro": "Nenhuma transação encontrada no PDF."}
            )

        relatorio_final = analisar_gastos_com_agente(transacoes)
        return JSONResponse(content=relatorio_final)

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "erro": f"Ocorreu um erro durante o processamento: {str(e)}"}
        )
    finally:
        if os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)
