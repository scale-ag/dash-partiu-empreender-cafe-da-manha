# GUIA — Interpretação de Métricas de Funil de Venda Direta

> Referência **durável** para quem redige os Insights de Tráfego (a Routine do
> Claude, ou qualquer pessoa preenchendo `build/relatorios.json` manualmente).
> Como cada execução automática é uma sessão nova, sem memória da conversa que
> originou este guia, **este arquivo precisa ser lido por inteiro antes de
> redigir** — é aqui que moram as regras de diagnóstico, não só no
> `GUIA-RELATORIOS.md` (que define o formato/estrutura do texto).

Este cliente opera um **perpétuo de venda direta** (Café da Manhã Lucrativo):
anúncio → landing page → checkout → compra. **Não existe lead, MQL, agendamento
nem reunião** — se encontrar esse vocabulário em algum texto do repositório, é
resquício do template original e não deve ser reproduzido.

```
Impressões → Cliques → Visitas na LP → Checkouts iniciados → Vendas → Faturamento
```

A forma mais útil de interpretar esse funil é tratar cada métrica como um
**diagnóstico probabilístico**, não uma regra absoluta. Uma métrica ruim
raramente significa, sozinha, que aquele é o problema: ela precisa ser analisada
junto com as métricas anteriores e posteriores do funil.

## CTR (Click Through Rate)

**O que mede:** percentual de quem viu o anúncio e clicou. **Fórmula:** Cliques
÷ Impressões. **Funil:** Impressões → Cliques. **Objetivo:** capacidade do
criativo de gerar interesse suficiente para levar à página.

**Possíveis gargalos:** criativo fraco ou saturado; promessa genérica; público
errado ou muito amplo; fadiga de frequência; copy sem ângulo claro; formato
inadequado ao posicionamento.

**Ações recomendadas:** novos ângulos de criativo; testar variações de gancho
nos 3 primeiros segundos; revisar público; renovar criativos em fadiga;
adequar formato ao posicionamento (Feed x Stories).

**Quando NÃO é necessariamente um problema:** CTR baixo com CPV, Tx‑CHK e CAC
saudáveis costuma indicar comunicação qualificadora — clica menos gente, mas
quem clica compra. Nunca trate CTR como objetivo em si.

**Deve ser analisado junto com:** CPM, CPC, ConvLP, CPV, CAC.

## CPM (Custo por Mil Impressões)

**O que mede:** preço de entregar mil impressões. **Objetivo:** ler o custo do
leilão e a percepção de qualidade do criativo pelo Meta.

**Possíveis gargalos:** leilão mais caro (sazonalidade, concorrência); público
estreito demais; criativo com baixo engajamento; qualidade baixa atribuída pela
plataforma; muitas campanhas concorrendo pelo mesmo público (sobreposição).

**Quando NÃO é necessariamente um problema:** CPM subindo em TODAS as campanhas
ao mesmo tempo é leilão, não criativo — se CAC e ROAS seguem saudáveis, não
mexer. CPM alto com CTR alto e CAC dentro da meta é apenas tráfego mais caro e
mais qualificado.

**Deve ser analisado junto com:** CTR, CPC, CPV, CAC.

## CPC (Custo por Clique)

**O que mede:** quanto custa cada clique no link. **Fórmula:** Investimento ÷
Cliques. **Objetivo:** eficiência de compra de tráfego, já combinando CPM e CTR.

**Possíveis gargalos:** CPM alto, CTR baixo ou os dois; público saturado;
criativo em fadiga; posicionamento caro.

**Quando NÃO é necessariamente um problema:** CPC alto com ConvLP e Tx‑CHK altas
pode sair mais barato no fim (menos cliques, mais compras). Julgue sempre com o
CPV e o CAC ao lado.

**Deve ser analisado junto com:** CPM, CTR, CPV, CAC.

## ConvLP (Clique → Visita na LP)

**O que mede:** quanto dos cliques vira visita registrada na página.
**Fórmula:** Visitas na LP ÷ Cliques. **Objetivo:** saúde **técnica** do caminho
entre o anúncio e a página.

**Possíveis gargalos:** página lenta; redirect quebrado; link errado no
anúncio; erro de rastreamento (pixel/CAPI); experiência mobile ruim; usuário
desiste antes do carregamento.

