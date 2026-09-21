#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera a dashboard estatica (index.html) do funil PERPETUO "Cafe da Manha" (cliente
Rogerio) a partir de DUAS planilhas do Google Sheets (somente leitura):

  - Meta Ads — "Extracao Dashboard - Cafe da Manha", aba "Pagina 1":
    investimento/impressoes/cliques/visitas na LP (e Initiate Checkout, quando o
    Adveronix exportar a coluna) por Day x Campaign x Ad Set x Ad.
  - Compradores — "Partiu Empreender | 2026", aba "Cafe da Manha Lucrativo":
    uma linha por compra, com os UTMs do checkout.

NAO existe etapa de lead/MQL neste funil: e' venda direta (perpetuo). O funil e'
  Gasto -> Impressoes -> Cliques -> Visitas na LP -> Checkouts -> Vendas -> Faturamento

ATRIBUICAO: por UTM, nao por telefone (a aba de Compradores nao tem telefone).
utm_campaign/utm_medium/utm_content do checkout sao, respectivamente, o
Campaign Name / Ad Set Name / Ad Name do Meta Ads — batem 1:1 depois de
URL-decode (o checkout as vezes grava "Capta%C3%A7%C3%A3o").

REGRA DE VENDA (decisao do cliente): so conta como venda a linha com UTM
COMPLETA (campanha + conjunto + anuncio). Linha sem UTM normalmente e' Pix
gerado e nao pago — e' descartada e o total descartado aparece no log do build.

Este script apenas LE as planilhas (export CSV publico) e emite os REGISTROS
BRUTOS (meta[] e sales[]) dentro do HTML. Todos os filtros, agregacoes, KPIs,
tabelas e graficos sao calculados no navegador. Nunca escreve nada de volta.

Teste local: --meta-file / --sales-file apontando para CSVs baixados.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import os
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone, timedelta

# --------------------------------------------------------------------------- #
# Fontes de dados (somente leitura)
# --------------------------------------------------------------------------- #
# As abas sao lidas por NOME (endpoint gviz), nao por gid: os gids nao sao
# expostos publicamente pelo Sheets e o nome da aba e' estavel — assim tambem
# nao quebra se as abas forem reordenadas na planilha.
META_SPREADSHEET_ID = "1KEmIpxN6fS-ovuLipmQTzGldKAIYAUznJStGeSSV7rM"
META_SHEET = "Página 1"
SALES_SPREADSHEET_ID = "1Qe1_LFcrd98hhOTa5rJAL78ZRUoHCZ-Pj4kIRgdiljI"
SALES_SHEET = "Cafe da Manha Lucrativo"
EXPORT_URL = "https://docs.google.com/spreadsheets/d/{sid}/gviz/tq?tqx=out:csv&headers=1&sheet={sheet}"

# Identificacao do cliente/oferta (usada so em textos/relatorios).
CLIENT_NAME = "Rogerio"
MAIN_PRODUCT = "Café da Manhã Lucrativo"
FUNNEL_NAME = "Perpétuo"
# Sigla do funil, comum a TODAS as campanhas da conta:
#   "CML | E6-VEN | P3-FRIO | CONV | CBO | VA | 2026-09-02 | Teste de Criativos 1"
#    ^^^ sigla do funil (Cafe da Manha Lucrativo); E6-VEN = etapa de venda,
#        P3-FRIO = publico frio, CONV = objetivo, CBO/ABO = estrutura de verba.
MAIN_PRODUCT_PREFIX = "CML"

BRT = timezone(timedelta(hours=-3))   # horario de Brasilia (exibicao)
TAX_FACTOR = 1.13806   # imposto/taxa sobre o gasto de midia paga (Meta Ads) = 13,806%.
                       # Aplicado so ao gasto do Meta; o toggle "Imposto Meta" do
                       # dashboard liga/desliga. Use 1.0 se nao houver imposto.

