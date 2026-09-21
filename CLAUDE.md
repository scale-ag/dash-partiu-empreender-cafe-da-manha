# CLAUDE.md — Contexto do projeto (Rogerio · Café da Manhã)

> Este arquivo é lido automaticamente pelo Claude Code ao abrir o repositório.
> Ele carrega TODO o contexto necessário para continuar o trabalho sem depender
> de mensagens anteriores. Mantenha-o atualizado.
>
> Este repositório **já está configurado** para o cliente (nasceu do template
> High Ticket, mas foi convertido para um funil de venda direta). Todos os
> marcadores de template foram preenchidos.

---

## O que é

Dashboard de **tráfego pago** do funil **Perpétuo** (venda direta) do produto
*Café da Manhã Lucrativo* — um app de BI estático (HTML/CSS/JS puro + Chart.js
via CDN) publicado no **GitHub Pages**, que cruza o gerenciador de mídia paga
com a planilha de Compradores e se atualiza sozinho a cada ~30 min (build 100%
na nuvem via GitHub Actions, disparado externamente pelo cron-job.org).

- **Cliente/projeto:** Rogerio · **Subtítulo:** Café da Manhã · **Funil:** Perpétuo
- **URL pública:** https://scale-ag.github.io/dash-partiu-empreender-cafe-da-manha/
- **Repositório:** `scale-ag/dash-partiu-empreender-cafe-da-manha`
- **Somente leitura** das planilhas. Nunca escrever de volta.

### Diferença essencial para o template original
O template foi feito para captação de leads High Ticket (Conversas → MQL →
venda). **Aqui não existe lead nem MQL**: é venda direta. O funil é

```
Gasto → Impressões → Cliques no link → Visitas na LP → Checkouts iniciados → Vendas → Faturamento
```

com CPM, CTR, CPC, ConvLP, CPV, Tx‑CHK, CPCHK, Tx‑Venda, **CAC**, Ticket médio e
**ROAS**. Qualquer menção a MQL/lead/especialidade/telefone neste repositório é
resquício do template e está errada — corrija ao encontrar.

## Fontes de dados (Google Sheets, somente leitura)

São **duas planilhas diferentes** (o template pressupunha uma só). As abas são
lidas **por NOME** via endpoint `gviz`, não por `gid`: o Sheets não expõe os gids
publicamente e o nome da aba é estável e imune a reordenação.

| Fonte | Spreadsheet ID | Aba | Colunas usadas |
|---|---|---|---|
| **Meta Ads** (`Extração Dashboard - Cafe da Manha`) | `1KEmIpxN6fS-ovuLipmQTzGldKAIYAUznJStGeSSV7rM` | `Página 1` | `Day` · `Campaign Name` · `Ad Set Name` · `Ad Name` · `Impressions` · `Link Clicks` · `Landing Page Views` · `Amount Spent` · *(opcional)* `Initiate Checkout` · *(opcional)* permalink do criativo |
| **Compradores** (`Partiu Empreender \| 2026`) | `1Qe1_LFcrd98hhOTa5rJAL78ZRUoHCZ-Pj4kIRgdiljI` | `Cafe da Manha Lucrativo` | `Data` · `Nome` · `Email` · `Valor da Compra` · `Forma de Pagto` · `Utm_source` · `utm_campaign` · `utm_medium` · `utm_content` · `Utm_term` · `Origem de Checkout` |

URL de export CSV usada pelo build:
`https://docs.google.com/spreadsheets/d/<ID>/gviz/tq?tqx=out:csv&headers=1&sheet=<NOME DA ABA>`

Particularidades reais dessas planilhas:
- `Amount Spent` vem com **vírgula decimal** (`26,64`) — `to_float()` trata.
- `Data` dos Compradores vem **com hora** (`03/09/2026 01:22`) — `parse_date()`
  corta a hora antes do `strptime` (sem isso, a venda perdia a data).
