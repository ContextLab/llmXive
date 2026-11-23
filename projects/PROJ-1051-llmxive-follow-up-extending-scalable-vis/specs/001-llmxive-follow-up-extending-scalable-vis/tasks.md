# Tasks: Do distilled structural‑latent features add predictive value beyond dense text features for the corpus overlap/CPU‑score label?

**Inputs**: `spec.md` (with amendments), `plan.md` (re‑plan v4), `data‑model.md`, contract schemas, and any existing artifacts.  
All tasks write only to project‑owned paths under `data/`, `artifacts/`, `src/`, or `figures/`.  
Tasks are ordered to respect data flow; each task lists the primary script/file it creates or modifies and the artefacts it must produce.

---

## Phase 1 – Setup and first end‑to‑end analysis  

| Goal | Run an executable analysis on a small real input early, producing a real result file that can be inspected. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T001 [P] [US1] **Download and validate the verified textual dataset**  
  *Script*: `src/data/download_text.py` (defines `TEXT_DATASET_URL`)  
  *Outputs*: `data/raw/overlap.parquet`, `data/raw/provenance_text.json` (contains `dataset_url`, `sha256`, `n_rows`, `label_semantics`, `seeds`)  
  *Verification*:  
  ‑ The parquet file exists and its SHA‑256 matches the entry in `provenance_text.json`.  
  ‑ `provenance_text.json` includes all required fields and reports `n_rows ≥ 10 000`.  
  ‑ Unit test `src/tests/test_download_text.py` asserts successful load via `pyarrow`, confirms the row count, and checks that a missing/invalid URL exits with error code 1 and the message `VERIFIED DATASET URL MISSING/UNREACHABLE`.

- [ ] T002 [P] [US1] **Preprocess raw parquet into schema‑valid `DocumentPair` records**  
  *Script*: `src/data/preprocess.py` – validates each row against `contracts/documentpair.schema.yaml`, drops rows missing required fields, and writes `data/processed/document_pairs.parquet`.  
  *Outputs*: `data/processed/document_pairs.parquet`, `data/processed/preprocess_stats.json` (records `n_valid_rows`, `n_dropped`).  
  *Verification*:  
  ‑ All rows in the output parquet validate against the schema.  
  ‑ If `n_valid_rows < 1000` the script aborts with FR‑007 error `Insufficient valid rows (found X, required ≥1000)`.  
  ‑ Unit test `src/tests/test_preprocess.py` covers both success and below‑minimum failure paths.

- [ ] T003 [P] [US1] **Generate deterministic structural‑latent features**  
  *Script*: `src/features/structure.py` – extracts a fixed‑dimensional deterministic feature vector (e.g., line‑length statistics, token‑position histograms) from the `text` field; records extractor version.  
  *Outputs*: `data/processed/document_pairs_with_latent.parquet` (adds `structural_latent` column), `data/processed/structural_latent_provenance.json` (records `extractor_name`, `extractor_version`, `latent_dim`).  
  *Verification*:  
  ‑ Every row has a `structural_latent` array of length `D` (as recorded).  
  ‑ Determinism test confirms that re‑running the script on the same input yields identical latents.  
  ‑ Unit test `src/tests/test_structural_latent.py` checks shape, dtype, and reproducibility.

- [ ] T004 [P] [US1] **Create deterministic train/val/test splits**  
  *Script*: `src/utils/split_generator.py` – shuffles with a fixed seed (`42`) and writes splits respecting a 0.8/0.1/0.1 ratio.  
  *Outputs*: `data/splits/splits.yaml` (lists `train`, `val`, `test` document IDs).  
  *Verification*:  
  ‑ The file exists and the three sets contain the expected number of IDs (±1).  
  ‑ Unit test `src/tests/test_split_generator.py` validates the ratios and reproducibility.

- [ ] T005 [P] [US2] **Thin end‑to‑end smoke run**  
  *Script*: `src/cli/run_pipeline.py --smoke` – loads a tiny subset (first 200 rows) of the training split, runs the full pipeline (feature extraction, a single‑epoch distillation, baseline training, downstream evaluation) to ensure all components interoperate.  
  *Outputs*: `data/results/smoke_results.json`, updated `quickstart.md` with the command  

    ```bash
    python src/cli/run_pipeline.py --smoke
    ```  

  *Verification*:  
  ‑ `smoke_results.json` contains numeric metrics for both the text‑only and text ⊕ structural‑latent arms (no placeholders).  
  ‑ Executing the command from `quickstart.md` exits 0 and reproduces the same `smoke_results.json` (checked by a checksum test).

---

## Phase 2 – Complete the study and validate its evidence  

| Goal | Run the full specified parameter/data domain, preserve every population, baseline and scientific constraint from the specification. |
|------|------------------------------------------------------------------------------------------------------------------------------------------|

