# Perfil do Eleitorado Brasileiro — Dashboard

Minidashboard em **Streamlit + Pandas + Plotly** feito para a atividade
*Dashboard de Dados com apoio de IA* (Fórum Movimenta Senac – 2º ano de Ciência de Dados).

## Perguntas

1. Quais estados concentram mais eleitores?
2. Quais estados têm a maior proporção de eleitores com ensino superior completo?
3. Como a escolaridade dos eleitores muda entre as faixas de idade?

## Fonte dos dados

**TSE – Portal de Dados Abertos**, conjunto [Eleitorado – Atual](https://dadosabertos.tse.jus.br/dataset/eleitorado-atual).
Arquivo original: `perfil_eleitorado_ATUAL.zip`.

O arquivo original tem milhões de linhas (município, zona, gênero, estado civil, idade, escolaridade).
O script `scripts/preparar_dados.py` soma os eleitores por **estado + escolaridade + faixa etária**
e gera `dados/eleitorado_tse.csv`. A data de geração informada pelo TSE fica em `dados/fonte.txt`.

O workflow `.github/workflows/dados_tse.yml` baixa o arquivo do TSE e roda o script automaticamente
(aba **Actions → Atualizar dados do TSE → Run workflow** para atualizar).

**Conferência:** o CSV gerado soma **158.765.458 eleitores** (dados gerados pelo TSE em 01/10/2026),
o que bate com os mais de 158,7 milhões de eleitores aptos divulgados pelo TSE para as eleições de 2026.

## Principais resultados

1. **SP** tem o maior eleitorado (34,1 milhões, 21,5% do total); SP, MG e RJ juntos somam 39,9%.
2. **DF** tem a maior proporção de eleitores com superior completo (23,3%) e **MA** a menor (6,1%);
   a média geral é 11,4%.
3. A faixa de **35 a 44 anos** tem a maior proporção de superior completo (17,3%); analfabetos ou
   eleitores que só leem e escrevem são 0,6% entre 18 e 24 anos e 33,4% entre quem tem 70 anos ou mais.

Os números acima são da versão atual da base; o próprio app recalcula tudo a partir do CSV.

## Estrutura

```
app.py                       # o dashboard
requirements.txt             # bibliotecas para o Streamlit Cloud
dados/eleitorado_tse.csv     # base resumida (gerada a partir do TSE)
dados/fonte.txt              # data de geração e total de eleitores
dados/log_geracao.txt        # log da última geração (para conferir sem abrir o Actions)
scripts/preparar_dados.py    # transforma o zip do TSE no CSV resumido
```

## Como rodar

```bash
pip install -r requirements.txt
streamlit run app.py
```

O app aceita o CSV por upload. Se nenhum arquivo for enviado, usa `dados/eleitorado_tse.csv`.

## Tratamentos feitos

- remoção de espaços extras nos textos;
- conversão de `Total_Eleitores` para número;
- remoção de linhas duplicadas;
- **sem** `dropna()`: a categoria "Não informado" é mantida e aparece nos gráficos;
- "Exterior" (eleitores que votam fora do Brasil) entra no total, mas fica fora dos rankings de estados.
