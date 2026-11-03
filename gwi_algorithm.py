"""Kern der Demo: gewichteter Matroid-Schnitt auf höchstens 16 Elementen (Bitmasken): zu jeder Elementzahl k die billigste gemeinsame unabhängige Menge I_k, über kürzeste Wege im Austauschgraphen.

Knotenlängen beim Minimieren: +c für Elemente außerhalb von I, −c für Elemente in I; Bellman–Ford, bei gleicher Länge der Weg mit den wenigsten Knoten; I_{k+1} = I_k Δ Weg.
I hat die kleinsten Kosten unter allen gemeinsamen Mengen mit |I| Elementen genau dann, wenn der Austauschgraph keinen Kreis negativer Länge hat.

Unten die Grundlagen aus Stück 7 (Tabellen, Paar, Greedy, Austauschgraph, alle kleinen Paare):

Gemeinsam unabhängig: in beiden Matroiden unabhängig. Greedy = eine maximale gemeinsame Menge (Elemente in irgendeiner Reihenfolge hinzufügen, solange sie in beiden passen).
Austauschgraph D(I) zu einer gemeinsamen Menge I: Pfeil y → x (y in I, x außerhalb), wenn I − y + x in M1 unabhängig ist; Pfeil x → y, wenn I − y + x in M2 unabhängig ist.
Quellen X1 = {x : I + x in M1}, Senken X2 = {x : I + x in M2}. Ein kürzester Weg von X1 nach X2 vergrößert I um 1 (symmetrische Differenz); ohne Weg ist I größtmöglich.
Zertifikat: R = von X1 aus erreichbar, A = E ∖ R; dann r1(A) + r2(E ∖ A) = |I| (Min-Max-Formel von Edmonds)."""

import itertools
from dataclasses import dataclass, field
from functools import cached_property

import numpy as np


def popcount(x: int) -> int:
    return bin(x).count("1")


def elements(mask: int, m: int) -> list[int]:
    return [e for e in range(m) if mask >> e & 1]


