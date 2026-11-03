"""Gemeinsame Fixtures: kleine Paare von Matroiden mit Kosten, an denen jede Einheit von Hand geprüft wird (DEMO-PLAYBOOK §1b)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from gwi_algorithm import Pair, graphic_table, partition_table, tie_pair  # noqa: E402


@pytest.fixture
def weg():
    """Weg mit drei Kanten als Zuordnung, Elemente a, b, c = 0, 1, 2; M1: Klassen {a, b}, {c}; M2: Klassen {a}, {b, c}; Kosten 3, 1, 3 (minimieren).
    Gemeinsam unabhängig: ∅, a, b, c, {a, c}. Kleinste Kosten je Elementzahl: 0, 1, 6; Zuwächse 1, 5. Weg von {b} nach {a, c}: c → b → a mit der Länge 3 − 1 + 3 = 5."""
    return Pair("weg", 3, partition_table(3, [0, 0, 1]), partition_table(3, [0, 1, 1]), ("a", "b", "c"), "kanten", costs=(3, 1, 3))


@pytest.fixture
def dreieck_farben():
    """Dreieck a, b, c (Knoten 0, 1, 2) mit den Farben 0, 0, 1 und den Kosten 5, 2, 4: Regenbogen-Wald mit 2 Elementen; billigster: {b, c} mit 6; {a, c} kostet 9."""
    return Pair("dreieck", 3, graphic_table(3, [(0, 1), (1, 2), (0, 2)]), partition_table(3, [0, 0, 1]), ("a", "b", "c"), "kanten", costs=(5, 2, 4))


@pytest.fixture
def tie():
    """Das feste Gleichstandsbeispiel: 5 Elemente, Kosten 2, 2, 0, 0, 0, 10 gemeinsame Mengen; Weg-Wahl nur nach Länge führt zu {d, e}, das nicht gemeinsam unabhängig ist."""
    return tie_pair()
