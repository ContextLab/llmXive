# Tasks: llmXive follow‑up – extending “Scalable Visual Pretraining for Language Intelligence”

**Inputs**: `spec.md`, `plan.md`, existing source files, reviewer feedback (failed T001‑T013).  
The pipeline must run end‑to‑end on real data, stay within CPU‑only constraints (≤ 7 GB RAM, ≤ 6 h wall‑clock), and produce verifiable artifacts for every functional requirement (FR‑001 – FR‑009) and success criterion (SC‑001 – SC‑007).

---  

- [ ] **T001** [US‑1] Download primary and fallback scientific‑document corpora and verify sufficient annotated pages.   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  **Implementation**: `src/data/download.py` uses `datasets.load_dataset("allenai/pubmed-layout", streaming=False)`. If the filtered page count is lower than expected, it falls back to `datasets.load_dataset("allenai/pubmed-layout-fallback")`.  
  **Verification**:  
  - Compute SHA‑256 checksums of all cached files and store them in `artifacts/checksums/downloads.yaml`.  
  - After filtering for non‑empty `layout_annotations`, log the total `num_valid_pages`. If the count is unexpectedly low (below the spec‑defined minimum, which is currently a placeholder), emit a warning but do **not** enforce a hard numeric threshold.  
  - CI must see exit code 0 and the checksum file present.

- [ ] **T002** [US‑2] Preprocess the raw dataset into canonical `DocumentPair` records and write a Parquet table.  
  **Implementation**: `src/data/preprocess.py` reads the downloaded dataset (triggering a download if the data is missing), runs OCR via `pytesseract` where needed, pairs extracted text with layout boxes, and writes `data/processed/document_pairs.parquet`.  
  **Verification**:  
  - Validate every record against `contracts/documentpair.schema.yaml` with `jsonschema`.  
  - Pages missing `layout_annotations` are skipped; a warning is logged and must be ≤ 5 % of total pages.  
  - Unit test `tests/unit/test_preprocess.py` passes (Parquet file exists and schema‑valid).  

- [ ] **T003** [US‑3] Generate visual‑layout latents on CPU using a frozen **ResNet‑18** visual encoder.  
  **Implementation**: `src/data/latent_generator.py` first attempts to load `torchvision.models.resnet18(pretrained=True)` with `map_location="cpu"` inside `torch.no_grad()`. If the encoder fails to load, the script aborts with a clear error (no silent fallback). It then processes each `image_path` from `document_pairs.parquet`, extracts a 512‑dim latent, and appends it to each row, writing `data/processed/document_pairs_with_latent.parquet`. **If this file already exists, the script can be run in “verify‑only” mode to skip regeneration**, making the task independently testable.  
  **Verification**:  
  - Ensure the encoder loads successfully before any per‑document processing.  
  - Every row contains a `visual_latent` of length 512 with no NaNs.  
  - Total inference time for 10 000 pages ≤ 30 min on the CI runner (recorded in `artifacts/runtime/latent_inference_seconds.txt`).  
  - In “verify‑only” mode, confirm that `document_pairs_with_latent.parquet` exists and passes a schema check identical to the generation step.

- [ ] **T004** [US‑4] Create deterministic train/validation/test splits (seed = 42).  
  **Implementation**: `src/utils/split_generator.py` reads `document_pairs_with_latent.parquet` (or, if missing, falls back to `document_pairs.parquet` and aborts with a clear message) and writes three index files: `data/splits/train_idx.json`, `data/splits/val_idx.json`, `data/splits/test_idx.json` with ratios 0.8/0.1/0.1.  
  **Verification**:  
  - Re‑running the script produces byte‑identical JSON files (determinism).  
  - Split sizes respect the target ratios within ±1 document.  

- [ ] **T005** [US‑5] Train the DistilledModel (text → visual latent) for **3 seeds** (42‑44).  
  **Implementation**: `src/models/distilled.py` builds a pruned DistilBERT (~50 M parameters) with a linear projection head (768 → 512). Training uses MSE loss, AdamW (lr = 1e‑4), cosine LR scheduler, early‑stop patience = 3 on validation MSE. Checkpoints are saved under `artifacts/models/distilled_{seed}/`.  
  **Verification (per seed)**:  
  - Validation MSE is ≥ 5 % lower than the **random‑init baseline** recorded by **T005b** (paired t‑test, α = 0.025).  
  - Peak RAM ≤ 7 GB (measured via `psutil`).  
  - Wall‑clock ≤ 5 h (recorded in `artifacts/runtime/train_{seed}_seconds.txt`).  
  - Validation‑loss / training‑loss ≤ 2.0 (SC‑007).  

- [ ] **T005b** [US‑5‑baseline] Compute random‑init baseline MSE for each seed.  
  **Implementation**: `src/models/baseline_mse.py` loads an untrained DistilBERT with the same projection head, runs a single forward pass on the training split, and records the MSE against the true visual latents. Results are stored in `artifacts/baseline_mse/baseline_mse_{seed}.json`.  
  **Verification**:  
  - JSON file exists and contains a numeric `baseline_mse` field for each seed.  

- [ ] **T006** [US‑6] Train the text‑only baseline model for the same **3 seeds** using a **frozen random linear projection head** (capacity‑controlled).  
  **Implementation**: `src/models/baseline.py` re‑uses the same pruned DistilBERT architecture but adds a **randomly initialized linear projection (768 → 512) that is kept frozen**. Checkpoints are saved under `artifacts/models/baseline_{seed}/`.  
  **Verification (per seed)**:  
  - No OOM; peak RAM ≤ 7 GB.  
  - Final training loss is monotonically decreasing (asserted in `artifacts/logs/baseline_{seed}_loss.csv`).  

