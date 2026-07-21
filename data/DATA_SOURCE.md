# Data source & methodology notes

## Source

CMS Provider Data Catalog — **Hospital Readmissions Reduction Program (HRRP)**
Dataset page: https://data.cms.gov/provider-data/dataset/9n3s-kdb3
Dataset ID: `9n3s-kdb3`
Performance period covered: 07/01/2021 – 06/30/2024 (FY2024 measures)

This is a public, freely licensed U.S. government dataset published by the
Centers for Medicare & Medicaid Services (CMS). No authentication or API
key is required.

## API access

Data was pulled directly from the live CMS datastore query API:

```
GET https://data.cms.gov/provider-data/api/1/datastore/query/9n3s-kdb3/0
    ?conditions[0][property]=state
    &conditions[0][value]=<STATE_ABBR>
    &conditions[0][operator]==
    &limit=500
    &format=csv
```

Example (California):
```
https://data.cms.gov/provider-data/api/1/datastore/query/9n3s-kdb3/0?conditions[0][property]=state&conditions[0][value]=CA&conditions[0][operator]=%3D&limit=500&format=csv
```

## Sampling methodology

The full dataset contains **18,330** facility-measure records across all
50 states + DC/territories. To keep this portfolio project reproducible
and reviewable in a reasonable time, we pulled a **5-state sample**
covering large, geographically diverse hospital markets:

| State | Records pulled | Total records saved after cleaning |
|-------|-----------------|-------------------------------------|
| California (CA) | up to 500 | 454 |
| Texas (TX)       | up to 500 | 448 |
| New York (NY)    | up to 500 | 459 |
| Florida (FL)     | up to 500 | 465 |
| Ohio (OH)        | up to 500 | 465 |
| **Total**        |           | **2,291** |

Each state's pull was capped at 500 records per API call (a practical
limit for a single request); where a state's true row count exceeds that
(e.g., California has 1,662 total facility-measure rows), the sample
reflects the first ~450-465 rows returned by the API in its default
sort order, not a random sample of that state. This is disclosed here for
transparency — conclusions in the README are described as applying to
"this 5-state sample," not to national HRRP performance.

`data/hrrp_sample.csv` is a smaller 300-row cut (60 hospitals randomly
sampled per state, seed=42) included for quick spreadsheet inspection
without needing to open the full 2,291-row file.

## Fields

| Column | Description |
|---|---|
| `facility_name` | Hospital name |
| `facility_id` | CMS CCN facility identifier |
| `state` | Two-letter state code |
| `measure_name` | Readmission measure (condition), e.g. `READM-30-HF` |
| `number_of_discharges` | Discharges used to compute the measure (suppressed if too small) |
| `excess_readmission_ratio` | Predicted / expected readmission rate. >1.0 = worse than expected |
| `predicted_readmission_rate` | Model-predicted 30-day readmission rate for this hospital |
| `expected_readmission_rate` | Rate expected for an average hospital with this hospital's case mix |
| `number_of_readmissions` | Observed readmissions (suppressed if too small) |
| `start_date` / `end_date` | Performance period |

## Reproducing this dataset

Re-run the same API calls for any state (or add more states) and re-run
`scripts/01_clean_data.py` to regenerate `hrrp_clean.csv` and `hrrp.db`.
