"""Plotly-Abbildungen. Alle Achsen sind gesperrt (fixedrange), damit Touch-Geräte beim Scrollen nicht am Diagramm hängen bleiben."""

import math

import plotly.graph_objects as go

import gwi_constants as C


def lock_axes(fig):
    fig.update_xaxes(fixedrange=True)
    fig.update_yaxes(fixedrange=True)
    return fig


def _base(fig, height=360):
    fig.update_layout(height=height, margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2), plot_bgcolor="rgba(0,0,0,0)")
    return lock_axes(fig)


def _frame(fig, lo=-0.05, hi=1.05):
    fig.add_trace(go.Scatter(x=[lo, hi], y=[lo, hi], mode="markers", marker=dict(opacity=0), hoverinfo="skip", showlegend=False))
    fig.update_xaxes(visible=False, scaleanchor="y", scaleratio=1)
    fig.update_yaxes(visible=False)


def build_plan(pair, groups, height=430, edge_text=None):
    """Plan der Standorte mit den Leitungen als Elementen. groups: Liste (Name, Elemente, Farbe) in Zeichenreihenfolge, hervorgehoben (dick); übrige Leitungen dünn in ihrer
    Kabelfarbe (beim Regenbogen) oder grau. edge_text: {Element: Text}, an der Mitte der Leitung."""
    inst = pair.inst
    fig = go.Figure()
    marked = {e for _, ids, _ in groups for e in ids}
    palette = C.PALETTE
    if pair.colors:
        for c in sorted(set(pair.colors)):
            ids = [e for e in range(inst.m) if e not in marked and pair.colors[e] == c]
            if ids:
                xs, ys = _lines(inst, ids)
                fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=palette[c % len(palette)], width=2), name=f"Farbe F{c + 1}", hoverinfo="skip"))
    else:
        ids = [e for e in range(inst.m) if e not in marked]
        if ids:
            xs, ys = _lines(inst, ids)
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=C.COLOR_OTHER, width=2), name="mögliche Leitung", hoverinfo="skip"))
    for name, ids, color in groups:
        if ids:
            xs, ys = _lines(inst, ids)
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color=color, width=6), name=name, hoverinfo="skip"))
    if edge_text:
        ids = sorted(edge_text)
        fig.add_trace(go.Scatter(
            x=[(inst.points[inst.edges[e][0]][0] + inst.points[inst.edges[e][1]][0]) / 2 for e in ids], y=[(inst.points[inst.edges[e][0]][1] + inst.points[inst.edges[e][1]][1]) / 2 for e in ids],
            mode="text", text=[edge_text[e] for e in ids], textfont=dict(size=13), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=[p[0] for p in inst.points], y=[p[1] for p in inst.points], mode="markers+text", text=[inst.name(v) for v in range(inst.n)], textposition="top center", textfont=dict(size=14),
        marker=dict(size=16, color=[C.COLOR_DEPOT if v == 0 else C.COLOR_NODE for v in range(inst.n)], line=dict(color="white", width=1.5)),
        hovertemplate="%{text}<extra></extra>", showlegend=False))
    _frame(fig)
    return _base(fig, height)


def _lines(inst, edge_ids):
    xs, ys = [], []
    for e in edge_ids:
        u, v, _ = inst.edges[e]
        xs += [inst.points[u][0], inst.points[v][0], None]
        ys += [inst.points[u][1], inst.points[v][1], None]
    return xs, ys


