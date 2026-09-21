#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gera build/relatorios_dados.json: SÓ NÚMEROS (nenhuma interpretação/texto),
agregados por período/campanha/conjunto/anúncio a partir dos mesmos dados que
alimentam o dashboard (Meta Ads x Compradores). É o insumo lido pela Routine do
Claude (ver GUIA-RELATORIOS.md) para escrever build/relatorios.json — garante
que os números do texto batem 1:1 com o site sem depender do Claude "fazer
conta". Não chama nenhuma API de IA/LLM.

Uso:
    python build/coletar_dados_relatorio.py --out build/relatorios_dados.json
    python build/coletar_dados_relatorio.py --meta-file meta.csv --sales-file sales.csv --out build/relatorios_dados.json

Sem --meta-file/--sales-file, busca os CSVs públicos das planilhas (mesma URL de
build.py) — precisa de acesso a docs.google.com (o runner do GitHub Actions tem;
o sandbox do agente normalmente não).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as bp  # reaproveita fetch/parse/process/constantes de build.py
from relatorio_lib import (
    BRT, d, build_periods, in_range, agg, derived, shift_back,
    previous_period, compare, funnel_health, money, pct, num,
)


def daily_series(meta: list[dict], sales: list[dict], start, end, camp=None, adset=None, ad=None) -> list[dict]:
    """Uma linha por dia (gasto/visitas/checkouts/vendas + derivadas) — dá ao
    Claude a base pra enxergar tendência (ex.: CPM subindo/ConvLP caindo N dias
    seguidos)."""
    out = []
    cur = start
    while cur <= end:
        a = derived(agg(meta, sales, cur, cur, camp=camp, adset=adset, ad=ad))
        if a["spend"] or a["vendas"]:
            out.append({
                "d": cur.strftime("%Y-%m-%d"),
                "spend": round(a["spend"], 2), "impr": a["impr"], "clicks": a["clicks"],
                "vis": a["vis"], "chk": a["chk"], "vendas": a["vendas"], "fat": round(a["fat"], 2),
                "cpm": _r(a["cpm"]), "ctr": _r(a["ctr"], 4), "cpc": _r(a["cpc"]),
                "convlp": _r(a["convlp"], 4), "cpv": _r(a["cpv"]), "cpchk": _r(a["cpchk"]),
                "cac": _r(a["cac"]), "roas": _r(a["roas"], 4), "ticket": _r(a["ticket"]),
            })
        cur += timedelta(days=1)
    return out


def _r(v, nd=2):
    return None if v is None else round(v, nd)


def totais_dict(a: dict) -> dict:
    return {
        "spend": round(a["spend"], 2), "impr": a["impr"], "clicks": a["clicks"],
        "vis": a["vis"], "chk": a["chk"], "vendas": a["vendas"], "fat": round(a["fat"], 2),
        "cpm": _r(a["cpm"]), "ctr": _r(a["ctr"], 4), "cpc": _r(a["cpc"]),
        "convlp": _r(a["convlp"], 4), "cpv": _r(a["cpv"]),
        "txchk": _r(a["txchk"], 4), "cpchk": _r(a["cpchk"]),
        "txvenda": _r(a["txvenda"], 4), "convvis": _r(a["convvis"], 4),
        "cac": _r(a["cac"]), "roas": _r(a["roas"], 4), "ticket": _r(a["ticket"]),
    }


def breakdown(meta: list[dict], sales: list[dict], start, end, dim: str, camp_filter=None) -> list[dict]:
    """Agrega por campanha/conjunto/anúncio dentro do período (só métricas
    agregadas — SEM série diária por estrutura, que inchava o arquivo). A série
    diária existe apenas AGREGADA no nível do período (ver periodo_payload)."""
    def key_of(r):
        if dim == "camp":
            return r["camp"]
        if dim == "adset":
            return (r["camp"], r["adset"])
        return (r["camp"], r["adset"], r["ad"])

    keys = set()
    for r in meta:
        if in_range(r["d"], start, end) and (camp_filter is None or r["camp"] == camp_filter):
            keys.add(key_of(r))
    for r in sales:
        if in_range(r["d"], start, end) and (camp_filter is None or r["camp"] == camp_filter):
            keys.add(key_of(r))

    out = []
    for k in sorted(keys, key=lambda x: str(x)):
        if dim == "camp":
            camp, adset, ad = k, None, None
        elif dim == "adset":
            camp, adset, ad = k[0], k[1], None
        else:
            camp, adset, ad = k

        a = derived(agg(meta, sales, start, end, camp=camp, adset=adset, ad=ad))
        if not a["spend"] and not a["vendas"]:
            continue
        row = totais_dict(a)
        if dim == "camp":
            row["campanha"] = camp
        elif dim == "adset":
            row["campanha"], row["conjunto"] = camp, adset
        else:
            row["campanha"], row["conjunto"], row["anuncio"] = camp, adset, ad
        out.append(row)
    out.sort(key=lambda r: -r["spend"])
    return out