# --------------------------------------------------------------------------- #
# Regras da aba Relatorio (Top anuncios)
# --------------------------------------------------------------------------- #
# Amostra minima para JULGAR um anuncio. Abaixo disso ele entra como
# "Em observacao" (dado insuficiente) — nunca e' classificado so porque teve
# 1 venda com pouco investimento. Referencia: 1 ticket medio de gasto.
SAMPLE_MIN_SPEND = 347.0   # gasto minimo (R$) para amostra relevante
SAMPLE_MIN_SALES = 1       # vendas minimas para julgar o anuncio
TOP_ADS_N = 10             # nº de linhas em Top anuncios

# Metas & parametros da conta (DEFAULTS do painel editavel da aba Relatorio).
# Sao so o valor inicial: o gestor edita no navegador (persistido em
# localStorage) e as tabelas de anuncio recoram CAC/ROAS ao vivo.
# None = "meta nao definida" (metrica aparece sem cor ate o gestor preencher).
META_CAC = None            # meta de CAC (R$/venda); None = nao definida
META_ROAS = None           # meta de ROAS (x); None = nao definida
VOLUME_MIN_AMOSTRAL = SAMPLE_MIN_SALES  # vendas minimas p/ amostra confiavel
N_DIAS_CORTE = 5           # dias consecutivos acima do teto p/ considerar corte


# --------------------------------------------------------------------------- #
# Leitura
# --------------------------------------------------------------------------- #
FETCH_RETRIES = 3       # tentativas totais em caso de timeout/erro de rede
FETCH_RETRY_DELAY = 15  # segundos entre tentativas
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/128.0.0.0 Safari/537.36")


def sheet_url(sid: str, sheet: str) -> str:
    return EXPORT_URL.format(sid=sid, sheet=urllib.parse.quote(sheet))


def fetch_csv(url: str) -> list[list[str]]:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "*/*"})
    last_err: Exception | None = None
    for attempt in range(1, FETCH_RETRIES + 1):
        try:
            with urllib.request.urlopen(req, timeout=180) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
            return list(csv.reader(io.StringIO(raw)))
        except (TimeoutError, urllib.error.URLError) as exc:
            last_err = exc
            if attempt < FETCH_RETRIES:
                print(f"[fetch_csv] tentativa {attempt}/{FETCH_RETRIES} falhou ({exc!r}); "
                      f"tentando de novo em {FETCH_RETRY_DELAY}s...", file=sys.stderr)
                time.sleep(FETCH_RETRY_DELAY)
    raise last_err


def read_csv_file(path: str) -> list[list[str]]:
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        return list(csv.reader(f))


def load_rows(url: str, local: str | None) -> list[list[str]]:
    return read_csv_file(local) if local else fetch_csv(url)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def norm(s: str | None) -> str:
    return strip_accents((s or "").strip().lower())


def to_float(v) -> float:
    if v is None:
        return 0.0
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[^\d,.\-]", "", str(v).strip())
    if not s:
        return 0.0
    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s:
        s = s.replace(",", ".")
    try:
        return float(s)
    except ValueError:
        return 0.0


