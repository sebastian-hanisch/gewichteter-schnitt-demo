"""Kennzahlen, Experimente und Verdikte. Alle sichtbaren Zahlen kommen aus diesen Funktionen."""

import statistics
from dataclasses import dataclass
from functools import lru_cache

import gwi_constants as C
from gwi_algorithm import (
    TIEBREAKS,
    best_by_size,
    elements,
    greedy_by_cost,
    improve_to_extreme,
    popcount,
    small_weighted_row,
    tie_pair,
    tie_search,
    total_cost,
    weighted_steps,
    worst_of_size,
    is_extreme,
)
from gwi_systems import get_pair


def de(x: float, digits: int = 1) -> str:
    """Zahl mit Dezimalkomma."""
    return f"{x:.{digits}f}".replace(".", ",")


def prozent(x: float, digits: int = 1) -> str:
    return de(100.0 * x, digits)


def zahl(n: int) -> str:
    """Ganze Zahl mit Leerzeichen als Tausendertrenner und echtem Minuszeichen."""
    return f"{n:,}".replace(",", " ").replace("-", "−")


def elemente(k: int) -> str:
    return "1 Element" if k == 1 else f"{k} Elemente"


@dataclass(frozen=True)
class Settings:
    n: int = C.DEFAULT_N
    seed: int = C.DEFAULT_SEED
    system: str = "regenbogen"
    k: int = C.DEFAULT_K


@dataclass(frozen=True)
class Analysis:
    settings: Settings
    m: int
    labels: tuple
    kind: str                   # "kanten" oder "boegen"
    costs: tuple
    opt: int                    # größte gemeinsame unabhängige Menge
    curve: tuple                # kleinste Kosten je Elementzahl k = 0 bis opt (Aufzählung)
    n_common: int


def pair_of(settings: Settings):
    return get_pair(settings.system, settings.n, settings.seed, settings.k)


def analyse(settings: Settings) -> Analysis:
    p = pair_of(settings)
    best = best_by_size(p)
    return Analysis(settings, p.m, p.labels, p.kind, tuple(p.costs), p.opt, tuple(best[k] for k in range(p.opt + 1)), p.n_common)


def names(a: Analysis, mask: int) -> str:
    return ", ".join(a.labels[e] for e in elements(mask, a.m))


def setstr(a: Analysis, mask: int) -> str:
    """Menge als {a, b, c}; die leere Menge als ∅."""
    return "{" + names(a, mask) + "}" if mask else "∅"


def seq(a: Analysis, path) -> str:
    return " → ".join(a.labels[v] for v in path)


def increments(curve) -> list[int]:
    return [b - x for x, b in zip(curve, curve[1:])]


def is_convex(curve) -> bool:
    d = increments(curve)
    return all(d2 >= d1 for d1, d2 in zip(d, d[1:]))


# --- Hauptansicht: Kostenkurve und Weg --------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=32)
def steps_view(settings: Settings) -> tuple:
    return tuple(weighted_steps(pair_of(settings)))


def round_groups(a: Analysis, rounds, k: int) -> list:
    """Gruppen für das Bild zu I_k: die Menge und der Weg, der von I_{k−1} zu ihr geführt hat."""
    groups = [("I_k (billigste Menge mit k Elementen)", elements(rounds[k]["set"], a.m), C.COLOR_SET)]
    path = rounds[k - 1]["path"] if k >= 1 else None
    if path:
        groups.append(("Weg von I_{k−1} nach I_k", list(path), C.COLOR_PATH))
    return groups


def edge_costs(a: Analysis, groups) -> dict:
    return {e: str(a.costs[e]) for _, ids, _ in groups for e in ids}


def round_rows(a: Analysis, rounds, k: int) -> list[dict]:
    """Die Elemente beim Schritt von I_{k−1} nach I_k: Kosten, ob in I_{k−1}, Länge im Austauschgraphen, Entfernung von den Quellen, Stelle im Weg."""
    rd = rounds[k - 1]
    pos = {v: i + 1 for i, v in enumerate(rd["path"] or [])}
    rows = []
    for e in range(a.m):
        rows.append({
            "Element": a.labels[e], "Kosten": a.costs[e], "in I_{k−1}": "ja" if rd["set"] >> e & 1 else "nein", "Länge": zahl(rd["lengths"][e]),
            "kürzeste Entfernung": zahl(rd["dist"][e]) if e in rd["dist"] else "–", "im Weg": str(pos[e]) if e in pos else "–",
        })
    return rows


