# Implementation Plan: Evaluating the Impact of Code Generation on Code Review Burden

**Branch**: `001-code-gen-review-burden` | **Date**: 2026-10-26 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `/specs/001-code-gen-review-burden/spec.md`

## Summary
The project will (1) extract pull‑request metadata from a curated list of public GitHub repositories via the GitHub REST API (respecting rate limits and exponential backoff), (2) verify that each PR contains every variable required by the schemas (including the newly‑added `first_comment_timestamp`), (3) classify each PR’s provenance using the exact FR‑002 precedence hierarchy (file‑header > diff‑pattern > commit‑message), (4) compute reviewer‑effort metrics (`review_active_seconds`, `review_duration_seconds`, `comment_density`, `issue_severity`), (5) filter & outlier‑remove according to FR‑003/FR‑006/FR‑014, (6) run a pre‑registered statistical comparison (Mann‑Whitney U primary, Welch t‑test companion) with mixed‑effects adjustment (FR‑013) and Bonferroni correction, (7) perform a manual validation of provenance on an independent auxiliary dataset (Cohen’s κ, FR‑007), (8) conduct the required sensitivity analyses, and (9) generate a fully reproducible report. All steps are CPU‑tractable on the GitHub Actions free tier; no GPU escape hatch is needed.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `datasets==2.19.*`, `pyyaml==6.0.*`, `matplotlib==3.8.*`, `psutil==5.9.*`, `httpx==0.27.*` (for GitHub API)  
- **Storage**: file‑based CSV/Parquet under `data/`  
- **Testing**: `pytest` (unit tests for classification precedence, metric computation, statistical wrappers)  
- **Target Platform**: Linux runner (GitHub Actions free tier: 2 CPU, ~7 GB RAM, ≤6 h)  
- **Constraints**: Must use only open GitHub repositories listed in `code/repo_list.txt`; no external gated data.  
- **Performance Goals**: complete all phases within the CI time‑budget and memory limit (SC‑005)  
- **Citation for Issue‑Severity Proxy**: Jones et al., 2022 (see FR‑017).  

## Constitution Check

| Principle | How the plan satisfies it |
|-----------|---------------------------|
| I. Reproducibility | Fixed random seeds; deterministic API pagination; all scripts are pure functions producing files with documented names. |
| II. Verified Accuracy | No new citations beyond the required Jones et al., 2022; all external data sources are public GitHub repos. |
| III. Data Hygiene | Raw JSON responses are SHA‑256‑checked (`data/checksums.txt`). No in‑place mutation; each transformation writes a new file. |
| IV. Single Source of Truth | `data/processed/processed_prs.csv` is the SSoT (FR‑020) and is the sole input to downstream analysis. |
| V. Versioning Discipline | Platform‑provided content hashes track every artifact; `state/projects/...updated_at` is updated automatically. |
| VI. Provenance Rigor | Classification follows FR‑002 precedence exactly; unit test `test_precedence_header_wins` guarantees header overrides. |
| VII. Statistical Validation Discipline | Pre‑specified Mann‑Whitney U primary test, Welch t‑test companion, effect‑size reporting, IQR outlier handling, mixed‑effects adjustment, Bonferroni correction, and independent validation κ are all implemented. |

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
├── download_data.py
├── classify_provenance.py
├── compute_metrics.py
├── outlier_filter.py
├── statistical_analysis.py
├── validation.py
├── sensitivity.py
└── report.py

