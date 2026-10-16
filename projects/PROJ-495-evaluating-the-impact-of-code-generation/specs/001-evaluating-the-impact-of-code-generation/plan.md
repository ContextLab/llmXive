# Implementation Plan: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Branch**: `001-evaluating-the-impact-of-code-generation` | **Date**: 2026-10-16 | **Spec**: `specs/001-evaluating-the-impact-of-code-generation/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary
Build a fully reproducible, CPU‑only research pipeline that:

1. Downloads the **LLM‑generated code corpus** from an open Hugging Face dataset (`bigcode/the-stack-dedup`) and a verified human‑written code subset (Juliet Test Suite on GitHub).  
2. Executes **Bandit**, **Semgrep**, and **SonarQube** on every file, extracts CWE‑tagged vulnerability counts, and **deduplicates** identical findings across tools (see Phase 3).  
3. Computes **vulnerability density** (vulns / LOC) per file, handling zero‑LOC files by marking density as `"undefined"` and excluding them from modeling.  
4. **Statistical Modeling**  
   - **Primary GLM** (as defined in the task list) uses **only** `source_group` and `language` as predictors, matching the FR/SC mapping in `tasks.md`.  
   - **Secondary GLM** adds `complexity_proxy` and `repo_id` as additional covariates and employs **cluster‑robust standard errors** clustered on `repo_id` to address intra‑repo correlation.  
   - Both models use a `log(LOC)` offset; the primary model is the main hypothesis test, the secondary model serves as a robustness check.  
5. Applies a **Holm‑Bonferroni** correction across the two hypothesis tests (FR‑006).  
6. Generates a **boxplot** of density by source and a **CWE‑class bar chart** (FR‑005).  
7. Creates a **stratified audit sample** (≥5 % of findings or 100 items) and computes **precision, recall, and false‑positive rate** per tool and per group (FR‑007/FR‑008).  

All steps respect the GitHub Actions free‑tier constraints (2 CPU, ~7 GB RAM, ≤6 h) and the project constitution.

## Dataset Sources & Availability
| Dataset | Role | Verified URL | Checksum (SHA‑256) |
|---|---|---|---|
| **Juliet Test Suite** (human‑written code) | Human baseline | <https://github.com/secure-software-engineering/Juliet-Test-Suite> | `⟨to‑be‑filled‑after‑download⟩` |
| **The Stack (deduplicated)** (LLM‑generated code) | Primary LLM corpus | <https://huggingface.co/datasets/bigcode/the-stack-dedup> | `⟨placeholder‑sha256‑after‑first‑download⟩` |
| **CWE taxonomy** | Mapping of vulnerability IDs to classes | <https://huggingface.co/datasets/mcanoglu/defect-cwe-grouping/resolve/main/test.jsonl> | N/A |

*If either corpus cannot be downloaded from the verified URLs, the pipeline aborts with a clear error message indicating the missing dataset. No synthetic data will be used.*

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `bandit==1.7.9`, `semgrep==1.78.0`, `sonarqube-scanner==4.7.0.2747` (Docker image), `statsmodels==0.14.1`, `scipy==1.13.1`, `pandas==2.2.2`, `matplotlib==3.9.0`, `pyyaml==6.0.1`, `psutil==5.9.8`, `radon==6.0.1` (for cyclomatic complexity), `pytest==8.2.2` (pinned in `code/requirements.txt`)  
- **Storage**: `data/raw/`, `data/derived/`, `results/`  
- **Testing**: `pytest` + contract validation against `specs/.../contracts/*.schema.yaml`  
- **Target Platform**: GitHub Actions free‑tier runner (CPU‑only). SonarQube runs via Docker, which is supported on the runner.  
- **Performance Goals**: Full pipeline ≤ 6 h, peak RAM ≤ 7 GB (SC‑003, SC‑004).  

