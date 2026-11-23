# Tasks: Assessing the Predictive Power of Machine Learning for Organic Reaction Outcomes

**Inputs**: Active `spec.md`, `plan.md`, data-model.md, contracts, and prior task history.
**Scope**: Smallest complete study — verified USPTO yield ingestion → RDKit sanitization + ECFP4/MACCS fingerprints → stratified-by-class + scaffold-grouped split → fixed representative training subset → RF/SVM grid-search training → validation/test evaluation, per-class generalization, substructure importance → reproducible result artifacts. CPU-only (scikit-learn, RDKit), ≤ 7 GB RAM, 6 h runtime, free-tier CI. This revision atomizes coarse tasks (T003, T004, T008) into sub-tasks, adds the materialized Fixed Representative Subset (T005a), adds the FR-005 validation-set evaluation, and serializes the post-training tasks.

**Canonical data source (Constitution I)**: The authoritative ingestion mechanism for execution is the HuggingFace `datasets` recipe in T002. The spec's `wget`/DOI assumption and the plan's "canonical HuggingFace URLs" wording must be reconciled to this recipe upstream (flagged for kickback); until then, tasks implement the HF `datasets` loader only, with no synthetic fallback ever.

## Phase 1: Setup and first end-to-end analysis

- [ ] T001 [US1] **Verify contracts and validate input provenance.** Redo of previously rejected T008a: write a valid, non-empty `specs/001-assessing-the-predictive-power-of-machin/contracts/output.schema.yaml` (fields: `model_type` string, `hyperparameters` object, `metrics` object with required `R2`/`RMSE`/`MAE` numbers, `split_ratios` object; all four top-level keys required) and implement `code/utils/validators.py` with `validate_output_schema(payload: dict, schema_path: str)` and `validate_dataset_schema(payload: dict, schema_path: str)` enforcing both contracts via `pydantic`, raising on mismatch.
  - Verification: `cat specs/001-assessing-the-predictive-power-of-machin/contracts/output.schema.yaml` shows well-formed YAML; a deterministic smoke check passes:
    `python -c "from code.utils.validators import validate_output_schema, validate_dataset_schema; validate_output_schema({'model_type':'RF','hyperparameters':{},'metrics':{'R2':0.5,'RMSE':10.0,'MAE':8.0},'split_ratios':{}}, 'specs/001-assessing-the-predictive-power-of-machin/contracts/output.schema.yaml')"` exits 0, and the analogous `validate_dataset_schema` call with a minimal valid reaction record against `dataset.schema.yaml` exits 0; an invalid payload raises.
  - Also confirm the existing `code/config.py` constants (pinned seeds, `YIELD_RANGE_STRATEGY`, `TRAIN_VAL_TEST_SPLIT_RATIOS`, `BATCH_SIZE_ROWS`, hyperparameter grids, `SC003_HIGH_YIELD_PERCENTILE`, `SUBSET_SIZE`) and document the runnable entry point in the feature's `quickstart.md`. (FR-001, Constitution I).

- [ ] T002 [US1] **Download the real USPTO yield dataset.** Implement `code/preprocessing/download.py`: fetch via `datasets.load_dataset("farama/USPTO_Yields", split='train')`, convert to DataFrame, save `data/raw/uspto_raw.parquet`. If the dataset ID is unreachable, retry up to `MAX_RETRIES` (3), then RAISE `FileNotFoundError("Dataset verification failed: canonical source could not be accessed. No synthetic fallback allowed.")` — NO synthetic/mock fallback may ever fire. If the fetch fails, the run must fail loudly so the execution stage can discover a verified source. <!-- FAILED-IN-EXECUTION: code/preprocessing/download.py exit=1 -->
  - Record SHA-256 of the raw parquet and the row count in `data/results/download_checksum.txt` and `data/results/download_log.txt`. (FR-001, Constitution I, III).

