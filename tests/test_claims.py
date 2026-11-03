"""Jede Zahl der README („Befunde“) wird hier mit den Funktionen der App nachgerechnet (DEMO-PLAYBOOK §4)."""

import re
from pathlib import Path

import gwi_algorithm as A
import gwi_evaluation as ev

README = (Path(__file__).resolve().parent.parent / "README.md").read_text(encoding="utf-8")

EXAMPLES = {  # Name in der README -> (Einstellungen, größte Elementzahl, Kurve, Zuwächse, Greedy: Elementzahl, Kosten)
    "Regenbogen-Spannbaum mit 6 Farben": (ev.Settings(7, 8, "regenbogen", 6), 5, (0, 4, 17, 42, 77, 151), [4, 13, 25, 35, 74], 4, 77),
    "Regenbogen mit 3 Farben": (ev.Settings(7, 8, "regenbogen", 3), 3, (0, 4, 29, 67), [4, 25, 38], 3, 67),
    "Zuordnung": (ev.Settings(7, 8, "zuordnung", 6), 5, (0, 4, 29, 55, 96, 170), [4, 25, 26, 41, 74], 4, 109),
    "Arboreszenz (fest)": (ev.Settings(6, 8, "arboreszenz", 6), 5, (0, 1, 2, 5, 10, 16), [1, 1, 3, 5, 6], 5, 16),
}


def test_the_four_examples_on_the_plan():
    for name, (s, opt, curve, deltas, gk, gcost) in EXAMPLES.items():
        a = ev.analyse(s)
        assert (a.opt, a.curve, ev.increments(a.curve)) == (opt, curve, deltas) and ev.is_convex(a.curve), name
        assert [r["cost"] for r in ev.steps_view(s)] == list(curve), name
        g = ev.greedy_view(s)
        assert (g["k"], g["cost"]) == (gk, gcost), name
        line = [l for l in README.splitlines() if l.startswith("| " + name + " |")]
        assert line and f"| {opt} | {', '.join(str(c) for c in curve)} | {', '.join(str(d) for d in deltas)} |" in line[0], name
    assert EXAMPLES["Zuordnung"][5] - ev.greedy_view(EXAMPLES["Zuordnung"][0])["best_at_k"] == 13 and ev.greedy_view(EXAMPLES["Zuordnung"][0])["best_at_k"] == 96


def test_all_small_pairs_and_runs():
    rows = ev.small_rows()
    assert [r["runs"] for r in rows] == [50, 512, 9248, 6000] and sum(r["runs"] for r in rows) == 15810
    assert [r["ok"]["hops"] for r in rows] == [50, 512, 9248, 6000]
    assert [r["ok"]["any"] for r in rows] == [50, 512, 9232, 5969] and sum(r["ok"]["any"] for r in rows) == 15763 and sum(r["ok"]["rev"] for r in rows) == 15764
    assert 9248 - rows[2]["ok"]["any"] == 16 == 9248 - rows[2]["ok"]["rev"] and 6000 - rows[3]["ok"]["any"] == 31 and 6000 - rows[3]["ok"]["rev"] == 30
    assert sum(r["convex"] for r in rows) == sum(r["convex_checked"] for r in rows) == 7905
    assert [r["common_sets"] for r in rows[:3]] == [44, 695, 21165] and sum(r["extreme_agree"] for r in rows) == sum(r["common_sets"] for r in rows) == 21904 and not rows[3]["extreme_checked"]


def test_tie_example_and_tie_series():
    tv = ev.tie_view()
    assert [r["cost"] for r in tv["runs"]["hops"]["rounds"]] == [0, 0, 0, 2] and all(tv["runs"]["hops"]["valid"])
    assert tv["runs"]["any"]["reached"] == 2 and tv["runs"]["any"]["valid"] == [True, True, False] and tv["runs"]["rev"]["reached"] == 2
    assert int(A.tie_pair().common.sum()) == 10
    res = ev.tie_series()
    assert res["pairs"] == 6000 and res["fail"] == {"hops": 0, "any": 48, "rev": 51} and res["invalid"] == res["fail"]
    assert ev.prozent(48 / 6000) == "0,8" and ev.prozent(51 / 6000) == "0,9"


def test_greedy_on_the_plans():
    expected = {
        "regenbogen": [(7, 1, 13), (9, 0, 11), (9, 2, 11)],
        "zuordnung": [(11, 2, 9), (10, 2, 10), (15, 1, 5)],
        "arboreszenz": [(4, 2, 26)],
    }
    for system, rows in expected.items():
        got = ev.greedy_series(system)
        assert [(r["stuck"], r["costlier"], r["reach"]) for r in got] == rows, system
    assert sum(r["stuck"] for r in ev.greedy_series("regenbogen")) + sum(r["stuck"] for r in ev.greedy_series("zuordnung")) == 7 + 9 + 9 + 11 + 10 + 15


def test_the_tauschkreis_of_the_standard_case():
    s = ev.Settings(7, 8, "regenbogen", 6)
    a = ev.analyse(s)
    cv = ev.cert_view(s, ev.steps_view(s), 2)
    assert ev.total_cost_of(a, cv["worst"]) == 95 and a.curve[2] == 17 and cv["chain"][0]["length"] == -44 and len(cv["chain"][0]["cycle"]) == 2 and len(cv["chain"]) == 3 and cv["chain"][-1]["cost"] == 17


def test_readme_names_every_checked_number():
    for needle in ("**15 810**", "**15 763**", "**15 764**", "**7 905**", "**21 904 von 21 904**", "(44, 695, 21 165)", "16 von 9 248 Läufen", "31 (Erzeugungsreihenfolge) bzw. 30 (umgekehrt) von 6 000", "48 und 51", "rund 0,8 %",
                   "**48**", "**51**", "**7, 9, 9**", "1 von 13, 0 von 11, 2 von 11", "**11, 10, 15**", "2 von 9, 2 von 10, 1 von 5", "2 von 26", "**60 von 60**", "**30 von 30**", "Länge −44", "nach 3 Tauschkreisen", "Kosten 2, 2, 0, 0, 0",
                   "kleinste Zahl gemeinsamer Mengen: 10", "bei 4 Elementen wären 96 möglich", "gwi_"):
        assert needle in README, needle


def test_readme_tables_have_no_decimal_points():
    table = README.split("## Befunde (gemessen, keine Behauptungen)")[1].split("## Ehrliche Grenzen")[0]
    assert not re.search(r"\d\.\d", table)
