# Tasks: Predicting the Impact of Residual Stress on Fatigue Life Using Public Datasets

**Inputs**: `spec.md`, `plan.md`, original research idea, existing artifacts, and reviewer feedback.

This checklist implements the smallest complete study satisfying FR-001–FR-014 and SC-001–SC-005 under the plan's verified scope: **no verified public dataset provides measured residual stress with fatigue life, process parameters, and material class**, so the study runs on the repo-bundled pipeline-verification CSV and the deterministic synthetic validation dataset (seed 42), with all measured-stress conclusions labeled "synthetic validation — pipeline validation only, not an external scientific claim". NIST/UCI/OpenML repository ingestion is NOT tasked (verified unavailable; **spec gap flagged for kickback**: spec.md FR-001, US-1, and Assumptions still assert these repositories are suitable and must be revised). Prior failed attempts to download from those repositories are corrected here: no fabricated or fallback data sources are permitted — the loader must fail loudly if the bundled real inputs are missing.

**Upstream conflicts flagged for kickback (not resolvable by editing tasks.md)**:
1. FR-001/US-1/Assumptions vs plan/tasks scope (repository ingestion unmet) — spec must be revised.
2. Constitution Principle VII ("paired t-tests on absolute errors") vs FR-008 (Wilcoxon signed-rank) — T006 reconciles operationally by reporting BOTH tests, but the constitution/spec wording conflict needs upstream resolution.
3. FR-003/FR-004 "measured or estimated" Set B wording vs the measured-only balanced subset used for paired tests — T004 adds a proxy-augmented Set B-full variant; the spec wording should be clarified.
4. FR-005/US-2 "[deferred]" split placeholder — tasks adopt 80/20; the spec placeholder should be resolved to 80/20.
5. FR-013 does not define the 50–63 under-power band that plan Phase 7 and T008 implement — spec should document it.
6. plan.md Technical Context dependency list omits `jsonschema` (needed by T002's schema validation); T001 now authors `code/requirements.txt` including the `jsonschema` pin, but plan.md's pinned dependency list must be updated upstream to match.

---

## Phase 1 – Setup and first end-to-end analysis

- [ ] T001 [P] [US1] **Establish runnable environment, dependency pinning, quick-start, and input provenance** (redo: prior `scripts/env_check.sh` and `scripts/run_pipeline.sh` exited 1)
  *Files*: `quickstart.md`, `code/src/env_check.py`, `code/requirements.txt`
  *Actions*:
  – Verify Python 3.11 and required packages (pandas 2.2.*, numpy 1.26.*, scikit-learn 1.5.*, torch 2.3.* CPU-only, statsmodels 0.14.*, pyyaml 6.0.*, pytest 8.2.*, **jsonschema 4.2x**) import cleanly; fail fast with a clear message on any missing dependency or insufficient disk (< 12 GB free). Do NOT attempt to install packages inside the script — the platform provides the common scientific stack; report missing ones and exit non-zero.
  – **Author `code/requirements.txt`** with the full pinned dependency list, including `jsonschema==4.23.*` — this file is the single source for the isolated-venv execution model (constitution Reproducibility Requirements) and closes the dependency gap that would otherwise make T002's `jsonschema`-based schema validation fail at import. (plan.md's Technical Context dependency list omits `jsonschema`; flagged for kickback — upstream plan must add it.)
  – Document in `quickstart.md` the single end-to-end command and the exact location of the two real inputs: `data/raw/pipeline_verification.csv` (bundled, with known unit inconsistencies and missing values) and `data/raw/synthetic_fatigue.csv` (deterministic synthetic validation dataset generated from seed 42 per research.md).
  – Record SHA-256 checksums of both raw inputs to `data/raw/checksums.json`; the loader in T002 must verify these and RAISE on mismatch — never fall back to generated or placeholder data.
  *Verification*: `pytest code/tests/test_env_check.py` asserts exit code 0, that `jsonschema` is importable, that `code/requirements.txt` exists and pins `jsonschema==4.23.*` (plus all other required packages), and that `checksums.json` matches recomputed hashes of the two bundled files.