- [ ] T003a [US1] **Sanitize structures and parse yields.** Implement `code/preprocessing/sanitize.py`:
  - Verify the raw-file SHA-256 against `data/results/download_checksum.txt` before processing; raise on mismatch.
  - RDKit sanitization: salt removal and component standardization; exclude reactions with missing reagent information; handle duplicate reactions with conflicting yields by averaging (with logging); parse yield ranges per `YIELD_RANGE_STRATEGY` ('midpoint' default, or exclude), excluding unparseable yields with a logged reason.
  - Output `data/processed/sanitized_reactions.parquet` with sanitized SMILES, parsed yields in [0, 100], and `reaction_class`.
  - Verification: unit tests in `tests/unit/test_sanitize.py` pass; spot-check that output yields are within [0, 100] and no null SMILES remain. (FR-001, FR-002).

- [ ] T003b [US1] **Generate ECFP4 and MACCS fingerprints (chunked).** Implement `code/preprocessing/fingerprints.py`:
  - Chunked/streamed fingerprint generation from `data/processed/sanitized_reactions.parquet`: ECFP4 (2048-bit) and MACCS (167-bit) for reactants/reagents, batched by `BATCH_SIZE_ROWS` to stay < 7 GB RAM.
  - Output `data/processed/cleaned_reactions.parquet` validated against `specs/001-assessing-the-predictive-power-of-machin/contracts/dataset.schema.yaml` (fields `smiles`, `yield`, `reaction_class`, `fingerprint_ecfp`, `fingerprint_maccs`).
  - Verification: unit tests in `tests/unit/test_fingerprints.py` pass; confirm the output parquet has non-null fingerprint vectors of exactly 2048/167 bits. (FR-003, FR-009).

- [ ] T003c [US1] **Orchestrate preprocessing and emit the data-quality report.** Implement the preprocessing path of `code/main.py` chaining T003a → T003b and writing `data/results/data_quality_report.json` containing `exclusion_fraction`, exclusion reasons, yield-parsing strategy and rationale, and fingerprint dimensions. Log actual bit lengths to `data/results/fingerprint_dimensions.log`.
  - Verification: `python -m code.main --stage preprocess` runs end-to-end on the real data; `data_quality_report.json` exists with all keys; `exclusion_fraction` computed from real counts (SC-005). (FR-001, FR-009, SC-005).

- [ ] T003 [US1] **Preprocessing completion gate.** Parent task: checked only when T003a, T003b, and T003c are all complete and verified. (FR-001, FR-002, FR-003, FR-009, SC-005).

## Phase 2: Complete the study and validate its evidence

- [ ] T004a [US2] **Murcko scaffold keying.** Implement `code/preprocessing/scaffold.py`: compute Murcko scaffold keys from `data/processed/cleaned_reactions.parquet` → `data/processed/scaffold_groups.parquet` with a mandatory `scaffold_id` column plus `reaction_class`; log unique-scaffold count to `data/results/scaffold_generation_log.txt`.
  - Verification: output parquet has no null `scaffold_id`; logged count matches `scaffold_groups.parquet` unique values. (FR-004).

- [ ] T004b [US2] **Stratified-by-class + intra-class scaffold split.** Implement `code/modeling/split.py`:
  - (1) merge classes with n < 20 into the nearest neighbor class (or exclude with `CLASS_EXCLUDED_DUE_TO_SMALL_N` log); (2) stratify by `reaction_class` (primary, Constitution VI); (3) group by `scaffold_id` within class (secondary); (4) assign whole scaffold groups to train/val/test per `TRAIN_VAL_TEST_SPLIT_RATIOS` (default 0.7/0.15/0.15), placing cross-class scaffolds in the split where they are most frequent; (5) verify every class with n > 20 appears in the test set (warn `CLASS_MISSING_IN_TEST_SET` otherwise); (6) verify no `scaffold_id` spans splits.
  - Outputs: `data/processed/{train,validation,held_out_test}_indices.csv`, `data/results/split_log.json` (including `scaffold_leakage_verified`, class-presence flags), and `data/results/split_ratios_final.json` recording the exact ratios used (FR-004 mandate).
  - Verification: `split_log.json` shows `scaffold_leakage_verified: true`; every class with n > 20 present in test indices. (FR-004, Constitution VI, SC-002).

