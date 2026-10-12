# Tasks: Predicting Catalytic Activity from Electronic Structure and Reaction Path Features

**Inputs**: `specs/001-predicting-catalytic-activity/spec.md`, `plan.md`, data-model.md, contracts/, original idea, prior verification feedback.
**Scope**: Full pipeline implementing FR-001 through FR-007. Includes OC20, Materials Project (MP) bulk descriptors, and the 2025 CO₂ hydrogenation study (with OC20-experimental fallback). Verified completed work (T004–T007, T011, T013a, T015, T016a/b, T012a, T019, T024–T030, T033–T041, T042a–c, T043a–c, T044–T046, T049, T039a/b) is preserved as completed below; rejected tasks are consolidated into the revised T101–T109.

## Phase 1: Setup and first end-to-end analysis

**Goal**: A runnable pipeline that acquires real data, derives descriptors, and produces a contract-valid aligned dataset.

- [ ] T101 [US1] **Repair project skeleton and package init**. Use `llmxive_toolkit.paths` to create `data/raw/`, `data/processed/`, `outputs/`, `code/`, `code/utils/`, `code/models/`, and `tests/` (with `contract/`, `integration/`, `unit/` subdirs) on demand. Add empty `__init__.py` files to `code/`, `code/utils/`, `code/models/`. Add `.ruff.toml` with rules `E, F, W, I`. **Verification**: `ls code/__init__.py` succeeds; `ruff check --config=.ruff.toml .` runs without config errors; `tests/integration/test_skeleton.py::test_dirs_exist` asserts `os.path.isdir` for each directory and exits nonzero on failure. <!-- FAILED-IN-EXECUTION: code/run_ruff_check.py exit=1 -->
- [ ] T102 [US1] **Acquire real OC20, MP, and 2025 study data**. Rewrite `code/download_data.py` to: (a) fetch `Open-Catalyst/oc20-experimental` via `datasets.load_dataset(..., streaming=True)` and save a fixed-seed stratified sample to `data/raw/oc20_sample.parquet`; (b) fetch bulk descriptors via `mp-api` (using API key in env) to `data/raw/mp_descriptors.json`; (c) fetch the 2025 CO₂ hydrogenation study dataset (falling back to OC20-experimental if unavailable) to `data/raw/experimental_tof.csv`. The loader MUST raise on fetch failure—no synthetic fallback. Record the HF dataset revision hash. **Verification**: `data/raw/oc20_sample.parquet`, `data/raw/mp_descriptors.json`, and `data/raw/experimental_tof.csv` exist and are non-empty; `tests/integration/test_download.py` asserts row count > 0. <!-- FAILED: unspecified --> <!-- FAILED-IN-EXECUTION: code/download_data.py exit=1 -->
- [ ] T103 [US1] **Derive descriptors and build the unified DataFrame**. In `code/preprocess.py` (utilizing `code/extract_descriptors.py` logic), (a) derive `d_band_center`, `p_band_center`, and `bader_charges` from raw structures/MP data; (b) align entries using **exact string matching** on `composition`, `surface_facet`, and `synthesis_condition` per FR-002; (c) write `data/processed/unified_dataset.parquet` and `outputs/alignment_metrics.json` (SC-002). **Verification**: `outputs/alignment_metrics.json` exists and contains `alignment_rate`; `data/processed/unified_dataset.parquet` has $\ge 500$ matched entries (per US-1) and contains all required descriptor columns.
- [ ] T104 [US1] **Stoichiometry vocabulary, k-NN imputation, and final aligned dataset**. Extend `code/preprocess.py` to: (a) build global element vocabulary and write `data/processed/stoich_vocab.json`; (b) run k=5 stoichiometry-space imputation (target `experimental_tof` excluded), flagging entries with <5 neighbors; (c) apply scaling to zero mean/unit variance; (d) write `data/processed/aligned_dataset.csv` conforming strictly to `specs/.../contracts/aligned_dataset.schema.yaml` (primary key: `catalyst_id`, exclusion flag: `excluded_from_training`) with no NaN in `experimental_tof`. **Verification**: `tests/unit/test_preprocess.py` asserts no NaN in target; `data/processed/aligned_dataset.csv` validates against `aligned_dataset.schema.yaml`.

**Checkpoint**: The documented command (`python -m code.download_data && python -m code.preprocess`) executes on real data and `aligned_dataset.csv` is contract-valid.

## Phase 2: Complete the study and validate its evidence

