"""
01_clean_data.py

Fetches the CMS Hospital Readmissions Reduction Program (HRRP) records for a
5-state sample (CA, TX, NY, FL, OH) directly from the live CMS API, cleans
and standardizes them, and loads the result into a local SQLite database for
SQL analysis.

Data source
-----------
CMS Provider Data Catalog - Hospital Readmissions Reduction Program (HRRP)
Dataset ID: 9n3s-kdb3
API endpoint used:
  https://data.cms.gov/provider-data/api/1/datastore/query/9n3s-kdb3/0
Fields: facility_name, facility_id, state, measure_name (readmission
condition), number_of_discharges, excess_readmission_ratio,
predicted_readmission_rate, expected_readmission_rate,
number_of_readmissions, start_date, end_date.

The full public dataset contains 18,330 facility-measure records across
all 50 states. For this portfolio project we pull a representative 5-state
sample (CA, TX, NY, FL, OH - ~2,300 records) directly from the live CMS
API. See data/DATA_SOURCE.md for full methodology notes.

Usage
-----
python scripts/01_clean_data.py
"""

from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATES = ["CA", "TX", "NY", "FL", "OH"]

API_BASE = "https://data.cms.gov/provider-data/api/1/datastore/query/9n3s-kdb3/0"

NUMERIC_COLUMNS = [
    "number_of_discharges",
    "excess_readmission_ratio",
    "predicted_readmission_rate",
    "expected_readmission_rate",
    "number_of_readmissions",
]


def fetch_state(state: str, limit: int = 500) -> pd.DataFrame:
    """Pull one state's HRRP records directly from the live CMS API."""
    params = {
        "conditions[0][property]": "state",
        "conditions[0][value]": state,
        "conditions[0][operator]": "=",
        "limit": limit,
        "format": "csv",
    }
    url = f"{API_BASE}?{urlencode(params)}"
    print(f"  Fetching {state} from CMS API...")
    with urlopen(url, timeout=30) as resp:
        raw_text = resp.read().decode("utf-8")

    # Save the raw pull for reference/reproducibility, then parse it.
    raw_path = DATA_DIR / f"{state}.csv"
    raw_path.write_text(raw_text, encoding="utf-8")
    return pd.read_csv(raw_path, engine="python", on_bad_lines="skip")


def load_raw() -> pd.DataFrame:
    """Fetch and concatenate the per-state pulls from the live CMS API.

    Falls back to any already-downloaded data/{STATE}.csv files if the
    live API isn't reachable (e.g. offline development).
    """
    frames = []
    for state in STATES:
        try:
            df = fetch_state(state)
        except Exception as exc:  # network unavailable, rate-limited, etc.
            path = DATA_DIR / f"{state}.csv"
            if path.exists():
                print(f"  ({state}: live fetch failed ({exc}), using cached {path.name})")
                df = pd.read_csv(path, engine="python", on_bad_lines="skip")
            else:
                raise RuntimeError(
                    f"Could not fetch {state} from CMS API and no cached "
                    f"file found at {path}"
                ) from exc
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Standardize column names, coerce numeric fields, tidy measure labels."""
    df = df.copy()
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # CMS marks suppressed / low-volume cells as "N/A" or "Too Few to Report".
    # Coerce these to NaN rather than dropping rows, so suppression itself
    # remains analyzable (e.g. how many hospitals are too small to score).
    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Shorten measure codes for readability: READM-30-HF-HRRP -> READM-30-HF
    df["measure_name"] = df["measure_name"].str.replace("-HRRP", "", regex=False)

    return df


def main():
    raw = load_raw()
    print(f"Loaded {len(raw)} raw facility-measure records "
          f"across {raw['State'].nunique()} states")

    clean_df = clean(raw)
    clean_path = DATA_DIR / "hrrp_clean.csv"
    clean_df.to_csv(clean_path, index=False)
    print(f"Wrote cleaned data to {clean_path} ({clean_df.shape[0]} rows)")

    db_path = DATA_DIR / "hrrp.db"
    import sqlite3
    conn = sqlite3.connect(db_path)
    clean_df.to_sql("readmissions", conn, if_exists="replace", index=False)
    conn.close()
    print(f"Loaded cleaned data into SQLite database at {db_path}")


if __name__ == "__main__":
    main()
