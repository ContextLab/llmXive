# Tasks: Predicting Antibiotic Resistance Evolution from Genomic Sequences

**Inputs**: `spec.md`, `plan.md`, existing artifacts, verifier feedback (rejected T040/T047/T048; duplicate task IDs T039/T047).

**Re-plan note**: This revision repairs the malformed task list — duplicate identities (T039, T047 appeared twice) are eliminated by giving each deliverable a single unique task ID and single location. Verified completed work is preserved. The three rejected tasks (T047 entry point, T040 state hashing, T048 runtime measurement) are reopened below with deterministic artifact checks.

## Format

`- [ ] T### [P?] [USx?] description with exact artifact paths`. `[P]` = parallel-safe (different files, no dependencies).

---

## Completed work (preserved, verified)

The following deliverables were previously verified and are retained as completed context; they are NOT re-tasked:

- Project scaffolding, `code/requirements.txt`, config/lint tooling, `code/utils/logging.py`, `code/utils/config.py` (keys: `random_seed`, `max_isolates`, `permutation_iterations`, `thresholds`), `code/utils/hash_artifacts.py`, directory structure, contract/unit test scaffolds.
- US1 pipeline: `code/01_ingest/download_ncbi.py` (fail-loudly, no synthetic fallback), `ingest_metadata.py` (W003 logging), `download_card.py`, `code/02_process/run_snippy.sh`, `run_ariba.sh`, `build_feature_matrix.py` (CNV proxy with `cnv_source` flag, W005/E004 edge cases, FASTA pre-validation), `generate_phylogeny.py` → `data/processed/phylogeny.nwk`.
- Contract gate logic in `tests/contract/` (feature matrix + model output schemas).
- US2: `generate_class_gene_mapping.py` → `data/processed/class_to_genes.json`, `mechanism_blind_filter.py`, `split_data.py` (phylogenetically-blocked, stratified within clade), `train_models.py` (per-class LR-L1/RF, 5-fold CV, `model_{type}_{class}.pkl`), `evaluate.py` (AUC-ROC, PR curves, `feature_ranking.csv`, `metrics.json`).
- US3: `code/04_validate/phylo_permutation.py` (PGLS residual permutation, config-driven iterations, tree pre-check, `permutation_results.json` with p-value/significance flag, blocks if p ≥ 0.05), `sensitivity_analysis.py` (exact threshold set {0.4, 0.45, 0.5, 0.55, 0.6}, `sensitivity_sweep.csv` with FP/FN rates and FP-rate range, JSON logging), `code/05_viz/generate_plots.py`.
- `code/main_reproducible.py` full-pipeline re-execution, docs/quickstart updates, CPU-efficiency and N-limit enforcement, fail-loudly ingestion fixes (T041–T046 work).

---

## Phase 1: Entry point and first end-to-end run

- [ ] T101 [US1/US2/US3] **REDO of rejected T047**: Create `code/main.py` as the single pipeline entry point orchestrating: (1) ingestion, (2) contract validation gate — it MUST invoke `pytest tests/contract/` via subprocess immediately after ingestion and abort with error code E001 ("Contract Validation Failed") on failure, (3) modeling, (4) validation, (5) versioning/state finalization. The script must be a real executable Python file with a `if __name__ == "__main__":` block and exit codes. **Verification**: `python code/main.py --help` exits 0; the file exists, is non-empty, and contains the five-stage orchestration in order. **Verification**: run the full pipeline end-to-end on the N=1000 CI subset and confirm `data/processed/feature_matrix.csv`, `data/models/model_lr_*.pkl`, `data/models/model_rf_*.pkl`, `data/models/metrics.json`, `data/processed/permutation_results.json`, `data/processed/sensitivity_sweep.csv`, and figures in `data/processed/` all exist and are non-empty after the run. <!-- FAILED-IN-EXECUTION: code/main.py exit=1 -->
  - Update `docs/quickstart.md` to document `python code/main.py` as the primary command.
  - **Note**: `code/main.py` and `code/main_reproducible.py` must not diverge; `main.py` is the canonical entry point and `main_reproducible.py` may delegate to it.

## Phase 2: Runtime and state verification

- [ ] T102 [US1/US2/US3] **REDO of rejected T048**: Implement runtime and memory measurement inside `code/main.py`: record start/end timestamps, peak RSS memory usage (in bytes), and write `data/processed/pipeline_runtime.json` containing keys `start_time`, `end_time`, `duration_seconds`, `peak_memory_bytes` (ISO‑8601 timestamps, float seconds, integer bytes). **Verification**: after the T101 end-to-end run, `data/processed/pipeline_runtime.json` exists, parses as JSON, contains all four keys, `duration_seconds` < 21600 for the N=1000 run (SC‑004), and `peak_memory_bytes` < 7 GB (7 * 1024³). Failure to meet the limit must be reported as an explicit error, not silently logged.

