# Tasks: Do distilled structural text features add predictive value beyond dense text features for the corpus overlap/CPU‑score label?

**Inputs**: `spec.md` (amendments pending), `plan.md` (re‑plan v3), `data‑model.md`, contract schemas, prior execution failures (T001/T002).  
**Scope note**: The original visual‑encoder mechanism is not executable; the study uses deterministic structural features of text as distillation targets, evaluates incremental predictive value against a per‑seed re‑trained text‑only baseline, and frames all findings associationally (FR‑006). All tasks write only to project‑owned paths under `data/`, `artifacts/`, `src/`, or `figures/`.

## Phase 1 – Setup and first end‑to‑end analysis

- [ ] T001 [P] [US1] **Download and validate the verified dataset**  
  *Implementation*: `src/data/download.py` defines `DATASET_URL` (the concrete URL from the plan’s verified‑datasets block). The script downloads the parquet to `data/raw/mixsub_overlap.parquet`, computes its SHA‑256, and writes provenance metadata to `data/raw/provenance.json` (including `dataset_url`, `sha256`, `n_rows`, `label_semantics`, `min_valid_rows: 1000`, `seeds: [42,43,44]`).  
  *Verification*:  
  ‑ `data/raw/mixsub_overlap.parquet` exists and its SHA‑256 matches the entry in `provenance.json`.  
  ‑ `provenance.json` contains the required fields and a non‑empty `dataset_url`.  
  ‑ Unit test `src/tests/test_download.py` asserts successful load via `pyarrow`, checks that `n_rows ≥ 1000`, and verifies that an empty or unreachable `DATASET_URL` exits with error code 1 and message `VERIFIED DATASET URL MISSING/UNREACHABLE`.

- [ ] T002 [P] [US1] **Preprocess raw parquet into schema‑valid `DocumentPair` records**  
  *Implementation*: `src/data/preprocess.py` reads `data/raw/mixsub_overlap.parquet`, validates each row against `specs/001-llmxive-follow-up-extending-scalable-vis/contracts/documentpair.schema.yaml` (using `jsonschema`), assigns a unique `doc_id`, copies `source_url` from provenance, records `row_index`, and drops rows with empty `text` (logging a warning). The cleaned set is written to `data/processed/document_pairs.parquet`. A summary `data/processed/preprocess_stats.json` records `n_valid_rows` and any rows removed.  
  *Verification*:  
  ‑ All rows in `document_pairs.parquet` pass the `DocumentPair` schema.  
  ‑ If `n_valid_rows < 1000` the script aborts with FR‑007 error message: `Insufficient valid rows (found X, required ≥1000)`.  
  ‑ Unit test `src/tests/test_preprocess.py` covers the success path and the below‑minimum failure path.

- [ ] T003 [P] [US1] **Deterministic structural‑feature extractor with non‑degeneracy gate**  
  *Implementation*: `src/features/structure.py` computes a fixed‑dimension vector per document from plain text (line‑count stats, line‑length distribution, whitespace/punctuation ratios, token‑length histogram, indentation patterns). After computing the full feature matrix, a degeneracy check evaluates per‑feature variance; if primary line‑structure features are near‑constant, the fallback set (whitespace/punctuation/token‑length) is used. If both sets are degenerate the script aborts with a clear “structural target degeneracy” error. Successful output is `data/processed/document_pairs_with_latent.parquet` (adds `structural_latent` column) and a gate report `data/processed/degeneracy_report.json`.  
  *Verification*:  
  ‑ `degeneracy_report.json` contains `passed`, `fallback_used`, `min_feature_variance`, `n_near_constant_features`.  
  ‑ Every row has a `structural_latent` vector of dimension D (recorded in `provenance.json`).  
  ‑ Unit tests `src/tests/test_structure.py` verify determinism (identical input → identical vector) and correct gate logic.

- [ ] T004 [P] [US2] **Generate deterministic splits, author quickstart, and run a thin end‑to‑end smoke analysis**  
  *Implementation*:  
  ‑ `src/utils/split_generator.py` reads `data/processed/document_pairs_with_latent.parquet` and writes deterministic splits (`data/splits/splits.yaml`) with ratios 0.8/0.1/0.1 using seed 42.  
  ‑ `src/cli/run_pipeline.py --smoke` loads the splits, extracts TF‑IDF text features, fits a minimal ridge head on the train split for two arms (text‑only and text ⊕ structural latent), and writes `data/results/smoke_results.json` containing numeric metrics for both arms.  
  ‑ `quickstart.md` (created/updated by this task) documents the runnable command:  

    ```bash
    python src/cli/run_pipeline.py --smoke
    ```  

  *Verification*:  
  ‑ `splits.yaml` exists and split sizes are within ±1 document of the target ratios.  
  ‑ `smoke_results.json` contains real numeric metrics for both arms (no placeholders).  
  ‑ Executing the command from `quickstart.md` exits 0 and reproduces the same `smoke_results.json`.

