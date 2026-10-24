# Tasks: Do distilled visual layout features add predictive value beyond dense text features for the corpus overlap/CPU‑score label?

**Inputs**: `spec.md` (with amendments), `plan.md` (re‑plan v4), `data‑model.md`, contract schemas, and any existing artifacts.  
All tasks write only to project‑owned paths under `data/`, `artifacts/`, `src/`, or `figures/`.  
Tasks are ordered to respect data flow; each task lists the primary script/file it creates or modifies and the artefacts it must produce.

---

- [ ] T001 [P] [US1] **Download and validate the verified textual dataset**  
  *Script*: `src/data/download_text.py` (defines `TEXT_DATASET_URL`)  
  *Outputs*: `data/raw/mixsub_overlap.parquet`, `data/raw/provenance_text.json` (contains `dataset_url`, `sha256`, `n_rows`, `label_semantics`, `seeds`)  
  *Verification*:  
  ‑ The parquet file exists and its SHA‑256 matches the entry in `provenance_text.json`.  
  ‑ `provenance_text.json` includes all required fields and a non‑empty `dataset_url`.  
  ‑ Unit test `src/tests/test_download_text.py` asserts successful load via `pyarrow`, confirms `n_rows ≥ 1000`, and checks that an empty or unreachable `TEXT_DATASET_URL` exits with error code 1 and the message `VERIFIED DATASET URL MISSING/UNREACHABLE`.

- [ ] T002 [P] [US1] **Download and validate a verified visual‑layout dataset**  
  *Script*: `src/data/download_visual.py` (defines `VISUAL_DATASET_URL`) – a publicly‑available dataset containing page images and layout annotations (e.g., `[UNRESOLVED-CLAIM: https://huggingface.co/datasets/docvqa` — HTTP 404]).  
  *Outputs*: `data/raw/visual_pages.parquet`, `data/raw/provenance_visual.json` (contains `dataset_url`, `sha256`, `n_rows`, `has_layout_annotations`).  
  *Verification*:  
  ‑ File exists and checksum matches `provenance_visual.json`.  
  ‑ Validation script checks that at least 1000 rows have non‑null `layout_annotations`; otherwise exits with FR‑007 error `Insufficient pages with layout annotations`.  
  ‑ Unit test `src/tests/test_download_visual.py` covers success and failure paths.

- [ ] T003 [P] [US1] **Generate visual‑layout latents using a frozen visual encoder (CPU‑only)**  
  *Script*: `src/features/visual_latent.py` – loads a frozen CLIP visual encoder (`torchvision.models.clip_vit_b32(pretrained=True)`) in `torch.no_grad()` on CPU and computes a fixed‑dimensional embedding for each page image.  
  *Outputs*: `data/processed/document_pairs_with_visual_latent.parquet` (adds `visual_latent` column), `data/processed/visual_latent_provenance.json` (records `encoder_name`, `encoder_version`, `latent_dim`).  
  *Verification*:  
  ‑ Every row with a valid image has a `visual_latent` vector of dimension D.  
  ‑ Determinism test ensures identical input → identical latent.  
  ‑ Unit test `src/tests/test_visual_latent.py` confirms shape, dtype, and reproducibility.

- [ ] T004 [P] [US1] **Preprocess raw parquet into schema‑valid `DocumentPair` records**  
  *Script*: `src/data/preprocess.py` – merges the textual parquet (T001) and visual parquet (T002) on `doc_id`, validates against `documentpair.schema.yaml`, and writes `data/processed/document_pairs.parquet`.  
  *Outputs*: `data/processed/document_pairs.parquet`, `data/processed/preprocess_stats.json` (records `n_valid_rows` and rows removed).  
  *Verification*:  
  ‑ All rows validate against the schema.  
  ‑ If `n_valid_rows < 1000` the script aborts with FR‑007 error `Insufficient valid rows (found X, required ≥1000)`.  
  ‑ Unit tests `src/tests/test_preprocess.py` cover success and below‑minimum failure.