def verdict_step(a: Analysis, rounds, k: int) -> tuple[str, str]:
    rd, prev = rounds[k], rounds[k - 1]
    path = prev["path"]
    length = prev["length"]
    if rd["cost"] - prev["cost"] != length or rd["cost"] != a.curve[k]:
        return "error", "Die Kosten von I_k stimmen nicht mit dem Weg oder der Aufzählung überein. Das darf nicht sein: Rechenfehler."
    parts = " + ".join(zahl(prev["lengths"][v]) for v in path).replace("+ −", "− ")
    parts = parts + " = " if len(path) > 1 else ""
    delta = increments(a.curve)
    before = f" (vorher {zahl(delta[k - 2])})" if k >= 2 else ""
    return "success", (
        f"I_{k} = {setstr(a, rd['set'])} kostet **{zahl(rd['cost'])}**. Der kürzeste Weg von I_{k - 1} hat {elemente(len(path))}: {seq(a, path)}; seine Länge ist {parts}**{zahl(length)}**. "
        f"Die Kosten wachsen also um {zahl(length)}{before}; das Minimum über alle gemeinsamen Mengen mit {k} Elementen ist ebenfalls {zahl(a.curve[k])}."
    )


def curve_data(a: Analysis) -> dict:
    return {"ks": list(range(a.opt + 1)), "costs": list(a.curve), "deltas": increments(a.curve)}


def verdict_curve(a: Analysis, rounds) -> tuple[str, str]:
    if [r["cost"] for r in rounds] != list(a.curve) or len(rounds) != a.opt + 1:
        return "error", "Die Kosten der Läufe stimmen nicht mit der Aufzählung überein. Das darf nicht sein: Rechenfehler."
    d = increments(a.curve)
    if is_convex(a.curve):
        return "success", (
            f"Die kleinsten Kosten wachsen **konvex** mit der Elementzahl: Zuwächse {', '.join(zahl(x) for x in d)} (jeder mindestens so groß wie der vorige). "
            f"Alle {a.opt} Schritte des Verfahrens liefern die billigste Menge ihrer Größe; am Ende (k = {a.opt}) gibt es keinen Weg mehr."
        )
    return "warning", f"Die Zuwächse {', '.join(zahl(x) for x in d)} wachsen nicht durchgehend: Die Kostenkurve ist nicht konvex."


# --- Experiment 1: Greedy nach Kosten -----------------------------------------------------------------------------------------------------------


def greedy_view(settings: Settings) -> dict:
    p = pair_of(settings)
    g = greedy_by_cost(p)
    best = best_by_size(p)
    k = popcount(g)
    return {"set": g, "k": k, "cost": total_cost(p, g), "best_at_k": best[k], "opt": p.opt, "best_cost": best[p.opt], "stuck": k < p.opt, "costlier": total_cost(p, g) > best[k]}


def verdict_greedy(a: Analysis, v: dict) -> tuple[str, str]:
    head = f"Greedy nach Kosten (billigste Leitung zuerst) wählt {setstr(a, v['set'])}: {elemente(v['k'])} für {zahl(v['cost'])}. "
    if v["stuck"]:
        extra = f"Es **bleibt stecken**: Das Optimum hat {elemente(v['opt'])} (kleinste Kosten {zahl(v['best_cost'])}). "
        extra += f"Bei {v['k']} Elementen wäre {zahl(v['best_at_k'])} möglich" + (f", Greedy zahlt {zahl(v['cost'] - v['best_at_k'])} mehr." if v["costlier"] else ", Greedy zahlt dort nicht mehr.")
        return "warning", head + extra
    if v["costlier"]:
        return "warning", head + f"Es erreicht die größte Elementzahl, ist aber **teurer** als das Optimum ({zahl(v['best_at_k'])}): {zahl(v['cost'] - v['best_at_k'])} mehr ({prozent(v['cost'] / v['best_at_k'] - 1)} %)."
    return "success", head + "Es erreicht die größte Elementzahl und die kleinsten Kosten."


