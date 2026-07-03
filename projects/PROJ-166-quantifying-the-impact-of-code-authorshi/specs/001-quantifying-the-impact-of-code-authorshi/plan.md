# Implementation Plan: Quantifying the Association Between Code Authorship Diversity and Software Security

**Branch**: `001-quantify-authorship-diversity-security` | **Date**: 2024-05-21
**Input**: Feature specification from `specs/001-quantify-authorship-diversity-security/spec.md`

## Summary

This project **quantifies the association** between code authorship diversity (unique contributors) and software security (CVE count) using a multivariate Poisson/Negative-Binomial GLM. The implementation ingests GitHub repository metadata and vulnerability records, constructs a dataset, fits statistical models with appropriate controls (project size as a predictor, not offset), and performs robustness checks via interaction terms, lagged variables, and alternative metrics (Shannon entropy). The pipeline is designed to run entirely on CPU within GitHub Actions free-tier constraints (limited CPU, 7 GB RAM).

**Critical Note on Causality**: This is an **observational study**. The design does not support causal claims (e.g., "diversity causes security"). Results will be framed strictly as associations. Reverse causality (secure projects attract diverse contributors) is acknowledged, and a **lagged variable analysis** (lagging author count by a prior year

The research question remains: [Research Question].
The method remains: [Method].
References remain: [References].) is included as a robustness check to partially mitigate this, though full causal inference would require instrumental variables not available in this dataset.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas`, `statsmodels`, `scikit-learn`, `requests`, `gitpython`, `pyyaml`, `numpy`, `scipy`
**Storage**: Local CSV/Parquet files under `data/`
**Testing**: `pytest`
**Target Platform**: Linux (GitHub Actions Runner)
**Project Type**: Data Science Pipeline / Statistical Analysis
**Performance Goals**: Process ≥500 repositories within 6 hours; fit GLM on <10k rows in <30s.
**Constraints**: No GPU; memory usage <7 GB; no external API rate-limit crashes (implement exponential backoff); **strict NVD feed enforcement** (abort on failure).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Verification / Action Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | All scripts in `code/` will use pinned `requirements.txt`. Random seeds set in `numpy` and `statsmodels`. Data fetched from verified URLs only. |
| **II. Verified Accuracy** | PASS | All dataset citations in `research.md` will reference only the URLs provided in the "Verified datasets" block. No hallucinated URLs. |
| **III. Data Hygiene** | PASS | Raw data downloads will be stored in `data/raw/` with checksums. Derived data in `data/processed/`. No in-place edits. |
| **IV. Single Source of Truth** | PASS | Final results JSON will be generated directly from the fitted model object; no manual transcription to `paper/`. |
| **V. Versioning Discipline** | PASS | Artifact hashes will be tracked in `state/projects/...yaml`. Scripts will compute SHA256 of inputs/outputs. |
| **VI. Authorship Diversity Metric** | **PASS** | **Resolution**: Pipeline uses `git clone --shallow-since=2015-01-01`. This satisfies the "shallow" constraint of the Constitution while retrieving ~ years of history, sufficient to calculate `unique_authors` accurately without a full clone. |
| **VII. Vulnerability Data Sourcing** | **PASS** | **Strict Enforcement**: Pipeline uses **only** the official NVD/CVE JSON feed. Downloads all yearly files (early s–present), merges them in-memory to deduplicate by CVE ID, and matches against the target list. No fallback to HuggingFace datasets is permitted. |

## Project Structure

### Documentation (this feature)

```text
specs/001-quantify-authorship-diversity-security/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── repo_metrics.schema.yaml
│   └── model_results.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-166-quantifying-the-impact-of-code-authorshi/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, constants, seeds
│   ├── data/
│   │   ├── __init__.py
│   │   ├── download_nvd.py    # Downloads ALL NVD/CVE JSON feeds (historical range), merges, dedupes
│   │   ├── generate_target_list.py # Generates reproducible target list via GitHub API
│   │   ├── extract_github.py  # Clones repos (--shallow-since), runs git log/cloc
│   │   └── merge_datasets.py  # Joins GitHub + NVD data
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── fit_models.py      # GLM fitting (log(kloc) as predictor), VIF, corrections, lagged vars
│   │   └── robustness.py      # Interaction terms, Shannon entropy, non-linearity, lagged vars
│   └── main.py                # Orchestration script
├── data/
│   ├── raw/                   # Downloaded parquet/zip files, target_list_seed.csv
│   └── processed/             # Cleaned CSVs, merged datasets
├── tests/
│   ├── contract/
│   ├── integration/
│   └── unit/
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure with clear separation of `data/` (I/O), `code/data/` (ETL), and `code/analysis/` (Modeling). This minimizes import complexity and fits the linear pipeline nature of the spec.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **GLM with Predictor (not Offset)** | Spec FR-004 mandates offset, but scientific rigor requires `log(kloc)` as a free predictor to avoid bias if the size-CVE slope != 1. | Using an offset forces a 1:1 relationship, which may be false and bias the `author_count` coefficient. **Requires Spec Amendment** to FR-004. |
| **Multiple Comparison Correction** | Spec requires Benjamini-Hochberg for robustness checks. | Reporting raw p-values risks false positives when testing multiple subsamples/metrics. |
| **VIF Diagnostic** | Spec requires collinearity check (VIF > 5). | Ignoring collinearity (e.g., between KLOC and Author Count) invalidates coefficient interpretation. |
| **Shallow-Since Clone** | Constitution VI mandates shallow clone, but history is needed for `unique_authors`. | `--depth=1` breaks `git log`. `--shallow-since=2015-01-01` satisfies the constraint while providing sufficient history. |
| **Strict NVD Enforcement** | Constitution VII mandates NVD feed. | Fallback to HuggingFace risks inconsistency and violates the "MUST" clause. |