- [ ] **T007** [US‑7] Independence ablation: show that predicted latents contain information beyond the text encoder.  
  **Implementation**: `src/eval/independence_ablation.py` (for each seed)  
  1. Compute Mutual Information (MI) and Pearson r between predicted latents and the BERT `[CLS]` embeddings.  
  2. Assert MI < 0.1 bits and Pearson r < 0.3; otherwise emit a warning.  
  3. Train a **latent‑only** downstream classifier (using only the predicted visual latent) on the same downstream task and compare its accuracy/F1 to the text‑only baseline.  
  **Verification**:  
  - MI and Pearson thresholds are met; results written to `artifacts/eval/independence_summary.md`.  
  - Latent‑only model achieves ≥ 5 % above random and its performance difference vs. baseline is statistically significant (paired test, α = 0.05).  

- [ ] **T008** [US‑8] Downstream evaluation on DocVQA (augmented vs. baseline) across all seeds.  
  **Implementation**: `src/eval/downstream.py` (per seed)  
  1. Load the distilled checkpoint, generate predicted latents for the test split.  
  2. Concatenate each predicted latent with the BERT `[CLS]` embedding → 1280‑dim vector.  
  3. Fine‑tune a lightweight linear classifier on the training split.  
  4. Repeat steps 1‑3 for the baseline model (re‑trained per seed).  
  5. Compute Exact Match (EM) and F1 on the held‑out test set.  
  **Verification (per seed)**:  
  - Write `artifacts/eval/downstream_{seed}.json` containing `accuracy_baseline`, `accuracy_augmented`, `f1_baseline`, `f1_augmented`.  
  - After all seeds, run a paired t‑test (or Wilcoxon if Shapiro‑Wilk p < 0.05) on the accuracy deltas; require p < 0.05 (fulfills FR‑005 & FR‑006).  
  - Record the test statistic and p‑value in `artifacts/eval/downstream_summary.md`.  

- [ ] **T009** [US‑9] Compile the final evaluation report.  
  **Implementation**: `artifacts/report/final_report.md` aggregates:  
  * SC‑001 (validation MSE improvement),  
  * SC‑002 & SC‑003 (downstream accuracy/F1 and statistical significance),  
  * SC‑004 & SC‑005 (peak RAM and total runtime),  
  * SC‑006 (page‑count check),  
  * SC‑007 (loss‑ratio check),  
  * Independence ablation results (MI, Pearson r, latent‑only performance).  
  The report explicitly frames any performance gains as *associational* (FR‑006) and cites the exact artifact files for every number.  
  **Verification**: CI parses the markdown, checks that every cited file exists, and confirms that no numeric value is hard‑coded without a provenance comment.  

- [ ] **T010** [US‑10] Compute SHA‑256 checksums of every generated artifact and record them in the project state file.  
  **Implementation**: `src/utils/checksum.py` walks `data/processed/`, `artifacts/models/`, `artifacts/eval/`, `artifacts/report/` and writes entries to `state/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis.yaml`.  
  **Verification**: CI step compares current hashes to the stored ones; any mismatch triggers failure.  

- [ ] **T011** [US‑11] End‑to‑end smoke test on a 100‑document sample.  
  **Implementation**: `src/cli/run_pipeline.py --sample-size 100` executes the full workflow (download → preprocess → latent generation → one seed of distillation & baseline → downstream evaluation) on a tiny subset.  
  **Verification**:  
  - CI runs the command and expects exit 0 within 30 min.  
  - Produces `data/results/sample_output.parquet` containing `doc_id`, `predicted_latent`, `baseline_pred`, `augmented_pred`.  
  - All unit tests in `tests/` pass.  

- [ ] **T012** [US‑12] Enforce the 6‑hour wall‑clock limit for the full pipeline.  
  **Implementation**: Wrapper in `src/cli/run_pipeline.py` records start/end timestamps to `artifacts/runtime/runtime_seconds.txt`.  
  **Verification**: CI fails if the recorded total duration exceeds 21 600 seconds (6 h) **or** if any individual seed exceeds 21 600 seconds.  

- [ ] **T013** [US‑13] Verify training‑vs‑validation loss ratio ≤ 2.0 across all seeds and produce a summary.  
  **Implementation**: `src/eval/loss_ratio.py` aggregates `train_loss.csv` and `val_loss.csv` from each seed, computes `val_loss / train_loss` per seed, asserts ≤ 2.0, and writes `artifacts/eval/loss_ratio_summary.md`.  
  **Verification**: CI parses the summary; any ratio > 2.0 triggers failure (SC‑007).  

---  

### Mapping of tasks to functional requirements & success criteria  

| FR | Covered by |
|----|-------------|
| FR‑001 | T001, T002, T003 |
| FR‑002 | T005 |
| FR‑003 | T005, T006 (RAM checks) |
| FR‑004 | T008 (concatenation) |
| FR‑005 | T008 |
| FR‑006 | T009 (report framing) |
| FR‑007 | T001 (page‑count check) |
| FR‑008 | T007 |
| FR‑009 | T006 (baseline re‑trained per seed) |

| SC | Covered by |
|----|-------------|
| SC‑001 | T005 (MSE improvement) |
| SC‑002 | T008 (accuracy/F1) |
| SC‑003 | T008 (paired test p‑value) |
| SC‑004 | T005, T006 (RAM measurement) |
| SC‑005 | T012 (total runtime) |
| SC‑006 | T001 (page‑count logging) |
| SC‑007 | T005 (loss‑ratio) & T013 (aggregate verification) |

*All tasks are presently unchecked; they will be automatically marked complete by the CI pipeline once their verification steps succeed.*  