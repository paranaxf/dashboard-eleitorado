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

## Estrutura

```
app.py                       # o dashboard
requirements.txt             # bibliotecas para o Streamlit Cloud
dados/eleitorado_tse.csv     # base resumida (gerada a partir do TSE)
dados/fonte.txt              # data de geração e total de eleitores
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