## Phase 2 – Complete the study and validate its evidence

- [ ] T005 [P] [US2] **Train the distillation student (text → structural latent) – sanity‑check only**  
  *Implementation*: `src/models/distilled.py` trains a compact CPU‑tractable MLP (input = TF‑IDF of `text`, output = structural latent) using MSE loss on the train split. Invocation via the driver:  

    ```bash
    python src/cli/run_pipeline.py --stage distill --seeds 42,43,44
    ```  

  The script also trains a frozen‑random‑head baseline (same architecture, random weights) in parallel. Checkpoints are stored under `artifacts/models/distilled_<seed>/`.  
  *Verification*:  
  ‑ For each seed, `artifacts/eval/distill_{seed}.json` records `val_mse`, `train_mse`, `peak_ram_gb`, `runtime_s`.  
  ‑ Aggregated `artifacts/eval/distill_summary.json` includes `mse_val_mean`, `mse_random_init_mean`, `p_value`, `test_name`, `alpha: 0.025`, and `is_sanity_check_only: true`.  
  ‑ A paired test across the three seeds must satisfy `p_value < 0.025` **and** `mse_val_mean < mse_random_init_mean`; otherwise the script exits with `distillation sanity check failed`.  
  ‑ Peak RAM ≤ 7 GB and total runtime ≤ 21 600 s (recorded in `resources.json`).

- [ ] T006 [P] [US3] **Train per‑seed re‑trained text‑only downstream baseline**  
  *Implementation*: `src/models/baseline.py` builds a text‑only model (hashed n‑gram TF‑IDF + ridge regression head) and trains it independently for each seed in `[42, 43, 44]`. Checkpoints go to `artifacts/models/baseline_<seed>/`.  
  *Verification*:  
  ‑ For each seed, `artifacts/eval/baseline_{seed}.json` contains `val_metric` and `test_metric`.  
  ‑ No OOM errors; `peak_ram_gb` ≤ 7 GB.  
  ‑ Exactly three baseline checkpoints exist.

- [ ] T007 [P] [US3] **Leakage pre‑check and downstream evaluation of augmented vs. baseline**  
  *Implementation*: `src/eval/downstream.py` first computes the Spearman correlation between the label and a surface‑text‑similarity feature (cosine similarity of TF‑IDF vectors). If `|rho| ≥ 0.95` (pre‑registered `LEAKAGE_THRESHOLD`), `is_trivial_function_of_text` is set true and the downstream delta is marked uninterpretable. Otherwise, for each seed:  
    1. Predict structural latents with the distilled student (T005).  
    2. Concatenate the predicted latent to a frozen sentence‑transformer text embedding.  
    3. Train a downstream ridge head on the augmented representation and evaluate on the test split.  
    4. Compare against the per‑seed baseline from T006.  
  Results are written to `artifacts/eval/downstream_{seed}.json`.  
  *Verification*:  
  ‑ `label_semantics` and `leakage_check` blocks are populated in `artifacts/eval/results.json`.  
  ‑ Each downstream JSON contains `metric_baseline`, `metric_augmented`, `delta`.  
  ‑ Negative deltas are retained with their p‑values.

- [ ] T008 [P] [US3] **Statistical analysis with Bonferroni correction and associational framing**  
  *Implementation*: `src/eval/stats.py` reads the per‑seed downstream results, performs a paired t‑test (or Wilcoxon if normality fails) across the three seeds, applies a Bonferroni‑corrected α = 0.025, and writes the consolidated `downstream` block in `artifacts/eval/results.json`. The script also records `framing: "associational"` and sets `interpretable` based on the leakage gate.  
  *Verification*:  
  ‑ `results.json` validates against `specs/001-llmxive-follow-up-extending-scalable-vis/contracts/results.schema.yaml`.  
  ‑ Fields `metric_name`, `baseline_mean`, `augmented_mean`, `delta`, `p_value`, `test_name`, `alpha`, `interpretable` are present and numeric where required.

