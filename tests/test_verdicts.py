"""Verdikte (reine Funktionen in gwi_evaluation.py) an handgesetzten Werten: jeder Zweig, jede Zahl im Text (DEMO-PLAYBOOK §4)."""

import gwi_algorithm as A
import gwi_evaluation as ev


def _setup(system="regenbogen", k=6, n=7, seed=8):
    s = ev.Settings(n, seed, system, k)
    return s, ev.analyse(s), ev.steps_view(s)


# --- Hauptansicht ------------------------------------------------------------------------------------------------------------------------


def test_step_verdict_for_a_one_element_path_and_for_a_three_element_path():
    s, a, rounds = _setup()
    kind, text = ev.verdict_step(a, rounds, 2)
    assert kind == "success" and "I_2 = {A–F, A–G} kostet **17**" in text and "Der kürzeste Weg von I_1 hat 1 Element: A–F; seine Länge ist **13**." in text
    assert "Die Kosten wachsen also um 13 (vorher 4)" in text and "ebenfalls 17" in text
    kind, text = ev.verdict_step(a, rounds, 5)
    assert "hat 3 Elemente" in text and " = **" in text and "Die Kosten wachsen also um 74 (vorher 35)" in text
    z, za, zr = _setup("zuordnung")
    assert "hat 3 Elemente" in ev.verdict_step(za, zr, 3)[1]


def test_step_verdict_shows_negative_parts_with_a_minus_sign():
    s, a, rounds = _setup("zuordnung")
    text = ev.verdict_step(a, rounds, 3)[1]
    assert "−" in text and " − " in text.split("seine Länge ist")[1].split("**")[0]


def test_step_verdict_error_branch():
    s, a, rounds = _setup()
    broken = list(rounds)
    broken[2] = {**rounds[2], "cost": rounds[2]["cost"] + 1}
    assert ev.verdict_step(a, broken, 2)[0] == "error"


def test_curve_verdicts():
    s, a, rounds = _setup()
    kind, text = ev.verdict_curve(a, rounds)
    assert kind == "success" and "**konvex**" in text and "Zuwächse 4, 13, 25, 35, 74" in text and "Alle 5 Schritte" in text
    assert ev.verdict_curve(a, rounds[:-1])[0] == "error"
    nc = ev.Analysis(a.settings, a.m, a.labels, a.kind, a.costs, 4, (0, 4, 5, 20, 21), a.n_common)
    kind, text = ev.verdict_curve(nc, [{"cost": c} for c in nc.curve])
    assert kind == "warning" and "nicht konvex" in text


def test_curve_data():
    s, a, rounds = _setup()
    d = ev.curve_data(a)
    assert d == {"ks": [0, 1, 2, 3, 4, 5], "costs": [0, 4, 17, 42, 77, 151], "deltas": [4, 13, 25, 35, 74]}


def test_round_rows_and_groups():
    s, a, rounds = _setup()
    rows = ev.round_rows(a, rounds, 2)
    assert len(rows) == 12 and sum(r["in I_{k−1}"] == "ja" for r in rows) == 1 and {r["im Weg"] for r in rows} == {"–", "1"}
    groups = ev.round_groups(a, rounds, 2)
    assert [g[0] for g in groups] == ["I_k (billigste Menge mit k Elementen)", "Weg von I_{k−1} nach I_k"] and ev.edge_costs(a, groups)[groups[1][1][0]] == str(a.costs[groups[1][1][0]])


# --- Experiment 1 ----------------------------------------------------------------------------------------------------------------------


def _g(k, cost, best_at_k, opt, best_cost):
    return {"set": 3, "k": k, "cost": cost, "best_at_k": best_at_k, "opt": opt, "best_cost": best_cost, "stuck": k < opt, "costlier": cost > best_at_k}