def consolidado_criativos(por_anuncio: list[dict]) -> list[dict]:
    """Agrupa as ocorrências (campanha+conjunto+anúncio) de `por_anuncio` pelo
    NOME do anúncio — visão consolidada do criativo (regra §11-A do briefing:
    o mesmo criativo pode rodar em várias estruturas com resultados diferentes)."""
    by_ad: dict[str, list[dict]] = {}
    for row in por_anuncio:
        by_ad.setdefault(row["anuncio"], []).append(row)

    out = []
    for ad, occs in by_ad.items():
        spend = sum(o["spend"] for o in occs)
        impr = sum(o["impr"] for o in occs)
        clicks = sum(o["clicks"] for o in occs)
        vis = sum(o["vis"] for o in occs)
        chk = sum(o["chk"] for o in occs)
        vendas = sum(o["vendas"] for o in occs)
        fat = sum(o["fat"] for o in occs)
        occs_com_venda = [o for o in occs if o["vendas"]]
        melhor = min(occs_com_venda, key=lambda o: o["cac"]) if occs_com_venda else None
        pior = max(occs_com_venda, key=lambda o: o["cac"]) if occs_com_venda else None
        out.append({
            "anuncio": ad,
            "n_estruturas": len(occs),
            "estruturas": [{"campanha": o["campanha"], "conjunto": o["conjunto"]} for o in occs],
            "spend": round(spend, 2), "impr": impr, "clicks": clicks,
            "vis": vis, "chk": chk, "vendas": vendas, "fat": round(fat, 2),
            "cpm": round(spend / impr * 1000, 2) if impr else None,
            "ctr": round(clicks / impr, 4) if impr else None,
            "convlp": round(vis / clicks, 4) if clicks else None,
            "cpv": round(spend / vis, 2) if vis else None,
            "cpchk": round(spend / chk, 2) if chk else None,
            "cac": round(spend / vendas, 2) if vendas else None,
            "roas": round(fat / spend, 4) if spend else None,
            "ticket": round(fat / vendas, 2) if vendas else None,
            "melhor_estrutura": (
                {"campanha": melhor["campanha"], "conjunto": melhor["conjunto"], "cac": melhor["cac"]}
                if melhor else None
            ),
            "pior_estrutura": (
                {"campanha": pior["campanha"], "conjunto": pior["conjunto"], "cac": pior["cac"]}
                if pior and pior is not melhor else None
            ),
        })
    out.sort(key=lambda r: -r["spend"])
    return out


def whatsapp_numeros(label: str, start, end, cur: dict, saude: dict) -> dict:
    """Números já formatados (moeda/percentual) para o bloco copiável do
    WhatsApp — a Routine do Claude só preenche destaques/ações em texto,
    nunca recalcula nem inventa estes valores (regra §6 do briefing)."""
    return {
        "periodo_label": label,
        "periodo_range": f"{start.strftime('%d/%m/%Y')} a {end.strftime('%d/%m/%Y')}",
        "gasto": money(cur["spend"]), "cpm": money(cur["cpm"]), "ctr": pct(cur["ctr"]),
        "cpc": money(cur["cpc"]), "conv_lp": pct(cur["convlp"]),
        "visitas": num(cur["vis"]), "cpv": money(cur["cpv"]),
        "checkouts": num(cur["chk"]) if cur["chk"] else "Não disponível",
        "cpchk": money(cur["cpchk"]) if cur["cpchk"] is not None else "Não disponível",
        "vendas": num(cur["vendas"]), "faturamento": money(cur["fat"]),
        "cac": money(cur["cac"]), "roas": (f"{cur['roas']:.2f}x".replace(".", ",") if cur["roas"] is not None else "—"),
        "ticket_medio": money(cur["ticket"]),
        "saude_funil": (
            f"{saude['nota']:.1f}/10 — {saude['classificacao']}" + (" (provisória)" if saude["provisoria"] else "")
            if saude["nota"] is not None else "Nota provisória — dados insuficientes"
        ),
    }


