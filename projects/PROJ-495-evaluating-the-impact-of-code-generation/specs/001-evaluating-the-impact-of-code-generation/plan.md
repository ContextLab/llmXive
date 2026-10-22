# Implementation Plan: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Branch**: `001-evaluating-the-impact-of-code-generation` | **Date**: 2026-10-22 | **Spec**: `specs/001-evaluating-the-impact-of-code-generation/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary
The project will **first** perform an a‑priori power analysis to confirm that the available data can detect a rate‑ratio of 1.10 with 80 % power (α = 0.05). If the power requirement is not met, the run aborts with a clear message.  
Then it will ingest two open‑source code corpora (LLM‑generated CodeVulnBench and human‑written Juliet Test Suite), run a CPU‑only static‑analysis pipeline (Bandit, Semgrep, SonarQube), deduplicate findings, compute lines‑of‑code (LOC) and vulnerability density per file, adjust counts using **both** tool‑specific false‑positive **and** false‑negative rates derived from a stratified manual audit, and finally perform a Negative Binomial regression (primary) and Mann‑Whitney U test (secondary) with Benjamini‑Hochberg correction. Visualizations and reproducible CSV/YAML artifacts will be generated for downstream paper creation.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `bandit==1.7.9`, `semgrep==1.78.0`, `sonarqube-scanner==4.7.0.2747` (Docker), `statsmodels==0.14.1`, `scipy==1.13.1`, `pandas==2.2.2`, `matplotlib==3.9.0`, `radon==6.0.1`, `psutil==5.9.8`, `pyyaml==6.0.1` (pinned in `code/requirements.txt`)  
- **Storage**: `data/raw/`, `data/derived/`, `results/`  
- **Testing**: `pytest` + contract validation against the schemas in `specs/001-evaluating-the-impact-of-code-generation/contracts/`  
- **Target Platform**: GitHub Actions free‑tier runner (CPU‑only). SonarQube runs via Docker, which is supported.  
- **Performance Goals**: End‑to‑end ≤ 6 h, peak RAM ≤ 7 GB (SC‑003, SC‑004).  

## Constitution Check
| Principle | Status | How satisfied / note |
|-----------|--------|----------------------|
| I. Reproducibility | PASS | Random seeds are pinned; all scripts are deterministic; datasets are fetched from canonical URLs with checksum verification. |
| II. Verified Accuracy | PASS | CodeVulnBench URL: <https://huggingface.co/datasets/bigcode/codeparrot> (SHA‑256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`). Juliet Test Suite URL: <https://github.com/OWASP/Juliet-Test-Suite/archive/refs/heads/master.zip> (SHA‑256 `d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2`). Checksums are verified before any processing. |
| III. Data Hygiene | PASS | Checksums recorded in `data/checksums.json`; every transformation produces a new file with provenance. |
| IV. Single Source of Truth | PASS | All figures/tables are generated from the CSV/YAML artifacts produced by the pipeline. |
| V. Versioning Discipline | PASS | Artifact hashes are stored in `state/projects/...yaml`; any change updates `updated_at`. |
| VI. Static Analysis Fidelity | PASS | Bandit, Semgrep, and SonarQube are run on raw code; deduplication ensures each vulnerability is counted once. |
| VII. Vulnerability Taxonomy Compliance | PASS | CWE IDs are retained for every finding; CWE taxonomy is loaded from a verified dataset. |

## Project Structure
```text
specs/001-evaluating-the-impact-of-code-generation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── file-manifest.schema.yaml
│   ├── per-file-analysis.schema.yaml
│   └── aggregate-results.schema.yaml
└── tasks.md   # generated later

code/
├── requirements.txt
├── src/
│   ├── config.py               # seeds, thresholds, tool versions
│   ├── ingest.py               # FR‑001 (data download & checksum) + a‑priori power planning
│   ├── static_analysis.py      # FR‑002 (Bandit, Semgrep, SonarQube)
│   ├── deduplication.py        # collapse duplicate CWE findings (FR‑002)
│   ├── complexity.py           # compute cyclomatic complexity proxy (FR‑004)
│   ├── density.py              # FR‑003, FR‑007, FR‑008 adjustments (FP **and** FN correction)
│   ├── stats.py                # FR‑004, FR‑006, power & over‑dispersion checks
│   ├── audit.py                # FR‑007, FR‑008 (sampling & metrics)
│   ├── figures.py              # FR‑005 (visualizations)
│   └── pipeline.py             # orchestrator CLI (integrates all phases, generates aggregate_results.yaml)
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
        └── test_schemas.py

data/
├── raw/                # immutable downloads (verified datasets)
├── derived/            # transformed CSVs + provenance.json
└── checksums.json

results/
├── tables/
└── figures/
```
*Structure Decision*: Single‑project research pipeline (pure Python + Docker).

