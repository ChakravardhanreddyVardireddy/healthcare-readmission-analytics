# Hospital Readmissions Analytics (CMS HRRP)

> **Self-directed portfolio project** built on public CMS data as part of a job
> search in business/data analytics. This is not employer work product and
> does not use any proprietary or organizational data.

## Business problem

Hospitals face financial penalties under CMS's Hospital Readmissions
Reduction Program (HRRP) when their 30-day readmission rates for certain
conditions are worse than expected given their patient mix. For a hospital
system's analytics or quality team, the operational questions are:

- Which clinical conditions are driving the most excess (avoidable)
  readmissions across our facilities?
- How does readmission performance vary by state/region, and is that a
  signal of local care-delivery differences or just data noise?
- Which specific facilities have a systemic readmissions problem (poor
  performance across multiple conditions) versus a single-condition
  outlier that may need a more targeted intervention?

This project answers those questions using CMS's own public HRRP dataset.

## Dataset

- **Source**: [CMS Provider Data Catalog](https://data.cms.gov/provider-data/dataset/9n3s-kdb3) — Hospital Readmissions Reduction Program (HRRP), FY2024 measures (performance period 07/01/2021–06/30/2024).
- **Access method**: pulled directly from the live CMS datastore API
  (`https://data.cms.gov/provider-data/api/1/datastore/query/9n3s-kdb3/0`).
- **Scope**: the full public dataset covers 18,330 facility-measure records
  across all 50 states. For this project we pulled a **5-state sample**
  (California, Texas, New York, Florida, Ohio — 2,291 records) to keep the
  project a manageable, reproducible size while still spanning very
  different hospital markets (large/small, urban/rural, different regional
  regulatory environments).
- **Measures covered**: 30-day readmission rates for heart failure (HF),
  pneumonia (PN), COPD, acute myocardial infarction (AMI), CABG surgery,
  and hip/knee replacement.
- Full sourcing and reproduction notes: [`data/DATA_SOURCE.md`](data/DATA_SOURCE.md).

CMS suppresses statistics for hospitals with too few cases per condition
(shown as "N/A" / "Too Few to Report" in the raw data); these are treated
as missing values rather than dropped, so suppression itself is analyzable
(see finding on data completeness below).

## Methodology

1. **Extract** — pull raw JSON/CSV from the CMS datastore API per state (`data/{STATE}.csv`).
2. **Clean** (`scripts/01_clean_data.py`) — standardize column names, coerce
   suppressed/non-numeric values to null, shorten measure codes, and load
   the result into a local SQLite database (`data/hrrp.db`).
3. **Analyze** — descriptive statistics and grouping in both Python
   (`scripts/02_analysis.py`, pandas) and SQL (`sql/readmission_queries.sql`,
   run directly against the SQLite database) to cross-check results.
4. **Visualize** — an interactive HTML/Plotly dashboard (`dashboard/index.html`)
   summarizing the findings below.

## Key findings

- **53.4%** of scored facility-measures (891 of 1,670) had an excess
  readmission ratio above 1.0 — i.e., more readmissions than CMS's
  risk-adjusted model predicted for a comparable hospital.
- **Heart attack (AMI) and heart failure (HF)** are the highest-penalty
  conditions: 58.8% and 57.4% of hospitals scored above 1.0 respectively,
  compared to 46.7% for CABG surgery — the best-performing condition in
  the sample.
- **Heart failure has by far the largest "avoidable readmission" gap**:
  the average predicted rate exceeds the expected rate by 0.31 percentage
  points for HF, roughly 10–30x the gap seen for CABG (0.01 pts) or
  hip/knee replacement (0.03 pts). This points to HF discharge planning
  and post-acute follow-up as the highest-leverage intervention area.
- **State-level performance is relatively tight** (average excess ratio
  ranges from 1.004 in Texas to 1.015 in Florida), suggesting readmission
  performance in this sample is driven more by individual facility
  practices than by broad state-level healthcare system differences.
- **4 facilities in the sample were penalized on every single condition
  they were scored on** (ADVENTHEALTH ORLANDO, MEMORIAL REGIONAL HOSPITAL,
  RIVERSIDE COMMUNITY HOSPITAL, ST BERNARDINE MEDICAL CENTER — each
  scored above 1.0 on all 6 measures), flagging them as candidates for a
  systemic, cross-condition readmissions review rather than a
  single-condition fix.
- **Data completeness varies by state**: 18.5% of Florida's records were
  suppressed for low volume vs. 31.5% of Texas's, meaning cross-state
  comparisons should account for the fact that Texas's sample skews
  toward smaller facilities.

## Recommendations

1. **Prioritize heart failure discharge planning system-wide.** HF has both
   the highest penalty rate and the largest predicted-vs-expected gap; a
   1-point reduction in HF excess readmissions would move more hospitals
   out of penalty status than an equivalent improvement in any other
   condition.
2. **Flag repeat-offender facilities for a systemic quality review.**
   Facilities penalized across 4+ conditions (see
   `sql/readmission_queries.sql`, query 5) likely have process-level
   issues (e.g., discharge instructions, follow-up scheduling) rather than
   condition-specific clinical issues, and should be reviewed
   holistically rather than measure-by-measure.
3. **Treat CABG and hip/knee replacement as the benchmark playbook.**
   These conditions have the lowest penalty rates and smallest
   predicted-expected gaps; the discharge/follow-up protocols used for
   these should be studied and considered for adaptation to
   higher-penalty conditions.
4. **Normalize state comparisons by suppression rate before drawing
   regional conclusions** — apparent state differences may partly reflect
   which states have more small/rural hospitals with suppressed data
   rather than true performance differences.

## Repo structure

```
healthcare-readmission-analytics/
├── data/
│   ├── hrrp_sample.csv         # 300-row representative sample (60/state) shipped in the repo
│   └── DATA_SOURCE.md          # dataset source, API details, sampling methodology
│   (running 01_clean_data.py additionally generates, gitignored:
│    CA.csv/TX.csv/NY.csv/FL.csv/OH.csv raw pulls, hrrp_clean.csv, hrrp.db)
├── scripts/
│   ├── 01_clean_data.py        # fetches live from the CMS API, cleans, loads to SQLite
│   └── 02_analysis.py          # pandas descriptive analysis (prints the findings above)
├── sql/
│   └── readmission_queries.sql # 7 annotated SQL queries against data/hrrp.db
├── dashboard/
│   ├── index.html              # interactive Plotly dashboard (open directly in a browser)
│   └── chart_data.json         # the underlying chart data, pre-computed from the analysis
├── requirements.txt
├── .gitignore
└── LICENSE
```

## Running this project

```bash
pip install -r requirements.txt
python scripts/01_clean_data.py     # fetches fresh data from CMS, builds hrrp_clean.csv + hrrp.db
python scripts/02_analysis.py       # prints the key findings
sqlite3 data/hrrp.db < sql/readmission_queries.sql   # or run queries interactively
open dashboard/index.html           # view the interactive dashboard
```

`data/hrrp_sample.csv` (300 rows) ships in the repo for quick inspection
without running the scripts; the full 2,291-row dataset and SQLite database
are regenerated locally by `01_clean_data.py` and are gitignored to keep the
repository lean.

## Tools

Python (pandas), SQL (SQLite), HTML/Plotly for the dashboard. Built as a
demonstration of end-to-end analytics skill — data extraction from a
public API, cleaning, SQL + Python analysis, and dashboard delivery — for
healthcare-sector business/data analyst roles.
