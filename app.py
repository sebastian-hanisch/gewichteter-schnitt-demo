"""Gewichteter Matroid-Schnitt - interaktive Konzept-Demo
Sebastian Hanisch - Operations Research und Machine Learning

Stück 8 der Reihe „Matroide und Submodularität“ (Bereich Kombinatorik). Aufbau und Regeln: DEMO-PLAYBOOK.md (§2).

Lauffähig mit: streamlit run app.py
"""

import streamlit as st

import gwi_constants as C
from gwi_algorithm import elements, find_negative_cycle, tie_pair, worst_of_size
from gwi_evaluation import (
    RESEARCH_EXACT,
    RESEARCH_OTHER,
    RESEARCH_SOURCES,
    Settings,
    analyse,
    cert_rows,
    cert_view,
    chain_rows,
    curve_data,
    edge_costs,
    elemente,
    greedy_series,
    greedy_series_table,
    greedy_view,
    pair_of,
    play_view,
    round_groups,
    round_rows,
    small_rows,
    small_table,
    steps_view,
    tie_rows,
    tie_series,
    tie_view,
    verdict_cert,
    verdict_curve,
    verdict_greedy,
    verdict_greedy_series,
    verdict_play,
    verdict_small,
    verdict_step,
    verdict_tie,
    verdict_tie_series,
    zahl,
)
from gwi_layout import dunkles_design, kopf_css
from gwi_pdf_export import build_pdf
from gwi_presets import bounds, init_session_state_defaults, load_permalink_settings, randomize_seed, sidebar_presets, sync_query_params
from gwi_visualization import build_cost_curve, build_figure

st.set_page_config(page_title="Gewichteter Matroid-Schnitt – Sebastian Hanisch", layout="wide")


@st.cache_data(show_spinner="Tabellen der zwei Matroide aufbauen …")
def _analysis(settings):
    return analyse(settings)


@st.cache_data(show_spinner=False)
def _steps(settings):
    return steps_view(settings)


@st.cache_data(show_spinner=False)
def _greedy(settings):
    return greedy_view(settings)


@st.cache_data(show_spinner="Pläne durchrechnen (einige Sekunden) …")
def _greedy_series(system):
    return greedy_series(system)


@st.cache_data(show_spinner=False)
def _cert(settings, k):
    return cert_view(settings, steps_view(settings), k)


@st.cache_data(show_spinner=False)
def _tie():
    return tie_view()


@st.cache_data(show_spinner="6 000 Zufallspaare durchrechnen (einige Sekunden) …")
def _tie_series():
    return tie_series()


@st.cache_data(show_spinner="Alle Paare bis 5 Elemente durchrechnen (einige Sekunden) …")
def _small():
    return small_rows()


@st.cache_data(show_spinner=False)
def _play(settings, mask):
    return play_view(settings, mask)


# Fester Kopf: nur der Titel bleibt beim Scrollen oben (Stylesheet in gwi_layout.py).
st.html(kopf_css(dunkles_design()))
with st.container(key="kopf"):
    st.title("⚖️ Gewichteter Matroid-Schnitt")
st.markdown(
    """
Stück 7 suchte die **größte** Menge, die in zwei Matroiden unabhängig ist. Jetzt hat jedes Element **Kosten**, und gesucht ist zu jeder Elementzahl k die **billigste** gemeinsame Menge I_k. Der Austauschgraph bleibt derselbe; jedes Element bekommt eine **Länge**: **+Kosten** außerhalb von I, **−Kosten** in I. Der **kürzeste Weg** von den Quellen zu den Senken (bei gleicher Länge der mit den wenigsten Knoten) macht aus I_k das billigste I_{k+1}. Weil Längen negativ sind, nimmt man **Bellman–Ford**. Das **Zertifikat** ist: kein Kreis negativer Länge. Bei Zuordnung und Arboreszenz kommt dasselbe heraus wie bei der **Ungarischen Methode** und bei **Chu-Liu/Edmonds**.

Dies ist das **achte Stück** der Reihe „Matroide und Submodularität“. Weiter unten: vier Experimente (🔬), eine **Spielwiese**, der Tab **📚 Stand der Forschung**, **🚧 Wo die Annahmen enden** und der Expander **📐 Mathematische Formulierung**.
"""
)