@lru_cache(maxsize=4)
def greedy_series(system: str) -> tuple:
    """Greedy nach Kosten gegen das Optimum: je Plangröße (Regenbogen mit n − 1 Farben, Zuordnung; Seeds 0 bis 19), bei der Arboreszenz 30 Kostenvektoren (Seeds 0 bis 29)."""
    rows = []
    groups = [(n, range(C.SERIES_SEEDS)) for n in C.SERIES_N] if system != "arboreszenz" else [(0, range(C.ARB_COST_SEEDS))]
    for n, seeds in groups:
        stuck = costlier = reach_opt = 0
        excess = []
        for seed in seeds:
            s = Settings(n, seed, system, n - 1 if system == "regenbogen" else C.DEFAULT_K)
            v = greedy_view(s)
            stuck += v["stuck"]
            if not v["stuck"]:
                reach_opt += 1
                costlier += v["costlier"]
                excess.append(v["cost"] / v["best_at_k"] - 1 if v["best_at_k"] else 0.0)
        rows.append({"n": n, "plans": len(seeds), "stuck": stuck, "costlier": costlier, "reach": reach_opt, "excess": statistics.mean(excess) if excess else 0.0})
    return tuple(rows)


def greedy_series_table(system: str, rows) -> list[dict]:
    out = []
    for r in rows:
        out.append({("Standorte" if system != "arboreszenz" else "Kostenvektoren"): (r["n"] if system != "arboreszenz" else r["plans"]), "Pläne": r["plans"], "Greedy bleibt vor der größten Elementzahl stecken": r["stuck"],
                    "bei gleicher Größe teurer": f"{r['costlier']} von {r['reach']}", "mittlerer Aufschlag dort": f"{prozent(r['excess'])} %"})
    return out


def verdict_greedy_series(system: str, rows) -> tuple[str, str]:
    plans = sum(r["plans"] for r in rows)
    stuck = sum(r["stuck"] for r in rows)
    costlier = sum(r["costlier"] for r in rows)
    reach = sum(r["reach"] for r in rows)
    return "info", (
        f"Von {plans} Beispielen bleibt Greedy nach Kosten bei **{stuck}** vor der größten Elementzahl stecken (die Kosten allein sind dann nicht der Grund); "
        f"von den {reach}, die sie erreichen, ist es bei **{costlier}** teurer als das Optimum."
    )


# --- Experiment 2: Zertifikat (kein negativer Kreis) und Tauschkreis -----------------------------------------------------------------------------


def cert_rows(a: Analysis, rounds) -> list[dict]:
    rows = []
    for k, rd in enumerate(rounds):
        rows.append({"k": k, "Kosten von I_k": zahl(rd["cost"]), "Relaxierungsrunden (Bellman–Ford)": rd["rounds"], "Verbesserungen": rd["relax"],
                         "Kreis negativer Länge": "nein" if not rd["neg"] else "ja"})
    return rows


def cert_view(settings: Settings, rounds, k: int) -> dict:
    """Zu k: die billigste Menge I_k (kein negativer Kreis) und als Gegenstück die teuerste gemeinsame Menge mit k Elementen mit der Kette von Tauschkreisen bis zur billigsten."""
    p = pair_of(settings)
    worst = worst_of_size(p, k)
    chain = improve_to_extreme(p, worst)
    return {"k": k, "best": rounds[k]["set"], "worst": worst, "chain": chain, "best_extreme": is_extreme(p, rounds[k]["set"]), "worst_extreme": is_extreme(p, worst), "final": chain[-1]["after"] if chain else worst}


def chain_rows(a: Analysis, view: dict) -> list[dict]:
    rows = [{"Schritt": 0, "Menge": setstr(a, view["worst"]), "Kosten": zahl(total_cost_of(a, view["worst"])), "Kreis": "–", "Länge des Kreises": "–"}]
    for i, st in enumerate(view["chain"], 1):
        rows.append({"Schritt": i, "Menge": setstr(a, st["after"]), "Kosten": zahl(st["cost"]), "Kreis": seq(a, st["cycle"]) + f" → {a.labels[st['cycle'][0]]}", "Länge des Kreises": zahl(st["length"])})
    return rows


def total_cost_of(a: Analysis, mask: int) -> int:
    return sum(a.costs[e] for e in elements(mask, a.m))


