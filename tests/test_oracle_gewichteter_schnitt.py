"""Orakel (ORACLE-PLAYBOOK §5): anderer Rechenweg als der der Demo.

1. Kleinste Kosten je Elementzahl: Zuordnung gegen die Ungarische Methode (scipy), Arboreszenz gegen Chu-Liu/Edmonds (networkx), Regenbogen gegen eine Aufzählung mit networkx-Wald und Farben.
2. Kürzester Weg: Länge und Knotenzahl gegen networkx (Bellman–Ford, alle einfachen Wege) auf dem explizit aus Mengenoperationen gebauten Austauschgraphen.
3. Zertifikat: „extrem gleich kein negativer Kreis“ gegen eine Aufzählung der gemeinsamen Mengen; der Tauschkreis ist ein Kreis, hat negative Länge und senkt die Kosten.
4. Konvexität der Kosten je Elementzahl gegen die Aufzählung.
5. Literatur: Matroide 2, 5, 16, 68, 406."""

import itertools
import random

import numpy as np
import pytest

import gwi_algorithm as A
import gwi_constants as C
import gwi_systems as S

nx = pytest.importorskip("networkx")
scipy_opt = pytest.importorskip("scipy.optimize")


def _forest(v, edges, mask):
    g = nx.MultiGraph()
    g.add_nodes_from(range(v))
    g.add_edges_from(edges[e] for e in range(len(edges)) if mask >> e & 1)
    return nx.is_forest(g)


def _best_by_enumeration(pair, member1, member2):
    best = {}
    for mask in range(1 << pair.m):
        if member1(mask) and member2(mask):
            k = bin(mask).count("1")
            c = sum(pair.costs[e] for e in range(pair.m) if mask >> e & 1)
            best[k] = min(best.get(k, c), c)
    return best


def test_regenbogen_costs_per_size_equal_the_enumeration_with_networkx_forests():
    for n, seed, k in ((6, 0, 5), (6, 3, 3), (7, 8, 6), (7, 2, 4)):
        p = S.get_pair("regenbogen", n, seed, k)
        edges = [(u, w) for u, w, _ in p.inst.edges]
        best = _best_by_enumeration(p, lambda mask: _forest(n, edges, mask), lambda mask: len({p.colors[e] for e in range(p.m) if mask >> e & 1}) == bin(mask).count("1"))
        rounds = A.weighted_steps(p)
        assert [r["cost"] for r in rounds] == [best[i] for i in range(p.opt + 1)] and all(p.common[r["set"]] for r in rounds), (n, seed, k)


def test_zuordnung_equals_the_hungarian_method_of_scipy():
    for n in (6, 7, 8):
        for seed in range(20):
            p = S.get_pair("zuordnung", n, seed, 0)
            edges = [(u, w) for u, w, _ in p.inst.edges]
            rounds = A.weighted_steps(p)
            big = 10 ** 6
            mat = np.full((n, n), 10 ** 9, dtype=np.int64)
            for (u, w), c in zip(edges, p.costs):
                mat[u, w] = min(mat[u, w], c - big)               # je Paar die billigste Leitung; Abzug macht jede zusätzliche Zuordnung billiger
            r, cidx = scipy_opt.linear_sum_assignment(mat)
            chosen = [(a, b) for a, b in zip(r, cidx) if mat[a, b] < 10 ** 8]
            assert len(chosen) == p.opt == len(rounds) - 1 and int(sum(mat[a, b] + big for a, b in chosen)) == rounds[-1]["cost"], (n, seed)


def test_arboreszenz_equals_chu_liu_edmonds_of_networkx():
    rng = random.Random(1)
    p0 = S.get_pair("arboreszenz", 6, 8, 6)
    for _ in range(30):
        costs = tuple(rng.randint(1, 9) for _ in C.ARBORESCENCE_ARCS)
        p = A.Pair("a", p0.m, p0.ok1, p0.ok2, p0.labels, p0.kind, costs=costs)
        rounds = A.weighted_steps(p)
        g = nx.DiGraph()
        for (a, b), c in zip(C.ARBORESCENCE_ARCS, costs):
            if b != 0 and (not g.has_edge(a, b) or g[a][b]["weight"] > c):
                g.add_edge(a, b, weight=c)
        arb = nx.minimum_spanning_arborescence(g)
        assert len(rounds) - 1 == 5 == arb.number_of_edges() and rounds[-1]["cost"] == sum(d["weight"] for _, _, d in arb.edges(data=True))


