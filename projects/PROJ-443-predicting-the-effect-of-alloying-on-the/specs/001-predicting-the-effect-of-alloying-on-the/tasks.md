# Tasks: Predicting the Effect of Alloying on the Elastic Modulus of High-Entropy Alloys

**Inputs**: Active `spec.md`, `plan.md`, `data-model.md`, `contracts/`, prior task list, reviewer rejection feedback.

## Phase 1: Setup and first end‑to‑end data pipeline

- [ ] T001 [P] Establish the project scaffold and dependencies: create top‑level `code/`, `data/raw/`, `data/processed/`, `results/`, `scripts/`, and `code/requirements.txt` pinning `pandas`, `numpy`, `scikit-learn`, `scipy`, `pyyaml`, `requests`, `shap`, `pytest`, **`mp-api`**, **`compositional`**, **`matplotlib`**. Copy/keep the verified seed‑management module at `code/utils/seeds.py` and document the entry command (`python -m code.main --stage all`) in `specs/001-predict-elastic-modulus/quickstart.md`.
  - Verification: all listed directories exist, `pip install -r code/requirements.txt` succeeds, and `pytest code/tests/` collects the carried‑forward unit tests (`test_normalization.py`, `test_coda.py`, `test_bootstrap.py`, `test_fdr.py`, etc.).

- [ ] T002 [US1] Implement real data ingestion with provenance in `code/data/fetch.py` and `code/data/metadata.py` (FR‑001, FR‑009): retrieve HEA composition and elastic‑constant records from the Materials Project API (`mp_api`) and OQMD, applying the ≥5‑principal‑elements filter. Use retry logic (max 3 attempts) and raise on failure (no synthetic fallback). Write raw dumps (checksummed, SHA‑256) to **`data/raw/`** and generate **`data/source_metadata.yaml`** per `metadata.schema.yaml`. Include `check_and_update_provenance()` to re‑download when checksum differs. <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  - Verification: `python -m code.main --stage fetch` exits 0; `data/raw/` contains non‑empty real API output; `data/source_metadata.yaml` validates against `contracts/metadata.schema.yaml`; unit test `code/tests/unit/test_fetch.py` asserts proper raise on unreachable endpoint.

- [ ] T003 [US1] Implement cleaning, normalization, descriptor/feature engineering in `code/data/clean.py` and `code/features/descriptors.py` (FR‑002, US‑1 Scenarios 2‑4): normalize compositions to sum 1.0 (log adjustments), drop samples missing elastic constants, compute standard descriptors (mixing entropy, VEC, atomic‑radius variance, electronegativity variance) **and** the three Miedema‑derived features (`mixing_enthalpy_miedema`, `atomic_radius_variance_miedema`, `electronegativity_variance_miedema`). Apply ILR transformation via the `compositional` library. Implement `code/features/exclusion.py` to conditionally drop `$MIEDEMA_FEATURES$` when the target is a Residual Modulus, with a pre‑training assertion that halts on leakage. Output the processed dataset to **`data/processed/hea_features.csv`** (and Parquet) conforming to `contracts/dataset.schema.yaml` and `contracts/hea_sample.schema.yaml`, with no NaNs.
  - Verification: `python -m code.main --stage features` exits 0; CSV exists with all descriptor columns; `code/tests/unit/test_exclusion.py` asserts the exclusion assertion fires when Miedema features appear in a Residual‑target matrix; existing ILR/normalization tests pass.

- [ ] T004 [US1] Run the first end‑to‑end data pipeline checkpoint: execute fetch → clean → feature stages on the real dataset, producing `data/processed/hea_features.csv`. If the retrieved sample count is **< 500**, generate an **‘Underpowered Study Report’** (`results/underpowered_report.md`) quantifying power deficit and confidence‑interval widening, and flag reduced power in downstream outputs (spec Edge‑Case 1). Connect `code/main.py` so `--stage all` runs these steps and writes the report when needed.
  - Verification: `python -m code.main --stage all` completes within the 6‑hour CPU budget; `results/underpowered_report.md` is emitted only when count < 500; otherwise pipeline proceeds normally.