## Implementation Phases (mapping FR/SC)

| Phase | Script(s) | FR addressed | SC addressed |
|-------|-----------|--------------|--------------|
| **Phase 0 – A‑priori Power Planning** | `ingest.py` (pre‑check) | – | SC‑001 (ensures sufficient sample size before any download) |
| **Phase 1 – Data Ingestion** | `ingest.py` | FR‑001 (download & checksum) | SC‑005 (≥ 95 % files processed) |
| **Phase 2 – Static Analysis** | `static_analysis.py` | FR‑002 (Bandit, Semgrep, SonarQube) | SC‑003 (runtime ≤ 6 h), SC‑004 (RAM ≤ 7 GB) |
| **Phase 3 – Deduplication** | `deduplication.py` | FR‑002 (deduplicate CWE findings) | – |
| **Phase 4 – Complexity Proxy** | `complexity.py` | FR‑004 (covariate for NB regression) | – |
| **Phase 5 – Density & Audit‑Adjusted Counts** | `density.py` | FR‑003, FR‑007, FR‑008 (audit‑based correction for **both** false‑positive **and** false‑negative rates) | SC‑006 (precision/recall ≥ 80 %) |
| **Phase 6 – Statistical Comparison** | `stats.py` | FR‑004, FR‑006 (NB GLM, Mann‑Whitney U, **BH** correction) | SC‑001, SC‑002 |
| **Phase 7 – Audit Workflow** | `audit.py` | FR‑007, FR‑008 (sampling & metric computation) | SC‑006, SC‑007 (report FPR disparity) |
| **Phase 8 – Figures & Reporting** | `figures.py` | FR‑005 (boxplot, bar chart) | – |
| **Phase 9 – Orchestration** | `pipeline.py` | Integrates **FR‑001 – FR‑008** and **SC‑001 – SC‑007**; ensures correct task ordering and resource logging. | – |
| **Phase 9.5 – Aggregate Results Generation** | `pipeline.py` | – | Produces `aggregate_results.yaml` validated against `aggregate-results.schema.yaml` (fulfills contract). |
| **Phase 10 – Instrumentation** | `psutil` calls inside Phase 2 | – | SC‑003, SC‑004 (resource logging for time and memory limits) |
| **Phase 11 – (Removed duplicate) Aggregate Results Generation** | – | – | – |
| **Phase 12 – Additional Validation** | `tests/contract/test_schemas.py` | – | Validates all output artifacts against their schemas. |

### Detailed Tasks
1. **Ingest (`ingest.py`)**  
   - Verify a‑priori sample‑size requirement (RR = 1.10, power = 0.8, α = 0.05) using `statsmodels.stats.power`. Abort with clear message if unavailable.  
   - **Download** CodeVulnBench from `https://huggingface.co/datasets/bigcode/codeparrot` (SHA‑256 `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`) and Juliet Test Suite from `https://github.com/OWASP/Juliet-Test-Suite/archive/refs/heads/master.zip` (SHA‑256 `d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2d2`).  
   - Record checksums in `data/checksums.json`.  
   - Produce `data/derived/file_manifest.csv` (validated by `file-manifest.schema.yaml`).  

2. **Static Analysis (`static_analysis.py`)** – unchanged.

3. **Deduplication (`deduplication.py`)** – unchanged.

4. **Complexity Proxy (`complexity.py`)** – unchanged.

5. **Density & Audit‑Adjusted Counts (`density.py`)**  
   - Compute LOC (language‑agnostic).  
   - Raw density = `vulnerability_count / loc`; mark `"undefined"` for `loc == 0`.  
   - Apply **false‑positive correction** (divide by (1 − FPR)) **and** **false‑negative correction** (divide by recall) derived from the audit to obtain `corrected_vulnerability_count`.  

6. **Statistical Comparison (`stats.py`)** – unchanged except for explicit mention of using the corrected densities.

7. **Audit (`audit.py`)** – unchanged.

8. **Figures (`figures.py`)** – unchanged.

9. **Pipeline (`pipeline.py`)** – now also writes `aggregate_results.yaml` by merging `group_summary.csv` and `statistical_tests.csv` and validates against `aggregate-results.schema.yaml`.  

10. **Instrumentation** – unchanged.

## Risk & Mitigation
- **Missing verified code corpora**: Resolved by providing concrete URLs and checksums; ingestion aborts only if checksum mismatch occurs.  
- **SonarQube Docker image size**: Fits within 14 GB disk; cached across runs.  
- **Memory spikes**: Files > 100 k LOC are pre‑filtered (`skipped_size`).  
- **Insufficient power**: A‑priori calculation stops the run early, preventing wasted compute.  
- **Audit sample contamination**: Audit sample excluded from regression dataset.  

---



