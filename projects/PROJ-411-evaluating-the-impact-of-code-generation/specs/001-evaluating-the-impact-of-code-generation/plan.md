# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Burden

**Branch**: `001-code-gen-review-burden` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-code-gen-review-burden/spec.md`

## Summary
The project will (1) download three **verified** PR datasets from HuggingFace, (2) verify that each dataset contains every variable required by the schemas, (3) classify each PR’s provenance using the exact FR‑002 precedence hierarchy (file‑header > diff‑pattern > commit‑message), (4) compute reviewer‑effort metrics (`review_active_seconds`, `comment_density`, `issue_severity`), (5) filter & outlier‑remove according to FR‑003/FR‑006/FR‑014, (6) run a pre‑registered statistical comparison (Mann‑Whitney U primary, Welch t‑test companion) with mixed‑effects adjustment (FR‑013) and Bonferroni correction, (7) perform a manual validation of provenance on a fixed 50‑PR‑per‑group sample (Cohen’s κ, FR‑007), (8) conduct the required sensitivity analyses, and (9) generate a fully reproducible report. All steps are CPU‑tractable on the GitHub Actions free tier; no GPU escape hatch is needed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `datasets==2.19.*`, `pyyaml==6.0.*`, `matplotlib==3.8.*`, `psutil==5.9.*`  
- **Storage**: file‑based CSV/Parquet under `data/`  
- **Testing**: `pytest` (unit tests for classification precedence, metric computation, statistical wrappers)  
- **Target Platform**: Linux runner (GitHub Actions free tier: 2 CPU, ~7 GB RAM, ≤6 h)  
- **Project Type**: research‑oriented CLI scripts  
- **Performance Goals**: complete all phases within the CI time‑budget and memory limit (SC‑005)  
- **Constraints**: only the three **verified** datasets listed in the “Verified datasets” block may be used; no GPU is required.

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed random seeds; deterministic data download via `datasets.load_dataset`; all scripts are pure functions producing files with documented names. |
| II. Verified Accuracy | No new citations; all external data sources are the verified URLs from the block. |
| III. Data Hygiene | Raw files are SHA‑256‑checked (`data/checksums.txt`). No in‑place mutation; each transformation writes a new file. |
| IV. Single Source of Truth | `data/processed/processed_prs.csv` is the SSoT (FR‑020) and is the sole input to downstream analysis. |
| V. Versioning Discipline | Platform‑provided content hashes track every artifact; `state/projects/...updated_at` is updated automatically. |
| VI. Provenance Rigor | Classification follows FR‑002 precedence exactly; unit test `test_precedence_header_wins` guarantees header overrides. |
| VII. Statistical Validation Discipline | Pre‑specified Mann‑Whitney U primary test, Welch t‑test companion, effect‑size reporting, IQR outlier handling, mixed‑effects adjustment, Bonferroni correction, and validation κ are all implemented. |

## Project Structure
```text
specs/001-code-gen-review-burden/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── raw_prs.schema.yaml
    ├── processed_prs.schema.yaml
    └── statistical_results.schema.yaml

code/
├── download_data.py        # Phase 0 – download + checksum + schema‑map
├── classify_provenance.py  # Phase 1 – provenance labeling
├── compute_metrics.py      # Phase 2 – SSoT creation
├── outlier_filter.py       # Phase 3 – filtering & IQR variants
├── statistical_analysis.py # Phase 4 – power, normality, tests, mixed‑effects
├── validation.py           # Phase 5 – manual κ & misclassification response
├── sensitivity.py          # Phase 6 – IQR & comment‑filter sweeps, source‑stratified checks
└── report.py               # Phase 7 – final markdown report & figures

data/
├── raw/
│   ├── prs_v2_sample.parquet                     # primary verified PR dataset
│   ├── agbd_prs.csv                              # auxiliary known‑LLM set A
│   └── agbd_lite_prs.h5                          # auxiliary known‑LLM set B
├── processed/
│   ├── classified_prs.csv
│   ├── processed_prs.csv                         # SSoT
│   ├── filtered_prs_iqr1.0.csv
│   ├── filtered_prs_iqr1.5.csv
│   ├── filtered_prs_iqr2.0.csv
│   └── filtered_prs_relaxed.csv
└── results/
    ├── stats_summary.csv
    ├── sensitivity_report.csv
    ├── validation_report.md
    ├── group_source_contingency.csv
    └── figures/
        ├── review_active_seconds_boxplot.png
        └── comment_density_boxplot.png
