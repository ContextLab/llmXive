# Implementation Plan: Evaluating the Statistical Validity of Public A/B Test Summaries

**Branch**: `001-eval-ab-test-validity` | **Date**: 2026-06-25 | **Spec**: [/specs/001-eval-ab-test-validity/spec.md](../specs/001-eval-ab-test-validity/spec.md)  
**Input**: Feature specification from `/specs/001-eval-ab-test-validity/spec.md`

## Summary
The core deliverable is a reproducible, CI‑compatible audit pipeline that (1) ingests a list of URLs to public A/B test summaries, (2) extracts the required metrics, (3) reconstructs the appropriate statistical test (two‑proportion z/Fisher for binary outcomes, Welch’s t‑test for continuous outcomes), (4) flags inconsistencies according to the tolerances defined in **FR‑004**, (5) performs a binomial prevalence test (**FR‑005a**) with post‑hoc power assessment, (6) conducts a sensitivity analysis on the FR‑004 thresholds, (7) exports both a detailed JSON audit report and a concise CSV summary (**FR‑024**), (8) evaluates potential selection bias, and (9) logs all parsing failures (**FR‑007**) while remaining within the 6‑hour GitHub Actions runner limit (**FR‑009**, **SC‑008**).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `requests`, `beautifulsoup4`, `pandas`, `numpy`, `scipy>=1.12`, `statsmodels>=0.14`, `tqdm`, `pyyaml`  
- **Storage**: Files on the repository (`data/`, `output/`) – no external database.  
- **Testing**: `pytest` + contract‑based validation (`jsonschema` for JSON outputs, custom YAML schemas for CSV).  
- **Target Platform**: Linux runner used by GitHub Actions (CPU‑only).  
- **Performance Goals**: Process up to **[deferred]** URLs within 6 h; peak RAM ≤ 4 GB (benchmark: ~0.7 s per URL on the default runner).
- **Constraints**: CPU‑only, no GPU, no large‑model inference, all libraries must install on the default runner.  

## Constitution Check
| Principle | How the plan satisfies it |
|-----------|--------------------------|
| I. Reproducibility | All code is deterministic (random seeds pinned), external datasets fetched via canonical URLs, Dockerfile provided for environment reproducibility. |
| II. Verified Accuracy | All external citations (e.g., Kohavi et al., 2020) are listed in `docs/references.bib` and will be validated by the Reference‑Validator Agent. |
| III. Data Hygiene | Raw HTML pages are saved under `data/raw/` with SHA‑256 checksums recorded in `data/manifest.yaml`. Transformations write new files under `data/processed/`. |
| IV. Single Source of Truth | **SSoT Designation**: `data/manifest.yaml` is the authoritative source for provenance and checksums; `output/audit_report.json` is the authoritative source for all reported metrics and figures. No manual transcription of numbers. |
| V. Versioning Discipline | All artifacts (scripts, schemas, Docker image) are version‑hashed; the CI workflow records the hash in `state/artifact_hashes.yaml`. |
| VI. Statistical Consistency Verification | The pipeline implements the exact tests and tolerance thresholds described in **FR‑004**; any discrepancy > 0.05 is flagged and logged. |
| VII. Source Provenance & Transparency | The original URL is stored in every extracted record and propagated to the JSON/CSV outputs; provenance is also logged in `data/metadata.yaml`. |

## Project Structure
```text
specs/001-eval-ab-test-validity/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── extracted_summary.schema.yaml
    └── audit_record.schema.yaml

code/
├── run_audit.sh                # orchestration script
├── extract.py                  # HTML parsing & field extraction
├── reconstruct.py              # p‑value / effect size reconstruction
├── audit.py                    # inconsistency detection, sensitivity analysis
├── report.py                   # JSON/CSV generation, power assessment
└── utils.py                    # shared helpers (logging, checksum)

data/
├── raw/                        # downloaded HTML pages (checksum‑verified)
├── processed/                  # extracted tables (CSV)
└── manifest.yaml               # checksums & provenance

output/
├── audit_report.json
└── summary_report.csv

tests/
├── contract/
│   ├── test_extracted_schema.py
│   └── test_audit_schema.py
├── unit/
│   ├── test_extract.py
│   ├── test_reconstruct.py
│   └── test_audit.py
└── integration/
    └── test_full_pipeline.py

Dockerfile
requirements.txt
```

## Complexity Tracking
No constitution‑level violations identified. All required functionality fits within a single repository; no additional micro‑services are needed.