with st.expander("So hängt es zusammen", expanded=True):
    st.markdown(
        """
1. **Aufgabe:** Zu jeder Elementzahl k die gemeinsame unabhängige Menge I_k mit den kleinsten Kosten (Gewichte maximieren geht mit Kosten = −Gewicht).
2. **Länge im Austauschgraphen:** Element außerhalb von I: +Kosten; Element in I: −Kosten. Die Länge eines Weges ist die Summe der Längen seiner Elemente.
3. **Verbessern:** Der kürzeste Weg von X1 nach X2 (bei gleicher Länge der mit den wenigsten Knoten) wird mit I vertauscht (symmetrische Differenz): I_{k+1} = I_k Δ Weg, mit genau den kleinsten Kosten unter allen gemeinsamen Mengen mit k + 1 Elementen.
4. **Zertifikat:** I hat die kleinsten Kosten unter allen gemeinsamen Mengen derselben Größe genau dann, wenn der Austauschgraph zu I **keinen Kreis negativer Länge** hat. Hat er einen, verbessert der Tausch entlang des Kreises die Kosten.
5. **Gleichstand:** Ohne die Knotenzahl-Regel kann ein Umweg mit Abkürzung gewählt werden; dann ist das Ergebnis nicht mehr in beiden Matroiden unabhängig (Experiment 3).
        """
    )

st.caption("🔗 Die Adresszeile oben spiegelt Ihre aktuelle Konfiguration wider – einfach kopieren, um ein Szenario zu teilen.")

load_permalink_settings()
init_session_state_defaults()

with st.sidebar:
    sidebar_presets()  # Schnellstart oben, das aktive Preset ist hervorgehoben
    st.header("⚙️ Einstellungen")
    st.markdown("**Beispiel**")
    system = st.selectbox("Zwei Matroide", C.SYSTEMS, key="system_select", format_func=C.SYSTEM_NAMES.get,
                          help="Regenbogen-Spannbaum und Zuordnung liegen auf dem Leitungsnetz (Kosten = Kosten der Leitungen); die Arboreszenz ist ein festes Beispiel mit 12 Bögen und Kosten aus dem Seed.")
    st.markdown("**Plan**")
    n = st.slider("Standorte (mit Depot A)", *bounds("n_slider"), key="n_slider", help="Wie viele Standorte der Plan hat. Bis 9 (16 mögliche Leitungen). Die Arboreszenz hängt nicht vom Plan ab.")
    seed = st.number_input("Zufalls-Seed des Plans", *bounds("seed_input"), key="seed_input", step=1, help="Bestimmt Plan und Farben; bei der Arboreszenz die Kosten der Bögen.")
    st.button("🎲 Neuen Plan generieren", width="stretch", on_click=randomize_seed)
    k = st.slider("Kabelfarben (Regenbogen)", *bounds("k_slider"), key="k_slider", help="Wie viele Farben die Leitungen haben. Mit n − 1 Farben kann es einen Spannbaum in lauter verschiedenen Farben geben.")

sync_query_params({"n_slider": int(n), "seed_input": int(seed), "system_select": system, "k_slider": int(k)})

settings = Settings(int(n), int(seed), system, int(k))
a = _analysis(settings)
pair = pair_of(settings)
rounds = _steps(settings)
play_id = f"{system}_{settings.n}_{settings.seed}_{settings.k}"
m1_name, m2_name = C.MATROID_NAMES[system]

# --- Kostenkurve und Weg ---------------------------------------------------------------------------------------------------------------------

