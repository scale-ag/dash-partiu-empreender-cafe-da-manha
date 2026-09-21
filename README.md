# Dashboard de Tráfego Pago · Rogerio — Café da Manhã

Dashboard **100% na nuvem** do funil **Perpétuo** (venda direta) do *Café da Manhã
Lucrativo*: cruza o gerenciador de mídia paga (Meta Ads) com a planilha de
Compradores e se atualiza sozinho a cada ~30 min. HTML/CSS/JS puro + Chart.js
via CDN, build no GitHub Actions, publicação no GitHub Pages.

**URL pública:** https://scale-ag.github.io/dash-partiu-empreender-cafe-da-manha/

## Funil

```
Gasto → Impressões → Cliques no link → Visitas na LP → Checkouts iniciados → Vendas → Faturamento
```

Não existe etapa de lead/MQL: é venda direta. Métricas derivadas: CPM, CTR, CPC,
ConvLP, CPV, Tx‑CHK, CPCHK, Tx‑Venda, **CAC**, Ticket médio e **ROAS**.

A etapa **Checkouts iniciados** depende da coluna de *Initiate Checkout* na
planilha de mídia (Adveronix). O build detecta a coluna sozinho: se ela existir,
a etapa e as colunas Tx‑CHK/CPCHK entram no funil e nas tabelas; se não, aparecem
como “-”. O **custo por checkout é calculado na dash** (gasto ÷ checkouts) — não
precisa exportar coluna de custo.

## Fontes (somente leitura — nunca escrevemos nas planilhas)

| Planilha | Aba | Colunas usadas |
|---|---|---|
| [Extração Dashboard - Cafe da Manha](https://docs.google.com/spreadsheets/d/1KEmIpxN6fS-ovuLipmQTzGldKAIYAUznJStGeSSV7rM/edit) | **Página 1** | `Day` · `Campaign Name` · `Ad Set Name` · `Ad Name` · `Impressions` · `Link Clicks` · `Landing Page Views` · `Amount Spent` (+ `Initiate Checkout`, opcional) |
| [Partiu Empreender \| 2026](https://docs.google.com/spreadsheets/d/1Qe1_LFcrd98hhOTa5rJAL78ZRUoHCZ-Pj4kIRgdiljI/edit) | **Cafe da Manha Lucrativo** | `Data` · `Nome` · `Email` · `Valor da Compra` · `Forma de Pagto` · `Utm_source` · `utm_campaign` · `utm_medium` · `utm_content` · `Utm_term` |

As abas são lidas **por nome** (endpoint `gviz`), não por `gid` — o Sheets não
expõe os gids publicamente e o nome da aba é estável.

## Regras de negócio

- **Atribuição por UTM, não por telefone.** `utm_campaign`/`utm_medium`/`utm_content`
  do checkout são exatamente o `Campaign Name`/`Ad Set Name`/`Ad Name` do Meta Ads.
  O build faz URL‑decode (o checkout às vezes grava `Capta%C3%A7%C3%A3o`) e casa
  com o nome canônico do Meta, então o mesmo anúncio nunca vira duas linhas.
- **Só conta venda com UTM completa** (campanha + conjunto + anúncio). Linha sem
  UTM normalmente é Pix gerado e não pago — é descartada, e o build loga quantas
  e de que valor caíram fora.
- **Imposto da mídia:** `TAX_FACTOR = 1.13806` (13,806%) aplicado só ao gasto do
  Meta Ads. O toggle “Imposto Meta” vem **ligado** e recalcula CPM/CPC/CPV/CAC/ROAS.
- **PII mascarada:** a página é pública, então nome vira `Fulano S.` e e‑mail vira
  `fu****@dominio.com`. A lista completa fica só na planilha.

## Sigla do funil

Todas as campanhas seguem `CML | E6-VEN | P3-FRIO | CONV | CBO | VA | <data> | <teste>`:

- `CML` — **sigla do funil** (Café da Manhã Lucrativo), também no sufixo dos anúncios (`_CML`)
- `E6-VEN` etapa de venda · `P3-FRIO` público frio · `CONV` objetivo conversão
- `CBO`/`ABO` estrutura de verba · `VA` variação

## Páginas

1. **Visão Geral de Vendas** — funil + KPIs + evolução diária + tabela diária com
   heatmap + distribuição das vendas (campanha, posicionamento, forma de pagamento, anúncio).
2. **Mídia Paga (Meta Ads)** — mesmo funil com filtro cruzado; vendas por anúncio;
   conversão da LP; compilado de anúncios; hierarquia Campanha → Conjunto → Anúncio
   com gráfico de custo por visita por dia; lista de Compradores.
3. **Relatório** — espelha a Visão Geral + painel de metas editável (Meta CAC, Meta
   ROAS, volume e gasto mínimos amostrais, N dias p/ corte) + ranking de anúncios
   com status Avaliável/Em observação + Insights de Tráfego.

## Automação

- `.github/workflows/deploy.yml` — roda `build/build.py` e publica no Pages
  (`workflow_dispatch` + `schedule` a cada 30 min + `push` em `build/**`).
- `.github/workflows/briefing.yml` — roda `build/coletar_dados_relatorio.py` 1×/dia
  e commita `build/relatorios_dados.json` (números brutos para os Insights).
- Disparo pontual a cada 30 min pelo **cron-job.org** — valores exatos em `SETUP-CRON.md`.

## Rodar local

```bash
python build/build.py --meta-file meta.csv --sales-file sales.csv --out dist/index.html
```

O sandbox do agente não alcança `docs.google.com`; use CSVs baixados. O runner do
GitHub Actions tem internet e busca as planilhas ao vivo.
