# Tasks: Evaluating the Impact of Code Generation on Code Review Burden

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and the three contract schemas under `specs/001-evaluating-the-impact-of-code-generation/contracts/`.

## Phase 1: Setup and first end‑to‑end analysis

**Goal**: Download the three verified real parquet datasets, verify their actual columns against `contracts/raw_prs.schema.yaml`, and run a thin end‑to‑end classification → metrics → primary statistical test on the primary population (`loubnabnl/prs-v2-sample`) producing real result rows.

- [ ] T001 [P] [US-001] Implement `code/download_data.py` (Phase 0): download the three verified real parquet datasets via `huggingface_hub` from their canonical HF URLs — `loubnabnl/prs-v2-sample` (primary population), `davanstrien/authors_merged_model_prs`, and `davanstrien/authors_merged_dataset_prs` (auxiliary known‑LLM references only) — into `data/raw/` as separate files tagged with `source_dataset`, compute SHA‑256 checksums into `data/checksums.txt`, and validate/inspect each file's actual columns against `contracts/raw_prs.schema.yaml` (FR‑022). Write `data/raw/schema_map.md` documenting, per dataset and per required variable, whether it is present, derivable, or missing. The loader MUST fail loudly (raise) on any download or read failure — no synthetic/mock fallback ever (FR‑001). If a required outcome variable (`comment_count`, merge timestamps, provenance‑signal fields) is missing in `prs-v2-sample`, halt with a clear scope‑mismatch error; missing fields in the davanstrien datasets are reported as expected degradation, not errors. Record the documented run command in `specs/001-evaluating-the-impact-of-code-generation/quickstart.md`.
  - Verification: `python code/download_data.py` exits 0; `data/raw/` contains the three real parquet files; `data/checksums.txt` lists three SHA‑256 hashes; `data/raw/schema_map.md` exists and covers every field in `raw_prs.schema.yaml` per dataset.

- [ ] T002 [US-001] Implement `code/classify_provenance.py` (Phase 1) with focused tests in `tests/test_classify.py`: apply the FR‑002 precedence hierarchy — file‑header attribution (overrides all) → diff‑pattern matches to known LLM generation signatures (overrides commit‑message keywords) → commit‑message keywords (e.g., “Copilot”, “GPT”, “Codeium”) — to assign `provenance_label` ∈ {LLM-generated, Human‑written, Mixed} within `prs-v2-sample` only (FR‑002, FR‑008). PRs with conflicting LLM and human signals are labeled Mixed and excluded from the binary comparison. When higher‑precedence signal fields are absent per the schema map, the precedence collapses to the commit‑message tier and this is reported as an explicit limitation, not silently assumed. Log a warning and exclude any repository with zero LLM‑generated PRs (FR‑010). Emit `data/processed/classified_prs.csv` (intermediate) and the group×source contingency table `data/results/group_source_contingency.csv`. **Do not** perform selection‑bias analysis here.
  - Verification: `pytest tests/test_classify.py` passes, including precedence‑order unit tests (header > diff > commit‑message), Mixed‑conflict cases, and keyword‑negative default; `data/processed/classified_prs.csv` exists with `provenance_label` column containing only the three allowed values.

- [ ] T003 [US-001] Implement `code/compute_metrics.py` (Phase 2, sole writer of the SSoT) with tests in `tests/test_metrics.py`: from `classified_prs.csv` compute `review_duration_seconds` (creation→merge), `review_active_seconds` (first comment→merge using `first_comment_timestamp` when present; otherwise fall back to `review_duration_seconds` with an explicit limitation note, FR‑015/FR‑016), `comment_density` (comments/lines), `issue_severity` mapped from PR labels to {bug, enhancement, documentation, other} (FR‑012), and `creation_period` (calendar quarter of `created_at`). Write the unfiltered SSoT `data/processed/processed_prs.csv` conforming to `contracts/processed_prs.schema.yaml` (FR‑020). Implement the numeric severity mapping (bug = 3, enhancement = 2, documentation = 1, other = 0) and add a column `severity_score` for quantitative analysis (new requirement for FR‑012 quantitative treatment).  <!-- FAILED-IN-EXECUTION: code/compute_metrics.py exit=1 -->
  - Verification: `pytest tests/test_metrics.py` passes including IQR‑boundary and severity‑mapping unit tests; `processed_prs.csv` validates against `processed_prs.schema.yaml` and contains the new `severity_score` column.

- [ ] T011 [US-001] Perform selection‑bias assessment (FR‑018) **after** metrics are available: compare Mixed vs. pure groups on `comment_density`, `issue_severity`, and `severity_score` using Mann‑Whitney U (for numeric) and chi‑square (for categorical) with α = 0.05. Write `data/results/selection_bias_report.csv`. 
  - Verification: script `code/selection_bias.py` runs without error; report file exists with p‑values and effect sizes.

