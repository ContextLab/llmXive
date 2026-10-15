# Tasks: llmXive follow‑up – extending “Scalable Visual Pretraining for Language Intelligence”

**Inputs**: `spec.md`, `plan.md`, existing source files, reviewer feedback (failed T001).  
**Goal**: Implement a fully reproducible CPU‑only pipeline that (1) downloads real scientific document data, (2) generates visual‑layout latents with a frozen encoder, (3) trains a text‑to‑visual DistilledModel and a matched baseline, (4) evaluates both on a downstream reasoning benchmark, and (5) records all evidence for independent verification.

---

## Phase 1 – Data acquisition, preprocessing, and latent generation  

- [ ] **T001** Download primary and fallback corpora from verified HuggingFace URLs and verify integrity.   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1; src/data/preprocess.py exit=1; src/data/latent_generator.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=2 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  - **Implementation**: `src/data/download.py` uses `datasets.load_dataset("allenai/pubmed-layout", streaming=False, download_mode="force_redownload")` for the primary PubLayNet subset and, if the post‑filter page count is < 10 000, falls back to `datasets.load_dataset("allenai/pubmed-layout-fallback")`.  
  - **Verification**:  
    - Compute SHA‑256 checksums of each cached file produced by the dataset download (found under `~/.cache/huggingface/datasets/...`) and store them in `artifacts/checksums/downloads.yaml`.  
    - After filtering for pages with non‑empty `layout_annotations`, assert `num_valid_pages >= 10_000`; otherwise raise a clear `RuntimeError` with message “Insufficient annotated pages (FR‑007)”.  
    - CI must show exit code 0; previous failure (`exit=2`) is resolved.

- [ ] **T002** Preprocess raw files into canonical `DocumentPair` records and write a Parquet table.  
  - **Implementation**: `src/data/preprocess.py` reads the downloaded dataset, runs OCR via Tesseract (`pytesseract`), pairs extracted text with layout boxes, and writes `data/processed/document_pairs.parquet`.  
  - **Verification**:  
    - Validate each record against `contracts/documentpair.schema.yaml` using `jsonschema`.  
    - Skip pages lacking `layout_annotations`; emit a warning and count them (must be ≤ 5 % of total).  
    - Unit test `tests/contract/test_documentpair.py` must pass.  

- [ ] **T003** Generate visual‑layout latents on CPU using the frozen `layoutlmv3‑base` encoder.   <!-- FAILED-IN-EXECUTION: src/data/latent_generator.py exit=1 -->
  - **Implementation**: `src/data/latent_generator.py` loads `layoutlmv3-base` with `torch.load(..., map_location="cpu")` inside `torch.no_grad()`, processes `image_path` from the Parquet file, and appends a `visual_latent` (768‑dim `float32` array) to each row, writing `data/processed/document_pairs_with_latent.parquet`.  
  - **Verification**:  
    - Every row contains a `visual_latent` of length 768 with no NaNs.  
    - Total inference time for 10 000 pages ≤ 30 min on the CI runner (recorded in `artifacts/runtime/latent_inference_seconds.txt`).  
    - If the encoder cannot be loaded on CPU, the script aborts with a clear error “Frozen visual encoder cannot be loaded on CPU – incompatibility”, satisfying the edge‑case requirement.  

- [ ] **T004** Create deterministic train/validation/test splits (seed = 42).  
  - **Implementation**: `src/utils/split_generator.py` reads `document_pairs_with_latent.parquet` and writes three index files: `data/splits/train_idx.json`, `val_idx.json`, `test_idx.json` with ratios 0.8/0.1/0.1.  
  - **Verification**:  
    - Re‑running the script produces byte‑identical JSON files (determinism).  
    - Split sizes respect the ratios within ±1 document.  

---

## Phase 2 – Model training, baseline, and ablation  

- [ ] **T005** Train the DistilledModel (text → visual latent) for 15 seeds (42‑56).  
  - **Implementation**: `src/models/distilled.py` builds a pruned DistilBERT (≈50 M parameters) with a linear projection head (768 → 768). Training uses MSE loss, AdamW (lr = 1e‑4), cosine LR scheduler, early‑stop patience = 3 on validation MSE. Checkpoints saved under `artifacts/models/distilled_{seed}/`.  
  - **Verification (per seed)**:  
    - Validation MSE is ≥ 5 % lower than a random‑init baseline (paired t‑test, α = 0.025).  
    - Peak RAM ≤ 7 GB (monitored via `psutil`).  
    - Training wall‑clock ≤ 5 h (recorded in `artifacts/runtime/train_{seed}_seconds.txt`).  
    - Validation loss / training loss ≤ 2.0 (SC‑007).  

- [ ] **T006** Train the text‑only baseline model for the same 15 seeds.  
  - **Implementation**: `src/models/baseline.py` re‑uses the same pruned DistilBERT architecture **without** the projection head. Checkpoints saved under `artifacts/models/baseline_{seed}/`.  
  - **Verification (per seed)**:  
    - No OOM; peak RAM ≤ 7 GB.  
    - Final training loss is monotonically decreasing (asserted in `logs/baseline_{seed}_loss.csv`).  

