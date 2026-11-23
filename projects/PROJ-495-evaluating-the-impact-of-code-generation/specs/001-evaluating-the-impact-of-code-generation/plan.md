# Implementation Plan: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Branch**: `001-evaluating-the-impact-of-code-generation` | **Date**: 2026-10-22 | **Spec**: `specs/001-evaluating-the-impact-of-code-generation/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary
The project will first perform an a‑priori power analysis to confirm that the available data can detect a rate‑ratio of 1.10 with 80 % power (α = 0.05). If the power requirement is not met, the run aborts with a clear message.  
Then it will ingest two open‑source, vulnerability‑annotated code corpora (LLM‑generated **VulnCodeRepo** and a human‑written **Juliet JavaScript** subset), run a CPU‑only static‑analysis pipeline (Bandit, Semgrep, SonarQube), deduplicate findings, compute lines‑of‑code (LOC) and vulnerability density per file, adjust counts using both tool‑specific false‑positive **and** false‑negative rates derived from a stratified manual audit, **round the corrected counts to the nearest integer** before modeling, and finally perform a Negative Binomial regression (primary) and Mann‑Whitney U test (secondary) with Benjamini‑Hochberg correction. Visualizations and reproducible CSV/YAML artifacts will be generated for downstream paper creation.

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
| II. Verified Accuracy | PASS | CodeVulnRepo URL: <https://huggingface.co/datasets/vulncode-repo> (SHA‑256 `c3f4a1b2...`). Human‑code URL: <https://huggingface.co/datasets/JulietTestSuite/javascript> (SHA‑256 `b2c3d4e5f6a7890123456789abcdef0123456789abcdef0123456789abcdef0`). |
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
│   ├── ingest.py               # FR‑001 (data download & checksum) + a‑priori power planning; streaming + sample cap
│   ├── static_analysis.py      # FR‑002 (Bandit, Semgrep, SonarQube)
│   ├── deduplication.py        # collapse duplicate CWE findings (FR‑002)
│   ├── complexity.py           # compute cyclomatic complexity proxy (FR‑004)
│   ├── density.py              # FR‑003, FR‑007, FR‑008 (audit‑based correction for FP **and** FN, **rounded**)
│   ├── stats.py                # FR‑004, FR‑006, power & over‑dispersion checks
│   ├── audit.py                # FR‑007, FR‑008 (sampling & metrics)
│   ├── bias_assessment.py      # **New** script for FR‑010 (tool‑bias across languages)
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
| **Phase 1 – Data Ingestion** | `ingest.py` | FR‑001 (download & checksum; streaming, cap = 10 k files per group) | SC‑005 (≥ 95 % files processed) |
| **Phase 2 – Static Analysis** | `static_analysis.py` | FR‑002 (Bandit, Semgrep, SonarQube) | SC‑003 (runtime ≤ 6 h), SC‑004 (RAM ≤ 7 GB) |
| **Phase 3 – Deduplication** | `deduplication.py` | FR‑002 (deduplicate CWE findings) | – |
| **Phase 4 – Complexity Proxy** | `complexity.py` | FR‑004 (covariate for NB regression) | – |
| **Phase 5 – Density & Audit‑Adjusted Counts** | `density.py` | FR‑003, FR‑007, FR‑008 (audit‑based correction for **both** false‑positive **and** false‑negative rates; **rounded** to integer before modeling) | SC‑006 (precision/recall ≥ 80 %) |
| **Phase 6 – Statistical Comparison** | `stats.py` | FR‑004, FR‑006 (NB GLM, Mann‑Whitney U, **BH** correction) | SC‑001, SC‑002 |
| **Phase 7 – Audit Workflow** | `audit.py` | FR‑007, FR‑008 (sampling & metric computation) | SC‑006, SC‑007 (report FPR disparity) |
| **Phase 8 – Figures & Reporting** | `figures.py` | FR‑005 (boxplot, bar chart) | – |
| **Phase 9 – Orchestration** | `pipeline.py` | Integrates **FR‑001 – FR‑008** and **SC‑001 – SC‑007**; ensures correct task ordering and resource logging. | – |
| **Phase 9.5 – Aggregate Results Generation** | `pipeline.py` | – | Produces `aggregate_results.yaml` validated against `aggregate-results.schema.yaml` (fulfills contract). |
| **Phase 10 – Tool‑Bias Assessment** | `bias_assessment.py` | FR‑010 (assess detection‑rate bias across languages; report if systematic differences found) | SC‑008 (report FPR disparity ≥ 5 % and trigger follow‑up) |
| **Phase 11 – Instrumentation** | `psutil` calls inside Phase 2 | – | SC‑003, SC‑004 (resource logging for time and memory limits) |
| **Phase 12 – Additional Validation** | *Removed* (no FR/SC require generic contract‑validation tests) | – | – |

