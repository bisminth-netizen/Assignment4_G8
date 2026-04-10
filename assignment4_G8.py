"""
=============================================================================
  Agentic Workflow — Multimodal Engineering Diagram Extraction
  Dynamic Interactive Report  |  Topic: Agents, Tool Use, Multimodal
=============================================================================
  FIX NOTES (v2):
  1. execution_log.json is now bundled / generated alongside this script.
     No external dependency needed — the JSON file is the single source of
     truth for all agent-loop metrics.
  2. Each execution step now carries a `prompt_engineering_note` field that
     documents WHY each design decision was made (sequential ordering,
     JSON schema enforcement, context chaining, etc.).
  3. The metadata block contains an explicit `note_on_output_format` field
     explaining why HTML is used instead of a static PDF — this is surfaced
     prominently in the report's hero section and in a dedicated callout.
  4. A "Prompt Engineering Rationale" section (§2) is added to the report
     so the documented process is visible to the reader / instructor.

  Output : self-contained HTML with fully interactive Plotly charts
           (zoom, pan, hover, click-to-filter — all inline, no server)
  Run    : python generate_report.py
=============================================================================
"""

import json
import os
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
#  0. CONFIG & LOAD DATA
# ─────────────────────────────────────────────
COLORS = {
    "primary":   "#2E86AB",
    "secondary": "#A23B72",
    "warning":   "#E63946",
    "success":   "#2A9D8F",
    "accent":    "#F4A261",
    "dark":      "#1B4965",
    "light_bg":  "#F0F4F8",
    "muted":     "#6B7280",
}

CHART_TEMPLATE = dict(
    template="plotly_white",
    font=dict(family="'Syne', system-ui, sans-serif", size=12, color="#1F2937"),
    title_font=dict(family="'Syne', system-ui, sans-serif", size=16, color="#1B4965"),
    hoverlabel=dict(bgcolor="white", font_size=12, font_family="Syne"),
    margin=dict(l=40, r=40, t=70, b=40),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)

# ── Load execution log ──────────────────────
script_dir = os.path.dirname(os.path.abspath(__file__))
log_path   = os.path.join(script_dir, "execution_log.json")

with open(log_path, "r", encoding="utf-8") as f:
    raw = json.load(f)

execution_log = raw["execution_log"]
meta          = raw["metadata"]

# ─────────────────────────────────────────────
#  1. RAW EXTRACTED DATA  (mirrors diagram)
# ─────────────────────────────────────────────
components_data = [
    ["CB1102",         "Circuit Breaker",    "15A",              "A", "#14 AWG Yellow",    "11.00–11.02"],
    ["PMR1107",        "Transformer",        "10 kVA 460V→120V", "B", "#10 AWG Red/White", "11.07"],
    ["CB1108",         "Circuit Breaker",    "30A",              "B", "#10 AWG Red",       "11.07–11.09"],
    ["PS1111",         "Power Supply (PLC)", "24VDC 1769-PA4",   "C", "#14 AWG Red",       "11.10–11.11"],
    ["PS1112",         "Power Supply (PLC)", "24VDC 1769-PA4",   "C", "#14 AWG Red",       "11.11–11.12"],
    ["PS1113",         "Power Supply",       "240W 24VDC",       "C", "#14 AWG Red",       "11.12–11.13"],
    ["STRATIX5700",    "Ethernet Switch",    "N/A",              "D", "#18 AWG Blue",      "11.14"],
    ["PANELVIEW+1000", "HMI",               "24VDC",            "D", "#18 AWG Blue",      "11.15–11.16"],
    ["PS1117",         "Power Supply",       "480W 24VDC",       "E", "#18 AWG Blue",      "11.17"],
    ["CB1117",         "Circuit Breaker",    "15A",              "E", "#14 AWG Red",       "11.17"],
    ["CB1121",         "Circuit Breaker",    "5A",               "F", "N/A",              "11.21"],
    ["CB1123",         "Circuit Breaker",    "5A",               "F", "N/A",              "11.23"],
    ["CB1146",         "Circuit Breaker",    "1A",               "F", "N/A",              "11.46"],
]
components_df = pd.DataFrame(
    components_data,
    columns=["ID", "Type", "Rating", "Zone", "Wire Spec", "Line Ref"]
)

bom_data = [
    ["1",  "1769-PA4",        "PLC Power Supply, 24VDC",       "2", "PS1111, PS1112"],
    ["2",  "1769-L30ER",      "CompactLogix PLC",              "1", "PLC Rack"],
    ["3",  "1783-US06T",      "Stratix 5700 Ethernet Switch",  "1", "STRATIX5700"],
    ["4",  "2711P-T10C22D9P", "PanelView+ 1000 HMI",          "1", "PANELVIEW+1000"],
    ["5",  "1492-PSPA240W",   "Power Supply 240W 24VDC",       "1", "PS1113"],
    ["6",  "1492-PSPA480W",   "Power Supply 480W 24VDC",       "1", "PS1117"],
    ["7",  "140M-C2E-C16",   "Circuit Breaker 15A",           "2", "CB1102, CB1117"],
    ["8",  "140M-C2E-C30",   "Circuit Breaker 30A",           "1", "CB1108"],
    ["9",  "140M-C2E-C5",    "Circuit Breaker 5A",            "2", "CB1121, CB1123"],
    ["10", "140M-C2E-C1",    "Circuit Breaker 1A",            "1", "CB1146"],
    ["11", "PMR1107-CUSTOM", "Transformer 10kVA 480V/120V",   "1", "PMR1107"],
]
bom_df = pd.DataFrame(bom_data, columns=["Item", "Part Number", "Description", "Qty", "Reference"])

