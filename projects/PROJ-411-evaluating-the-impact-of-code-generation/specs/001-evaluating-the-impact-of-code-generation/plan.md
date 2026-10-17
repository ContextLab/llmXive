# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Burden

**Branch**: `001-code-gen-review-burden` | **Date**: 2026-10-17 | **Spec**: [spec.md](../specs/001-code-gen-review-burden/spec.md)  
**Input**: Feature specification from `/specs/001-code-gen-review-burden/spec.md`

## Summary
The project will (1) obtain a verified public PR dataset, (2) classify each PR as *LLM‑generated*, *Human‑written*, or *Mixed* using the precedence rules in FR‑002, (3) compute reviewer‑effort metrics (review_active_seconds, comment_density, issue_severity), (4) perform a **observational** statistical comparison between the LLM and Human groups (normality‑driven test selection, Bonferroni‑adjusted α, effect‑size reporting), (5) validate the classification on a manual sample (Cohen’s κ), and (6) run predefined sensitivity analyses (outlier IQR thresholds, comment‑filter relaxation). All steps are CPU‑tractable and run within the GitHub Actions free‑tier limits. **All findings are interpreted as associational differences; no causal claims are made.** Findings are reported as associational differences only, not causal effects.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**:
- `pandas==2.2.*`
- `numpy==1.26.*`
- `requests==2.32.*` (fallback GitHub API calls)
- `tqdm==4.66.*`
- `scipy==1.13.*`
- `statsmodels==0.14.*`
- `scikit-learn==1.5.*`
- `huggingface_hub==0.23.*`
- `pyyaml==6.0.*`
- `matplotlib==3.8.*`

**Storage**: file‑based CSV/Parquet under `data/`  
**Testing**: `pytest` (unit tests for classification, metric computation, statistical wrappers)  
**Target Platform**: Linux (GitHub Actions runner)  
**Project Type**: research‑oriented CLI library + notebooks  
**Performance Goals**: ≤ 6 h total CPU time, ≤ 7 GB RAM, ≤ 14 GB disk  
**Constraints**: Must use only the three verified PR datasets (see “Verified datasets” block). No GPU required.  

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All scripts are deterministic (fixed random seeds), data is fetched from immutable HF URLs, and the full pipeline can be re‑run on a fresh runner. |
| II. Verified Accuracy | No external citations are introduced beyond the three verified dataset URLs. |
| III. Data Hygiene | Raw parquet files are checksum‑verified on download; every transformation writes a new file with a provenance note. |
| IV. Single Source of Truth | **`data/processed/processed_prs.csv` is designated as the Single Source of Truth** for all downstream figures, tables, and statistical results. |
| V. Versioning Discipline | All artifacts are listed in `state/projects/PROJ-411-evaluating-the-impact-of-code-generation.yaml` with content hashes (handled by the platform). |
| VI. Provenance Rigor | Classification follows the exact signal hierarchy defined in FR‑002. |
| VII. Statistical Validation Discipline | Normality testing, test selection, effect size calculation, IQR outlier handling, and mixed‑effects adjustment are implemented exactly as required. |

## Project Structure

```text
specs/001-code-gen-review-burden/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── contracts/
    ├── processed_prs.schema.yaml
    └── statistical_results.schema.yaml

code/
├── download_data.py
├── classify_provenance.py
├── compute_metrics.py
├── statistical_analysis.py
├── validation.py
├── sensitivity.py
└── report.py

data/
├── raw/
│   ├── prs_v2_sample.parquet
│   ├── authors_merged_model_prs.parquet
│   └── authors_merged_dataset_prs.parquet
├── processed/
│   └── processed_prs.csv
└── results/
    ├── stats_summary.csv   <-- must conform to contracts/statistical_results.schema.yaml
    └── validation_report.md

tests/
├── test_classify.py
├── test_metrics.py
└── test_analysis.py
```

**Structure Decision**: A single‑project layout under `code/` is sufficient; the analysis is pure data‑processing with no web service or mobile components.

