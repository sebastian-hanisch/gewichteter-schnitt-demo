# Gewichteter Matroid-Schnitt – der billige Weg – Streamlit-Demo

<!-- TODO nach dem Deploy: direkt hierher den Live-Link setzen (Leerzeile davor und danach):
**[→ Demo live ausprobieren](https://sebastianhanisch-gewichteter-schnitt-demo.streamlit.app/)** -->

Achtes Stück der Reihe **Matroide und Submodularität** (Bereich Kombinatorik) in der „Konzepte“-Reihe für die Website „Sebastian Hanisch – Operations Research und Machine Learning“. Die Demo macht aus dem Matroid-Schnitt von Stück 7 den **gewichteten**: Jedes Element hat Kosten, gesucht ist zu jeder Elementzahl k die **billigste** gemeinsame unabhängige Menge I_k. Im Austauschgraphen bekommt jedes Element außerhalb von I die Länge **+Kosten**, jedes Element in I die Länge **−Kosten**; der **kürzeste Weg** (Bellman–Ford, bei gleicher Länge der mit den wenigsten Knoten) macht aus I_k das billigste I_{k+1}. Das **Zertifikat** ist „kein Kreis negativer Länge“. Dazu der Tab **Stand der Forschung** als Literaturübersicht (nicht nachgebaut).

**Einordnung in die Reihe:** Nachfolger von [matroid-schnitt-demo](../matroid-schnitt-demo) (Stück 7: ungewichtet), [dualmatroid-demo](../dualmatroid-demo) (Stück 6), [greedy-optimalitaet-demo](../greedy-optimalitaet-demo) (Stück 5), [rang-basen-kreise-demo](../rang-basen-kreise-demo) (Stück 4), [matroid-demo](../matroid-demo) (Stück 3), [unabhaengigkeitssystem-demo](../unabhaengigkeitssystem-demo) (Stück 2) und [greedy-austausch-demo](../greedy-austausch-demo) (Stück 1). Die drei Beispiele sind dieselben wie in Stück 7, jetzt mit Kosten. Stück 9 behandelt die Vereinigung.

## Warum dieses Problem

Fast jede Anwendung des Matroid-Schnitts hat Kosten: den **billigsten** Regenbogen-Spannbaum, die **billigste** Zuordnung, die **billigste** Arboreszenz. Greedy nach Kosten reicht nicht, und der ungewichtete Weg aus Stück 7 ist nicht billig. Offen ist, wie man den Weg billig macht. Die Antwort sind Längen im Austauschgraphen: Was in I steht, wird bei einem Tausch frei und spart seine Kosten; was dazukommt, kostet. Der Weg mit der kleinsten Länge ist der billigste.

## Befunde und Korrekturen gegenüber dem Plan

- **Die Wegwahl ohne Knotenzahl scheitert häufiger als in der Messung vor dem Bau:** Damals war „falsch“ nur ein zu hohes Gewicht; die App prüft strenger, dass jedes I_k auch **in beiden Matroiden unabhängig** ist. Dann scheitert die Wegwahl nur nach der Länge schon bei n = 4 in 16 von 9 248 Läufen und bei n = 5 in 31 (Erzeugungsreihenfolge) bzw. 30 (umgekehrt) von 6 000; bei 6 000 Zufallspaaren mit Kosten aus {0, 1, 2} sind es 48 und 51 Paare (rund 0,8 %). Jedes Mal ist das Ergebnis eine Menge, die **nicht mehr gemeinsam unabhängig ist**: der Weg war ein Umweg mit einer Abkürzung. Mit der Knotenzahl-Regel gibt es **keinen** Fehler.
- **Festes Gleichstandsbeispiel:** 5 Elemente (a bis e), Kosten 2, 2, 0, 0, 0, a eine Schleife in M1, aus der Suche über 12 000 Zufallspaare (kleinste Zahl gemeinsamer Mengen: 10).
- **Greedy nach Kosten scheitert hier überwiegend an der Elementzahl,** nicht an den Kosten (Experiment 1).
- **`scipy` und `networkx` nur in den Tests:** `scipy.optimize.linear_sum_assignment` (Ungarische Methode) und `networkx.minimum_spanning_arborescence` (Chu-Liu/Edmonds) sind die Gegenproben; zur Laufzeit reichen numpy und plotly.
- **Präfix `gwi_`** (nicht `gws_`: das ist in `gewichtete-summe-demo` belegt), Port 9348.
- **Kostenkurve statt „Gewichte maximieren“:** Alles läuft mit Kosten (kleinste); Gewichte maximieren ist dasselbe mit Kosten = −Gewicht.

## Modell

Dieselben drei Beispiele wie in Stück 7: **Regenbogen-Spannbaum** (M1 = Wald, M2 = höchstens eine Leitung je Farbe, 2 bis 8 Farben), **Zuordnung** (zwei Partitionsmatroide: je unterem und je oberem Endpunkt höchstens eine Leitung) und **Arboreszenz** (festes Beispiel mit 6 Knoten und 12 Bögen). Die **Kosten** sind die Leitungskosten des Plans (Entfernung mal 100, ganzzahlig); bei der Arboreszenz ganze Zahlen von 1 bis 9, deterministisch aus dem Seed. Formeln und Beweisskizzen: Expander „📐 Mathematische Formulierung“ in der App.

## Methodik

- **Länge im Austauschgraphen:** +Kosten für Elemente außerhalb von I, −Kosten für Elemente in I (`node_lengths`).
- **Kürzester Weg:** Bellman–Ford auf dem ganzen Austauschgraphen, Ordnung (Länge, Knotenzahl); die Wegwahl „nur die Länge“ gibt es in zwei Varianten (Pfeile in Erzeugungsreihenfolge, umgekehrt) für Experiment 3 (`shortest_path`, `weighted_steps`).
- **Zertifikat und Tauschkreis:** ein Kreis negativer Länge mit den wenigsten Pfeilen, gesucht über geschlossene Wege mit 2, 3, … Pfeilen; der Tausch entlang des Kreises senkt die Kosten (`find_negative_cycle`, `improve_to_extreme`).
- **Gegenprobe:** die Aufzählung aller gemeinsamen Mengen je Elementzahl (`best_by_size`).
- **Greedy nach Kosten:** billigste Leitung zuerst, solange die Menge in beiden Matroiden unabhängig bleibt (`greedy_by_cost`).
- **Alle kleinen Paare:** alle Paare beschrifteter Matroide mit 2 bis 4 Elementen und 3 000 Zufallspaare mit 5, je zwei Kostenvektoren (`small_weighted_row`).

## Befunde (gemessen, keine Behauptungen)

Alle Zahlen stehen in `tests/test_claims.py` und werden dort mit den Funktionen der App nachgerechnet. Plan: 7 Standorte, 12 mögliche Leitungen, Seed 8 (die Arboreszenz ist fest und hängt nur vom Seed ab, über die Kosten der Bögen).

| Beispiel | größte Elementzahl | kleinste Kosten für k = 0, 1, 2, … | Zuwächse | Greedy nach Kosten |
|---|---|---|---|---|
| Regenbogen-Spannbaum mit 6 Farben | 5 | 0, 4, 17, 42, 77, 151 | 4, 13, 25, 35, 74 | 4 Elemente für 77: bleibt stecken |
| Regenbogen mit 3 Farben | 3 | 0, 4, 29, 67 | 4, 25, 38 | 3 Elemente für 67: optimal |
| Zuordnung | 5 | 0, 4, 29, 55, 96, 170 | 4, 25, 26, 41, 74 | 4 Elemente für 109 (bei 4 Elementen wären 96 möglich): bleibt stecken |
| Arboreszenz (fest) | 5 | 0, 1, 2, 5, 10, 16 | 1, 1, 3, 5, 6 | 5 Elemente für 16: optimal |

| Frage | Befund |
|---|---|
| **Alle Paare und Läufe** (2 bis 4 Elemente alle, 5 Elemente 3 000 Zufallspaare; je zwei Kostenvektoren: 50, 512, 9 248, 6 000 Läufe, zusammen **15 810**) | Mit der Knotenzahl-Regel liefert das Verfahren in **allen 15 810** Läufen für **jede** Elementzahl die billigste gemeinsame Menge; ohne die Regel nur in **15 763** (Pfeile in Erzeugungsreihenfolge) bzw. **15 764** Läufen (umgekehrt). |
| **Konvexität** | Die kleinsten Kosten je Elementzahl sind bei allen **7 905** geprüften Paaren konvex. |
| **Extrem gleich kein negativer Kreis** (alle gemeinsamen Mengen aller Paare bis 4 Elemente) | Bei **21 904 von 21 904** gemeinsamen Mengen (44, 695, 21 165) stimmen die zwei Aussagen überein. |
| **Gleichstandsbeispiel** (5 Elemente, Kosten 2, 2, 0, 0, 0) | Mit der Regel: I_0 bis I_3 gemeinsam unabhängig, Kosten 0, 0, 0, 2. Nur nach der Länge: Lauf endet bei 2 Elementen mit {d, e}, das **nicht** in beiden Matroiden unabhängig ist. |
| **Gleichstand bei Zufallspaaren** (6 000 Paare mit 5 Elementen, Kosten aus {0, 1, 2}) | Mit Knotenzahl-Regel **0** Fehler, nur nach der Länge **48** (Pfeile in Erzeugungsreihenfolge) bzw. **51** Paare (umgekehrt); jedes Mal ist die erzeugte Menge nicht gemeinsam unabhängig. |
| **Greedy nach Kosten auf Plänen** (20 Pläne je Größe, n = 6, 7, 8) | Regenbogen mit n − 1 Farben: bleibt vor der größten Elementzahl stecken bei **7, 9, 9** Plänen; bei gleicher Größe teurer bei 1 von 13, 0 von 11, 2 von 11. Zuordnung: stecken bei **11, 10, 15**; teurer bei 2 von 9, 2 von 10, 1 von 5. Arboreszenz (30 Kostenvektoren): stecken bei **4**, teurer bei 2 von 26. |
| **Gegenproben** (Tests) | Die Zuordnung hat gleiche Elementzahl und **gleiche Kosten** wie die Ungarische Methode bei **60 von 60** Plänen (n = 6, 7, 8; Seeds 0 bis 19); die Arboreszenz gleiche Kosten wie Chu-Liu/Edmonds bei **30 von 30** Kostenvektoren. |
| **Tauschkreis** | Bei der teuersten gemeinsamen Menge mit 2 Elementen im Standardfall (Kosten 95, billigste 17) hat der Austauschgraph einen Kreis der Länge −44 mit 2 Elementen; nach 3 Tauschkreisen sind die Kosten bei 17. |

## Ehrliche Grenzen

- **Zwei Matroide, ganzzahlige Kosten.** Drei Matroide sind NP-schwer; die Gleichstände sind für ganze Zahlen angelegt.
- **Kleine Grundmengen.** Höchstens 16 Elemente; das Optimum je Elementzahl wird aus allen Teilmengen berechnet.
- **Bellman–Ford auf dem ganzen Austauschgraphen.** Je Runde alle Pfeile (Orakelaufrufe wie das naive Verfahren aus Stück 7); ob eine faule Variante mit weniger Aufrufen geht, ist nicht untersucht.
- **Beispiele auf einem Plan** und Messreihen über Seeds 0 bis 19 bzw. 30 Kostenvektoren; die Gleichstandsfälle sind selten (unter 1 % der Zufallspaare), das feste Beispiel ist aus einer Suche, nicht minimiert.
- **Zertifikat über den negativen Kreis,** nicht über die Gewichtsaufspaltung (Frank), die nur erwähnt wird.
- **Der Tab Stand der Forschung ist eine Übersicht aus Suchauszügen,** nicht gegen die Originalarbeiten geprüft und nicht nachgebaut; ein exaktes gewichtetes Verfahren aus 2024 bis 2026 mit besseren Schranken als Tu (2022) wurde nicht gefunden.
- **Quellen nur als Auszüge** (Schrijver Satz 41.7, Frank, Brezovec–Cornuéjols–Glover, Huang–Kakimura–Kamiyama, Tu, Terao, Dudeja–Grilnberger): Konvexität und „extrem gleich kein negativer Kreis“ sind hier an allen kleinen Paaren nachgerechnet, nicht aus einer Quelle übernommen.

## Verifikation

- **Kern:** Längen, Kosten, Bellman–Ford (Entfernungen und Knotenzahlen), Tauschkreis, Greedy nach Kosten und das Gleichstandsbeispiel gegen Handrechnung am Weg mit drei Kanten (Kosten 3, 1, 3) und am Dreieck mit zwei gleichfarbigen Kanten (`tests/conftest.py`, `tests/test_algorithm.py`); Randfälle: ein Element, Nullmatroid, gleiche, null und negative Kosten, Reglergrenzen, alle Zweige der Spielwiese (`tests/test_edge_cases.py`).
- **Orakel** (`tests/test_oracle_gewichteter_schnitt.py`): Zuordnung gegen `scipy.optimize.linear_sum_assignment` (60 Pläne), Arboreszenz gegen `networkx.minimum_spanning_arborescence` (30 Kostenvektoren), Regenbogen gegen eine Aufzählung mit `networkx`-Wald; kürzester Weg (Länge und Knotenzahl) gegen alle einfachen Wege in `networkx` auf dem explizit gebauten Austauschgraphen; „extrem gleich kein negativer Kreis“ gegen die Aufzählung; der Tauschkreis ist ein Kreis, hat negative Länge und senkt die Kosten; Konvexität gegen die Aufzählung; Matroidzahlen 2, 5, 16, 68, 406.
- **Eigenschaften** (`tests/test_properties.py`): jedes I_k ist gemeinsam unabhängig, hat k Elemente und die kleinsten Kosten; Kosten je k konvex, jeder Zuwachs gleich der Wegelänge; Wege wechseln zwischen außen und innen; Konstante addieren verschiebt die Kurve um k·c, Verdoppeln verdoppelt sie; Vertauschen der Matroide und Umbenennen ändern die Kurve nicht; die Verbesserung der teuersten Menge endet bei den kleinsten Kosten mit fallenden Kosten; der gefundene Kreis hat die wenigsten Pfeile unter allen negativen Kreisen.
- **Verdikte und Presets:** jeder Zweig und jede Zahl der Verdikte an handgesetzten Werten; jedes Preset zeigt den versprochenen Effekt (inklusive der Gegenproben); kein einzelner Reglerwechsel trifft ein anderes Preset.
- **Zahlen aus dieser README:** `tests/test_claims.py`.
- **Oberfläche:** AppTest-Rauchtest (jeder Button, jeder Regler an den Grenzen), Hauptansicht, Experimente, Tab, Spielwiese, Permalink, PDF; Layout (Kopf, Schnellstart, Hervorhebung) und Footer.
- **Umfang:** siehe `pytest --collect-only -q tests`.

## Dateistruktur

| Datei | Inhalt |
|---|---|
| `app.py` | Streamlit-Oberfläche: Kostenkurve und Weg, Kernfrage, vier Experimente, Spielwiese, Tab Stand der Forschung, Grenzen, Formeln |
| `gwi_constants.py` | Reglergrenzen, die drei Beispiele, das feste Beispiel Arboreszenz, das Gleichstandsbeispiel, Farben, Presets |
| `gwi_scenario.py` | Plan: Standorte, mögliche Leitungen, Kosten (wie in den Stücken 1 bis 7) |
| `gwi_algorithm.py` | Kern: Tabellen, Paar mit Kosten, Austauschgraph, Bellman–Ford, Tauschkreis, Greedy nach Kosten, Messreihen |
| `gwi_systems.py` | die drei Beispiele als Paare von Matroiden mit Kosten |
| `gwi_evaluation.py` | Kennzahlen, Ansichten der Experimente, Verdikte, Tabellen des Tabs Stand der Forschung |
| `gwi_visualization.py` | Plan, Digraph für die Arboreszenz, Kostenkurve, Balken |
| `gwi_presets.py` | Permalink, Presets, Zufalls-Seed |
| `gwi_layout.py` | fester Kopf |
| `gwi_pdf_export.py` | PDF des aktuellen Beispiels |
| `tests/` | Kern, Orakel, Eigenschaften, Verdikte, Presets, Claims, Randfälle, Oberfläche, Layout, Footer, Importe |

## Bewusst nicht umgesetzt

- Gewichtsaufspaltung (Frank) und Skalierungsverfahren als eigene Verfahren; die unterquadratischen und Näherungsverfahren des Tabs (nur Literatur).
- Eine faule Variante des gewichteten Verfahrens mit weniger Orakelaufrufen; Orakelaufrufe des gewichteten Verfahrens als eigenes Experiment.
- Matroid-Parität, Schnitt von drei oder mehr Matroiden, Vereinigung (Stück 9).
- Erklärseite „verständlich erklärt“ und Website-Einbindung (erst mit der vollständigen Linie).

## Lokal ausführen

```bash
pip install -r requirements.txt
streamlit run app.py
```

Tests: `pip install -r requirements-dev.txt`, dann `python -m pytest tests -q`. Die CI läuft mit Python 3.12 (`.github/workflows/tests.yml`); die in Streamlit Cloud eingestellte Python-Version ist beim Deploy zu nennen.

Gebaut mit Streamlit, Plotly, numpy und fpdf2.

---

Diese Demo ist Teil des Portfolios von [Sebastian Hanisch](https://sebastianhanisch.net) – Operations Research und Machine Learning ([Über mich](https://sebastianhanisch.net/ueber-mich.html)). Mehr zu den Demos: [Interaktive Demos](https://sebastianhanisch.net/demos.html).
