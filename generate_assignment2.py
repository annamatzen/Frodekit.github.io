"""
Assignment 2 — generate visualizations for the data story:
"The Anatomy of SF's Post-Pandemic Crime Shift"

Run from this directory:
    python generate_assignment2.py
"""

import json
import os
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import plotly.express as px
import folium
from folium.plugins import HeatMapWithTime

# ── Paths ──────────────────────────────────────────────────────────────────
BASE      = os.path.dirname(os.path.abspath(__file__))
DATA_DIR  = r"c:/Users/frode/OneDrive/Skrivebord/DTU - Kandidat/02806 Social Data Analysis and Visualization"
CSV_PATH  = os.path.join(DATA_DIR, "sf_crime_merged_2003_present.csv")
VIZ_DIR   = os.path.join(BASE, "visualizations")
IMG_DIR   = os.path.join(BASE, "images")

os.makedirs(VIZ_DIR, exist_ok=True)
os.makedirs(IMG_DIR, exist_ok=True)

# ── Shared palette (matches site CSS variables) ────────────────────────────
BG_DARK   = '#0d0f1a'
PLOT_BG   = '#1c2237'
ACCENT    = '#16c79a'   # teal
ACCENT2   = '#e94560'   # red
TEXT      = '#e2e8f0'
MUTED     = '#8892a4'

focus_crimes = [
    'Assault', 'Robbery', 'Burglary', 'Larceny Theft',
    'Motor Vehicle Theft', 'Drug Offense', 'Warrant', 'Other Offenses'
]

# ── Load data ──────────────────────────────────────────────────────────────
print("Loading crime data (this may take a moment)...")
df = pd.read_csv(CSV_PATH, low_memory=False)
print(f"  Loaded {len(df):,} rows")

# Parse year — use Incident Datetime, fall back to Date column
df['_dt'] = pd.to_datetime(df['Incident Datetime'], errors='coerce')
mask_missing = df['_dt'].isna()
df.loc[mask_missing, '_dt'] = pd.to_datetime(
    df.loc[mask_missing, 'Date'], errors='coerce'
)
df['Year'] = df['_dt'].dt.year

# ──────────────────────────────────────────────────────────────────────────
# VIZ 1 — Static matplotlib: crime trends 2016-2024 with annotations
# ──────────────────────────────────────────────────────────────────────────
print("\n[1/3] Static chart: crime trends 2016-2024...")

df_focus = df[
    df['Unified Category'].isin(focus_crimes) &
    df['Year'].between(2016, 2024)
].copy()

yearly = (
    df_focus.groupby(['Year', 'Unified Category'])
    .size()
    .unstack(fill_value=0)
)

# Colour map: MVT = red, Larceny = teal, others = muted palette
color_map = {
    'Motor Vehicle Theft': ACCENT2,
    'Larceny Theft':       ACCENT,
    'Assault':             '#63b3ed',
    'Robbery':             '#f6ad55',
    'Burglary':            '#b794f4',
    'Drug Offense':        '#68d391',
    'Warrant':             '#fbb6ce',
    'Other Offenses':      '#a0aec0',
}
lw_map = {c: 2.5 if c in ('Motor Vehicle Theft', 'Larceny Theft') else 1.5
          for c in focus_crimes}
alpha_map = {c: 1.0 if c in ('Motor Vehicle Theft', 'Larceny Theft') else 0.55
             for c in focus_crimes}

fig, ax = plt.subplots(figsize=(13, 7))
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(PLOT_BG)

for crime in focus_crimes:
    if crime not in yearly.columns:
        continue
    ax.plot(
        yearly.index, yearly[crime],
        label=crime,
        color=color_map.get(crime, '#a0aec0'),
        linewidth=lw_map[crime],
        alpha=alpha_map[crime],
        marker='o', markersize=3.5,
        zorder=3 if crime in ('Motor Vehicle Theft', 'Larceny Theft') else 2
    )

# COVID shading
ax.axvspan(2020, 2020.75, alpha=0.10, color='white', zorder=1)
ax.axvline(x=2020, color=MUTED, linestyle='--', linewidth=1, alpha=0.6, zorder=2)
ax.text(2020.05, ax.get_ylim()[1] * 0.02 if ax.get_ylim()[1] > 0 else 100,
        'COVID-19\nlockdowns', color=MUTED, fontsize=8, va='bottom', zorder=4)

