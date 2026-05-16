"""
Lead Quality Dashboard
======================
Run:  python lead_quality_dashboard.py path/to/leads.xlsx
      python lead_quality_dashboard.py path/to/leads.csv

The dashboard auto-refreshes every 30 seconds and works with both
.xlsx (sheet "leads_dataset.csv") and plain .csv files.

Required columns:
  lead_id, lead_name, source, timestamp, form_completion_time_sec,
  state, pincode, phone_number, carrier_acceptance_status
"""

import sys
import pathlib
from datetime import datetime

import pandas as pd
import dash
from dash import dcc, html, Input, Output
import plotly.graph_objects as go

# ── colour palette ────────────────────────────────────────────────────────────
SRC_PALETTE = {
    "PolicyBazaar_Direct": "#185FA5",
    "GoogleAds_Search":    "#0F6E56",
    "OrganicSEO":          "#639922",
    "MetaAds_Retarget":    "#534AB7",
    "AffiliateNet_IN":     "#BA7517",
    "src_quality_tier_2":  "#A32D2D",
}
STATUS_COLORS = {
    "Accepted": "#3B6D11",
    "Rejected": "#A32D2D",
    "Pending":  "#185FA5",
}
BG       = "#F8F7F4"
SURFACE  = "#FFFFFF"
BORDER   = "#E2E0D8"
TEXT_PRI = "#1A1A18"
TEXT_SEC = "#6B6A65"

PLOT_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Arial, sans-serif", color=TEXT_PRI, size=12),
    margin=dict(t=10, b=40, l=50, r=20),
)

# ── data loading ──────────────────────────────────────────────────────────────
def parse_ts(ts):
    for fmt in ("%Y-%m-%d %H:%M:%S", "%d/%m/%y %H:%M", "%Y-%m-%d"):
        try:
            return pd.to_datetime(str(ts), format=fmt)
        except Exception:
            pass
    try:
        return pd.to_datetime(str(ts))
    except Exception:
        return pd.NaT


def load_data(filepath: str) -> pd.DataFrame:
    fp = pathlib.Path(filepath)
    if fp.suffix in (".xlsx", ".xlsm", ".xls"):
        xl = pd.ExcelFile(fp)
        sheet = "leads_dataset.csv" if "leads_dataset.csv" in xl.sheet_names else xl.sheet_names[-1]
        df = pd.read_excel(fp, sheet_name=sheet)
    else:
        df = pd.read_csv(fp)

    df["ts"]    = df["timestamp"].apply(parse_ts)
    df["hour"]  = df["ts"].dt.hour
    df["month"] = df["ts"].dt.month
    df["month_name"] = df["ts"].dt.strftime("%b")

    phone_str = df["phone_number"].astype(str).str.strip()
    df["phone_valid"] = phone_str.str.match(r"^[6-9]\d{9}$")
    return df


