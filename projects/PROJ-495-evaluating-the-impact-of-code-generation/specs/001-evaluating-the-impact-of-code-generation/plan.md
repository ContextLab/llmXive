# Implementation Plan: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Branch**: `001-evaluating-the-impact-of-code-generation` | **Date**: 2026-10-16 | **Spec**: `specs/001-evaluating-the-impact-of-code-generation/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary
The project aims to compare vulnerability density between LLM‑generated code and human‑written code. The pipeline will:

1. **Ingest** the required open‑source code corpora (CodeVulnBench for LLM‑generated code and Juliet Test Suite for human‑written code).  
2. **Run** Bandit, Semgrep, and SonarQube (CPU‑only) on every file, deduplicate overlapping findings, and record CWE IDs.  
3. **Compute** lines‑of‑code (LOC) and vulnerability density per file, handling edge cases (zero LOC, oversized files) per the spec.  
4. **Adjust** raw counts using tool‑specific false‑positive rates derived from a **separate** stratified manual audit (FR‑007/FR‑008) and apply corrections before statistical testing.  
5. **Fit** a Negative Binomial regression (primary test) and a Mann‑Whitney U test (secondary robustness check), applying **Benjamini‑Hochberg** false‑discovery‑rate correction across the two tests (FR‑006).  
6. **Generate** required visualizations (boxplot of density, bar chart of CWE distribution).  
7. **Report** all results in reproducible CSV/PNG artifacts.

## Critical Data‑Availability Note
The specification mandates downloading **CodeVulnBench** and the **Juliet Test Suite**. No verified URLs for these datasets are currently available in the “Verified datasets” block. Consequently, the pipeline **must abort early with a clear error** indicating the missing resources. No proxy dataset will be used; a spec amendment providing verifiable open‑source URLs is required before the primary analysis can be performed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `bandit==1.7.9`, `semgrep==1.78.0`, `sonarqube-scanner==4.7.0.2747` (Docker), `statsmodels==0.14.1`, `scipy==1.13.1`, `pandas==2.2.2`, `matplotlib==3.9.0`, `radon==6.0.1`, `psutil==5.9.8`, `pyyaml==6.0.1` (pinned in `code/requirements.txt`)  
- **Storage**: `data/raw/`, `data/derived/`, `results/`  
- **Testing**: `pytest` + contract validation against the schemas in `specs/001-evaluating-the-impact-of-code-generation/contracts/`  
- **Target Platform**: GitHub Actions free‑tier runner (CPU‑only). SonarQube runs via Docker, which is supported on the runner.  
- **Performance Goals**: End‑to‑end ≤ 6 h, peak RAM ≤ 7 GB (SC‑003, SC‑004).  

## Constitution Check
| Principle | Status | How satisfied / note |
|-----------|--------|----------------------|
| I. Reproducibility | PASS | Random seeds are pinned; all scripts are deterministic; datasets are fetched from canonical URLs with cryptographic hash verification (when URLs are provided). |
| II. Verified Accuracy | **FAIL** (data gap) | Required CodeVulnBench and Juliet URLs lack verified sources. The pipeline aborts until a spec amendment supplies verified URLs. |
| III. Data Hygiene | PASS | Checksums recorded in `data/checksums.json`; every transformation produces a new file with provenance. |
| IV. Single Source of Truth | PASS | All figures/tables are generated from the CSV artifacts produced by the pipeline. |
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
│   ├── ingest.py               # FR‑001 (data download & checksum)
│   ├── static_analysis.py      # FR‑002 (Bandit, Semgrep, SonarQube)
│   ├── deduplication.py        # collapse duplicate CWE findings
│   ├── complexity.py           # compute cyclomatic complexity proxy
│   ├── density.py              # FR‑003, FR‑007/FR‑008 adjustments
│   ├── stats.py                # FR‑004, FR‑006, power & over‑dispersion checks
│   ├── audit.py                # FR‑007, FR‑008 (sampling & metrics)
│   ├── figures.py              # FR‑005 (visualizations)
│   └── pipeline.py             # orchestrator CLI
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
| **Phase 1 – Data Ingestion** | `ingest.py` | FR‑001 (download & checksum) | SC‑005 (≥ 95 % files processed) |
| **Phase 2 – Static Analysis** | `static_analysis.py` | FR‑002 (Bandit, Semgrep, SonarQube) | SC‑003 (runtime ≤ 6 h), SC‑004 (RAM ≤ 7 GB) |
| **Phase 3 – Deduplication** | `deduplication.py` | Ensures unique CWE counts (construct validity) | – |
| **Phase 4 – Complexity Proxy** | `complexity.py` | Provides `complexity_proxy` covariate for FR‑004 | – |
| **Phase 5 – Density & Audit‑Adjusted Counts** | `density.py` | FR‑003, FR‑007, FR‑008 (audit‑based correction) | SC‑006 (precision/recall ≥ 80 %) |
| **Phase 6 – Statistical Comparison** | `stats.py` | FR‑004, FR‑006 (NB GLM, Mann‑Whitney U, **Benjamini‑Hochberg** correction) | SC‑001, SC‑002 |
| **Phase 7 – Audit Workflow** | `audit.py` | FR‑007, FR‑008 (sampling & metric computation) | SC‑006, SC‑007 (report FPR disparity) |
| **Phase 8 – Figures & Reporting** | `figures.py` | FR‑005 (boxplot, bar chart) | – |
| **Phase 9 – Orchestration** | `pipeline.py` | Integrates **FR‑001 – FR‑008** and **SC‑001 – SC‑007**; ensures correct task ordering and resource logging. | – |
| **Phase 10 – Instrumentation** | `psutil` calls inside Phase 2 | – | SC‑003, SC‑004 (resource logging) |

