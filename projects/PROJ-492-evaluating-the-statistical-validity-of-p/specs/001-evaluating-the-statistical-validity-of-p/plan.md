# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-10-21 | **Spec**: `specs/001-evaluating-the-statistical-validity-of-p/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-statistical-validity-of-p/spec.md`

## Summary
The pipeline will (1) ingest a CSV of URLs supplied by the user, (2) scrape each public A/B test summary, (3) extract the required fields into `ABSummary` records, (4) reconstruct p‑values and effect sizes using the appropriate statistical test, (5) flag inconsistencies according to the absolute 0.05 p‑value rule (Constitution VI) and the effect‑size rule, (6) compute the overall inconsistency prevalence with a two‑sided binomial test and a Wilson confidence interval, (7) perform a sensitivity sweep of the baseline proportion (0.02 – 0.10), (8) validate every statistical routine with a 10 000‑replicate Monte Carlo simulation, (9) evaluate extraction accuracy on a manually annotated real‑world validation set (≥ 100 summaries), and (10) export JSON and CSV artifacts while staying within the default GitHub Actions runner limits (≤ 2 vCPUs, ≤ 2 GB RAM, ≤ 6 h).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `requests`, `beautifulsoup4`, `scipy`, `statsmodels`, `pyyaml`, `pytest`  
- **Storage**: Local filesystem (`data/` for inputs & intermediates, `output/` for results)  
- **Testing**: `pytest` with contract‑based schema tests  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (CPU‑only)  
- **Project Type**: CLI/Data‑pipeline library  
- **Performance Goals**: Audit ≥ 300 summaries ≤ 6 h, memory ≤ 2 GB  
- **Constraints**: No GPU, strict adherence to Constitution VI absolute p‑value floor, no invented dataset URLs  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | All code lives under `src/`, `requirements.txt` pins exact versions, random seeds are fixed in `config.yaml`. The CI workflow runs the full pipeline from scratch on every push. |
| **II. Verified Accuracy** | Citations (Kohavi 2020, John 2022) are validated by the Reference‑Validator before inclusion in any report. |
| **III. Data Hygiene** | Raw inputs (`data/input/urls.csv`) are checksummed (`data/checksums.txt`). Every transformation writes a new file; originals remain untouched. |
| **IV. Single Source of Truth** | Every statistic in the final report is derived from `output/audit_report.json` and `output/summary_report.csv`. No hand‑typed numbers are permitted. |
| **V. Versioning Discipline** | Each artifact’s SHA‑256 is recorded in `output/checksums.txt` and the project state file is updated on change. |
| **VI. Statistical Consistency Verification** | The inconsistency flag uses the absolute 0.05 p‑value rule (FR‑004, Constitution VI). Monte Carlo validation (FR‑026) guarantees implementation fidelity. |
| **VII. Source Provenance & Transparency** | Every `ABSummary` stores the original URL and extracted domain; provenance is carried through to all reports. |

## Project Structure
```
specs/001-evaluating-the-statistical-validity-of-p/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── ABSummary.schema.yaml
    ├── AuditRecord.schema.yaml
    └── SummaryReport.schema.yaml

src/
├── extraction/          # URL fetching & HTML parsing (FR‑001, FR‑002)
├── statistics/          # Reconstruction & inconsistency logic (FR‑003‑004b)
├── validation/          # Monte‑Carlo validation (FR‑026) & real‑world extraction eval (FR‑031b)
├── reporting/           # JSON/CSV export, prevalence test, sensitivity sweep (FR‑005a‑005b, FR‑024)
├── cli/                 # `run_audit` entry point
└── config/              # thresholds, random seeds, logger config (FR‑007)

tests/
├── contract/            # Schema validation tests
├── unit/                # Statistical functions
└── integration/         # End‑to‑end pipeline test
```

## Complexity Tracking
- **Memory**: All in‑memory tables (< 10 000 rows) < 200 MB.  
- **CPU**: Monte Carlo (10 k replicates) ≈ 1.5 CPU‑hours; URL extraction for ≥ 300 summaries ≈ 0.5 CPU‑hours. Total < 3 CPU‑hours.  
- **Disk**: All artifacts < 10 MB, well under the 14 GB runner limit.  
- **GPU**: Not required; all libraries are CPU‑only.  

## Task Registry (selected)
| Task ID | Description | Phase | Status |
|---------|-------------|-------|--------|
| T044 | Power‑analysis confirming N ≥ 300 for the binomial prevalence test (FR‑025) | Phase 0 | Planned |
| T062 | Monte Carlo validation of statistical tests (10 000 replicates) (FR‑026) | Phase 3 | Planned |
| T076 | Compute SHA‑256 checksums for all input files (`data/checksums.txt`) | Phase 4 | Planned |
| T077 | Compute SHA‑256 checksums for all output files (`output/checksums.txt`) | Phase 4 | Planned |
| T081 | Create manually annotated extraction validation set (≥ 100 summaries) (FR‑031b) | Phase 3 | Planned |
| T082 | Evaluate extraction precision/recall/F1 on the validation set (SC‑031b) | Phase 3 | Planned |
| T083 | Quickstart verification: run the pipeline on 30 URLs within 30 min (FR‑028) | Phase 4 | Planned |
| T099 | Constitution compliance audit (Principles I‑VII) | Phase 3 | Planned |