def compute_src_stats(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for src, g in df.groupby("source"):
        total    = len(g)
        accepted = (g["carrier_acceptance_status"] == "Accepted").sum()
        rejected = (g["carrier_acceptance_status"] == "Rejected").sum()
        pending  = (g["carrier_acceptance_status"] == "Pending").sum()
        acc_rate = round(accepted / total * 100, 1) if total else 0
        avg_time = round(g["form_completion_time_sec"].mean(), 1)
        phone_ok = round(g["phone_valid"].mean() * 100, 1)
        rows.append(dict(source=src, total=total, accepted=int(accepted),
                         rejected=int(rejected), pending=int(pending),
                         acc_rate=acc_rate, avg_time=avg_time,
                         phone_valid_pct=phone_ok))
    return pd.DataFrame(rows).sort_values("acc_rate", ascending=False)


def verdict(acc_rate: float) -> tuple[str, str]:
    if acc_rate >= 65:
        return "Scale ↑", "#3B6D11"
    elif acc_rate >= 45:
        return "Watch →", "#854F0B"
    else:
        return "Cut ✕",  "#A32D2D"


# ── chart builders ────────────────────────────────────────────────────────────
def fig_acceptance_bar(src_stats: pd.DataFrame) -> go.Figure:
    colors = [SRC_PALETTE.get(s, "#888") for s in src_stats["source"]]
    fig = go.Figure(go.Bar(
        y=src_stats["source"],
        x=src_stats["acc_rate"],
        orientation="h",
        marker_color=colors,
        text=[f"{v}%" for v in src_stats["acc_rate"]],
        textposition="outside",
        cliponaxis=False,
    ))
    fig.update_layout(**PLOT_LAYOUT, showlegend=False,
                      xaxis=dict(range=[0, 110], showgrid=True,
                                 gridcolor=BORDER, title="Acceptance rate (%)"),
                      yaxis=dict(showgrid=False))
    fig.add_vline(x=src_stats["acc_rate"].mean(), line_dash="dot",
                  line_color=TEXT_SEC, annotation_text="avg",
                  annotation_position="top right")
    return fig


def fig_status_donut(df: pd.DataFrame) -> go.Figure:
    counts = df["carrier_acceptance_status"].value_counts()
    fig = go.Figure(go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=0.62,
        marker_colors=[STATUS_COLORS.get(s, "#888") for s in counts.index],
        textinfo="label+percent",
        textfont_size=12,
    ))
    acc   = (df["carrier_acceptance_status"] == "Accepted").sum()
    fig.update_layout(**PLOT_LAYOUT, showlegend=False,
                      annotations=[dict(text=f"<b>{acc}</b><br>accepted",
                                        x=0.5, y=0.5, showarrow=False,
                                        font=dict(size=14, color=TEXT_PRI))])
    return fig


def fig_monthly_trend(df: pd.DataFrame) -> go.Figure:
    monthly = (df.groupby(["month", "source"])["carrier_acceptance_status"]
               .agg(total="count",
                    accepted=lambda x: (x == "Accepted").sum())
               .reset_index())
    monthly["acc_rate"] = (monthly["accepted"] / monthly["total"] * 100).round(1)
    monthly = monthly.sort_values("month")
    months  = ["Jan","Feb","Mar","Apr","May","Jun",
                "Jul","Aug","Sep","Oct","Nov","Dec"]

    fig = go.Figure()
    for src in monthly["source"].unique():
        sub = monthly[monthly["source"] == src].set_index("month")
        y   = [sub.loc[m, "acc_rate"] if m in sub.index else None for m in range(1, 13)]
        fig.add_trace(go.Scatter(
            x=months, y=y,
            name=src,
            mode="lines+markers",
            line=dict(color=SRC_PALETTE.get(src, "#888"), width=2),
            marker=dict(size=5),
            connectgaps=True,
        ))
    fig.update_layout(**PLOT_LAYOUT, showlegend=True,
                      legend=dict(orientation="h", y=-0.25, x=0, font_size=10),
                      yaxis=dict(title="Acceptance %", range=[0, 110],
                                 gridcolor=BORDER),
                      xaxis=dict(showgrid=False))
    return fig


def fig_hourly(df: pd.DataFrame) -> go.Figure:
    hourly = (df[df["carrier_acceptance_status"] == "Accepted"]
              .groupby("hour").size().reindex(range(24), fill_value=0))
    labels = [f"{h}:00" for h in hourly.index]
    fig = go.Figure(go.Bar(
        x=labels, y=hourly.values,
        marker_color="#378ADD",
        marker_line_width=0,
    ))
    peak = int(hourly.idxmax())
    fig.add_vline(x=peak, line_dash="dot", line_color="#A32D2D",
                  annotation_text=f"peak {peak}:00",
                  annotation_position="top right")
    fig.update_layout(**PLOT_LAYOUT, showlegend=False,
                      xaxis=dict(showgrid=False, tickangle=-45),
                      yaxis=dict(title="Accepted leads", gridcolor=BORDER))
    return fig