## Phase 2: Complete the study and validate its evidence

- [ ] T005 [US2] Implement model training for **Residual Bulk Modulus** in `code/models/train_residual_bulk.py` (FR‑004): Random Forest, Gradient Boosting, ElasticNet (scikit‑learn, CPU‑only, `n_jobs=2`, seeded). Use grouped train/val/test split (70/15/15) by `element_set` via `code/models/split.py`. Write model artifacts `results/models/rf_bulk.pkl`, `results/models/gb_bulk.pkl`, `results/models/en_bulk.pkl` and test‑set predictions `results/predictions/rf_bulk.csv`, etc.
  - Verification: `python -m code.main --stage train_residual_bulk` exits 0 and creates the listed files.

- [ ] T006 [US2] Implement statistical evaluation in `code/models/evaluate.py` (FR‑005, FR‑008, SC‑002, SC‑003, SC‑005): compute R², RMSE, MAE on held‑out test set; perform **grouped bootstrap** (1000 iters, grouping by `element_set`) for 95 % CI of R² with fallback warning for < 10 groups; run **permutation test** (1000 iters) for R² > 0, output `results/null_hypothesis.yaml`; apply Benjamini–Hochberg FDR correction to pairwise model p‑values; calculate Pearson |r| between residuals and `$MIEDEMA_FEATURES$`, log warning if |r| > 0.1; check train‑test performance gap CI and halt if CI excludes zero. Write **`results/metrics.yaml`** conforming to `contracts/output.schema.yaml` (see T018 for schema alignment) and include the mandatory disclaimer string.
  - Verification: `results/metrics.yaml` exists, validates against `contracts/output.schema.yaml`, contains entries for all three models, includes CI bounds, permutation p‑value, FDR‑corrected values, and the disclaimer.

- [ ] T007 [US3] Implement interpretability and sensitivity analysis in `code/models/interpret.py` (FR‑006, FR‑007, US‑3): SHAP/permutation feature importance for the best model (top 3‑5 descriptors); generate parity and partial‑dependence plots saved under `results/plots/`; perform threshold sweep `{0.25, 0.30, 0.35}` computing permutation‑test p‑values for R² > threshold; record variance of these p‑values in `results/sensitivity.yaml`. Add `code/utils/claim_validator.py` that aborts with non‑zero exit if the p‑value at **0.30** exceeds 0.05, logging “Primary claim rejected…”.
  - Verification: `results/interpretability.yaml`, `results/sensitivity.yaml`, and plot files exist; unit test `code/tests/unit/test_claim_validator.py` covers both halt and pass paths.

- [ ] T008 Add independent correctness, sensitivity, and runtime checks and execute them: run the full pipeline on the complete retrieved dataset (no toy substitution), record outcomes, and add `code/tests/integration/test_pipeline.py` covering fetch‑contract → schema validation → Miedema‑exclusion assertion → metrics‑schema validation. Record pipeline runtime and confirm it stays within the 6‑hour CPU budget.
  - Verification: `pytest code/tests/` passes; `python -m code.main --stage verify` (added in T021) exits 0.

- [ ] T009 [US3] Implement `code/report_generator.py` (FR‑007, US‑3): programmatically generate `results/report.md` from `results/metrics.yaml`, `results/sensitivity.yaml`, and plot assets; embed the exact disclaimer string, underpowered‑study notice when applicable, bootstrap‑CI warning flag, and any circularity warnings. Include `code/utils/causal_check.py` to scan the report for causal language violations.
  - Verification: `results/report.md` exists, contains the disclaimer, and the causal scanner test passes.

- [ ] T010 Re‑run the documented workflow (`python -m code.main --stage all`) and confirm all tests and artifact checks pass; verify that metric values (e.g., R²) differ by less than **0.01** from the previous run (tolerance defined in T020). Update `specs/001-predict-elastic-modulus/quickstart.md` if needed.
  - Verification: a clean re‑run reproduces metrics within the defined tolerance; `quickstart.md` commands execute as written.

