# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-10-21 | **Spec**: `specs/001-evaluating-the-statistical-validity-of-p/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-statistical-validity-of-p/spec.md`

## Summary
The pipeline will (1) ingest a user‑provided CSV of URLs, (2) scrape each public A/B test summary, (3) extract the required fields into `ABSummary` records, (4) reconstruct p‑values and effect sizes using the appropriate statistical test, (5) flag inconsistencies according to the absolute 0.05 p‑value threshold mandated by Constitution VI, (6) compute overall and bias‑adjusted inconsistency prevalence (binomial test, sensitivity analysis, domain weighting), (7) validate every statistical routine with a high‑replication Monte Carlo simulation **(FR‑026 – synthetic validation dataset generation and independent Monte‑Carlo validation)**, (8) generate a synthetic validation set (a large number of records) with independent ground truth **(FR‑030)**, (9) evaluate extraction accuracy on a manually annotated real‑world set (≥ 100 summaries) **(FR‑031b)**, and (10) export JSON and CSV artifacts while remaining within the GitHub Actions free‑tier limits (≤ 2 vCPUs, ≤ 2 GB RAM, ≤ 6 h runtime).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `requests`, `beautifulsoup4`, `scipy`, `statsmodels`, `pyyaml`, `pytest`  
- **Storage**: Local filesystem (`data/` for inputs & intermediates, `output/` for results)  
- **Testing**: `pytest` with contract tests (YAML schemas) and integration tests  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (CPU‑only)  
- **Project Type**: CLI/Data‑pipeline library  
- **Performance Goals**: Full audit of ≥ 300 summaries ≤ 6 h, memory ≤ 2 GB  
- **Constraints**: No GPU, strict adherence to Constitution VI absolute p‑value floor, domain bias ≤ 30 % (FR‑027)  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| **I. Reproducibility** | All code lives under `src/`, `requirements.txt` pins exact versions, random seeds are fixed in `config.yaml`. The CI workflow runs the full pipeline from scratch on every push. |
| **II. Verified Accuracy** | Citations (Kohavi 2020, John 2022) are validated by the Reference‑Validator before inclusion in any report. |
| **III. Data Hygiene** | Raw inputs (`data/input/urls.csv`) are checksummed (`data/checksums.txt`). Every transformation writes a new file; original files remain untouched. |
| **IV. Single Source of Truth** | Every statistic in the final paper will be derived from `output/audit_report.json` and `output/summary_report.csv`. No hand‑typed numbers are permitted. |
| **V. Versioning Discipline** | Each artifact’s SHA‑256 is recorded in `output/checksums.txt` and the project state file is updated on change. |
| **VI. Statistical Consistency Verification** | The inconsistency flag uses the absolute 0.05 p‑value rule (FR‑004, Constitution VI). Monte Carlo validation (**FR‑026**) guarantees implementation fidelity; the synthetic dataset used for Monte Carlo is generated independently of the reconstruction code (see Research). |
| **VII. Source Provenance & Transparency** | Every `ABSummary` stores the original URL, `source_domain`, and extraction timestamp; the provenance is carried through to all reports. |

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
├── statistics/          # Reconstruction logic (FR‑003, FR‑004)
├── validation/          # Synthetic generator, Monte Carlo, real‑world eval (FR‑030‑031b, FR‑026)
├── reporting/           # JSON/CSV export, bias adjustment, subgroup analysis (FR‑005‑032)
├── cli/                 # `run_audit` entry point
└── config/              # thresholds, random seeds, domain limits

tests/
├── contract/            # Schema validation tests
├── unit/                # Statistical functions
└── integration/         # End‑to‑end pipeline test

data/
├── input/               # `urls.csv` supplied by the user
├── synthetic/           # Generated synthetic validation set
├── real_world/          # Human‑annotated extraction set
└── checksums.txt        # SHA‑256 of raw inputs

