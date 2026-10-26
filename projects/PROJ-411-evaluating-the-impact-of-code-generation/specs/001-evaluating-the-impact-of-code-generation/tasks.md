# Tasks: Evaluating the Impact of Code Generation on Code Review Burden

**Inputs**: `spec.md`, `plan.md`, `data-model.md`, and the three contract schemas under `specs/001-evaluating-the-impact-of-code-generation/contracts/`.

## Phase 1 – Setup and first end‑to‑end analysis  

**Goal**: Obtain real input data via the GitHub REST API, produce a classified and metric‑rich single source of truth, and verify that a minimal pipeline runs without error on real data.

- [ ] T001 [P] [US-001] **Download raw PR metadata from GitHub** – implement `code/download_data.py` that: <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 -->
  - Reads the list of target repositories from `code/repo_list.txt`.
  - Calls the GitHub REST API (`/repos/{owner}/{repo}/pulls`) with pagination, respecting the concrete rate‑limit of **5 000 requests per hour** (FR‑001) and applying exponential backoff on 429/403 responses (FR‑009).
  - Persists raw JSON responses under `data/raw/` (one file per repository) and records SHA‑256 checksums in `data/checksums.txt`.
  - Validates each raw record against `specs/001-evaluating-the-impact-of-code-generation/contracts/raw_prs.schema.yaml`; aborts loudly if required fields (including `first_comment_timestamp`) are missing.
  - Writes a mapping report `data/raw/schema_map.md` documenting presence/derivation of each required field.
  - Logs the exact command used in `specs/001-evaluating-the-impact-of-code-generation/quickstart.md`.
  - **Verification**: `python code/download_data.py` exits 0; raw JSON files exist; checksums file present; schema_map covers all required fields; rate‑limit handling exercised.

- [ ] T002 [P] [US-001] **Classify code provenance** – implement `code/classify_provenance.py` that reads the raw files produced by T001, applies FR‑002 precedence (file‑header > diff‑pattern > commit‑message) and produces:
  - `data/processed/classified_prs.csv` with a `provenance_label` column limited to `["LLM-generated","Human‑written","Mixed"]`.
  - `data/results/group_source_contingency.csv` (note the `data/results/` location) containing the contingency of provenance vs. source repository.
  - Repository‑level fallback: if a repository contains **zero LLM‑generated PRs**, log a warning and **exclude only that repository** from the binary comparison (FR‑010). Mixed‑signal PRs are labelled “Mixed” and excluded from the primary comparison (FR‑008).
  - Unit tests in `tests/test_classify.py` include `test_precedence_header_wins` to guarantee correct precedence.
  - **Verification**: pytest passes; `classified_prs.csv` contains ≥ 100 rows with non‑empty `provenance_label`; `group_source_contingency.csv` exists under `data/results/`.

- [ ] T003 [P] [US-001] **Compute reviewer‑effort metrics & create SSoT** – implement `code/compute_metrics.py` that reads `data/processed/classified_prs.csv` and writes `data/processed/processed_prs.csv` conforming to `contracts/processed_prs.schema.yaml`. The script:
  - Derives `lines_changed = additions + deletions`.
  - Computes `review_duration_seconds = merged_at – created_at`.
  - Computes `review_active_seconds` using `first_comment_timestamp` when present; otherwise falls back to `review_duration_seconds` and logs the limitation (FR‑015/FR‑016).
  - Calculates `comment_density = comment_count / lines_changed`.
  - Maps PR labels to `issue_severity` per FR‑012 and adds `creation_quarter`.
  - Pins the global NumPy/Pandas random seed (`np.random.seed(42)`) for deterministic downstream sampling (Constitution I).
  - **Verification**: pytest passes; output validates against `processed_prs.schema.yaml`; required columns present.

- [ ] T004 [P] [US-001] **Apply filters and IQR outlier removal** – implement `code/outlier_filter.py` that reads `data/processed/processed_prs.csv` and writes five filtered variants under `data/processed/`:
  - `filtered_prs_iqr1.0.csv` (IQR = 1.0),
  - `filtered_prs_iqr1.5.csv` (IQR = 1.5, primary),
  - `filtered_prs_iqr2.0.csv` (IQR = 2.0),
  - `filtered_prs_relaxed.csv` (comment‑count ≥ 0, IQR = 1.5),
  - `filtered_prs_base.csv` (baseline filter only: `lines_changed ≥ 5` and `comment_count ≥ 1`).
  - All files contain only PRs with `provenance_label` in {“LLM‑generated”, “Human‑written”} (Mixed excluded).
  - **Verification**: pytest passes; all CSV files exist with expected row counts.

## Phase 2 – Complete statistical study, validation, and robustness checks  

- [ ] T006 [P] [US-002] **Mixed‑effects modeling & collinearity diagnostics** – implement `code/mixed_effects.py` (called by T005) that fits a linear mixed‑effects model with `repo_name` as a random intercept and fixed effects `lines_changed`, `author_experience`, `repository_popularity`, and `creation_quarter`. It also computes VIF for `lines_changed` vs. `comment_density`; if any VIF > 5, the script reports a joint relationship note. Outputs model rows appended to `data/results/stats_summary.csv` and writes `data/results/vif_report.txt`.
  - **Verification**: script runs without error; additional rows appear in `stats_summary.csv`; `vif_report.txt` contains VIF values.

