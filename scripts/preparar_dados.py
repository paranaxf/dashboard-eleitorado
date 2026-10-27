"""
Gera o CSV usado no dashboard a partir do arquivo oficial do TSE.

Fonte: TSE - Portal de Dados Abertos, conjunto "Eleitorado - Atual"
https://dadosabertos.tse.jus.br/dataset/eleitorado-atual
Arquivo: https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_ATUAL.zip

O arquivo original tem milhões de linhas (uma por município, zona, gênero,
estado civil, faixa etária e escolaridade). Este script soma os eleitores por
Estado + Escolaridade + Faixa etária, gerando uma base pequena para o Streamlit.

Uso:
    python scripts/preparar_dados.py perfil_eleitorado_ATUAL.zip
"""

import re
import sys
import unicodedata
import zipfile
from pathlib import Path

import pandas as pd

SAIDA_CSV = Path("dados/eleitorado_tse.csv")
SAIDA_INFO = Path("dados/fonte.txt")
URL_FONTE = "https://cdn.tse.jus.br/estatistica/sead/odsele/perfil_eleitorado/perfil_eleitorado_ATUAL.zip"

COLUNAS = ["DT_GERACAO", "SG_UF", "DS_FAIXA_ETARIA", "DS_GRAU_ESCOLARIDADE", "QT_ELEITORES_PERFIL"]

# Nomes mais legíveis para a escolaridade (chave sem acento e em maiúsculas)
ESCOLARIDADE = {
    "ANALFABETO": "Analfabeto",
    "LE E ESCREVE": "Lê e escreve",
    "ENSINO FUNDAMENTAL INCOMPLETO": "Fundamental incompleto",
    "ENSINO FUNDAMENTAL COMPLETO": "Fundamental completo",
    "ENSINO MEDIO INCOMPLETO": "Médio incompleto",
    "ENSINO MEDIO COMPLETO": "Médio completo",
    "SUPERIOR INCOMPLETO": "Superior incompleto",
    "SUPERIOR COMPLETO": "Superior completo",
    "NAO INFORMADO": "Não informado",
}


def sem_acento(texto):
    texto = unicodedata.normalize("NFKD", str(texto))
    return "".join(c for c in texto if not unicodedata.combining(c)).upper().strip()


def agrupar_idade(texto):
    """'21 a 24 anos' -> '18 a 24 anos'. Usa o primeiro número da faixa do TSE."""
    numero = re.search(r"\d+", str(texto))
    if numero is None:
        return "Não informado"
    idade = int(numero.group())
    if idade < 18:
        return "16 e 17 anos"
    if idade < 25:
        return "18 a 24 anos"
    if idade < 35:
        return "25 a 34 anos"
    if idade < 45:
        return "35 a 44 anos"
    if idade < 60:
        return "45 a 59 anos"
    if idade < 70:
        return "60 a 69 anos"
    return "70 anos ou mais"


def main(caminho_zip):
    with zipfile.ZipFile(caminho_zip) as z:
        nome_csv = next(n for n in z.namelist() if n.lower().endswith(".csv"))
        print("Lendo", nome_csv)

        partes = []
        data_geracao = None
        with z.open(nome_csv) as f:
            # Lê em pedaços para não estourar a memória
            for bloco in pd.read_csv(
                f, sep=";", encoding="latin1", usecols=COLUNAS,
                dtype=str, chunksize=1_000_000,
            ):
                data_geracao = data_geracao or bloco["DT_GERACAO"].iloc[0]
                bloco["QT_ELEITORES_PERFIL"] = pd.to_numeric(bloco["QT_ELEITORES_PERFIL"])
                partes.append(
                    bloco.groupby(["SG_UF", "DS_FAIXA_ETARIA", "DS_GRAU_ESCOLARIDADE"])["QT_ELEITORES_PERFIL"].sum()
                )

    df = pd.concat(partes).groupby(level=[0, 1, 2]).sum().reset_index()

    df["Estado"] = df["SG_UF"].str.strip().replace({"ZZ": "Exterior"})
    df["Faixa_Etaria"] = df["DS_FAIXA_ETARIA"].map(agrupar_idade)
    chave = df["DS_GRAU_ESCOLARIDADE"].map(sem_acento)
    df["Escolaridade"] = chave.map(ESCOLARIDADE).fillna(df["DS_GRAU_ESCOLARIDADE"].str.strip().str.capitalize())

    final = (
        df.groupby(["Estado", "Escolaridade", "Faixa_Etaria"], as_index=False)["QT_ELEITORES_PERFIL"]
        .sum()
        .rename(columns={"QT_ELEITORES_PERFIL": "Total_Eleitores"})
        .sort_values(["Estado", "Faixa_Etaria", "Escolaridade"])
    )

    SAIDA_CSV.parent.mkdir(exist_ok=True)
    final.to_csv(SAIDA_CSV, index=False, encoding="utf-8")
    SAIDA_INFO.write_text(
        "Fonte: TSE - Portal de Dados Abertos, conjunto 'Eleitorado - Atual'\n"
        f"Arquivo original: {URL_FONTE}\n"
        f"Data de geração informada pelo TSE (DT_GERACAO): {data_geracao}\n"
        f"Total de eleitores: {int(final['Total_Eleitores'].sum())}\n",
        encoding="utf-8",
    )

    print(SAIDA_INFO.read_text(encoding="utf-8"))
    print("Linhas geradas:", len(final))
    print("Escolaridades:", sorted(final["Escolaridade"].unique()))
    print("Faixas:", sorted(final["Faixa_Etaria"].unique()))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "perfil_eleitorado_ATUAL.zip")