- [ ] T002 [P] [US1] **Implement data ingestion (CSV and nested-JSON parsing), harmonization, and proxy computation** (redo: prior `code/ingest/ingest.py` exited 1; remove the failed NIST/UCI/OpenML download logic entirely)
  *File*: `code/src/ingest.py`
  *Actions*:
  – Load ONLY the two bundled real inputs (`data/raw/pipeline_verification.csv`, `data/raw/synthetic_fatigue.csv`); on read failure, raise — no synthetic fallback, no guessed URLs (FR-001 partial: schema unification, CSV/JSON parsing, unit standardization, imputation; repository ingestion is a documented spec gap flagged for kickback).
  – Parse CSV and **nested JSON structures** (OpenML-style nested feature dicts, per US-1 scenario 2 / FR-001) into the flat unified schema of `specs/001-predicting-the-impact-of-residual-stress/contracts/dataset_schema.yaml`. The JSON parsing path is a real, tested deliverable: `code/tests/fixtures/openml_style_nested.json` is a small hand-authored fixture with nested feature structures, and `ingest.py` exposes a `parse_json_records()` function that flattens it into the unified schema.
  – Compute per-row SHA-256 `checksum`; convert psi → MPa (`1 psi = 0.00689476 MPa`); median-impute missing numeric values and record original missingness in `data/processed/missing_flags.json` (FR-002).
  – Compute the proxy `σ_res = k·heat_input·cooling_rate` (k=0.8 steel, k=0.6 aluminum) for **ALL rows** into `residual_stress_proxy`; set `is_proxy=True` only where it replaces a missing measured value; clamp negatives to 0.01 MPa and log adjustment counts (FR-003, edge case).
  – Write `data/processed/unified_fatigue.csv`; validate against `contracts/dataset_schema.yaml` with `jsonschema` (pinned in `code/requirements.txt` from T001) and abort on failure.
  *Verification*: `pytest code/tests/test_ingest.py` runs against (i) a small fixture derived from the bundled verification CSV and (ii) the nested-JSON fixture `openml_style_nested.json`, asserting for both: checksum column present, all stress values in MPa, `residual_stress_proxy` present for every row with correct `is_proxy` flags, and schema validation passes. The JSON fixture exercises the full nested→flat parsing path.

- [ ] T003 [US1] **Proxy–measured agreement check (FR-014), phase instrumentation, and early end-to-end run** — depends on T002
  *Files*: `code/src/proxy_agreement.py`, `code/src/run_e2e.py`, `code/src/timing.py`
  *Actions*:
  – On rows where both `residual_stress_measured` and `residual_stress_proxy` exist, compute Pearson's r and R² between them; write `data/results/proxy_agreement.csv` with a mandatory circularity caveat column/notes (the proxy is a deterministic function of the same process parameters used as predictors — descriptive agreement only, NOT independent validation).
  – **Instrumentation mechanism (feeds T010/T011)**: `code/src/timing.py` provides a `phase_timer` context manager (wall-clock via `time.perf_counter`) and a peak-memory sampler (RSS via `psutil`, sampled at 1 Hz in a background thread while a phase runs). `run_e2e.py` (and the later phase scripts) wrap each pipeline phase with `phase_timer` and append rows to `data/results/runtime_summary.csv` (`phase`, `wall_clock_s`, `peak_rss_mb`).
  – `run_e2e.py` executes ingest → proxy agreement on the full bundled inputs and writes a small real summary `data/results/e2e_summary.json` (row counts, % proxy rows, per-material counts, agreement metrics).
  *Verification*: `pytest code/tests/test_e2e.py` asserts `data/results/e2e_summary.json` exists, contains finite agreement metrics when any both-values rows exist, that measured-stress row counts are reported (feeding the FR-013 eligibility check in T008), and that `runtime_summary.csv` contains at least one row with finite `wall_clock_s` and `peak_rss_mb` per executed phase.

## Phase 2 – Feature sets, model training, and predictive comparison

- [ ] T004 [US2] **Construct feature sets A, B (balanced and full variants), and C** — depends on T002
  *File*: `code/src/build_features.py`
  *Actions*:
  – Read `data/processed/unified_fatigue.csv`.
  – **Feature Set A (process only)** and **Feature Set B (process + measured residual stress)** built on the **identical balanced subset** of measured-stress rows (`is_proxy=False`) so paired A-vs-B comparisons isolate the stress feature with equal sample sizes.
  – **Feature Set B-full (proxy-augmented)**: per FR-003/FR-004's "measured **or** estimated stress" wording, also construct Set B-full = process + stress (measured where available, proxy otherwise) on the **full dataset**. B-full is reported descriptively with explicit sample-size disclosure and is NEVER compared head-to-head with A/B via paired tests (differing row sets). The balanced measured-only Set B remains the basis for all paired statistical tests (FR-012).
  – **Feature Set C** (process + material properties + estimated stress proxy) built on the **full dataset**; C is likewise reported descriptively only, with explicit sample-size disclosure (FR-003, FR-012).
  – Standardize numeric features (zero mean / unit variance) with fitted scalers persisted for reuse.
  *Verification*: `pytest code/tests/test_features.py` asserts A and B row sets are identical, B contains no `is_proxy=True` rows, B-full and C span the full dataset, and B-full uses measured stress on measured rows and proxy on proxy rows.