### Detailed Tasks
1. **Ingest (`ingest.py`)**  
   - Attempt download of **CodeVulnBench** and **Juliet**; verify SHA‑256 checksums.  
   - If either URL is missing or checksum verification fails, abort with a clear error message indicating the missing verified source.  
   - Record checksums in `data/checksums.json`.  
   - Produce `data/derived/file_manifest.csv` (validated by `file-manifest.schema.yaml`).  

2. **Static Analysis (`static_analysis.py`)**  
   - Iterate over `file_manifest.csv`.  
   - Run **Bandit** for Python files, **Semgrep** for Java/JavaScript, and **SonarQube** (Docker) for all supported languages.  
   - Parse each tool’s JSON output, extract CWE IDs, severity, and line numbers.  
   - Log parse errors; continue processing (edge‑case requirement).  
   - Write raw findings to `data/derived/findings_raw.csv`.  

3. **Deduplication (`deduplication.py`)**  
   - Collapse records that share `file_id`, `line_number`, and `cwe_id` across tools.  
   - Output `data/derived/findings.csv` and update per‑file counts.  

4. **Complexity Proxy (`complexity.py`)**  
   - Use `radon` to compute average cyclomatic complexity per file.  
   - Store in `complexity_proxy` column of `file_manifest.csv`.  

5. **Density & Audit‑Adjusted Counts (`density.py`)**  
   - Compute LOC (language‑agnostic comment/blank removal).  
   - Raw density = `vulnerability_count / loc`; mark `"undefined"` for `loc == 0`.  
   - Apply **tool‑specific false‑positive rates** (derived from audit) to obtain `corrected_vulnerability_count`.  
   - Produce `per_file_analysis.csv` (validated by `per-file-analysis.schema.yaml`).  

6. **Statistical Comparison (`stats.py`)**  
   - **Power analysis** based on observed `n` per group; log if power < 0.8.  
   - **Over‑dispersion check**; if variance/mean ≤ 1.5, fall back to Poisson GLM and note the change.  
   - **Primary NB GLM**: outcome = `corrected_vulnerability_count`, offset = `log(loc)`, predictors = `source_group` + `language`; cluster‑robust SE on `repo_id`.  
   - **Secondary NB GLM**: adds `complexity_proxy` + `repo_id`.  
   - **Mann‑Whitney U** on `density_corrected`.  
   - Apply **Benjamini‑Hochberg** correction across the two tests; output `statistical_tests.csv`.  

7. **Audit (`audit.py`)**  
   - Determine total findings; sample `min(0.10 * total_findings, 200)` stratified by `tool × CWE × source_group` (at least 100 samples if total findings are small).  
   - Write `audit_sample.csv`.  
   - After manual labeling (`audit_verdicts.csv`), compute precision, recall, and **false‑positive rate per tool**; write `audit_metrics.csv`.  
   - **Important**: Files/findings in the audit sample are **excluded** from the regression dataset to avoid circular use of the same data.  

8. **Figures (`figures.py`)**  
   - Boxplot of `density_corrected` by `source_group`.  
   - Bar chart of CWE class counts per group (using corrected counts).  
   - Save PNG & SVG under `results/figures/`.  

9. **Pipeline (`pipeline.py`)**  
   - CLI orchestrates phases in the order above, enforces dependencies, and provides a `--smoke N` flag for quick validation (US‑1).  

10. **Instrumentation**  
    - Use `psutil` to capture wall‑clock time and peak RSS for each phase; write `resource_usage.csv` for SC‑003/SC‑004 verification.

## Risk & Mitigation
- **Missing verified code corpora** (FR‑001): The pipeline aborts early with an informative error; a spec amendment to provide verified open datasets is required before any statistical comparison can be performed.
- **SonarQube Docker image size**: Pulls ~600 MB; fits within the 14 GB disk limit. If disk pressure occurs, the image can be cached across runs.
- **Memory spikes during static analysis**: Files > 100 k LOC are pre‑filtered (`skipped_size`) as required; processing is streamed line‑by‑line where possible.
- **Power insufficiency**: If estimated power < 0.8, the limitation is recorded in `results/limitations.md` and the study is framed as exploratory (SC‑001).
- **Audit sample contamination**: The audit sample is explicitly excluded from the regression dataset to avoid circular dependence (addresses scientific soundness concern).

---

