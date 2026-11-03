"""AppTest: Hauptansicht, Experimente, Spielwiese, Permalink und PDF (DEMO-PLAYBOOK §3, §5)."""

import os
from pathlib import Path

from streamlit.testing.v1 import AppTest

import gwi_constants as C
import gwi_evaluation as ev
from gwi_pdf_export import build_pdf

APP = str(Path(__file__).resolve().parent.parent / "app.py")
TIMEOUT = int(os.environ.get("APPTEST_TIMEOUT", "300"))
PLAY = "regenbogen_7_8_6"


def _app(params=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=TIMEOUT)
    for key, value in (params or {}).items():
        at.query_params[key] = value
    at.run()
    assert not at.exception, [str(e) for e in at.exception]
    return at


def _texts(at):
    return [m.value for m in list(at.success) + list(at.info) + list(at.warning) + list(at.error)]


def _click_preset(at, name):
    at.sidebar.button(key=f"preset_{name}").click().run()
    assert not at.exception, [str(e) for e in at.exception]


def test_default_shows_the_second_step_and_the_convex_curve():
    at = _app()
    assert any("I_2 = {A–F, A–G} kostet **17**" in t and "seine Länge ist **13**" in t for t in _texts(at))
    assert any("**konvex**" in t and "Zuwächse 4, 13, 25, 35, 74" in t for t in _texts(at))
    assert [m.value for m in at.metric][:4] == ["5", "151", "30", "74"]


def test_step_slider_changes_the_path():
    at = _app()
    at.slider(key=f"k_{PLAY}").set_value(5).run()
    assert not at.exception and any("I_5" in t and "hat 3 Elemente" in t for t in _texts(at))
    at.slider(key=f"k_{PLAY}").set_value(1).run()
    assert not at.exception and any(t.startswith("I_1 = ") and "(vorher" not in t for t in _texts(at))


def test_main_verdict_matches_each_preset():
    expected = {
        "Standardfall (Voreinstellung)": "Zuwächse 4, 13, 25, 35, 74",
        "Zuordnung": "Zuwächse 4, 25, 26, 41, 74",
        "Arboreszenz (fest)": "Zuwächse 1, 1, 3, 5, 6",
        "Drei Farben": "Zuwächse 4, 25, 38",
    }
    at = _app()
    for name, needle in expected.items():
        _click_preset(at, name)
        assert any(needle in t for t in _texts(at)), name


def test_experiment_one_greedy_and_the_series_on_demand():
    at = _app()
    assert any("**bleibt stecken**" in t and "Das Optimum hat 5 Elemente (kleinste Kosten 151)" in t for t in _texts(at))
    assert not any(t.startswith("Von 60 Beispielen") for t in _texts(at))
    at.button(key="greedy_series_run").click().run()
    assert not at.exception and any("Von 60 Beispielen bleibt Greedy nach Kosten bei **25**" in t and "bei **3** teurer" in t for t in _texts(at))
    _click_preset(at, "Zuordnung")
    assert any("Greedy zahlt 13 mehr" in t for t in _texts(at))
    _click_preset(at, "Arboreszenz (fest)")
    assert any("erreicht die größte Elementzahl und die kleinsten Kosten" in t for t in _texts(at))


def test_experiment_two_certificate_and_the_chain():
    at = _app()
    assert any("hat **keinen** Kreis negativer Länge" in t and "nach 3 Tauschkreis(en)" in t for t in _texts(at))
    at.slider(key=f"kc_{PLAY}").set_value(4).run()
    assert not at.exception and any("Die billigste Menge mit 4 Elementen" in t for t in _texts(at))


def test_experiment_three_tie_example_and_the_series_on_demand():
    at = _app()
    assert any("I_2 ist **nicht mehr in beiden Matroiden unabhängig**" in t for t in _texts(at))
    assert not any(t.startswith("Bei 6 000 Zufallspaaren") for t in _texts(at))
    at.button(key="tie_series_run").click().run()
    assert not at.exception and any(t.startswith("Bei 6 000 Zufallspaaren") and "**48**" in t and "**51**" in t for t in _texts(at))