def verdict_cert(a: Analysis, view: dict) -> tuple[str, str]:
    k = view["k"]
    if not view["best_extreme"]:
        return "error", "Die billigste Menge hat einen Kreis negativer Länge. Das darf nicht sein: Rechenfehler."
    final_cost = total_cost_of(a, view["final"])
    if final_cost != a.curve[k]:
        return "error", "Die Tauschkreise führen nicht zu den kleinsten Kosten. Das darf nicht sein: Rechenfehler."
    if not view["chain"]:
        return "success", f"Bei k = {k} gibt es nur Mengen mit gleichen Kosten ({zahl(a.curve[k])}) oder nur eine: Auch die teuerste hat keinen Kreis negativer Länge."
    first = view["chain"][0]
    return "success", (
        f"Die billigste Menge mit {k} Elementen (Kosten {zahl(a.curve[k])}) hat **keinen** Kreis negativer Länge. Die teuerste gemeinsame Menge mit {k} Elementen ({zahl(total_cost_of(a, view['worst']))}) hat einen "
        f"(Länge {zahl(first['length'])}, {elemente(len(first['cycle']))}); nach {len(view['chain'])} Tauschkreis(en) sind die Kosten bei {zahl(final_cost)}: die kleinsten."
    )


# --- Experiment 3: Gleichstand -----------------------------------------------------------------------------------------------------------------


def tie_view() -> dict:
    p = tie_pair()
    best = best_by_size(p)
    out = {"best": best, "opt": p.opt, "runs": {}}
    for v in TIEBREAKS:
        rounds = weighted_steps(p, v)
        out["runs"][v] = {"rounds": rounds, "valid": [bool(p.common[r["set"]]) for r in rounds], "reached": len(rounds) - 1}
    return out


TIE_NAMES = {"hops": "Länge, dann wenigste Knoten", "any": "nur die Länge (Pfeile in Erzeugungsreihenfolge)", "rev": "nur die Länge (Pfeile umgekehrt)"}


def tie_rows(view: dict) -> list[dict]:
    p = tie_pair()
    labels = tuple("abcde")
    out = []
    for v, run in view["runs"].items():
        mask_names = lambda m: "{" + ", ".join(labels[e] for e in elements(m, 5)) + "}" if m else "∅"
        out.append({"Wegwahl": TIE_NAMES[v], "erreichte Elementzahl": run["reached"], "Mengen I_0, I_1, …": " ; ".join(mask_names(r["set"]) for r in run["rounds"]),
                    "alle gemeinsam unabhängig": "ja" if all(run["valid"]) else "nein", "Wege (Knotenzahl)": ", ".join(str(len(r["path"])) for r in run["rounds"] if r["path"]) or "–"})
    return out


def verdict_tie(view: dict) -> tuple[str, str]:
    ok = view["runs"]["hops"]
    if ok["reached"] != view["opt"] or not all(ok["valid"]) or [r["cost"] for r in ok["rounds"]] != [view["best"][k] for k in range(view["opt"] + 1)]:
        return "error", "Mit der Knotenzahl-Regel stimmt das Ergebnis nicht. Das darf nicht sein: Rechenfehler."
    bad = [v for v in ("any", "rev") if view["runs"][v]["reached"] != view["opt"] or not all(view["runs"][v]["valid"])]
    if not bad:
        return "info", "In diesem Beispiel liegen alle Wegwahlen richtig."
    first = view["runs"][bad[0]]
    invalid = next(i for i, ok_ in enumerate(first["valid"]) if not ok_)
    return "warning", (
        f"Mit „Länge, dann wenigste Knoten“ führt der Lauf bis zur Elementzahl {view['opt']} und alle I_k sind gemeinsam unabhängig. Ohne die Knotenzahl-Regel liegt die Wegwahl "
        f"(hier: {', '.join(TIE_NAMES[v] for v in bad)}) falsch: Der Weg ist bei gleicher Länge ein Umweg mit einer Abkürzung, I_{invalid} ist **nicht mehr in beiden Matroiden unabhängig**, "
        f"und der Lauf endet bei Elementzahl {first['reached']} statt {view['opt']}."
    )


@lru_cache(maxsize=1)
def tie_series() -> dict:
    return tie_search(C.TIE_PAIRS, C.PLAY_SEED + 5)