- [ ] T006 [P] [US2] **Train the DistilledModel (text → structural latent) across all required seeds**  
  *Script*: `src/models/distilled.py`, invoked via  

    ```bash
    src/cli/run_pipeline.py --stage distill --seeds 42,43,44,45,46,47,48,49,50,51
    ```  

  *Outputs*: checkpoints under `artifacts/models/distilled_<seed>/`, per‑seed eval files `artifacts/eval/distill_{seed}.json`, aggregated summary `artifacts/eval/distill_summary.json` (fields `mse_val_mean`, `mse_random_init_mean`, `p_value`, `test_name`, `alpha: 0.025`, `is_sanity_check_only: true`, `val_train_loss_ratio`).  
  *Verification*:  
  ‑ Each `distill_{seed}.json` records `val_mse`, `train_mse`, `peak_ram_gb`, `runtime_s`.  
  ‑ The summary shows `p_value < 0.025` **and** `mse_val_mean < mse_random_init_mean`; otherwise the script exits with `distillation sanity check failed`.  
  ‑ Peak RAM ≤ 7 GB and total runtime ≤ 21 600 s (recorded in `resources.json`).

- [ ] T007 [P] [US3] **Train per‑seed text‑only downstream baseline (matching the 10 seeds)**  
  *Script*: `src/models/baseline.py`, invoked via  

    ```bash
    src/cli/run_pipeline.py --stage baseline --seeds 42,43,44,45,46,47,48,49,50,51
    ```  

  *Outputs*: checkpoints under `artifacts/models/baseline_<seed>/`, evaluation files `artifacts/eval/baseline_{seed}.json` (fields `val_metric`, `test_metric`, `peak_ram_gb`).  
  *Verification*:  
  ‑ Exactly ten baseline checkpoints exist, one per seed.  
  ‑ No OOM errors; each `peak_ram_gb` ≤ 7 GB.  
  ‑ Unit test `src/tests/test_baseline.py` confirms that re‑training with the same seed reproduces identical metrics.

- [ ] T008 [P] [US3] **Leakage pre‑check and downstream evaluation of augmented vs. baseline**  
  *Script*: `src/eval/downstream.py`, invoked via  

    ```bash
    src/cli/run_pipeline.py --stage downstream --seeds 42,43,44,45,46,47,48,49,50,51
    ```  

  *Outputs*: per‑seed downstream files `artifacts/eval/downstream_{seed}.json` (fields `metric_baseline`, `metric_augmented`, `delta`), consolidated `artifacts/eval/results.json` containing `label_semantics`, `leakage_check`, and the augmented predictions (structural latents concatenated with text embeddings).  
  *Verification*:  
  ‑ Leakage gate computes Spearman correlation between the label and a simple surface‑text‑similarity feature; if `|rho| ≥ 0.8` the `interpretable` flag is set `false`.  
  ‑ Each seed’s JSON records both baseline and augmented metrics (including negative deltas when they occur).  
  ‑ All required fields appear in `results.json` and validate against `contracts/results.schema.yaml`.

- [ ] T009 [P] [US3] **Statistical analysis with Bonferroni correction and associational framing**  
  *Script*: `src/eval/stats.py` (run via `src/cli/run_pipeline.py --stage stats`)  
  *Outputs*: updated `artifacts/eval/results.json` with a populated `downstream` block (fields `metric_name`, `baseline_mean`, `augmented_mean`, `delta`, `p_value`, `test_name`, `alpha: 0.025`, `interpretable`) and top‑level `framing: "associational"`.  
  *Verification*:  
  ‑ `results.json` validates against `contracts/results.schema.yaml`.  
  ‑ The paired test (t‑test or Wilcoxon, chosen after Shapiro‑Wilk) respects the Bonferroni‑corrected α = 0.025.  
  ‑ A sanity‑check note (`distillation_sanity_check.is_sanity_check_only: true`) is present.

- [ ] T010 [P] [US3] **Incremental‑value ablation and independence descriptive analysis**  
  *Script*: `src/eval/ablation.py` (run via `src/cli/run_pipeline.py --stage ablation --seeds 42,43,44,45,46,47,48,49,50,51`)  
  *Outputs*: additions to `artifacts/eval/results.json` – `ablation_incremental_value` block (`latent_only_mean`, `p_value_vs_baseline`, `independence_claim_supportable: false`) and `independence_descriptive` block (`mutual_information_bits`, `pearson_r`).  
  *Verification*:  
  ‑ The latent‑only arm is trained and evaluated per seed; its mean metric appears as `latent_only_mean`.  
  ‑ Mutual information (via `sklearn.metrics.mutual_info_score`) and Pearson‑r between predicted structural latents and text embeddings are computed and stored.  
  ‑ The `independence_claim_supportable` flag is `false` (as required by the amended spec).