- [ ] T005 [P] [US2] **Create deterministic splits and run a thin end‑to‑end smoke analysis**  
  *Scripts*: `src/utils/split_generator.py` (writes splits), `src/cli/run_pipeline.py --smoke` (minimal ridge heads)  
  *Outputs*: `data/splits/splits.yaml`, `data/results/smoke_results.json`, updated `quickstart.md` with the command  

    ```bash
    python src/cli/run_pipeline.py --smoke
    ```  

  *Verification*:  
  ‑ `splits.yaml` exists and split sizes are within ±1 document of the 0.8/0.1/0.1 target ratios.  
  ‑ `smoke_results.json` contains real numeric metrics for both the text‑only and text ⊕ visual‑latent arms (no placeholders).  
  ‑ Executing the command from `quickstart.md` exits 0 and reproduces the same `smoke_results.json`.

- [ ] T006 [P] [US2] **Train the full DistilledModel (text → visual latent) across all required seeds**  
  *Script*: `src/models/distilled.py`, invoked via `src/cli/run_pipeline.py --stage distill --seeds 42,43,44,45,46,47,48,49,50,51` (full seed set matching the baseline seeds to satisfy FR‑009)  
  *Outputs*: checkpoints under `artifacts/models/distilled_<seed>/`, per‑seed eval files `artifacts/eval/distill_{seed}.json`, aggregated summary `artifacts/eval/distill_summary.json` (fields `mse_val_mean`, `mse_random_init_mean`, `p_value`, `test_name`, `alpha: 0.025`, `is_sanity_check_only: false`, `val_train_loss_ratio`).  
  *Verification*:  
  ‑ For each seed, `distill_{seed}.json` records `val_mse`, `train_mse`, `peak_ram_gb`, `runtime_s`.  
  ‑ The summary must show `p_value < 0.025` **and** `mse_val_mean < mse_random_init_mean`; otherwise the script exits with `distillation sanity check failed`.  
  ‑ Peak RAM ≤ 7 GB and total runtime ≤ 21 600 s (recorded in `resources.json`).

- [ ] T007 [P] [US3] **Train per‑seed re‑trained text‑only downstream baseline (matching the 10 seeds)**  
  *Script*: `src/models/baseline.py`, invoked via `src/cli/run_pipeline.py --stage baseline --seeds 42,43,44,45,46,47,48,49,50,51`  
  *Outputs*: checkpoints under `artifacts/models/baseline_<seed>/`, evaluation files `artifacts/eval/baseline_{seed}.json` (fields `val_metric`, `test_metric`, `peak_ram_gb`).  
  *Verification*:  
  ‑ Exactly ten baseline checkpoints exist, one per seed.  
  ‑ No OOM errors; `peak_ram_gb` ≤ 7 GB for each run.

- [ ] T008 [P] [US3] **Leakage pre‑check and downstream evaluation of augmented vs. baseline**  
  *Script*: `src/eval/downstream.py` (run via `src/cli/run_pipeline.py --stage downstream --seeds 42,43,44,45,46,47,48,49,50,51`)  
  *Outputs*: per‑seed downstream files `artifacts/eval/downstream_{seed}.json` (fields `metric_baseline`, `metric_augmented`, `delta`), and a consolidated `artifacts/eval/results.json` containing `label_semantics`, `leakage_check`, and the augmented predictions (visual latents concatenated with text embeddings).  
  *Verification*:  
  ‑ Leakage gate computes Spearman correlation between the label and a surface‑text‑similarity feature; if `|rho| ≥ 0.8` the `interpretable` flag is set false.  
  ‑ Each seed’s JSON records both baseline and augmented metrics (including negative deltas when they occur).  
  ‑ All required fields appear in `results.json`.

- [ ] T009 [P] [US3] **Statistical analysis with Bonferroni correction and associational framing**  
  *Script*: `src/eval/stats.py` (run via `src/cli/run_pipeline.py --stage stats`)  
  *Outputs*: updated `artifacts/eval/results.json` with a populated `downstream` block (fields `metric_name`, `baseline_mean`, `augmented_mean`, `delta`, `p_value`, `test_name`, `alpha: 0.025`, `interpretable`) and top‑level `framing: "associational"`.  
  *Verification*:  
  ‑ `results.json` validates against `results.schema.yaml`.  
  ‑ The paired test (t‑test or Wilcoxon) respects the Bonferroni‑corrected α = 0.025.