class System:
    """Unabhängigkeitssystem auf m Elementen; ok[mask] sagt, ob die Menge `mask` zulässig ist."""

    def __init__(self, name: str, m: int, ok):
        if not 1 <= m <= 16:
            raise ValueError(f"m = {m} außerhalb von 1 bis 16")
        if len(ok) != 1 << m or not ok[0]:
            raise ValueError("ok braucht 2**m Einträge, und die leere Menge muss zulässig sein")
        self.name, self.m, self.ok = name, m, list(ok)
        self.full = (1 << m) - 1
        self.ind = [mask for mask in range(1 << m) if self.ok[mask]]
        self.ind_array = np.array(self.ind, dtype=np.int64)
        self.sizes = np.array([popcount(i) for i in self.ind], dtype=np.int64)
        self._ranks()

    # --- Grundbegriffe ------------------------------------------------------------------------------------------------------------------

    def check_down_closed(self) -> bool:
        """Mit jeder zulässigen Menge sind alle Mengen ohne ein Element zulässig (genügt für alle Teilmengen)."""
        return all(self.ok[mask & ~(1 << e)] for mask in self.ind for e in range(self.m) if mask >> e & 1)

    def can_add(self, mask: int, e: int) -> bool:
        return not mask >> e & 1 and self.ok[mask | 1 << e]

    def addable(self, mask: int) -> int:
        """Maske aller Elemente, die zu `mask` passen."""
        out = 0
        for e in range(self.m):
            if self.can_add(mask, e):
                out |= 1 << e
        return out

    def is_maximal(self, mask: int) -> bool:
        return self.ok[mask] and self.addable(mask) == 0

    def _ranks(self):
        m, ok = self.m, self.ok
        ur = [0] * (1 << m)
        for mask in range(1, 1 << m):
            ur[mask] = popcount(mask) if ok[mask] else max(ur[mask & ~(1 << e)] for e in range(m) if mask >> e & 1)
        self.ur = ur
        lr = [0] * (1 << m)
        for i in sorted(self.ind, key=popcount):
            free = self.full & ~i & ~self.addable(i)
            s = free
            while True:
                f = i | s
                if f and lr[f] == 0:
                    lr[f] = popcount(i)
                if s == 0:
                    break
                s = (s - 1) & free
        self.lr = lr
        best = None
        for f in range(1, 1 << m):
            if ur[f] > 0:
                q = lr[f] / ur[f]
                if best is None or q < best[0] - 1e-15:
                    best = (q, f)
        self.q = best[0] if best else 1.0

    # --- Rang, Basen, Kreise, Abschluss, Flache -------------------------------------------------------------------------------------------

    @property
    def rank(self) -> int:
        """Rang der ganzen Grundmenge: Größe der größten zulässigen Menge."""
        return self.ur[self.full]

    def rank_of(self, f: int) -> int:
        return self.ur[f]

    @cached_property
    def bases(self) -> list[int]:
        """Maximale zulässige Mengen (bei einem Matroid alle gleich groß)."""
        return [i for i in self.ind if self.is_maximal(i)]

    @cached_property
    def circuits(self) -> list[int]:
        """Minimale unzulässige Mengen."""
        out = []
        for c in range(1, 1 << self.m):
            if not self.ok[c] and all(self.ok[c & ~(1 << e)] for e in range(self.m) if c >> e & 1):
                out.append(c)
        return out

    def closure(self, f: int) -> int:
        """cl(F) = F plus alle e, deren Hinzunahme den Rang nicht erhöht."""
        r = self.ur[f]
        out = f
        for e in range(self.m):
            if not f >> e & 1 and self.ur[f | 1 << e] == r:
                out |= 1 << e
        return out

    @cached_property
    def closures(self) -> list[int]:
        return [self.closure(f) for f in range(1 << self.m)]

    @cached_property
    def flats(self) -> list[int]:
        return [f for f in range(1 << self.m) if self.closures[f] == f]

    def flats_by_rank(self) -> dict[int, int]:
        out: dict[int, int] = {}
        for f in self.flats:
            out[self.ur[f]] = out.get(self.ur[f], 0) + 1
        return dict(sorted(out.items()))

    def circuits_in(self, mask: int) -> list[int]:
        """Alle Kreise, die in `mask` enthalten sind."""
        return [c for c in self.circuits if c & ~mask == 0]

    def fundamental_circuit(self, base: int, e: int):
        """Der Kreis in B + e, wenn es genau einen gibt (bei einem Matroid immer), sonst None."""
        inside = self.circuits_in(base | 1 << e)
        return inside[0] if len(inside) == 1 else None

    def swap_is_basis(self, base: int, f: int, e: int) -> bool:
        """Ist B − f + e wieder eine Basis (maximale zulässige Menge)?"""
        new = (base & ~(1 << f)) | 1 << e
        return self.is_maximal(new)

    def maximal_sizes(self) -> dict[int, int]:
        sizes: dict[int, int] = {}
        for i in self.bases:
            sizes[popcount(i)] = sizes.get(popcount(i), 0) + 1
        return dict(sorted(sizes.items()))

    # --- Austauschprobe (Stück 3) -------------------------------------------------------------------------------------------------------

    def exchange_scan(self, weak: bool = False) -> tuple[int, int]:
        """(Zahl der Paare (I1, I2) mit |I1| < |I2|, Zahl der Paare ohne Austauschpartner); je I1 ein Maskenvergleich über alle I2."""
        pairs = viol = 0
        for i1, s1 in zip(self.ind, self.sizes):
            bigger = self.sizes == s1 + 1 if weak else self.sizes > s1
            count = int(bigger.sum())
            if not count:
                continue
            pairs += count
            viol += int(((self.ind_array[bigger] & ~i1 & self.addable(i1)) == 0).sum())
        return pairs, viol

    @cached_property
    def is_matroid(self) -> bool:
        return self.exchange_scan()[1] == 0


# --- Tabellen: Rang, Partitionsmatroid, graphisches Matroid ----------------------------------------------------------------------------------


_PC = None


def pc_table() -> np.ndarray:
    """Elementzahl aller Masken bis 2^16."""
    global _PC
    if _PC is None:
        _PC = np.array([bin(i).count("1") for i in range(1 << 16)], dtype=np.int16)
    return _PC


def rank_table(ok: np.ndarray, m: int) -> np.ndarray:
    """Rang jeder Teilmenge: Größe der größten unabhängigen Teilmenge (Schichten nach Elementzahl, mit numpy)."""
    pc = pc_table()[: 1 << m]
    ur = np.zeros(1 << m, dtype=np.int16)
    idx = np.arange(1 << m)
    for k in range(1, m + 1):
        layer = idx[pc == k]
        best = np.zeros(len(layer), dtype=np.int16)
        for e in range(m):
            has = (layer >> e & 1) == 1
            sub = ur[layer[has] & ~(1 << e)]
            best[has] = np.maximum(best[has], sub)
        ur[layer] = np.where(ok[layer], k, best)
    return ur