def test_greedy_verdict_branches():
    _, a, _ = _setup()
    kind, text = ev.verdict_greedy(a, _g(4, 77, 77, 5, 151))
    assert kind == "warning" and "**bleibt stecken**" in text and "Das Optimum hat 5 Elemente (kleinste Kosten 151)" in text and "Greedy zahlt dort nicht mehr" in text
    kind, text = ev.verdict_greedy(a, _g(4, 109, 96, 5, 170))
    assert "Greedy zahlt 13 mehr" in text
    kind, text = ev.verdict_greedy(a, _g(5, 160, 151, 5, 151))
    assert kind == "warning" and "**teurer**" in text and "9 mehr (6,0 %)" in text
    kind, text = ev.verdict_greedy(a, _g(5, 151, 151, 5, 151))
    assert kind == "success" and "kleinsten Kosten" in text


def test_greedy_series_table_and_verdict():
    rows = ({"n": 6, "plans": 20, "stuck": 7, "costlier": 1, "reach": 13, "excess": 0.005}, {"n": 8, "plans": 20, "stuck": 9, "costlier": 2, "reach": 11, "excess": 0.017})
    table = ev.greedy_series_table("regenbogen", rows)
    assert table[0] == {"Standorte": 6, "Pläne": 20, "Greedy bleibt vor der größten Elementzahl stecken": 7, "bei gleicher Größe teurer": "1 von 13", "mittlerer Aufschlag dort": "0,5 %"}
    kind, text = ev.verdict_greedy_series("regenbogen", rows)
    assert kind == "info" and "Von 40 Beispielen bleibt Greedy nach Kosten bei **16** vor der größten Elementzahl stecken" in text and "von den 24, die sie erreichen, ist es bei **3** teurer" in text
    arb = ev.greedy_series_table("arboreszenz", ({"n": 0, "plans": 30, "stuck": 4, "costlier": 2, "reach": 26, "excess": 0.013},))
    assert arb[0]["Kostenvektoren"] == 30


# --- Experiment 2 ----------------------------------------------------------------------------------------------------------------------


def test_cert_verdict_rows_and_error_branches():
    s, a, rounds = _setup()
    cv = ev.cert_view(s, rounds, 2)
    kind, text = ev.verdict_cert(a, cv)
    assert kind == "success" and "Die billigste Menge mit 2 Elementen (Kosten 17) hat **keinen** Kreis negativer Länge" in text and "(95)" in text and "nach 3 Tauschkreis(en)" in text and "bei 17" in text
    rows = ev.chain_rows(a, cv)
    assert rows[0]["Schritt"] == 0 and rows[0]["Kosten"] == "95" and rows[-1]["Kosten"] == "17" and rows[1]["Länge des Kreises"] == "−44"
    assert ev.verdict_cert(a, {**cv, "best_extreme": False})[0] == "error"
    assert ev.verdict_cert(a, {**cv, "final": cv["worst"], "chain": []})[0] == "error"
    cr = ev.cert_rows(a, rounds)
    assert len(cr) == 6 and cr[1] == {"k": 1, "Kosten von I_k": "4", "Relaxierungsrunden (Bellman–Ford)": 2, "Verbesserungen": 3, "Kreis negativer Länge": "nein"}


def test_cert_verdict_without_a_chain_when_all_sets_of_that_size_cost_the_same():
    s, a, rounds = _setup("regenbogen", 3)
    cv = ev.cert_view(s, rounds, 1)
    assert cv["chain"] and ev.verdict_cert(a, cv)[0] == "success"


# --- Experiment 3 ----------------------------------------------------------------------------------------------------------------------


def test_tie_verdicts_and_rows():
    tv = ev.tie_view()
    kind, text = ev.verdict_tie(tv)
    assert kind == "warning" and "führt der Lauf bis zur Elementzahl 3" in text and "I_2 ist **nicht mehr in beiden Matroiden unabhängig**" in text and "Elementzahl 2 statt 3" in text
    rows = ev.tie_rows(tv)
    assert [r["erreichte Elementzahl"] for r in rows] == [3, 2, 2] and [r["alle gemeinsam unabhängig"] for r in rows] == ["ja", "nein", "nein"]
    assert rows[0]["Mengen I_0, I_1, …"] == "∅ ; {c} ; {c, e} ; {b, c, e}"
    assert rows[1]["Mengen I_0, I_1, …"] == "∅ ; {c} ; {d, e}"
    ok_all = {**tv, "runs": {v: tv["runs"]["hops"] for v in ev.TIEBREAKS}}
    assert ev.verdict_tie(ok_all)[0] == "info"
    broken = {**tv, "runs": {**tv["runs"], "hops": tv["runs"]["any"]}}
    assert ev.verdict_tie(broken)[0] == "error"


