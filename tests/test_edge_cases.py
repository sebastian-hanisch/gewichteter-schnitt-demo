"""Randfälle (DEMO-PLAYBOOK §4): kleinste Paare, gleiche und negative Kosten, Nullmatroid, Reglergrenzen, Spielwiese."""

import numpy as np

import gwi_algorithm as A
import gwi_constants as C
import gwi_evaluation as ev
import gwi_systems as S
from gwi_algorithm import Pair


def _pair(m, ok1, ok2, costs):
    return Pair("x", m, np.array(ok1, dtype=bool), np.array(ok2, dtype=bool), tuple(str(i) for i in range(m)), "kanten", costs=tuple(costs))


def test_single_element_pair():
    p = _pair(1, [True, True], [True, True], (5,))
    rounds = A.weighted_steps(p)
    assert [r["cost"] for r in rounds] == [0, 5] and rounds[0]["path"] == [0] and rounds[1]["path"] is None
    q = _pair(1, [True, True], [True, False], (5,))                     # M2: Schleife
    assert [r["cost"] for r in A.weighted_steps(q)] == [0] and q.opt == 0


def test_the_zero_matroid_gives_only_the_empty_set():
    p = _pair(3, [True] * 8, [mask == 0 for mask in range(8)], (1, 2, 3))
    rounds = A.weighted_steps(p)
    assert len(rounds) == 1 and rounds[0]["set"] == 0 and rounds[0]["path"] is None and A.best_by_size(p) == {0: 0}


def test_all_costs_equal_give_costs_k_times_c_and_ties_everywhere(weg):
    p = _pair(3, weg.ok1, weg.ok2, (2, 2, 2))
    rounds = A.weighted_steps(p)
    assert [r["cost"] for r in rounds] == [0, 2, 4] and all(p.common[r["set"]] for r in rounds)


def test_zero_and_negative_costs_work(weg):
    p = _pair(3, weg.ok1, weg.ok2, (0, 0, 0))
    assert [r["cost"] for r in A.weighted_steps(p)] == [0, 0, 0]
    q = _pair(3, weg.ok1, weg.ok2, (-3, -1, -3))
    rounds = A.weighted_steps(q)
    assert [r["cost"] for r in rounds] == [0, -3, -6] and A.run_is_correct(q, rounds, A.best_by_size(q)) and not any(r["neg"] for r in rounds)


def test_negative_cycle_detection_in_bellman_ford_flags_a_non_extreme_start():
    p = _pair(3, [True] * 8, [True] * 8, (1, 1, 1))
    sp = A.shortest_path(p, 0)
    assert sp["path"] == [0] and not sp["neg"]
    q = _pair(3, [True] * 8, [True] * 8, (3, 1, 3))
    sp = A.shortest_path(q, 1)                                          # I = {a} kostet 3, {b} kostet 1: Kreis negativer Länge im Austauschgraphen
    assert sp["neg"] and sp["path"] is None


def test_every_example_at_the_slider_limits_builds_and_matches_the_enumeration():
    for key in C.SYSTEMS:
        for n in (C.N_MIN, C.N_MAX):
            for k in (C.K_MIN, C.K_MAX):
                if key != "regenbogen" and k != C.K_MIN:
                    continue
                s = ev.Settings(n, C.DEFAULT_SEED, key, k)
                a = ev.analyse(s)
                rounds = ev.steps_view(s)
                assert [r["cost"] for r in rounds] == list(a.curve) and len(rounds) == a.opt + 1, (key, n, k)


def test_regenbogen_with_two_colors_has_only_two_steps():
    a = ev.analyse(ev.Settings(7, 8, "regenbogen", 2))
    assert a.opt == 2 and len(a.curve) == 3


def test_greedy_view_flags_for_the_examples():
    g = ev.greedy_view(ev.Settings(7, 8, "regenbogen", 6))
    assert (g["k"], g["cost"], g["best_at_k"], g["stuck"], g["costlier"]) == (4, 77, 77, True, False)
    z = ev.greedy_view(ev.Settings(7, 8, "zuordnung", 6))
    assert (z["k"], z["cost"], z["best_at_k"], z["stuck"], z["costlier"]) == (4, 109, 96, True, True)
    r = ev.greedy_view(ev.Settings(6, 8, "arboreszenz", 6))
    assert (r["k"], r["cost"], r["best_at_k"], r["stuck"], r["costlier"]) == (5, 16, 16, False, False)


def test_play_view_branches():
    s = ev.Settings(7, 8, "regenbogen", 6)
    a, p = ev.analyse(s), ev.pair_of(s)
    bad1 = next(m for m in range(1 << p.m) if not p.ok1[m] and p.ok2[m])
    bad2 = next(m for m in range(1 << p.m) if p.ok1[m] and not p.ok2[m])
    both = next(m for m in range(1 << p.m) if not p.ok1[m] and not p.ok2[m])
    for mask, needle in ((bad1, "in M1 nicht unabhängig"), (bad2, "in M2 nicht unabhängig"), (both, "in beiden Matroiden nicht unabhängig")):
        kind, text = ev.verdict_play(a, ev.play_view(s, mask))
        assert kind == "info" and needle in text
    final = ev.steps_view(s)[2]["set"]
    kind, text = ev.verdict_play(a, ev.play_view(s, final))
    assert kind == "success" and "**keinen** Kreis negativer Länge" in text
    kind, text = ev.verdict_play(a, ev.play_view(s, 0))
    assert kind == "success" and "I hat 0 Elemente" in text


def test_set_formatting_helpers():
    a = ev.analyse(ev.Settings(6, 8, "arboreszenz", 6))
    assert ev.setstr(a, 0) == "∅" and ev.setstr(a, 3) == "{0→1, 0→2}" and ev.seq(a, [0, 2]) == "0→1 → 1→2"
    assert ev.zahl(-1234) == "−1 234" and ev.increments((0, 4, 17)) == [4, 13] and ev.is_convex((0, 4, 17, 42)) and not ev.is_convex((0, 4, 5, 20, 21))
