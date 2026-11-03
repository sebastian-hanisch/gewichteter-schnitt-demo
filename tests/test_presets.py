"""Presets: Vollständigkeit, gültige Werte, Standard-Preset = Standardeinstellungen, und jedes Preset zeigt den Effekt, den sein Hilfetext verspricht."""

import gwi_constants as C
import gwi_evaluation as ev
import gwi_presets as P


def _settings(name):
    return ev.Settings(**C.PRESETS[name])


def test_every_preset_has_help_and_all_keys():
    assert set(C.PRESETS) == set(C.PRESET_HELP)
    for name, preset in C.PRESETS.items():
        assert set(preset) == set(P.PRESET_KEYS), name
        assert C.PRESET_HELP[name]


def test_preset_values_are_inside_the_bounds_and_choices():
    for preset in C.PRESETS.values():
        assert C.N_MIN <= preset["n"] <= C.N_MAX and 0 <= preset["seed"] <= C.SEED_MAX and preset["system"] in C.SYSTEMS and C.K_MIN <= preset["k"] <= C.K_MAX


def test_default_preset_equals_the_default_settings():
    assert ev.Settings(**C.PRESETS["Standardfall (Voreinstellung)"]) == ev.Settings()
    assert [P.SETTING_SPECS[key].default for key in ("system_select", "k_slider")] == [ev.Settings().system, ev.Settings().k]


def test_setting_specs_cover_every_preset_key_and_have_valid_defaults():
    assert set(P.PRESET_KEYS.values()) == set(P.SETTING_SPECS)
    for spec in P.SETTING_SPECS.values():
        assert spec.choices is None or (spec.default in spec.choices and spec.lo in spec.choices and spec.hi in spec.choices)


def test_no_single_regler_change_of_the_default_lands_on_another_preset():
    """Das Layout setzt jeden Regler auf seinen Höchstwert (oder Tiefstwert): das darf kein Preset treffen, sonst bliebe ein Preset markiert."""
    default = dict(C.PRESETS["Standardfall (Voreinstellung)"])
    for state_key, spec in P.SETTING_SPECS.items():
        key = next(k for k, v in P.PRESET_KEYS.items() if v == state_key)
        for value in (spec.hi, spec.lo):
            if value == default[key]:
                continue
            variant = {**default, key: value}
            assert all(variant != preset for preset in C.PRESETS.values()), (state_key, value)


def test_standardfall_help_says_convex_and_longer_paths():
    s = _settings("Standardfall (Voreinstellung)")
    a, rounds = ev.analyse(s), ev.steps_view(s)
    assert ev.is_convex(a.curve) and any(len(r["path"]) > 1 for r in rounds if r["path"])


def test_zuordnung_help_says_hungarian_method_agrees():
    from scipy.optimize import linear_sum_assignment
    import numpy as np
    s = _settings("Zuordnung")
    p, a = ev.pair_of(s), ev.analyse(s)
    big = 10 ** 6
    mat = np.full((s.n, s.n), 10 ** 9, dtype=np.int64)
    for (u, w, _), c in zip(p.inst.edges, p.costs):
        mat[u, w] = min(mat[u, w], c - big)
    r, cidx = linear_sum_assignment(mat)
    assert int(sum(mat[x, y] + big for x, y in zip(r, cidx) if mat[x, y] < 10 ** 8)) == a.curve[-1]


def test_arboreszenz_help_says_chu_liu_edmonds_agrees():
    import networkx as nx
    s = _settings("Arboreszenz (fest)")
    p, a = ev.pair_of(s), ev.analyse(s)
    g = nx.DiGraph()
    for (u, v), c in zip(C.ARBORESCENCE_ARCS, p.costs):
        if v != 0 and (not g.has_edge(u, v) or g[u][v]["weight"] > c):
            g.add_edge(u, v, weight=c)
    assert sum(d["weight"] for _, _, d in nx.minimum_spanning_arborescence(g).edges(data=True)) == a.curve[-1]


def test_three_colors_help_says_three_steps():
    a = ev.analyse(_settings("Drei Farben"))
    assert a.opt == 3 and len(a.curve) == 4
