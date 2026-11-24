"""South African Statistics Curriculum Explorer — public, read-only prototype."""
from __future__ import annotations
import os
import pandas as pd
import streamlit as st
from data_prep import load_csv, PUBLIC_COLUMNS

st.set_page_config(page_title="SA Statistics Curriculum Explorer", page_icon="📊", layout="wide")
st.markdown('''<style>
.block-container {padding-top:1.6rem;max-width:1360px}
[data-testid="stMetric"] {background:#f5f8fa;border:1px solid #e5eaf0;padding:16px;border-radius:12px}
.small-note {color:#596579;font-size:0.86rem}
</style>''', unsafe_allow_html=True)

PUBLIC_SHEET_ID = "1eNmGVsZ1qT4hv4zRPAQ8w1qsgC7kzSc-LTxihY_4O1o"
# Read the worksheet by NAME, avoiding an assumption about the tab's numeric gid.
DEFAULT_PUBLIC_CSV_URL = (
    f"https://docs.google.com/spreadsheets/d/{PUBLIC_SHEET_ID}/gviz/tq"
    "?tqx=out:csv&sheet=Modules"
)

@st.cache_data(ttl=86400, show_spinner="Loading curriculum catalogue...")
def load_data(csv_url: str) -> tuple[pd.DataFrame, str]:
    if csv_url:
        import requests
        response = requests.get(csv_url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status()
        body = response.content
        sample = body[:300].lstrip().lower()
        if sample.startswith(b"<!doctype html") or sample.startswith(b"<html"):
            raise ValueError("Google returned a web page rather than CSV; check that the publication Sheet is publicly viewable and the tab is named Modules.")
        df = load_csv(body, strict_public_headers=True)
        return df, "Public Google Sheet (24-hour app cache)"
    local = os.path.join(os.path.dirname(__file__), "data", "module_snapshot.csv")
    with open(local, "rb") as file:
        df = load_csv(file.read())
    return df, "Bundled Excel snapshot (not live)"

# For offline testing only: set USE_SNAPSHOT=1. Otherwise the public Sheet is the source.
use_snapshot = os.environ.get("USE_SNAPSHOT", "0").lower() in ("1", "true", "yes")
try:
    configured = st.secrets.get("PUBLIC_CSV_URL", "")
except (FileNotFoundError, AttributeError):
    configured = ""
url = "" if use_snapshot else (configured or os.environ.get("PUBLIC_CSV_URL", DEFAULT_PUBLIC_CSV_URL))
try:
    df, source_label = load_data(url)
except Exception as exc:
    st.error("The public Google Sheet could not be loaded. The app has NOT silently switched to older data.")
    st.write("Check that the spreadsheet is shared as Anyone with the link — Viewer, and its data tab is named `Modules` with the expected 16-column headers. Google may also still be processing its IMPORTRANGE permission.")
    with st.expander("Technical diagnostic"):
        st.code(str(exc))
        st.code(url)
    st.info("For local offline testing only, run with USE_SNAPSHOT=1 to load the bundled historical snapshot.")
    st.stop()

st.title("SA Statistics Curriculum Explorer")
st.caption("A descriptive catalogue of undergraduate Statistics modules at participating South African institutions")
st.info(f"**Data source:** {source_label}. This catalogue is incomplete and evolving. Absence from the catalogue does not imply absence of teaching, and similar disciplines do not establish module equivalence.")

with st.sidebar:
    st.header("Explore the catalogue")
    page = st.radio("View", ["National overview", "Institution explorer", "Discipline explorer", "Compare institutions", "Module browser"], label_visibility="collapsed")
    st.divider()
    all_insts = sorted(df["Institution"].dropna().unique())
    inst_filter = st.multiselect("Institution filter", all_insts)
    years = sorted(df["Year level numeric"].dropna().unique().astype(int).tolist())
    year_filter = st.multiselect("Year level", years)
    st.caption("These filters apply across all pages except the dedicated two-institution comparison.")
    st.divider()
    st.caption("Public read-only app · No contributor contact information is displayed · The underlying Google Sheet is not modified.")

filtered = df.copy()
if inst_filter:
    filtered = filtered[filtered["Institution"].isin(inst_filter)]
if year_filter:
    filtered = filtered[filtered["Year level numeric"].isin(year_filter)]

DISPLAY_COLS = ["Institution", "Module code", "Module name", "Year level", "Semester (0/1/2)", "NQF level", "Credits", "Discipline display", "Category display"]
def show_table(data: pd.DataFrame, columns=DISPLAY_COLS):
    st.dataframe(data[columns].rename(columns={"Discipline display":"Discipline", "Category display":"Module category"}), use_container_width=True, hide_index=True)

def module_details(record: pd.Series):
    st.subheader(f"{record['Module code']} — {record['Module name'] if pd.notna(record['Module name']) else 'Unnamed module'}")
    st.write(f"**Institution:** {record['Institution']} · **Year:** {fmt(record['Year level'])} · **NQF:** {fmt(record['NQF level'])} · **Credits:** {fmt(record['Credits'])} · **Semester:** {fmt(record['Semester (0/1/2)'])}")
    st.write(f"**Primary discipline:** {record['Discipline display']} · **Category:** {record['Category display']}")
    for field in ["Contents", "Outcomes", "Mathematical portion", "Applied portion", "Programming portion", "Software", "Distance Option?"]:
        with st.expander(field, expanded=field in ("Contents", "Outcomes")):
            value = record[field]
            st.write(str(value) if pd.notna(value) else "Not supplied")
    if record["Suggested topics (unverified)"]:
        st.caption("Potential topics inferred automatically from source text; NOT academically validated: " + ", ".join(record["Suggested topics (unverified)"]))

def fmt(value):
    return str(value) if pd.notna(value) else "Not supplied"

if page == "National overview":
    st.header("National overview")
    a,b,c,d = st.columns(4)
    a.metric("Module records", len(filtered))
    b.metric("Institutions represented", filtered["Institution"].nunique())
    c.metric("Primary disciplines", filtered.loc[filtered["Discipline display"]!="Unspecified", "Discipline display"].nunique())
    d.metric("Records with outcomes", filtered["Outcomes"].notna().sum())
    left,right = st.columns(2)
    with left:
        st.subheader("Modules by institution")
        st.bar_chart(filtered["Institution"].value_counts().sort_values(), horizontal=True)
    with right:
        st.subheader("Modules by year level")
        values = filtered["Year level numeric"].dropna().astype(int).value_counts().sort_index()
        st.bar_chart(values)
    st.subheader("Primary discipline distribution")
    st.bar_chart(filtered["Discipline display"].value_counts().head(18), horizontal=True)
    st.subheader("Field completeness")
    fields = ["Module name", "Year level", "NQF level", "Credits", "Contents", "Outcomes", "Mathematical portion", "Applied portion", "Programming portion", "Software", "Module Category", "Discipline"]
    st.bar_chart(pd.Series({field: round(100*filtered[field].notna().mean(), 1) if len(filtered) else 0 for field in fields}, name="% records populated"), horizontal=True)
    st.caption("All graphs count listed module records. They are not measures of teaching quality, student exposure, or curriculum equivalence.")

elif page == "Institution explorer":
    st.header("Institution explorer")
    options=sorted(filtered["Institution"].dropna().unique())
    if not options: st.warning("No institutions match the sidebar filters."); st.stop()
    institution=st.selectbox("Institution", options)
    subset=filtered[filtered["Institution"]==institution]
    st.metric("Listed modules", len(subset))
    st.subheader("Year-level profile")
    st.bar_chart(subset["Year level numeric"].dropna().astype(int).value_counts().sort_index())
    st.subheader("Primary disciplines at this institution")
    st.dataframe(subset.groupby(["Discipline display", "Year level"], dropna=False).size().rename("Module records").reset_index(), use_container_width=True, hide_index=True)
    st.subheader("Module offerings")
    show_table(subset)
    st.caption("A discipline not present here may be embedded within another module, omitted from the submitted data, or genuinely not offered. No conclusion is automatic.")

elif page == "Discipline explorer":
    st.header("Discipline explorer")
    st.caption("This view uses the contributor-provided primary discipline (with limited spelling corrections). Multiple topics in one module may not be captured by this classification.")
    disciplines=sorted(filtered["Discipline display"].unique())
    if not disciplines: st.warning("No disciplines match the filters."); st.stop()
    discipline=st.selectbox("Primary discipline", disciplines)
    subset=filtered[filtered["Discipline display"]==discipline]
    st.metric("Listed modules in selected discipline", len(subset))
    matrix=pd.crosstab(subset["Institution"], subset["Year level numeric"])
    matrix.columns=[f"Year {int(x)}" for x in matrix.columns]
    st.subheader("Institution × year coverage (module counts)")
    st.dataframe(matrix.style.background_gradient(cmap="Blues"), use_container_width=True)
    st.subheader("Matching modules")
    show_table(subset)

elif page == "Compare institutions":
    st.header("Compare institutions")
    options=sorted(df["Institution"].dropna().unique())
    if len(options)<2: st.warning("At least two institutions are needed."); st.stop()
    col1,col2=st.columns(2)
    with col1: ia=st.selectbox("Institution A", options, index=0)
    with col2: ib=st.selectbox("Institution B", options, index=min(1,len(options)-1))
    a=df[df["Institution"]==ia]
    b=df[df["Institution"]==ib]
    if year_filter:
        a=a[a["Year level numeric"].isin(year_filter)]
        b=b[b["Year level numeric"].isin(year_filter)]
    if ia==ib: st.warning("Select different institutions to compare.")
    else:
        st.subheader("Primary discipline coverage")
        counts=pd.concat([a["Discipline display"].value_counts().rename(ia),b["Discipline display"].value_counts().rename(ib)],axis=1).fillna(0).astype(int)
        st.dataframe(counts.style.background_gradient(cmap="Blues", axis=None), use_container_width=True)
        left_only=sorted(set(a["Discipline display"])-set(b["Discipline display"])-{"Unspecified"})
        right_only=sorted(set(b["Discipline display"])-set(a["Discipline display"])-{"Unspecified"})
        common=sorted(set(a["Discipline display"]) & set(b["Discipline display"])-{"Unspecified"})
        st.write(f"**Shared listed primary disciplines ({len(common)}):** {', '.join(common) or 'None recorded'}")
        st.write(f"**Listed only at {ia} ({len(left_only)}):** {', '.join(left_only) or 'None recorded'}")
        st.write(f"**Listed only at {ib} ({len(right_only)}):** {', '.join(right_only) or 'None recorded'}")
        st.caption("'Only' refers strictly to the participating catalogue, not to the absence of teaching at the other institution. Counts are not credit-weighted.")
        c1,c2=st.columns(2)
        with c1: st.subheader(ia); show_table(a)
        with c2: st.subheader(ib); show_table(b)

elif page == "Module browser":
    st.header("Browse and inspect modules")
    query=st.text_input("Search module code, name, contents, outcomes, institution or software")
    subset=filtered
    if query.strip():
        cols=["Institution", "Module code", "Module name", "Contents", "Outcomes", "Software", "Discipline"]
        combined=filtered[cols].fillna("").astype(str).agg(" ".join, axis=1)
        subset=filtered[combined.str.contains(query.strip(), case=False, regex=False)]
    st.caption(f"{len(subset)} matching module records")
    show_table(subset)
    if not subset.empty:
        choices={f"{r['Institution']} · {r['Module code']} · {r['Module name'] if pd.notna(r['Module name']) else '(name not supplied)'} · {r['Record ID']}":idx for idx,r in subset.iterrows()}
        selection=st.selectbox("Open module details", list(choices))
        module_details(df.loc[choices[selection]])

st.divider()
st.caption("Prototype for descriptive institutional benchmarking. Last data cache update occurs when data are fetched, at most once per 24 hours per active Streamlit instance. Academic interpretation remains with the participating departments.")