def verdict_tie_series(res: dict) -> tuple[str, str]:
    if res["fail"]["hops"]:
        return "error", "Mit der Knotenzahl-Regel scheitert ein Zufallspaar. Das darf nicht sein: Rechenfehler."
    return "info", (
        f"Bei {zahl(res['pairs'])} Zufallspaaren mit 5 Elementen und Kosten aus {{0, 1, 2}} scheitert die Wegwahl **mit** Knotenzahl-Regel bei **0**, die nur nach der Länge bei "
        f"**{res['fail']['any']}** (Pfeile in Erzeugungsreihenfolge) und **{res['fail']['rev']}** (umgekehrt) Paaren ({prozent(res['fail']['any'] / res['pairs'])} % und {prozent(res['fail']['rev'] / res['pairs'])} %); "
        f"jedes Mal ist die erzeugte Menge nicht mehr in beiden Matroiden unabhängig."
    )


# --- Experiment 4: alle kleinen Paare -----------------------------------------------------------------------------------------------------------


@lru_cache(maxsize=1)
def small_rows() -> tuple:
    return tuple(small_weighted_row(n, 10 ** 9 if n <= 4 else C.SMALL_SAMPLE, C.PLAY_SEED) for n in range(2, C.ENUM_MAX_N + 1))


def small_table(rows) -> list[dict]:
    return [{
        "Elemente n": r["n"], "Paare": zahl(r["pairs"]), "Läufe (zwei Kostenvektoren je Paar)": zahl(r["runs"]), "richtig mit Knotenzahl-Regel": zahl(r["ok"]["hops"]),
        "richtig nur nach Länge": f"{zahl(r['ok']['any'])} und {zahl(r['ok']['rev'])}", "Kosten je Elementzahl konvex": f"{zahl(r['convex'])} von {zahl(r['convex_checked'])}",
        "gemeinsame Mengen: extrem gleich kein negativer Kreis": f"{zahl(r['extreme_agree'])} von {zahl(r['common_sets'])}" if r["extreme_checked"] else "nicht geprüft",
    } for r in rows]


def verdict_small(rows) -> tuple[str, str]:
    runs = sum(r["runs"] for r in rows)
    hops = sum(r["ok"]["hops"] for r in rows)
    convex = sum(r["convex"] for r in rows)
    convex_checked = sum(r["convex_checked"] for r in rows)
    sets = sum(r["common_sets"] for r in rows)
    agree = sum(r["extreme_agree"] for r in rows)
    if hops != runs or convex != convex_checked or agree != sets:
        return "error", "Eine der Aussagen ist bei einem kleinen Paar verletzt. Das darf nicht sein: Rechenfehler."
    any_ok = sum(r["ok"]["any"] for r in rows)
    return "success", (
        f"In allen {zahl(runs)} Läufen liefert das Verfahren mit der Knotenzahl-Regel für **jede** Elementzahl die billigste gemeinsame Menge (ohne die Regel: {zahl(any_ok)} von {zahl(runs)}). "
        f"Die Kosten sind je Elementzahl bei allen {zahl(convex_checked)} geprüften Paaren **konvex**, und bei allen {zahl(sets)} gemeinsamen Mengen der Paare bis 4 Elemente gilt: "
        f"extrem genau dann, wenn kein Kreis negativer Länge da ist."
    )


# --- Spielwiese ------------------------------------------------------------------------------------------------------------------------------


def play_view(settings: Settings, mask: int) -> dict:
    p = pair_of(settings)
    out = {"mask": mask, "ok1": bool(p.ok1[mask]), "ok2": bool(p.ok2[mask]), "chain": None, "cost": None, "best": None}
    if out["ok1"] and out["ok2"]:
        out["cost"] = total_cost(p, mask)
        out["best"] = best_by_size(p)[popcount(mask)]
        out["chain"] = improve_to_extreme(p, mask)
    return out


def verdict_play(a: Analysis, view: dict) -> tuple[str, str]:
    if not view["ok1"] or not view["ok2"]:
        which = "beiden Matroiden" if not view["ok1"] and not view["ok2"] else ("M1" if not view["ok1"] else "M2")
        return "info", f"Die Menge ist in {which} nicht unabhängig, also keine gemeinsame unabhängige Menge. Wählen Sie eine Menge, die in beiden passt."
    size = popcount(view["mask"])
    head = f"I hat {elemente(size)} und kostet {zahl(view['cost'])} (das Minimum bei {size} Elementen: {zahl(view['best'])}). "
    if not view["chain"]:
        return "success", head + "Der Austauschgraph hat **keinen** Kreis negativer Länge: I ist unter allen gemeinsamen Mengen dieser Größe die billigste."
    first = view["chain"][0]
    final = view["chain"][-1]["cost"]
    return "warning", head + (
        f"Es gibt einen Kreis negativer Länge ({elemente(len(first['cycle']))}: {seq(a, first['cycle'])} → {a.labels[first['cycle'][0]]}; Länge {zahl(first['length'])}). "
        f"Nach {len(view['chain'])} Tauschkreis(en) sind die Kosten bei {zahl(final)}, dem Minimum."
    )