def partition_table(m: int, classes, caps=None) -> np.ndarray:
    """Partitionsmatroid: je Klasse höchstens caps[klasse] Elemente (Standard 1)."""
    caps = caps or {}
    pc = pc_table()[: 1 << m]
    idx = np.arange(1 << m)
    ok = np.ones(1 << m, dtype=bool)
    for cls in set(classes):
        mask = sum(1 << e for e in range(m) if classes[e] == cls)
        ok &= pc[idx & mask] <= caps.get(cls, 1)
    return ok


def graphic_table(v: int, edges) -> np.ndarray:
    """Graphisches Matroid der Kantenliste auf v Knoten (Schleifen sind nie unabhängig)."""
    m = len(edges)
    ok = np.zeros(1 << m, dtype=bool)
    for mask in range(1 << m):
        parent = list(range(v))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        good = True
        for e in range(m):
            if mask >> e & 1:
                a, b = find(edges[e][0]), find(edges[e][1])
                if a == b:
                    good = False
                    break
                parent[a] = b
        ok[mask] = good
    return ok


@dataclass
class Pair:
    """Zwei Matroide auf derselben Grundmenge mit m Elementen (ok1[mask], ok2[mask]: ist die Menge in M1 bzw. M2 unabhängig?)."""
    key: str
    m: int
    ok1: np.ndarray
    ok2: np.ndarray
    labels: tuple
    kind: str                       # "kanten" (Leitungen des Plans) oder "boegen" (festes Beispiel)
    inst: object = None
    colors: tuple = ()
    extra: dict = field(default_factory=dict)
    costs: tuple = ()               # Kosten je Element (ganze Zahlen); beim Minimieren der Kosten sind es die Längen des Austauschgraphen

    @cached_property
    def common(self) -> np.ndarray:
        return self.ok1 & self.ok2

    @cached_property
    def full(self) -> int:
        return (1 << self.m) - 1

    @cached_property
    def ur1(self) -> np.ndarray:
        return rank_table(self.ok1, self.m)

    @cached_property
    def ur2(self) -> np.ndarray:
        return rank_table(self.ok2, self.m)

    @cached_property
    def opt(self) -> int:
        return int(pc_table()[np.nonzero(self.common)[0]].max())

    @cached_property
    def opt_set(self) -> int:
        """Die erste gemeinsame Menge (nach Maske) mit der Größe des Optimums."""
        idx = np.nonzero(self.common)[0]
        return int(idx[pc_table()[idx] == self.opt][0])

    @cached_property
    def maximal(self) -> np.ndarray:
        """Alle maximalen gemeinsamen Mengen (kein Element passt in beiden Matroiden dazu), als Masken."""
        idx = np.arange(1 << self.m)
        maximal = self.common.copy()
        for e in range(self.m):
            bit = 1 << e
            has = (idx & bit) == 0
            grow = np.zeros(1 << self.m, dtype=bool)
            grow[has] = self.common[idx[has] | bit]
            maximal &= ~grow
        return np.nonzero(maximal)[0]

    @cached_property
    def worst_set(self) -> int:
        """Die erste maximale gemeinsame Menge (nach Maske) mit den wenigsten Elementen."""
        sizes = pc_table()[self.maximal]
        return int(self.maximal[int(sizes.argmin())])

    @cached_property
    def n_common(self) -> int:
        return int(self.common.sum())


# --- Greedy ------------------------------------------------------------------------------------------------------------------------------


def greedy_common(pair: Pair, order) -> int:
    """Elemente in der Reihenfolge `order` hinzufügen, solange die Menge in beiden Matroiden unabhängig bleibt."""
    cur = 0
    for e in order:
        if pair.common[cur | 1 << e]:
            cur |= 1 << e
    return cur


def random_greedy(pair: Pair, trials: int, seed: int) -> dict:
    """Greedy bei zufälligen Reihenfolgen: Größen der gefundenen Mengen gegen das Optimum."""
    rng = np.random.default_rng(seed)
    sizes = []
    for _ in range(trials):
        sizes.append(popcount(greedy_common(pair, [int(x) for x in rng.permutation(pair.m)])))
    return {"trials": trials, "sizes": sizes}


def maximal_sizes(pair: Pair) -> dict[int, int]:
    sizes = pc_table()[pair.maximal]
    return {int(k): int((sizes == k).sum()) for k in sorted(set(sizes.tolist()))}