st.markdown("## 🎯 Kostenkurve und Weg")
st.caption(f"{C.SYSTEM_NAMES[system]}: M1 = {m1_name}; M2 = {m2_name}. {a.m} Elemente, {zahl(a.n_common)} gemeinsame unabhängige Mengen; Kosten der Elemente: {', '.join(str(c) for c in a.costs)}.")
mc1, mc2, mc3, mc4 = st.columns(4)
mc1.metric("Größte Elementzahl", a.opt)
mc2.metric("Kleinste Kosten dabei", zahl(a.curve[-1]))
mc3.metric("Ein Schritt kostet im Mittel", zahl(round(a.curve[-1] / a.opt)) if a.opt else "–")
mc4.metric("Zuwachs im letzten Schritt", zahl(a.curve[-1] - a.curve[-2]) if a.opt else "–")
if a.opt >= 1:
    kk = st.slider("Elementzahl k", 1, a.opt, min(2, a.opt), key=f"k_{play_id}", help="Welche Menge I_k gezeigt wird und der Weg, der von I_{k−1} zu ihr geführt hat.")
else:
    kk = 0
col_a, col_b = st.columns(2)
with col_a:
    groups = round_groups(a, rounds, kk) if kk else [("I_0", [], C.COLOR_SET)]
    st.plotly_chart(build_figure(pair, groups, edge_text=edge_costs(a, groups)), width="stretch", key="map_step")
    st.caption("Blaugrün: die billigste Menge I_k. Orange: der Weg von I_{k−1} nach I_k. Die Zahlen an den Elementen sind ihre Kosten.")
with col_b:
    cd = curve_data(a)
    st.plotly_chart(build_cost_curve(cd["ks"], cd["costs"], cd["deltas"], kk), width="stretch", key="curve")
    st.caption("Linie: kleinste Kosten einer gemeinsamen Menge mit k Elementen. Balken: Zuwachs je Schritt (wächst: konvex).")
if kk:
    with st.expander("Der Austauschgraph bei diesem Schritt (Längen und kürzeste Entfernungen)"):
        st.dataframe(round_rows(a, rounds, kk), hide_index=True, width="stretch")

if st.button("📄 PDF des aktuellen Beispiels erstellen", key="pdf_make"):
    st.session_state["pdf_made"] = (settings, build_pdf(a, settings))
made = st.session_state.get("pdf_made")
if made and made[0] == settings:
    st.download_button("⬇️ PDF herunterladen", data=made[1], file_name="gewichteter-matroid-schnitt.pdf", mime="application/pdf", key="pdf_download")

# --- Kernfrage -----------------------------------------------------------------------------------------------------------------------------

st.markdown("## ❓ Kernfrage: Wie wird der Austauschpfad billig?")
if kk:
    kind_v, text_v = verdict_step(a, rounds, kk)
    getattr(st, kind_v)(text_v)
kind_v, text_v = verdict_curve(a, rounds)
getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Experimente ---------------------------------------------------------------------------------------------------------------------------

st.subheader("🔬 Experiment 1: Greedy nach Kosten")
st.caption("Die billigste Leitung zuerst nehmen, solange die Menge in beiden Matroiden unabhängig bleibt: Erreicht das die größte Elementzahl, und wie viel zahlt es mehr?")
gv = _greedy(settings)
g1, g2 = st.columns(2)
with g1:
    st.markdown("**Greedy nach Kosten**")
    gg = [("Greedy-Menge", elements(gv["set"], a.m), C.COLOR_GREEDY)]
    st.plotly_chart(build_figure(pair, gg, height=300, edge_text=edge_costs(a, gg)), width="stretch", key="map_greedy")
with g2:
    st.markdown("**Optimum**")
    oo = [("billigste Menge mit größter Elementzahl", elements(rounds[-1]["set"], a.m), C.COLOR_OPT)]
    st.plotly_chart(build_figure(pair, oo, height=300, edge_text=edge_costs(a, oo)), width="stretch", key="map_greedy_opt")