- [ ] T005 [P] [US-002] **Primary statistical comparison & power analysis** – implement `code/statistical_analysis.py` that reads `data/processed/filtered_prs_iqr1.5.csv` and performs:
  - A priori power analysis targeting medium effect (Cohen’s d = 0.5), α = 0.05, power = 0.8; records required n per group and whether the dataset meets it (FR‑019, SC‑007).
  - Shapiro‑Wilk normality per metric per group; automatically selects Mann‑Whitney U (non‑normal) or Welch’s t‑test (normal).
  - Effect‑size computation (rank‑biserial or Cohen’s d) regardless of significance (FR‑005).
  - Bonferroni correction across the three primary numeric metrics.
  - Chi‑square test with Cramér’s V for `issue_severity`.
  - Invokes `code/mixed_effects.py` for the mixed‑effects extension.
  - Writes all results to `data/results/stats_summary.csv` conforming to `contracts/statistical_results.schema.yaml`, including explicit null‑result statements when p ≥ α (FR‑011).
  - **Verification**: pytest passes; `stats_summary.csv` contains rows for each metric with required fields.

- [ ] T007 [P] [US-003] **Generate validation sample** – implement `code/validation_generate.py` that deterministically (fixed seed) samples 50 PRs from each provenance group in `classified_prs.csv` and writes `data/results/validation_sample.csv` (100 rows).
  - **Verification**: script exits 0; CSV has exactly 100 rows with a `group` column.

- [ ] T008 [P] [US-003] **Manual‑label validation (Cohen’s κ)** – implement `code/validation.py` that reads `data/results/validation_sample.csv` and a human‑provided `data/processed/manual_labels.csv`. Computes Cohen’s κ; if κ < 0.6, writes a warning and sets `significant = False` in `validation_report.md`; aborts pipeline with informative error if κ < 0.6 (SC‑001). Writes `data/results/validation_report.md`.
  - **Verification**: markdown produced; CI fails with clear error when κ < 0.6.

- [ ] T009 [P] [US-003] **Sensitivity analysis over outlier thresholds & comment filter** – implement `code/sensitivity.py` that re‑runs the primary statistical comparison (as in T005) for each IQR multiplier {1.0, 1.5, 2.0} and for the relaxed comment‑count filter (`comment_count ≥ 0`). Records for each run whether significance flips relative to the primary (IQR 1.5) result; any flip sets a “Low Robustness” flag (SC‑003). Writes `data/results/sensitivity_report.csv`.
  - **Verification**: script exits 0; CSV contains rows for all configurations and correct flags.

- [ ] T010 [P] [US-001] **Selection‑bias assessment for Mixed PRs** – implement `code/selection_bias.py` that compares the excluded “Mixed” group to the pure LLM‑generated and Human‑written groups on `comment_density`, `issue_severity`, and `severity_score` using Mann‑Whitney U (numeric) and chi‑square (categorical). Writes `data/results/selection_bias_report.csv`.
  - **Verification**: script runs; CSV exists and matches schema used for other result tables.

## Phase 3 – Reproducibility, resource safety, and final hand‑off  

- [ ] T011 [ ] [US-001] **Resource monitoring & limits** – add `code/resource_monitor.py` that wraps each pipeline script, logs peak RAM and CPU time to `data/results/resource_usage.csv`, and aborts with a clear message if RAM > 6 GB or cumulative CPU time > 6 h (SC‑005). The task is **not** marked parallel‑safe to avoid race conditions.
  - **Verification**: after a full run, `resource_usage.csv` contains entries for every script and all values are below limits.

- [ ] T012 [P] [US-001] **Pin exact dependencies** – create `code/requirements.txt` listing the exact versions used in the plan (e.g., `pandas==2.2.*`, `numpy==1.26.*`, `scipy==1.13.*`, `statsmodels==0.14.*`, `scikit-learn==1.5.*`, `datasets==2.19.*`, `httpx==0.27.*`, `pyyaml==6.0.*`, `matplotlib==3.8.*`, `psutil==5.9.*`).
  - **Verification**: file exists; `pip install -r code/requirements.txt` succeeds in a fresh environment.

- [ ] T013 [P] [US-002] **Generate figures and final report** – implement `code/report.py` that reads all result CSVs, creates box‑plots for `review_active_seconds` and `comment_density` by provenance, effect‑size summary tables, κ summary, and the group‑source contingency heatmap. Saves figures under `data/results/figures/`. Assembles `data/results/report.md` containing:
  - Methods and data sources overview.
  - All tables from `stats_summary.csv`, `sensitivity_report.csv`, `selection_bias_report.csv`, and `validation_report.md`.
  - Explicit null‑result statements wherever p ≥ α.
  - Effect‑size interpretation against small/medium/large benchmarks (SC‑004).
  - Limitations: power shortfall, selection bias from Mixed exclusion, misclassification attenuation, missing `first_comment_timestamp`, observational framing, robustness flags.
  - “Paper‑stage hand‑off” section listing artifact paths.
  - **Verification**: script exits 0; figures exist; report includes required sections and references every result artifact.

- [ ] T014 [P] [US-001] **Document and verify the full workflow** – update `specs/001-evaluating-the-impact-of-code-generation/quickstart.md` with the exact sequential commands (as listed below) and confirm that a clean CI run produces all artifacts and passes all pytest suites within resource limits.
  ```bash
  python code/download_data.py
  python code/classify_provenance.py
  python code/compute_metrics.py
  python code/outlier_filter.py
  python code/mixed_effects.py
  python code/statistical_analysis.py
  python code/validation_generate.py
  python code/validation.py   # requires manual labels
  python code/sensitivity.py
  python code/selection_bias.py
  python code/resource_monitor.py
  python code/report.py
  ```
  - **Verification**: a fresh runner completes the chain, all pytest tests pass, all result files are generated, and `report.md` lists all artifact paths.
