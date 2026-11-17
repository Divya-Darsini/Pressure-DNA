from pathlib import Path
import html
import os
import re
import tempfile
from datetime import date

import pandas as pd
import streamlit as st

# ============================================================
# PRESSURE DNA | RR IPL 2027 SCOUTING INTELLIGENCE
# Replace: Pressure_DNA/dashboard/app.py
# Reads existing files from Pressure_DNA/outputs and /data.
# This app does NOT recalculate or modify the Pressure DNA model.
# ============================================================

st.set_page_config(
    page_title="Pressure DNA | RR 2027",
    page_icon="🏏",
    layout="wide",
    initial_sidebar_state="collapsed",
)

APP_DIR = Path(__file__).resolve().parent
ROOT_DIR = APP_DIR.parent
OUTPUT_DIR = ROOT_DIR / "outputs"
DATA_DIR = ROOT_DIR / "data"
WATCHLIST_PATH = OUTPUT_DIR / "auction_watchlist.csv"

RANK_FILES = {
    "Batters": OUTPUT_DIR / "batter_rankings.csv",
    "Bowlers": OUTPUT_DIR / "bowler_rankings.csv",
}
TOP_FILES = {
    "Batters": OUTPUT_DIR / "top_10_batters.csv",
    "Bowlers": OUTPUT_DIR / "top_10_bowlers.csv",
}
EVIDENCE_FILES = {
    "Batters": [
        OUTPUT_DIR / "top10_batter_scoring_evidence.csv",
        OUTPUT_DIR / "top10_batter_evidence.csv",
    ],
    "Bowlers": [
        OUTPUT_DIR / "top10_bowler_scoring_evidence.csv",
        OUTPUT_DIR / "top10_bowler_evidence.csv",
    ],
}
PRESSURE_DATA_FILE = OUTPUT_DIR / "pressure_delivery_dataset.csv"
MATCH_LEVEL_FILES = {
    "Batters": OUTPUT_DIR / "batter_match_pressure.csv",
    "Bowlers": OUTPUT_DIR / "bowler_match_pressure.csv",
}

# These are validated counts from the latest recorded project build.
# Live files take precedence whenever available.
VALIDATED_SNAPSHOT = {
    "batters": 115,
    "bowlers": 171,
    "deliveries": 193_988,
    "pressure_deliveries": 66_560,
}

WATCHLIST_COLUMNS = [
    "player_name", "nationality", "role", "current_franchise",
    "franchise_status", "auction_registration", "availability_status",
    "recent_playing_activity", "pressure_dna_rank", "pressure_dna_score",
    "potential_contribution", "rr_squad_fit", "fit_reason",
    "strengths", "limitations", "scouting_notes", "source_name",
    "source_url", "last_verified",
]

ROLE_OPTIONS = ["Batter", "Bowler", "All-rounder", "Wicketkeeper", "Unconfirmed"]
NATIONALITY_OPTIONS = ["Indian", "Overseas", "Unconfirmed"]
FRANCHISE_OPTIONS = ["Retained", "Released", "Unconfirmed", "Not applicable"]
REGISTRATION_OPTIONS = ["Registered", "Not registered", "Unconfirmed"]
AVAILABILITY_OPTIONS = ["Available", "Unavailable", "Unconfirmed"]
RECENT_OPTIONS = ["Active", "Inactive", "Needs verification", "Unconfirmed"]
FIT_OPTIONS = ["Strong fit", "Possible fit", "Needs assessment", "Not assessed"]

