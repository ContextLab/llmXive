# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Burden

**Branch**: `001-code-gen-review-burden` | **Date**: 2026-10-17 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-evaluating-the-impact-of-code-generation/spec.md`

## Summary

The project will (1) download three verified public PR parquet datasets from HuggingFace, (2) verify per-dataset which variables each actually contains (schema-mapping step with explicit per-dataset reporting), (3) run the **primary comparison within a single PR population** (`loubnabnl/prs-v2-sample`, both LLM-labeled and Human-labeled PRs classified by the FR-002 signal hierarchy, so group membership is not determined by dataset origin), (4) compute reviewer-effort metrics (`review_active_seconds`, `comment_density`, `issue_severity`), (5) perform an **observational, associational** statistical comparison (pre-specified Mann-Whitney U primary test with Welch t-test robustness companion, Bonferroni-adjusted α, effect-size reporting, mixed-effects adjustment including temporal and source covariates), (6) validate the classification against a manual sample (Cohen's κ) with a pre-planned misclassification response, and (7) run predefined sensitivity analyses (outlier IQR thresholds, comment-filter relaxation, source-stratified analysis). The two `davanstrien` datasets are used **only** as auxiliary known-LLM references (classification validation and a descriptive source-stratified sensitivity analysis); they are never pooled with the control group. All steps are CPU-tractable within GitHub Actions free-tier limits. **All findings are framed as associational differences; no causal claims are made.**

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `huggingface_hub==0.23.*`, `pyyaml==6.0.*`, `matplotlib==3.8.*`, `psutil==5.9.*`
**Storage**: file-based CSV/Parquet under `data/`
**Testing**: `pytest` (unit tests for classification, metric computation, statistical wrappers)
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, ~7 GB RAM, ~14 GB disk, ≤6 h)
**Project Type**: research-oriented CLI scripts
**Performance Goals**: ≤ 6 h total CPU time, ≤ 7 GB RAM (SC-005)
**Constraints**: Only the three verified PR parquet URLs may be used as data sources. No GPU required; no GitHub API scraping is needed because the verified datasets are pre-extracted PR dumps (FR-001/FR-009 are satisfied by using static downloads; the backoff guard is retained only for the optional metadata-enrichment path and is a no-op when unused).

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | All scripts are deterministic (pinned random seeds in `code/`); data fetched from the same canonical HF URLs every run; full pipeline re-runnable on a fresh runner. |
| II. Verified Accuracy | No external citations beyond the three verified dataset URLs listed in the Verified-datasets block. The unverified "Jones et al., 2022" citation in spec FR-017 is NOT repeated in any plan-stage artifact; the construct-validity caveat is stated without citation (spec edit kicked back). |
| III. Data Hygiene | Raw parquet files are SHA-256 checksummed on download (`data/checksums.txt`); raw files never modified; every transformation writes a new file with a documented derivation; no PII committed (PR text fields used only transiently for classification, not persisted beyond needed columns). |
| IV. Single Source of Truth | `data/processed/processed_prs.csv` (FR-020), written solely by `compute_metrics.py`, is the SSoT; every figure/statistic traces to it. |
| V. Versioning Discipline | Artifacts carry content hashes recorded by the platform; state file `updated_at` maintained. |
| VI. Provenance Rigor | Classification follows the exact FR-002 signal hierarchy; a Human-written control group drawn from the same PR population is maintained for all comparisons. |
| VII. Statistical Validation Discipline | Pre-specified Mann-Whitney U primary test (with Welch t-test companion), effect sizes, IQR outlier handling (1.5 default), and Cohen's κ on a manual sample per group are implemented exactly as required. |

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
├── download_data.py        # Phase 0: download + checksum + per-dataset schema mapping
├── classify_provenance.py  # Phase 1 (writes classified_prs.csv)
├── compute_metrics.py      # Phase 2 (sole writer of the SSoT processed_prs.csv)
├── outlier_filter.py       # Phase 3 (sole writer of all filtered variants)
├── statistical_analysis.py # Phase 4
├── validation.py           # Phase 5
├── sensitivity.py          # Phase 6
└── report.py               # Phase 7

data/
├── raw/                    # immutable downloaded parquet files
├── processed/
│   ├── classified_prs.csv  # Phase 1 output (intermediate)
│   ├── processed_prs.csv   # SSoT (FR-020), written by compute_metrics.py
│   ├── filtered_prs.csv    # Phase 3 output, IQR = 1.5, comment_count >= 1
│   ├── filtered_prs_iqr1.0.csv  # Phase 3 output, IQR = 1.0 variant (FR-006)
│   ├── filtered_prs_iqr2.0.csv  # Phase 3 output, IQR = 2.0 variant (FR-006)
│   └── filtered_prs_relaxed.csv # Phase 3 output, comment_count >= 0 variant (FR-014)
└── results/
    ├── stats_summary.csv   # conforms to contracts/statistical_results.schema.yaml
    ├── sensitivity_report.csv
    ├── validation_report.md
    └── figures/

tests/
├── test_classify.py
├── test_metrics.py
└── test_analysis.py
```