# --- Stand der Forschung (Literaturübersicht, nicht nachgebaut) ---------------------------------------------------------------------------------


RESEARCH_EXACT = (
    {"Jahr": "1981", "Arbeit": "Frank: Gewichtsaufspaltung", "Ergebnis": "Eine gemeinsame Menge ist optimal genau dann, wenn sich das Gewicht in zwei Gewichte aufspalten lässt, für die sie in M1 bzw. M2 optimal ist; Verfahren mit O(n r²) Orakelaufrufen (laut Zusammenfassung)", "Orakel": "Unabhängigkeit"},
    {"Jahr": "1986", "Arbeit": "Brezovec, Cornuéjols, Glover: zwei Verfahren", "Ergebnis": "Eines verlangt ganzzahlige Gewichte; eines mit Zeit O(n r (r + c + log n)) (laut Zusammenfassung)", "Orakel": "Unabhängigkeit"},
    {"Jahr": "2016", "Arbeit": "Huang, Kakimura, Kamiyama (SODA)", "Ergebnis": "Zurückführung auf W ungewichtete Schnitte (W = größtes Gewicht): exakt in O(√W n r^1,5)-Zeit (in einer Liste O(W n r^1,5)), (1 − ε)-Näherung in O(ε⁻¹ n r^1,5 log r)", "Orakel": "Unabhängigkeit"},
    {"Jahr": "2022", "Arbeit": "Tu (ISAAC): unterquadratisch", "Ergebnis": "Deterministisch exakt mit Õ(n r^{3/4} log W) Anfragen", "Orakel": "Rang"},
)
RESEARCH_OTHER = (
    {"Jahr": "1975, 1986", "Arbeit": "Lawler; Cunningham: ungewichtet", "Ergebnis": "Verbesserungswege im Austauschgraphen; Cunningham: kürzere Wege, O(n r^1,5) Aufrufe (Stück 7)", "Orakel": "Unabhängigkeit"},
    {"Jahr": "2021 bis 2023", "Arbeit": "Blikstad u. a.: ungewichtet unterquadratisch", "Ergebnis": "STOC 2021: randomisiert Õ(n^{6/5} r^{3/5}); STOC 2023 (Blikstad, Mukhopadhyay, Nanongkai, Tu): Õ(n√r) mit dynamischem Rangorakel", "Orakel": "Unabhängigkeit, Rang"},
    {"Jahr": "2025", "Arbeit": "Terao (WADS; arXiv 2410.18820): Näherung", "Ergebnis": "Deterministische (2/3 − ε)-Näherung mit O(n/ε + r log r) Unabhängigkeitsanfragen, ungewichtet", "Orakel": "Unabhängigkeit"},
    {"Jahr": "2026", "Arbeit": "Dudeja, Grilnberger (arXiv 2602.15702): gewichtet auf ungewichtet", "Ergebnis": "Aus einer α-Näherung für den ungewichteten Schnitt wird eine α(1 − ε)-Näherung für den gewichteten, Faktor log W", "Orakel": "Unabhängigkeit"},
)
RESEARCH_SOURCES = (
    ("Exact and approximation algorithms for weighted matroid intersection (Chalmers)", "https://research.chalmers.se/en/publication/239227"),
    ("Subquadratic Weighted Matroid Intersection Under Rank Oracles (arXiv 2212.00508)", "https://arxiv.org/abs/2212.00508"),
    ("Terao, arXiv 2410.18820", "https://arxiv.org/abs/2410.18820v1"),
    ("Dudeja, Grilnberger, arXiv 2602.15702", "https://arxiv.org/html/2602.15702v1"),
    ("Matroid intersection (Wikipedia)", "https://en.wikipedia.org/wiki/Matroid_intersection"),
)