def test_experiment_four_small_pairs_on_demand():
    at = _app()
    assert not any(t.startswith("In allen 15 810 Läufen") for t in _texts(at))
    at.button(key="small_run").click().run()
    assert not at.exception and any(t.startswith("In allen 15 810 Läufen") and "(ohne die Regel: 15 763 von 15 810)" in t and "7 905 geprüften Paaren **konvex**" in t and "21 904 gemeinsamen Mengen" in t for t in _texts(at))
    _click_preset(at, "Zuordnung")
    assert any(t.startswith("In allen 15 810 Läufen") for t in _texts(at))


def test_every_example_runs_without_exception_and_has_a_verdict():
    at = _app()
    for system in C.SYSTEMS:
        at.sidebar.selectbox(key="system_select").set_value(system).run()
        assert not at.exception, (system, [str(e) for e in at.exception])
        texts = _texts(at)
        assert any("**konvex**" in t for t in texts) and any(t.startswith("Greedy nach Kosten") for t in texts) and any("Kreis negativer Länge" in t for t in texts), system


def test_color_slider_changes_the_regenbogen():
    at = _app()
    at.sidebar.slider(key="k_slider").set_value(3).run()
    assert not at.exception and any("Zuwächse 4, 25, 38" in t for t in _texts(at))


def test_playground_branches():
    at = _app()
    assert any("Es gibt einen Kreis negativer Länge" in t for t in _texts(at))
    at.multiselect(key=f"play_i_{PLAY}").set_value(list(range(12))).run()
    assert not at.exception and any("nicht unabhängig" in t for t in _texts(at))
    at.multiselect(key=f"play_i_{PLAY}").set_value([]).run()
    assert not at.exception and any(t.startswith("I hat 0 Elemente") for t in _texts(at))


def test_research_tab_has_the_two_tables_and_the_sources():
    at = _app()
    assert len(at.tabs) == 2 and [t.label for t in at.tabs] == ["Gewichtet: exakt", "Weiteres: ungewichtet und Näherungen"]
    md = " ".join(m.value for m in at.markdown)
    assert "nicht gefunden" in md and "research.chalmers.se" in md and "arxiv.org/abs/2212.00508" in md


def test_permalink_loads_valid_values_and_ignores_invalid_choices():
    at = _app(dict(n="8", seed="3", system="zuordnung", k="4"))
    assert at.sidebar.slider(key="n_slider").value == 8 and at.sidebar.number_input(key="seed_input").value == 3 and at.sidebar.selectbox(key="system_select").value == "zuordnung"
    assert at.sidebar.slider(key="k_slider").value == 4
    bad = _app(dict(n="99", seed="-4", system="gibtsnicht", k="99"))
    assert bad.sidebar.slider(key="n_slider").value == C.N_MAX and bad.sidebar.number_input(key="seed_input").value == 0 and bad.sidebar.selectbox(key="system_select").value == "regenbogen"
    assert bad.sidebar.slider(key="k_slider").value == C.K_MAX


def test_address_line_mirrors_the_settings():
    at = _app(dict(system="zuordnung"))
    assert str(at.query_params["system"]) in ("zuordnung", "['zuordnung']")


def test_pdf_button_makes_a_download():
    at = _app()
    at.button(key="pdf_make").click().run()
    assert not at.exception and "pdf_made" in at.session_state and at.session_state["pdf_made"][1][:4] == b"%PDF"


def test_pdf_builds_for_every_example():
    for key in C.SYSTEMS:
        s = ev.Settings(n=6, seed=2, system=key, k=4)
        assert build_pdf(ev.analyse(s), s)[:4] == b"%PDF", key


def test_extreme_plan_sizes_do_not_raise():
    for n in (C.N_MIN, C.N_MAX):
        for system in ("regenbogen", "zuordnung"):
            at = _app(dict(n=str(n), system=system))
            assert not at.exception, (n, system)