- [ ] T105 [US2] **Re-validate training pipeline against the rebuilt dataset**. Re-run `code/train.py` (T024–T030: stratified split, linear baseline, XGBoost k-fold cross-validated grid search per FR-004, seed 42, Shapiro-Wilk $\to$ paired t-test/Wilcoxon per FR-005). Save the best model to `code/models/best_xgboost.json` and write `outputs/metrics.json` (schema per `contracts/metrics.schema.yaml`). **Verification**: `outputs/metrics.json` exists and validates against the metrics contract; `metrics.json['alignment_rate']` matches `alignment_metrics.json`. <!-- FAILED: unspecified -->
- [ ] T107 [US2] **Sensitivity and runtime checks**. Add `tests/integration/test_sensitivity.py` verifying: (a) seed stability: re-running `code/train.py` with seed 42 reproduces identical test-set R²/MAE; (b) edge cases (missing-neighbor exclusion, non-normal error distributions) pass; (c) measure full pipeline duration and write `outputs/feasibility_verification.json` (SC-004). **Verification**: `pytest tests/ -q` passes; `outputs/feasibility_verification.json` contains `duration_seconds` and `feasibility_status`, where `duration_seconds <= 21600` (6 hours).
- [ ] T106 [US3] **Re-run SHAP and SC-003 verification**. Execute `code/interpret.py` (T033–T037: `shap.TreeExplainer` on `code/models/best_xgboost.json`, mean-absolute-SHAP ranking, `outputs/feature_importance.png` top-5 bar plot). Train a reduced top-5 model using the same grid and calculate the R² ratio. **Verification**: `outputs/feature_importance.png` is regenerated; `outputs/sc003_verification.json` contains `ratio` and `SC-003_status`, where `ratio >= 0.50` is required for a PASS.

## Phase 3: Reproducible results and paper handoff

- [ ] T108 [US3] **Regenerate the final report from actual artifacts**. Re-run `code/report.py` (T040/T039/T049) so `outputs/final_report.md` reflects: Pearson R, MAE, p-value/test type, top-5 SHAP descriptors, quantitative SC-003 result, and the Nørskov comparison table. **Verification**: Every number in the report traces to `outputs/metrics.json` or `outputs/sc003_verification.json`; `code/data/norskov_2005_descriptors.json` exists and is used for the comparison. <!-- FAILED-IN-EXECUTION: code/report.py exit=1 -->
- [ ] T109 [US1] **Document the runnable workflow and paper-stage handoff**. Update `quickstart.md` with exact commands (`python -m code.download_data`, `python -m code.preprocess`, `python -m code.train`, `python -m code.interpret`, `python -m code.report`) and the path to `tests/`. Confirm a fresh clone reproduces all artifacts. Record the handoff: figures (`outputs/feature_importance.png`), result tables (`outputs/metrics.json`, `outputs/sc003_verification.json`), and `outputs/final_report.md`. **Verification**: `pytest tests/` passes on a fresh environment; all final outputs are generated.

## Completed work preserved (do not redo)

The following previously verified tasks remain satisfied and their artifacts are reused: config/logging/hashing/validation infrastructure (T004–T007), checksum verification (T011), OC20 parsing (T013a), target retrieval (T015), stoichiometry features and distance (T016a/b), FR-002 alignment logic (T012a), scaling (T019), train/test split and both models with the fixed grid and statistical testing (T024–T030), SHAP analysis, reduced model, SC-003 logic and unit tests (T033–T037, T041), report generation and Nørskov comparison (T039/T040/T049), runtime verification (T042a–c), lint/cleanup/README/quickstart (T043a–c, T044, T046), and the Nørskov reference list (T039a).

## Dependencies and requirement coverage

- **FR-001** (data acquisition): T102 (OC20, MP, 2025 study).
- **FR-002** (alignment): T103 (exact string match).
- **FR-003** (k-NN imputation, scaling): T104 (k=5, scaled).
- **FR-004** (XGBoost grid search): T105 (k-fold CV).
- **FR-005** (baseline + statistical test): T105 (Shapiro-Wilk $\to$ t-test/Wilcoxon).
- **FR-006** (SHAP ranking + plot): T106.
- **FR-007** (final report with Nørskov comparison): T108.
- **SC-002** (alignment rate): T103. **SC-003** (reduced model ratio): T106. **SC-004** (runtime): T107. **SC-001/SC-005** (performance + significance): T105.
- Execution order: T101 $\to$ T102 $\to$ T103 $\to$ T104 $\to$ T105 $\to$ T107 $\to$ T106 $\to$ T108 $\to$ T109.

## Revision behavior notes

- Scope restored to include MP and 2025 study per FR-001.
- Alignment restored to exact matching per FR-002.
- Descriptor extraction integrated into T103 to satisfy `aligned_dataset.schema.yaml`.
- T104 standardized on `catalyst_id` and `excluded_from_training` to resolve contract conflicts.
- Training reverted to k-fold CV grid search per FR-004.
- Test paths unified to root `tests/` and verification fixed to avoid stdlib shadowing.
- Runtime enforcement added to T107 (6-hour limit).
- US2 tasks (T105, T107) and US3 tasks (T106, T108) grouped contiguously.