- [ ] T004c [US3] **Derive the SC-003 validation subset.** Implement in `code/modeling/split.py`: high-yield = yield > 90th percentile of the VALIDATION split; write `data/processed/sc003_val_indices.csv` and log the threshold to `data/results/split_log.json` (`sc003_threshold`).
  - Verification: threshold equals the validation-split 90th percentile; index file non-empty. (SC-003).

- [ ] T004 [US2] **Split completion gate.** Parent task: checked only when T004a, T004b, and T004c are complete and verified. (FR-004, Constitution VI, SC-002, SC-003).

- [ ] T005a [US2] **Materialize the Fixed Representative Subset.** Implement `code/modeling/subset.py`: create `data/processed/fixed_representative_subset.parquet` from the training split via a fixed-seed (`random_state=42`), class-stratified sample of size `SUBSET_SIZE` (from `code/config.py`), used for BOTH tuning and final training (no tuning-on-sample/train-on-full mismatch). Record the sample rule (stratified by `reaction_class`, seed, exact row count) in `data/results/subset_log.json` and the SHA-256 of the subset file in `data/results/subset_checksum.txt`.
  - Verification: subset row count equals `SUBSET_SIZE`; class proportions match the training split within ±0.02; checksum file matches the parquet's SHA-256. (Plan Complexity Tracking, Constitution III; note: spec.md FR-001/FR-009 wording on full-dataset training must be reconciled upstream — flagged for kickback).

- [ ] T005 [US2] **Train RF and SVM with grid search + CV; evaluate on the held-out VALIDATION set.** Complete/execute `code/modeling/train.py` (RF grid over `n_estimators`/`max_depth`; SVM grid over `C`/kernel linear+RBF; 5-fold CV on the Fixed Representative Subset; `n_jobs=-1`; pinned seeds) and `code/modeling/save_models.py` (artifacts under `data/results/best_models/`). Then implement the evaluation path in `code/modeling/evaluate.py`:
  - Metrics (R2, RMSE, MAE, 4 decimals) for the best models on the **held-out validation set** → `data/results/val_metrics.json` (this is the FR-005 model-selection evaluation), on the training set → `data/results/train_metrics.json`, and on the held-out test set → `data/results/test_metrics.json` (FR-006).
  - Run the ±0.05 CV-consistency check on the VALIDATION metrics: |val R² − mean CV R²| ≤ 0.05; report any deviation honestly in `val_metrics.json` (`cv_consistency_deviation`).
  - Validate all three outputs against `specs/001-assessing-the-predictive-power-of-machin/contracts/output.schema.yaml`. (FR-005, FR-006, US-2 acceptance 3).

- [ ] T006 [US2] **Resource profiling and sensitivity checks.** Implement `code/utils/memory_profiler.py` (`@profile_memory` decorator using `tracemalloc`/`psutil`, wall-clock timing, per-task log files `data/results/memory_profile_{task_id}.log`), wrap the `code/modeling/train.py` and `code/modeling/evaluate.py` entry-point functions, and aggregate into `data/results/memory_profile.log` and `data/results/runtime_profile.json` with `peak_ram_mb` and `wall_clock_time_seconds` per step. Assert peak RAM < 7 GB and total runtime within the 6 h budget. If a budget is exceeded, the ONLY permitted fallbacks are streaming/chunking adjustments and `BATCH_SIZE_ROWS` reduction — training-data reduction is NOT permitted (the Fixed Representative Subset is a fixed, pre-declared design element from T005a, never an emergency shrink knob); if streaming cannot bring the run within budget, report the exact mismatch honestly rather than fabricating or shrinking results. Also run a split-sensitivity check (re-split with a second pinned seed; report metric variance) and record outcomes in `data/results/sensitivity_report.json`. (FR-009, FR-010, SC-004).

- [ ] T007 [US3] **Per-reaction-class generalization analysis.** Implement `code/modeling/per_class.py` (distinct module; does not edit `evaluate.py`): compute per-class R² and RMSE on the held-out test set (classes with n > 20 only; merge/exclude smaller classes with warnings), compute the train–test generalization gap per class, and output `data/results/per_class_metrics.json` and `data/results/generalization_gap_report.json` with pass/fail status against SC-002 (gap ≤ 0.10). Report the best model's overall test R² against SC-001 (≥ 0.40) honestly, including a null result if observed. (FR-007, SC-001, SC-002).