# --- Austauschgraph und Verfahren ----------------------------------------------------------------------------------------------------


def exchange_graph(pair: Pair, cur: int) -> dict:
    """Der vollständige Austauschgraph zu I = cur: Quellen, Senken, Pfeile (von, nach, welches Matroid)."""
    m = pair.m
    out = [e for e in range(m) if not cur >> e & 1]
    inn = [e for e in range(m) if cur >> e & 1]
    x1 = [x for x in out if pair.ok1[cur | 1 << x]]
    x2 = [x for x in out if pair.ok2[cur | 1 << x]]
    arcs = []
    for y in inn:
        for x in out:
            swap = (cur & ~(1 << y)) | 1 << x
            if pair.ok1[swap]:
                arcs.append((y, x, 1))
            if pair.ok2[swap]:
                arcs.append((x, y, 2))
    return {"out": out, "inn": inn, "x1": x1, "x2": x2, "arcs": arcs}


def bfs_path(sources, is_sink, neighbors):
    """Kürzester Weg von einer Quelle zu einer Senke; (Weg oder None, besuchte Menge)."""
    parent = {s: None for s in sources}
    queue = list(sources)
    head = 0
    while head < len(queue):
        v = queue[head]
        head += 1
        if is_sink(v):
            path = []
            while v is not None:
                path.append(v)
                v = parent[v]
            return path[::-1], set(parent)
        for w in neighbors(v):
            if w not in parent:
                parent[w] = v
                queue.append(w)
    return None, set(parent)


def greedy_start(pair: Pair) -> int:
    return greedy_common(pair, range(pair.m))


START_NAMES = {"leer": "leere Menge", "greedy": "Greedy nach Nummer", "schlecht": "schlechteste maximale Menge"}


def steps(pair: Pair, start: str = "leer") -> list[dict]:
    """Der Lauf Runde für Runde mit dem vollständigen Austauschgraphen: je Runde die Menge I, Quellen, Senken, Pfeile und der kürzeste Weg (am Ende: keiner, dafür die erreichbare Menge R).
    start: "leer" (I = ∅), "greedy" (Greedy in der Reihenfolge der Nummern) oder "schlecht" (die kleinste maximale gemeinsame Menge, der schlechteste Fall für Greedy)."""
    cur = {"leer": 0, "greedy": greedy_start(pair), "schlecht": pair.worst_set}[start]
    rounds = []
    while True:
        g = exchange_graph(pair, cur)
        adj: dict[int, list[int]] = {v: [] for v in range(pair.m)}
        for a, b, _ in g["arcs"]:
            adj[a].append(b)
        sinks = set(g["x2"])
        path, seen = bfs_path(g["x1"], lambda v: v in sinks, lambda v: adj[v])
        rounds.append({"set": cur, **g, "path": path, "reach": sum(1 << v for v in seen) if path is None else None})
        if path is None:
            return rounds
        for v in path:
            cur ^= 1 << v


class Oracle:
    """Zählt jede Frage „ist die Menge unabhängig?“."""

    def __init__(self, ok):
        self.ok, self.calls = ok, 0

    def __call__(self, mask):
        self.calls += 1
        return self.ok[mask]


VARIANTS = ("naiv", "faul", "faul+greedy")


def intersect(pair: Pair, variant: str) -> dict:
    """Drei Varianten des Verfahrens, mit gezählten Orakelaufrufen. naiv: ganzer Austauschgraph je Runde; faul: Pfeile erst beim Besuch; faul+greedy: dazu Start mit Greedy."""
    m = pair.m
    o1, o2 = Oracle(pair.ok1.tolist()), Oracle(pair.ok2.tolist())
    cur = 0
    start = 0
    if variant == "faul+greedy":
        for e in range(m):
            if o1(cur | 1 << e) and o2(cur | 1 << e):
                cur |= 1 << e
        start = popcount(cur)
    lengths = []
    while True:
        out = [e for e in range(m) if not cur >> e & 1]
        inn = [e for e in range(m) if cur >> e & 1]
        x1 = [x for x in out if o1(cur | 1 << x)]
        if variant == "naiv":
            x2 = {x for x in out if o2(cur | 1 << x)}
            adj: dict[int, list[int]] = {v: [] for v in range(m)}
            for y in inn:
                for x in out:
                    swap = (cur & ~(1 << y)) | 1 << x
                    if o1(swap):
                        adj[y].append(x)
                    if o2(swap):
                        adj[x].append(y)
            path, seen = bfs_path(x1, lambda v: v in x2, lambda v: adj[v])
        else:
            def is_sink(v):
                return not cur >> v & 1 and o2(cur | 1 << v)

            def neighbors(v):
                if cur >> v & 1:
                    return [x for x in out if o1((cur & ~(1 << v)) | 1 << x)]
                return [y for y in inn if o2((cur & ~(1 << y)) | 1 << v)]

            path, seen = bfs_path(x1, is_sink, neighbors)
        if path is None:
            return {"set": cur, "calls": o1.calls + o2.calls, "rounds": len(lengths), "lengths": lengths, "reach": sum(1 << v for v in seen), "start": start}
        for v in path:
            cur ^= 1 << v
        lengths.append(len(path))


