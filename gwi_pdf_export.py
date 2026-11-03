"""PDF-Export des aktuellen Beispiels (fpdf2). Kernschriften sind latin-1: Umlaute gehen, Sonderzeichen werden ersetzt."""

from __future__ import annotations

from fpdf import FPDF

import gwi_constants as C
from gwi_evaluation import Analysis, Settings, elemente, increments, steps_view, verdict_curve, verdict_step, zahl

_REPLACE = {"→": "->", "–": "-", "—": "-", "−": "-", "≤": "<=", "≥": ">=", "·": "*", "€": "EUR", "„": '"', "“": '"', "×": "x", "≈": "~", "∖": "\\", "∅": "{}", "½": "1/2", "₁": "1", "₂": "2", "²": "2", "Δ": "D", "√": "sqrt"}


def _s(text) -> str:
    out = str(text).replace("**", "")
    for old, new in _REPLACE.items():
        out = out.replace(old, new)
    return out.encode("latin-1", "replace").decode("latin-1")


def build_pdf(a: Analysis, settings: Settings) -> bytes:
    rounds = steps_view(settings)
    pdf = FPDF(orientation="P", unit="mm", format="A4")
    pdf.set_auto_page_break(auto=True, margin=12)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 15)
    pdf.cell(0, 9, _s("Gewichteter Matroid-Schnitt"), new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Helvetica", "", 10)
    plan = f"{settings.n} Standorte, Plan-Seed {settings.seed}" + (f", {settings.k} Farben" if settings.system == "regenbogen" else "") if settings.system != "arboreszenz" else f"festes Beispiel, Kosten aus Seed {settings.seed}"
    pdf.multi_cell(0, 5, _s(f"{C.SYSTEM_NAMES[settings.system]}; {plan}; {elemente(a.m)}; größte Elementzahl {a.opt}; {zahl(a.n_common)} gemeinsame unabhängige Mengen."), new_x="LMARGIN", new_y="NEXT")
    pdf.multi_cell(0, 5, _s("M1: " + C.MATROID_NAMES[settings.system][0] + ". M2: " + C.MATROID_NAMES[settings.system][1] + "."), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Helvetica", "B", 8)
    widths = (25, 40, 40)
    heads = ("k", "kleinste Kosten", "Zuwachs")
    for h, w in zip(heads, widths):
        pdf.cell(w, 6, _s(h), border=1)
    pdf.ln()
    pdf.set_font("Helvetica", "", 8)
    deltas = [None] + increments(a.curve)
    for k, cost in enumerate(a.curve):
        for val, w in zip((k, cost, "-" if deltas[k] is None else deltas[k]), widths):
            pdf.cell(w, 5.5, _s(val), border=1)
        pdf.ln()
    pdf.ln(2)
    pdf.set_font("Helvetica", "", 9)
    for k in range(1, a.opt + 1):
        pdf.multi_cell(0, 5, _s(verdict_step(a, rounds, k)[1]), new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
    pdf.multi_cell(0, 5, _s(verdict_curve(a, rounds)[1]), new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, _s("Quelle: gewichteter-schnitt-demo, Sebastian Hanisch."), new_x="LMARGIN", new_y="NEXT")
    return bytes(pdf.output())