**Ações recomendadas:** medir velocidade da página no mobile; conferir o link
do anúncio e os parâmetros de UTM; validar o evento de PageView; reduzir peso
da página.

**Quando NÃO é necessariamente um problema:** uma diferença permanente entre
cliques e visitas é normal (cliques acidentais, desistência no carregamento).
O alerta é a **queda súbita**, principalmente em várias campanhas ao mesmo dia
— isso é quase sempre técnico, não criativo.

**Deve ser analisado junto com:** CPC, CPV, Tx‑CHK.

## CPV (Custo por Visita na LP)

**O que mede:** quanto custa colocar uma pessoa na página de vendas.
**Fórmula:** Investimento ÷ Visitas na LP. **Objetivo:** é o melhor indicador
**diário** de eficiência de mídia num funil de venda direta — tem volume todos
os dias, ao contrário do CAC, que depende de venda.

**Possíveis gargalos:** CPM alto; CTR baixo; ConvLP ruim (problema técnico);
público saturado.

**Quando NÃO é necessariamente um problema:** CPV baixo **não** é vitória se a
Tx‑CHK é baixa — significa tráfego barato e sem intenção de compra. CPV alto com
Tx‑CHK e CAC saudáveis é tráfego caro e qualificado; não escale nem corte pelo
CPV isolado.

**Deve ser analisado junto com:** CTR, ConvLP, Tx‑CHK, CAC.

## Tx‑CHK (Visita → Checkout iniciado)

**O que mede:** quanto das visitas vira intenção de compra. **Fórmula:**
Checkouts iniciados ÷ Visitas na LP. **Objetivo:** avaliar se a página, a oferta
e o preço convencem.

**Possíveis gargalos:** promessa pouco clara; página desalinhada com o anúncio;
preço/ancoragem mal construídos; falta de prova social; CTA fraco; página lenta
no mobile; oferta pouco atrativa para o público que está chegando.

**Ações recomendadas:** melhorar headline e promessa; alinhar criativo e página;
reforçar prova social e garantia; revisar ancoragem de preço; melhorar o CTA e
a versão mobile; testar variações de página (o cliente já roda campanhas de
"Teste de Páginas" — compare-as diretamente).

**Quando NÃO é necessariamente um problema:** Tx‑CHK baixa com CAC dentro da
meta indica página qualificadora. E quando a planilha de mídia não traz a coluna
de Initiate Checkout (`has_checkout=false`), esta métrica simplesmente **não
existe no período** — diga que o dado falta, nunca escreva 0%.

**Deve ser analisado junto com:** CPV, CPCHK, Tx‑Venda, CAC.

## CPCHK (Custo por Checkout Iniciado)

**O que mede:** quanto custa cada intenção de compra. **Fórmula:** Investimento
÷ Checkouts iniciados. **Objetivo:** ponte entre o custo de mídia e o CAC —
sobe antes do CAC quando a página perde eficiência.

**Possíveis gargalos:** CPV alto; Tx‑CHK caindo; público novo com menos
intenção; oferta perdendo apelo.

**Quando NÃO é necessariamente um problema:** CPCHK alto com Tx‑Venda alta pode
resultar num CAC saudável. Também é calculado na dash (gasto ÷ checkouts) — não
depende de coluna de custo na planilha.

**Deve ser analisado junto com:** CPV, Tx‑CHK, Tx‑Venda, CAC.

## Tx‑Venda (Checkout iniciado → Compra)

**O que mede:** quanto dos checkouts iniciados vira compra paga. **Fórmula:**
Vendas ÷ Checkouts iniciados. **Objetivo:** medir a fricção do checkout — é a
última etapa antes do dinheiro entrar.

**Possíveis gargalos:** Pix gerado e não pago; recusa de cartão; parcelamento
insuficiente; poucos meios de pagamento; checkout lento ou confuso; frete/taxas
surpresa; falta de confiança (selo, garantia, suporte); preço acima do esperado
depois da página.

**Ações recomendadas:** revisar meios de pagamento e parcelamento; recuperação
de checkout abandonado; reduzir campos do checkout; reforçar garantia/segurança
no próprio checkout; comparar taxa por forma de pagamento (a dash quebra vendas
por `Forma de Pagto`).

