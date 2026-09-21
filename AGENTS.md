# AGENTS.md — instruções para agentes neste repositório

> Contexto completo do projeto: **`CLAUDE.md`** (leia primeiro).
> Este arquivo é o resumo operacional do que pode e do que não pode ser mexido.

## O que é

Dashboard estático (HTML/CSS/JS puro + Chart.js via CDN) do funil **Perpétuo** de
venda direta do *Café da Manhã Lucrativo* (cliente Rogerio), publicado no GitHub
Pages e reconstruído a cada ~30 min pelo GitHub Actions.

Funil: `Gasto → Impressões → Cliques → Visitas na LP → Checkouts → Vendas → Faturamento`.
**Não existe lead/MQL neste funil** — qualquer texto ou métrica de MQL é resquício
do template original e está errado aqui.

## Regras invioláveis

1. **Somente leitura das planilhas.** Nunca escrever de volta no Google Sheets.
2. **Só conta venda com UTM completa** (campanha + conjunto + anúncio). Linha sem
   UTM é Pix gerado e não pago — descartada, com log no build.
3. **PII sempre mascarada** no HTML publicado (página pública): nome `Fulano S.`,
   e‑mail `fu****@dominio.com`.
4. **`build.py` não agrega.** Ele emite registros brutos (`meta[]`/`sales[]`) e
   TODA a lógica (filtros de data, filtro cruzado, KPIs, tabelas, gráficos,
   heatmap, imposto) roda no navegador, em `app.js`.
5. **Nunca comitar token** no repositório (nem em `.git/config`). O token do
   cron-job.org vive só lá.
6. Se a planilha mudar de cabeçalho, o build **falha alto** (`require()` em
   `build.py`) em vez de publicar uma dash zerada. Mantenha esse comportamento.

## Onde mexer

| Quero mudar… | Arquivo |
|---|---|
| Fonte de dados, colunas, regra de venda, metas padrão | `build/build.py` (constantes no topo) |
| Cores (claro/escuro), heatmap, cores de série | `build/identidade-visual.css` |
| Layout/componentes | `build/estilos.css` |
| KPIs, funil, tabelas, gráficos, filtro cruzado | `build/app.js` |
| Esqueleto HTML, títulos, rótulos das páginas | `build/template.html` |
| Números dos Insights | `build/coletar_dados_relatorio.py` + `build/relatorio_lib.py` |
| Regras de redação dos Insights | `build/GUIA-RELATORIOS.md` + `build/GUIA-INTERPRETACAO-METRICAS.md` |

`render()` em `build.py` costura `template.html` + `identidade-visual.css` +
`estilos.css` + `app.js` nos placeholders `__STYLES__`/`__APP_JS__`/`__DATA_JSON__`.

## Testar antes de publicar

```bash
python build/build.py --meta-file meta.csv --sales-file sales.csv --out dist/index.html
```

O sandbox do agente normalmente **não alcança** `docs.google.com` nem `*.github.io`
— teste com CSVs locais. O runner do Actions alcança tudo.
