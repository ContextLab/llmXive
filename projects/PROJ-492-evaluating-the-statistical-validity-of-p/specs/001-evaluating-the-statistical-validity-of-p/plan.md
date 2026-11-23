# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-10-25 | **Spec**: `specs/001-evaluating-the-statistical-validity-of-p/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-statistical-validity-of-p/spec.md`

## Summary
The audit pipeline will (1) ingest a CSV of URLs, (2) download and parse each public A/B test summary, (3) extract required fields into `ABSummary` records, (4) reconstruct p‑values and effect sizes using the appropriate statistical test (two‑proportion z/Fisher for binary outcomes, Welch’s t for continuous outcomes), (5) flag inconsistencies according to the **absolute 0.05 p‑value floor** and the [deferred] relative effect‑size rule (Constitution VI, FR‑004), (6) compute the overall inconsistency prevalence with a two‑sided binomial test and a Wilson 95 % confidence interval (FR‑005a), (7) run a sensitivity sweep of the baseline proportion (FR‑005b), (8) validate every statistical routine with a high‑replication Monte Carlo simulation (FR‑026), (9) evaluate extraction accuracy on a manually annotated validation set (FR‑031b), (10) export JSON and CSV artifacts while staying within the default GitHub Actions runner limits (FR‑009, FR‑028). All functional requirements (FR‑001‑FR‑004b, FR‑005a‑FR‑005b, FR‑007, FR‑009, FR‑012, FR‑024, FR‑025, FR‑026, FR‑028, FR‑031b) and success criteria (SC‑001‑SC‑003, SC‑005‑SC‑008, SC‑013‑SC‑015, SC‑024‑SC‑028, SC‑031b) are explicitly addressed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas`, `requests`, `beautifulsoup4`, `scipy`, `statsmodels`, `numpy`, `pyyaml`, `pytest`  
- **Storage**: Local filesystem (`data/` for inputs & intermediates, `output/` for results)  
- **Testing**: `pytest` with contract‑based schema validation (`contracts/*.schema.yaml`)  
- **Target Platform**: Ubuntu‑latest GitHub Actions runner (CPU‑only)  
- **Project Type**: CLI/Data‑pipeline library  
- **Performance Goals**: Audit ≥ 300 summaries ≤ 6 h, memory ≤ 2 GB, no GPU usage  
- **Constraints**: Must honor Constitution VI absolute 0.05 p‑value floor; must not invent dataset URLs; must respect FR‑009 resource caps.

## Constitution Check
| Principle | Compliance Statement |
|-----------|----------------------|
| **I. Reproducibility** | All code lives under `src/`, `requirements.txt` pins exact versions, random seeds are fixed in `config.yaml`. The CI workflow runs the full pipeline from scratch on every push. |
| **II. Verified Accuracy** | Citations (Kohavi 2020, John 2022) are validated by the Reference‑Validator before inclusion in any report. |
| **III. Data Hygiene** | Raw inputs (`data/input/urls.csv`) are checksummed (`data/checksums.txt`). Every transformation writes a new file; originals remain untouched. |
| **IV. Single Source of Truth** | Every statistic in the final report is derived from `output/audit_report.json` and `output/summary_report.csv`. No hand‑typed numbers are permitted. |
| **V. Versioning Discipline** | Each artifact’s SHA‑256 is recorded in `output/checksums.txt` and the project state file is updated on change. |
| **VI. Statistical Consistency Verification** | Inconsistency flag uses the **non‑negotiable absolute 0.05 p‑value floor** (FR‑004, Constitution VI). Effect‑size inconsistency uses the [deferred] relative rule (FR‑004). |
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
├── extraction/
│   ├── loader.py          # T017 – curate corpus
│   └── parser.py          # URL download & HTML parsing
├── statistics/
│   ├── reconstruct.py     # p‑value & effect‑size reconstruction (FR‑003, FR-012)
│   ├── inconsistency.py   # flagging logic (FR‑004, FR‑004b)
│   └── monte_carlo.py     # T004 – Monte Carlo validation (FR‑026)
├── reporting/
│   ├── prevalence.py      # binomial test & sensitivity sweep (FR‑005a‑b)
│   └── export.py          # JSON & CSV export (FR‑024)
├── config/
│   └── logger.py          # error logging (FR‑007)
└── run_audit.py           # orchestrates all phases

tests/
├── contract/
│   └── test_contracts.py  # schema validation
└── integration/
    └── test_end_to_end.py # full pipeline on a 30‑URL sample
```

## Complexity Tracking
| Aspect | Estimate |
|--------|----------|
| **Memory** | < 200 MB (all DataFrames ≤ 10 k rows) |
| **CPU** | Monte Carlo (≈ 1.2 CPU‑h), URL download & extraction (≈ 0.6 CPU‑h), prevalence & reporting (≈ 0.2 CPU‑h) → total < 2 CPU‑h |
| **Disk** | All artifacts < 15 MB |
| **GPU** | Not required (CPU‑only libraries) |

## Implementation Phases

### Phase 0 – Research & Validation Setup
| Task ID | Description | FR/SC addressed |
|---------|-------------|-----------------|
| **R01** | Verify that `scipy`/`statsmodels` run within ≤ 2 GB RAM on the default runner. | FR‑009, SC‑008 |
| **R02** | Design Monte Carlo harness that generates synthetic data independent of the production code. | FR‑026, SC‑003, SC‑026 |
| **R03** | Draft annotation protocol for the real‑world extraction validation set (≥ 100 summaries, stratified across five domains). | FR‑031b, SC‑031b |
| **R04** | Compute exact sample‑size requirement for the binomial prevalence test (power ≥ 0.80, α = 0.05, target proportion 0.10). | FR‑025, SC‑025 |

### Phase 1 – Data Model & Contracts
| Task ID | Description | FR/SC addressed |
|---------|-------------|-----------------|
| **D01** | Formalise `ABSummary`, `AuditRecord`, `SummaryReport` JSON/YAML schemas (see `contracts/`). | FR‑002, FR‑024, SC‑001, SC‑024 |
| **D02** | Write Quickstart guide (FR‑028) and embed a runtime check that 30 URLs finish ≤ 30 min on the runner. | FR‑028, SC‑028 |
| **D03** | Add contract tests that validate `audit_report.json` and `summary_report.csv` against the schemas. | FR‑024, SC‑024 |

### Phase 2 – Core Implementation
| Task ID | Description | FR/SC addressed |
|---------|-------------|-----------------|
| **I01** | **T017** – `loader.py` reads `data/input/urls.csv`, validates each URL (HTTP 200, HTML content), de‑duplicates, writes `data/curated_urls.csv`. Logs `ERR‑001`…`ERR‑010` for dead or non‑HTML URLs (FR‑007). | FR‑001, FR‑007, SC‑005 |
| **I02** | `parser.py` downloads each curated URL, extracts required fields (sample sizes, conversions/rates, reported p‑value, effect size, outcome type) into `ABSummary` objects (FR‑002). Missing fields trigger `ERR‑011` with ≤ 200‑char note. | FR‑002, FR‑007, SC‑001 |
| **I03** | `reconstruct.py` implements: <br>• Two‑proportion z‑test (or Fisher’s exact when any cell ≤ 5) for binary outcomes. <br>• Welch’s two‑sample t‑test for continuous outcomes. <br>• **Baseline Handling (FR-012)**: If baseline conversion rate is missing, use the average of the two variant rates to estimate the baseline. | FR‑003, FR-012 |
| **I04** | `inconsistency.py` applies: <br>• **Primary rule**: `|reported_p – reconstructed_p| > 0.05` → flag inconsistent (Constitution VI, FR‑004). <br>• **Effect‑size rule**: relative absolute difference > 5 % of larger magnitude → flag (FR‑004). <br>• **Sample‑size mismatch** > 5 % → add `data_quality_warning` to notes (FR‑004b). <br>• **Baseline Heuristic (FR-012)**: If reconstructed using the average of variant rates, add `baseline_heuristic` flag to notes. | FR‑004, FR‑004b, FR-012 |
| **I05** | `prevalence.py` runs a two‑sided binomial test against baseline 0.05 (FR‑005a), computes Wilson 95 % CI, and performs a sweep of baseline proportions 0.02–0.10 (step 0.01) (FR‑005b). The maximum change in prevalence across the sweep must be ≤ 0.02 (SC‑015). | FR‑005a, FR‑005b, SC‑014, SC‑015 |
| **I06** | `export.py` writes: <br>• `output/audit_report.json` (array of `AuditRecord`). <br>• `output/summary_report.csv` (columns per `SummaryReport`). <br>• `output/manifest.json` with timestamps, resource usage, and file list (SC‑013). | FR‑024, SC‑024, SC‑013 |
| **I07** | `logger.py` emits clear `ERR‑###` messages ≤ 200 chars for any parsing or extraction failure (FR‑007). | FR‑007 |

### Phase 3 – Validation & Testing
| Task ID | Description | FR/SC addressed |
|---------|-------------|-----------------|
| **V01** | **T004** – `monte_carlo.py` generates synthetic datasets for each statistical test, runs 10 000 replicates, compares library output to Monte Carlo estimate, asserts absolute difference ≤ 0.005. Results saved to `data/validation/monte_carlo_report.json`. | FR‑026, SC‑003, SC‑026 |
| **V02** | Execute extraction on the manually annotated validation set (Task T081) and compute precision, recall, F1. Store results in `data/validation/extraction_report.json`. Must meet precision ≥ 85 %, recall ≥ 75 % (F1 ≥ 0.80). | FR‑031b, SC‑031b |
| **V03** | Run the full pipeline on a corpus of ≥ 300 curated URLs (or abort with clear message if N < 300). Verify: <br>• Parsing‑error rate ≤ 5 % (SC‑005). <br>• Extraction accuracy ≥ 95 % (SC‑001). <br>• All success criteria (SC‑014, SC‑015, SC‑024, SC‑025, SC‑028) are satisfied. | FR‑001, FR‑002, FR‑025, SC‑001‑SC‑028 |

### Phase 4 – CI & Documentation
| Task ID | Description | FR/SC addressed |
|---------|-------------|-----------------|
| **C01** | GitHub Actions workflow (`.github/workflows/audit.yml`) installs dependencies, runs `run_audit.py` on `data/input/urls.csv`, captures `cpu_time_seconds`, `memory_peak_mb`, `runtime_seconds`, and fails if limits exceed (SC‑008). | FR‑009, SC‑008 |
| **C02** | **T076** – compute SHA‑256 checksums for every input file (`data/checksums.txt`). | FR‑009, SC‑008 |
| **C03** | **T077** – compute SHA‑256 checksums for every output file (`output/checksums.txt`). | FR‑009, SC‑008 |
| **C04** | **T083** – Quickstart verification: run the pipeline on the 30‑URL sample, assert `runtime_seconds ≤ 1800` and memory ≤ 2 GB; abort with clear error if not met. | FR‑028, SC‑028 |
| **C05** | Populate `output/manifest.json` with run ID, timestamps, status, file list, checksums, and resource usage (SC‑013). | SC‑013 |

## Compute Feasibility
- **Memory**: < 200 MB throughout.  
- **CPU**: < 2 CPU‑hours total (well under the 6‑hour wall‑clock limit).  
- **Disk**: < 15 MB total output + input.  
- **GPU**: No GPU required; all libraries are CPU‑only and run on the default GitHub Actions runner.