kind_v, text_v = verdict_greedy(a, gv)
getattr(st, kind_v)(text_v)
label = "📊 Messreihe über 20 Pläne je Größe (6 bis 8 Standorte)" if system != "arboreszenz" else "📊 Messreihe über 30 Kostenvektoren"
if st.button(label, key="greedy_series_run"):
    st.session_state["greedy_series_done"] = True
if st.session_state.get("greedy_series_done"):
    rows = _greedy_series(system)
    st.dataframe(greedy_series_table(system, rows), hide_index=True, width="stretch")
    kind_v, text_v = verdict_greedy_series(system, rows)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 2: Das Zertifikat – kein Kreis negativer Länge")
st.caption("Zu jedem k hat die billigste Menge I_k keinen Kreis negativer Länge. Die teuerste gemeinsame Menge derselben Größe hat einen; der Tausch entlang des Kreises senkt die Kosten, bis keiner mehr da ist.")
st.dataframe(cert_rows(a, rounds), hide_index=True, width="stretch")
if a.opt >= 1:
    kc = st.slider("Elementzahl für die teuerste Menge", 1, a.opt, min(2, a.opt), key=f"kc_{play_id}")
    cv = _cert(settings, kc)
    c1, c2 = st.columns(2)
    with c1:
        cyc = cv["chain"][0]["cycle"] if cv["chain"] else []
        cg = [("teuerste Menge", elements(cv["worst"], a.m), C.COLOR_GREEDY)] + ([("Tauschkreis", cyc, C.COLOR_CYCLE)] if cyc else [])
        st.plotly_chart(build_figure(pair, cg, height=320, edge_text=edge_costs(a, cg)), width="stretch", key="map_cert")
        st.caption("Orange: die teuerste gemeinsame Menge mit k Elementen; rot: die Elemente des ersten Kreises negativer Länge.")
    with c2:
        st.markdown("**Tauschkreise bis zur billigsten Menge**")
        st.dataframe(chain_rows(a, cv), hide_index=True, width="stretch")
    kind_v, text_v = verdict_cert(a, cv)
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 3: Gleichstand – wozu die Knotenzahl-Regel gut ist")
st.caption("Ein festes Beispiel mit 5 Elementen (Kosten 2, 2, 0, 0, 0; M1 mit einer Schleife a): Mehrere Wege haben dieselbe Länge. Drei Wegwahlen nebeneinander.")
tv = _tie()
st.dataframe(tie_rows(tv), hide_index=True, width="stretch")
kind_v, text_v = verdict_tie(tv)
getattr(st, kind_v)(text_v)
if st.button("📊 Wie oft bei Zufallspaaren? (6 000 Paare mit 5 Elementen)", key="tie_series_run"):
    st.session_state["tie_series_done"] = True
if st.session_state.get("tie_series_done"):
    kind_v, text_v = verdict_tie_series(_tie_series())
    getattr(st, kind_v)(text_v)

st.subheader("🔬 Experiment 4: Alle kleinen Paare")
st.caption("Alle Paare von Matroiden auf 2 bis 4 Elementen (und 3 000 Zufallspaare auf 5), je zwei Kostenvektoren (0 bis 2 mit vielen Gleichständen, und −2 bis 3): das Verfahren gegen die Aufzählung, die Konvexität und „extrem gleich kein negativer Kreis“.")
if st.button("📊 Alle Paare prüfen (einige Sekunden)", key="small_run"):
    st.session_state["small_done"] = True
if st.session_state.get("small_done"):
    rows = _small()
    st.dataframe(small_table(rows), hide_index=True, width="stretch")
    kind_v, text_v = verdict_small(rows)
    getattr(st, kind_v)(text_v)

st.markdown("---")