breakers_data = [
    ["CB1102", "15A", "Zone A general loads",            "PASS"],
    ["CB1108", "30A", "Transformer PMR1107 primary",     "PASS"],
    ["CB1117", "15A", "Zone E power supply PS1117",      "PASS"],
    ["CB1121", "5A",  "Zone F branch circuit A",         "PASS"],
    ["CB1123", "5A",  "Zone F branch circuit B",         "PASS"],
    ["CB1146", "1A",  "Zone F sensitive/signal circuit", "PASS"],
]
breakers_df = pd.DataFrame(breakers_data, columns=["Breaker ID", "Rating", "Protects", "Status"])

# ─────────────────────────────────────────────
#  2. BUILD ALL FIGURES
# ─────────────────────────────────────────────

def base_layout(**kwargs):
    layout = dict(**CHART_TEMPLATE)
    layout.update(kwargs)
    return layout


# ── 2-A  Execution Timeline ──────────────────
df_timeline = pd.DataFrame([
    {
        "Step": f"Step {s['step']}: {s['tool_name']}",
        "Duration (s)": round(s["duration_ms"] / 1000, 2),
        "Input Tokens":  s["input_tokens"],
        "Output Tokens": s["output_tokens"],
        "Stop Reason":   s["stop_reason"],
        "Tool":          s["tool_name"],
        "Description":   s["description"],
    }
    for s in execution_log
])

color_map = {"tool_use": COLORS["primary"], "end_turn": COLORS["success"]}

fig_timeline = px.bar(
    df_timeline,
    x="Duration (s)", y="Step", orientation="h",
    color="Stop Reason", color_discrete_map=color_map,
    text="Duration (s)",
    title="<b>Agent Execution Timeline</b><br><sup>Plan → Act → Observe → Reflect loop across 7 tool calls</sup>",
    custom_data=["Input Tokens", "Output Tokens", "Tool", "Description"],
)
fig_timeline.update_traces(
    texttemplate="%{text:.1f}s", textposition="outside", marker_line_width=0,
    hovertemplate=(
        "<b>%{y}</b><br>Duration: %{x:.1f}s<br>"
        "Input Tokens: %{customdata[0]:,}<br>Output Tokens: %{customdata[1]:,}<br>"
        "Purpose: %{customdata[3]}<extra></extra>"
    ),
)
fig_timeline.update_layout(**base_layout(
    height=480, xaxis_title="Duration (seconds)", yaxis_title="",
    yaxis=dict(autorange="reversed"),
    legend=dict(title="Stop Reason", x=0.75, y=0.02, bgcolor="rgba(255,255,255,0.85)"),
    dragmode="zoom",
))


# ── 2-B  Token Usage per Step ─────────────────
df_tokens = pd.concat([
    pd.DataFrame([{"Step": f"Step {s['step']}", "Type": "Input Tokens",  "Tokens": s["input_tokens"]}  for s in execution_log]),
    pd.DataFrame([{"Step": f"Step {s['step']}", "Type": "Output Tokens", "Tokens": s["output_tokens"]} for s in execution_log]),
])

fig_tokens = px.bar(
    df_tokens, x="Step", y="Tokens", color="Type", barmode="group",
    color_discrete_map={"Input Tokens": COLORS["primary"], "Output Tokens": COLORS["secondary"]},
    text="Tokens",
    title="<b>Claude API Token Usage per Tool Call</b>",
)
fig_tokens.update_traces(
    texttemplate="%{text:,}", textposition="outside", marker_line_width=0,
    hovertemplate="<b>%{x}</b> · %{data.name}: <b>%{y:,}</b> tokens<extra></extra>",
)
fig_tokens.update_layout(**base_layout(
    height=460, xaxis_title="Execution Step", yaxis_title="Number of Tokens",
    legend=dict(title="Token Type", x=0.02, y=0.98), dragmode="zoom",
))


# ── 2-C  Cumulative Token Burn ────────────────
cum_in, cum_out, cum_total = [], [], []
ri = ro = 0
for s in execution_log:
    ri += s["input_tokens"];  cum_in.append(ri)
    ro += s["output_tokens"]; cum_out.append(ro)
    cum_total.append(ri + ro)

df_cum = pd.DataFrame({
    "Step": [f"Step {i+1}" for i in range(len(execution_log))],
    "Step Number": list(range(1, len(execution_log) + 1)),
    "Cumulative Input":  cum_in,
    "Cumulative Output": cum_out,
    "Cumulative Total":  cum_total,
})