- [ ] T012 [US-001] Implement `code/outlier_filter.py` (Phase 3, sole writer of all filtered variants): from the SSoT apply the FR‑003 filter (`lines_changed ≥ 5`, `comment_count ≥ 1`) plus IQR outlier removal (multiplier 1.5) → `data/processed/filtered_prs.csv`; IQR 1.0 and 2.0 variants → `filtered_prs_iqr1.0.csv`, `filtered_prs_iqr2.0.csv` (FR‑006); comment‑relaxed variant (`comment_count ≥ 0`, IQR 1.5) → `filtered_prs_relaxed.csv` (FR‑014). 
  - Verification: `pytest tests/test_outlier_filter.py` passes; all five filtered files exist.

- [ ] T004 [US-002] Implement `code/statistical_analysis.py` (Phase 4) and run the thin end‑to‑end primary comparison on real data: perform an **a priori power analysis** via `statsmodels.stats.power.TTestIndPower` (d = 0.5, α = 0.05, power = 0.8 → n ≈ 64/group) and report both the t‑test‑based and rank‑based sample thresholds with the ARE limitation (FR‑019, SC‑007). Detect normality per metric per group with Shapiro‑Wilk; **automatically select** the appropriate test (Mann‑Whitney U for non‑normal, Welch t‑test for normal) and report the chosen test name. Compute effect sizes (rank‑biserial for Mann‑Whitney, Cohen’s d for t‑test) **regardless of significance** (FR‑005). Apply Bonferroni correction across all primary metrics (α = 0.05/k). Include a chi‑square test with Cramér’s V for the categorical `issue_severity` and a separate Mann‑Whitney U test for the numeric `severity_score`. Output `data/results/stats_summary.csv` conforming to `contracts/statistical_results.schema.yaml`. 
  - Verification: `pytest tests/test_analysis.py` passes; `stats_summary.csv` contains rows for each metric, test name, p‑value, effect size, and corrected α; power analysis line is present.

- [ ] T013 [US-002] Synthetic benchmark validation: generate a tiny synthetic dataset with a known effect size for each metric, run the same statistical pipeline, and assert that the reported effect size is within ±0.05 of the analytically expected value (FR‑005). No synthetic data are merged with real results. 
  - Verification: script runs and exits 0; asserts pass.

- [ ] T005 [US-002] Complete the full statistical modeling in `code/statistical_analysis.py` (Phase 4 continuation): mixed‑effects model with `repo_name` random intercept plus fixed effects for `lines_changed`, `author_experience`, `repository_popularity` (only where present per the schema map), and the temporal covariate `creation_period`. Perform VIF collinearity diagnostics for `lines_changed` vs. `comment_density`; if r > 0.8, report a joint relationship only. Add stratified‑by‑period sensitivity check and record any limitation statements. Append these mixed‑effects results to `data/results/stats_summary.csv`. 
  - Verification: model runs without error; additional rows appear in `stats_summary.csv`; VIF report is written to `data/results/vif_report.txt`.

- [ ] T014 [US-003] Implement `code/validation_generate.py` (Phase 5) to deterministically sample (fixed seed) 50 PRs per group from `classified_prs.csv` and emit the labeling worksheet `data/results/validation_sample.csv`. This task owns the production of the worksheet that human annotators must fill. 
  - Verification: script runs; exactly 100 rows (50 per group) are written.

- [ ] T006 [US-003] Implement `code/validation.py` (Phase 5): read the human‑provided `data/processed/manual_labels.csv` (must exist, otherwise abort with clear error), compute Cohen’s κ, flag any group with κ < 0.6, and write `data/results/validation_report.md`. If κ < 0.6 or the false‑negative rate in the Human‑written group exceeds 10 %, record the corresponding limitation and **do not** allow the pipeline to proceed to the final report without these flags being documented. The pre‑planned misclassification response now runs **after** the sensitivity analysis (T007). 
  - Verification: script exits 0 when `manual_labels.csv` is present; κ is reported; pipeline aborts with informative message if file missing.

- [ ] T007 [US-003] Implement `code/sensitivity.py` (Phase 6): re‑run the primary tests for IQR multipliers {1.0, 1.5, 2.0} and the relaxed comment filter (≥ 0); record significance flips and set the “Low Robustness” flag on any flip (FR‑006, FR‑014, SC‑003). Also run the source‑stratified sensitivity analysis: descriptive comparison of review metrics for the known‑LLM davanstrien PRs (where outcome fields exist) against the primary‑population groups, reported separately and never pooled. Write `data/results/sensitivity_report.csv`. 
  - Verification: `sensitivity_report.csv` contains rows for all three IQR multipliers and the relaxed filter with p‑values, significance booleans, and flip flags; script exits 0.