# --- Spielwiese ----------------------------------------------------------------------------------------------------------------------------

st.subheader("🛠️ Spielwiese: Eine eigene gemeinsame Menge verbessern")
st.caption("Wählen Sie eine Menge I. Ist sie in M1 und M2 unabhängig, zeigt die App, ob der Austauschgraph einen Kreis negativer Länge hat, und verbessert sie Kreis für Kreis bis zu den kleinsten Kosten.")
default_i = elements(worst_of_size(pair, min(2, a.opt)), a.m) if a.opt else []
sel = st.multiselect("Menge I", list(range(a.m)), default=default_i, key=f"play_i_{play_id}", format_func=lambda x: a.labels[x])
pv = _play(settings, sum(1 << x for x in sel))
kind_v, text_v = verdict_play(a, pv)
getattr(st, kind_v)(text_v)
if sel and pv["chain"] is not None:
    gpl = [("gewählte Menge I", sel, C.COLOR_SET)]
    if pv["chain"]:
        gpl.append(("erster Tauschkreis", pv["chain"][0]["cycle"], C.COLOR_CYCLE))
    st.plotly_chart(build_figure(pair, gpl, height=320, edge_text=edge_costs(a, gpl)), width="stretch", key="map_play")
    if pv["chain"]:
        st.dataframe(chain_rows(a, {"worst": pv["mask"], "chain": pv["chain"]}), hide_index=True, width="stretch")

st.markdown("---")

# --- Stand der Forschung ----------------------------------------------------------------------------------------------------------------------

st.subheader("📚 Stand der Forschung")
st.caption("Eine Literaturübersicht, **nicht nachgebaut** und nicht gegen die Originalarbeiten geprüft (Quellen: Suchauszüge und Zusammenfassungen). Oraklemodell: Unabhängigkeitsorakel (Frage „ist S unabhängig?“) oder Rangorakel (Frage „welchen Rang hat S?“).")
tab1, tab2 = st.tabs(["Gewichtet: exakt", "Weiteres: ungewichtet und Näherungen"])
with tab1:
    st.dataframe(list(RESEARCH_EXACT), hide_index=True, width="stretch")
    st.markdown("Ein exaktes gewichtetes Verfahren aus den Jahren 2024 bis 2026 mit besseren Schranken als Tu (2022) wurde bei der Recherche **nicht gefunden**; ob es eines gibt, ist hier offen.")
with tab2:
    st.dataframe(list(RESEARCH_OTHER), hide_index=True, width="stretch")
st.markdown("Quellen: " + "; ".join(f"[{name}]({url})" for name, url in RESEARCH_SOURCES) + ".")

st.markdown("---")

# --- Grenzen -------------------------------------------------------------------------------------------------------------------------------

st.subheader("🚧 Wo die Annahmen enden")
st.markdown(
    """
| Annahme | Was passiert, wenn sie verletzt ist (wer setzt an) |
|---|---|
| **Zwei Matroide, nicht drei** | Der gewichtete Schnitt von drei oder mehr Matroiden ist NP-schwer; das Verfahren gilt für genau zwei. **(nicht in dieser Reihe)** |
| **Ganzzahlige Kosten** | Die Demo rechnet mit ganzen Zahlen; Bellman–Ford verträgt auch Brüche, aber die Tests und Gleichstände sind für ganze Zahlen angelegt. **(Stück 8)** |
| **Kleine Grundmengen (höchstens 16 Elemente)** | Das Optimum je k wird aus allen Teilmengen berechnet und mit dem Verfahren verglichen; bei großen Matroiden gibt es nur ein Orakel, dann zählt die Zahl der Anfragen (siehe Tab Stand der Forschung). **(Stück 8)** |
| **Bellman–Ford auf dem ganzen Austauschgraphen** | Das gewichtete Verfahren braucht je Runde alle Pfeile (Orakelaufrufe wie das naive Verfahren aus Stück 7); ob eine faule Variante mit weniger Aufrufen möglich ist, wurde nicht untersucht. **(Stück 8)** |
| **Die Beispiele sind klein und zufällig** | Greedy-Anteile und Messreihen gelten für die gezeigten Pläne (Seeds 0 bis 19) und Kostenvektoren; die Gleichstandsfälle sind selten (unter 1 % der Zufallspaare). **(Stück 8)** |
| **Kein Zertifikat über Gewichtsaufspaltung** | Das Zertifikat ist „kein Kreis negativer Länge“; die Gewichtsaufspaltung von Frank, die eine Optimalitätsaussage ohne Austauschgraph gibt, wird nur erwähnt. **(nicht gebaut)** |
| **Vereinigung statt Schnitt** | Wie viele disjunkte Strukturen in ein Matroid passen, ist die Vereinigung; sie wird auf den Schnitt zurückgeführt. **(Stück 9)** |
"""
)