- [ ] T008a [US3] **Permutation importance.** Implement `code/modeling/importance.py` (distinct module): permutation importance for the best RF (`n_repeats=5`, `random_state=42`, `n_jobs=-1`) → `data/results/permutation_importance.json`. (FR-008, US-3 acceptance 2).

- [ ] T008b [US3] **Bit mapping and reaction-center identification.** In `code/modeling/importance.py`:
  - Bit-to-atom mapping via `GetMorganFingerprintAsBitVect` with `bitInfo` → `data/results/bit_mapping.json`.
  - Reaction-center identification by reactant/product bond-order differencing. Product structures are obtained by parsing the reaction SMILES field on the `'>>'` separator (left = reactants, right = products); entries whose SMILES lacks `'>>'` or fails RDKit parsing are flagged `ambiguous: true` and excluded from center identification with a logged reason. Threshold |Δorder| ≥ 1.0; documented fallback for no/threshold-ambiguous cases → `data/results/reaction_centers.json` with `atom_indices`, `bond_changes`, `ambiguous`, `reaction_center_count`. (FR-008).

- [ ] T008c [US3] **Substructure aggregation and top-3 selection.** In `code/modeling/importance.py`: aggregate importance across all bits mapping to the same substructure (radius-2 environment SMILES), summing scores for colliding bits; rank substructures and select the top subset → `data/results/feature_importance_report.json` with `substructure_smiles`, `aggregated_score`, `bit_indices`, `collision_count`, `collision_details`, and `top_3_substructures`; set `bit_collision_acknowledged: true` when collisions occur. (FR-008, US-3 acceptance 3).

- [ ] T008 [US3] **Importance completion gate.** Parent task: checked only when T008a, T008b, and T008c are complete and verified. (FR-008).

- [ ] T009 [US3] **SC-003 interpretability validation.** Implement in `code/modeling/importance.py` (or a small `code/modeling/sc003.py`): load `data/processed/sc003_val_indices.csv` (validation-split derived), `data/results/feature_importance_report.json`, and the saved models; compute the fraction of high-yield validation reactions (yield > 90th-percentile threshold from T004c) containing EACH of the `top_3_substructures`. **Deterministic pass rule (SC-003)**: pass iff EVERY one of the three substructures individually has frequency > 0.80; a single substructure below 0.80 fails. Output `data/results/sc003_validation.json` with per-substructure `frequencies` (list of 3), `yield_threshold`, `frequency_threshold` (0.80), and `pass_fail_status` (pass / fail; `INSUFFICIENT_DATA` with warning `INSUFFICIENT_HIGH_YIELD_SAMPLES` if the high-yield subset is too small). (SC-003, FR-008).

- [ ] T010 [US3] **Figures and final results aggregation.** Generate publication-quality figures directly from validated outputs with `matplotlib`: predicted-vs-actual test scatter with per-class coloring, per-class R² bar chart, top-substructure importance chart, and generalization-gap plot → `figures/`. Aggregate all metrics (train/val/test), split ratios (from `data/results/split_ratios_final.json`), data-quality statistics (`exclusion_fraction`), SC-001/SC-002/SC-003 outcomes, and feature importance into `data/results/final_report.json`, all values sourced from the result artifacts — no manual entry. (FR-006, FR-007, FR-008, SC-005).

## Phase 3: Reproducible results and paper handoff

- [ ] T011 Write the methods/results account in `specs/001-assessing-the-predictive-power-of-machin/results.md`, linked to the actual output artifacts (`data/results/*.json`) and figure files (`figures/*`). Report the measured R²/RMSE/MAE (train/val/test), per-class gaps, substructure findings, the exclusion fraction, and resource usage; describe negative findings, failures, and limitations (bit collisions, subset/sampling limitations, small-class merges) honestly. Verification: the file exists at that exact path and contains working relative links to at least `data/results/final_report.json`, `data/results/per_class_metrics.json`, `data/results/feature_importance_report.json`, and at least one `figures/` file. (Constitution IV).

