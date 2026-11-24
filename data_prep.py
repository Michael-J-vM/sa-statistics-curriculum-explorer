"""Preserve catalogue content; normalise only specified display categories."""
from __future__ import annotations
import io
import re
import pandas as pd

COLUMNS = ["Institution", "Information provider", "Module code", "Module name", "Year level", "Semester (0/1/2)", "Distance Option?", "NQF level", "Credits", "Contents", "Outcomes", "Mathematical portion", "Applied portion", "Programming portion", "Software", "Module Category", "Discipline"]
PUBLIC_COLUMNS = [c for c in COLUMNS if c != "Information provider"]
DISCIPLINE_ALIASES = {"Aplied: Biostatistics": "Applied: Biostatistics", "Generalized Linear Models": "Generalised Linear Models", "Nonparametric statistics": "Nonparametric Statistics"}
TOPIC_GROUPS = {"Probability Theory": ["probability", "distribution theory"], "Regression": ["regression", "linear model"], "Time Series Analysis": ["time series", "forecasting", "arima"], "Bayesian Statistics": ["bayesian", "posterior"], "Machine Learning": ["machine learning", "statistical learning"], "Multivariate Statistics": ["multivariate", "principal component"], "Stochastic Processes": ["stochastic", "markov"], "Sampling Theory": ["sampling", "survey sampling"], "Survival Analysis": ["survival", "hazard function"], "Generalised Linear Models": ["generalized linear model", "generalised linear model", "glm"]}

def prepare(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]
    for col in COLUMNS:
        if col not in df.columns:
            df[col] = pd.NA
    # Forward fill the institution for rows where the spreadsheet groups entries under one institution.
    # Users must still inspect these inherited values when validating the source.
    df = df.dropna(how="all", subset=["Institution", "Module code", "Module name"])
    df["Institution"] = df["Institution"].replace(r"^\s*$", pd.NA, regex=True).ffill()
    for col in COLUMNS:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
        df[col] = df[col].replace(["", "None", "none", "N/A", "n/a", "nan"], pd.NA)
    df = df.loc[df["Institution"].notna() & df["Module code"].notna()].copy()
    df["Discipline display"] = df["Discipline"].map(lambda x: DISCIPLINE_ALIASES.get(x, x) if pd.notna(x) else "Unspecified")
    df["Category display"] = df["Module Category"].fillna("Unspecified")
    for field in ("Year level", "NQF level", "Credits"):
        df[field + " numeric"] = pd.to_numeric(df[field], errors="coerce")
    # Separate "subject inferred from free text" from contributor-provided primary discipline.
    def topics(r):
        body = " ".join(str(r[k]) for k in ("Module name", "Contents", "Outcomes") if pd.notna(r[k])).lower()
        return [label for label, words in TOPIC_GROUPS.items() if any(re.search(r"\b" + re.escape(w) + r"\b", body) for w in words)]
    df["Suggested topics (unverified)"] = df.apply(topics, axis=1)
    df["Record ID"] = [f"record-{i}" for i in range(1, len(df)+1)]
    return df.reset_index(drop=True)

def load_csv(binary: bytes, strict_public_headers: bool = False) -> pd.DataFrame:
    raw = pd.read_csv(io.BytesIO(binary), dtype=str, keep_default_na=False, encoding="utf-8-sig")
    raw.columns = [str(c).strip() for c in raw.columns]
    if strict_public_headers:
        missing = [c for c in PUBLIC_COLUMNS if c not in raw.columns]
        if missing:
            raise ValueError("The public CSV is missing these expected column headings: " + ", ".join(missing) + ". Check that headers are in row 1 and the import formula begins in row 2.")
    # Do not retain any unrequested extra public columns in memory.
    return prepare(raw[[c for c in PUBLIC_COLUMNS if c in raw.columns]].copy())

def public_data(df: pd.DataFrame) -> pd.DataFrame:
    return df.drop(columns=["Information provider"], errors="ignore")