data/
├── raw/
│   └── (GitHub API JSON responses)
├── processed/
│   ├── classified_prs.csv
│   ├── processed_prs.csv
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
| **0 – Data Acquisition & Schema Mapping** | Use `download_data.py` to query the GitHub REST API for each repository in `code/repo_list.txt`. Pagination respects the API’s rate limit; exponential backoff (FR‑009) is applied on 403/429 responses. Responses are saved under `data/raw/` and SHA‑256 checksummed. Verify presence of every required variable against `contracts/raw_prs.schema.yaml`; abort with a clear error if any primary variable is missing. **`first_comment_timestamp` is optional (may be null); if absent for a PR, `review_active_seconds` will fall back to `review_duration_seconds` and this limitation will be logged.** | FR‑001, FR‑016, FR‑020, FR‑022, SC‑005 |
| **1 – Provenance Classification** | Apply FR‑002 precedence rules to each PR **in the primary dataset only**. Write `data/processed/classified_prs.csv` with a `provenance_label` column. **Precedence**: (1) File‑header attribution → label per header (overrides all); (2) Diff‑pattern matches → label per diff; (3) Commit‑message keywords → label per keyword. If after applying these rules both LLM and Human signals remain, label as “Mixed” and **exclude** from the binary comparison (FR‑008). PRs labelled “Mixed” are retained for the selection‑bias check (FR‑018). Repositories that contain **zero LLM‑generated PRs** trigger a **graceful fallback**: the binary hypothesis tests are skipped, a descriptive summary of the Human‑written group is produced, and a limitation statement is added to the final report. Write a contingency table `data/results/group_source_contingency.csv`. | FR‑002, FR‑008, FR‑010 (modified handling), FR‑018 |
| **2 – Metric Computation & SSoT** | From `classified_prs.csv`, compute `lines_changed` (additions + deletions), `review_duration_seconds` (merged − created), `review_active_seconds` (first comment → merge using `first_comment_timestamp`; if missing, fall back to `review_duration_seconds` and note the limitation), `comment_density`, `issue_severity` (mapped from PR labels per Jones et al., 2022), and `creation_quarter`. Write **only** `data/processed/processed_prs.csv` (the SSoT, FR‑020). | FR‑003, FR‑012, FR‑015, FR‑016, FR‑020 |
| **3 – Outlier Handling & Filter Variants** | Apply FR‑003 filter (`lines_changed ≥ 5`, `comment_count ≥ 1`) and IQR outlier removal with multipliers 1.0, 1.5, 2.0 → three filtered files. Also create `*_relaxed.csv` where `comment_count ≥ 0`. | FR‑003, FR‑006, FR‑014 |
| **4 – Statistical Modeling** | • **Power analysis**: Perform a Mann‑Whitney U‑appropriate power calculation (using `statsmodels.stats.power.NormalIndPower` with rank‑based effect‑size conversion) targeting a medium effect (Cohen’s d≈0.5 ↔ rank‑biserial≈0.33) and α = 0.05. • **Normality**: Shapiro‑Wilk per metric per group. • **Primary test**: Mann‑Whitney U on `review_active_seconds` and `comment_density` (report rank‑biserial). • **Companion test**: Welch t‑test (report Cohen’s d). • **Mixed‑effects model** (FR‑013) with `repo_name` random intercept + fixed effects (`lines_changed`, `author_experience`, `repository_popularity`, `creation_quarter`). • **Chi‑square** for `issue_severity`. • **Bonferroni** correction across all primary metrics (α_corrected = 0.05/k). • **Collinearity**: VIF for `lines_changed` vs. `comment_density`; if VIF > 5, report joint relationship only. Write `data/results/stats_summary.csv` conforming to `contracts/statistical_results.schema.yaml`. If **no LLM‑generated PRs** are present (see Phase 1 fallback), this phase writes a descriptive summary instead of hypothesis‑test rows. | FR‑004, FR‑005, FR‑011, FR‑013, FR‑019, FR‑021, SC‑002, SC‑004, SC‑006, SC‑007 |
| **5 – Validation (Cohen’s κ) & Independent Misclassification Check** | • Sample **independently** 50 PRs per group from the auxiliary known‑LLM datasets (AGBD & AGBD‑Lite) to compute Cohen’s κ against human labels (`validation_independent.csv`). • Additionally, draw a second random 50‑PR‑per‑group sample from the primary dataset for a sanity check. • If κ < 0.6 (SC‑001) flag the group and downgrade to descriptive reporting. • Estimate false‑negative rate; if > 10 % run a secondary analysis excluding keyword‑negative PRs from high‑LLM prevalence repos and note the attenuation limitation. Produce `data/results/validation_report.md`. | FR‑007, SC‑001 |
| **6 – Sensitivity Analyses & Selection‑Bias Checks** | • Re‑run the primary tests for each IQR multiplier (1.0, 1.5, 2.0) and for the relaxed comment filter (≥ 0). Record any significance flips → “Low Robustness” flag (SC‑003). • Perform a **selection‑bias analysis** comparing excluded‑repo PRs (zero LLM PRs) to included repos on size, comment density, and severity; report any significant differences (addresses FR‑018). • Report the contingency table `group_source_contingency.csv`. Write `data/results/sensitivity_report.csv`. | FR‑006, FR‑014, FR‑018, SC‑003 |
| **7 – Reporting** | Assemble tables, box‑plots, contingency tables, and explicit null‑result statements (FR‑011). Include limitation statements for power, selection bias, misclassification attenuation, missing `first_comment_timestamp`, observational framing, and any fallback due to zero LLM PRs. Write `report.md`. | FR‑011, FR‑017, FR‑018 |
| **8 – Resource Monitoring** | Each script logs peak RAM & CPU via `psutil`; abort with a clear error if > 6 GB RAM or > 6 h cumulative runtime (SC‑005). | SC‑005 |
| **9 – Optional GitHub API Enrichment** | Implement exponential backoff (FR‑009) for any optional metadata fetches; the main pipeline runs without additional API calls, so the guard is a no‑op in CI. | FR‑009 |

All 22 functional requirements (FR‑001 – FR‑022) and 7 success criteria (SC‑001 – SC‑007) are now explicitly covered.

## Complexity Tracking
No constitution violations require justification. The only spec‑level gap was the missing citation for issue‑severity (Jones et al., 2022); this has been added, satisfying Constitution II.

---