- [ ] T103 [US1/US2/US3] **REDO of rejected T040**: Execute `code/utils/hash_artifacts.py` as the final stage of `code/main.py` to finalize project state: compute SHA256 hashes for all `data/` and `code/` artifacts and write them, with an `updated_at` timestamp, to the canonical state file `state/projects/PROJ-027-predict-antibiotic-resistance-evoluti.yaml`. **Verification**: the state file exists at the path above, parses as valid YAML/JSON, contains an `artifact_hashes` map covering the current artifacts and an `updated_at` timestamp. If the platform state file does not exist or its schema is ambiguous, STOP and surface the stage‑ownership conflict for correction rather than fabricating a state file.

## Phase 3: Independent verification of scientific evidence

- [ ] T104 [US2] Run an independent verification script `code/03_model/verify_results.py` that loads `data/models/metrics.json` and `data/processed/feature_ranking.csv` and checks: (a) AUC‑ROC values exist for every antibiotic class with a trained model, (b) the mechanism‑blind filter excluded the canonical resistance genes for each class (cross‑check against `data/processed/class_to_genes.json`), (c) the top‑10 feature ranking table exists and excludes target‑class genes. **Verification**: script exits 0 and writes a pass/fail summary to `data/processed/verification_summary.json`.

- [ ] T105 [US3] Run an independent statistical sanity check `code/04_validate/verify_statistics.py` that: (a) re‑reads `data/processed/permutation_results.json` and confirms the p‑value was computed from ≥1000 phylogenetically‑aware permutations, (b) re‑reads `data/processed/sensitivity_sweep.csv` and confirms the threshold set is exactly {0.4, 0.45, 0.5, 0.55, 0.6} with FP/FN rates for each, and the FP‑rate range summary field is present. **Verification**: script exits 0 and appends results to `data/processed/verification_summary.json`.

- [ ] T109 [US2] **Baseline AUC comparison**: Compute a baseline performance metric (e.g., majority‑class AUC or random‑classifier AUC) and record it in `data/processed/baseline_metrics.json`. Extend `code/03_model/verify_results.py` to compare each class’s AUC‑ROC against this baseline and add a boolean `exceeds_baseline` per class in the verification summary. **Verification**: `verification_summary.json` includes baseline values and per‑class pass/fail flags indicating whether the model exceeds the baseline.

- [ ] T110 [US1] **VIF filtering**: Implement variance‑inflation‑factor filtering on the feature matrix to remove highly collinear predictors. Create script `code/02_process/vif_filter.py` that reads `data/processed/feature_matrix.csv`, computes VIF for each feature, drops features with VIF > 5, and writes the filtered matrix to `data/processed/feature_matrix_vif.csv`. Also output a log `data/processed/vif_report.txt` listing dropped features and their VIF scores. **Verification**: filtered matrix exists, column count is reduced relative to the unfiltered matrix, and the log file is non‑empty.

- [ ] T111 [US2] **Standard stratified split**: In addition to phylogenetically‑blocked cross‑validation, generate a conventional stratified train/validation/test split (70 % / 15 % / 15 %) stored as `data/processed/stratified_split.json` containing three arrays of isolate IDs. **Verification**: each split preserves the overall class distribution within 1 % tolerance, and the file exists and is valid JSON.

- [ ] T112 [US1] **Copy‑Number Variation extraction**: Replace the CNV proxy with real CNV extraction using a tool such as `cnvkit` or `CNVnator`. Implement `code/02_process/extract_cnv.py` that processes BAM files (derived from Snippy alignments) to produce CNV calls, integrates them into the feature matrix, and writes the final matrix to `data/processed/feature_matrix_with_cnv.csv`. Produce a summary `data/processed/cnv_summary.csv` listing CNV regions per isolate. **Verification**: CNV columns are present in the final feature matrix, and the summary file is non‑empty.

## Phase 4: Reproducibility and results handoff

- [ ] T106 [US1/US2/US3] Re‑run the documented workflow from its declared inputs (`python code/main.py`) a second time with the pinned random seed and confirm deterministic reproduction: `metrics.json` AUC values match the first run within 1e‑6, and `pipeline_runtime.json` is regenerated. **Verification**: a comparison report `data/processed/reproducibility_check.json` records first‑run vs second‑run metrics and a boolean `reproducible` field.

- [ ] T107 [US1/US2/US3] Write a concise methods/results account in `specs/001-predict-antibiotic-resistance/results.md` (the plan‑declared directory) linked to the actual artifacts: report per‑class AUC‑ROC from `metrics.json`, permutation p‑values from `permutation_results.json`, sensitivity ranges from `sensitivity_sweep.csv`, and the N=1000 CI‑scale limitation versus the spec’s ≤5000‑isolate target. Describe negative findings (e.g., classes excluded under W005, W003 plasmid‑missing handling, any class where p ≥ 0.05 blocked the pipeline) honestly. **Verification**: document exists, cites real file paths, and contains no values absent from the result artifacts.

- [ ] T108 [US1/US2/US3] Document the paper‑stage handoff in the results document from T107: list the figures (`data/processed/*.png`), tables (`feature_ranking.csv`, `sensitivity_sweep.csv`, `metrics.json`), and the claim structure (associational, not causal; mechanism‑blind validation) the paper stage must consume. **Verification**: handoff section is present in the results document and references the exact artifact paths.