- [ ] T005 [US2] **Train RF, GBM, and shallow NN with 5-fold CV, hyperparameter search, and per-model timing** — depends on T004
  *File*: `code/src/train.py`
  *Actions*:
  – For each algorithm and each feature set (A, B, B-full, C), evaluate a grid of 10 hyperparameter combos via 5-fold CV stratified by `material_class` (FR-004, FR-005). The exact grids (defined in `code/src/hparam_grids.py`, seed-pinned):
    – **RandomForestRegressor**: `n_estimators` ∈ {100, 200}, `max_depth` ∈ {None, 10, 20}, `min_samples_leaf` ∈ {1, 5} — the 10 combinations enumerated as the Cartesian product's first 10 in a fixed order.
    – **GradientBoostingRegressor**: `n_estimators` ∈ {100, 200}, `learning_rate` ∈ {0.05, 0.1}, `max_depth` ∈ {2, 3, 5} — first 10 combinations in fixed order.
    – **Shallow NN (PyTorch, 1 hidden layer)**: `hidden_units` ∈ {16, 32, 64}, `learning_rate` ∈ {0.001, 0.01}, `batch_size` ∈ {32, 64}, plus L2 weight decay ∈ {0, 1e-4} — first 10 combinations in fixed order; ≤500 epochs with early stopping (patience 20).
  – Fixed `SEED=42` for splits, initialization, and shuffling (FR-010).
  – Record per-fold MAPE and R²; select lowest mean CV-MAPE; retrain on the training split; persist best models under `code/models/`.
  – Split the balanced subset into stratified train (80%) / held-out test (20%) with seed 42 (the 80/20 ratio the spec's "[deferred]" placeholder should adopt — flagged for kickback); compute test MAPE and R² per model overall and per material class; write `data/results/model_performance.csv`.
  – **Per-model timing (US-2 scenario 2)**: record per-model wall-clock training time (via `code/src/timing.py`) as a `train_time_s` column in `model_performance.csv`; assert the shallow-NN fits complete within **60 minutes** each and raise a clear error if exceeded.
  *Verification*: `pytest code/tests/test_train.py` runs on a truncated input and asserts model files are created, CV-MAPE values are finite floats, `train_time_s` is present and finite, and NN training times are ≤ 3600 s.

- [ ] T006 [P] [US2] [US3] **Statistical comparison of Set A vs Set B: Wilcoxon signed-rank (FR-008) plus paired t-test (Constitution VII)** — depends on T005
  *File*: `code/src/wilcoxon_compare.py`
  *Actions*:
  – Compute absolute errors for Model A vs Model B on the **same measured-stress test rows**; run the **Wilcoxon signed-rank test** per algorithm family as the primary non-parametric test (FR-008).
  – **Constitution VII reconciliation**: ALSO run a **paired t-test on absolute errors** per algorithm family and report it alongside the Wilcoxon result, so the constitution's "paired t-tests on absolute errors" requirement is demonstrably satisfied. Both tests are reported; the Wilcoxon result (Bonferroni-corrected across the three families, α = 0.05/3) is primary. The residual wording conflict between FR-008 and Constitution VII is flagged for upstream kickback; this dual reporting does not weaken either constraint.
  – Report the ≥10% MAPE-improvement criterion alongside the test results: a model is reported as meaningfully improved only if test MAPE is ≥10% lower than baseline AND the corrected Wilcoxon p < 0.05; the pipeline must NOT exit non-zero merely because the empirical improvement is below 10% — it records the honest outcome (the threshold is a reporting criterion, not a fabricated guarantee).
  – Write `data/results/wilcoxon_results.csv` with `statistic`, `p_uncorrected`, `p_corrected`, `ttest_statistic`, `ttest_p`, `mape_reduction_pct`, `meets_threshold`.
  *Verification*: `pytest code/tests/test_wilcoxon.py` asserts required columns (including the paired-t-test columns), that p-values are in [0,1]; a fixture with known paired errors recovers the expected significance decision for both tests.

- [ ] T007 [P] [US3] **Cross-material transfer evaluation with permutation testing (FR-009, FR-011)** — depends on T005
  *File*: `code/src/cross_material.py`
  *Actions*:
  – Train on steel-only, test on aluminum-only, and vice versa, for each algorithm/feature set; compute ΔMAPE relative to within-material baselines.
  – Assess significance with a permutation test (10,000 permutations, α = 0.05, Holm-Bonferroni across material pairs).
  – Write `data/results/cross_material.csv` with `train_material`, `test_material`, `mape_same`, `mape_other`, `delta_mape`, `perm_p`, `p_corrected`.
  *Verification*: `pytest code/tests/test_cross_material.py` asserts both directions present, `delta_mape` finite, permutation p-values in [0,1].

## Phase 3 – Conditional mediation analysis

- [ ] T008 [US3] **A-priori power analysis, eligibility gate, and proxy_dependent branch (FR-013)** — depends on T002
  *File*: `code/src/power_analysis.py`
  *Actions*:
  – Conduct the a-priori power analysis for mediation (medium effect f² = 0.15, α = 0.05, power = 0.80) and document the required minimum sample size (≈45); adopt the operational ≥50 measured-stress-row threshold. (The 50–63 under-power band implemented below is a conservative caveat-widening, not a weakening; spec FR-013 does not yet document it — flagged for kickback.)
  – Count measured-stress rows (`is_proxy=False`) overall and per material class; write `data/results/mediation_eligibility.json` with `n_measured`, `eligible` (≥50), `under_power_band` (50–63), `skip_mediation` (<50), and **`proxy_dependent`** (true iff `n_measured == 0`, per the spec edge case "Missing measured stress for all samples": the final report must set `proxy_dependent=True` and omit mediation).
  *Verification*: `pytest code/tests/test_power.py` asserts the eligibility JSON matches recomputed counts from `unified_fatigue.csv`, and that a zero-measured-row fixture yields `proxy_dependent=true` with `skip_mediation=true`.

- [ ] T009 [US3] **Bootstrap mediation analysis on measured-stress subset (FR-006, FR-007, FR-012)** — depends on T008
  *File*: `code/src/boot_mediation.py`
  *Actions*:
  – Proceed only if `eligible=true` from T008; if in the 50–63 band, flag estimates as potentially under-powered; if <50 or `proxy_dependent=true`, log a warning, write a skip row, and do not run.
  – Exclude all proxy-only rows from mediation (FR-012, prevents circularity).
  – **Exact model specification** (exposure variable named explicitly):
    – Exposure: a single composite **process-intensity index** `P = z(heat_input) · z(cooling_rate)` (z = standardized on the measured-stress subset), so the a-path exposure is distinct from the covariates and no self-contradictory control structure arises.
    – **a-path**: `residual_stress_measured ~ P + elastic_modulus + yield_strength + C(material_class)` (OLS).
    – **b-path**: `fatigue_life_cycles ~ residual_stress_measured + P + elastic_modulus + yield_strength + C(material_class)` (OLS).
    – Indirect effect = a · b; direct effect = c′ from the b-path coefficient on P.
  – Compute VIF for each predictor; flag any >5.
  – Bootstrap mediation with 10,000 resamples (seed 42); report indirect effect, 95% CI, proportion mediated; Holm-Bonferroni across material classes.
  – Mandatory framing: all indirect effects labeled "associational — no causal identification" and, because inputs are synthetic, additionally "pipeline validation only — synthetic data, not an external scientific claim".
  – Write `data/results/mediation_summary.csv` and PNG effect-size plots under `figures/`.
  *Verification*: `pytest code/tests/test_mediation.py` verifies CI bounds non-null when run, corrected p ≤ 1, labels present, the a-path/b-path formulas match the specification above, and that a <50-row fixture and a zero-measured fixture each produce the skip row.

## Phase 4 – Reporting, reproducibility, and handoff

- [ ] T010 [US3] **Generate results report and figures** — depends on T003, T005, T006, T007, T008, T009
  *File*: `code/src/generate_report.py`
  *Actions*:
  – Read all `data/results/*.csv` artifacts (model performance, Wilcoxon, cross-material, proxy agreement, mediation summary/eligibility).
  – Produce PNG figures: (i) MAPE per feature set (including B-full) and algorithm, (ii) mediation indirect-effect forest plot (if executed), (iii) cross-material ΔMAPE summary; save under `figures/`.
  – Write `paper/results_report.md` linking each table and figure, interpreting SC-001–SC-004, including the proxy circularity caveat, the associational framing, the synthetic-data scope limitation, the documented FR-001 repository-ingestion gap, any skipped/under-powered mediation, and — when `mediation_eligibility.json` has `proxy_dependent=true` — an explicit `proxy_dependent: true` statement in the report body.
  – Consolidate `data/results/runtime_summary.csv` (wall-clock, peak memory per phase, accumulated by the `timing.py` instrumentation from T003 onward).
  *Verification*: `pytest code/tests/test_report.py` asserts the report exists, references ≥3 figures, every referenced artifact path exists, and that a `proxy_dependent=true` eligibility fixture produces the corresponding report statement.

- [ ] T011 [US2] [US1] **Reproducibility verification and end-to-end re-run** — depends on T010
  *File*: `code/src/repro_check.py`
  *Actions*:
  – Verify `SEED=42` is fixed across splits, model init, and bootstrap; recompute raw-file checksums and compare to `data/raw/checksums.json` and the `checksum` column.
  – Assert wall-clock ≤ 6 h and peak memory ≤ 7 GB from `runtime_summary.csv` (SC-005), AND that every shallow-NN `train_time_s` in `model_performance.csv` is ≤ 60 minutes (US-2 scenario 2).
  – Re-run the documented workflow from `quickstart.md` end-to-end and confirm outputs are byte-stable for seeded stages.
  – Write `data/results/reproducibility_report.txt` with per-check pass/fail.
  *Verification*: `pytest code/tests/test_repro.py` asserts the report shows all checks passed, including the per-model NN 60-minute check.

- [ ] T012 [US3] **Paper-stage handoff documentation** — depends on T011
  *File*: `paper/paper_handoff.md`
  *Actions*:
  – Enumerate exact artifact locations for the manuscript stage (`data/results/model_performance.csv`, `wilcoxon_results.csv`, `cross_material.csv`, `proxy_agreement.csv`, `mediation_summary.csv`, `mediation_eligibility.json`, `figures/`, `paper/results_report.md`, `data/results/reproducibility_report.txt`).
  – State the scope limitation for the paper stage: measured-stress results are synthetic validation only; the research question cannot be answered with real measured residual stress from open data; FR-001's repository-ingestion requirement remains unmet pending a verified real source.
  – Preserve manuscript requirements (layout, PDF compilation, publication) as handoff items — not research tasks.
  *Verification*: `pytest code/tests/test_handoff.py` asserts the file exists and every listed artifact path resolves.

---

## Dependencies and requirement coverage

| Requirement | Satisfying Task(s) |
|---|---|
| FR-001 (partial: CSV + nested-JSON parsing, unification, units; repository ingestion documented as spec gap) | T002 |
| FR-002 (median imputation, MPa standardization) | T002 |
| FR-003 (proxy for all rows, flagging, clamping; Set B "measured or estimated" via B-full) | T002, T004 |
| FR-004 (feature sets A/B/B-full/C × three algorithms) | T005 |
| FR-005 (5-fold CV, held-out 80/20 test) | T005 |
| FR-006/FR-007 (bootstrap mediation, CI, proportion mediated) | T009 |
| FR-008 (Wilcoxon signed-rank on measured subset) + Constitution VII (paired t-test) | T006 |
| FR-009 (material-class stratification) | T005, T007, T009 |
| FR-010 (fixed seeds) | T001, T005, T009, T011 |
| FR-011 (cross-material transfer) | T007 |
| FR-012 (proxy rows excluded from mediation, included in B-full/C) | T004, T009 |
| FR-013 (a-priori power analysis, ≥50-row gate, proxy_dependent edge case) | T008 |
| FR-014 (proxy–measured agreement with circularity caveat) | T003 |
| SC-001–SC-005 | T005–T011 |
| US-2 scenario 2 (per-model NN ≤ 60 min) | T005, T011 |
| Constitution VII (≥10% MAPE improvement, paired t-test on absolute errors) | T006 |
| Isolated-venv dependency completeness (incl. `jsonschema` for T002) | T001 |

Execution order (matches [P] tags): T001 ∥ T002 → T003 → T004 → T005 → T006 ∥ T007 → T008 → T009 → T010 → T011 → T012. Only T001/T002 (mutually independent) and the T006/T007 pair are parallel-safe; all other tasks have hard producer-before-consumer dependencies and are tagged sequentially. T001 and T002 are redone from the rejected prior iteration: the failed NIST/UCI/OpenML download logic is removed in favor of the verified bundled inputs, with no synthetic fallback permitted anywhere in the loader. T001 additionally authors the pinned `code/requirements.txt` (including `jsonschema==4.23.*`) so the isolated-venv execution model required by the constitution can run T002's schema validation.