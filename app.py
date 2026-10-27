from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# ------------------------------------------------------------
# CONFIGURAÇÃO
# ------------------------------------------------------------
st.set_page_config(page_title="Perfil do Eleitorado", layout="wide")

BASE_PADRAO = Path(__file__).parent / "dados" / "eleitorado_tse.csv"
INFO_FONTE = Path(__file__).parent / "dados" / "fonte.txt"
LINK_FONTE = "https://dadosabertos.tse.jus.br/dataset/eleitorado-atual"
COLUNAS_ESPERADAS = ["Estado", "Escolaridade", "Faixa_Etaria", "Total_Eleitores"]

# Ordem lógica das categorias (do menor para o maior grau / da mais nova para a mais velha)
ORDEM_ESCOLARIDADE = [
    "Analfabeto", "Lê e escreve", "Fundamental incompleto", "Fundamental completo",
    "Médio incompleto", "Médio completo", "Superior incompleto", "Superior completo",
    "Não informado",
]
ORDEM_IDADE = [
    "16 e 17 anos", "18 a 24 anos", "25 a 34 anos", "35 a 44 anos",
    "45 a 59 anos", "60 a 69 anos", "70 anos ou mais", "Não informado",
]
# Escala ordenada (Viridis): roxo = menos escolaridade, amarelo = mais; cinza = não informado
CORES = dict(zip(
    ORDEM_ESCOLARIDADE,
    px.colors.sample_colorscale("Viridis", [i / 7 for i in range(8)]) + ["#9e9e9e"],
))


def formatar(n):
    """155432100 -> '155,4 milhões' (vírgula decimal, padrão brasileiro)."""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f} milhões".replace(".", ",")
    return f"{n:,.0f}".replace(",", ".")


def pct(x):
    return f"{x:.1f}%".replace(".", ",")


# ------------------------------------------------------------
# APRESENTAÇÃO
# ------------------------------------------------------------
st.title("Perfil do Eleitorado Brasileiro")

st.write("""
Este dashboard apresenta uma análise sobre os eleitores brasileiros cadastrados no TSE,
separados por **estado**, **escolaridade** e **faixa etária**.

O objetivo é responder três perguntas:
1. **Quais estados concentram mais eleitores?**
2. **Quais estados têm a maior proporção de eleitores com ensino superior completo?**
3. **Como a escolaridade dos eleitores muda entre as faixas de idade?**
""")

st.caption(f"Fonte: TSE – Portal de Dados Abertos, conjunto “Eleitorado – Atual” ({LINK_FONTE}).")
if INFO_FONTE.exists():
    with st.expander("Detalhes da fonte"):
        st.text(INFO_FONTE.read_text(encoding="utf-8"))

# ------------------------------------------------------------
# AULA 2 – UPLOAD
# ------------------------------------------------------------
arquivo = st.file_uploader("Envie o arquivo CSV (eleitorado_tse.csv)", type=["csv"])

if arquivo is not None:
    df = pd.read_csv(arquivo)
elif BASE_PADRAO.exists():
    st.info("Nenhum arquivo enviado: usando a base do TSE que acompanha o projeto.")
    df = pd.read_csv(BASE_PADRAO)
else:
    st.info("Envie o arquivo eleitorado_tse.csv para iniciar a análise.")
    st.stop()

faltando = [c for c in COLUNAS_ESPERADAS if c not in df.columns]
if faltando:
    st.error(f"O arquivo não tem as colunas necessárias: {faltando}")
    st.stop()

# ------------------------------------------------------------
# AULA 2 – VERIFICAÇÃO E TRATAMENTO
# ------------------------------------------------------------
st.subheader("1. Conhecendo e verificando os dados")

c1, c2, c3, c4 = st.columns(4)
c1.metric("Registros", df.shape[0])
c2.metric("Colunas", df.shape[1])
c3.metric("Valores ausentes", int(df.isnull().sum().sum()))
c4.metric("Linhas duplicadas", int(df.duplicated().sum()))

st.dataframe(df.head(10))

# Tratamentos mínimos — nenhum apaga dado válido:
# 1) tira espaços extras dos textos ("SP " e "SP" seriam estados diferentes)
for coluna in ["Estado", "Escolaridade", "Faixa_Etaria"]:
    df[coluna] = df[coluna].astype(str).str.strip()

# 2) garante que o total é número (texto inválido vira NaN em vez de quebrar a soma)
df["Total_Eleitores"] = pd.to_numeric(df["Total_Eleitores"], errors="coerce")
invalidos = int(df["Total_Eleitores"].isnull().sum())

# 3) remove só linhas 100% repetidas (contariam o mesmo grupo duas vezes)
duplicadas = int(df.duplicated().sum())
df = df.drop_duplicates()

total = df["Total_Eleitores"].sum()
nao_inf_esc = df.loc[df["Escolaridade"] == "Não informado", "Total_Eleitores"].sum()