def _explicit(pair, cur):
    ins = {e for e in range(pair.m) if cur >> e & 1}
    outs = set(range(pair.m)) - ins
    arcs = []
    for y in ins:
        for x in outs:
            swapped = (cur - (1 << y)) | (1 << x)
            if pair.ok1[swapped]:
                arcs.append((y, x))
            if pair.ok2[swapped]:
                arcs.append((x, y))
    x1 = [x for x in outs if pair.ok1[cur | 1 << x]]
    x2 = [x for x in outs if pair.ok2[cur | 1 << x]]
    return x1, x2, arcs


def test_shortest_path_length_and_hops_agree_with_networkx_on_the_explicit_exchange_graph():
    rng = random.Random(2)
    for key, n, seed, k in (("regenbogen", 6, 1, 5), ("zuordnung", 6, 2, 0), ("arboreszenz", 6, 8, 6)):
        p = S.get_pair(key, n, seed, k)
        commons = np.nonzero(p.common)[0].tolist()
        for cur in rng.sample(commons, min(40, len(commons))):
            if not A.is_extreme(p, cur):
                continue                                                                   # der Weg ist nur zu extremen Mengen erklärt (kein negativer Kreis)
            x1, x2, arcs = _explicit(p, cur)
            l = A.node_lengths(p, cur)
            d = nx.DiGraph()
            d.add_nodes_from(range(p.m))
            for a, b in arcs:
                d.add_edge(a, b, weight=l[b])
            d.add_node("S")
            for x in x1:
                d.add_edge("S", x, weight=l[x])
            candidates = []
            for x in x2:
                if nx.has_path(d, "S", x):
                    for path in nx.all_simple_paths(d, "S", x):
                        candidates.append((sum(l[v] for v in path[1:]), len(path) - 1))
            sp = A.shortest_path(p, cur)
            if candidates:
                assert sp["path"] is not None and (sp["length"], len(sp["path"])) == min(candidates)
            else:
                assert sp["path"] is None


def _brute_best(pair, cur):
    k = bin(cur).count("1")
    return A.best_by_size(pair)[k]


def test_extreme_equals_no_negative_cycle_on_all_common_sets_of_all_pairs_up_to_three_elements():
    rng = random.Random(3)
    total = 0
    for n in range(2, 4):
        mats = A.small_matroids(n)
        for (ok1, ur1), (ok2, ur2) in itertools.product(mats, mats):
            p = A.Pair("k", n, ok1, ok2, tuple(str(i) for i in range(n)), "kanten", costs=tuple(rng.randint(-1, 3) for _ in range(n)))
            p.__dict__["ur1"], p.__dict__["ur2"] = ur1, ur2
            best = A.best_by_size(p)
            for s in np.nonzero(p.common)[0].tolist():
                extreme = A.total_cost(p, s) == best[bin(s).count("1")]
                assert extreme == A.is_extreme(p, s)
                total += 1
    assert total == 44 + 695


def test_the_negative_cycle_is_a_cycle_of_the_explicit_graph_with_negative_length_and_improves_the_cost():
    rng = random.Random(4)
    p = S.get_pair("regenbogen", 6, 1, 5)
    commons = np.nonzero(p.common)[0].tolist()
    seen = 0
    for cur in rng.sample(commons, 60):
        cycle = A.find_negative_cycle(p, cur)
        if cycle is None:
            continue
        seen += 1
        _, _, arcs = _explicit(p, cur)
        pairs = list(zip(cycle, cycle[1:] + cycle[:1]))
        assert all(pr in set(arcs) for pr in pairs) and len(set(cycle)) == len(cycle)
        assert sum(A.node_lengths(p, cur)[v] for v in cycle) < 0
        after = cur ^ sum(1 << v for v in cycle)
        assert p.common[after] and bin(after).count("1") == bin(cur).count("1") and A.total_cost(p, after) < A.total_cost(p, cur)
        assert A.total_cost(p, after) - A.total_cost(p, cur) == sum(A.node_lengths(p, cur)[v] for v in cycle)
    assert seen > 10


def test_costs_per_size_are_convex_by_enumeration():
    rng = random.Random(5)
    for n in range(2, 5):
        mats = A.small_matroids(n)
        pool = list(itertools.product(mats, mats))
        for (ok1, ur1), (ok2, ur2) in rng.sample(pool, min(400, len(pool))):
            p = A.Pair("k", n, ok1, ok2, tuple(str(i) for i in range(n)), "kanten", costs=tuple(rng.randint(-2, 4) for _ in range(n)))
            p.__dict__["ur1"], p.__dict__["ur2"] = ur1, ur2
            best = A.best_by_size(p)
            vals = [best[k] for k in range(p.opt + 1)]
            diffs = [b - a for a, b in zip(vals, vals[1:])]
            assert all(d2 >= d1 for d1, d2 in zip(diffs, diffs[1:]))


def test_matroid_counts_up_to_five_elements():
    assert [len(A.small_matroids(n)) for n in range(1, 6)] == [2, 5, 16, 68, 406]