- [ ] T012 Re-run the documented workflow end-to-end from its declared inputs (`python -m code.main` per `quickstart.md`), confirm the full `pytest` suite (`tests/unit`, `tests/contract`, `tests/integration`) passes and all result artifacts regenerate consistently under pinned seeds, and document the paper-stage handoff: required tables (overall + per-class metrics, top substructures), figures, and the interpretability/generalization claims the paper stage must preserve. (Constitution I, V).

## Dependencies and requirement coverage

| Requirement | Task(s) | Demonstration |
|---|---|---|
| FR-001 ingestion | T002, T003a–T003c | `data/raw/uspto_raw.parquet` + download log/checksum |
| FR-002 sanitization | T003a | `data/processed/sanitized_reactions.parquet`, unit tests |
| FR-003 fingerprints | T003b | 2048/167-bit vectors, `fingerprint_dimensions.log` |
| FR-004 scaffold split | T004a–T004c | `split_log.json`, `split_ratios_final.json` |
| FR-005 grid search + validation eval | T005, T005a | `data/results/best_models/`, `val_metrics.json` with CV-consistency check |
| FR-006 test metrics | T005, T010 | `test_metrics.json`, `final_report.json` |
| FR-007 per-class | T007, T010 | `per_class_metrics.json` |
| FR-008 importance | T008a–T008c, T009 | `feature_importance_report.json`, `sc003_validation.json` |
| FR-009/FR-010 CPU/RAM | T003b, T006 | `memory_profile.log`, `runtime_profile.json` |
| SC-001–SC-005 | T005–T010 | statuses inside `final_report.json` |

**Execution order (strictly serial; no parallel task pairs)**: T001 → T002 → T003a → T003b → T003c → T004a → T004b → T004c → T005a → T005 → T006 → T007 → T008a → T008b → T008c → T009 → T010 → T011 → T012. Parent gates T003, T004, T008 are marked complete only when all their sub-tasks are verified. T006, T007, and T008a–c previously claimed parallelism but all touched `code/modeling/evaluate.py`; they are now serialized and their code lives in distinct modules (`per_class.py`, `importance.py`), with T006 wrapping only the train/evaluate entry points.

## Revision behavior

- Preserved as complete (previously verified): project scaffolding, `code/config.py`, `code/utils/io.py`, package `__init__.py` files, requirements, lint config, `.gitkeep` markers, and the existing unit/contract/integration test files (T001b–T006, T009, T011–T013, T020–T021, T024–T025, T028–T030 of the prior list).
- Reopened: the rejected T008a output-schema artifact is redone as T001 with the correct feature path `specs/001-assessing-the-predictive-power-of-machin/contracts/output.schema.yaml` and explicit validator arguments.
- Atomized this round: T003 → T003a/T003b/T003c; T004 → T004a/T004b/T004c; T008 → T008a/T008b/T008c (parent IDs retained as completion gates).
- Added this round: T005a (materialized Fixed Representative Subset with checksum), validation-set metrics + ±0.05 CV-consistency check in T005 (FR-005), deterministic SC-003 all-three rule in T009, product-SMILES source (`'>>'` parsing) in T008b, concrete results.md deliverable in T011.
- Upstream kickbacks (not fixable in tasks.md): plan.md Technical Context contains leftover CI/CD content and placeholder numbers; spec.md FR-004 lacks the class-stratification wording of Constitution VI; spec.md Assumptions name `wget`/DOI while execution uses the HF `datasets` recipe; spec.md SC-004 has a placeholder where the 6 h limit belongs; data-model.md attribute names (`ecfp4_vector`/`maccs_vector`) and filenames (`uspto_yield.parquet`, `sanitized.parquet`, `subset_train.parquet`, `data/results/models/`) diverge from the contracts and actual outputs (`fingerprint_ecfp`/`fingerprint_maccs`, `uspto_raw.parquet`, `sanitized_reactions.parquet`, `fixed_representative_subset.parquet`, `data/results/best_models/`). Tasks implement the contract-compliant forms.
- Data rule: the loader must fail loudly on fetch failure; no synthetic fallback, no toy stand-in. If the full dataset exceeds the compute budget, stream/chunk it; the only sanctioned subset is the pre-declared, fixed-seed, class-stratified Fixed Representative Subset (T005a), with sample size and limitation stated.