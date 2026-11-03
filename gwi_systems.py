"""Die drei Beispiele der Demo als Paare von Matroiden mit Kosten: Regenbogen-Spannbaum und Zuordnung auf dem Leitungsnetz (Kosten der Leitungen), Arboreszenz als festes Beispiel (Kosten aus dem Seed)."""

import random
from functools import lru_cache

import gwi_constants as C
from gwi_algorithm import Pair, graphic_table, partition_table
from gwi_scenario import Instance, make_instance


def edge_colors(inst: Instance, seed: int, k: int) -> list[int]:
    """Farbe (0 bis k − 1) je Leitung, deterministisch aus dem Seed."""
    rng = random.Random(seed * 31 + 7)
    return [rng.randrange(k) for _ in range(inst.m)]


def color_name(c: int) -> str:
    return f"F{c + 1}"


def arc_costs(seed: int) -> list[int]:
    """Kosten der 12 Bögen der Arboreszenz: ganze Zahlen von 1 bis ARB_COST_MAX, deterministisch aus dem Seed."""
    rng = random.Random(seed * 17 + 3)
    return [rng.randint(1, C.ARB_COST_MAX) for _ in C.ARBORESCENCE_ARCS]


def build_pair(key: str, n: int, seed: int, k: int) -> Pair:
    """Das Beispiel `key` (aus C.SYSTEMS) auf dem Plan (n, seed); k Farben beim Regenbogen. Die Arboreszenz hängt nicht vom Plan ab."""
    if key not in C.SYSTEMS:
        raise ValueError(f"unbekanntes Beispiel: {key}")
    if key == "arboreszenz":
        arcs = C.ARBORESCENCE_ARCS
        m = len(arcs)
        heads = ["wurzel" if h == 0 else h for _, h in arcs]
        return Pair(key, m, graphic_table(6, arcs), partition_table(m, heads, {"wurzel": 0}), tuple(f"{a}→{b}" for a, b in arcs), "boegen", costs=tuple(arc_costs(seed)))
    inst = make_instance(n, seed)
    edges = [(u, w) for u, w, _ in inst.edges]
    labels = tuple(inst.label(e) for e in range(inst.m))
    costs = tuple(int(c) for _, _, c in inst.edges)
    if key == "regenbogen":
        colors = edge_colors(inst, seed, k)
        return Pair(key, inst.m, graphic_table(inst.n, edges), partition_table(inst.m, colors), labels, "kanten", inst, tuple(colors), costs=costs)
    return Pair(key, inst.m, partition_table(inst.m, [u for u, _ in edges]), partition_table(inst.m, [w for _, w in edges]), labels, "kanten", inst, costs=costs)


@lru_cache(maxsize=24)
def _cached_pair(key: str, n: int, seed: int, k: int) -> Pair:
    return build_pair(key, n, seed, k)


def get_pair(key: str, n: int, seed: int, k: int) -> Pair:
    """Gleiches Paar für gleiche Eingaben: der Aufbau der Tabellen kostet bei 16 Leitungen etwa eine Sekunde. n, seed und k zählen nur, wo sie das Beispiel bestimmen
    (die Arboreszenz hängt nur vom Seed ab, die Zuordnung nicht von k); die übrigen Werte werden vor dem Zwischenspeichern auf 0 gesetzt."""
    if key == "arboreszenz":
        n, k = 0, 0
    elif key == "zuordnung":
        k = 0
    return _cached_pair(key, n, seed, k)
