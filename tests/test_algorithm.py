"""Einheiten des Kerns an Mini-Instanzen von Hand (DEMO-PLAYBOOK §1b, §4)."""

import numpy as np

import gwi_algorithm as A
import gwi_constants as C
import gwi_systems as S


def test_node_lengths_and_costs(weg):
    assert A.node_lengths(weg, 0) == [3, 1, 3]
    assert A.node_lengths(weg, 2) == [3, -1, 3]                       # I = {b}: b innen, a und c außen
    assert A.total_cost(weg, 5) == 6 and A.total_cost(weg, 0) == 0
    assert A.cost_table(weg).tolist() == [0, 3, 1, 4, 3, 6, 4, 7]
    assert A.best_by_size(weg) == {0: 0, 1: 1, 2: 6}


def test_weighted_run_by_hand(weg):
    rounds = A.weighted_steps(weg)
    assert [r["set"] for r in rounds] == [0, 2, 5] and [r["cost"] for r in rounds] == [0, 1, 6] and [r["path"] for r in rounds] == [[1], [2, 1, 0], None]
    assert rounds[0]["length"] == 1 and rounds[1]["length"] == 5 and rounds[1]["dist"] == {2: 3, 1: 2, 0: 5} and rounds[1]["hops"] == {2: 1, 1: 2, 0: 3}
    assert rounds[1]["x1"] == [2] and rounds[1]["x2"] == [0] and rounds[1]["lengths"] == [3, -1, 3]
    assert not any(r["neg"] for r in rounds) and rounds[-1]["length"] is None


def test_the_cost_increments_by_hand_are_convex(weg):
    assert [A.total_cost(weg, r["set"]) for r in A.weighted_steps(weg)] == [0, 1, 6]
    diffs = [1, 5]
    assert diffs[1] >= diffs[0]


def test_negative_cycle_at_a_bad_set_and_its_improvement(weg):
    cycle = A.find_negative_cycle(weg, 1)                              # I = {a}: kostet 3, {b} kostet 1
    assert set(cycle) == {0, 1} and A.cycle_length(weg, 1, cycle) == -2
    steps = A.improve_to_extreme(weg, 1)
    assert len(steps) == 1 and steps[0]["after"] == 2 and steps[0]["cost"] == 1 and steps[0]["length"] == -2
    assert A.is_extreme(weg, 2) and not A.is_extreme(weg, 1) and A.is_extreme(weg, 5) and A.is_extreme(weg, 0)


def test_worst_set_and_greedy_by_cost(weg):
    assert A.worst_of_size(weg, 1) == 1 and A.worst_of_size(weg, 2) == 5                     # {a} und {c} kosten beide 3: die erste nach Maske
    g = A.greedy_by_cost(weg)
    assert g == 2 and A.popcount(g) == 1                                                       # b zuerst blockiert a und c: bleibt stecken (Optimum hat 2 Elemente)


def test_triangle_with_two_equal_colors_picks_the_cheaper_rainbow(dreieck_farben):
    p = dreieck_farben
    assert p.opt == 2 and A.best_by_size(p) == {0: 0, 1: 2, 2: 6}
    rounds = A.weighted_steps(p)
    assert [r["set"] for r in rounds][-1] == 6 and rounds[-1]["cost"] == 6                    # {b, c} kostet 2 + 4
    assert A.greedy_by_cost(p) == 6                                                           # billigste zuerst: b (2), c (4), a gleiche Farbe wie b: abgelehnt


def test_tie_example_three_path_choices(tie):
    assert tie.opt == 3 and int(tie.common.sum()) == 10 and A.best_by_size(tie) == {0: 0, 1: 0, 2: 0, 3: 2}
    hops = A.weighted_steps(tie, "hops")
    assert [r["set"] for r in hops] == [0, 4, 20, 22] and [r["cost"] for r in hops] == [0, 0, 0, 2] and all(tie.common[r["set"]] for r in hops)
    for variant in ("any", "rev"):
        bad = A.weighted_steps(tie, variant)
        assert [r["set"] for r in bad] == [0, 4, 24] and not tie.common[24] and len(bad) - 1 < tie.opt                        # {d, e} ist nicht gemeinsam unabhängig
    best = A.best_by_size(tie)
    assert A.run_is_correct(tie, hops, best) and not A.run_is_correct(tie, A.weighted_steps(tie, "any"), best)


def test_small_weighted_rows_for_two_and_three_elements():
    r2 = A.small_weighted_row(2, 10 ** 9, 1)
    assert (r2["pairs"], r2["runs"], r2["ok"], r2["convex"], r2["common_sets"], r2["extreme_agree"]) == (25, 50, {"hops": 50, "any": 50, "rev": 50}, 25, 44, 44)
    r3 = A.small_weighted_row(3, 10 ** 9, 1)
    assert (r3["pairs"], r3["runs"], r3["ok"]["hops"], r3["convex"], r3["common_sets"], r3["extreme_agree"]) == (256, 512, 512, 256, 695, 695)


def test_tie_search_is_reproducible_and_never_fails_with_the_node_rule():
    a, b = A.tie_search(200, 1), A.tie_search(200, 1)
    assert a == b and a["fail"]["hops"] == 0 and a["invalid"]["hops"] == 0 and a["fail"]["any"] == a["invalid"]["any"]


def test_arboreszenz_costs_come_from_the_seed_and_are_in_range():
    c1, c2 = S.arc_costs(8), S.arc_costs(9)
    assert S.arc_costs(8) == c1 and c1 != c2 and len(c1) == 12 and all(1 <= x <= C.ARB_COST_MAX for x in c1)
    p = S.get_pair("arboreszenz", 9, 8, 3)
    assert p is S.get_pair("arboreszenz", 6, 8, 7) and list(p.costs) == c1 and p.costs != S.get_pair("arboreszenz", 6, 9, 7).costs


def test_pair_costs_are_the_plan_edge_costs():
    p = S.get_pair("regenbogen", 7, 8, 6)
    assert list(p.costs) == [c for _, _, c in p.inst.edges] and p.costs[:3] == (48, 38, 44)
    z = S.get_pair("zuordnung", 7, 8, 1)
    assert z is S.get_pair("zuordnung", 7, 8, 5) and z.costs == p.costs


def test_cost_table_and_best_by_size_on_a_free_pair():
    ok = np.ones(8, dtype=bool)
    p = A.Pair("frei", 3, ok, ok.copy(), ("a", "b", "c"), "kanten", costs=(5, 1, 3))
    assert A.best_by_size(p) == {0: 0, 1: 1, 2: 4, 3: 9} and A.greedy_by_cost(p) == 7
    assert [r["cost"] for r in A.weighted_steps(p)] == [0, 1, 4, 9]