with st.expander("Quais tratamentos foram feitos?"):
    st.markdown(f"""
- **Espaços extras** removidos das colunas de texto.
- **Total_Eleitores** convertido para número ({invalidos} valor(es) inválido(s) encontrado(s)).
- **Duplicadas removidas:** {duplicadas} linha(s).
- **Não usamos `dropna()`** nem apagamos a categoria "Não informado": ela representa
  {pct(nao_inf_esc / total * 100)} dos eleitores e continua aparecendo nos gráficos.
- **"Exterior"** são brasileiros que votam fora do país. Entra no total geral, mas fica
  fora dos rankings de estados, porque não é um estado.
""")

# ------------------------------------------------------------
# AULA 3 – INDICADORES
# ------------------------------------------------------------
st.subheader("2. Indicadores gerais")

estados = df[df["Estado"] != "Exterior"]
por_estado = (
    estados.groupby("Estado", as_index=False)["Total_Eleitores"].sum()
    .sort_values("Total_Eleitores", ascending=False)
)
maior = por_estado.iloc[0]
superior_total = df.loc[df["Escolaridade"] == "Superior completo", "Total_Eleitores"].sum()
exterior_total = df.loc[df["Estado"] == "Exterior", "Total_Eleitores"].sum()

i1, i2, i3 = st.columns(3)
i1.metric("Total de eleitores", formatar(total))
i2.metric("Estado com mais eleitores", maior["Estado"], formatar(maior["Total_Eleitores"]))
i3.metric("Eleitores com superior completo", pct(superior_total / total * 100))

# ------------------------------------------------------------
# PERGUNTA 1 – Quais estados concentram mais eleitores?
# ------------------------------------------------------------
st.subheader("3. Quais estados concentram mais eleitores?")

fig1 = px.bar(
    por_estado.sort_values("Total_Eleitores"),
    x="Total_Eleitores", y="Estado", orientation="h",
    text_auto=".3s",
    title="Total de eleitores por estado",
    labels={"Total_Eleitores": "Total de eleitores", "Estado": ""},
    height=700,
)
fig1.update_traces(textposition="outside", textfont_size=12)
fig1.update_layout(separators=",.")
st.plotly_chart(fig1)

top3 = por_estado.head(3)
menor = por_estado.iloc[-1]
st.markdown(f"""
### O que podemos observar?
**{maior['Estado']}** é o estado com mais eleitores: **{formatar(maior['Total_Eleitores'])}**,
o que representa **{pct(maior['Total_Eleitores'] / total * 100)}** de todo o eleitorado.
Somados, os três maiores ({', '.join(top3['Estado'])}) reúnem
**{pct(top3['Total_Eleitores'].sum() / total * 100)}** de todo o eleitorado.
O menor eleitorado é o de **{menor['Estado']}** ({formatar(menor['Total_Eleitores'])}).
Fora dos estados, o eleitorado no exterior soma {formatar(exterior_total)}.

Esse gráfico mostra **tamanho**, não perfil: estados maiores têm mais eleitores principalmente
porque têm mais habitantes. Para comparar estados de tamanhos diferentes, a próxima pergunta usa percentuais.
""")

# ------------------------------------------------------------
# PERGUNTA 2 – Proporção com ensino superior por estado
# ------------------------------------------------------------
st.subheader("4. Quais estados têm a maior proporção de eleitores com ensino superior completo?")

sup_estado = (
    estados.assign(Superior=estados["Total_Eleitores"].where(estados["Escolaridade"] == "Superior completo", 0))
    .groupby("Estado", as_index=False)[["Superior", "Total_Eleitores"]].sum()
)
sup_estado["Percentual"] = sup_estado["Superior"] / sup_estado["Total_Eleitores"] * 100
sup_estado = sup_estado.sort_values("Percentual")
media_brasil = superior_total / total * 100

fig2 = px.bar(
    sup_estado,
    x="Percentual", y="Estado", orientation="h",
    text_auto=".1f",
    title="% dos eleitores com ensino superior completo, por estado",
    labels={"Percentual": "% com superior completo", "Estado": ""},
    height=700,
)
fig2.add_vline(
    x=media_brasil, line_dash="dash", line_color="gray",
    annotation_text=f"Média geral: {pct(media_brasil)}", annotation_position="top",
)
fig2.update_traces(textposition="outside", textfont_size=12)
fig2.update_layout(separators=",.")
st.plotly_chart(fig2)

topo = sup_estado.iloc[-1]
base = sup_estado.iloc[0]
acima = int((sup_estado["Percentual"] > media_brasil).sum())
st.markdown(f"""
### O que podemos observar?
No eleitorado como um todo, **{pct(media_brasil)}** dos eleitores declararam ter ensino superior completo.
A maior proporção está em **{topo['Estado']}** ({pct(topo['Percentual'])}) e a menor em
**{base['Estado']}** ({pct(base['Percentual'])}) — uma diferença de
**{f"{topo['Percentual'] - base['Percentual']:.1f}".replace(".", ",")} pontos percentuais**.
{acima} das {len(sup_estado)} unidades da federação (26 estados + DF) ficam acima da média geral (linha tracejada).

Os dados mostram **onde** essa proporção é maior ou menor, mas não explicam **por quê**.
""")