- [ ] T008 [P] [US-001] Implement resource monitoring in `code/` (Phase 8): use `psutil` to log peak RAM and CPU time per script run to `data/results/resource_usage.csv`, aborting with a clear error if the GitHub Actions free‑tier limits (~7 GB RAM, ≤ 6 h CPU) are approached (SC‑005). Add the conditional rate‑limit guard (Phase 9): exponential backoff with pause/resume for any optional GitHub REST enrichment calls (FR‑009) — a no‑op when the static datasets suffice. 
  - Verification: `resource_usage.csv` shows measured peak RAM/CPU per script; all runs stay within limits.

- [ ] T015 [P] Reproducibility – Pin dependencies: create `code/requirements.txt` listing all pinned packages (e.g., `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `huggingface_hub==0.23.*`, `pyyaml==6.0.*`, `matplotlib==3.8.*`, `psutil==5.9.*`). This satisfies the constitution’s reproducibility clause. 
  - Verification: `requirements.txt` exists and matches the versions declared in the plan.

- [ ] T009 [US-002] Implement `code/report.py` (Phase 7): generate figures directly from the validated outputs — boxplots of `review_active_seconds` and `comment_density` by group, effect‑size summary, κ summary, and the group×source contingency table — into `data/results/figures/`. Assemble `data/results/report.md` with: explicit null‑result statements (“No statistically significant difference found at α = 0.05”) wherever applicable; effect sizes benchmarked against small/medium/large standards (SC‑004); the construct‑validity caveat for issue‑severity‑as‑effort‑proxy **without** the unverified citation; and the full set of limitation statements — power/sample‑size, selection bias from Mixed exclusion (FR‑018), misclassification attenuation, missing covariates, temporal confounding, dataset‑origin, provenance‑label proxy limits, and observational/associational framing. Also include the quantitative severity‑score results. 
  - Verification: `python code/report.py` exits 0; every figure file exists; `report.md` contains the required statements and references all result files.

- [ ] T010 Re‑run the complete documented workflow from its declared inputs (`python code/download_data.py` → `classify_provenance.py` → `compute_metrics.py` → `outlier_filter.py` → `statistical_analysis.py` → `validation_generate.py` → `validation.py` → `sensitivity.py` → `report.py`) per `quickstart.md`, confirm all pytest suites pass (`pytest tests/`) and every artifact check above succeeds, and document the paper‑stage handoff in `data/results/report.md`: the linked result tables (`stats_summary.csv`, `sensitivity_report.csv`, `selection_bias_report.csv`, `group_source_contingency.csv`), figure files, validation status, and the honest statement of any pending items (e.g., κ awaiting manual labels). 
  - Verification: a fresh sequential run of all documented commands completes within resource limits; `pytest tests/` passes; `report.md` ends with a paper‑hand‑off section listing every artifact path.

## Phase 2: Complete the study and validate its evidence

*(All tasks above already cover the required validation, sensitivity, and reporting steps.)*

## Phase 3: Reproducible results and paper handoff

*(Handled by T009 and T010.)*

## Dependencies and requirement coverage

- FR‑001/FR‑022 (data acquisition + schema gate): T001. FR‑009 (rate‑limit guard, conditional): T008.
- FR‑002/FR‑008/FR‑010/FR‑018 (classification, Mixed exclusion, zero‑LLM repos, selection bias): T002, T011.
- FR‑003/FR‑012/FR‑015/FR‑016/FR‑020 (metrics, severity, SSoT) and FR‑006/FR‑014 (filter variants): T003, T012.
- FR‑004/FR‑005/FR‑011/FR‑019/FR‑021, SC‑002/SC‑004/SC‑006/SC‑007 (primary statistics, effect sizes, power, schema‑conformant results): T004, T013.
- FR‑013 (mixed‑effects + covariates): T005.
- FR‑007/SC‑001 (Cohen’s κ validation): T014, T006.
- FR‑006/FR‑014/SC‑003 (sensitivity): T007.
- SC‑005 (resources): T008.
- FR‑009 (rate‑limit guard): T008.
- Reproducibility (requirements.txt): T015.
- Constitution VII (manual verification) enforced by T014 → T006 pipeline.

Execution order: T001 → T002 → T003 → T011 → T012 → T004 → T013 → T005 → T014 → T006 → T007 → T008 → T015 → T009 → T010. T006 will abort if `manual_labels.csv` is missing, ensuring the mandatory κ calculation is performed before final reporting. 