def certificate(pair: Pair, reach: int) -> tuple[int, int, int]:
    """(r1(E ∖ R), r2(R), Summe) zur erreichbaren Menge R am Ende des Verfahrens."""
    a, b = int(pair.ur1[pair.full ^ reach]), int(pair.ur2[reach])
    return a, b, a + b


def min_max(pair: Pair) -> dict:
    """Minimum über alle A von r1(A) + r2(E ∖ A) und die Menge der Minimierer (Masken, nach Größe und Maske geordnet)."""
    idx = np.arange(1 << pair.m)
    total = pair.ur1[idx] + pair.ur2[pair.full ^ idx]
    value = int(total.min())
    mins = np.nonzero(total == value)[0]
    order = sorted(mins.tolist(), key=lambda x: (popcount(x), x))
    return {"value": value, "count": len(order), "first": order[:8]}


def intersection_is_matroid(pair: Pair, limit: int = 12):
    """Ist die Familie der gemeinsamen unabhängigen Mengen selbst ein Matroid? Nur bis `limit` Elemente gerechnet (sonst None)."""
    if pair.m > limit:
        return None
    return System("schnitt", pair.m, pair.common.tolist()).exchange_scan()[1] == 0


# --- alle Paare kleiner Matroide ------------------------------------------------------------------------------------------------------------


def all_systems(n: int) -> list[tuple[bool, ...]]:
    """Alle nach unten abgeschlossenen Familien auf n Elementen mit leerer Menge, jeweils als Tupel ok[mask]."""
    masks = sorted(range(1 << n), key=lambda x: (popcount(x), x))
    out: list[tuple[bool, ...]] = []
    family = [False] * (1 << n)

    def rec(i):
        if i == len(masks):
            if family[0]:
                out.append(tuple(family))
            return
        mask = masks[i]
        allowed = mask == 0 or all(family[mask & ~(1 << e)] for e in range(n) if mask >> e & 1)
        family[mask] = False
        rec(i + 1)
        if allowed:
            family[mask] = True
            rec(i + 1)
            family[mask] = False

    rec(0)
    return out


def small_matroids(n: int) -> list[tuple[np.ndarray, np.ndarray]]:
    """Alle Matroide auf n Elementen als (Tabelle der unabhängigen Mengen, Rangtabelle)."""
    out = []
    for ok in all_systems(n):
        s = System("x", n, list(ok))
        if s.exchange_scan()[1] == 0:
            out.append((np.array(s.ok, dtype=bool), np.array(s.ur, dtype=np.int16)))
    return out


def small_pairs_row(n: int, sample: int, seed: int) -> dict:
    """Alle Paare von Matroiden auf n Elementen: Greedy-Faktor (schlechteste maximale Menge gegen Optimum), Min-Max-Formel, und das Verfahren (alle Paare bis 4 Elemente, sonst eine Stichprobe)."""
    mats = small_matroids(n)
    pc = pc_table()[: 1 << n]
    idx = np.arange(1 << n)
    full = (1 << n) - 1
    comp = full ^ idx
    row = {"n": n, "matroids": len(mats), "pairs": 0, "fail": 0, "worst": 1.0, "half": 0, "below_half": 0, "minmax": 0, "checked": 0, "alg_ok": 0, "cert_ok": 0, "rounds": []}
    grow_index = [(idx & (1 << e)) == 0 for e in range(n)]
    for ok1, ur1 in mats:
        for ok2, ur2 in mats:
            common = ok1 & ok2
            opt = int(pc[common].max())
            maximal = common.copy()
            for e in range(n):
                grow = np.zeros(1 << n, dtype=bool)
                grow[grow_index[e]] = common[idx[grow_index[e]] | (1 << e)]
                maximal &= ~grow
            lo = int(pc[maximal].min())
            row["pairs"] += 1
            row["fail"] += lo < opt
            ratio = lo / opt if opt else 1.0
            row["worst"] = min(row["worst"], ratio)
            row["below_half"] += ratio < 0.5 - 1e-12
            row["half"] += abs(ratio - 0.5) < 1e-12
            row["minmax"] += int((ur1[idx] + ur2[comp]).min()) == opt
    pool = [(a, b) for a in mats for b in mats]
    if len(pool) > sample:
        rng = np.random.default_rng(seed + n)
        pool = [pool[i] for i in rng.choice(len(pool), size=sample, replace=False)]
    for (ok1, ur1), (ok2, ur2) in pool:
        pair = Pair("klein", n, ok1, ok2, tuple(str(i) for i in range(n)), "kanten")
        pair.__dict__["ur1"], pair.__dict__["ur2"] = ur1, ur2
        r = intersect(pair, "faul")
        row["checked"] += 1
        row["alg_ok"] += popcount(r["set"]) == pair.opt
        row["cert_ok"] += certificate(pair, r["reach"])[2] == popcount(r["set"])
        row["rounds"].append(r["rounds"])
    return row


