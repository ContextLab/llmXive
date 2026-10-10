# Implementation Plan: Evaluating the Impact of Code Generation on Code Vulnerability Density

**Branch**: `001-evaluating-the-impact-of-code-generation` | **Date**: 2026-10-10 | **Spec**: `specs/001-evaluating-the-impact-of-code-generation/spec.md`  
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary
Build a fully reproducible, CPU‑only research pipeline that:

1. Downloads the **CodeVulnBench** LLM‑generated corpus and a human‑written code subset (e.g., Juliet Test Suite).  
2. Runs **Bandit**, **Semgrep**, and **SonarQube** on every file, extracting CWE‑tagged vulnerability counts.  
3. Computes **vulnerability density** (vulns / LOC) per file, handling zero‑LOC files by marking density as `"undefined"` and excluding them from modeling.  
4. Performs a **Negative Binomial GLM** (primary) with covariates (source_group, language, LOC, simple complexity proxy) and a **Mann‑Whitney U** test (secondary).  
5. Applies a **Holm‑Bonferroni** correction across the two tests (appropriate for dependent tests).  
6. Generates a **boxplot** of density by source and a **CWE‑class bar chart** (FR‑005).  
7. Creates a **stratified audit sample** (≥5 % of findings or 100 items) and computes **precision, recall, and false‑positive rate** per group (FR‑007/FR‑008).  

All steps respect the GitHub Actions free‑tier constraints (2 CPU, ~7 GB RAM, ≤6 h) and the project constitution.

## Dataset Sources & Availability
| Dataset | Role | Verified URL | Checksum (SHA‑256) |
|---|---|---|---|
| **Juliet Test Suite** (human‑written code) | Human baseline | | `⟨to‑be‑filled‑after‑download⟩` |
| **CodeVulnBench** (LLM‑generated code) | Primary LLM corpus | **No verified public source found** – the spec must be amended to provide an open, programmatically downloadable substitute (e.g., a Hugging Face dataset) before the pipeline can run. | N/A |

**Dataset Availability Note**: Because no verified public source exists for CodeVulnBench, the pipeline will first check for a verified substitute dataset defined in the manifest. If such a dataset is not present, the pipeline aborts with a clear error message indicating the missing verified source. No synthetic or unverified data will be used.

*If the CodeVulnBench source remains unavailable, the pipeline aborts with a clear error message indicating the missing dataset.*  

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `bandit==1.7.9`, `semgrep==1.78.0`, `sonarqube-scanner==4.7.0.2747` (Docker image), `statsmodels==0.14.1`, `scipy==1.13.1`, `pandas==2.2.2`, `matplotlib==3.9.0`, `pyyaml==6.0.1`, `psutil==5.9.8`, `pytest==8.2.2` (pinned in `code/requirements.txt`)  
- **Storage**: `data/raw/`, `data/derived/`, `results/`  
- **Testing**: `pytest` + contract tests against `specs/.../contracts/*.schema.yaml`  
- **Target Platform**: GitHub Actions free‑tier runner (CPU‑only). SonarQube runs via Docker, which is supported on the runner.  
- **Performance Goals**: Full pipeline ≤ 6 h, peak RAM ≤ 7 GB (SC‑003, SC‑004).  

## Constitution Check
| Principle | Status | How satisfied |
|---|---|---|
| I. Reproducibility | PASS | Random seeds pinned (`code/src/config.py`); deterministic CLI entry point; datasets fetched from manifest with SHA‑256 checksums recorded in `data/checksums.json`. |
| II. Verified Accuracy | PASS (with flag) | Human dataset has a verified URL; LLM dataset currently lacks a verified source and is flagged for spec amendment. |
| III. Data Hygiene | PASS | Raw files checksummed; every transformation writes a new file plus provenance entry (`data/derived/provenance.json`). |
| IV. Single Source of Truth | PASS | Every figure/statistic produced by scripts in `code/src/` and stored under `results/`; paper stage reads only these files. |
| V. Versioning Discipline | PASS | Artifact hashes recorded in `state/projects/PROJ-495-...yaml`; `updated_at` updated on any change. |
| VI. Static Analysis Fidelity | PASS | Pipeline now runs **Bandit**, **Semgrep**, **SonarQube** on all code samples, satisfying the fidelity requirement. |
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
│   ├── density.py          # FR‑003 (+ audit‑adjusted counts)
│   ├── stats.py            # FR‑004, FR‑006, power analysis, over‑dispersion check
│   ├── audit.py            # FR‑007, FR‑008
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
| **Phase 3 – Density & Audit‑Adjusted Counts** | `density.py` (Task 3) | FR‑003, FR‑007/FR‑008 (adjusted counts) | SC‑005 (files with defined density) |
| **Phase 4 – Statistical Comparison** | `stats.py` (Task 4) | FR‑004, FR‑006 | SC‑001, SC‑002 |
| **Phase 5 – Audit Workflow** | `audit.py` (Task 5) | FR‑007, FR‑008 | SC‑006, SC‑007 |
| **Phase 6 – Figures & Reporting** | `figures.py` (Task 6) | FR‑005 | – |
| **Phase 7 – Orchestration & Quickstart** | `pipeline.py` (Task 7) | integrates all FRs | – |
| **Phase 8 – Instrumentation** | timing & memory logging inside Phase 2 | – | SC‑003, SC‑004 |