fig_cumulative = px.line(
    df_cum, x="Step Number",
    y=["Cumulative Input", "Cumulative Output", "Cumulative Total"],
    color_discrete_map={
        "Cumulative Input":  COLORS["primary"],
        "Cumulative Output": COLORS["secondary"],
        "Cumulative Total":  COLORS["accent"],
    },
    markers=True,
    title="<b>Cumulative Token Consumption</b><br><sup>Total API cost growth across the agent loop</sup>",
)
fig_cumulative.update_traces(
    line=dict(width=2.5), marker=dict(size=9),
    hovertemplate="Step %{x}<br>%{fullData.name}: <b>%{y:,}</b> tokens<extra></extra>",
)
fig_cumulative.update_layout(**base_layout(
    height=420, xaxis_title="Step Number",
    xaxis=dict(tickmode="linear", tick0=1, dtick=1),
    yaxis_title="Cumulative Tokens",
    legend=dict(title="Series", x=0.02, y=0.98), dragmode="zoom",
))


# ── 2-D  Circuit Breaker Audit Table ─────────
status_colors  = {row["Breaker ID"]: "#D1FAE5" if row["Status"] == "PASS" else "#FEE2E2" for _, row in breakers_df.iterrows()}
cell_fill      = [[status_colors[bid] for bid in breakers_df["Breaker ID"]]]
status_display = ["✅ " + s if s == "PASS" else "❌ " + s for s in breakers_df["Status"]]

fig_audit = go.Figure(data=[go.Table(
    columnwidth=[100, 80, 240, 80],
    header=dict(
        values=["<b>Breaker ID</b>", "<b>Rating</b>", "<b>Protects</b>", "<b>Audit</b>"],
        fill_color=COLORS["dark"], font=dict(color="white", size=12),
        align="center", height=38,
    ),
    cells=dict(
        values=[breakers_df["Breaker ID"], breakers_df["Rating"], breakers_df["Protects"], status_display],
        fill_color=cell_fill, align=["center", "center", "left", "center"],
        font=dict(size=12), height=32,
    ),
)])
fig_audit.update_layout(
    title="<b>Circuit Breaker Audit — IEC 60364 Compliance</b>",
    height=310, margin=dict(l=20, r=20, t=55, b=15), paper_bgcolor="rgba(0,0,0,0)",
)


# ── 2-E  Power Distribution Sankey ───────────
sankey_nodes = [
    "480V AC Source", "CB1108 (30A)", "PMR1107 Transformer\n10 kVA", "120V AC Bus",
    "PS1111 / PS1112\nRectifiers", "24V DC Bus", "PLC Rack\n(CompactLogix)",
    "HMI\n(PanelView+ 1000)", "PS1113 (240W)", "PS1117 (480W)",
]
sankey_colors = [COLORS["warning"], COLORS["accent"], "#E9C46A", COLORS["success"],
                 "#52B788", COLORS["dark"], "#023E8A", "#0077B6", "#1B4965", "#1B4965"]

fig_sankey = go.Figure(data=[go.Sankey(
    arrangement="snap",
    node=dict(
        pad=25, thickness=28, line=dict(color="white", width=1),
        label=sankey_nodes, color=sankey_colors,
        hovertemplate="<b>%{label}</b><extra></extra>",
    ),
    link=dict(
        source=[0, 1, 2, 3, 4, 5, 5, 3, 3],
        target=[1, 2, 3, 4, 5, 6, 7, 8, 9],
        value=[100, 95, 90, 85, 80, 45, 20, 10, 15],
        label=["480V AC feed", "Protected supply to TX", "Step-down 480→120V",
               "120V AC to rectifiers", "Rectified 24VDC", "PLC power",
               "HMI power", "240W supply", "480W supply"],
        color="rgba(46,134,171,0.35)",
        hovertemplate="<b>%{label}</b><br>%{source.label} → %{target.label}<br>Relative flow: %{value}<extra></extra>",
    ),
)])
fig_sankey.update_layout(
    title="<b>Power Distribution Flow</b><br><sup>480V AC → 120V AC → 24V DC — drag nodes to rearrange</sup>",
    height=540, font=dict(size=11, family="Syne, sans-serif"),
    hoverlabel=dict(bgcolor="white", font_size=12),
    paper_bgcolor="rgba(0,0,0,0)", margin=dict(l=30, r=30, t=65, b=20),
)


# ── 2-F  Time Distribution Donut ─────────────
df_tool_time = pd.DataFrame([{"Tool": s["tool_name"], "Duration (ms)": s["duration_ms"]} for s in execution_log])

fig_donut = px.pie(
    df_tool_time, values="Duration (ms)", names="Tool",
    title="<b>Execution Time Distribution by Tool</b>",
    color_discrete_sequence=px.colors.sequential.Blues_r, hole=0.45,
)
fig_donut.update_traces(
    textposition="inside", textinfo="percent+label", pull=[0.04] * len(df_tool_time),
    hovertemplate="<b>%{label}</b><br>%{value:.0f} ms  (%{percent})<extra></extra>",
)
fig_donut.update_layout(**base_layout(height=440, showlegend=True, legend=dict(x=0.8, y=0.5, font_size=11)))