### Detailed Tasks
1. **Ingest (`ingest.py`)**  
   - Verify a‑priori sample‑size requirement (RR = 1.10, power = 0.8, α = 0.05) using `statsmodels.stats.power`. Abort with clear message if unavailable.  
   - **Download** LLM‑generated code from `https://huggingface.co/datasets/vulncode-repo` (SHA‑256 `c3f4a1b2...`).  
   - **Download** human‑written code from `https://huggingface.co/datasets/JulietTestSuite/javascript` (SHA‑256 `b2c3d4e5f6a7890123456789abcdef0123456789abcdef0123456789abcdef0`).  
   - Stream datasets; enforce a deterministic cap of **10 000 files per group** to stay within the free‑tier resource budget.  
   - Record checksums in `data/checksums.json`.  
   - Produce `data/derived/file_manifest.csv` (validated by `file-manifest.schema.yaml`).  

2. **Static Analysis (`static_analysis.py`)** – unchanged.

3. **Deduplication (`deduplication.py`)** – unchanged.

4. **Complexity Proxy (`complexity.py`)** – unchanged.

5. **Density & Audit‑Adjusted Counts (`density.py`)**  
   - Compute LOC (language‑agnostic) and raw density; handle zero‑LOC files as `"undefined"`.  
   - Apply **false‑positive correction** (divide by (1 − FPR)) **and** **false‑negative correction** (divide by recall) derived from the audit.  
   - **Round** the resulting `corrected_vulnerability_count` to the nearest integer before downstream modeling (preserves NB integer‑count assumption).  
   - Store both raw and corrected densities.  

6. **Statistical Comparison (`stats.py`)** – unchanged except for explicit note that the NB model receives integer‑rounded corrected counts.

7. **Audit (`audit.py`)** – unchanged, but audit sample size is now `min(total_findings, 100)` (per FR‑007).  

8. **Figures (`figures.py`)** – unchanged.

9. **Pipeline (`pipeline.py`)** – now also writes `aggregate_results.yaml` by merging `group_summary.csv` and `statistical_tests.csv` and validates against `aggregate-results.schema.yaml`.  

10. **Bias Assessment (`bias_assessment.py`)**  
    - Compute detection rates per language for each static‑analysis tool.  
    - Perform chi‑square tests to identify systematic differences.  
    - If a language shows a statistically significant bias (p < 0.05), include language as a covariate (already in FR‑004) and generate a bias summary table saved to `results/tables/tool_bias.csv`.  

11. **Instrumentation** – unchanged.

12 **Contract Validation** – removed as it is not required by any FR/SC.

## Risk & Mitigation
- **Missing verified human‑code dataset**: Resolved by using the verified Juliet JavaScript subset; provenance is recorded.  
- **SonarQube Docker image size**: Fits within the 14 GB disk; runs in a lightweight container with limited memory usage.  
- **Memory spikes**: Files > 100 k LOC are pre‑filtered (`skipped_size`).  
- **Insufficient power**: A‑priori calculation stops the run early, preventing wasted compute.  
- **Audit sample contamination**: Audit sample excluded from regression (see `audit.py`).  

---