# --- Gewichtet: Knotenlängen, Bellman–Ford, Tauschkreis -------------------------------------------------------------------------------------


def node_lengths(pair: Pair, cur: int, costs=None) -> list[int]:
    """Länge jedes Elements im Austauschgraphen zu I = cur beim Minimieren der Kosten: +c für Elemente außerhalb, −c für Elemente in I."""
    costs = pair.costs if costs is None else costs
    return [-costs[v] if cur >> v & 1 else costs[v] for v in range(pair.m)]


def total_cost(pair: Pair, mask: int, costs=None) -> int:
    costs = pair.costs if costs is None else costs
    return sum(costs[e] for e in range(pair.m) if mask >> e & 1)


TIEBREAKS = ("hops", "any", "rev")


def shortest_path(pair: Pair, cur: int, tiebreak: str = "hops", costs=None) -> dict:
    """Kürzester Weg von den Quellen X1 zu den Senken X2 im Austauschgraphen zu I = cur, mit Bellman–Ford auf den Knotenlängen.
    tiebreak: "hops" (kleinste Länge, bei Gleichstand wenigste Knoten), "any" (nur die Länge, Pfeile in der Erzeugungsreihenfolge), "rev" (nur die Länge, Pfeile umgekehrt).
    Rückgabe: Weg (oder None), seine Länge, Quellen, Senken, Entfernungen und Knotenzahlen der erreichten Elemente, Zahl der Runden und der Verbesserungen, Kennzeichen „negativer Kreis“."""
    g = exchange_graph(pair, cur)
    l = node_lengths(pair, cur, costs)
    arcs = [(a, b) for a, b, _ in g["arcs"]]
    if tiebreak == "rev":
        arcs = arcs[::-1]
    dist: dict[int, int] = {}
    hops: dict[int, int] = {}
    parent: dict[int, int | None] = {}
    for s in g["x1"]:
        dist[s], hops[s], parent[s] = l[s], 1, None
    relax = 0
    neg = False
    rounds = 0
    for rounds in range(1, pair.m + 2):
        changed = False
        for a, b in arcs:
            if a in dist:
                nd, nh = dist[a] + l[b], hops[a] + 1
                better = b not in dist or ((nd, nh) < (dist[b], hops[b]) if tiebreak == "hops" else nd < dist[b])
                if better:
                    dist[b], hops[b], parent[b] = nd, nh, a
                    changed = True
                    relax += 1
        if not changed:
            break
    else:
        neg = True
    out = {"path": None, "length": None, "x1": g["x1"], "x2": g["x2"], "dist": dist, "hops": hops, "lengths": l, "rounds": rounds, "relax": relax, "neg": neg}
    sinks = [x for x in g["x2"] if x in dist]
    if neg or not sinks:
        return out
    best = min(sinks, key=lambda x: (dist[x], hops[x]) if tiebreak == "hops" else (dist[x], x))
    path = []
    v = best
    while v is not None:
        path.append(v)
        v = parent[v]
    out["path"] = path[::-1]
    out["length"] = dist[best]
    return out