**Quando NÃO é necessariamente um problema:** Pix gerado e não pago é comum —
nesta dash, essas linhas **não contam como venda** (regra do cliente: só entra
compra com UTM completa). Não as reporte como venda perdida nem as some ao
faturamento.

**Deve ser analisado junto com:** Tx‑CHK, CAC, Ticket Médio, forma de pagamento.

## CAC (Custo de Aquisição)

**O que mede:** quanto custa adquirir um novo cliente. **Fórmula:**
Investimento ÷ Vendas. **Objetivo:** eficiência financeira de toda a
operação de aquisição.

**Possíveis gargalos:** CAC alto normalmente é *consequência* de problemas
anteriores — CPM/CPC alto, ConvLP quebrada, CPV alto, Tx‑CHK baixa, CPCHK alto,
Tx‑Venda baixa (fricção de pagamento), público saturado ou escala excessiva.

**Ações recomendadas:** nunca atacar o CAC diretamente — identificar em qual
etapa do funil está a maior perda (Impressão→Clique, Clique→Visita,
Visita→Checkout, Checkout→Venda) e corrigir a etapa responsável.

**Quando NÃO é necessariamente um problema:** CAC alto pode ser saudável
quando o ticket médio aumentou, a margem permanece positiva, há upsell/recorrência
depois da compra, o ROAS segue saudável, ou a operação está em expansão (natural
que o CAC suba ao buscar públicos mais amplos). **Atenção à amostra:** com
ticket de ~R$ 300 e poucas vendas no período, uma venda a mais ou a menos muda
o CAC em dezenas de reais — cite a amostra antes de concluir.

**Deve ser analisado junto com:** ROAS, Ticket Médio, Tx‑Venda, Margem.

## ROAS

**O que mede:** retorno sobre o investimento em mídia. **Fórmula:** Receita
÷ Investimento. **Objetivo:** retorno financeiro gerado pelas campanhas.

**Possíveis gargalos:** ROAS baixo normalmente é consequência de CAC alto,
ticket médio baixo, Tx‑CHK ou Tx‑Venda baixas, vendas não registradas na
planilha, UTM faltando no checkout, ou escala excessiva.

**Ações recomendadas:** encontrar qual etapa anterior reduziu a eficiência —
nunca otimizar diretamente para ROAS sem entender o resto do funil. Também
verificar: todas as vendas foram registradas na planilha? o checkout gravou os
UTMs? os pagamentos foram aprovados (Pix gerado e não pago não é venda)?

**Quando NÃO é necessariamente um problema:** ROAS baixo pode ser temporário
quando a campanha começou há pouco, quando o dia ainda está em curso (a compra
costuma cair horas depois do clique, então o dia mais recente quase sempre
subestima vendas), ou quando o objetivo declarado é ganhar escala. Num perpétuo
de venda direta o ciclo é curto — se o ROAS segue abaixo de 1 por vários dias
com amostra suficiente, é deterioração real, não maturação.

**Deve ser analisado junto com:** CAC, Ticket Médio, Tx‑Venda, Margem.

## Ticket Médio

**O que mede:** receita média por venda. **Fórmula:** Receita ÷ Vendas.
**Objetivo:** quanto cada novo cliente gera de receita na aquisição.

**Possíveis gargalos:** descontos e cupons excessivos; ausência de order bump/
upsell no checkout; mix de ofertas com valores diferentes; promoção pontual
puxando o ticket para baixo.

**Ações recomendadas:** testar order bump e upsell no checkout; revisar cupons;
melhorar empilhamento de valor e ancoragem de preço; acompanhar ticket por
campanha/anúncio (a dash traz Ticket por linha nas tabelas).

**Quando NÃO é necessariamente um problema:** ticket baixo pode ser proposital
quando a oferta de entrada facilita a aquisição, há upsell posterior, a Tx‑Venda
aumenta ou o CAC cai na mesma proporção. Variação de ticket entre períodos com
poucas vendas é ruído de amostra, não tendência.

**Deve ser analisado junto com:** CAC, ROAS, Tx‑Venda, Margem.

## Visão geral do funil de venda direta

Ordem de leitura: Impressões → Cliques → Visitas na LP → Checkouts → Vendas.