# ── 2-G  Component Count by Zone ─────────────
zone_counts = components_df["Zone"].value_counts().reset_index()
zone_counts.columns = ["Zone", "Count"]
zone_counts = zone_counts.sort_values("Zone")

fig_zones = px.bar(
    zone_counts, x="Zone", y="Count",
    title="<b>Component Count by Power Zone</b>",
    color="Count", color_continuous_scale="Blues", text="Count",
)
fig_zones.update_traces(textposition="outside", marker_line_width=0,
                        hovertemplate="Zone <b>%{x}</b>: %{y} component(s)<extra></extra>")
fig_zones.update_layout(**base_layout(height=380, xaxis_title="Zone", yaxis_title="Number of Components",
                                      coloraxis_showscale=False))


# ─────────────────────────────────────────────
#  3. EXPORT FIGURES TO HTML DIVS
# ─────────────────────────────────────────────
config = dict(
    responsive=True, displayModeBar=True,
    modeBarButtonsToAdd=["v1hovermode", "toggleSpikelines"],
    toImageButtonOptions=dict(format="png", scale=2),
)

def fig_to_div(fig):
    return fig.to_html(full_html=False, include_plotlyjs=False, config=config)

div_timeline   = fig_to_div(fig_timeline)
div_tokens     = fig_to_div(fig_tokens)
div_cumulative = fig_to_div(fig_cumulative)
div_audit      = fig_to_div(fig_audit)
div_sankey     = fig_to_div(fig_sankey)
div_donut      = fig_to_div(fig_donut)
div_zones      = fig_to_div(fig_zones)


# ─────────────────────────────────────────────
#  4. STATIC TABLE HTML HELPERS
# ─────────────────────────────────────────────

def df_to_html_table(df, highlight_col=None, good_val=None):
    rows_html = ""
    for _, row in df.iterrows():
        cells = ""
        for col in df.columns:
            val = row[col]
            style = ""
            if highlight_col and col == highlight_col:
                style = 'style="color:#059669;font-weight:600;"' if val == good_val else 'style="color:#DC2626;font-weight:600;"'
            cells += f"<td {style}>{val}</td>"
        rows_html += f"<tr>{cells}</tr>"
    headers = "".join(f"<th>{c}</th>" for c in df.columns)
    return f'<table class="data-table"><thead><tr>{headers}</tr></thead><tbody>{rows_html}</tbody></table>'


components_table = df_to_html_table(components_df)
bom_table        = df_to_html_table(bom_df)

# Execution log table rows
log_rows = ""
for s in execution_log:
    stop_badge = (
        '<span class="badge badge-primary">tool_use</span>'
        if s["stop_reason"] == "tool_use"
        else '<span class="badge badge-success">end_turn</span>'
    )
    log_rows += f"""
    <tr>
      <td><strong>Step {s['step']}</strong></td>
      <td><code>{s['tool_name']}</code></td>
      <td class="text-muted" style="font-size:0.82rem;">{s['description']}</td>
      <td>{s['duration_ms']} ms</td>
      <td>{s['input_tokens']:,}</td>
      <td>{s['output_tokens']:,}</td>
      <td>{stop_badge}</td>
    </tr>"""

# Prompt rationale rows
rationale_rows = ""
for s in execution_log:
    rationale_rows += f"""
    <tr>
      <td><strong>Step {s['step']}</strong></td>
      <td><code>{s['tool_name']}</code></td>
      <td style="font-size:0.84rem;">{s['prompt_engineering_note']}</td>
    </tr>"""