- `utm_content` às vezes vem **URL-encoded** (`Capta%C3%A7%C3%A3o_CML`) —
  `urldec()` decodifica e `squash()` casa com o nome canônico do Meta, senão o
  mesmo anúncio viraria duas linhas.
- A aba de Compradores tem 16 colunas vazias à direita — inofensivas.

### Regra de VENDA (decisão do cliente)
Só conta como venda a linha com **UTM completa** (`utm_campaign` + `utm_medium` +
`utm_content`). Linha sem UTM é normalmente **Pix gerado e não pago** — é
descartada de TODOS os números, e o build loga quantas e de que valor caíram
fora (`process_sales`). Não existe bucket "(sem campanha)" nesta dash.

### Atribuição
**Por UTM, não por telefone** (a aba de Compradores não tem telefone).
`utm_campaign`/`utm_medium`/`utm_content` são exatamente o
`Campaign Name`/`Ad Set Name`/`Ad Name` do Meta Ads. O build indexa os nomes
canônicos do Meta e casa por chave normalizada (sem acento, minúsculo, espaços
colapsados). Venda cuja campanha não existe na aba de mídia entra nos totais e é
logada como ATENÇÃO no build.

### Checkouts iniciados
A quantidade vem da coluna **Initiate Checkout** (Adveronix) na aba de mídia.
O **custo por checkout é calculado na dash** (gasto ÷ checkouts) — não precisa
exportar coluna de custo. O build detecta a coluna sozinho (`B.has_checkout`):
existindo, a etapa e as colunas Tx‑CHK/CPCHK entram no funil, nas tabelas diárias,
nas hierárquicas e no ranking de anúncios; faltando, aparecem como "-" e o funil
marca a etapa como "sem dado". Aliases aceitos em `build.py` cobrem variações do
cabeçalho (`Initiate Checkout`, `Checkouts iniciados`, `Adds to Cart`…).

### Imposto da mídia paga
`TAX_FACTOR = 1.13806` (13,806%) em `build.py`, aplicado **somente** ao gasto de
Meta Ads. O toggle "Imposto Meta" fica **ativo por padrão** (`STATE.tax=true`) e
aplica o fator em todo o gasto e derivados (CPM, CPC, CPV, CPCHK, CAC, ROAS) via
`taxf()`, que só multiplica `a.sp`.

### Convenções de campanha (Sigla do Funil)
Padrão: `CML | E6-VEN | P3-FRIO | CONV | CBO | VA | 2026-09-02 | Teste de Criativos 1`

- **`CML` = sigla do funil** (Café da Manhã Lucrativo) — `MAIN_PRODUCT_PREFIX`.
  Aparece nas 6 campanhas e no sufixo de todos os anúncios (`_CML`). É a única.
- `E6-VEN` etapa de venda · `P3-FRIO` público frio · `CONV` objetivo conversão ·
  `CBO`/`ABO` estrutura de verba · `VA` variação · depois data e nome do teste.

### Privacidade
A página é **pública** (repo público + GitHub Pages). Nome vira `Fulano S.`
(`first_last_initial`) e e‑mail vira `fu****@dominio.com` (`mask_email`) antes de
entrar no HTML. Nunca publicar PII crua.

## Arquitetura / arquivos