- [ ] T009 [P] [US2] **Incremental‑value ablation and descriptive collinearity analysis**  
  *Implementation*: `src/eval/ablation.py` trains a latent‑only downstream arm (using only the predicted structural latent) for each seed, compares its metric to the text‑only baseline, and computes mutual information (bits) and Pearson r between predicted latents and text embeddings. Results are added to `results.json` under `ablation_incremental_value` and `independence_descriptive`. The `independence_claim_supportable` flag is set to `false` per the reframed FR‑008.  
  *Verification*:  
  ‑ `ablation_incremental_value` block contains `latent_only_mean`, `p_value_vs_baseline`, `independence_claim_supportable: false`.  
  ‑ `independence_descriptive` block contains `mutual_information_bits` and `pearson_r`.

- [ ] T010 [P] [US3] **Resource tracking and full‑pipeline reproducibility check**  
  *Implementation*: The pipeline driver (`src/cli/run_pipeline.py`) records peak RAM (via `psutil`) and wall‑clock time for every stage into `artifacts/eval/resources.json`. It also writes `artifacts/eval/repro_check.md` documenting a second full run (same seeds, same data) and confirming that `results.json` matches the first run within a tolerance of 1e‑6.  
  *Verification*:  
  ‑ `resources` block in `results.json` shows `peak_ram_gb ≤ 7` and `runtime_seconds ≤ 21 600`.  
  ‑ `repro_check.md` contains the observed second‑run values and a statement “deterministic re‑run verified”.

## Phase 3 – Reproducible results and paper handoff

- [ ] T011 [P] [US3] **Generate summary tables and figures from validated outputs**  
  *Implementation*: `src/eval/report.py` reads `artifacts/eval/results.json` and produces:  
    • `figures/per_seed_downstream.png` (baseline vs. augmented metric per seed)  
    • `figures/distillation_sanity.png` (MSE curves for student vs. random‑head)  
    • `data/results/summary_table.md` (markdown table enumerating SC‑001 – SC‑007 outcomes, sanity‑check downgrade note, and scope‑limitation statement).  
  *Verification*:  
  ‑ Every numeric entry in the table/figures traces back to a field in `results.json`.  
  ‑ The scope‑limitation paragraph explicitly mentions the infeasibility of visual‑latent generation and the use of deterministic structural features.

- [ ] T012 [P] [US3] **Write methods/results account and paper‑stage handoff**  
  *Implementation*: `artifacts/report/final_report.md` documents:  
    1. The reframed research question and why the original visual‑encoder approach was un‑executable.  
    2. Detailed methods (data download, preprocessing, structural‑feature extraction, student training, baseline training, leakage gate, downstream evaluation, statistical analysis, ablation, resource tracking).  
    3. All results with explicit citations to artifact files (`results.json`, figures, tables).  
    4. Limitations (sanity‑check nature of distillation, collinearity, fixed seed count, associational framing).  
    5. A clear “paper‑stage handoff” section pointing to `figures/`, `data/results/`, and the repository location for the manuscript‑preparation pipeline.  
    The `quickstart.md` is updated to include the single command that reproduces the full workflow:  

    ```bash
    python src/cli/run_pipeline.py --full
    ```  

  *Verification*:  
  ‑ Every referenced artifact exists.  
  ‑ No numeric value appears without a provenance link to `results.json` or a figure.  
  ‑ Running the command from `quickstart.md` on a clean checkout reproduces all tests and artifacts.

---

### Execution order (dependency graph)

`T001 → T002 → T003 → T004 → (T005 ‖ T006) → T007 → T008 → T009 → T010 → T011 → T012`

*Parallel* (`‖`) indicates tasks that do not depend on each other but must both finish before the next stage.

| Requirement | Task(s) | Primary artifact / command |
|-------------|---------|----------------------------|
| FR‑001 (reframed: structural targets) | T001‑T003 | `python src/cli/run_pipeline.py --smoke` |
| FR‑002, FR‑003 | T005 | `python src/cli/run_pipeline.py --stage distill --seeds 42,43,44` |
| FR‑004 (reframed) | T007 | `artifacts/eval/downstream_{seed}.json` |
| FR‑005 (reframed), FR‑006 | T007‑T008 | `artifacts/eval/results.json` |
| FR‑007 (minimum 1000 valid rows) | T001‑T002 | `provenance.json` |
| FR‑008 (reframed: incremental value) | T009 | `ablation_incremental_value` block in `results.json` |
| FR‑009 | T006 | `artifacts/models/baseline_<seed>/` |
| SC‑001 (sanity), SC‑004, SC‑005, SC‑007 | T005, T010 | `distill_summary.json`, `resources.json` |
| SC‑002, SC‑003 (α = 0.025) | T007‑T008 | `downstream` block in `results.json` |
| SC‑006 (minimum = 1000) | T001‑T002 | `provenance.json` |

All tasks remain unchecked until their corresponding scripts and artifacts are produced and pass the verification steps described above.