**Structure Decision**: single-project layout under `code/`; pure data processing, no service/UI components. Each intermediate file has exactly one writer script, completing the Constitution III/IV derivation chain.

## Dataset-Variable Fit Assessment (blocking gate before analysis)

Phase 0 inspects the actual columns of each downloaded parquet and writes `data/raw/schema_map.md` listing, for every variable required by `contracts/raw_prs.schema.yaml`, whether it is present, derivable, or **missing — per dataset**. Expected per-dataset degradation (stated up front, verified at runtime):

- **`loubnabnl/prs-v2-sample` (primary population)**: expected to carry PR-level fields (`pr_id`, `repo_name`, timestamps, additions/deletions, comment counts, commit-message text, labels). This dataset alone drives the primary comparison. If a required outcome variable (`comment_count`, merge timestamps, provenance signal fields) is missing **here**, the pipeline halts and reports the mismatch for scope revision. `first_comment_timestamp` (FR-016) and `diff_text`/`file_headers` may be absent; if so, `review_active_seconds` falls back to `review_duration_seconds` and the FR-002 precedence collapses to the commit-message tier — both reported as explicit limitations, not silently assumed.
- **`davanstrien/authors_merged_model_prs` and `authors_merged_dataset_prs` (auxiliary only)**: these are curated collections of PRs authored by LLM agents on HuggingFace Hub repositories (model-card/dataset-metadata edits). They are **near-certainly missing** review-interaction fields (`comment_count`, `first_comment_timestamp`, review comments, labels) and diff/header text; FR-002 precedence there collapses to commit-message-only. Because of this expected degradation — and because their sampling frame (HF Hub metadata PRs) differs from the general GitHub PR population — they are **excluded from the primary comparison** and used only as (a) a known-LLM reference for classification-signal validation and (b) a descriptive source-stratified sensitivity analysis, conditional on the fields actually present. Missing outcome fields in these datasets do not halt the pipeline.
- **`author_experience` / `repository_popularity` (FR-013 covariates)**: if absent, the mixed-effects model is fit with repository random intercepts only, and the missing covariates are reported as an uncontrolled-confounding limitation rather than fabricated proxies.

## Phase-by-Phase Implementation Tasks (mapped to FR/SC)