st.markdown("---")

with st.expander("📐 Mathematische Formulierung"):
    st.markdown(
        r"""
**Gegeben** zwei Matroide $M_1, M_2$ auf $E$ und Kosten $c : E \to \mathbb{Z}$. Gesucht ist zu jedem $k$ eine gemeinsame unabhängige Menge $I_k$ mit $\lvert I_k \rvert = k$ und kleinstem $c(I_k) = \sum_{e \in I_k} c(e)$. (Gewichte $w$ maximieren: $c = -w$.)

| Symbol | Bedeutung |
|---|---|
| $D(I)$ | Austauschgraph zu $I$ wie in Stück 7 mit Quellen $X_1$ und Senken $X_2$ |
| $\ell(x)$ | Länge von $x$: $+c(x)$ für $x \notin I$, $-c(y)$ für $y \in I$ |
| $\ell(P)$ | Länge eines Weges oder Kreises: Summe der $\ell$ über seine Elemente |
| $I_k$ | billigste gemeinsame Menge mit $k$ Elementen („extrem“) |

**Verbessern.** Ist $I = I_k$ extrem, so ist für einen Weg $P$ von $X_1$ nach $X_2$ mit kleinster Länge $\ell(P)$ und unter diesen mit den wenigsten Knoten $I_{k+1} = I \,\triangle\, V(P)$ extrem, und $c(I_{k+1}) = c(I_k) + \ell(P)$. Gibt es keinen Weg, ist $I_k$ die größte gemeinsame Menge.

**Zertifikat.** $I$ ist extrem (kleinste Kosten unter allen gemeinsamen Mengen mit $\lvert I \rvert$ Elementen) genau dann, wenn $D(I)$ keinen Kreis negativer Länge hat. Hat $D(I)$ einen, so liefert ein Kreis negativer Länge mit den wenigsten Pfeilen $C$ die bessere Menge $I \triangle V(C)$ derselben Größe.

**Konvexität.** Die Wegelängen wachsen: $c(I_{k+1}) - c(I_k) \ge c(I_k) - c(I_{k-1})$; die Funktion $k \mapsto c(I_k)$ ist konvex.

**Gleichstand.** Unter den Wegen kleinster Länge muss einer mit den wenigsten Knoten gewählt werden; ein Weg mit einer Abkürzung darf nicht genommen werden, sonst ist $I \triangle V(P)$ nicht mehr gemeinsam unabhängig.

**Literatur.** Die Längen $+c$ und $-c$ und die Knotenzahl-Regel stehen bei Schrijver (Satz 41.7, nach Zusammenfassungen; die Originalarbeiten sind nicht eingesehen); Frank (1981) gibt die Gewichtsaufspaltung. Konvexität und „extrem gleich kein negativer Kreis“ sind hier an allen kleinen Paaren nachgerechnet, nicht aus einer Quelle übernommen.
        """
    )

st.markdown("---")
st.caption(
    "Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – "
    "Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). "
    "Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html)."
)