# Annotations for MVT and Larceny
if 'Motor Vehicle Theft' in yearly.columns and 2022 in yearly.index:
    mvt_2022 = yearly.loc[2022, 'Motor Vehicle Theft']
    mvt_2019 = yearly.loc[2019, 'Motor Vehicle Theft']
    pct = int(round((mvt_2022 - mvt_2019) / mvt_2019 * 100))
    ax.annotate(
        f'MVT +{pct}% vs 2019',
        xy=(2022, mvt_2022),
        xytext=(2021.1, mvt_2022 + max(yearly.values.max() * 0.05, 200)),
        color=ACCENT2, fontsize=8.5, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=ACCENT2, lw=1.2),
        zorder=5
    )

if 'Larceny Theft' in yearly.columns and 2023 in yearly.index:
    lt_2019 = yearly.loc[2019, 'Larceny Theft']
    lt_2023 = yearly.loc[2023, 'Larceny Theft']
    pct_lt = int(round((lt_2023 - lt_2019) / lt_2019 * 100))
    ax.annotate(
        f'Larceny {pct_lt}% vs 2019',
        xy=(2023, lt_2023),
        xytext=(2021.3, lt_2023 - max(yearly.values.max() * 0.12, 500)),
        color=ACCENT, fontsize=8.5, fontweight='bold',
        arrowprops=dict(arrowstyle='->', color=ACCENT, lw=1.2),
        zorder=5
    )

ax.set_title('SF Crime Trends 2016–2024: Not All Crimes Recovered Equally',
             color=TEXT, fontsize=15, pad=14, fontweight='bold')
ax.set_xlabel('Year', color=TEXT, fontsize=11)
ax.set_ylabel('Reported Incidents', color=TEXT, fontsize=11)
ax.set_xticks(range(2016, 2025))
ax.tick_params(colors=TEXT, labelsize=9)
for spine in ax.spines.values():
    spine.set_edgecolor('#2a3352')
ax.grid(True, alpha=0.15, color='white', linestyle='--')
ax.legend(
    facecolor=PLOT_BG, labelcolor=TEXT, edgecolor='#2a3352',
    framealpha=0.9, fontsize=8.5, loc='upper right',
    ncol=2, columnspacing=0.8, handlelength=1.8
)

plt.tight_layout()
out1 = os.path.join(IMG_DIR, "crime_shift_trends.png")
plt.savefig(out1, dpi=150, bbox_inches='tight', facecolor=BG_DARK)
plt.close()
print(f"  Saved {out1}")

# ──────────────────────────────────────────────────────────────────────────
# VIZ 2 — Folium HeatMapWithTime: MVT by year
# ──────────────────────────────────────────────────────────────────────────
print("\n[2/3] Folium HeatMapWithTime: Motor Vehicle Theft 2016-2024...")

df_mvt = df[
    (df['Unified Category'] == 'Motor Vehicle Theft') &
    df['Year'].between(2016, 2024) &
    df['X'].notna() & df['Y'].notna()
].copy()

# Coordinate sanity filter
df_mvt = df_mvt[
    (df_mvt['Y'] > 37) & (df_mvt['Y'] < 38) &
    (df_mvt['X'] > -123) & (df_mvt['X'] < -122)
]

years = list(range(2016, 2025))
SAMPLE_PER_YEAR = 2500

heat_data = []
year_labels = []
for yr in years:
    subset = df_mvt[df_mvt['Year'] == yr][['Y', 'X']]
    n = min(SAMPLE_PER_YEAR, len(subset))
    sample = subset.sample(n, random_state=42) if n > 0 else subset
    heat_data.append(sample.values.tolist() if n > 0 else [])
    year_labels.append(str(yr))
    print(f"    {yr}: {n} points")

m = folium.Map(
    location=[37.7749, -122.4194],
    zoom_start=12,
    tiles='https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png',
    attr='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> '
         'contributors &copy; <a href="https://carto.com/">CARTO</a>'
)

HeatMapWithTime(
    heat_data,
    index=year_labels,
    auto_play=False,
    max_opacity=0.85,
    min_opacity=0.05,
    radius=14,
    blur=10,
    gradient={0.2: '#0d0f1a', 0.45: '#3b1f8c', 0.65: ACCENT2, 0.85: '#f5a623', 1.0: '#ffffff'}
).add_to(m)