```
build/build.py            # lê os 2 CSVs (read-only), emite REGISTROS BRUTOS (meta[]/sales[]/ad_links); render() costura os 4 arquivos abaixo
build/template.html       # esqueleto HTML. Placeholders __STYLES__, __APP_JS__, __DATA_JSON__, __BUILD_ID__, __GENERATED_BRT__
build/identidade-visual.css  # TODAS as cores (tema claro=padrão / escuro). Mexa AQUI p/ trocar só cor
build/estilos.css         # layout/componentes (sidebar, topbar, period-picker, funil, tabelas, gráficos, aba Relatório)
build/app.js              # lógica + renderização (KPIs, funil, tabelas, filtro cruzado, period-picker, heatmap, Relatório)
build/relatorios.json     # Insights de Tráfego por período (aba Relatório) — VERSIONADO; lido no build, sem API. Vazio ({}) até existir Routine.
build/relatorios_dados.json      # números brutos por período (insumo p/ a Routine escrever relatorios.json) — não lido pelo site
build/relatorio_lib.py           # datas/agregação compartilhadas (mesmo funil de venda direta)
build/coletar_dados_relatorio.py # gera relatorios_dados.json (só números, sem texto) — roda no briefing.yml, 1x/dia
build/GUIA-RELATORIOS.md            # formato/estrutura dos Insights da aba Relatório (os 7 blocos)
build/GUIA-INTERPRETACAO-METRICAS.md # regras de diagnóstico por métrica — leitura obrigatória p/ redigir
.github/workflows/deploy.yml    # roda build.py e publica no Pages (workflow_dispatch + schedule + push)
.github/workflows/briefing.yml  # roda coletar_dados_relatorio.py e commita relatorios_dados.json na main (cron 1x/dia)
dist/index.html           # saída gerada (gitignored; o Actions reconstrói)
GUIA-REPLICACAO.md        # como replicar este modelo para outros relatórios/clientes
SETUP-CRON.md             # valores exatos do cron-job.org
```

> **Nota:** `build/gerar_relatorios.py` (gerador determinístico de texto, fallback
> manual) foi **removido** na conversão para venda direta — ele era todo escrito
> no vocabulário de MQL do template e quebraria no schema novo. O pipeline diário
> de números (`coletar_dados_relatorio.py`) continua funcionando.

### Modelo de dados no navegador
`DATA.meta[]` = 1 linha por dia × campanha × conjunto × anúncio
(`{d, camp, adset, ad, sp, im, cl, pv, ck}`).
`DATA.sales[]` = 1 linha por COMPRA
(`{d, src, camp, adset, ad, plat, pay, vendas, fat, nm, em}`), na **data real da
compra**. Um "agregado" em `app.js` é sempre `{sp,im,cl,pv,chk,vendas,fat}`, venha
de campanha, anúncio, dia ou total — `derive()` calcula as métricas de mídia e
`salesOf()` as de venda (CAC, ROAS, ticket, taxas).

### Páginas
1. **Visão Geral de Vendas** — funil vertical + KPIs secundários; gráfico combinado
   diário (barras Visitas/Checkouts, linha verde de Vendas em eixo próprio, linhas
   de Gasto e CAC em R$) + tabela diária com heatmap; distribuição das vendas por
   campanha / posicionamento (`Utm_term`) / forma de pagamento / anúncio.
2. **Mídia Paga (Meta Ads)** — mesmo funil respeitando o filtro cruzado; vendas por
   anúncio; donut de conversão da LP; compilado de anúncios; 3 tabelas hierárquicas
   Campanha → Conjunto → Anúncio, cada uma com gráfico de **custo por visita por
   dia** (métrica densa; o CAC do período aparece na legenda) ; lista de Compradores.
3. **Relatório** — espelha a Visão Geral + painel de Metas editável + ranking de
   anúncios + Insights de Tráfego. Ver `build/GUIA-RELATORIOS.md`.

**Ordem das colunas nas tabelas diárias:** `Data · Dia · Gasto · CPM · CTR ·
Cliques · CPC · Visitas · ConvLP · CPV · [Checkouts · Tx‑CHK · CPCHK] · Vendas ·
Tx‑Venda · CAC · Ticket · Fat. · ROAS`.