def parse_date(v: str) -> str | None:
    """Aceita 2026-09-02, 03/09/2026 e 03/09/2026 01:22 (a aba de Compradores
    grava data COM hora; sem cortar a hora, o strptime falhava e a venda
    perdia a data)."""
    if not v:
        return None
    s = str(v).strip()
    if not s:
        return None
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", s)
    if m:
        return f"{m.group(1)}-{m.group(2)}-{m.group(3)}"
    s = re.split(r"[ T]", s, 1)[0]          # descarta a parte de hora, se houver
    for fmt in ("%d/%m/%Y", "%m/%d/%Y", "%d/%m/%y", "%b %d, %Y", "%Y/%m/%d"):
        try:
            return datetime.strptime(s, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def is_test_lead(rowtext: str) -> bool:
    return "<test lead" in rowtext.lower()


def urldec(v: str) -> str:
    """UTM do checkout as vezes chega URL-encoded ("Capta%C3%A7%C3%A3o_CML").
    Sem o decode, o mesmo anuncio viraria duas linhas diferentes no dashboard."""
    s = (v or "").strip()
    if "%" not in s:
        return s
    try:
        return urllib.parse.unquote(s)
    except Exception:
        return s


def squash(v: str) -> str:
    """Chave de comparacao entre UTM e nome do Meta: sem acento, minusculo e
    com espacos colapsados (o Sheets as vezes guarda espaco duplo)."""
    return re.sub(r"\s+", " ", norm(v)).strip()


def first_last_initial(name: str) -> str:
    parts = (name or "").strip().split()
    if not parts:
        return "—"
    return parts[0] if len(parts) == 1 else f"{parts[0]} {parts[-1][:1]}."


def mask_email(e: str) -> str:
    e = (e or "").strip()
    if "@" not in e:
        return "—"
    user, dom = e.split("@", 1)
    keep = user[:2] if len(user) > 2 else user[:1]
    return f"{keep}****@{dom}"


def pretty_pay(v: str) -> str:
    """Forma de pagamento legivel (a planilha grava CREDIT_CARD/PIX/BOLETO)."""
    k = norm(v).replace("-", "_").replace(" ", "_")
    return {
        "credit_card": "Cartão de crédito", "creditcard": "Cartão de crédito",
        "debit_card": "Cartão de débito", "pix": "Pix", "boleto": "Boleto",
        "bank_slip": "Boleto", "paypal": "PayPal",
    }.get(k, (v or "").strip() or "—")


def pretty_plat(v: str) -> str:
    """utm_term traz o posicionamento (Instagram_Feed, Facebook_Mobile_Feed...)."""
    s = (v or "").strip()
    return s.replace("_", " ") if s else "—"


# --------------------------------------------------------------------------- #
# Indexacao das colunas
# --------------------------------------------------------------------------- #
def header_index(header, wanted, fallback=None):
    """Casa cabecalhos por alias. Primeiro tenta igualdade exata (sem acento/
    caixa) em TODOS os aliases e so depois 'contem' — senao "utm_campaign"
    casaria com a coluna "utm_campaign_id" que aparecesse antes."""
    fallback = fallback or {}
    idx = {}
    hn = [norm(h) for h in header]
    for key, aliases in wanted.items():
        found = None
        for a in aliases:
            a = norm(a)
            for i, h in enumerate(hn):
                if h == a:
                    found = i
                    break
            if found is not None:
                break
        if found is None:
            for a in aliases:
                a = norm(a)
                for i, h in enumerate(hn):
                    if a and a in h:
                        found = i
                        break
                if found is not None:
                    break
        idx[key] = found if found is not None else fallback.get(key)
    return idx


def cell(row, i):
    if i is None or i < 0 or i >= len(row):
        return ""
    return (row[i] or "").strip()


def require(idx: dict, keys: list[str], header: list[str], origem: str) -> None:
    """Falha ALTO e claro se a planilha mudou de cabecalho — melhor o build
    quebrar (e a dash anterior seguir no ar) do que publicar dash zerada."""
    faltando = [k for k in keys if idx.get(k) is None]
    if faltando:
        raise SystemExit(
            f"[build] ERRO: colunas obrigatorias nao encontradas na aba {origem}: "
            f"{', '.join(faltando)}.\n        Cabecalho lido: {header}\n"
            f"        Ajuste os aliases em build.py (header_index) ou a planilha."
        )


# --------------------------------------------------------------------------- #
# Meta Ads -> registros brutos
# --------------------------------------------------------------------------- #
def process_meta(meta_rows):
    header = meta_rows[0] if meta_rows else []
    idx = header_index(header, {
        "day": ["day", "data", "date"],
        "campaign": ["campaign name", "campanha", "campaign"],
        "adset": ["ad set name", "conjunto", "adset"],
        "ad": ["ad name", "anuncio", "ad"],
        "spent": ["amount spent", "valor gasto", "gasto", "spend"],
        "impr": ["impressions", "impressoes", "impress"],
        "clicks": ["link clicks", "cliques no link", "clicks", "cliques"],
        "pv": ["landing page views", "visualizacoes da pagina de destino", "page views", "pageviews"],
        # Initiate Checkout (o cliente ligou no Adveronix). A QUANTIDADE vem da
        # planilha; o CUSTO por checkout e' calculado na dash (gasto / checkouts),
        # entao nao precisa de coluna de custo aqui.
        "chk": ["initiate checkout", "initiates checkout", "initiated checkout",
                "website initiate checkout", "checkouts iniciados", "checkout iniciado",
                "inicios de finalizacao de compra", "inicio de finalizacao de compra",
                "adds to cart", "add to cart"],
        # Link do criativo — coluna opcional; sem ela a coluna "Link" some da UI.
        "link": ["creative instagram permalink", "instagram permalink", "permalink",
                 "creative link", "link do anuncio", "link do criativo"],
    })
    require(idx, ["day", "campaign", "adset", "ad", "spent", "impr", "clicks"], header, f"Meta Ads ({META_SHEET})")

    meta, ad_links = [], {}
    for row in meta_rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        ad = cell(row, idx["ad"]) or "(sem anúncio)"
        link = cell(row, idx["link"])
        if link and ad not in ad_links:
            ad_links[ad] = link
        meta.append({
            "d": parse_date(cell(row, idx["day"])),
            "camp": cell(row, idx["campaign"]) or "(sem campanha)",
            "adset": cell(row, idx["adset"]) or "(sem conjunto)",
            "ad": ad,
            "sp": round(to_float(cell(row, idx["spent"])), 4),
            "im": to_float(cell(row, idx["impr"])),
            "cl": to_float(cell(row, idx["clicks"])),
            "pv": to_float(cell(row, idx["pv"])),
            "ck": to_float(cell(row, idx["chk"])),
        })
    has_chk = idx["chk"] is not None
    print(f"  meta      : {len(meta)} linhas · colunas: {', '.join(header)}", file=sys.stderr)
    print(f"  checkouts : coluna de Initiate Checkout "
          + ("ENCONTRADA -> funil completo" if has_chk
             else "AUSENTE (Adveronix ainda nao exportou) -> etapa aparece '-'"), file=sys.stderr)
    return meta, ad_links, has_chk


# --------------------------------------------------------------------------- #
# Compradores -> registros brutos (1 registro por COMPRA)
# --------------------------------------------------------------------------- #
def process_sales(sales_rows, meta):
    header = sales_rows[0] if sales_rows else []
    idx = header_index(header, {
        "date": ["data", "date"],
        "name": ["nome", "name"],
        "email": ["email", "e-mail"],
        "valor": ["valor da compra", "valor", "faturamento", "preco"],
        "pay": ["forma de pagto", "forma de pagamento", "metodo de pagamento", "payment"],
        "src": ["utm_source"],
        "camp": ["utm_campaign"],
        "adset": ["utm_medium"],
        "ad": ["utm_content"],
        "plat": ["utm_term"],
    })
    require(idx, ["date", "valor", "camp", "adset", "ad"], header, f"Compradores ({SALES_SHEET})")

    # Nome canonico do Meta por chave normalizada: garante que a venda entre com
    # EXATAMENTE o mesmo texto de campanha/conjunto/anuncio das linhas de midia
    # (senao "Captação" do checkout e "Captação" do Meta virariam 2 linhas).
    canon = {"camp": {}, "adset": {}, "ad": {}}
    for r in meta:
        for k in canon:
            canon[k].setdefault(squash(r[k]), r[k])

    sales, descartadas, sem_meta = [], [], []
    for row in sales_rows[1:]:
        if not any((c or "").strip() for c in row):
            continue
        if is_test_lead(" ".join(str(c) for c in row)):
            continue
        camp = urldec(cell(row, idx["camp"]))
        adset = urldec(cell(row, idx["adset"]))
        ad = urldec(cell(row, idx["ad"]))
        d = parse_date(cell(row, idx["date"]))
        fat = to_float(cell(row, idx["valor"]))
        src = cell(row, idx["src"])
        # REGRA DO CLIENTE: sem UTM completa nao e' venda (normalmente Pix
        # gerado e nao pago). Fica fora de TODOS os numeros da dash.
        if not (camp and adset and ad):
            descartadas.append({"d": d, "fat": fat, "src": src or "(vazio)"})
            continue
        camp_c = canon["camp"].get(squash(camp), camp)
        adset_c = canon["adset"].get(squash(adset), adset)
        ad_c = canon["ad"].get(squash(ad), ad)
        if squash(camp) not in canon["camp"]:
            sem_meta.append((d, camp))
        sales.append({
            "d": d,
            "src": "meta",
            "camp": camp_c,
            "adset": adset_c,
            "ad": ad_c,
            "plat": pretty_plat(cell(row, idx["plat"])),
            "pay": pretty_pay(cell(row, idx["pay"])),
            "vendas": 1,
            "fat": round(fat, 2),
            "nm": first_last_initial(cell(row, idx["name"])),
            "em": mask_email(cell(row, idx["email"])),
        })

    fat_total = sum(s["fat"] for s in sales)
    print(f"  vendas    : {len(sales)} com UTM completa · faturamento R$ {fat_total:,.2f}", file=sys.stderr)
    if descartadas:
        fat_desc = sum(x["fat"] for x in descartadas)
        print(f"  descartadas: {len(descartadas)} linha(s) SEM UTM completa (R$ {fat_desc:,.2f}) — "
              f"regra do cliente: nao contam como venda (Pix gerado e nao pago etc.)", file=sys.stderr)
        for x in descartadas:
            print(f"    - {x['d'] or '?'}  R$ {x['fat']:,.2f}  utm_source={x['src']}", file=sys.stderr)
    if sem_meta:
        print(f"  ATENCAO   : {len(sem_meta)} venda(s) com campanha que NAO existe na aba de Meta Ads "
              f"(entram nos totais, mas sem linha de gasto correspondente):", file=sys.stderr)
        for d, c in sem_meta:
            print(f"    - {d or '?'}  {c}", file=sys.stderr)
    return sales


# --------------------------------------------------------------------------- #
# Processamento -> payload da dashboard
# --------------------------------------------------------------------------- #
def process(meta_rows, sales_rows):
    meta, ad_links, has_chk = process_meta(meta_rows)
    sales = process_sales(sales_rows, meta)

    dates = sorted({d for d in ([m["d"] for m in meta if m["d"]] + [s["d"] for s in sales if s["d"]])})
    now_brt = datetime.now(BRT)
    return {
        "build": {
            "generated_at_brt": now_brt.strftime("%d/%m/%Y %H:%M"),
            "build_id": datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"),
            "today": now_brt.strftime("%Y-%m-%d"),
            "date_min": dates[0] if dates else None,
            "date_max": dates[-1] if dates else None,
            "tax_factor": TAX_FACTOR,
            "client": CLIENT_NAME,
            "product": MAIN_PRODUCT,
            "funnel": FUNNEL_NAME,
            # etapa de checkout so aparece no funil quando a coluna existe
            "has_checkout": has_chk,
            # config da aba Relatorio (lida pelo front)
            "sample_min_spend": SAMPLE_MIN_SPEND,
            "sample_min_sales": SAMPLE_MIN_SALES,
            "top_ads_n": TOP_ADS_N,
            # metas & parametros (defaults do painel editavel; None = nao definida)
            "meta_cac": META_CAC,
            "meta_roas": META_ROAS,
            "volume_min_amostral": VOLUME_MIN_AMOSTRAL,
            "n_dias_corte": N_DIAS_CORTE,
        },
        "meta": meta,
        "sales": sales,
        # Anuncio -> permalink do criativo (vazio enquanto a planilha nao tiver a coluna).
        "ad_links": ad_links,
        # Insights de Trafego (texto pre-escrito, lido de relatorios.json).
        "briefings": {},
    }


# --------------------------------------------------------------------------- #
# Insights de Trafego (aba Relatorio)
# --------------------------------------------------------------------------- #
def load_briefings(path: str) -> dict:
    """Le build/relatorios.json. Estrutura:
        {"generated_at": "...", "periodos": {"<preset>": {...}, ...}}
    Retorna o dict inteiro (ou {} se o arquivo nao existir/for invalido).
    A geracao NAO acontece aqui — este build so le o texto ja pronto, sem
    chamar nenhuma API (custo zero no build/no navegador)."""
    if not path or not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
        return obj if isinstance(obj, dict) else {}
    except (ValueError, OSError):
        return {}


# --------------------------------------------------------------------------- #
# Render
# --------------------------------------------------------------------------- #
def render(data, template_path):
    # A dashboard e montada a partir de arquivos separados (visual x logica):
    #   template.html          -> esqueleto HTML (placeholders __STYLES__/__APP_JS__)
    #   identidade-visual.css  -> TODAS as cores (edite aqui p/ mexer so em cor)
    #   estilos.css            -> layout/componentes
    #   app.js                 -> logica + renderizacao
    # Esta funcao so COSTURA os arquivos e injeta os dados; nao altera nada deles.
    base = os.path.dirname(os.path.abspath(template_path))

    def readf(name):
        with open(os.path.join(base, name), "r", encoding="utf-8") as f:
            return f.read()

    with open(template_path, "r", encoding="utf-8") as f:
        tpl = f.read()
    styles = readf("identidade-visual.css") + "\n" + readf("estilos.css")
    tpl = tpl.replace("__STYLES__", styles)
    tpl = tpl.replace("__APP_JS__", readf("app.js"))
    tpl = tpl.replace("__DATA_JSON__", json.dumps(data, ensure_ascii=False))
    tpl = tpl.replace("__BUILD_ID__", data["build"]["build_id"])
    tpl = tpl.replace("__GENERATED_BRT__", data["build"]["generated_at_brt"])
    return tpl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta-file", help="CSV local da aba de Meta Ads")
    ap.add_argument("--sales-file", help="CSV local da aba de Compradores")
    ap.add_argument("--template", default="build/template.html")
    ap.add_argument("--out", default="dist/index.html")
    args = ap.parse_args()

    print("== build ==", file=sys.stderr)
    meta_rows = load_rows(sheet_url(META_SPREADSHEET_ID, META_SHEET), args.meta_file)
    sales_rows = load_rows(sheet_url(SALES_SPREADSHEET_ID, SALES_SHEET), args.sales_file)

    data = process(meta_rows, sales_rows)

    # Insights de Trafego (texto pre-escrito) — lidos do arquivo versionado ao
    # lado do template. Sem chamada de API no build.
    briefings_path = os.path.join(os.path.dirname(os.path.abspath(args.template)), "relatorios.json")
    data["briefings"] = load_briefings(briefings_path)

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write(render(data, args.template))

    b = data["build"]
    sp = sum(m["sp"] for m in data["meta"])
    vis = sum(m["pv"] for m in data["meta"])
    chk = sum(m["ck"] for m in data["meta"])
    vd = sum(s["vendas"] for s in data["sales"])
    fat = sum(s["fat"] for s in data["sales"])
    print(f"  periodo   : {b['date_min']} -> {b['date_max']}", file=sys.stderr)
    print(f"  gasto     : R$ {sp:,.2f} (sem imposto) · visitas LP: {vis:,.0f} · checkouts: {chk:,.0f}", file=sys.stderr)
    print(f"  resultado : {vd} venda(s) · R$ {fat:,.2f} · CAC R$ {(sp*TAX_FACTOR/vd) if vd else 0:,.2f} "
          f"· ROAS {(fat/(sp*TAX_FACTOR)) if sp else 0:,.2f}x (c/ imposto)", file=sys.stderr)
    print(f"  out       : {args.out}", file=sys.stderr)
    print("== build ok ==", file=sys.stderr)


if __name__ == "__main__":
    main()