out2 = os.path.join(VIZ_DIR, "mvt_heatmap_by_year.html")
m.save(out2)
print(f"  Saved {out2}")

# ──────────────────────────────────────────────────────────────────────────
# VIZ 3 — Plotly grouped bar: MVT by district, 2019 vs 2022
# ──────────────────────────────────────────────────────────────────────────
print("\n[3/3] Plotly grouped bar: MVT by district 2019 vs 2022...")

df_district = df[
    (df['Unified Category'] == 'Motor Vehicle Theft') &
    (df['Year'].isin([2019, 2022])) &
    df['PdDistrict'].notna()
].copy()
df_district['District'] = df_district['PdDistrict'].str.title()

counts = (
    df_district.groupby(['District', 'Year'])
    .size()
    .reset_index(name='Count')
)
counts['Year'] = counts['Year'].astype(str)

# Sort districts by 2022 count descending
order_2022 = (
    counts[counts['Year'] == '2022']
    .sort_values('Count', ascending=False)
)
sorted_districts = order_2022['District'].tolist()

# Add % change label for hover
pivot = counts.pivot(index='District', columns='Year', values='Count').fillna(0)
pivot.columns.name = None
pivot = pivot.reset_index()
if '2019' in pivot.columns and '2022' in pivot.columns:
    pivot['pct_change'] = ((pivot['2022'] - pivot['2019']) / pivot['2019'].replace(0, 1) * 100).round(1)
    pct_map = dict(zip(pivot['District'], pivot['pct_change']))
else:
    pct_map = {}

counts['pct_change'] = counts['District'].map(pct_map).fillna(0)
counts['hover_text'] = counts.apply(
    lambda r: f"<b>{r['District']}</b><br>Year: {r['Year']}<br>Incidents: {int(r['Count']):,}"
              + (f"<br>Change vs 2019: +{r['pct_change']:.1f}%" if r['Year'] == '2022' else ""),
    axis=1
)

fig3 = px.bar(
    counts,
    x='District',
    y='Count',
    color='Year',
    barmode='group',
    color_discrete_map={'2019': ACCENT, '2022': ACCENT2},
    title='Motor Vehicle Theft by District: 2019 (Pre-COVID) vs 2022 (Post-COVID Peak)',
    labels={'District': 'Police District', 'Count': 'Incidents', 'Year': 'Year'},
    category_orders={'District': sorted_districts},
    custom_data=['hover_text']
)

fig3.update_traces(
    hovertemplate='%{customdata[0]}<extra></extra>',
    marker_line_width=0
)

fig3.update_layout(
    paper_bgcolor=BG_DARK,
    plot_bgcolor=PLOT_BG,
    font=dict(color=TEXT, family='Segoe UI, system-ui, sans-serif', size=12),
    title_font=dict(size=15, color=TEXT),
    xaxis=dict(
        tickangle=-30,
        gridcolor='rgba(255,255,255,0.06)',
        linecolor='#2a3352',
        tickfont=dict(size=11)
    ),
    yaxis=dict(
        gridcolor='rgba(255,255,255,0.06)',
        zeroline=False,
        linecolor='#2a3352',
        title_font=dict(size=12)
    ),
    legend=dict(
        bgcolor='rgba(28,34,55,0.85)',
        bordercolor=MUTED,
        borderwidth=1,
        title_text='Year',
        title_font=dict(color=TEXT),
        font=dict(color=TEXT)
    ),
    bargap=0.22,
    bargroupgap=0.06,
    hoverlabel=dict(bgcolor=PLOT_BG, font_color=TEXT, bordercolor=MUTED),
    margin=dict(t=60, b=80, l=60, r=30)
)

out3 = os.path.join(VIZ_DIR, "mvt_district_comparison.html")
fig3.write_html(out3, include_plotlyjs='cdn')
print(f"  Saved {out3}")

print("\n✓ All Assignment 2 visualizations exported!")
print(f"  → {IMG_DIR}/crime_shift_trends.png")
print(f"  → {VIZ_DIR}/mvt_heatmap_by_year.html")
print(f"  → {VIZ_DIR}/mvt_district_comparison.html")