## Phase‑wise Plan & Mapping to FR/SC

| Phase | Description | FR/SC Addressed |
|-------|-------------|-----------------|
| **Phase 0 – Research & Feasibility** | Review verified datasets, prototype HTML extraction on a 100‑item validation set, benchmark statistical reconstruction speed (≈ 0.7 s per URL). | SC‑001, SC‑003, SC‑013 |
| **Phase 1 – Data Model & Schemas** | Define `extracted_summary.schema.yaml` and `audit_record.schema.yaml`; implement checksum‑based data hygiene. | FR‑002, FR‑007, III, IV |
| **Phase 2 – Extraction Module** (`code/extract.py`) | • Download URLs (with retry, exponential back‑off, timeout). <br>• Parse HTML via BeautifulSoup. <br>• Locate tables/text using multiple XPath/regex fall‑backs to handle format diversity. <br>• Normalize effect‑size units (lift % → absolute diff; use average of variants when baseline missing per **FR‑012**). <br>• Emit CSV conforming to `extracted_summary.schema.yaml`. | FR‑001, FR‑002, SC‑001, SC‑005 |
| **Phase 3 – Reconstruction Module** (`code/reconstruct.py`) | • Determine outcome type (binary vs. continuous). <br>• Apply two‑proportion z‑test (or Fisher’s exact when any cell ≤ 5) via `statsmodels.stats.proportion`. <br>• Apply Welch’s t‑test for continuous outcomes via `scipy.stats.ttest_ind(equal_var=False)`. <br>• Compute reconstructed effect size (absolute difference). | FR‑003, SC‑003 |
| **Phase 4 – Inconsistency Detection & Sensitivity** (`code/audit.py`) | • Compare reported vs. reconstructed p‑values and effect sizes using tolerances from **FR‑004**. <br>• Flag missing metrics, size mismatches, inequality p‑values, CI violations. <br>• Log each parsing failure per **FR‑007**. <br>• **Sensitivity Analysis**: after main audit, re‑evaluate flags across a small grid of tolerance parameters (e.g., p‑diff 0.04–0.06, effect‑size rel‑diff 4–[deferred]) and record stability metrics. | FR‑004, FR‑007, SC‑001, SC‑005 |
| **Phase 5 – Prevalence Test, Power Assessment & Reporting** (`code/report.py`) | • Aggregate flags, compute overall inconsistency proportion `k/n`. <br>• Perform two‑sided binomial test against baseline 0.05 using `statsmodels.stats.proportion.binom_test`. <br>• Compute 95 % Wilson CI via `statsmodels.stats.proportion.proportion_confint`. <br>• **Power Assessment**: calculate achieved power for detecting a deviation of 0.05 from the baseline using the observed `n` and `k` (via `statsmodels.stats.proportion.power_binom_test`). Report power; if < 0.8, note limitation. <br>• Write `audit_report.json` (per‑summary) and `summary_report.csv` (aggregate) matching **FR‑024**. | FR‑005a, FR‑024, SC‑014, SC‑024 |
| **Phase 6 – CI Integration** (`.github/workflows/audit.yml`) | • Define workflow that mounts `input/urls.csv`, runs `run_audit.sh`, caches `data/raw/` to avoid re‑download, enforces timeout ≤ 6 h. <br>• Limit parallelism to 2 workers (matches runner vCPUs). <br>• Capture resource usage (`/usr/bin/time -v`). | FR‑009, SC‑008, SC‑013 |
| **Phase 7 – Validation & Testing** | • Run the curated **≥ 100**‑item validation set and assert extraction accuracy ≥ 95 % and detection precision ≥ 90 % (SC‑001, SC‑014). <br>• Contract tests validate JSON/CSV against schemas. | SC‑001, SC‑014, SC‑024 |
| **Phase 8 – Bias Assessment & Documentation** | • Stratify the URL list by source category (e.g., corporate blog, open‑source repo, conference paper) and ensure proportional representation. <br>• Produce a source‑distribution summary table for transparency. <br>• Document all bias‑mitigation steps in the final report. | Addresses selection‑bias concern; supports reproducibility. |
| **Phase 9 – Documentation & Quickstart** | Write `quickstart.md` with example commands, Docker usage, interpretation guide, and SSoT references. | All user‑story deliverables |

Each phase will be implemented as a separate GitHub Actions job when appropriate, guaranteeing that data download precedes extraction, reconstruction precedes auditing, and reporting follows auditing.

---