```
*Structure Decision*: a single‑project layout under `code/`; all data‑processing scripts are pure Python CLI tools.

## Phase‑by‑Phase Tasks (FR / SC Mapping)

| Phase | Description | FR / SC addressed |
|-------|-------------|-------------------|
| **0 – Data Acquisition & Schema Mapping** | Download the three verified datasets (`prs-v2-sample` parquet, `AGBD` CSV, `AGBD‑Lite` H5) using `datasets.load_dataset(..., streaming=False)`. Verify SHA‑256 checksums, generate `data/raw/schema_map.md` that records per‑dataset presence of every field required by `contracts/raw_prs.schema.yaml`. Abort with a clear error if the primary dataset lacks any required variable. | FR‑001, FR‑016, FR‑020, FR‑022, SC‑005 |
| **1 – Provenance Classification** | Apply FR‑002 precedence rules to each PR **in the primary dataset only**. Write `data/processed/classified_prs.csv` with a `provenance_label` column. Exclude “Mixed” PRs from the binary comparison but retain them for the selection‑bias check (FR‑018). Log a warning and **exclude any repository that contains zero LLM‑generated PRs** (FR‑010). Write a contingency table `data/results/group_source_contingency.csv` (source = primary vs. auxiliary). | FR‑002, FR‑008, FR‑010, FR‑018 |
| **2 – Metric Computation & SSoT** | From `classified_prs.csv`, compute `lines_changed` (additions + deletions), `review_duration_seconds` (merged − created), `review_active_seconds` (first comment → merge, using `first_comment_timestamp`; fallback to `review_duration_seconds` with limitation note), `comment_density`, `issue_severity` (mapped from PR labels). Write **only** `data/processed/processed_prs.csv` (the SSoT, FR‑020). | FR‑003, FR‑012, FR‑015, FR‑016, FR‑020 |
| **3 – Outlier Handling & Filter Variants** | Apply FR‑003 filter (`lines_changed ≥ 5`, `comment_count ≥ 1`) and IQR outlier removal with multipliers 1.0, 1.5, 2.0 → three filtered files (`*_iqr1.0.csv`, `*_iqr1.5.csv`, `*_iqr2.0.csv`). Also create `*_relaxed.csv` where `comment_count ≥ 0`. Each file is written by `outlier_filter.py`. | FR‑003, FR‑006, FR‑014 |
| **4 – Statistical Modeling** | • **Power analysis** (FR‑019) using `statsmodels.stats.power.TTestIndPower`; report required n and compare to actual group sizes. • **Normality**: Shapiro‑Wilk per metric per group. • **Primary test**: Mann‑Whitney U (rank‑biserial effect) on `review_active_seconds` and `comment_density`; Welch t‑test (Cohen’s d) reported as companion. • **Mixed‑effects model** (FR‑013) with `repo_name` random intercept + fixed effects (`lines_changed`, `author_experience`, `repository_popularity`, `creation_quarter`). • **Chi‑square** for `issue_severity`. • **Bonferroni** correction (α = 0.05/k). • **Collinearity**: VIF for `lines_changed` vs. `comment_density`. • Write `data/results/stats_summary.csv` conforming to `contracts/statistical_results.schema.yaml`. | FR‑004, FR‑005, FR‑011, FR‑013, FR‑019, FR‑021, SC‑002, SC‑004, SC‑006, SC‑007 |
| **5 – Validation (Cohen’s κ) & Misclassification Response** | Deterministically sample (seed = 2023) 50 PRs per group; emit `data/processed/validation_sample.csv`. Human labels are committed as `data/processed/manual_labels.csv`. `validation.py` computes Cohen’s κ; if κ < 0.6 (SC‑001) flag the group and downgrade to descriptive reporting. Estimate the false‑negative rate for the Human‑written group; if > 10 % add an attenuation limitation and run a secondary sensitivity that excludes keyword‑negative PRs from repositories with high LLM prevalence. Produce `data/results/validation_report.md`. | FR‑007, SC‑001 |
| **6 – Sensitivity Analyses** | Re‑run the primary tests for each IQR multiplier (1.0, 1.5, 2.0) and for the relaxed comment filter. Record any significance flips → “Low Robustness” flag (SC‑003). Also run a **source‑stratified descriptive comparison** of the auxiliary known‑LLM datasets against the primary groups; never pool them. Write `data/results/sensitivity_report.csv`. | FR‑006, FR‑014, SC‑003 |
| **7 – Reporting** | Assemble tables, box‑plots, contingency tables, and explicit null‑result statements (FR‑011). Include limitation statements for power, selection bias (FR‑018), misclassification attenuation, missing covariates, temporal confounding, dataset‑origin, and observational framing. Write `report.md`. | FR‑011, FR‑017, FR‑018 |
| **8 – Resource Monitoring** | Each script logs peak RAM & CPU via `psutil`; abort with a clear error if > 6 GB RAM or > 6 h total runtime (SC‑005). | SC‑005 |
| **9 – Optional GitHub API Enrichment** | Implement exponential backoff (FR‑009) for any optional metadata fetches; the main pipeline runs without API calls, so the guard is a no‑op in CI. | FR‑009 |

All 22 functional requirements (FR‑001 – FR‑022) and 7 success criteria (SC‑001 – SC‑007) are explicitly covered.

## Complexity Tracking
No constitution violations require justification. The only spec‑level gap is the unverified “Jones et al., 2022” citation (FR‑017); the plan omits that citation and notes the construct‑validity caveat without referencing the source, satisfying Constitution II.

---