def periodo_payload(meta: list[dict], sales: list[dict], today, start, end, key, date_min, date_max,
                     meta_cac, meta_roas, volume_min) -> dict:
    cur = derived(agg(meta, sales, start, end))
    ref7 = derived(agg(meta, sales, today - timedelta(days=6), today))
    ref14 = derived(agg(meta, sales, today - timedelta(days=13), today))
    ref30 = derived(agg(meta, sales, today - timedelta(days=29), today))

    p_start, p_end, metodo = previous_period(key, start, end, today, date_min, date_max)
    anterior = derived(agg(meta, sales, p_start, p_end)) if p_start else None

    saude = funnel_health(cur, ref30, meta_cac, meta_roas, volume_min, [ref7, ref14, ref30])
    por_anuncio = breakdown(meta, sales, start, end, "ad")

    return {
        "range": {"start": start.strftime("%Y-%m-%d"), "end": end.strftime("%Y-%m-%d")},
        "totais": totais_dict(cur),
        # Série diária AGREGADA do período (não por estrutura) — só a base p/ o
        # Claude ver tendência geral (CPM subindo / ConvLP caindo N dias). Limitada
        # aos últimos 60 dias com atividade p/ não inchar "todo período". A série
        # por campanha/conjunto/anúncio foi REMOVIDA de propósito: ela respondia por
        # ~75% do tamanho do arquivo (≈280k tokens) e ninguém a consome — o veredito
        # por estrutura usa as métricas agregadas de por_campanha/conjunto/anuncio.
        "serie_diaria": daily_series(meta, sales, start, end)[-60:],
        "nota_saude": saude,
        "whatsapp_numeros": whatsapp_numeros("", start, end, cur, saude),
        "comparativos": {
            "7d": totais_dict(ref7), "14d": totais_dict(ref14), "30d": totais_dict(ref30),
            "periodo_anterior": {
                "range": ({"start": p_start.strftime("%Y-%m-%d"), "end": p_end.strftime("%Y-%m-%d")}
                          if p_start else None),
                "metodo": metodo,
                "totais": totais_dict(anterior) if anterior else None,
                "variacao": compare(cur, anterior),
            },
        },
        "por_campanha": breakdown(meta, sales, start, end, "camp"),
        "por_conjunto": breakdown(meta, sales, start, end, "adset"),
        "por_anuncio": por_anuncio,
        "criativos_consolidado": consolidado_criativos(por_anuncio),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--meta-file")
    ap.add_argument("--sales-file")
    ap.add_argument("--out", default="build/relatorios_dados.json")
    args = ap.parse_args()

    meta_rows = bp.load_rows(bp.sheet_url(bp.META_SPREADSHEET_ID, bp.META_SHEET), args.meta_file)
    sales_rows = bp.load_rows(bp.sheet_url(bp.SALES_SPREADSHEET_ID, bp.SALES_SHEET), args.sales_file)
    data = bp.process(meta_rows, sales_rows)
    meta, sales = data["meta"], data["sales"]

    now_brt = datetime.now(BRT)
    today = now_brt.date()
    date_min = d(data["build"]["date_min"]) if data["build"]["date_min"] else None
    date_max = d(data["build"]["date_max"]) if data["build"]["date_max"] else None

    periods = build_periods(today, date_min, date_max)

    out = {
        "generated_at": now_brt.strftime("%d/%m/%Y %H:%M"),
        "generated_at_iso": now_brt.isoformat(),
        "fonte": "Números brutos agregados a partir do funil de venda direta (Meta Ads × Compradores) — insumo para a "
                 "Routine do Claude escrever build/relatorios.json (Insights de Tráfego). Sem "
                 "interpretação/texto aqui, só aritmética.",
        "params": {
            "tax_factor": bp.TAX_FACTOR,
            "sample_min_spend": bp.SAMPLE_MIN_SPEND,
            "sample_min_sales": bp.SAMPLE_MIN_SALES,
            "meta_cac": bp.META_CAC,
            "meta_roas": bp.META_ROAS,
            "volume_min_amostral": bp.VOLUME_MIN_AMOSTRAL,
            "n_dias_corte": bp.N_DIAS_CORTE,
        },
        "periodos": {},
    }
    for key, (start, end, label) in periods.items():
        payload = periodo_payload(meta, sales, today, start, end, key, date_min, date_max,
                                   bp.META_CAC, bp.META_ROAS, bp.VOLUME_MIN_AMOSTRAL)
        payload["whatsapp_numeros"]["periodo_label"] = label
        out["periodos"][key] = {"label": label, **payload}

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("== coletar_dados_relatorio ok ==", file=sys.stderr)
    print(f"  periodos: {list(out['periodos'].keys())}", file=sys.stderr)
    print(f"  out: {args.out}", file=sys.stderr)


if __name__ == "__main__":
    main()