## Phase‑by‑Phase Implementation Tasks (mapped to FR/SC)

| Phase | Description | FR/SC addressed |
|-------|-------------|-----------------|
| **0 – Data Acquisition** | Download the three parquet files from HuggingFace, verify checksums, convert to a unified DataFrame **validated against `raw_prs.schema.yaml` defined in `data-model.md`**. | FR‑001, SC‑005 |
| **1 – Provenance Classification** | Apply precedence rules (file‑header → diff‑pattern → commit‑message) to assign `provenance_label`. Exclude `Mixed` rows from primary analysis. **Bias assessment**: compare Mixed PRs to included groups on `lines_changed` and `comment_count`; log any systematic differences. | FR‑002, FR‑008, methodology‑05fdafd2 |
| **2 – Metric Computation & Filtering** | Compute `review_active_seconds` (using `first_comment_timestamp` if present, otherwise fallback to `review_duration_seconds`), `comment_density`, `issue_severity` (from PR labels). Filter `lines_changed ≥ 5` and `comment_count ≥ 1` (primary) plus a relaxed version (`≥ 0`) for sensitivity. | FR‑003, FR‑015, FR‑012, FR‑014 |
| **3 – Outlier Handling** | Apply IQR outlier removal with multiplier 1.5 (default) and generate versions for 1.0 and 2.0. | FR‑006 |
| **4 – Statistical Modeling** | • **Power Analysis** – using `statsmodels.stats.power.TTestIndPower` assume medium effect size = 0.5, α = 0.05, power = 0.8 → required sample size per group is set to be sufficiently large to ensure adequate statistical power.; abort with warning if groups smaller. <br>• **Normality** – Shapiro‑Wilk (α = 0.05). <br>• **Test selection** – Mann‑Whitney U or independent‑samples t‑test. <br>• **Effect size** – rank‑biserial or Cohen’s d. <br>• **Multiple Comparison** – Bonferroni correction across the primary metrics (α = 0.05 / 5 = 0.01). <br>• **Mixed‑effects model** with `repo_name` as random intercept **and fixed effects** for `lines_changed`, `author_experience`, and `repo_stars` to adjust for known confounders. <br>• **Issue severity** is treated as a **secondary exploratory** metric; primary burden is captured by `review_active_seconds` and `comment_density`. <br>• Chi‑square test for `issue_severity` distribution (treated as secondary exploratory metric). <br>• Output `stats_summary.csv` **must conform to `contracts/statistical_results.schema.yaml`**. | FR‑004, FR‑005, FR‑013, SC‑002, SC‑006, methodology‑b81eea42, methodology‑d576283a, methodology‑81094217, methodology‑461e29a7 |
| **5 – Validation** | Randomly sample a representative set of PRs per provenance group, have a human label them, compute Cohen’s κ. Flag groups with κ < 0.6. | FR‑007, SC‑001 |
| **6 – Sensitivity Analyses** | Re‑run Phase 4 for each IQR multiplier and for the relaxed comment filter; record any p‑value flips → “Low Robustness” flag. | FR‑006, FR‑014, SC‑003 |
| **7 – Reporting** | Assemble tables/figures (boxplots of review_active_seconds, comment_density; forest plot of effect sizes; κ summary). Emit null‑result statements when p ≥ α_corrected. Write `report.md`. | FR‑011, SC‑004 |
| **8 – Resource Monitoring** | Log CPU time and peak RAM; abort with clear error if RAM > 6 GB or CPU time > 5 h, satisfying SC‑005. | SC‑005 |
| **9 – Logging & Rate‑Limit Guard** | If any fallback API calls are needed (e.g., missing diff text), implement exponential backoff per FR‑009. | FR‑009 |

All phases are ordered so that data download precedes any consumption, classification precedes metric computation, metrics precede statistical testing, and tests precede reporting. The final `stats_summary.csv` **must conform to `contracts/statistical_results.schema.yaml`**.
