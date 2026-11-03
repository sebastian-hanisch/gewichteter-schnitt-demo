"""Eigenschaftstests (Schicht „Eigenschaften“, siehe Eigenschaftstests-Pilot): Invarianten auf Zufallspaaren mit festem Seed."""

import random

import numpy as np

import gwi_algorithm as A
from gwi_algorithm import Pair

SEED = 20261110


def _random_matroid(rng, n):
    kind = rng.choice(["uniform", "partition", "graphic", "gf2"])
    if kind == "uniform":
        k = rng.randint(0, n)
        return np.array([bin(mask).count("1") <= k for mask in range(1 << n)])
    if kind == "partition":
        return A.partition_table(n, [rng.randint(0, 2) for _ in range(n)], {c: rng.randint(1, 2) for c in range(3)})
    if kind == "graphic":
        v = rng.randint(2, 5)
        return A.graphic_table(v, [(rng.randrange(v), rng.randrange(v)) for _ in range(n)])
    vec = [rng.getrandbits(3) for _ in range(n)]

    def indep(mask):
        basis = []
        for e in range(n):
            if mask >> e & 1:
                x = vec[e]
                for b in basis:
                    x = min(x, x ^ b)
                if not x:
                    return False
                basis.append(x)
        return True

    return np.array([indep(mask) for mask in range(1 << n)])


def _pairs(count=60):
    rng = random.Random(SEED)
    out = []
    for _ in range(count):
        n = rng.randint(2, 6)
        costs = tuple(rng.randint(-2, 5) for _ in range(n))
        out.append(Pair("zufall", n, _random_matroid(rng, n), _random_matroid(rng, n), tuple(str(i) for i in range(n)), "kanten", costs=costs))
    return out


def test_each_step_is_a_valid_cheapest_set_of_its_size_and_the_run_reaches_the_optimum():
    for p in _pairs():
        rounds = A.weighted_steps(p)
        assert A.run_is_correct(p, rounds, A.best_by_size(p))
        assert not any(r["neg"] for r in rounds)


def test_costs_per_size_are_convex_and_each_step_adds_the_path_length():
    for p in _pairs():
        rounds = A.weighted_steps(p)
        costs = [r["cost"] for r in rounds]
        diffs = [b - a for a, b in zip(costs, costs[1:])]
        assert all(d2 >= d1 for d1, d2 in zip(diffs, diffs[1:]))
        assert all(rounds[i]["length"] == diffs[i] for i in range(len(diffs)))


def test_the_run_sets_have_no_negative_cycle_and_paths_alternate():
    for p in _pairs():
        for rd in A.weighted_steps(p)[:-1]:
            assert A.is_extreme(p, rd["set"])
            path = rd["path"]
            assert len(path) % 2 == 1 and all(not rd["set"] >> v & 1 for v in path[::2]) and all(rd["set"] >> v & 1 for v in path[1::2])


def test_the_node_rule_never_uses_more_nodes_than_the_other_choices_when_lengths_are_equal():
    for p in _pairs(40):
        for rd in A.weighted_steps(p)[:-1]:
            other = A.shortest_path(p, rd["set"], "any")
            if other["path"] is not None and not other["neg"] and other["length"] == rd["length"]:
                assert len(rd["path"]) <= len(other["path"])


def test_adding_a_constant_shifts_the_cost_curve_linearly_and_scaling_scales_it():
    for p in _pairs(30):
        base = [r["cost"] for r in A.weighted_steps(p)]
        shifted = Pair("s", p.m, p.ok1, p.ok2, p.labels, "kanten", costs=tuple(c + 3 for c in p.costs))
        doubled = Pair("d", p.m, p.ok1, p.ok2, p.labels, "kanten", costs=tuple(2 * c for c in p.costs))
        assert [r["cost"] for r in A.weighted_steps(shifted)] == [c + 3 * k for k, c in enumerate(base)]
        assert [r["cost"] for r in A.weighted_steps(doubled)] == [2 * c for c in base]


def test_swapping_the_matroids_and_relabeling_keep_the_cost_curve():
    rng = random.Random(SEED + 1)
    for p in _pairs(30):
        curve = [r["cost"] for r in A.weighted_steps(p)]
        swapped = Pair("v", p.m, p.ok2, p.ok1, p.labels, "kanten", costs=p.costs)
        assert [r["cost"] for r in A.weighted_steps(swapped)] == curve
        perm = list(range(p.m))
        rng.shuffle(perm)
        idx = np.arange(1 << p.m)
        new = np.zeros(1 << p.m, dtype=np.int64)
        for e in range(p.m):
            new |= ((idx >> e) & 1) << perm[e]
        ok1, ok2 = np.zeros(1 << p.m, dtype=bool), np.zeros(1 << p.m, dtype=bool)
        ok1[new], ok2[new] = p.ok1, p.ok2
        costs = [0] * p.m
        for e in range(p.m):
            costs[perm[e]] = p.costs[e]
        relabeled = Pair("r", p.m, ok1, ok2, p.labels, "kanten", costs=tuple(costs))
        assert [r["cost"] for r in A.weighted_steps(relabeled)] == curve


def test_improving_the_worst_set_ends_at_the_cheapest_cost_with_strictly_falling_costs():
    for p in _pairs(30):
        best = A.best_by_size(p)
        for k in range(1, p.opt + 1):
            start = A.worst_of_size(p, k)
            chain = A.improve_to_extreme(p, start)
            costs = [A.total_cost(p, start)] + [c["cost"] for c in chain]
            assert all(b < a for a, b in zip(costs, costs[1:])) and costs[-1] == best[k]
            assert all(p.common[c["after"]] and A.popcount(c["after"]) == k for c in chain)
            assert all(c["length"] == c2 - c1 for c, c1, c2 in zip(chain, costs, costs[1:]))


def test_the_negative_cycle_found_has_the_fewest_arcs_among_all_negative_cycles():
    import itertools
    for p in _pairs(20):
        for k in range(1, p.opt + 1):
            start = A.worst_of_size(p, k)
            cycle = A.find_negative_cycle(p, start)
            if cycle is None:
                continue
            g = A.exchange_graph(p, start)
            arcs = {(a, b) for a, b, _ in g["arcs"]}
            l = A.node_lengths(p, start)
            for h in range(2, len(cycle)):
                for combo in itertools.permutations(range(p.m), h):
                    if all((combo[i], combo[(i + 1) % h]) in arcs for i in range(h)):
                        assert sum(l[v] for v in combo) >= 0, (h, combo)