- [ ] **T007** Perform an ablation demonstrating that predicted visual latents contain information independent of the text‑only encoder (FR‑008).  
  **Implementation**: `src/eval/independence_ablation.py`  
    1. For each seed, compute Mutual Information (MI) and Pearson r between the predicted latents and the BERT `[CLS]` embeddings of the same documents.  
    2. Assert MI < 0.1 bits and Pearson r < 0.3; otherwise log a warning.  
    3. Train a **latent‑only** downstream model (using only the predicted visual latent, no text) on the same downstream task and compare its performance to the text‑only baseline.  
  - **Verification**:  
    - MI and Pearson thresholds are met; results written to `artifacts/eval/independence_summary.md`.  
    - Latent‑only model achieves a non‑trivial accuracy/F1 (≥ 5 % above random) and the performance difference vs. baseline is statistically significant (paired test, α = 0.05).  

---

## Phase 3 – Downstream reasoning evaluation  

- [ ] **T008** Evaluate augmented vs. baseline models on the DocVQA benchmark (mandatory downstream task).  
  - **Implementation**: `src/eval/downstream.py` for each seed:  
    1. Load the distilled checkpoint, generate predicted latents for the test split.  
    2. Concatenate each predicted latent with the BERT `[CLS]` embedding → 1536‑dim vector.  
    3. Fine‑tune a lightweight linear classifier on the training split.  
    4. Repeat steps 1‑3 for the baseline model (re‑trained per seed).  
    5. Compute Exact Match (EM) and F1 on the held‑out test set.  
  - **Verification (per seed)**:  
    - Write `artifacts/eval/downstream_{seed}.json` containing `accuracy_baseline`, `accuracy_augmented`, `f1_baseline`, `f1_augmented`.  
    - After all seeds, run a paired t‑test (or Wilcoxon if Shapiro‑Wilk p < 0.05) on the accuracy deltas; require p < 0.05 (FR‑005 & FR‑006).  
    - Record the test statistic and p‑value in `artifacts/eval/downstream_summary.md`.  

- [ ] **T009** Compile the final evaluation report.  
  - **Implementation**: `artifacts/report/final_report.md` aggregates:  
    * SC‑001 (validation MSE improvement),  
    * SC‑002 & SC‑003 (downstream accuracy/F1 and statistical significance),  
    * SC‑004 & SC‑005 (peak RAM and total runtime),  
    * SC‑006 (page‑count check),  
    * SC‑007 (loss‑ratio check),  
    * Independence ablation results (MI, Pearson r, latent‑only performance).  
  - **Verification**:  
    - The report explicitly frames any performance gains as *associational* (FR‑006).  
    - All numeric values are sourced from the artifacts produced in earlier tasks; no fabricated numbers.  

---

## Phase 4 – Reproducibility, logging, and end‑to‑end sanity check  

- [ ] **T011** Compute SHA‑256 checksums of every generated artifact and write them to the project state file.  
  - **Implementation**: `src/utils/checksum.py` walks `data/processed/`, `artifacts/models/`, `artifacts/eval/`, and writes entries to `state/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis.yaml`.  
  - **Verification**: CI step compares current hashes to the stored ones; mismatch causes failure.  

- [ ] **T012** End‑to‑end smoke test on a 100‑document sample.  
  - **Implementation**: `src/cli/run_pipeline.py --sample-size 100` executes the full workflow (download → preprocess → latent generation → one seed of distillation & baseline → downstream evaluation) on a tiny subset.  
  - **Verification**:  
    - CI runs the command and expects exit 0 within 30 min.  
    - Produces `data/results/sample_output.parquet` containing `doc_id`, `predicted_latent`, `baseline_pred`, `augmented_pred`.  
    - All unit tests in `tests/` pass.  

- [ ] **T013** Measure total pipeline runtime and enforce the 6‑hour wall‑clock limit.  
  - **Implementation**: Wrapper in `src/cli/run_pipeline.py` records start/end timestamps to `artifacts/runtime/runtime_seconds.txt`.  
  - **Verification**: CI fails if the recorded duration exceeds 21 600 seconds (SC‑005).  

- [ ] **T014** Validate validation‑vs‑training loss ratio across all seeds and produce a summary.  
  - **Implementation**: `src/eval/loss_ratio.py` aggregates `train_loss.csv` and `val_loss.csv` from each seed, computes `val_loss / train_loss` per seed, asserts ≤ 2.0, and writes `artifacts/eval/loss_ratio_summary.md`.  
  - **Verification**: CI step parses the summary; any ratio > 2.0 triggers failure (SC‑007).  

---

### Mapping of tasks to functional & success criteria  

| Functional Requirement | Covered by |
|------------------------|------------|
| FR‑001 | T001, T002, T003 |
| FR‑002 | T005 |
| FR‑003 | T005, T006 (RAM checks) |
| FR‑004 | T008 (concatenation) |
| FR‑005 | T008 |
| FR‑006 | T009 (report framing) |
| FR‑007 | T001 (page‑count abort) |
| FR‑008 | T007 (independence ablation) |
| FR‑009 | T006 (baseline re‑trained per seed) |

| Success Criterion | Covered by |
|-------------------|------------|
| SC‑001 | T005 (MSE improvement) |
| SC‑002 | T008 (accuracy/F1) |
| SC‑003 | T008 (paired test p‑value) |
| SC‑004 | T005, T006 (RAM measurement) |
| SC‑005 | T013 (total runtime) |
| SC‑006 | T001 (page‑count) |
| SC‑007 | T005 (loss‑ratio) & T014 (aggregate verification) |

*All tasks are currently unchecked. They will be marked complete automatically by the CI pipeline once their verification steps succeed.*  