def weighted_steps(pair: Pair, tiebreak: str = "hops", costs=None) -> list[dict]:
    """I_0 = ∅, I_1, …: je Runde die Menge, ihre Kosten und der Weg zur nächsten (am Ende: keiner)."""
    cur = 0
    rounds = []
    while True:
        sp = shortest_path(pair, cur, tiebreak, costs)
        rounds.append({"set": cur, "k": popcount(cur), "cost": total_cost(pair, cur, costs), **sp})
        if sp["path"] is None:
            return rounds
        for v in sp["path"]:
            cur ^= 1 << v


def cost_table(pair: Pair, costs=None) -> np.ndarray:
    """Kosten jeder Teilmenge (Tabelle über alle Bitmasken)."""
    costs = pair.costs if costs is None else costs
    idx = np.arange(1 << pair.m)
    vals = np.zeros(1 << pair.m, dtype=np.int64)
    for e in range(pair.m):
        vals += ((idx >> e) & 1) * costs[e]
    return vals


def best_by_size(pair: Pair, costs=None) -> dict[int, int]:
    """Kleinste Kosten einer gemeinsamen Menge mit k Elementen, k = 0 bis Optimum (Aufzählung)."""
    vals = cost_table(pair, costs)
    pc = pc_table()[: 1 << pair.m]
    return {k: int(vals[pair.common & (pc == k)].min()) for k in range(pair.opt + 1)}


def worst_of_size(pair: Pair, k: int, costs=None) -> int:
    """Die erste gemeinsame Menge (nach Maske) mit k Elementen und den größten Kosten."""
    vals = cost_table(pair, costs)
    idx = np.nonzero(pair.common & (pc_table()[: 1 << pair.m] == k))[0]
    return int(idx[int(vals[idx].argmax())])


def greedy_by_cost(pair: Pair, costs=None) -> int:
    """Billigste Leitung zuerst, solange die Menge in beiden Matroiden unabhängig bleibt."""
    costs = pair.costs if costs is None else costs
    return greedy_common(pair, sorted(range(pair.m), key=lambda e: (costs[e], e)))


def find_negative_cycle(pair: Pair, cur: int, costs=None):
    """Ein Kreis negativer Länge im Austauschgraphen zu I = cur mit möglichst wenigen Pfeilen, als Liste der Elemente in Pfeilrichtung (Länge = Summe der Knotenlängen),
    oder None. Gesucht wird über geschlossene Wege mit h = 2, 3, … Pfeilen: Der kürzeste negative geschlossene Weg ist ein einfacher Kreis."""
    g = exchange_graph(pair, cur)
    l = node_lengths(pair, cur, costs)
    m = pair.m
    preds: list[list[int]] = [[] for _ in range(m)]
    for a, b, _ in g["arcs"]:
        preds[b].append(a)
    inf = float("inf")
    tables = []
    for s in range(m):
        d = [[inf] * m for _ in range(m + 1)]
        par = [[-1] * m for _ in range(m + 1)]
        d[0][s] = 0
        for h in range(1, m + 1):
            for v in range(m):
                for u in preds[v]:
                    if d[h - 1][u] + l[v] < d[h][v]:
                        d[h][v] = d[h - 1][u] + l[v]
                        par[h][v] = u
        tables.append((d, par))
    for h in range(2, m + 1):
        for s in range(m):
            d, par = tables[s]
            if d[h][s] < 0:
                cycle, v = [], s
                for t in range(h, 0, -1):
                    cycle.append(v)
                    v = par[t][v]
                return cycle[::-1]
    return None


def cycle_length(pair: Pair, cur: int, cycle, costs=None) -> int:
    l = node_lengths(pair, cur, costs)
    return sum(l[v] for v in cycle)


def improve_to_extreme(pair: Pair, cur: int, costs=None) -> list[dict]:
    """Tauschkreise anwenden, bis keiner mehr da ist: je Schritt (Menge davor, Kreis, Länge, Menge danach, Kosten danach)."""
    steps_ = []
    while True:
        cycle = find_negative_cycle(pair, cur, costs)
        if cycle is None:
            return steps_
        nxt = cur ^ sum(1 << v for v in cycle)
        steps_.append({"before": cur, "cycle": cycle, "length": cycle_length(pair, cur, cycle, costs), "after": nxt, "cost": total_cost(pair, nxt, costs)})
        cur = nxt


def is_extreme(pair: Pair, cur: int, costs=None) -> bool:
    """Kein Kreis negativer Länge im Austauschgraphen zu I = cur."""
    return find_negative_cycle(pair, cur, costs) is None