def fig_state_bar(df: pd.DataFrame) -> go.Figure:
    state_g = df.groupby("state").agg(
        total=("carrier_acceptance_status", "count"),
        accepted=("carrier_acceptance_status", lambda x: (x == "Accepted").sum())
    ).reset_index()
    state_g["acc_rate"] = (state_g["accepted"] / state_g["total"] * 100).round(1)
    top10 = state_g.nlargest(10, "total")

    fig = go.Figure()
    fig.add_trace(go.Bar(y=top10["state"], x=top10["total"],
                         orientation="h", name="Total",
                         marker_color="#B5D4F4", marker_line_width=0))
    fig.add_trace(go.Bar(y=top10["state"], x=top10["accepted"],
                         orientation="h", name="Accepted",
                         marker_color="#185FA5", marker_line_width=0))
    fig.update_layout(**PLOT_LAYOUT, showlegend=True, barmode="overlay",
                      legend=dict(orientation="h", y=-0.2, x=0, font_size=10),
                      xaxis=dict(title="Leads", gridcolor=BORDER),
                      yaxis=dict(showgrid=False))
    return fig


def fig_form_time_box(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure()
    for src in df["source"].unique():
        sub = df[(df["source"] == src) & df["form_completion_time_sec"].notna()]
        fig.add_trace(go.Box(
            y=sub["form_completion_time_sec"],
            name=src,
            marker_color=SRC_PALETTE.get(src, "#888"),
            line_width=1.5,
            boxmean=True,
        ))
    fig.update_layout(**PLOT_LAYOUT, showlegend=False,
                      yaxis=dict(title="Seconds", gridcolor=BORDER),
                      xaxis=dict(showgrid=False, tickangle=-20))
    return fig


# ── layout helpers ────────────────────────────────────────────────────────────
def kpi_card(label: str, value: str, sub: str = "") -> html.Div:
    return html.Div([
        html.P(label, style={"fontSize": "11px", "color": TEXT_SEC,
                              "margin": "0 0 4px", "textTransform": "uppercase",
                              "letterSpacing": ".06em"}),
        html.P(value, style={"fontSize": "26px", "fontWeight": "600",
                              "color": TEXT_PRI, "margin": "0"}),
        html.P(sub,   style={"fontSize": "11px", "color": TEXT_SEC, "margin": "2px 0 0"}),
    ], style={"background": SURFACE, "border": f"0.5px solid {BORDER}",
              "borderRadius": "10px", "padding": "14px 18px", "flex": "1"})


def source_row(row: pd.Series) -> html.Tr:
    v_label, v_color = verdict(row["acc_rate"])
    bar_pct = f"{row['acc_rate']}%"
    return html.Tr([
        html.Td(row["source"],
                style={"fontWeight": "500", "padding": "10px 8px",
                       "color": SRC_PALETTE.get(row["source"], TEXT_PRI)}),
        html.Td(str(row["total"]),
                style={"padding": "10px 8px", "textAlign": "right"}),
        html.Td([
            html.Div([
                html.Div(style={"width": bar_pct, "height": "6px",
                                 "borderRadius": "3px",
                                 "background": SRC_PALETTE.get(row["source"], "#888")}),
            ], style={"flex": "1", "background": "#EBEBEB",
                       "borderRadius": "3px", "height": "6px",
                       "marginRight": "8px"}),
            html.Span(f"{row['acc_rate']}%", style={"minWidth": "42px",
                                                      "fontSize": "13px"}),
        ], style={"display": "flex", "alignItems": "center", "padding": "10px 8px"}),
        html.Td(f"{row['avg_time']}s",
                style={"padding": "10px 8px", "textAlign": "right"}),
        html.Td(html.Span(v_label,
                          style={"background": v_color + "1A",
                                 "color": v_color,
                                 "fontSize": "11px", "fontWeight": "600",
                                 "padding": "3px 10px", "borderRadius": "20px"}),
                style={"padding": "10px 8px"}),
    ], style={"borderBottom": f"0.5px solid {BORDER}"})


CARD = {"background": SURFACE, "border": f"0.5px solid {BORDER}",
        "borderRadius": "12px", "padding": "16px 20px"}

SECTION_LABEL = {"fontSize": "11px", "color": TEXT_SEC, "margin": "0 0 12px",
                 "textTransform": "uppercase", "letterSpacing": ".06em",
                 "fontWeight": "500"}


# ── app ───────────────────────────────────────────────────────────────────────
FILE_PATH = sys.argv[1] if len(sys.argv) > 1 else "leads_dataset.csv"

app = dash.Dash(__name__, title="Lead Quality Dashboard")

app.layout = html.Div([
    dcc.Interval(id="refresh", interval=30_000, n_intervals=0),
    dcc.Store(id="ts-store"),

    # ── header ────────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.H1("Lead Quality Dashboard",
                    style={"fontSize": "20px", "fontWeight": "600",
                           "color": TEXT_PRI, "margin": "0"}),
            html.P(id="last-updated",
                   style={"fontSize": "12px", "color": TEXT_SEC, "margin": "4px 0 0"}),
        ]),
        html.Div([
            html.Span("● LIVE", style={"color": "#3B6D11", "fontSize": "12px",
                                        "fontWeight": "600",
                                        "background": "#EAF3DE",
                                        "padding": "4px 12px",
                                        "borderRadius": "20px"}),
        ]),
    ], style={"display": "flex", "justifyContent": "space-between",
              "alignItems": "center", "marginBottom": "20px"}),

    # ── KPI row ───────────────────────────────────────────────────────────────
    html.Div(id="kpi-row",
             style={"display": "flex", "gap": "12px", "marginBottom": "20px"}),

    # ── scorecard table ───────────────────────────────────────────────────────
    html.Div([
        html.P("Source scorecard — scale vs cut decision", style=SECTION_LABEL),
        html.Table([
            html.Thead(html.Tr([
                html.Th("Source",        style={"textAlign": "left",  "padding": "4px 8px 10px", "fontSize": "11px", "color": TEXT_SEC, "fontWeight": "500"}),
                html.Th("Leads",         style={"textAlign": "right", "padding": "4px 8px 10px", "fontSize": "11px", "color": TEXT_SEC, "fontWeight": "500"}),
                html.Th("Acceptance rate",style={"textAlign": "left", "padding": "4px 8px 10px", "fontSize": "11px", "color": TEXT_SEC, "fontWeight": "500"}),
                html.Th("Avg form time", style={"textAlign": "right", "padding": "4px 8px 10px", "fontSize": "11px", "color": TEXT_SEC, "fontWeight": "500"}),
                html.Th("Verdict",       style={"textAlign": "left",  "padding": "4px 8px 10px", "fontSize": "11px", "color": TEXT_SEC, "fontWeight": "500"}),
            ], style={"borderBottom": f"1px solid {BORDER}"})),
            html.Tbody(id="scorecard-body"),
        ], style={"width": "100%", "borderCollapse": "collapse"}),
    ], style={**CARD, "marginBottom": "20px"}),

    # ── chart grid row 1 ──────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.P("Acceptance rate by source", style=SECTION_LABEL),
            dcc.Graph(id="bar-chart", config={"displayModeBar": False},
                      style={"height": "280px"}),
        ], style={**CARD, "flex": "1"}),

        html.Div([
            html.P("Status breakdown", style=SECTION_LABEL),
            dcc.Graph(id="donut-chart", config={"displayModeBar": False},
                      style={"height": "280px"}),
        ], style={**CARD, "flex": "1"}),
    ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

    # ── chart grid row 2 ──────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.P("Monthly acceptance rate by source", style=SECTION_LABEL),
            dcc.Graph(id="trend-chart", config={"displayModeBar": False},
                      style={"height": "280px"}),
        ], style={**CARD, "flex": "2"}),

        html.Div([
            html.P("Accepted leads by hour of day", style=SECTION_LABEL),
            dcc.Graph(id="hour-chart", config={"displayModeBar": False},
                      style={"height": "280px"}),
        ], style={**CARD, "flex": "1"}),
    ], style={"display": "flex", "gap": "16px", "marginBottom": "20px"}),

    # ── chart grid row 3 ──────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.P("Top 10 states — volume vs accepted", style=SECTION_LABEL),
            dcc.Graph(id="state-chart", config={"displayModeBar": False},
                      style={"height": "300px"}),
        ], style={**CARD, "flex": "1"}),

        html.Div([
            html.P("Form completion time by source", style=SECTION_LABEL),
            dcc.Graph(id="box-chart", config={"displayModeBar": False},
                      style={"height": "300px"}),
        ], style={**CARD, "flex": "1"}),
    ], style={"display": "flex", "gap": "16px"}),

], style={"fontFamily": "Inter, -apple-system, Arial, sans-serif",
          "background": BG, "minHeight": "100vh",
          "padding": "28px 32px", "color": TEXT_PRI})