### Detailed Tasks

1. **Ingest (`ingest.py`)**  
   - Load a manifest JSON listing URLs for CodeVulnBench and the human subset.  
   - Download via `datasets.load_dataset` (if a HuggingFace ID exists) or `urllib.request`.  
   - Verify SHA‑256 checksums (if provided); record in `data/checksums.json`.  
   - Build `data/derived/file_manifest.csv` (schema: `file-manifest.schema.yaml`).  
   - Files > 50 k LOC flagged `skipped_size`.  
   - Abort with a clear error if **neither** corpus is reachable via a verified URL.

2. **Static Analysis (`static_analysis.py`)**  
   - Iterate over `file_manifest.csv`.  
   - **Bandit** for Python files (Python API).  
   - **Semgrep** for Java/JavaScript (language‑specific rule sets).  
   - **SonarQube**: launch SonarQube Community Edition via Docker (`sonarqube:latest`), run SonarScanner CLI against each file, collect CWE IDs.  
   - Parse findings → `data/derived/findings.csv`.  
   - Produce `per_file_analysis.csv` matching `per-file-analysis.schema.yaml`.  
   - Log parse errors, continue processing (edge case).  
   - Record wall‑clock time & peak RSS to `results/tables/resource_usage.csv`.

3. **Density & Audit‑Adjusted Counts (`density.py`)**  
   - Compute LOC per file (language‑agnostic comment/blank line removal).  
   - Raw density = `vulnerability_count / loc`.  
   - Apply audit‑derived false‑positive rate (from `audit_metrics.csv`) to obtain `corrected_vulnerability_count`; recompute `density_corrected`.  
   - Files with `loc == 0` receive `density = "undefined"` and are excluded from modeling.  
   - Output `per_file_analysis.csv` (updated with `corrected_vulnerability_count` and `density_corrected`).  
   - Group‑level summary `group_summary.csv` (aggregate‑results schema).

4. **Statistical Comparison (`stats.py`)**  
   - **Power analysis**: compute detectable effect size given `n` per group; log power, flag if `<0.8`.  
   - **Over‑dispersion check**: compare variance/mean of raw counts; if ratio ≤ 1.5, fall back to Poisson GLM and note choice.  
   - **Negative Binomial GLM**: outcome = raw (or corrected) vulnerability count, offset = `log(loc)`, predictors = `source_group` + `language` + `complexity_proxy`.  
   - **Mann‑Whitney U** on `density_corrected` (excluding `"undefined"`).  
   - **Holm‑Bonferroni** correction across the two p‑values; store raw & adjusted p‑values.  
   - Write `statistical_tests.csv`.

5. **Audit (`audit.py`)**  
   - Determine total findings; compute `min(0.05 * total, 100)`.  
   - Stratify by `tool × CWE × source_group`; sample with fixed seed.  
   - Emit `audit_sample.csv` (empty verdict column).  
   - After human review, read `audit_verdicts.csv` and compute precision, recall, **False Positive Rate** per group → `audit_metrics.csv`.  
   - If no verdicts, write `"not_available"` and note limitation.

6. **Figures (`figures.py`)**  
   - Boxplot of `density_corrected` by `source_group` (PNG & SVG).  
   - Bar chart of CWE‑class counts per group (using corrected counts).  
   - Save under `results/figures/`.

7. **Pipeline (`pipeline.py`)**  
   - CLI orchestrating phases in order, respecting dependencies.  
   - `--smoke N` flag runs only the first `N` files for quick validation (US‑1 test).  

8. **Instrumentation**  
   - Use `time` and `psutil` to capture execution time & peak memory for SC‑003/SC‑004.

## Complexity Tracking
| Violation | Why Needed | Simpler Alternative Rejected |
|---|---|---|
| SonarQube previously omitted | Violated FR‑002 and Principle VI; restored via Docker which runs on free‑tier CI. | Using only Bandit+Semgrep would breach the specification. |
| No power analysis | Required to demonstrate adequacy of sample size; omission left study potentially under‑powered. | Skipping power analysis would ignore SC‑001 requirements. |
| Over‑dispersion unchecked | NB GLM assumes over‑dispersion; without verification model could be misspecified. | Directly using NB without check would risk invalid inference. |
| Multiple‑comparison correction choice | BH assumes independence; our tests are dependent. | Keeping BH would produce invalid adjusted p‑values. |

---