## Phase 3: Additional required infrastructure (plan compliance)

- [ ] T011 [P] Implement the traditional **t‑test** against R² = 0 per Constitution Principle VII (FR‑002 conflict resolution). Compute the t‑statistic and p‑value, write `results/t_test.yaml`, and record the deviation from the plan as a documented exception.
  - Verification: `results/t_test.yaml` exists with fields `t_statistic`, `p_value`; a unit test confirms values are numeric.

- [ ] T012 [P] Create the PII‑scan script `scripts/pii_scan.sh` that runs the repository‑hygiene agent before any commit. Hook it into CI via the existing workflow.
  - Verification: script file exists and is executable; CI config invokes it.

- [ ] T013 [P] Implement `update_state_file()` in `code/main.py` to write content hashes of all generated artifacts into `state/projects/PROJ-443-predicting-the-effect-of-alloying-on-the.yaml` (Constitution V).
  - Verification: after any stage run, the state file is updated with correct hashes.

- [ ] T014 [P] Implement `validate_citations()` in `code/utils/validation.py` to check all external citations against the Reference‑Validator Agent (Constitution II).
  - Verification: function runs during `--stage verify` and reports any invalid citations.

- [ ] T015 [US2] Train **Direct‑Target** regression models (Random Forest, Gradient Boosting, ElasticNet) for **Bulk Modulus**, **Young’s Modulus**, **Shear Modulus**, and **Poisson’s Ratio** **including** Miedema‑derived features, to evaluate their predictive power as allowed by FR‑002. Store artifacts under `results/models/direct_*` and metrics under `results/metrics_direct.yaml`.
  - Verification: models train without Miedema exclusion errors; metrics file validates against `contracts/model_output.schema.yaml`.

- [ ] T016 [US2] Perform a **Variance Inflation Factor (VIF)** check on the full descriptor matrix (standard + Miedema features) before any training, outputting `results/vif_report.yaml`. Halt if any VIF > 5.
  - Verification: VIF report generated; pipeline aborts on high VIF.

- [ ] T017 [US1] Implement the **target‑fallback** logic (Bulk → Shear → Formation Energy) in `code/features/targets.py`. When a sample lacks Bulk Modulus, automatically use Shear Modulus; if absent, use Formation Energy, and record the fallback decision in `data/processed/target_fallback.log`.
  - Verification: fallback log created; downstream tasks consume the constructed residual targets accordingly.

- [ ] T018 [US2] Post‑process the raw statistical outputs to conform to `contracts/output.schema.yaml`: map permutation‑test p‑values to the “Type I error rate” fields (`threshold_0_25`, etc.) and compute `fpr_variance`. Write the final `results/metrics.yaml` that passes schema validation.
  - Verification: schema validation succeeds; fields match contract expectations.

- [ ] T019 [US2] (see F001) Compute the **t‑test** for R² = 0 and store results as described in T011.

- [ ] T020 [US2] Define the reproducibility tolerance for T010 (ΔR² < 0.01) and document it in `specs/001-predict-elastic-modulus/quickstart.md`.
  - Verification: tolerance referenced in T010 verification step.

- [ ] T021 [P] Add a `--stage verify` entry point in `code/main.py` that runs all schema validations, provenance checks, citation validation, and the PII scan, exiting with status 0 only on full compliance.
  - Verification: `python -m code.main --stage verify` exits 0 after a successful run.

## Dependencies and requirement coverage

- All tasks now reference the same top‑level `data/` and `results/` directories.
- Required packages are fully listed in T001.
- Explicit filenames and paths are provided for every artifact to enable deterministic verification.

## Execution ordering

T001 → T002 → T003 → T004 → T005 → T006 → T007 → T008 → T009 → T010 → (infrastructure tasks T011‑T021 may be interleaved as needed, but must run before final verification).