def tie_pair() -> Pair:
    """Das feste Gleichstandsbeispiel mit 5 Elementen (siehe gwi_constants.TIE_*): unabhängig ist, was in einer der maximalen Mengen liegt."""
    import gwi_constants as C
    m = 5
    tables = []
    for maximal in (C.TIE_M1_MAXIMAL, C.TIE_M2_MAXIMAL):
        ok = np.zeros(1 << m, dtype=bool)
        for top in maximal:
            for mask in range(1 << m):
                if mask & ~top == 0:
                    ok[mask] = True
        tables.append(ok)
    return Pair("gleichstand", m, tables[0], tables[1], tuple("abcde"), "kanten", costs=tuple(C.TIE_COSTS))


# --- Messreihen ---------------------------------------------------------------------------------------------------------------------------


def run_is_correct(pair: Pair, rounds: list[dict], best: dict[int, int]) -> bool:
    """Alle I_k sind gemeinsam unabhängig, haben k Elemente und die kleinsten Kosten, und das Verfahren geht bis zum Optimum."""
    return len(rounds) == pair.opt + 1 and all(bool(pair.common[r["set"]]) and popcount(r["set"]) == r["k"] and r["cost"] == best[r["k"]] for r in rounds)


def small_weighted_row(n: int, sample: int, seed: int) -> dict:
    """Alle Paare von Matroiden auf n Elementen (bei n = 5 eine Stichprobe), je zwei Kostenvektoren (Werte 0 bis 2 mit vielen Gleichständen, und −2 bis 3):
    die drei Wegwahlen, die Konvexität der Kosten je Elementzahl und (bis n = 4) „extrem gleich kein negativer Kreis“ auf allen gemeinsamen Mengen."""
    rng = np.random.default_rng(seed + n)
    mats = small_matroids(n)
    pairs = [(a, b) for a in mats for b in mats]
    if len(pairs) > sample:
        pairs = [pairs[i] for i in rng.choice(len(pairs), size=sample, replace=False)]
    row = {"n": n, "pairs": len(pairs), "runs": 0, "ok": {v: 0 for v in TIEBREAKS}, "convex": 0, "convex_checked": 0, "common_sets": 0, "extreme": 0, "extreme_agree": 0, "extreme_checked": n <= 4}
    for (ok1, ur1), (ok2, ur2) in pairs:
        pair = Pair("klein", n, ok1, ok2, tuple(str(i) for i in range(n)), "kanten")
        pair.__dict__["ur1"], pair.__dict__["ur2"] = ur1, ur2
        for kind in (0, 1):
            costs = tuple(int(x) for x in (rng.integers(0, 3, n) if kind == 0 else rng.integers(-2, 4, n)))
            pair.costs = costs
            best = best_by_size(pair)
            row["runs"] += 1
            for v in TIEBREAKS:
                row["ok"][v] += run_is_correct(pair, weighted_steps(pair, v), best)
            if kind == 1:
                vals = [best[k] for k in range(pair.opt + 1)]
                diffs = [b - a for a, b in zip(vals, vals[1:])]
                row["convex_checked"] += 1
                row["convex"] += all(d2 >= d1 for d1, d2 in zip(diffs, diffs[1:]))
                if row["extreme_checked"]:
                    for s in np.nonzero(pair.common)[0].tolist():
                        ext = int(cost_table(pair)[s]) == best[popcount(s)]
                        row["common_sets"] += 1
                        row["extreme"] += ext
                        row["extreme_agree"] += ext == is_extreme(pair, s)
    return row


def tie_search(count: int, seed: int) -> dict:
    """Zufallspaare mit 5 Elementen und Kosten aus {0, 1, 2}: wie oft scheitert jede Wegwahl?"""
    rng = np.random.default_rng(seed)
    mats = small_matroids(5)
    out = {"pairs": count, "fail": {v: 0 for v in TIEBREAKS}, "invalid": {v: 0 for v in TIEBREAKS}}
    for _ in range(count):
        (ok1, ur1), (ok2, ur2) = mats[int(rng.integers(len(mats)))], mats[int(rng.integers(len(mats)))]
        pair = Pair("klein", 5, ok1, ok2, tuple(str(i) for i in range(5)), "kanten", costs=tuple(int(x) for x in rng.integers(0, 3, 5)))
        pair.__dict__["ur1"], pair.__dict__["ur2"] = ur1, ur2
        best = best_by_size(pair)
        for v in TIEBREAKS:
            rounds = weighted_steps(pair, v)
            out["fail"][v] += not run_is_correct(pair, rounds, best)
            out["invalid"][v] += any(not pair.common[r["set"]] for r in rounds)
    return out