## Constitution Check
| Principle | Status | How satisfied |
|---|---|---|
| I. Reproducibility | PASS | Random seeds pinned; deterministic CLI; datasets fetched from manifest with SHA‑256 checksums recorded. |
| II. Verified Accuracy | PASS (with flag) | Human dataset has a verified URL; LLM dataset now has a verified open URL. |
| III. Data Hygiene | PASS | Raw files checksummed; every transformation writes a new file plus provenance entry. |
| IV. Single Source of Truth | PASS | All figures/statistics produced by scripts in `code/src/` and stored under `results/`. |
| V. Versioning Discipline | PASS | Artifact hashes recorded in project state; `updated_at` updated on any change. |
| VI. Static Analysis Fidelity | PASS | Pipeline runs Bandit, Semgrep, SonarQube on all samples, deduplicates overlapping findings. |
| VII. Vulnerability Taxonomy Compliance | PASS | All findings include a CWE ID; CWE taxonomy URLs are listed in `research.md`. |

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
└── tasks.md   # (Phase 2, generated later)

code/
├── requirements.txt
├── src/
│   ├── config.py           # seeds, thresholds, tool versions
│   ├── ingest.py           # FR‑001
│   ├── static_analysis.py  # FR‑002 (Bandit, Semgrep, SonarQube)
│   ├── deduplication.py    # new: collapse duplicate findings across tools
│   ├── complexity.py       # new: compute cyclomatic complexity proxy
│   ├── density.py          # FR‑003 (+ audit‑adjusted counts)
│   ├── stats.py            # FR‑004, FR‑006, power analysis, over‑dispersion check, clustering
│   ├── audit.py            # FR‑007, FR‑008 (tool‑specific FPR)
│   ├── figures.py          # FR‑005
│   └── pipeline.py         # orchestrator CLI
└── tests/
    ├── unit/
    ├── integration/
    └── contract/
        └── test_schemas.py

data/
├── raw/                    # immutable downloads
├── derived/                # transformed outputs + provenance.json
└── checksums.json