- [ ] T010 [P] [US2] **Incremental‑value ablation and independence analysis**  
  *Script*: `src/eval/ablation.py` (run via `src/cli/run_pipeline.py --stage ablation --seeds 42,43,44,45,46,47,48,49,50,51`)  
  *Outputs*: additions to `artifacts/eval/results.json` – `ablation_incremental_value` block (`latent_only_mean`, `p_value_vs_baseline`, `independence_claim_supportable: true`) and `independence_descriptive` block (`mutual_information_bits`, `pearson_r`).  
  *Verification*:  
  ‑ The latent‑only arm is trained and evaluated per seed; its mean metric appears as `latent_only_mean`.  
  ‑ Mutual information and Pearson‑r are computed between predicted visual latents and text embeddings and stored correctly.  
  ‑ Independence claim is marked supportable per FR‑008.

- [ ] T011 [P] [US3] **Resource tracking and full‑pipeline reproducibility check**  
  *Script*: `src/cli/run_pipeline.py --full` (or the same driver used for the final run) records peak RAM via `psutil` and wall‑clock time for every stage into `artifacts/eval/resources.json`; it also writes `artifacts/eval/repro_check.md` documenting a second deterministic run (same seeds, same data) and confirming that `results.json` matches the first run within a tolerance of 1e‑6.  
  *Verification*:  
  ‑ `resources` block in `results.json` shows `peak_ram_gb ≤ 7` and `runtime_seconds ≤ 21 600`.  
  ‑ `repro_check.md` contains the observed second‑run values and the statement “deterministic re‑run verified”.

- [ ] T012a [P] [US2] **Generate summary tables and figures from validated outputs**  
  *Script*: `src/eval/report.py` (run via `src/cli/run_pipeline.py --stage report`)  
  *Outputs*:  
    ‑ `figures/per_seed_downstream.png` (baseline vs. augmented metric per seed)  
    ‑ `figures/distillation_sanity.png` (MSE curves for student vs. random‑head)  
    ‑ `data/results/summary_table.md` (markdown table enumerating SC‑001 – SC‑007 outcomes, the sanity‑check downgrade note, and the scope‑limitation statement).  
  *Verification*:  
  ‑ Every numeric entry in the table/figures traces back to a field in `results.json`.  
  ‑ The scope‑limitation paragraph explicitly mentions the infeasibility of visual‑latent generation (now resolved) and the use of deterministic structural features where applicable.

- [ ] T012b [P] [US3] **Write methods/results account and paper‑stage handoff**  
  *Artifact*: `artifacts/report/final_report.md` (methods, results, limitations, and explicit “paper‑stage handoff” section).  
  *Updates*: `quickstart.md` is revised to include the single command that reproduces the full workflow:  

    ```bash
    python src/cli/run_pipeline.py --full
    ```  

  *Verification*:  
  ‑ Every referenced artifact (e.g., `results.json`, figures, tables) exists.  
  ‑ No numeric value appears without a provenance link to `results.json` or a figure.  
  ‑ Running the command from `quickstart.md` on a clean checkout reproduces all tests and artifacts described in the report.

---

### Execution order (dependency graph)

`T001 → T002 → T003 → T004 → T005 → (T006 ‖ T007) → T008 → T009 → T010 → T011 → T012a → T012b`

*Parallel* (`‖`) indicates tasks that can run independently after the data preparation steps but must both finish before downstream evaluation proceeds.

| Requirement | Task(s) | Primary artifact / command |
|-------------|---------|----------------------------|
| FR‑001 (visual latents) | T001‑T004 | `python src/cli/run_pipeline.py --smoke` |
| FR‑002, FR‑003 | T006 | `python src/cli/run_pipeline.py --stage distill --seeds 42,43,44,45,46,47,48,49,50,51` |
| FR‑004 (augmented) | T008 | `artifacts/eval/downstream_{seed}.json` |
| FR‑005, FR‑006 | T008‑T009 | `artifacts/eval/results.json` |
| FR‑007 (layout annotation minimum) | T002‑T004 | `provenance_visual.json` |
| FR‑008 (independence) | T010 | `ablation_incremental_value` block in `results.json` |
| FR‑009 (baseline per seed) | T007 | `artifacts/models/baseline_<seed>/` |
| SC‑001 (sanity), SC‑004, SC‑005, SC‑007 | T006, T011 | `distill_summary.json`, `resources.json` |
| SC‑002, SC‑003 (α = 0.025) | T008‑T009 | `downstream` block in `results.json` |
| SC‑006 (minimum = 1000) | T001‑T004 | `provenance_text.json` |

All tasks remain unchecked until their corresponding scripts and artifacts are produced and pass the verification steps described above.