# ------------------------------------------------------------
# PERGUNTA 3 – Escolaridade x faixa etária
# ------------------------------------------------------------
st.subheader("5. Como a escolaridade muda entre as faixas de idade?")

opcoes = ["Todos os eleitores"] + sorted(df["Estado"].unique())
escolha = st.selectbox("Escolha o recorte", opcoes)
recorte = df if escolha == "Todos os eleitores" else df[df["Estado"] == escolha]

tabela = recorte.groupby(["Faixa_Etaria", "Escolaridade"], as_index=False)["Total_Eleitores"].sum()
tabela["Percentual"] = (
    tabela["Total_Eleitores"] / tabela.groupby("Faixa_Etaria")["Total_Eleitores"].transform("sum") * 100
)
tabela = tabela[tabela["Faixa_Etaria"] != "Não informado"]  # grupo mínimo, só atrapalha a leitura

fig3 = px.bar(
    tabela,
    x="Faixa_Etaria", y="Percentual", color="Escolaridade",
    category_orders={"Faixa_Etaria": ORDEM_IDADE, "Escolaridade": ORDEM_ESCOLARIDADE},
    color_discrete_map=CORES,
    title=f"Escolaridade dentro de cada faixa etária (%) — {escolha}",
    labels={"Faixa_Etaria": "Faixa etária", "Percentual": "% dos eleitores da faixa"},
    hover_data={"Total_Eleitores": ":,", "Percentual": ":.1f"},
)
# Legenda na mesma ordem da pilha (de cima para baixo)
fig3.update_layout(legend_traceorder="reversed", separators=",.")
st.plotly_chart(fig3)


def parte(faixa, niveis):
    linha = tabela[(tabela["Faixa_Etaria"] == faixa) & (tabela["Escolaridade"].isin(niveis))]
    return linha["Percentual"].sum()


def mais_comum(faixa):
    linha = tabela[tabela["Faixa_Etaria"] == faixa]
    return linha.nlargest(1, "Percentual")["Escolaridade"].iloc[0] if len(linha) else "sem dados"


faixas = [f for f in ORDEM_IDADE if f in set(tabela["Faixa_Etaria"])]
sup_por_faixa = {f: parte(f, ["Superior completo"]) for f in faixas}
faixa_top_sup = max(sup_por_faixa, key=sup_por_faixa.get)
baixa = ["Analfabeto", "Lê e escreve"]

st.markdown(f"""
### O que podemos observar? — {escolha}
A faixa com maior proporção de **superior completo** é a de **{faixa_top_sup}**
({pct(sup_por_faixa[faixa_top_sup])}). Entre os eleitores de **18 a 24 anos**, essa proporção é
{pct(sup_por_faixa.get('18 a 24 anos', 0))}, e a escolaridade mais comum nessa faixa é
**{mais_comum('18 a 24 anos')}**. Entre quem tem **70 anos ou mais**, a mais comum é
**{mais_comum('70 anos ou mais')}**.

Os eleitores **analfabetos ou que só leem e escrevem** são {pct(parte('18 a 24 anos', baixa))}
na faixa de 18 a 24 anos e {pct(parte('70 anos ou mais', baixa))} entre quem tem 70 anos ou mais.

**Cuidados ao interpretar:**
- O gráfico compara **gerações diferentes** hoje; não mostra a mesma pessoa ao longo da vida.
- Quem tem 18 a 24 anos, em boa parte, ainda não teve tempo de concluir um curso superior,
  então compare essa faixa com cuidado.
- A escolaridade vem do **cadastro eleitoral** (informada pelo eleitor), não de uma pesquisa como o
  Censo do IBGE, e o arquivo não diz quando cada eleitor atualizou essa informação.
- Os dados mostram associação entre idade e escolaridade, **não uma causa**.
""")

# ------------------------------------------------------------
# AULA 5 – REGISTRO DO USO DA IA
# ------------------------------------------------------------
with st.expander("Como a IA ajudou no desenvolvimento"):
    st.markdown("""
**Problema encontrado:** a primeira base que usamos tinha números redondos, sem fonte, e cada
escolaridade aparecia sempre com a mesma faixa etária — não dava para analisar as duas separadamente.

**Sugestão da IA:** trocar por dados oficiais do TSE ("Eleitorado – Atual") e resumir o arquivo
original (milhões de linhas) somando os eleitores por estado, escolaridade e faixa etária.

**O que precisou ser corrigido:** o script sugerido falhou na primeira execução, porque o TSE usa
nomes de coluna diferentes dos esperados (`DS_GRAU_INSTRUCAO` e `QT_ELEITORES`). O erro foi
encontrado lendo o cabeçalho do arquivo e o script foi ajustado.

**Como verificamos:**
- o total do CSV (158.765.458 eleitores) bate com o número divulgado pelo TSE para 2026
  (mais de 158,7 milhões de eleitores aptos);
- `pd.crosstab(df["Escolaridade"], df["Faixa_Etaria"])` mostra que agora toda escolaridade aparece em
  toda faixa etária (só faltam algumas combinações com "Não informado", que é um grupo muito pequeno).
""")