output/
├── audit_report.json
├── summary_report.csv
├── bias_report.json
├── subgroup_report.json
└── checksums.txt        # SHA‑256 of all outputs
```

**Structure Decision**: A single‑project layout keeps the CI footprint minimal and aligns with the CLI nature of the tool.

## Complexity Tracking
- **Memory**: All data structures (< 10 000 rows) occupy < 200 MB.  
- **CPU**: Monte Carlo (a substantial number of replicates) ≈ 1.5 CPU‑hours; extraction of several hundred URLs ≈ 0.5 CPU‑hours. Total < 3 CPU‑hours.  
- **Disk**: Synthetic CSV ≈ moderate size; all other artifacts < 10 MB. Well under the 14 GB limit.  
- **GPU**: Not required; all libraries are CPU‑only.  

## Task Registry (selected)
| Task ID | Description | Phase | Status |
|---------|-------------|-------|--------|
| T026 | Generate synthetic validation dataset (10 000 records) via `src/validation/synthetic_generator.py` | Phase 3 V02 | Planned |
| T044 | Power‑analysis calculation confirming N ≥ 300 | Phase 0 R04 | Planned |
| T062 | Monte Carlo validation of statistical tests (10 000 replicates) | Phase 3 V01 | Planned |
| T076 | Input data checksumming (`data/checksums.txt`) | Phase 4 C02 | Planned |
| T077 | Output artifact checksumming (`output/checksums.txt`) | Phase 4 C03 | Planned |
| T081 | Create manually annotated real‑world extraction set (≥ 100 summaries) | Phase 3 V04 | Planned |
| T082 | Evaluate extraction accuracy on real‑world set | Phase 3 V04 | Planned |
| T083 | Quickstart runner verification (≤ 30 min on 30 URLs) | Phase 4 C04 | Planned |
| T099 | Constitution compliance audit (Principles I‑VII) | Phase 3 V05 | Planned |

## Implementation Phases

### Phase 0 – Research & Validation Setup
1. **R01** – Verify that `scipy` and `statsmodels` run within ≤ 2 GB RAM on the default runner.  
2. **R02** – Design the synthetic generator (independent of the reconstruction code) and lock a random seed.  
3. **R03** – Draft the annotation protocol for the real‑world validation set (two annotators + resolver).  
4. **R04** – Compute the required N for [deferred] power detecting a 0.10 inconsistency proportion (≥ 300).

### Phase 1 – Data Model & Contracts
1. **D01** – Formalise `ABSummary`, `AuditRecord`, and `SummaryReport` as JSON/YAML schemas (see `contracts/`).  
2. **D02** – Write the Quickstart guide (FR‑028) and embed a runtime check that 30 URLs finish ≤ 30 min on the runner.  
3. **D03** – Add contract tests that validate output files against the schemas.  

### Phase 2 – Core Implementation
1. **I01** – URL ingestion (`src/extraction/loader.py`) and HTML parsing (`src/extraction/parser.py`).  
2. **I02** – Reconstruction module (`src/statistics/reconstruct.py`) implementing two‑proportion z/Fisher and Welch t‑test.  
3. **I03** – Inconsistency logic (`src/statistics/inconsistency.py`) applying the absolute 0.05 p‑value rule and the [deferred] effect‑size relative rule.  
4. **I04** – Domain bias handling (`src/reporting/bias.py`): compute domain proportions using the `source_domain` field (present in `ABSummary`), subsample if > 30 %, calculate bias‑adjusted rate.  
5. **I05a** – Prevalence estimation (`src/reporting/prevalence.py`): binomial test, Wilson CI, sensitivity sweep (0.02‑0.10).  
6. **I05b** – Reporting module (`src/reporting/export.py`) writes `audit_report.json`, `summary_report.csv`, `bias_report.json`, `subgroup_report.json`.  
7. **I06** – Logging utilities (`src/config/logger.py`) emit `ERR‑###` codes with ≤ 200‑char messages (FR‑007).  

### Phase 3 – Validation & Testing
1. **V01** – Monte Carlo validation (a substantial number of replicates) for each statistical routine; compare to `scipy` results (FR‑026, SC‑003).  
2. **V02** – **Synthetic dataset generation** (`src/validation/synthetic_generator.py`) producing exactly 10 000 records and `synthetic_ground_truth.json`. **Independence Note:** The generator uses direct random draws (`numpy.random`) and closed‑form calculations (`scipy.stats`) **without** invoking the reconstruction code from FR‑003, ensuring true independence for validation.  
3. **V03** – Run the detector on the synthetic set, compute precision/recall/F1, enforce ≥ 90 % / ≥ 80 % / ≥ 0.85 (FR‑031).  
4. **V04** – Execute extraction on the manually annotated real‑world set, compute precision/recall/F1, enforce ≥ 85 % / ≥ 75 % / ≥ 0.80 (FR‑031b, SC‑031b).  
5. **V05** – Constitution compliance audit (Task T099) that checks all seven principles.  

### Phase 4 – CI & Documentation
1. **C01** – GitHub Actions workflow (`.github/workflows/audit.yml`) installs dependencies, runs `run_audit.py`, captures resource usage, and fails if limits are exceeded.  
2. **C02** – Compute SHA‑256 checksums for every input file (`data/checksums.txt`).  
3. **C03** – Compute SHA‑256 checksums for every output file (`output/checksums.txt`).  
4. **C04** – Run the Quickstart verification (Task T083) on the runner; abort if runtime > 30 min.  
5. **C05** – Log CPU time, peak memory, and total runtime to `manifest.json` (SC‑013, SC‑008).  

## Compute Feasibility
- **Memory**: All data structures (< 10 000 rows) occupy < 200 MB.  
- **CPU**: Monte Carlo (10 k replicates) ≈ 1.5 CPU‑hours; extraction of 300 URLs ≈ 0.5 CPU‑hours. Total < 3 CPU‑hours.  
- **Disk**: Synthetic CSV ≈ tens of megabytes; all other artifacts < 10 MB. Well under the 14 GB limit.  
- **GPU**: Not required; all libraries are CPU‑only.  

