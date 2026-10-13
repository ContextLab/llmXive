# Quickstart: Mindfulness Components and Delivery Formats in ASD Social Skills

Project: PROJ-008-psychology-research (meta-analysis of mindfulness
interventions for social skills in children with ASD, age 6-12).

## Prerequisites

- Python 3.11+
- `pip`
- CPU-only environment (<= 7 GB RAM, <= 14 GB disk)

## 1. Establish the project layout (T001)

```bash
python code/setup_project.py
```

This creates (idempotently):

```text
code/{data,analysis,viz,lib,utils,reporting}
data/{raw,processed,results}
docs/ contracts/ tests/{unit,integration,contract}
```

## 2. Install dependencies

```bash
python -m venv venv
source venv/bin/activate # Windows: venv\Scripts\activate
pip install -r requirements.txt
# or, editable install with the pinned project config:
pip install -e code/
```

The dependency manifest is `requirements.txt` (mirroring
`code/pyproject.toml`, which is the authoritative project config per the
constitution's Reproducibility Requirements).

## 3. Run the pipeline (execution order matters)

```bash
# a. Thin-slice check (T002): fetch ONE real ClinicalTrials.gov record
# with submitted results, clean it, and compute Hedges' g
# -> data/results/thin_slice_result.json
python code/data/thin_slice.py

# b. Collect raw study records from ClinicalTrials.gov and OSF
# (rate-limited, exponential backoff; retrieval logged to
# data/raw/retrieval_log.json)
python code/data/collector.py --start-year 2015 --end-year 2024

# c. Clean, filter, and tag studies -> data/processed/cleaned_studies.csv
python code/data/cleaner.py --input data/raw/studies_raw.json --output data/processed/cleaned_studies.csv

# d. Calculate Hedges' g effect sizes -> data/processed/effect_sizes.csv
python code/analysis/effect_sizes.py --input data/processed/cleaned_studies.csv --output data/processed/effect_sizes.csv

# e. Meta-analysis, subgroups, and plots
python code/analysis/meta_analysis.py --input data/processed/effect_sizes.csv --output data/processed/results.json --plots-dir viz/
```

Notes:
- The thin-slice script queries the live ClinicalTrials.gov API v2 and
fails loudly if no real record with usable group summary statistics
(means, SDs, N) is found; it never fabricates an effect size.
- In CI, set `CI_MODE=true`; the collector then loads the canonical
baseline `data/raw/verified_snapshot_2026.json` instead of hitting the
live APIs, so the analysis is deterministic.
- The collector NEVER loads mock data; if `data/raw/mock_registry_response.json`
exists in a production/CI run, the collector aborts loudly.
- If fewer than 10 studies are found, the pipeline automatically
suppresses the funnel plot, Egger's test, and meta-regression, and
produces a descriptive synthesis instead.

## 4. Verify outputs

```bash
python code/data/verify_output.py
pytest tests/
```

## Troubleshooting

- **API limits**: the collector uses exponential backoff (max 5 retries).
If it fails, check connectivity; the full retry history is in the logs.
- **Empty results**: inspect `data/raw/excluded_studies.log` for exclusion
reasons (e.g., age-range mismatch, missing social-skill outcomes).
- **Missing modules**: make sure you activated `venv` and ran
`pip install -r requirements.txt` in the project root.