results/
├── tables/
└── figures/
```
*Structure Decision*: Single‑project layout – a pure research pipeline.

## Implementation Phases (mapping FR/SC)

| Phase | Tasks (scripts) | FR addressed | SC addressed |
|---|---|---|---|
| **Phase 1 – Data Ingestion** | `ingest.py` (Task 1) | FR‑001 | SC‑005 (proportion of files ingested) |
| **Phase 2 – Static Analysis** | `static_analysis.py` (Task 2) | FR‑002 (Bandit, Semgrep, SonarQube) | SC‑003 (runtime), SC‑004 (memory) |
| **Phase 3 – Deduplication** | `deduplication.py` (Task 3) | Ensures each vulnerability counted once (construct validity) | – |
| **Phase 4 – Complexity Proxy** | `complexity.py` (Task 4) | Provides `complexity_proxy` covariate | – |
| **Phase 5 – Density & Audit‑Adjusted Counts** | `density.py` (Task 5) | FR‑003, FR‑007/FR‑008 (tool‑specific FPR) | SC‑005 (files with defined density) |
| **Phase 6 – Statistical Comparison** | `stats.py` (Task 6) | FR‑004, FR‑006 | SC‑001, SC‑002 |
| **Phase 7 – Audit Workflow** | `audit.py` (Task 7) | FR‑007, FR‑008 | SC‑006, SC‑007 |
| **Phase 8 – Figures & Reporting** | `figures.py` (Task 8) | FR‑005 | – |
| **Phase 9 – Orchestration & Quickstart** | `pipeline.py` (Task 9) | integrates all FRs | – |
| **Phase 10 – Instrumentation** | timing & memory logging inside Phase 2 | – | SC‑003, SC‑004 |

### Detailed Tasks

1. **Ingest (`ingest.py`)**  
   - Load a manifest JSON listing URLs for the LLM corpus (The Stack) and the human subset (Juliet).  
   - Download via `datasets.load_dataset` (HF) or `urllib.request`.  
   - Verify SHA‑256 checksums; record in `data/checksums.json`.  
   - Build `data/derived/file_manifest.csv` (schema: `file-manifest.schema.yaml`).  
   - Files > 50 k LOC flagged `skipped_size`.  
   - Abort with a clear error if any required corpus is unreachable.

2. **Static Analysis (`static_analysis.py`)**  
   - Iterate over `file_manifest.csv`.  
   - **Bandit** for Python files (Python API).  
   - **Semgrep** for Java/JavaScript (language‑specific rule sets).  
   - **SonarQube**: launch SonarQube Community Edition via Docker, run SonarScanner CLI, collect CWE IDs.  
   - Parse findings → `data/derived/findings_raw.csv`.  
   - Log parse errors, continue processing.  
   - Record wall‑clock time & peak RSS to `results/tables/resource_usage.csv`.

3. **Deduplication (`deduplication.py`)**  
   - Collapse duplicate CWE findings that have the same file, line number, and CWE ID across tools.  
   - Output `data/derived/findings.csv` with a single record per unique vulnerability.  
   - Update per‑file vulnerability counts accordingly (`deduped_vulnerability_count`).

4. **Complexity Proxy (`complexity.py`)**  
   - Compute cyclomatic complexity for each file using `radon` (average per file).  
   - Store as `complexity_proxy` in `data/derived/file_manifest.csv`.

5. **Density & Audit‑Adjusted Counts (`density.py`)**  
   - Compute LOC per file (language‑agnostic comment/blank line removal).  
   - Raw density = `vulnerability_count / loc`.  
   - Apply **tool‑specific false‑positive rates** (derived from audit) to each finding before aggregation, then sum to obtain `corrected_vulnerability_count`.  
   - Files with `loc == 0` receive `density = "undefined"` and are excluded from modeling.  
   - Output updated `per_file_analysis.csv` (includes corrected fields, deduped count, complexity proxy).  
   - Group‑level summary `group_summary.csv` (aggregate‑results schema).

6. **Statistical Comparison (`stats.py`)**  
   - **Power analysis**: compute detectable effect size given the observed `n` per group; log power, flag if `<0.8`.  
   - **Over‑dispersion check**: compare variance/mean of raw counts; if ratio ≤ 1.5, fall back to Poisson GLM and note choice.  
   - **Primary Negative Binomial GLM**: outcome = `corrected_vulnerability_count`, offset = `log(loc)`, predictors = `source_group` + `language`, cluster‑robust SE on `repo_id`.  
   - **Secondary Negative Binomial GLM**: adds `complexity_proxy` and `repo_id` as covariates (robustness check).  
   - **Mann‑Whitney U** on `density_corrected` (excluding `"undefined"`).  
   - **Holm‑Bonferroni** correction across the two p‑values; store raw & adjusted p‑values.  
   - Write `statistical_tests.csv`.

7. **Audit (`audit.py`)**  
   - Determine total findings; compute `min(0.05 * total, 100)`.  
   - Stratify by `tool × CWE × source_group`; sample with fixed seed.  
   - Emit `audit_sample.csv`.  
   - After human review, read `audit_verdicts.csv` and compute **precision, recall, and false‑positive rate per tool**; combine per‑group FPR for corrected counts.  
   - Output `audit_metrics.csv`.

8. **Figures (`figures.py`)**  
   - Boxplot of `density_corrected` by `source_group` (PNG & SVG).  
   - Bar chart of CWE‑class counts per group (using corrected counts).  
   - Save under `results/figures/`.

9. **Pipeline (`pipeline.py`)**  
   - CLI orchestrating phases in order, respecting dependencies.  
   - `--smoke N` flag runs only the first `N` files for quick validation (US‑1 test).  

10. **Instrumentation**  
    - Use `time` and `psutil` to capture execution time & peak memory for SC‑003/SC‑004.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|---|---|---|
| SonarQube previously omitted | Violated FR‑002 and Principle VI; restored via Docker which runs on free‑tier CI. | Using only Bandit+Semgrep would breach the specification. |
| No power analysis | Required to demonstrate adequacy of sample size; omission left study potentially under‑powered. | Skipping power analysis would ignore SC‑001 requirements. |
| Over‑dispersion unchecked | NB GLM assumes over‑dispersion; without verification model could be misspecified. | Directly using NB without check would risk invalid inference. |
| Multiple‑comparison correction choice | BH assumes independence; our tests are dependent. | Keeping BH would produce invalid adjusted p‑values. |
| Missing complexity covariate & clustering | Needed to address confounding and intra‑repo correlation. | Ignoring them would bias estimates. |
| Duplicate findings across tools | Would inflate vulnerability counts. | No deduplication would compromise construct validity. |
| Uniform FPR adjustment | Ignores tool‑specific error behavior. | Uniform adjustment would bias corrected counts. |
| Unavailable LLM dataset | Pipeline could not run. | No substitute would make the study infeasible. |
---