def build_digraph(pair, groups, height=380, edge_text=None):
    """Das feste Beispiel Arboreszenz: 6 Knoten, 12 Bögen mit Pfeilen (gegenläufige Bögen leicht versetzt). groups wie bei build_plan."""
    pts, arcs = C.ARBORESCENCE_POINTS, C.ARBORESCENCE_ARCS
    fig = go.Figure()
    color_of = {}
    width_of = {}
    for name, ids, color in groups:
        for e in ids:
            color_of[e], width_of[e] = color, 4
    seen_names = set()

    def geometry(e, shorten=0.045):
        a, b = arcs[e]
        dx, dy = pts[b][0] - pts[a][0], pts[b][1] - pts[a][1]
        norm = math.hypot(dx, dy)
        ux, uy = dx / norm, dy / norm
        ox, oy = -uy * 0.022, ux * 0.022
        return (pts[a][0] + ux * shorten + ox, pts[a][1] + uy * shorten + oy), (pts[b][0] - ux * shorten + ox, pts[b][1] - uy * shorten + oy)

    for e in range(len(arcs)):
        (x0, y0), (x1, y1) = geometry(e)
        color = color_of.get(e, "rgba(150,150,150,0.8)")
        fig.add_annotation(x=x1, y=y1, ax=x0, ay=y0, xref="x", yref="y", axref="x", ayref="y", showarrow=True, arrowhead=2, arrowsize=1.1, arrowwidth=width_of.get(e, 1.5), arrowcolor=color)
    for name, ids, color in groups:
        if ids and name not in seen_names:
            seen_names.add(name)
            fig.add_trace(go.Scatter(x=[None], y=[None], mode="lines", line=dict(color=color, width=5), name=name))
    if edge_text:
        ids = sorted(edge_text)
        mids = []
        for e in ids:
            (x0, y0), (x1, y1) = geometry(e)
            mids.append(((x0 + x1) / 2, (y0 + y1) / 2))
        fig.add_trace(go.Scatter(x=[p[0] for p in mids], y=[p[1] for p in mids], mode="text", text=[edge_text[e] for e in ids], textfont=dict(size=12), hoverinfo="skip", showlegend=False))
    fig.add_trace(go.Scatter(
        x=[p[0] for p in pts], y=[p[1] for p in pts], mode="markers+text", text=[str(i) for i in range(len(pts))], textposition="middle center", textfont=dict(size=12, color="white"),
        marker=dict(size=26, color=[C.COLOR_DEPOT if i == 0 else C.COLOR_NODE for i in range(len(pts))], line=dict(color="white", width=1.5)), hovertemplate="Knoten %{text}<extra></extra>", showlegend=False))
    _frame(fig, 0.0, 1.0)
    return _base(fig, height)


def build_figure(pair, groups, height=430, edge_text=None):
    """Das Beispiel als Bild: Plan (Regenbogen, Zuordnung) oder Digraph (Arboreszenz)."""
    if pair.kind == "boegen":
        return build_digraph(pair, groups, min(height, 380), edge_text)
    return build_plan(pair, groups, height, edge_text)


def build_bar_chart(categories, values, colors, x_title, y_title, hover, height=300):
    """Balken; hover ist eine Formatzeichenfolge mit %{x} und %{y}."""
    fig = go.Figure(go.Bar(x=list(categories), y=list(values), marker_color=list(colors), hovertemplate=hover + "<extra></extra>"))
    fig.update_xaxes(title_text=x_title, type="category")
    fig.update_yaxes(title_text=y_title)
    return _base(fig, height)


def build_grouped_bars(categories, series, x_title, y_title, height=320):
    """Gruppierte Balken: series = [(Name, Werte, Farbe)]."""
    fig = go.Figure([go.Bar(name=name, x=list(categories), y=list(values), marker_color=color, hovertemplate=name + ": %{y:.0f}<extra></extra>") for name, values, color in series])
    fig.update_layout(barmode="group")
    fig.update_xaxes(title_text=x_title, type="category")
    fig.update_yaxes(title_text=y_title)
    return _base(fig, height)


def build_cost_curve(ks, costs, deltas, selected=None, height=330):
    """Kleinste Kosten je Elementzahl (Linie, links) und die Zuwächse je Schritt (Balken, rechts); selected: die gerade gezeigte Elementzahl."""
    fig = go.Figure()
    fig.add_trace(go.Bar(x=[str(k) for k in ks[1:]], y=list(deltas), name="Zuwachs je Schritt", marker_color="rgba(217,95,2,0.45)", yaxis="y2", hovertemplate="Schritt auf k = %{x}: +%{y}<extra></extra>"))
    fig.add_trace(go.Scatter(x=[str(k) for k in ks], y=list(costs), mode="lines+markers", name="kleinste Kosten", line=dict(color=C.COLOR_SET, width=3), yaxis="y", hovertemplate="k = %{x}: %{y}<extra></extra>"))
    if selected is not None:
        fig.add_trace(go.Scatter(x=[str(selected)], y=[costs[selected]], mode="markers", name="gezeigt", marker=dict(size=16, color=C.COLOR_PATH, symbol="circle-open", line=dict(width=3))))
    fig.update_layout(
        yaxis=dict(title="kleinste Kosten", rangemode="tozero"), yaxis2=dict(overlaying="y", side="right", title="Zuwachs je Schritt", showgrid=False, rangemode="tozero"),
        xaxis=dict(title="Elementzahl k", type="category", categoryorder="array", categoryarray=[str(k) for k in ks]),
    )
    return _base(fig, height)