**Regras obrigatórias das tabelas** (ver `GUIA-REPLICACAO.md`): cabeçalho sticky;
ordenação tri‑state; colunas redimensionáveis (persist localStorage); linha
"Total Geral" fixa; dimensão nunca truncada; seleção com toggle + Ctrl multi;
filtro cruzado bidirecional; tabela diária com último dia no topo; heatmap de cor
fixa por métrica: **Gasto=vermelho · Visitas=azul · Checkouts=ciano ·
Vendas=verde · ROAS=amarelo** (`--heat-gasto/vis/chk/vendas/roas`).

### Painel de Metas (aba Relatório)
Meta CAC · Meta ROAS · Volume mín. amostral (vendas) · Gasto mín. amostral (R$) ·
N dias p/ corte. Persiste em `localStorage['dm_metas']`, default de `build.py`
(`META_CAC`/`META_ROAS` = None → "não definida"; `SAMPLE_MIN_SPEND=347` ≈ 1 ticket;
`SAMPLE_MIN_SALES=1`). Editar recolore **CAC** (menor é melhor) e **ROAS** (maior é
melhor) nas tabelas de anúncio e reavalia o badge Em observação/Avaliável ao vivo.

### Briefing automático (Routine do Claude) — opcional, não configurado
`build/relatorios.json` pode ser escrito 1×/dia por uma **Routine do Claude**, em
2 etapas (o ambiente da Routine não alcança `docs.google.com`):
1. `coletar_dados_relatorio.py` (Actions, `briefing.yml`, 1×/dia) agrega **só
   números** em `relatorios_dados.json` e commita na `main`.
2. A Routine lê esse JSON + os 2 guias, redige `relatorios.json` e commita na
   `main`, disparando o `deploy.yml`. **Precisa ser criada por cliente**
   (`create_trigger`) — ainda **não existe** para este repo, então a aba mostra o
   estado vazio ("Insights ainda não gerados").

## Rodar/testar local

```bash
python build/build.py --meta-file meta.csv --sales-file sales.csv --out dist/index.html
# (o sandbox do agente NÃO alcança docs.google.com; use CSVs locais para testar.
#  O runner do GitHub Actions tem internet e busca os CSVs ao vivo.)
```

Para conferir o front sem internet: o `index.html` gerado carrega o Chart.js da
CDN; num sandbox sem rede, substitua a tag por um stub de `Chart` e renderize com
o Chromium headless (`--dump-dom`) para caçar erro de JS.

## Lacunas de dados conhecidas
- **Checkouts iniciados** dependem da coluna do Adveronix; sem ela, a etapa e as
  colunas Tx‑CHK/CPCHK aparecem "-".
- **Link do criativo**: a aba de mídia não tem permalink hoje, então a coluna
  "Link" do ranking de anúncios fica oculta (`HAS_LINKS`). Adicionando a coluna na
  planilha, ela volta sozinha.
- **Frequência / alcance** não são exportados pelo Adveronix hoje.

## Publicação — problemas conhecidos
1. **Push:** se a integração GitHub da sessão for somente‑leitura (403), o caminho
   é `git push` direto para `github.com` com o **PAT do usuário**. Nunca gravar o
   token no `.git/config` (usar URL efêmera `https://x-access-token:<TOKEN>@github.com/...`).
2. **cron-job.org só funciona na `main`:** `workflow_dispatch` só existe na branch
   padrão.
3. **Pages liga sozinho:** `actions/configure-pages@v6` com `enablement: true`
   (precisa `permissions: pages: write, id-token: write`).
4. **Proxy do sandbox:** o ambiente do agente NÃO alcança `docs.google.com`,
   `cdn.jsdelivr.net`, `*.github.io` nem parte da API REST de Actions/Pages (o
   proxy devolve 403 em `PUT /actions/permissions/*` e em `/pages`) — mas o runner
   do Actions alcança tudo. Para ler dados das planilhas de dentro do sandbox, rode
   um workflow descartável no Actions e leia o log.
5. **Token exposto:** se um token foi colado no chat, **revogar e gerar um novo**.

## Branch / git
- Desenvolvimento na branch designada da sessão; manter sincronizada com `main`.