# ── callbacks ─────────────────────────────────────────────────────────────────
@app.callback(
    Output("last-updated",   "children"),
    Output("kpi-row",        "children"),
    Output("scorecard-body", "children"),
    Output("bar-chart",      "figure"),
    Output("donut-chart",    "figure"),
    Output("trend-chart",    "figure"),
    Output("hour-chart",     "figure"),
    Output("state-chart",    "figure"),
    Output("box-chart",      "figure"),
    Input("refresh",         "n_intervals"),
)
def refresh(_):
    df       = load_data(FILE_PATH)
    src_stats = compute_src_stats(df)

    total    = len(df)
    accepted = (df["carrier_acceptance_status"] == "Accepted").sum()
    pending  = (df["carrier_acceptance_status"] == "Pending").sum()
    avg_time = round(df["form_completion_time_sec"].mean(), 0)
    acc_pct  = round(accepted / total * 100, 1)
    phone_ok = round(df["phone_valid"].mean() * 100, 1)

    kpis = html.Div([
        kpi_card("Total leads",       f"{total:,}",      f"{df['source'].nunique()} sources"),
        kpi_card("Acceptance rate",   f"{acc_pct}%",     f"{accepted:,} accepted"),
        kpi_card("Pending review",    f"{pending:,}",    f"{round(pending/total*100,1)}% of total"),
        kpi_card("Avg form time",     f"{int(avg_time)}s", f"{int(avg_time)//60}m {int(avg_time)%60}s"),
        kpi_card("Phone valid",       f"{phone_ok}%",    "10-digit format check"),
    ], style={"display": "flex", "gap": "12px", "width": "100%"})

    rows    = [source_row(r) for _, r in src_stats.iterrows()]
    bar_fig = fig_acceptance_bar(src_stats)
    donut   = fig_status_donut(df)
    trend   = fig_monthly_trend(df)
    hourly  = fig_hourly(df)
    state   = fig_state_bar(df)
    box     = fig_form_time_box(df)
    ts      = f"Last updated: {datetime.now().strftime('%d %b %Y, %H:%M:%S')}  ·  File: {pathlib.Path(FILE_PATH).name}"

    return ts, kpis, rows, bar_fig, donut, trend, hourly, state, box


# ── entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python lead_quality_dashboard.py <path_to_file.xlsx_or_.csv>")
        print("Example: python lead_quality_dashboard.py leads_dataset.csv")
        sys.exit(1)
    print("\n  Dashboard running → http://127.0.0.1:8050\n")
    app.run(debug=False, port=8050)