Cada métrica é um diagnóstico probabilístico — uma métrica ruim não significa
automaticamente que aquela etapa é o verdadeiro problema. Exemplos: CPV baixo +
Tx‑CHK baixa → tráfego barato e sem intenção; CPCHK alto + Tx‑Venda alta → pode
seguir saudável; ConvLP despencando no mesmo dia em todas as campanhas → quase
sempre problema técnico da página/rastreamento; muitos checkouts e poucas vendas
→ fricção de pagamento, não de tráfego; CAC alto → pode ser sustentável se
ticket e margem permitirem; ROAS do dia corrente abaixo do período → maturação
da compra, não deterioração.

A análise deve localizar a **primeira quebra relevante do funil** e verificar
como ela afeta todas as etapas posteriores.

## Heurísticas obrigatórias de interpretação

- Nunca concluir que uma métrica isolada representa o gargalo do funil — sempre
  interpretar junto com a etapa anterior e a posterior.
- ConvLP caindo em várias campanhas ao mesmo tempo → investigar **primeiro**
  problema técnico/de mensuração (LP fora do ar, redirect, pixel, UTM) antes de
  culpar criativo ou público.
- CPV alto → normalmente é efeito, não causa. Identificar se veio de CPM, de CTR
  ou de ConvLP antes de propor ação.
- CAC e ROAS são resultados acumulados — não tratá-los como ponto de otimização
  isolado; apontar a etapa que perdeu eficiência.
- Amostra curta manda: com ticket de ~R$ 300, períodos com 1–3 vendas não
  sustentam veredito de corte ou escala. Diga isso explicitamente.
- Mudança de público/escala → quedas moderadas em CTR/Tx‑CHK podem ser esperadas
  ao expandir audiências; comparar a perda com o aumento de volume/faturamento
  antes de classificar como gargalo.
- Venda sem UTM completa não entra na dash (regra do cliente) — nunca reporte
  essas linhas como venda perdida nem as some ao faturamento.
- Sempre considerar o **histórico da própria conta**: uma métrica abaixo de
  benchmark geral pode ainda ser um bom resultado se estiver acima da média
  histórica da operação. Priorizar **tendência ao longo do tempo** sobre valor
  absoluto isolado.

## Unidade de análise do anúncio: campanha + conjunto + anúncio

O mesmo anúncio (mesmo nome) pode rodar em campanhas/conjuntos diferentes com
resultados diferentes. A unidade operacional obrigatória é sempre a tripla
**campanha + conjunto + anúncio** (`por_anuncio` em `relatorios_dados.json` já
vem quebrado nessa granularidade). Nunca dê uma única decisão global a um
anúncio sem checar `criativos_consolidado` — se `n_estruturas > 1`, faça as
duas análises: consolidada (resultado total do criativo) e por ocorrência
(cada estrutura recebe decisão própria). "Cortar esta ocorrência nesta
estrutura" é uma decisão diferente de "cortar o criativo em todas as
estruturas" — nunca generalize corte de 1 estrutura fraca para o criativo
inteiro que é vencedor nas demais.

## Nível correto de orçamento (ABO x CBO)

Em **ABO** (orçamento por conjunto), o ajuste de verba é feito no **conjunto
de anúncios**. Em **CBO** (orçamento por campanha), o ajuste é na
**campanha**. No **anúncio**, as ações possíveis são ativar, pausar,
duplicar, substituir ou replicar — nunca "aumentar a verba do anúncio" como
se o orçamento estivesse configurado nele. A fonte de dados atual (planilha
de mídia paga) **não informa o tipo de orçamento** por estrutura — nunca
assuma ABO ou CBO; quando não for possível confirmar, escreva a recomendação
de forma neutra ("ajustar o orçamento no nível do conjunto/campanha,
conforme a configuração real — confirmar no Gerenciador de Anúncios antes de
executar").

## Como citar "padrão de mercado" no texto

Os limiares/benchmarks deste guia (ex.: ConvLP crítica abaixo de 70%) são
**referências gerais de funil de venda direta**, não dados medidos deste
cliente — nenhuma busca em tempo real acontece na geração automática. Sempre
que o texto usar um desses benchmarks, deixe explícito que é "referência
geral de mercado" (e não um número exclusivo desta conta), e prefira comparar
primeiro com o **histórico da própria conta** quando ele já existir.