# ─────────────────────────────────────────────
#  5. FULL HTML DOCUMENT
# ─────────────────────────────────────────────
total_input  = sum(s["input_tokens"]  for s in execution_log)
total_output = sum(s["output_tokens"] for s in execution_log)
total_tokens = total_input + total_output
total_dur_s  = sum(s["duration_ms"]   for s in execution_log) / 1000
generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Agentic Multimodal Extraction — Dynamic Report</title>
<script src="https://cdn.plot.ly/plotly-2.30.0.min.js"></script>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --primary:   #2E86AB;
    --secondary: #A23B72;
    --success:   #2A9D8F;
    --warning:   #E63946;
    --accent:    #F4A261;
    --dark:      #1B4965;
    --bg:        #F8FAFC;
    --surface:   #FFFFFF;
    --border:    #E2E8F0;
    --text:      #1E293B;
    --muted:     #64748B;
    --radius:    12px;
    --shadow:    0 2px 16px rgba(0,0,0,.07);
    --shadow-lg: 0 8px 32px rgba(0,0,0,.12);
  }}
  html {{ scroll-behavior: smooth; }}
  body {{
    font-family: 'Syne', system-ui, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.65;
    font-size: 15px;
  }}

  /* ── Hero Banner ─────────────────────── */
  .hero {{
    background: linear-gradient(135deg, var(--dark) 0%, #2E86AB 55%, #A23B72 100%);
    color: #fff;
    padding: 64px 48px 56px;
    position: relative;
    overflow: hidden;
  }}
  .hero::before {{
    content: '';
    position: absolute; inset: 0;
    background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.04'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  }}
  .hero-inner {{ position: relative; max-width: 900px; }}
  .hero-tag {{
    display: inline-block;
    background: rgba(255,255,255,.18);
    border: 1px solid rgba(255,255,255,.3);
    color: #fff;
    font-size: 0.75rem; font-weight: 700;
    letter-spacing: .1em; text-transform: uppercase;
    padding: 4px 14px; border-radius: 100px; margin-bottom: 18px;
  }}
  .hero h1 {{
    font-size: clamp(1.7rem, 4vw, 2.6rem);
    font-weight: 800; line-height: 1.2;
    margin-bottom: 14px; letter-spacing: -0.02em;
  }}
  .hero p {{ font-size: 1.05rem; opacity: .88; max-width: 640px; margin-bottom: 16px; }}
  .hero-format-note {{
    background: rgba(255,255,255,.15);
    border: 1px solid rgba(255,255,255,.25);
    border-radius: 10px;
    padding: 14px 18px;
    font-size: 0.83rem;
    opacity: .92;
    max-width: 700px;
    margin-bottom: 28px;
    line-height: 1.6;
  }}
  .hero-format-note strong {{ color: #FFD166; }}
  .hero-meta {{
    display: flex; flex-wrap: wrap; gap: 24px;
    font-size: 0.82rem; opacity: .8;
  }}
  .hero-meta span {{ display: flex; align-items: center; gap: 6px; }}

  /* ── KPI Strip ───────────────────────── */
  .kpi-strip {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0;
    border-bottom: 1px solid var(--border);
    background: var(--surface);
    box-shadow: var(--shadow);
  }}
  .kpi {{ padding: 26px 28px; border-right: 1px solid var(--border); text-align: center; }}
  .kpi:last-child {{ border-right: none; }}
  .kpi-value {{
    font-size: 2rem; font-weight: 800;
    color: var(--primary); line-height: 1.1; letter-spacing: -0.03em;
  }}
  .kpi-label {{
    font-size: 0.78rem; color: var(--muted); font-weight: 600;
    text-transform: uppercase; letter-spacing: .06em; margin-top: 4px;
  }}

  /* ── Layout ──────────────────────────── */
  .container {{ max-width: 1200px; margin: 0 auto; padding: 48px 24px; }}
  .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }}
  @media (max-width: 768px) {{ .grid-2 {{ grid-template-columns: 1fr; }} }}

  /* ── Section ─────────────────────────── */
  .section {{ margin-bottom: 56px; }}
  .section-header {{
    display: flex; align-items: center; gap: 14px;
    margin-bottom: 24px; padding-bottom: 14px;
    border-bottom: 2px solid var(--border);
  }}
  .section-icon {{
    width: 38px; height: 38px;
    background: linear-gradient(135deg, var(--primary), var(--dark));
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    font-size: 1.1rem; flex-shrink: 0;
  }}
  .section-header h2 {{ font-size: 1.2rem; font-weight: 700; color: var(--dark); margin: 0; }}
  .section-header p {{ font-size: 0.83rem; color: var(--muted); margin: 2px 0 0; }}

  /* ── Cards ───────────────────────────── */
  .card {{ background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 24px; box-shadow: var(--shadow); }}
  .card-full {{ width: 100%; }}

  /* ── Pipeline Steps ──────────────────── */
  .pipeline {{ display: flex; flex-direction: column; gap: 0; }}
  .pipeline-step {{
    display: flex; gap: 20px; padding: 18px 0;
    border-bottom: 1px solid var(--border);
  }}
  .pipeline-step:last-child {{ border-bottom: none; }}
  .step-num {{
    width: 36px; height: 36px;
    background: var(--primary); color: #fff;
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    font-weight: 700; font-size: 0.85rem; flex-shrink: 0; margin-top: 2px;
  }}
  .step-num.end {{ background: var(--success); }}
  .step-body {{ flex: 1; min-width: 0; }}
  .step-tool {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.82rem; font-weight: 500;
    color: var(--primary); background: #EFF6FF;
    padding: 2px 8px; border-radius: 5px;
    display: inline-block; margin-bottom: 4px;
  }}
  .step-desc {{ font-size: 0.87rem; color: var(--text); margin-bottom: 6px; }}
  .step-result {{ font-size: 0.8rem; color: var(--success); font-weight: 600; }}
  .step-meta {{
    display: flex; gap: 12px; font-size: 0.75rem; color: var(--muted);
    margin-top: 8px; flex-wrap: wrap;
  }}
  .step-meta span {{ background: var(--bg); border: 1px solid var(--border); padding: 2px 8px; border-radius: 5px; }}

  /* ── Data Table ──────────────────────── */
  .table-wrapper {{ overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--border); }}
  .data-table {{ width: 100%; border-collapse: collapse; font-size: 0.84rem; }}
  .data-table thead tr {{ background: var(--dark); color: #fff; }}
  .data-table th {{
    padding: 12px 14px; font-weight: 700; text-align: left;
    font-size: 0.78rem; letter-spacing: .04em; text-transform: uppercase; white-space: nowrap;
  }}
  .data-table td {{ padding: 10px 14px; border-bottom: 1px solid var(--border); vertical-align: top; }}
  .data-table tbody tr:hover {{ background: #F1F5F9; }}
  .data-table tbody tr:last-child td {{ border-bottom: none; }}
  .data-table code {{
    font-family: 'JetBrains Mono', monospace; font-size: 0.78rem;
    background: #EFF6FF; color: var(--primary); padding: 1px 5px; border-radius: 4px;
  }}

  /* ── Badges ──────────────────────────── */
  .badge {{
    display: inline-block; font-size: 0.72rem; font-weight: 700;
    padding: 3px 10px; border-radius: 100px;
    letter-spacing: .04em; text-transform: uppercase;
  }}
  .badge-primary {{ background: #DBEAFE; color: #1D4ED8; }}
  .badge-success {{ background: #D1FAE5; color: #065F46; }}

  /* ── Callout boxes ───────────────────── */
  .callout {{
    background: #EFF6FF; border-left: 4px solid var(--primary);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 16px 20px; margin-bottom: 20px; font-size: 0.9rem;
  }}
  .callout strong {{ color: var(--dark); }}
  .callout-warn {{
    background: #FFFBEB; border-left: 4px solid var(--accent);
    border-radius: 0 var(--radius) var(--radius) 0;
    padding: 16px 20px; margin-bottom: 20px; font-size: 0.88rem;
  }}
  .callout-warn strong {{ color: #92400E; }}

  /* ── Prompt Block ────────────────────── */
  .prompt-block {{
    background: #1E1E2E; color: #CDD6F4;
    border-radius: var(--radius); padding: 24px;
    font-family: 'JetBrains Mono', monospace; font-size: 0.82rem;
    line-height: 1.7; overflow-x: auto; margin-bottom: 12px;
  }}
  .prompt-block .kw  {{ color: #CBA6F7; }}
  .prompt-block .str {{ color: #A6E3A1; }}
  .prompt-block .com {{ color: #6C7086; font-style: italic; }}
  .prompt-block .hl  {{ color: #F38BA8; }}

  /* ── Rationale table ─────────────────── */
  .rationale-table {{ width:100%; border-collapse:collapse; font-size:0.84rem; }}
  .rationale-table th {{
    background: var(--dark); color:#fff;
    padding:10px 14px; font-size:0.78rem; text-transform:uppercase; letter-spacing:.04em; text-align:left;
  }}
  .rationale-table td {{ padding:12px 14px; border-bottom:1px solid var(--border); vertical-align:top; }}
  .rationale-table tbody tr:nth-child(even) {{ background:#F8FAFC; }}
  .rationale-table tbody tr:last-child td {{ border-bottom:none; }}
  .rationale-table code {{
    font-family:'JetBrains Mono',monospace; font-size:0.78rem;
    background:#EFF6FF; color:var(--primary); padding:1px 5px; border-radius:4px;
  }}

  /* ── Authors ─────────────────────────── */
  .hero-authors {{
    display: flex;
    flex-wrap: wrap;
    gap: 12px;
    margin-bottom: 28px;
  }}
  .author-chip {{
    display: flex;
    align-items: center;
    gap: 10px;
    background: rgba(255,255,255,.15);
    border: 1px solid rgba(255,255,255,.3);
    border-radius: 100px;
    padding: 7px 16px;
    font-size: 0.87rem;
    font-weight: 600;
    color: #fff;
    backdrop-filter: blur(4px);
  }}
  .author-chip .student-id {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.75rem;
    opacity: 0.75;
    font-weight: 400;
  }}

  /* ── Footer ──────────────────────────── */
  footer {{
    text-align: center; padding: 32px 24px;
    font-size: 0.8rem; color: var(--muted);
    border-top: 1px solid var(--border); background: var(--surface);
  }}
  .text-muted {{ color: var(--muted); }}
</style>
</head>
<body>

<!-- ════ HERO ════ -->
<div class="hero">
  <div class="hero-inner">
    <div class="hero-tag">📋 Dynamic Report · Agents · Tool Use · Multimodal</div>
    <h1>Agentic Multimodal Extraction<br>from Engineering Diagrams</h1>
    <p>
      An autonomous AI agent receives an industrial electrical panel wiring diagram,
      plans a sequence of tool calls, extracts structured data, audits protection devices,
      and generates this interactive report — all within a single execution loop.
    </p>

    <div class="hero-authors">
      <div class="author-chip">👤 Pheechaphuth Boonyoros <span class="student-id">LS2525207</span></div>
      <div class="author-chip">👤 Teh Bismin <span class="student-id">LS2525222</span></div>
    </div>

    <div class="hero-format-note">
      <strong>📄 Note on Output Format — HTML vs. Static PDF</strong><br>
      {meta['note_on_output_format']}
    </div>

    <div class="hero-meta">
      <span>🤖 Model: {meta['agent_model']}</span>
      <span>📐 Diagram: {meta['diagram_type']}</span>
      <span>🕐 Generated: {generated_at}</span>
      <span>📊 Standard: IEC 60617</span>
    </div>
  </div>
</div>

<!-- ════ KPI STRIP ════ -->
<div class="kpi-strip">
  <div class="kpi"><div class="kpi-value">7</div><div class="kpi-label">Tool Calls</div></div>
  <div class="kpi"><div class="kpi-value">13</div><div class="kpi-label">Components Extracted</div></div>
  <div class="kpi"><div class="kpi-value">11</div><div class="kpi-label">BOM Line Items</div></div>
  <div class="kpi"><div class="kpi-value">{total_tokens:,}</div><div class="kpi-label">Total Tokens Used</div></div>
  <div class="kpi"><div class="kpi-value">{total_dur_s:.1f}s</div><div class="kpi-label">Total Execution Time</div></div>
  <div class="kpi"><div class="kpi-value">6/6</div><div class="kpi-label">Breakers Passed</div></div>
</div>

<!-- ════ MAIN CONTENT ════ -->
<div class="container">

  <!-- §1  Task Overview & Prompt Design -->
  <div class="section">
    <div class="section-header">
      <div class="section-icon">🎯</div>
      <div>
        <h2>Task Overview &amp; Prompt Engineering Strategy</h2>
        <p>How the system prompt and tool schema were designed to drive the agent loop</p>
      </div>
    </div>

    <div class="callout">
      <strong>Assignment:</strong> Design an Agentic Workflow that processes <em>multimodal inputs</em>
      (an industrial electrical panel wiring diagram image), extracts structured data via a planned
      tool-call loop, and produces a documented extraction pipeline.
      Deliverable: a <strong>dynamic interactive report</strong> with zoomable visualizations.
    </div>

    <div class="grid-2">
      <div class="card">
        <h3 style="font-size:0.95rem;font-weight:700;color:var(--dark);margin-bottom:12px;">🔧 System Prompt Design</h3>
        <div class="prompt-block">
<span class="com"># System prompt (abridged)</span>
<span class="kw">You are</span> an expert electrical engineering AI.
<span class="kw">You have access to</span> the following tools:

<span class="str">extract_diagram_metadata</span>   <span class="com"># Step 1 — ground truth anchor</span>
<span class="str">extract_component_list</span>      <span class="com"># Step 2 — structured JSON schema</span>
<span class="str">extract_wire_specifications</span> <span class="com"># Step 3 — single responsibility</span>
<span class="str">build_bom</span>                   <span class="com"># Step 4 — context chaining</span>
<span class="str">audit_protection_devices</span>    <span class="com"># Step 5 — safety verification</span>
<span class="str">generate_power_flow_graph</span>   <span class="com"># Step 6 — graph as JSON</span>
<span class="str">compile_final_report</span>        <span class="com"># Step 7 — forced termination</span>

<span class="hl">RULES:</span>
- Call tools <span class="kw">sequentially</span>; each step builds on prior results.
- Never skip steps.
- Return <span class="kw">structured JSON</span> from every tool call.
- Use <span class="kw">end_turn ONLY</span> after Step 7.
        </div>
        <p style="font-size:0.83rem;color:var(--muted);">
          Sequential ordering + JSON output schema are the two most impactful
          prompt design decisions — see §2 for detailed rationale.
        </p>
      </div>

      <div class="card">
        <h3 style="font-size:0.95rem;font-weight:700;color:var(--dark);margin-bottom:12px;">📌 Multimodal Input Strategy</h3>
        <p style="font-size:0.87rem;margin-bottom:14px;">
          The user turn passes the wiring diagram as a <code>base64</code> encoded image
          alongside a task description. The model reasons over the visual content
          and emits structured tool calls — never raw image descriptions:
        </p>
        <div class="prompt-block">
<span class="kw">messages</span>: [{{
  <span class="str">"role"</span>: <span class="str">"user"</span>,
  <span class="str">"content"</span>: [
    {{
      <span class="str">"type"</span>: <span class="str">"image"</span>,
      <span class="str">"source"</span>: {{
        <span class="str">"type"</span>: <span class="str">"base64"</span>,
        <span class="str">"media_type"</span>: <span class="str">"image/jpeg"</span>,
        <span class="str">"data"</span>: <span class="hl">&lt;diagram_b64&gt;</span>
      }}
    }},
    {{
      <span class="str">"type"</span>: <span class="str">"text"</span>,
      <span class="str">"text"</span>: <span class="str">"Extract all structured data
               from this wiring diagram
               using the available tools."</span>
    }}
  ]
}}]
        </div>
      </div>
    </div>
  </div>

  <!-- §2  Prompt Engineering Rationale  ← NEW SECTION -->
  <div class="section">
    <div class="section-header">
      <div class="section-icon">🧠</div>
      <div>
        <h2>Prompt Engineering Rationale</h2>
        <p>Why each design decision was made — the documented thought process behind every step</p>
      </div>
    </div>

    <div class="callout-warn">
      <strong>Why does the order of tool calls matter?</strong><br>
      Free-form ReAct loops (where the model decides its own order) frequently produce partial
      extractions because the model terminates early once it believes the task is "done enough."
      Enforced sequential ordering guarantees completeness — every step must execute before
      <code>end_turn</code> is permitted. This is the single highest-impact prompt engineering
      decision in this workflow.
    </div>

    <div class="card card-full">
      <div class="table-wrapper">
        <table class="rationale-table">
          <thead>
            <tr>
              <th style="width:80px;">Step</th>
              <th style="width:200px;">Tool</th>
              <th>Prompt Engineering Rationale</th>
            </tr>
          </thead>
          <tbody>
            {rationale_rows}
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <!-- §3  Agent Loop -->
  <div class="section">
    <div class="section-header">
      <div class="section-icon">🔄</div>
      <div>
        <h2>Agent Planning &amp; Execution Loop</h2>
        <p>Plan → Act → Observe → Reflect — 7 sequential tool calls</p>
      </div>
    </div>
    <div class="card card-full">
      <div class="pipeline">
"""

for s in execution_log:
    num_class = "end" if s["stop_reason"] == "end_turn" else ""
    html += f"""
        <div class="pipeline-step">
          <div class="step-num {num_class}">{s['step']}</div>
          <div class="step-body">
            <div class="step-tool">{s['tool_name']}</div>
            <div class="step-desc">{s['description']}</div>
            <div class="step-result">✓ {s['result_summary']}</div>
            <div class="step-meta">
              <span>⏱ {s['duration_ms']} ms</span>
              <span>↑ {s['input_tokens']:,} in-tokens</span>
              <span>↓ {s['output_tokens']:,} out-tokens</span>
              <span class="badge {'badge-primary' if s['stop_reason'] == 'tool_use' else 'badge-success'}">{s['stop_reason']}</span>
            </div>
          </div>
        </div>"""

html += f"""
      </div>
    </div>
  </div>

  <!-- §4  Execution Analytics -->
  <div class="section">
    <div class="section-header">
      <div class="section-icon">📈</div>
      <div>
        <h2>Execution Analytics</h2>
        <p>Interactive charts — zoom, pan, hover, and click legend items to filter</p>
      </div>
    </div>
    <div class="card card-full" style="margin-bottom:24px;">{div_timeline}</div>
    <div class="grid-2" style="margin-bottom:24px;">
      <div class="card">{div_tokens}</div>
      <div class="card">{div_cumulative}</div>
    </div>
    <div class="grid-2">
      <div class="card">{div_donut}</div>
      <div class="card">{div_zones}</div>
    </div>
  </div>

  <!-- §5  Extracted Data Tables -->
  <div class="section">
    <div class="section-header">
      <div class="section-icon">🗂️</div>
      <div>
        <h2>Extracted Structured Data</h2>
        <p>Component list and Bill of Materials parsed from the wiring diagram</p>
      </div>
    </div>
    <div class="card card-full" style="margin-bottom:24px;">
      <h3 style="font-size:0.95rem;font-weight:700;color:var(--dark);margin-bottom:16px;">Component Inventory — All 13 Components by Zone</h3>
      <div class="table-wrapper">{components_table}</div>
    </div>
    <div class="card card-full">
      <h3 style="font-size:0.95rem;font-weight:700;color:var(--dark);margin-bottom:16px;">Bill of Materials (BOM) — 11 Line Items</h3>
      <div class="table-wrapper">{bom_table}</div>
    </div>
  </div>

  <!-- §6  Circuit Breaker Audit -->
  <div class="section">
    <div class="section-header">
      <div class="section-icon">🔒</div>
      <div>
        <h2>Protection Device Audit</h2>
        <p>IEC 60364 compliance check on all circuit breakers — hover rows for details</p>
      </div>
    </div>
    <div class="card card-full">{div_audit}</div>
  </div>

  <!-- §7  Power Flow Sankey -->
  <div class="section">
    <div class="section-header">
      <div class="section-icon">⚡</div>
      <div>
        <h2>Power Distribution Flow</h2>
        <p>Sankey diagram — drag nodes to rearrange, hover links for flow values</p>
      </div>
    </div>
    <div class="card card-full">{div_sankey}</div>
  </div>

  <!-- §8  Full Execution Log -->
  <div class="section">
    <div class="section-header">
      <div class="section-icon">📋</div>
      <div>
        <h2>Full Execution Log</h2>
        <p>Complete record of every API call in the agent loop</p>
      </div>
    </div>
    <div class="card card-full">
      <div class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>Step</th><th>Tool</th><th>Purpose</th>
              <th>Duration</th><th>Input Tok.</th><th>Output Tok.</th><th>Stop</th>
            </tr>
          </thead>
          <tbody>{log_rows}</tbody>
        </table>
      </div>
    </div>
  </div>

</div><!-- /container -->

<footer>
  Dynamic Interactive Report · Generated {generated_at} ·
  Agentic Multimodal Extraction Pipeline ·
  {total_tokens:,} tokens · {total_dur_s:.1f}s total ·
  Built with Python + Plotly
</footer>

</body>
</html>"""

# ─────────────────────────────────────────────
#  6. WRITE OUTPUT
# ─────────────────────────────────────────────
output_path = "agentic_multimodal_report.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"✅  Report saved → {output_path}")
print(f"    Total tokens : {total_tokens:,}  ({total_input:,} in / {total_output:,} out)")
print(f"    Total time   : {total_dur_s:.1f}s across {len(execution_log)} tool calls")
print(f"    File size    : {os.path.getsize(output_path) / 1024:.0f} KB")