def test_tie_series_verdict():
    kind, text = ev.verdict_tie_series({"pairs": 6000, "fail": {"hops": 0, "any": 48, "rev": 51}, "invalid": {"hops": 0, "any": 48, "rev": 51}})
    assert kind == "info" and "Bei 6 000 Zufallspaaren" in text and "**0**" in text and "**48**" in text and "**51**" in text and "0,8 % und 0,9 %" in text
    assert ev.verdict_tie_series({"pairs": 10, "fail": {"hops": 1, "any": 1, "rev": 1}, "invalid": {}})[0] == "error"


# --- Experiment 4 ----------------------------------------------------------------------------------------------------------------------


def test_small_verdict_and_table_and_the_error_branches():
    rows = tuple(A.small_weighted_row(n, 10 ** 9, 1) for n in (2, 3))
    kind, text = ev.verdict_small(rows)
    assert kind == "success" and "In allen 562 Läufen" in text and "(ohne die Regel: 562 von 562)" in text and "bei allen 281 geprüften Paaren **konvex**" in text and "bei allen 739 gemeinsamen Mengen" in text
    table = ev.small_table(rows)
    assert table[1]["Läufe (zwei Kostenvektoren je Paar)"] == "512" and table[1]["gemeinsame Mengen: extrem gleich kein negativer Kreis"] == "695 von 695"
    five = ev.small_table((A.small_weighted_row(2, 10, 1),))
    assert five[0]["richtig nur nach Länge"] == "20 und 20"
    assert ev.verdict_small(tuple({**r, "ok": {**r["ok"], "hops": r["ok"]["hops"] - 1}} if r["n"] == 3 else r for r in rows))[0] == "error"
    assert ev.verdict_small(tuple({**r, "convex": r["convex"] - 1} if r["n"] == 3 else r for r in rows))[0] == "error"
    assert ev.verdict_small(tuple({**r, "extreme_agree": r["extreme_agree"] - 1} if r["n"] == 3 else r for r in rows))[0] == "error"
    no_check = ev.small_table(({**rows[0], "extreme_checked": False},))
    assert no_check[0]["gemeinsame Mengen: extrem gleich kein negativer Kreis"] == "nicht geprüft"


# --- Spielwiese ------------------------------------------------------------------------------------------------------------------------


def test_play_verdicts():
    s, a, rounds = _setup()
    worst = A.worst_of_size(ev.pair_of(s), 2)
    kind, text = ev.verdict_play(a, ev.play_view(s, worst))
    assert kind == "warning" and "I hat 2 Elemente und kostet 95 (das Minimum bei 2 Elementen: 17)" in text and "Kreis negativer Länge (2 Elemente: A–G → A–B → A–G; Länge −44)" in text and "Nach 3 Tauschkreis(en) sind die Kosten bei 17" in text
    kind, text = ev.verdict_play(a, ev.play_view(s, rounds[2]["set"]))
    assert kind == "success" and "**keinen** Kreis negativer Länge" in text
    kind, text = ev.verdict_play(a, {"ok1": False, "ok2": True, "mask": 1})
    assert kind == "info" and "in M1 nicht unabhängig" in text


def test_research_tables_are_complete():
    assert len(ev.RESEARCH_EXACT) == 4 and len(ev.RESEARCH_OTHER) == 4 and all({"Jahr", "Arbeit", "Ergebnis", "Orakel"} <= set(r) for r in ev.RESEARCH_EXACT + ev.RESEARCH_OTHER)
    assert all(url.startswith("https://") for _, url in ev.RESEARCH_SOURCES) and len(ev.RESEARCH_SOURCES) == 5


def test_number_helpers():
    assert ev.de(1.5, 1) == "1,5" and ev.prozent(0.625) == "62,5" and ev.zahl(1234567) == "1 234 567" and ev.elemente(1) == "1 Element" and ev.elemente(3) == "3 Elemente"