## Implementation Phases

### Phase 0 – Research & Validation Setup
1. **R01** – Verify that `scipy` and `statsmodels` run within ≤ 2 GB RAM on the default runner.  
2. **R02** – Design the Monte Carlo validation harness (independent synthetic data generator).  
3. **R03** – Draft the annotation protocol for the real‑world extraction set (two annotators + resolver).  
4. **R04** – Compute the required sample size N for a two‑sided binomial test detecting an inconsistency proportion of 0.10 with α = 0.05 and power ≥ 0.80 (FR‑025).  

### Phase 1 – Data Model & Contracts
1. **D01** – Formalise `ABSummary`, `AuditRecord`, and `SummaryReport` as JSON/YAML schemas (see `contracts/`).  
2. **D02** – Write the Quickstart guide (FR‑028) and embed a runtime check that 30 URLs finish ≤ 30 min on the runner.  
3. **D03** – Add contract tests that validate `audit_report.json` and `summary_report.csv` against the schemas.  

### Phase 2 – Core Implementation
1. **I01** – URL ingestion (`src/extraction/loader.py`) and HTML parsing (`src/extraction/parser.py`).  
2. **I02** – Extraction module populates `ABSummary` records (FR‑001, FR‑002).  
3. **I03** – Reconstruction module (`src/statistics/reconstruct.py`) implements:  
   - Two‑proportion z‑test (or Fisher’s exact when any cell ≤ 5) for binary outcomes.  
   - Welch’s two‑sample t‑test for continuous outcomes. (FR‑003)  
4. **I04** – Inconsistency logic (`src/statistics/inconsistency.py`) applies:  
   - Absolute p‑value difference > 0.05 → flag.  
   - Effect‑size relative difference > 5 % of the larger magnitude → flag.  
   - Sample‑size mismatch > 5 % → `data_quality_warning` in notes (FR‑004b).  
5. **I05** – Prevalence estimation (`src/reporting/prevalence.py`):  
   - Two‑sided binomial test against baseline 0.05 (FR‑005a).  
   - Wilson 95 % confidence interval.  
   - Sensitivity sweep for baseline values 0.02–0.10 (step 0.01) (FR‑005b).  
6. **I06** – Reporting module (`src/reporting/export.py`) writes:  
   - `output/audit_report.json` (per FR‑024).  
   - `output/summary_report.csv` (per FR‑024).  
   - `output/manifest.json` with resource usage (SC‑013).  
7. **I07** – Logging utilities (`src/config/logger.py`) emit clear `ERR‑###` messages ≤ 200 chars (FR‑007).  

### Phase 3 – Validation & Testing
1. **V01** – Monte Carlo validation (Task T062): generate independent synthetic data, run each statistical routine 10 000 times, compare library result to Monte Carlo estimate; require absolute difference ≤ 0.005 (SC‑003, SC‑026).  
2. **V02** – Execute extraction on the manually annotated real‑world set (Task T081) and compute precision, recall, F1; require precision ≥ 85 % and recall ≥ 75 % (F1 ≥ 0.80) (SC‑031b).  
3. **V03** – Run the full pipeline on a sample corpus (≥ 300 summaries) and verify that:  
   - Parsing‑error rate ≤ 5 % (SC‑005).  
   - All success criteria (SC‑001, SC‑014, SC‑015, SC‑024, SC‑025, SC‑028) are met.  
4. **V04** – Constitution compliance audit (Task T099) checks adherence to all seven principles.  

### Phase 4 – CI & Documentation
1. **C01** – GitHub Actions workflow (`.github/workflows/audit.yml`) installs dependencies, runs `run_audit.py`, captures `cpu_time_seconds`, `memory_peak_mb`, `runtime_seconds`, and fails if limits are exceeded (SC‑008).  
2. **C02** – Compute SHA‑256 checksums for every input file (`data/checksums.txt`) (Task T076).  
3. **C03** – Compute SHA‑256 checksums for every output file (`output/checksums.txt`) (Task T077).  
4. **C04** – Run the Quickstart verification (Task T083); abort if runtime > 30 min.  
5. **C05** – Populate `output/manifest.json` with run ID, timestamps, status, file list, checksums, and resource usage (SC‑013).  

## Compute Feasibility
- **Memory**: < 200 MB throughout.  
- **CPU**: < 3 CPU‑hours total (well under the 6‑hour wall‑clock limit).  
- **Disk**: < 15 MB total output + input.  
- **GPU**: Not required; all steps run on CPU‑only packages.  

---===END PLAN===---