| Phase | Description | FR/SC addressed |
|-------|-------------|-----------------|
| **0 – Data Acquisition & Schema Mapping** | Download the three verified parquet files (SHA-256 checksums to `data/checksums.txt`) and validate/inspect columns **against `contracts/raw_prs.schema.yaml` defined in `data-model.md`** (FR-022), per dataset. Emit `data/raw/schema_map.md` documenting per-dataset variable availability per the fit gate above. Keep the three files separate (tagged with `source_dataset`); the primary analysis uses only `prs-v2-sample`. | FR-001, FR-016, FR-020, FR-022, SC-005 |
| **1 – Provenance Classification** | Apply precedence rules (file-header → diff-pattern → commit-message keywords) to assign `provenance_label` **within `prs-v2-sample`**; `Mixed` for conflicting signals, excluded from the binary comparison. Log a warning and exclude any repository with zero LLM-generated PRs (FR-010). Emit `data/processed/classified_prs.csv` (intermediate; the SSoT is written in Phase 2). **Selection-bias assessment (FR-018)**: compare Mixed PRs vs. pure groups on `lines_changed`, `comment_density`, `issue_severity` distributions; report any significant differences. Also emit a **group×source contingency table** (provenance label vs. `source_dataset`) so readers can assess residual source confounding. | FR-002, FR-008, FR-010, FR-018 |
| **2 – Metric Computation & Filtering (sole writer of the SSoT)** | From `classified_prs.csv`, compute `review_duration_seconds` (creation→merge) and `review_active_seconds` (first comment→merge, using `first_comment_timestamp` when present; fallback + limitation note per the fit gate). Compute `comment_density`, `issue_severity` (from PR labels, mapped to bug/enhancement/documentation/other). Write the SSoT `data/processed/processed_prs.csv` (unfiltered; filtering is Phase 3's responsibility). | FR-003, FR-012, FR-015, FR-016, FR-020 |
| **3 – Outlier Handling & Filter Variants (sole writer of all filtered files)** | From the SSoT, apply the FR-003 filter (`lines_changed ≥ 5`, `comment_count ≥ 1`) plus IQR outlier removal (default multiplier 1.5) → `filtered_prs.csv`; IQR 1.0 and 2.0 variants → `filtered_prs_iqr1.0.csv`, `filtered_prs_iqr2.0.csv`; and the comment-relaxed variant (`comment_count ≥ 0`, IQR 1.5) → `filtered_prs_relaxed.csv`. | FR-003, FR-006, FR-014 |
| **4 – Statistical Modeling** | • **A priori power analysis (FR-019)**: `statsmodels.stats.power.TTestIndPower`, d = 0.5, α = 0.05, power = 0.8 → required n ≈ 64/group. This figure is **t-test-based**; the pre-specified primary test is the rank-based Mann-Whitney U, whose asymptotic relative efficiency under normality is close to that of the parametric alternative, implying a slightly larger sample requirement than the corresponding t-test; the limitation statement covers both thresholds (SC-007). • **Normality**: Shapiro-Wilk (α = 0.05) per metric per group, reported for transparency; because normality tests are consistent, rejection at scale is expected and **Mann-Whitney U is pre-specified as the expected primary test** — the t-test branch is retained for small-sample cases only. • **Robustness companion**: the Welch t-test (with Cohen's d) is reported alongside every primary Mann-Whitney U result regardless of the normality outcome, so test selection is not the sole driver of conclusions. • **Effect sizes**: rank-biserial (Mann-Whitney U) and Cohen's d (Welch), reported regardless of significance; verified on a synthetic benchmark dataset with known effect (±0.05 tolerance, FR-005). • **Multiplicity**: Bonferroni correction across the primary tests (α = 0.05/k, k = number of primary metrics actually tested). • **Clustering adjustment (FR-013)**: mixed-effects model with `repo_name` random intercept plus fixed effects for `lines_changed`, `author_experience`, `repository_popularity` (where available, see fit gate), and a **temporal covariate** — PR creation period (calendar quarter of `created_at`) as a fixed effect — to control temporal drift in review practices; a stratified-by-period sensitivity check accompanies it, and a temporal-confounding limitation is stated. • **Collinearity diagnostic**: VIF for `lines_changed` vs. `comment_density`; if r > 0.8, report as joint relationship only. • **Chi-square test** for `issue_severity` distribution between groups (SC-006). • Output `stats_summary.csv` conforming to `contracts/statistical_results.schema.yaml` (FR-021). | FR-004, FR-005, FR-011, FR-013, FR-019, FR-021, SC-002, SC-004, SC-006, SC-007 |
| **5 – Validation (Cohen's κ) & Misclassification Response** | Deterministically sample (fixed seed) 50 PRs per group and emit a labeling worksheet (`data/results/validation_sample.csv`). A human labels the sample offline; the committed labels file (`data/processed/manual_labels.csv`) is read by `validation.py`, which computes Cohen's κ and flags groups with κ < 0.6. **Pre-planned misclassification response**: from the validation sample, estimate the false-negative rate in the Human-written group (PRs labeled Human by the classifier but LLM by the human rater). If that rate exceeds 10%, the report (a) states that group differences are attenuated toward the null, (b) runs a sensitivity analysis excluding keyword-negative PRs from repositories with high LLM-PR prevalence, and (c) records the attenuation as a limitation; if κ < 0.6 in a group, that group's headline comparison is additionally downgraded to descriptive reporting. **If no committed manual-label file exists at run time, the pipeline emits `validation_report.md` stating that κ validation is pending and treats SC-001 as unverified** — it never fabricates labels. The davanstrien datasets serve as a known-LLM reference for signal validation where their fields permit. | FR-007, SC-001 |
| **6 – Sensitivity Analyses** | Re-run the primary tests for IQR multipliers {1.0, 1.5, 2.0} and for the relaxed comment filter (≥ 0); record significance flips → "Low Robustness" flag (SC-003); write `sensitivity_report.csv`. Additionally run the **source-stratified sensitivity analysis**: descriptive comparison of review metrics for the known-LLM davanstrien PRs (where outcome fields exist) against the primary-population groups, reported separately and never pooled, so readers can assess dataset-origin confounding. | FR-006, FR-014, SC-003 |
| **7 – Reporting** | Assemble tables/figures (boxplots of `review_active_seconds` and `comment_density` by group; effect-size summary; κ summary; group×source contingency table). Insert explicit null-result statements ("No statistically significant difference found at α = 0.05") whenever p ≥ α (FR-011). Include power (t-test- and rank-based thresholds), selection-bias, misclassification-attenuation, missing-covariate, temporal-confounding, dataset-origin, and observational-framing limitation statements. Write `report.md`. | FR-011, FR-017, FR-018, SC-004 |
| **8 – Resource Monitoring** | `psutil` logs peak RAM and CPU time per script; abort with a clear error if limits are approached, satisfying SC-005. | SC-005 |
| **9 – Rate-Limit Guard (conditional)** | Exponential backoff with pause/resume for any optional GitHub REST enrichment calls (e.g., fetching missing metadata); a no-op when the static datasets suffice. | FR-009 |

Ordering: data is downloaded (Phase 0) before any consumption; classification precedes metrics; metrics precede filtering; filtering precedes testing; tests and figures precede reporting. Every FR-001 through FR-022 and SC-001 through SC-007 is addressed above. The GitHub API rate limit value remains `[deferred]` per FR-001/FR-009; the static-download design makes this non-blocking.

## Complexity Tracking

No constitution violations requiring justification. One spec-level gap is kicked back: FR-017's unverified "Jones et al., 2022" citation must be removed from spec.md (Constitution II); plan-stage artifacts state the construct-validity caveat without that citation.