- [ ] T011 [P] [US3] **Resource tracking and full‑pipeline reproducibility check**  
  *Script*: `src/cli/run_pipeline.py --full` (or the same driver used for the final run) records peak RAM via `psutil` and wall‑clock time for every stage into `artifacts/eval/resources.json`; it also writes `artifacts/eval/repro_check.md` documenting a second deterministic run (same seeds, same data) and confirming that `results.json` matches the first run within a tolerance of 1e‑6.  
  *Verification*:  
  ‑ `resources` block in `results.json` shows `peak_ram_gb ≤ 7` and `runtime_seconds ≤ 21 600`.  
  ‑ `repro_check.md` contains the observed second‑run values and the statement “deterministic re‑run verified”.  
  ‑ Unit test `src/tests/test_resources.py` asserts that the recorded RAM and time are within the limits.

- [ ] T012 [P] [US3] **Generate summary tables and figures from validated outputs**  
  *Script*: `src/eval/report.py` (run via `src/cli/run_pipeline.py --stage report`)  
  *Outputs*:  
    ‑ `figures/per_seed_downstream.png` (baseline vs. augmented metric per seed)  
    ‑ `figures/distillation_sanity.png` (MSE curves for student vs. random‑head)  
    ‑ `data/results/summary_table.md` (markdown table enumerating SC‑001 – SC‑007 outcomes, the sanity‑check downgrade note, and the scope‑limitation statement).  
  *Verification*:  
  ‑ Every numeric entry in the table/figures traces back to a field in `results.json`.  
  ‑ The scope‑limitation paragraph explicitly mentions the infeasibility of visual‑encoder latents and the use of deterministic structural features.  
  ‑ Unit test `src/tests/test_report.py` checks that the files exist and that the table contains all required SC columns.

- [ ] T013 [P] [US3] **Write methods/results account and paper‑stage handoff**  
  *Artifact*: `artifacts/report/final_report.md` (methods, results, limitations, and explicit “paper‑stage handoff” section).  
  *Updates*: `quickstart.md` is revised to include the single command that reproduces the full workflow:  

    ```bash
    python src/cli/run_pipeline.py --full
    ```  

  *Verification*:  
  ‑ Every referenced artifact (e.g., `results.json`, figures, tables) exists.  
  ‑ No numeric value appears without a provenance link to `results.json` or a figure.  
  ‑ Running the command from `quickstart.md` on a clean checkout reproduces all tests and artifacts described in the report (checked by an integration test `src/tests/test_full_pipeline.py`).

---

## Phase 3 – Reproducible results and paper handoff  

| Goal | Provide a concise, verifiable methods/results narrative and a deterministic handoff for the paper pipeline. |
|------|-----------------------------------------------------------------------------------------------|

- [ ] T014 [P] **Re‑run the documented full workflow from scratch to confirm end‑to‑end reproducibility**  
  *Command*: `python src/cli/run_pipeline.py --full` (as documented in `quickstart.md`).  
  *Verification*:  
  ‑ The run finishes without error, reproduces `artifacts/eval/results.json` identical to the previously committed version (hash match), and all verification tests pass.  
  ‑ The run logs (`artifacts/eval/run_log.txt`) contain timestamps and resource usage confirming compliance with SC‑004 and SC‑005.

- [ ] T015 [P] **Archive immutable artifacts for verification**  
  *Script*: `src/utils/archive_artifacts.py` – copies `results.json`, all checkpoint directories, figures, and tables into `artifacts/archive/<timestamp>/` and records a SHA‑256 manifest `artifacts/archive/manifest.json`.  
  *Verification*:  
  ‑ The manifest lists every archived file with its checksum.  
  ‑ A CI test `src/tests/test_archive.py` verifies that the manifest matches the actual files and that no file exceeds the size limits of the free‑tier runner.

---  

### Execution order (dependency graph)

`T001 → T002 → T003 → T004 → T005 → (T006 ‖ T007) → T008 → T009 → T010 → T011 → T012 → T013 → T014 → T015`

*Parallel* (`‖`) indicates tasks that can run independently after the data‑preparation steps but must both finish before downstream evaluation proceeds.

| Requirement | Task(s) | Primary artifact / command |
|-------------|---------|----------------------------|
| FR‑001 (structural latents) | T001‑T003 | `python src/cli/run_pipeline.py --smoke` |
| FR‑002, FR‑003 (distillation) | T006 | `src/cli/run_pipeline.py --stage distill …` |
| FR‑004 (augmented representation) | T008 | `artifacts/eval/downstream_{seed}.json` |
| FR‑005, FR‑006 (downstream evaluation & framing) | T008‑T009 | `artifacts/eval/results.json` |
| FR‑007 (data sufficiency) | T001‑T004 | `provenance_text.json` |
| FR‑008 (independence & ablation) | T010 | `ablation_incremental_value` block in `results.json` |
| FR‑009 (baseline per seed) | T007 | `artifacts/models/baseline_<seed>/` |
| SC‑001, SC‑004, SC‑005, SC‑007 (sanity, memory, runtime) | T006, T011 | `distill_summary.json`, `resources.json` |
| SC‑002, SC‑003 (statistical significance) | T008‑T009 | `downstream` block in `results.json` |
| SC‑006 (minimum rows) | T001‑T004 | `provenance_text.json` |

All tasks remain unchecked until their corresponding scripts and artifacts are produced and pass the verification steps described above.