# ----------------------------- STYLE -----------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { color-scheme: dark; }
.stApp { background: #0b1020; color: #edf2ff; }
[data-testid="stSidebar"] { display:none; }
[data-testid="stHeader"] { background: rgba(11,16,32,.94); }
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
h1,h2,h3 { font-family: 'Manrope', sans-serif !important; letter-spacing: -.025em; color: #f8f9ff; }
p, label, .stCaption { color: #c1cbe0; }
.hero { background: linear-gradient(118deg,#151f37 0%,#20213a 58%,#321d37 100%); border:1px solid #35425f; border-radius:18px; padding:18px 26px; margin:4px 0 22px; }
.eyebrow { color:#f18ab4; font-size:.70rem; font-weight:700; letter-spacing:.16em; text-transform:uppercase; }
.hero-title { color:#fff; font-family:'Manrope',sans-serif; font-size:2.55rem; font-weight:800; margin:4px 0; text-align:center; letter-spacing:.06em; }
.hero-sub { color:#c4cce0; font-size:.94rem; }
.metric-card { background:#141e33; border:1px solid #2b3955; border-radius:14px; padding:15px 17px; min-height:105px; }
.metric-label { color:#9eabc4; font-size:.77rem; font-weight:600; }
.metric-value { color:#fff; font-family:'Manrope',sans-serif; font-size:1.75rem; font-weight:800; margin-top:5px; }
.metric-note { color:#aab7ce; font-size:.70rem; margin-top:3px; }
.section-note,.muted { color:#9eabc4; font-size:.84rem; }
.insight { background:#151f34; border-left:3px solid #e879a8; border-radius:8px; padding:12px 15px; color:#dce5f5; margin:10px 0; }
.panel { background:#131d31; border:1px solid #293753; border-radius:13px; padding:14px 16px; margin:7px 0; }
.pink { color:#f18ab4; }
.status { display:inline-block; padding:3px 8px; border-radius:20px; background:#293650; color:#dce5f8; font-size:.72rem; font-weight:700; }
.status-pink { background:#46243a; color:#ffb6d2; }
.small-muted { color:#9eabc4; font-size:.75rem; }
.data-table { width:100%; border-collapse:collapse; font-size:.84rem; color:#e6ecf8; }
.data-table th { text-align:left; color:#f4a3c3; background:#1b2740; padding:10px 9px; border-bottom:1px solid #3a4965; white-space:nowrap; }
.data-table td { padding:9px; border-bottom:1px solid #293650; }
.data-table tr:nth-child(even) td { background:rgba(255,255,255,.018); }
.table-wrap { width:100%; overflow-x:auto; border:1px solid #293753; border-radius:11px; }
.bar-row { display:grid; grid-template-columns:minmax(120px, 190px) 1fr minmax(60px,90px); gap:10px; align-items:center; margin:9px 0; }
.bar-label { color:#c6d0e4; font-size:.82rem; }
.bar-track { height:11px; border-radius:20px; background:#26334d; overflow:hidden; }
.bar-fill { height:100%; border-radius:20px; background:linear-gradient(90deg,#bd5a88,#f18ab4); }
.bar-value { text-align:right; color:#edf2ff; font-size:.78rem; font-variant-numeric:tabular-nums; }
hr { border-color:#293650 !important; }
.stButton>button { border-radius:9px; border:1px solid #8d4668; background:#48283a; color:#fff; }
.stButton>button:hover { border-color:#f18ab4; background:#60324a; color:#fff; }
[data-testid="stMetric"] { background:#141e33; border:1px solid #293753; padding:12px 14px; border-radius:12px; }
[data-testid="stMetricLabel"] { color:#aab7ce; }
[data-testid="stMetricValue"] { color:#fff; }

/* Clickable ranking rows: subtle hover cue for native Streamlit dataframe rows */
div[data-testid="stDataFrame"] [role="row"]:hover { background: rgba(241,138,180,.20) !important; cursor: pointer !important; }
div[data-testid="stDataFrame"] { border:1px solid #394762; border-radius:12px; overflow:hidden; }
.stNumberInput input { background:#141e33 !important; color:#fff !important; }
[data-testid="stTextInput"] input { background:#141e33 !important; color:#fff !important; }
.profile-anchor { scroll-margin-top: 28px; }
</style>
""", unsafe_allow_html=True)

# ----------------------------- HELPERS -----------------------------
def norm(value):
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def read_csv(path):
    path = Path(path)
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path, low_memory=False)
    except Exception as exc:
        st.warning(f"Could not read {path.name}: {exc}")
        return pd.DataFrame()


def first_existing(paths):
    for path in paths:
        if Path(path).exists():
            return Path(path)
    return None


def col(df, candidates):
    if df is None or df.empty:
        return None
    lookup = {norm(c): c for c in df.columns}
    for candidate in candidates:
        key = norm(candidate)
        if key in lookup:
            return lookup[key]
    return None


def numeric(value):
    try:
        return float(value) if pd.notna(value) else None
    except (TypeError, ValueError):
        return None


def fmt(value, digits=1, suffix=""):
    n = numeric(value)
    if n is None:
        return "—"
    return f"{n:,.{digits}f}{suffix}"


def fmt_int(value):
    n = numeric(value)
    return "—" if n is None else f"{n:,.0f}"


def safe_text(value, default="—"):
    if value is None or pd.isna(value) or not str(value).strip():
        return default
    return str(value).strip()


def player_name_col(df):
    return col(df, ["player_name", "player", "name", "batter_name", "bowler_name"])


def standardize_rankings(raw, role):
    if raw.empty:
        return pd.DataFrame()
    pcol = player_name_col(raw)
    if not pcol:
        return pd.DataFrame()
    aliases = {
        "Rank": ["rank", "ranking"],
        "Player": ["player_name", "player", "name", "batter_name", "bowler_name"],
        "Pressure Exposure": ["total_pressure_exposure", "pressure_exposure", "pressure_balls", "pressure_legal_balls"],
        "Normal Exposure": ["total_normal_exposure", "normal_exposure", "normal_balls", "normal_legal_balls"],
        "Consistency": ["consistency_pct", "positive_match_phase_pct", "consistency"],
        "Pressure Matches": ["distinct_pressure_matches", "pressure_matches", "pressure_match_count"],
        "Impact Score": ["impact_score", "weighted_impact"],
        "Model Score": ["final_score", "overall_score", "pressure_score"],
    }
    out = pd.DataFrame(index=raw.index)
    for target, options in aliases.items():
        source = col(raw, options)
        if source:
            out[target] = raw[source]
    if "Player" not in out:
        out["Player"] = raw[pcol]
    if "Rank" not in out:
        out["Rank"] = range(1, len(out) + 1)
    for field in ["Rank", "Pressure Exposure", "Normal Exposure", "Consistency", "Pressure Matches", "Impact Score", "Model Score"]:
        if field in out:
            out[field] = pd.to_numeric(out[field], errors="coerce")
    if "Consistency" in out and out["Consistency"].dropna().size:
        if out["Consistency"].dropna().max() <= 1:
            out["Consistency"] = out["Consistency"] * 100
    out["Player"] = out["Player"].astype(str).str.strip()
    out = out[out["Player"].ne("") & out["Player"].ne("nan")]
    out["Role"] = role
    out = out.sort_values("Rank", na_position="last").drop_duplicates("Player", keep="first")
    return out.reset_index(drop=True)


def load_role_rankings(role):
    full = standardize_rankings(read_csv(RANK_FILES[role]), role)
    top = standardize_rankings(read_csv(TOP_FILES[role]), role)
    if not full.empty:
        return full, top if not top.empty else full.head(10).copy()
    if not top.empty:
        return top.copy(), top.copy()
    return pd.DataFrame(), pd.DataFrame()


def load_evidence(role):
    path = first_existing(EVIDENCE_FILES[role])
    return read_csv(path) if path else pd.DataFrame()


def player_evidence(df, player):
    if df.empty:
        return df
    pcol = player_name_col(df)
    if not pcol:
        return pd.DataFrame()
    return df[df[pcol].astype(str).str.casefold() == str(player).casefold()].copy()


def build_match_level_profile(raw, player, role):
    """Build phase/format pressure-v-normal evidence for any ranked player from pipeline match rows."""
    if raw is None or raw.empty:
        return pd.DataFrame()
    pcol = player_name_col(raw)
    required = {"match_format", "phase", "pressure_state", "match_id"}
    if not pcol or not required.issubset(set(raw.columns)):
        return pd.DataFrame()
    frame = raw[raw[pcol].astype(str).str.casefold() == str(player).casefold()].copy()
    if frame.empty:
        return pd.DataFrame()
    frame["_state"] = frame["pressure_state"].astype(str).str.strip().str.casefold()
    frame = frame[frame["_state"].isin(["pressure", "normal"])]
    if frame.empty:
        return pd.DataFrame()
    if role == "Batters":
        needed = ["balls_faced", "batter_runs", "boundaries", "dismissals"]
        if not set(needed).issubset(frame.columns):
            return pd.DataFrame()
        agg = {c: "sum" for c in needed}
        agg["match_id"] = pd.Series.nunique
        grouped = frame.groupby(["match_format", "phase", "_state"], dropna=False).agg(agg).reset_index()
        grouped = grouped.rename(columns={"match_id": "matches"})
        wide = grouped.pivot(index=["match_format", "phase"], columns="_state", values=needed + ["matches"])
        wide.columns = [f"{metric}_{state}" for metric, state in wide.columns]
        wide = wide.reset_index()
        for metric in needed + ["matches"]:
            for state in ["pressure", "normal"]:
                name = f"{metric}_{state}"
                if name not in wide:
                    wide[name] = 0
        wide["pressure_exposure"] = wide["balls_faced_pressure"]
        wide["normal_exposure"] = wide["balls_faced_normal"]
        for state in ["pressure", "normal"]:
            denom = wide[f"balls_faced_{state}"].replace(0, pd.NA)
            wide[f"{state}_runs_per_100"] = wide[f"batter_runs_{state}"] / denom * 100
            wide[f"{state}_boundaries_per_100"] = wide[f"boundaries_{state}"] / denom * 100
            wide[f"{state}_dismissals_per_100"] = wide[f"dismissals_{state}"] / denom * 100
        wide["pressure_matches"] = wide["matches_pressure"]
        wide["normal_matches"] = wide["matches_normal"]
    else:
        needed = ["legal_balls", "wickets"]
        if not set(needed).issubset(frame.columns):
            return pd.DataFrame()
        agg = {c: "sum" for c in needed}
        agg["match_id"] = pd.Series.nunique
        grouped = frame.groupby(["match_format", "phase", "_state"], dropna=False).agg(agg).reset_index()
        grouped = grouped.rename(columns={"match_id": "matches"})
        wide = grouped.pivot(index=["match_format", "phase"], columns="_state", values=needed + ["matches"])
        wide.columns = [f"{metric}_{state}" for metric, state in wide.columns]
        wide = wide.reset_index()
        for metric in needed + ["matches"]:
            for state in ["pressure", "normal"]:
                name = f"{metric}_{state}"
                if name not in wide:
                    wide[name] = 0
        wide["pressure_exposure"] = wide["legal_balls_pressure"]
        wide["normal_exposure"] = wide["legal_balls_normal"]
        for state in ["pressure", "normal"]:
            denom = wide[f"legal_balls_{state}"].replace(0, pd.NA)
            wide[f"{state}_wickets_per_24"] = wide[f"wickets_{state}"] / denom * 24
        wide["pressure_matches"] = wide["matches_pressure"]
        wide["normal_matches"] = wide["matches_normal"]
    wide["player_name"] = str(player)
    return wide


def get_player_profile_evidence(role, player, match_level_data, scoring_evidence_data):
    # Match-level source supports profiles for the full eligible ranking, not only the Top 10.
    from_match_rows = build_match_level_profile(match_level_data, player, role)
    if not from_match_rows.empty:
        return from_match_rows, "match-level player data"
    from_scoring = player_evidence(scoring_evidence_data, player)
    return from_scoring, "Top 10 scoring evidence" if not from_scoring.empty else "no detailed evidence file"


def html_table(df, columns=None, max_rows=None):
    if df is None or df.empty:
        st.info("No records are available for this view.")
        return
    view = df.copy()
    if columns:
        view = view[[c for c in columns if c in view.columns]]
    if max_rows:
        view = view.head(max_rows)
    if view.empty:
        st.info("The requested fields are not available in this dataset.")
        return
    for c in view.columns:
        if pd.api.types.is_float_dtype(view[c]):
            view[c] = view[c].map(lambda x: "—" if pd.isna(x) else f"{x:,.3f}")
    table = view.to_html(index=False, escape=True, classes="data-table", border=0)
    st.markdown(f'<div class="table-wrap">{table}</div>', unsafe_allow_html=True)


def metric_card(label, value, note=""):
    st.markdown(
        f'<div class="metric-card"><div class="metric-label">{html.escape(str(label))}</div>'
        f'<div class="metric-value">{html.escape(str(value))}</div>'
        f'<div class="metric-note">{html.escape(str(note))}</div></div>',
        unsafe_allow_html=True,
    )


def bar_chart_html(items, title, suffix="", digits=1):
    clean = []
    for label, value in items:
        v = numeric(value)
        if v is not None:
            clean.append((str(label), v))
    if not clean:
        st.info("No numeric evidence is available for this chart.")
        return
    max_abs = max(abs(v) for _, v in clean) or 1
    st.markdown(f"#### {html.escape(title)}")
    for label, value in clean:
        width = min(100, abs(value) / max_abs * 100)
        st.markdown(
            f'<div class="bar-row"><div class="bar-label">{html.escape(label)}</div>'
            f'<div class="bar-track"><div class="bar-fill" style="width:{width:.1f}%"></div></div>'
            f'<div class="bar-value">{value:,.{digits}f}{html.escape(suffix)}</div></div>',
            unsafe_allow_html=True,
        )


def format_consistency(value):
    n = numeric(value)
    return "—" if n is None else f"{n:.1f}%"


def save_watchlist(df):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    cleaned = df.copy()
    for field in WATCHLIST_COLUMNS:
        if field not in cleaned:
            cleaned[field] = ""
    cleaned = cleaned[WATCHLIST_COLUMNS]
    fd, temp_name = tempfile.mkstemp(prefix="auction_watchlist_", suffix=".csv", dir=str(OUTPUT_DIR))
    os.close(fd)
    try:
        cleaned.to_csv(temp_name, index=False)
        os.replace(temp_name, WATCHLIST_PATH)
        return True, "Watchlist saved successfully."
    except Exception as exc:
        try:
            os.remove(temp_name)
        except OSError:
            pass
        return False, f"Could not save watchlist: {exc}"


def load_watchlist(all_players):
    if WATCHLIST_PATH.exists():
        raw = read_csv(WATCHLIST_PATH)
        if raw.empty:
            return pd.DataFrame(columns=WATCHLIST_COLUMNS)
        name_col = player_name_col(raw)
        if name_col and name_col != "player_name":
            raw = raw.rename(columns={name_col: "player_name"})
        # Migrate earlier versions of the project's watchlist without losing entries.
        migrations = {
            "ipl_2027_availability": "availability_status",
            "verified_on": "last_verified",
            "what_selectors_should_know": "scouting_notes",
            "source_link": "source_url",
        }
        for old_name, new_name in migrations.items():
            if old_name in raw.columns and new_name not in raw.columns:
                raw = raw.rename(columns={old_name: new_name})
        for field in WATCHLIST_COLUMNS:
            if field not in raw:
                raw[field] = ""
        return raw[WATCHLIST_COLUMNS].fillna("")

    # Seed a manageable starting shortlist. Every status is explicitly unconfirmed.
    seed = []
    for role in ["Batters", "Bowlers"]:
        if role in all_players and not all_players[role].empty:
            for _, row in all_players[role].head(10).iterrows():
                seed.append({
                    "player_name": row["Player"],
                    "nationality": "Unconfirmed",
                    "role": "Batter" if role == "Batters" else "Bowler",
                    "current_franchise": "Unconfirmed",
                    "franchise_status": "Unconfirmed",
                    "auction_registration": "Unconfirmed",
                    "availability_status": "Unconfirmed",
                    "recent_playing_activity": "Needs verification",
                    "pressure_dna_rank": str(row.get("Rank", "")),
                    "pressure_dna_score": str(row.get("Model Score", "")),
                    "potential_contribution": "To be assessed",
                    "rr_squad_fit": "Not assessed",
                    "fit_reason": "",
                    "strengths": "",
                    "limitations": "",
                    "scouting_notes": "",
                    "source_name": "",
                    "source_url": "",
                    "last_verified": "",
                })
    frame = pd.DataFrame(seed, columns=WATCHLIST_COLUMNS)
    ok, message = save_watchlist(frame)
    if not ok:
        st.warning(message)
    return frame


def clean_watchlist(df):
    if df.empty:
        return pd.DataFrame(columns=WATCHLIST_COLUMNS)
    out = df.copy()
    for field in WATCHLIST_COLUMNS:
        if field not in out:
            out[field] = ""
    out["player_name"] = out["player_name"].astype(str).str.strip()
    out = out[out["player_name"].ne("")]
    out = out.drop_duplicates(subset=["player_name"], keep="last")
    return out[WATCHLIST_COLUMNS].fillna("").reset_index(drop=True)


def find_player_row(df, player):
    if df.empty:
        return None
    matches = df[df["Player"].astype(str).str.casefold() == str(player).casefold()]
    return None if matches.empty else matches.iloc[0]


def status_value(row, field, default="Unconfirmed"):
    return safe_text(row.get(field, ""), default)


def display_player_context(row):
    if row is None:
        st.info("No historical Pressure DNA ranking is available for this candidate.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historical rank", fmt_int(row.get("Rank")))
    c2.metric("Pressure exposure", fmt_int(row.get("Pressure Exposure")))
    c3.metric("Consistency", format_consistency(row.get("Consistency")))
    c4.metric("Model score", fmt(row.get("Model Score"), 3))

def open_player_profile_callback(player, role):
    # Streamlit callbacks run before the next script pass, so navigation state is safe to update.
    st.session_state["selected_profile_player"] = str(player)
    st.session_state["selected_profile_role"] = role
    st.session_state["profile_role"] = role
    st.session_state["nav_page"] = "Player Intelligence"


def set_page_callback(page_name):
    st.session_state["nav_page"] = page_name


def clickable_player_list(df, role, key_prefix, max_items=None, columns_count=1):
    """Render real Streamlit buttons labelled with player names; clicking opens the profile."""
    if df is None or df.empty:
        st.info("No players are available in this ranking view.")
        return
    view = df.head(max_items).copy() if max_items else df.copy()
    cols = st.columns(columns_count)
    for i, (_, row) in enumerate(view.iterrows()):
        player = str(row.get("Player", "Unknown player"))
        rank = fmt_int(row.get("Rank"))
        role_label = "Batter" if role == "Batters" else "Bowler"
        target = cols[i % columns_count]
        with target:
            st.button(
                f"#{rank}  {player}  ↗",
                key=f"{key_prefix}_{role}_{i}_{norm(player)}",
                use_container_width=True,
                on_click=open_player_profile_callback,
                args=(player, role),
            )
            detail_bits = []
            if numeric(row.get("Model Score")) is not None:
                detail_bits.append(f"Pressure DNA Score {fmt(row.get('Model Score'), 3)}")
            if numeric(row.get("Consistency")) is not None:
                detail_bits.append(f"Consistency {format_consistency(row.get('Consistency'))}")
            if numeric(row.get("Pressure Exposure")) is not None:
                unit = "balls" if role == "Batters" else "legal balls"
                detail_bits.append(f"{fmt_int(row.get('Pressure Exposure'))} pressure {unit}")
            st.caption(" • ".join(detail_bits) if detail_bits else role_label)


def weighted_rate(frame, value_col, weight_col):
    if frame.empty or value_col not in frame or weight_col not in frame:
        return None
    values = pd.to_numeric(frame[value_col], errors="coerce")
    weights = pd.to_numeric(frame[weight_col], errors="coerce")
    valid = values.notna() & weights.notna() & weights.gt(0)
    if not valid.any():
        return None
    return float((values[valid] * weights[valid]).sum() / weights[valid].sum())


def profile_evidence_summary(ev, role):
    """Summarise phase/format scoring evidence using exposure-weighted rates."""
    if ev.empty:
        return None, pd.DataFrame(), pd.DataFrame(), []
    if role == "Batters":
        metrics = [
            ("Runs per 100 balls", "pressure_runs_per_100", "normal_runs_per_100", "pressure_exposure", "normal_exposure", True),
            ("Boundaries per 100 balls", "pressure_boundaries_per_100", "normal_boundaries_per_100", "pressure_exposure", "normal_exposure", True),
            ("Dismissals per 100 balls", "pressure_dismissals_per_100", "normal_dismissals_per_100", "pressure_exposure", "normal_exposure", False),
        ]
        primary_label = "Runs per 100 balls"
    else:
        metrics = [
            ("Bowler wickets per 24 legal balls", "pressure_wickets_per_24", "normal_wickets_per_24", "pressure_exposure", "normal_exposure", True),
        ]
        primary_label = "Bowler wickets per 24 legal balls"
    summary_rows = []
    for label, pc, nc, pw, nw, higher_better in metrics:
        pv = weighted_rate(ev, pc, pw)
        nv = weighted_rate(ev, nc, nw)
        summary_rows.append({"Metric": label, "Pressure": pv, "Normal": nv,
                             "Difference": (pv - nv) if pv is not None and nv is not None else None,
                             "Direction": "Higher is better" if higher_better else "Lower is better"})
    phase_col = col(ev, ["phase"])
    format_col = col(ev, ["match_format"])
    primary = next(m for m in metrics if m[0] == primary_label)
    _, pc, nc, pw, nw, higher_better = primary

    def breakdown(group_col, group_name):
        rows = []
        if not group_col or pc not in ev or nc not in ev:
            return pd.DataFrame()
        for name, group in ev.groupby(group_col, dropna=False):
            pressure_value = weighted_rate(group, pc, pw)
            normal_value = weighted_rate(group, nc, nw)
            rows.append({group_name: str(name), "Pressure rate": pressure_value,
                         "Normal rate": normal_value,
                         "Difference": (pressure_value - normal_value) if pressure_value is not None and normal_value is not None else None,
                         "Pressure exposure": pd.to_numeric(group[pw], errors="coerce").sum() if pw in group else None,
                         "Normal exposure": pd.to_numeric(group[nw], errors="coerce").sum() if nw in group else None})
        return pd.DataFrame(rows)

    phase_df = breakdown(phase_col, "Phase")
    format_df = breakdown(format_col, "Format")
    insights = []
    if not phase_df.empty and phase_df["Difference"].notna().any():
        best = phase_df.loc[phase_df["Difference"].idxmax() if higher_better else phase_df["Difference"].idxmin()]
        insights.append(f"Strongest relative {str(best['Phase']).lower()}-phase evidence: pressure rate {fmt(best['Pressure rate'], 2)} versus normal rate {fmt(best['Normal rate'], 2)}.")
    if not format_df.empty:
        for _, fr in format_df.iterrows():
            if numeric(fr.get("Difference")) is not None:
                trend = "above" if (fr["Difference"] > 0) == higher_better else "below"
                insights.append(f"{fr['Format']}: pressure performance is {trend} the normal baseline for the primary metric.")
    return pd.DataFrame(summary_rows), phase_df, format_df, insights


def render_profile_description(player, role, row, ev, summary, phase_df):
    """Write a player-specific scouting read using only recorded model/evidence fields."""
    role_word = "batter" if role == "Batters" else "bowler"
    bits = [f"{player} is included in the Pressure DNA historical {role_word} rankings."]
    if row is not None:
        bits.append(f"The player is ranked #{fmt_int(row.get('Rank'))} among the eligible {role.lower()}, with a final model score of {fmt(row.get('Model Score'), 3)}.")
        if numeric(row.get("Pressure Exposure")) is not None:
            unit = "balls faced" if role == "Batters" else "legal balls bowled"
            bits.append(f"The ranking records {fmt_int(row.get('Pressure Exposure'))} pressure {unit} across {fmt_int(row.get('Pressure Matches'))} pressure matches.")
        if numeric(row.get("Consistency")) is not None:
            bits.append(f"The player met or exceeded their normal baseline in {format_consistency(row.get('Consistency'))} of pressure match-phase observations.")
    if not ev.empty and summary is not None and not summary.empty:
        primary = summary.iloc[0]
        if numeric(primary.get("Pressure")) is not None and numeric(primary.get("Normal")) is not None:
            difference = numeric(primary.get("Difference"))
            if role == "Batters":
                bits.append(f"Across the available format-phase scoring evidence, the exposure-weighted scoring rate was {fmt(primary['Pressure'], 2)} runs per 100 balls under the model's pressure definition versus {fmt(primary['Normal'], 2)} in normal situations (difference {fmt(difference, 2)}).")
            else:
                bits.append(f"Across the available format-phase scoring evidence, the exposure-weighted bowler-credit wicket rate was {fmt(primary['Pressure'], 2)} per 24 legal balls under the model's pressure definition versus {fmt(primary['Normal'], 2)} in normal situations (difference {fmt(difference, 2)}).")
        if not phase_df.empty:
            phase_names = ", ".join(phase_df["Phase"].astype(str).tolist())
            bits.append(f"Phase-level evidence is available for: {phase_names}.")
    else:
        bits.append("The supplied scoring-evidence files do not contain a detailed phase-by-phase record for this player, so a deeper statistical profile cannot be supported from the currently loaded evidence.")
    return " ".join(bits)


def render_profile_picker(role, df, search, current_limit):
    """Render a selectable full-row ranking table and search across all eligible players."""
    total = len(df)
    ranked = df.sort_values("Rank", na_position="last").copy()
    if search:
        table_df = ranked[ranked["Player"].astype(str).str.casefold().str.contains(search, na=False)].copy()
        st.caption(f"Search results: {len(table_df)} player(s) across all {total} eligible {role.lower()}.")
    else:
        table_df = ranked.head(int(current_limit)).copy()

    if table_df.empty:
        st.info("No ranked player matches that search.")
    else:
        display = pd.DataFrame({
            "Rank": table_df["Rank"].map(fmt_int),
            "Player Name": table_df["Player"].astype(str),
            "Pressure DNA Score": table_df["Model Score"].map(lambda x: fmt(x, 3)),
            "Consistency": table_df["Consistency"].map(format_consistency),
            "Pressure Balls": table_df["Pressure Exposure"].map(fmt_int),
        })
        table_key = f"rank_select_{role}_{'search_' + norm(search) if search else 'topn_' + str(current_limit)}"
        try:
            selection = st.dataframe(
                display,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key=table_key,
                column_config={
                    "Rank": st.column_config.TextColumn("Rank", width="small"),
                    "Player Name": st.column_config.TextColumn("Player Name", width="large"),
                    "Pressure DNA Score": st.column_config.TextColumn("Pressure DNA Score"),
                    "Consistency": st.column_config.TextColumn("Consistency"),
                    "Pressure Balls": st.column_config.TextColumn("Pressure Balls"),
                },
            )
            chosen_rows = list(selection.selection.rows)
            if chosen_rows:
                chosen_index = chosen_rows[0]
                if 0 <= chosen_index < len(table_df):
                    st.session_state["selected_profile_player"] = str(table_df.iloc[chosen_index]["Player"])
                    st.session_state["selected_profile_role"] = role
                    st.session_state["profile_row_selected_now"] = True
        except TypeError:
            st.warning("Your Streamlit version does not support selectable table rows. Upgrade Streamlit to enable full-row selection.")
            st.dataframe(display, use_container_width=True, hide_index=True)

    current = st.session_state.get("selected_profile_player")
    names = df["Player"].astype(str).tolist()
    if st.session_state.get("selected_profile_role") != role or current not in names:
        current = str(df.iloc[0]["Player"])
        st.session_state["selected_profile_player"] = current
        st.session_state["selected_profile_role"] = role
    return st.session_state.get("selected_profile_player", current)


# ----------------------------- LOAD PROJECT DATA -----------------------------
rankings = {}
top_rankings = {}
evidence = {}
match_level_data = {}
for role in ["Batters", "Bowlers"]:
    rankings[role], top_rankings[role] = load_role_rankings(role)
    evidence[role] = load_evidence(role)
    match_level_data[role] = read_csv(MATCH_LEVEL_FILES[role])

all_players = pd.concat([rankings["Batters"], rankings["Bowlers"]], ignore_index=True)
if all_players.empty:
    st.error("Pressure DNA ranking files were not found or could not be read.")
    st.markdown(
        "Place `batter_rankings.csv` and `bowler_rankings.csv` in the project's `outputs` folder, then rerun the app."
    )
    st.stop()

# ----------------------------- SINGLE-PAGE HEADER -----------------------------
st.markdown("""
<div class="hero">
  <div class="hero-title">PRESSURE DNA</div>
  <div class="hero-sub" style="text-align:center;margin-top:8px;">A data-driven cricket intelligence project that identifies players who perform in defined wicket-pressure situations using IPL and T20 data from 2022–2026.</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 1. EXECUTIVE OVERVIEW
# ============================================================
st.subheader("Executive Overview")
st.markdown('<div class="section-note">A selector-friendly view of the current historical model output.</div>', unsafe_allow_html=True)
batter_count = len(rankings["Batters"])
bowler_count = len(rankings["Bowlers"])
delivery_data = read_csv(PRESSURE_DATA_FILE)
if not delivery_data.empty:
    delivery_count = len(delivery_data)
    delivery_note = "Rows in pressure_delivery_dataset.csv"
else:
    delivery_count = VALIDATED_SNAPSHOT["deliveries"]
    delivery_note = "Last validated project snapshot; dataset file not found"
if batter_count == 10 and not RANK_FILES["Batters"].exists():
    batter_display, batter_note = f"10 / {VALIDATED_SNAPSHOT['batters']}", f"Top 10 loaded; validated full count is {VALIDATED_SNAPSHOT['batters']}"
else:
    batter_display, batter_note = f"{batter_count:,}", "Eligible players in loaded ranking file"
if bowler_count == 10 and not RANK_FILES["Bowlers"].exists():
    bowler_display, bowler_note = f"10 / {VALIDATED_SNAPSHOT['bowlers']}", f"Top 10 loaded; validated full count is {VALIDATED_SNAPSHOT['bowlers']}"
else:
    bowler_display, bowler_note = f"{bowler_count:,}", "Eligible players in loaded ranking file"
cards = st.columns(4)
with cards[0]: metric_card("Eligible batters", batter_display, batter_note)
with cards[1]: metric_card("Eligible bowlers", bowler_display, bowler_note)
with cards[2]: metric_card("Deliveries analysed", f"{delivery_count:,}", delivery_note)
eligible_batter_total = batter_count if RANK_FILES["Batters"].exists() else VALIDATED_SNAPSHOT["batters"]
eligible_bowler_total = bowler_count if RANK_FILES["Bowlers"].exists() else VALIDATED_SNAPSHOT["bowlers"]
with cards[3]: metric_card(
    "Eligible player pool",
    f"{eligible_batter_total + eligible_bowler_total:,}",
    f"{eligible_batter_total:,} eligible batters + {eligible_bowler_total:,} eligible bowlers",
)

st.markdown("---")
left, right = st.columns(2)
for container, role, title in [(left, "Batters", "No. 1 pressure batter"), (right, "Bowlers", "No. 1 pressure bowler")]:
    with container:
        st.markdown(f"#### {title}")
        top = top_rankings[role]
        if not top.empty:
            leader = top.iloc[0]
            st.markdown(
                f"<div class='panel'><div class='pink small-muted'>HISTORICAL MODEL LEADER</div><h3>{html.escape(str(leader['Player']))}</h3><div class='metric-value'>{fmt(leader.get('Model Score'),3)}</div><div class='metric-note'>Pressure DNA Score</div></div>",
                unsafe_allow_html=True,
            )
            st.caption(f"Rank #{fmt_int(leader.get('Rank'))} • Pressure exposure {fmt_int(leader.get('Pressure Exposure'))} • Consistency {format_consistency(leader.get('Consistency'))}")
        else:
            st.info("No top-ranked player is available.")

# ============================================================
# 2. PRESSURE RANKINGS
# ============================================================
st.markdown("---")
st.subheader("Pressure Rankings")
st.caption("Search the complete eligible player pool. The displayed rank remains the player's original historical rank.")

for role in ["Batters", "Bowlers"]:
    df_all = rankings[role].sort_values("Rank", na_position="last").reset_index(drop=True)
    if df_all.empty:
        st.info(f"No {role.lower()} ranking data is available.")
        continue
    st.markdown(f"### {role}")
    search_col, limit_col = st.columns([3, 1])
    with search_col:
        search_text = st.text_input(
            f"Search {role.lower()}", key=f"ranking_search_{role}",
            placeholder=f"Search any of the {len(df_all)} eligible {role.lower()}..."
        ).strip().casefold()
    with limit_col:
        display_limit = st.number_input(
            "Number of players displayed", min_value=1, max_value=max(1, len(df_all)),
            value=min(10, len(df_all)), step=1, key=f"ranking_limit_{role}"
        )
    if search_text:
        filtered = df_all[df_all["Player"].astype(str).str.casefold().str.contains(search_text, na=False)].copy()
        st.caption(f"Found {len(filtered)} matching player(s) across the full eligible pool; displaying up to {int(display_limit)}.")
    else:
        filtered = df_all.copy()
    visible = filtered.head(int(display_limit)).copy()
    if visible.empty:
        st.info("No player matches this search.")
    else:
        table = pd.DataFrame({
            "Rank": visible["Rank"].map(fmt_int),
            "Player Name": visible["Player"].astype(str),
            "Pressure DNA Score": visible["Model Score"].map(lambda x: fmt(x, 3)),
            "Consistency": visible["Consistency"].map(format_consistency),
            "Pressure Balls": visible["Pressure Exposure"].map(fmt_int),
        })
        st.caption("Tick the checkbox at the left of a player's row to open that player's profile below. Hover over a row to see the highlight.")
        selection = st.dataframe(
            table,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="single-row",
            key=f"pressure_rank_table_{role}",
            column_config={
                "Rank": st.column_config.TextColumn("Rank", width="small"),
                "Player Name": st.column_config.TextColumn("Player Name", width="large"),
                "Pressure DNA Score": st.column_config.TextColumn("Pressure DNA Score"),
                "Consistency": st.column_config.TextColumn("Consistency"),
                "Pressure Balls": st.column_config.TextColumn("Pressure Balls"),
            },
        )
        selected_rows = list(selection.selection.rows)
        if selected_rows:
            selected_idx = selected_rows[0]
            if 0 <= selected_idx < len(visible):
                chosen = str(visible.iloc[selected_idx]["Player"])
                previous = st.session_state.get("selected_profile_player")
                previous_role = st.session_state.get("selected_profile_role")
                if chosen != previous or role != previous_role:
                    st.session_state["selected_profile_player"] = chosen
                    st.session_state["selected_profile_role"] = role
                    st.session_state["profile_row_selected_now"] = True
                    st.rerun()
    st.markdown(" ")

# ============================================================
# 3. PLAYER INTELLIGENCE — CONTROLLED ONLY BY RANKING ROW CLICK
# ============================================================
st.markdown('<div id="player-intelligence" class="profile-anchor"></div>', unsafe_allow_html=True)
st.markdown("---")
st.subheader("Player Intelligence")
selected = st.session_state.get("selected_profile_player")
role = st.session_state.get("selected_profile_role")
if role not in ["Batters", "Bowlers"] or not selected or find_player_row(rankings.get(role, pd.DataFrame()), selected) is None:
    st.info("Select a player by clicking their row in Pressure Rankings. Their detailed profile will appear here.")
else:
    df = rankings[role]
    row = find_player_row(df, selected)
    ev, evidence_source = get_player_profile_evidence(role, selected, match_level_data[role], evidence[role])
    summary, phase_summary, _format_summary, _insight_lines = profile_evidence_summary(ev, role)
    if st.session_state.pop("profile_row_selected_now", False):
        st.components.v1.html("""<script>
            const target = window.parent.document.getElementById('player-intelligence');
            if (target) { target.scrollIntoView({behavior: 'smooth', block: 'start'}); }
        </script>""", height=1)
    st.markdown(f"## {html.escape(selected)}")
    rank_text = fmt_int(row.get("Rank"))
    role_label = "BATTER" if role == "Batters" else "BOWLER"
    st.markdown(f"<span class='status status-pink'>HISTORICAL RANK #{rank_text}</span> <span class='status'>{role_label}</span>", unsafe_allow_html=True)
    metric_cols = st.columns(5)
    metric_cols[0].metric("Historical rank", fmt_int(row.get("Rank")))
    metric_cols[1].metric("Pressure DNA Score", fmt(row.get("Model Score"), 3))
    metric_cols[2].metric("Consistency", format_consistency(row.get("Consistency")))
    metric_cols[3].metric("Pressure Balls", fmt_int(row.get("Pressure Exposure")))
    metric_cols[4].metric("Pressure matches", fmt_int(row.get("Pressure Matches")))

    st.markdown("### Pressure vs normal performance")
    if summary is not None and not summary.empty:
        primary = summary.iloc[0]
        pressure_rate, normal_rate = numeric(primary.get("Pressure")), numeric(primary.get("Normal"))
        difference = numeric(primary.get("Difference"))
        unit = "Runs per 100 balls" if role == "Batters" else "Bowler-credit wickets per 24 legal balls"
        if pressure_rate is not None and normal_rate is not None:
            bar_chart_html([("Pressure", pressure_rate), ("Normal", normal_rate)], unit, digits=2)
            if difference is not None:
                if role == "Batters":
                    better = difference > 0
                else:
                    better = difference > 0
                result = "higher" if difference > 0 else "lower" if difference < 0 else "equal to"
                st.markdown(f"- **Performance:** {fmt(pressure_rate, 2)} under pressure vs {fmt(normal_rate, 2)} normally ({unit.lower()}).")
                st.markdown(f"- **Pressure difference:** {fmt(abs(difference), 2)} {result} the normal baseline.")
        if role == "Batters":
            boundary = summary[summary["Metric"] == "Boundaries per 100 balls"]
            if not boundary.empty:
                b = boundary.iloc[0]
                st.markdown(f"- **Boundary rate:** {fmt(b.get('Pressure'), 2)} under pressure vs {fmt(b.get('Normal'), 2)} normally per 100 balls.")
        dismissal = summary[summary["Metric"] == "Dismissals per 100 balls"] if role == "Batters" else pd.DataFrame()
        if not dismissal.empty:
            d = dismissal.iloc[0]
            st.markdown(f"- **Dismissal rate:** {fmt(d.get('Pressure'), 2)} under pressure vs {fmt(d.get('Normal'), 2)} normally per 100 balls (lower is better).")
    else:
        st.info("Detailed pressure-versus-normal evidence is unavailable for this player in the loaded files.")

    st.markdown("### Phase-by-phase performance")
    if phase_summary is not None and not phase_summary.empty:
        phase_display = phase_summary.rename(columns={"Pressure rate": "Pressure", "Normal rate": "Normal"})
        html_table(phase_display, ["Phase", "Pressure", "Normal", "Difference", "Pressure exposure", "Normal exposure"])
        bar_chart_html([(str(r["Phase"]), r.get("Pressure rate")) for _, r in phase_summary.iterrows()], "Pressure rate by phase", digits=2)
    else:
        st.info("Phase-by-phase evidence is unavailable for this player.")

    st.markdown("### Scouting assessment")
    if summary is not None and not summary.empty:
        primary = summary.iloc[0]
        diff = numeric(primary.get("Difference"))
        consistency = numeric(row.get("Consistency"))
        exposure = numeric(row.get("Pressure Exposure"))
        if role == "Batters":
            st.markdown("- **Role evidence:** Batting output is evaluated using runs, boundary rate and dismissal rate in the project's defined pressure situations.")
        else:
            st.markdown("- **Role evidence:** Bowling output is evaluated using bowler-credit wickets per 24 legal balls in the project's defined pressure situations.")
        if diff is not None and diff > 0:
            st.markdown("- **Pressure signal:** The primary role metric is above the player's normal baseline.")
        elif diff is not None and diff < 0:
            st.markdown("- **Pressure signal:** The primary role metric is below the player's normal baseline; this should be examined alongside role and sample context.")
        else:
            st.markdown("- **Pressure signal:** The primary role metric is level with the normal baseline or cannot be separated clearly.")
        if consistency is not None:
            st.markdown(f"- **Repeatability:** {consistency:.1f}% of pressure match-phase observations met or exceeded the player's normal baseline.")
        if exposure is not None:
            unit = "balls faced" if role == "Batters" else "legal balls bowled"
            st.markdown(f"- **Evidence volume:** {int(exposure):,} pressure {unit} across {fmt_int(row.get('Pressure Matches'))} pressure matches.")
        if phase_summary is not None and not phase_summary.empty:
            valid = phase_summary[pd.to_numeric(phase_summary["Difference"], errors="coerce").notna()].copy()
            if not valid.empty:
                best = valid.loc[pd.to_numeric(valid["Difference"], errors="coerce").idxmax()]
                st.markdown(f"- **Best relative phase:** {best['Phase']} (pressure {fmt(best['Pressure rate'], 2)} vs normal {fmt(best['Normal rate'], 2)}).")
        st.markdown("- **RR interpretation:** These statistics provide historical role evidence only. A final recruitment decision also needs current role, availability and squad requirements to be independently verified.")
    else:
        st.info("There is not enough detailed evidence to make a player-specific scouting assessment.")
    st.caption(f"Evidence source: {evidence_source}. Pressure DNA Score is the model's calculated 70% impact + 30% consistency composite.")

# ============================================================
# 4. PLAYER COMPARISON
# ============================================================
st.markdown("---")
st.subheader("Player Comparison")
st.caption("Compare two players in the same role. Type part of a player's name in the search fields, then choose from the matching ranked players.")
compare_role = st.radio("Comparison role", ["Batters", "Bowlers"], horizontal=True, key="compare_role_single_page")
compare_df = rankings[compare_role].sort_values("Rank", na_position="last").copy()
compare_names = compare_df["Player"].astype(str).tolist()
if len(compare_names) < 2:
    st.info("At least two ranked players are needed for a comparison.")
else:
    pcol1, pcol2 = st.columns(2)
    with pcol1:
        q1 = st.text_input("Search player 1", key="compare_search_one", placeholder="Type a player name...").strip().casefold()
        opts1 = [n for n in compare_names if q1 in n.casefold()] if q1 else compare_names
        if not opts1:
            st.warning("No player matches the first search.")
            opts1 = compare_names
        p1 = st.selectbox("Player 1", opts1, key="compare_player_one_single")
    with pcol2:
        q2 = st.text_input("Search player 2", key="compare_search_two", placeholder="Type a player name...").strip().casefold()
        opts2 = [n for n in compare_names if q2 in n.casefold()] if q2 else compare_names
        opts2 = [n for n in opts2 if n != p1]
        if not opts2:
            st.warning("No different player matches the second search.")
            opts2 = [n for n in compare_names if n != p1]
        p2 = st.selectbox("Player 2", opts2, key="compare_player_two_single")
    a, b = find_player_row(compare_df, p1), find_player_row(compare_df, p2)
    if a is not None and b is not None:
        compare_rows = []
        for label, field in [
            ("Historical rank", "Rank"), ("Pressure DNA Score", "Model Score"),
            ("Pressure impact", "Impact Score"), ("Consistency (%)", "Consistency"),
            ("Pressure balls", "Pressure Exposure"), ("Normal exposure", "Normal Exposure"),
            ("Pressure matches", "Pressure Matches"),
        ]:
            compare_rows.append({"Metric": label, p1: a.get(field), p2: b.get(field)})
        html_table(pd.DataFrame(compare_rows))
        st.markdown("#### Visual comparison")
        bar_chart_html([(p1, a.get("Model Score")), (p2, b.get("Model Score"))], "Pressure DNA Score", digits=3)
        bar_chart_html([(p1, a.get("Consistency")), (p2, b.get("Consistency"))], "Consistency", suffix="%", digits=1)
        bar_chart_html([(p1, a.get("Pressure Exposure")), (p2, b.get("Pressure Exposure"))], "Pressure balls", digits=0)
        ev1, _ = get_player_profile_evidence(compare_role, p1, match_level_data[compare_role], evidence[compare_role])
        ev2, _ = get_player_profile_evidence(compare_role, p2, match_level_data[compare_role], evidence[compare_role])
        rows = []
        for player, pev in [(p1, ev1), (p2, ev2)]:
            if pev.empty:
                continue
            phase_field = col(pev, ["phase"])
            if phase_field:
                rate_fields = ("pressure_runs_per_100", "normal_runs_per_100") if compare_role == "Batters" else ("pressure_wickets_per_24", "normal_wickets_per_24")
                if all(field in pev.columns for field in rate_fields):
                    for phase, group in pev.groupby(phase_field, dropna=False):
                        rows.append({"Player": player, "Phase": str(phase),
                                     "Pressure rate": weighted_rate(group, rate_fields[0], "pressure_exposure"),
                                     "Normal rate": weighted_rate(group, rate_fields[1], "normal_exposure")})
        if rows:
            st.markdown("#### Phase-by-phase comparison")
            html_table(pd.DataFrame(rows))
        else:
            st.info("Detailed phase comparison is unavailable for one or both selected players.")
        score_a, score_b = numeric(a.get("Model Score")), numeric(b.get("Model Score"))
        if score_a is not None and score_b is not None:
            if score_a > score_b:
                st.markdown(f"**Score comparison:** {p1} has the higher historical Pressure DNA Score.")
            elif score_b > score_a:
                st.markdown(f"**Score comparison:** {p2} has the higher historical Pressure DNA Score.")
            else:
                st.markdown("**Score comparison:** Both players have the same recorded Pressure DNA Score.")
        st.caption("Interpret the score alongside consistency, pressure exposure, phase performance and role context. A higher score alone does not prove overall player quality or squad fit.")

# ============================================================
# 5. METHODOLOGY & RELIABILITY — COLLAPSED DROPDOWN
# ============================================================
st.markdown("---")
with st.expander("Methodology & Reliability", expanded=False):
    st.caption("Open this section to review the full model definition, scoring process, eligibility rules and limitations.")
    st.markdown("#### Dataset scope")
    st.write("IPL and T20I ball-by-ball data from 2022–2026. The latest validated build contained 193,988 regular-innings deliveries. Super Overs and innings outside regular innings 1 and 2 are excluded from the pressure model.")
    st.markdown("#### A. Pressure definition")
    st.write("Pressure is a project-defined wicket-and-phase proxy, not an official cricket pressure classification:")
    html_table(pd.DataFrame([
        ["Powerplay", "Overs 1–6", "At least 2 wickets have fallen before the delivery"],
        ["Middle", "Overs 7–15", "At least 4 wickets have fallen before the delivery"],
        ["Death", "Overs 16–20", "At least 5 wickets have fallen before the delivery"],
    ], columns=["Phase", "Overs", "Pressure condition"]))
    st.write("The model uses wickets_before and legal_balls_before from earlier deliveries only. It does not use future deliveries to classify the current ball.")
    st.markdown("#### B. Performance metrics and scoring")
    st.markdown("**Batters**\n- Runs per 100 balls.\n- Boundaries per 100 balls.\n- Dismissals per 100 balls (lower is better).\n- Pressure impact compares pressure and normal performance within the same match format and phase.")
    st.markdown("**Bowlers**\n- Bowler-credit wickets per 24 legal balls.\n- Run-outs are excluded from bowler-credit wickets.\n- Pressure impact compares pressure and normal wicket rates within the same match format and phase.")
    st.markdown("**Scoring process**\n- Separate IPL and T20I baselines.\n- Standardise impact metrics within match_format and phase using z-scores (clipped to ±3).\n- Average the available phase impact components.\n- Weight phase impact by pressure exposure.\n- Consistency is the percentage of pressure match-phase observations where the player's rate meets or exceeds their normal baseline in the same format-phase.\n- Final score = 70% normalised impact + 30% normalised consistency.")
    st.markdown("#### C. Eligibility thresholds")
    html_table(pd.DataFrame([
        ["Batters", "100 pressure balls", "50 normal balls", "8 distinct pressure matches", "12 pressure + 12 normal exposure in each eligible format-phase"],
        ["Bowlers", "96 pressure legal balls", "48 normal legal balls", "8 distinct pressure matches", "12 pressure + 12 normal exposure in each eligible format-phase"],
    ], columns=["Role", "Minimum pressure exposure", "Minimum normal exposure", "Minimum pressure matches", "Format-phase minimum"]))
    st.markdown("#### D. Sensitivity analysis")
    st.caption("Eligible-player counts from the project's recorded sample-threshold sensitivity run.")
    html_table(pd.DataFrame([
        ["Batters", "60 / 30 / 5", 153], ["Batters", "80 / 40 / 6", 132],
        ["Batters", "100 / 50 / 8 (current)", 115], ["Batters", "120 / 60 / 10", 96],
        ["Bowlers", "48 / 24 / 4", 232], ["Bowlers", "72 / 36 / 6", 199],
        ["Bowlers", "96 / 48 / 8 (current)", 171], ["Bowlers", "120 / 60 / 10", 156],
    ], columns=["Role", "Pressure / normal / matches threshold", "Eligible players"]))
    st.write("The eligible pool changes as minimum sample requirements become stricter. This is a sample-coverage check, not proof that one threshold is universally optimal.")


# ----------------------------- FOOTER -----------------------------
st.markdown("---")
st.caption("PRESSURE DNA • Historical cricket performance analysis • IPL & T20I 2022–2026")
