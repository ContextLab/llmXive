# tasks.md

**Project:** llmXive follow‑up: extending “Scalable Visual Pretraining for Language Intelligence”  
**Branch:** `001-llmxive-layout-distillation`  
**Generated:** 2026‑10‑10  

---  

## Phase 1 – Data acquisition & latent generation  

- [ ] **T001** [US1] **Download primary and fallback corpora** – implement `src/data/download.py` to fetch the DocBank subset and, if needed, the `pubmed‑layout` fallback from their verified HuggingFace URLs.   <!-- FAILED-IN-EXECUTION: src/data/download.py exit=2 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/run_download.sh exit=2 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 --> <!-- FAILED-IN-EXECUTION: src/data/download.py exit=1 -->
  - **Verification:**  
    - After download, count pages with layout annotations; abort with clear error if total < 10 000 (satisfies FR‑001 & FR‑007).  
    - Log the SHA‑256 checksum of each downloaded archive.  

- [ ] **T002** [US1] **Preprocess raw files into `DocumentPair` records** – implement `src/data/preprocess.py` to read the raw PDFs/JSON, extract OCR text, pair with layout annotations, and write a Parquet file `data/processed/document_pairs.parquet`.  
  - **Verification:**  
    - Validate each record against `contracts/documentpair.schema.yaml` using `jsonschema`.  
    - Skip pages lacking `layout_annotations`, emit a warning, and ensure the warning count is recorded.  
    - Ensure the output file passes schema validation (`pytest -k test_preprocess`).  

- [ ] **T003** [US1] **Generate visual‑layout latents on CPU** – implement `src/data/latent_generator.py` to load the frozen `layoutlmv3‑base` checkpoint on `device="cpu"` and produce a 768‑dimensional latent for every `DocumentPair`. Store results in `data/processed/document_pairs_with_latent.parquet`.  
  - **Verification:**  
    - Every row contains a `visual_latent` array of length 768, no NaNs.  
    - Total inference time for 10 000 pages < 30 min on the CI runner.  
    - If the encoder cannot be loaded on CPU, exit with an informative error (edge‑case handling).  

---  

## Phase 2 – Train/validation split  

- [ ] **T004** [US2] **Create deterministic train/val/test splits** – implement `src/utils/split_generator.py` to read `document_pairs_with_latent.parquet`, generate index files `data/splits/train_idx.json`, `val_idx.json`, `test_idx.json` using seed = 42 and ratios 0.8/0.1/0.1.  
  - **Verification:**  
    - Re‑run the script; the three JSON files are byte‑identical (determinism).  
    - The counts respect the specified ratios (within ±1 document).  

---  

## Phase 3 – Distillation & baseline model training (15 seeds)  

- [ ] **T005** [US2] **Train DistilledModel (text → visual latent)** – implement `src/models/distilled.py` to train a **50 M‑parameter** DistilledModel (e.g., full‑size DistilBERT with a projection head) using MSE loss against the frozen latents. Run for seeds 42‑56, saving checkpoints under `artifacts/models/distilled_{seed}/`.  
  - **Verification (per seed):**  
    - Validation MSE ≥ 5 % lower than a random‑init baseline (paired t‑test, α = 0.025).  
    - **SC‑007 check:** validation loss must not exceed **2 ×** training loss; fail otherwise.  
    - Peak RAM usage ≤ 7 GB (monitored via `psutil`).  
    - Training wall‑clock time ≤ 5 h (leaves margin for the 6‑h overall limit).  
    - Early‑stop patience = 3 epochs on validation MSE.  

- [ ] **T006** [US2] **Train text‑only baseline model** – implement `src/models/baseline.py` using the same pruned DistilBERT architecture **without** the projection head. Train for the same 15 seeds, saving under `artifacts/models/baseline_{seed}/`.  
  - **Verification (per seed):**  
    - Training completes without OOM; peak RAM ≤ 7 GB.  
    - Record final training loss; ensure loss curve is monotonic decreasing.  

---  

## Phase 4 – Ablation & latent‑layout fidelity  

- [ ] **T007** [US2] **Ablation: correlate latent distance with layout similarity** – implement `src/eval/ablation.py` to (a) compute Euclidean distance between predicted and frozen latents for a random sample of 500 documents, (b) compute IoU of their layout boxes, and (c) report Pearson r.  
  - **Verification:**  
    - Pearson correlation coefficient ≥ 0.5 (indicating MSE is a meaningful proxy).  
    - Output a CSV `artifacts/eval/ablation_correlation.csv` and a short markdown summary.  

---  

## Phase 5 – Downstream reasoning evaluation  

- [ ] **T008** [US3] **Evaluate augmented vs. baseline on downstream benchmark** – implement `src/eval/downstream.py` to (a) load each distilled checkpoint, generate predicted latents for the test split, concatenate them with the text `[CLS]` embedding (forming a 1536‑dim vector), (b) fine‑tune a lightweight classifier head on the training split, (c) evaluate accuracy/F1 on the held‑out test set, (d) repeat the exact procedure for the baseline model (re‑trained per seed).  
  - **Verification (per seed):**  
    - Produce `artifacts/eval/downstream_{seed}.json` containing `accuracy_baseline`, `accuracy_augmented`, `f1_baseline`, `f1_augmented`.  
    - After all seeds, run a paired t‑test (or Wilcoxon if Shapiro‑Wilk p < 0.05) on the accuracy deltas; report p‑value < 0.05 (FR‑005, FR‑006).  

- [ ] **T009** [US3] **Generate final evaluation report** – after successful downstream evaluation, compile (i) validation MSE improvement, (ii) ablation correlation, (iii) downstream accuracy/F1 statistics, (iv) resource usage (RAM, runtime), and (v) statistical significance. Produce `artifacts/report/final_report.md`.  
  - **Verification:**  
    - Report includes SC‑001, SC‑002, SC‑003, SC‑004, SC‑005, SC‑006, SC‑007 values and explicitly frames findings as *associational* (FR‑006).  
    - If the downstream benchmark is missing, the pipeline aborts with a clear error (preserving FR‑005).  

---  

## Phase 6 – Reproducibility, logging, and end‑to‑end sanity check  

- [ ] **T010** [US1] **Checksum & state logging** – implement `src/utils/checksum.py` to compute SHA‑256 hashes of every generated artifact (Parquet files, model checkpoints, JSON results) and write them to `state/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis.yaml`.  
  - **Verification:**  
    - After any pipeline run, the state file contains entries for all artifacts; a CI step compares current hashes against stored ones and fails on mismatch.  

- [ ] **T011** [US1] **End‑to‑end pipeline smoke test** – add a small‑sample entry point `src/cli/run_pipeline.py` that runs the full workflow on a **sample** of 100 documents (download → preprocess → latent generation → one seed of distillation & baseline → downstream evaluation). Output `data/results/sample_output.parquet`.  
  - **Verification:**  
    - CI executes `python -m src.cli.run_pipeline --sample-size 100`.  
    - The command finishes within 30 min, produces the result file, and the file contains columns `doc_id`, `predicted_latent`, `baseline_pred`, `augmented_pred`.  
    - All unit tests in `tests/` pass.  

- [ ] **T012** **Measure total pipeline runtime** – wrap the full end‑to‑end execution (including T001‑T011) with a timer that records start and end timestamps, writes the duration to `artifacts/runtime/runtime_seconds.txt`, and asserts the total wall‑clock time ≤ 6 hours.  
  - **Verification:**  
    - CI step fails if the recorded duration exceeds 21 600 seconds, satisfying SC‑005.  

- [ ] **T013** **Validate validation‑vs‑training loss ratio across seeds** – after all T005 runs, aggregate training and validation loss logs, compute the maximum ratio per seed, and assert each ratio ≤ 2.0. Write a summary `artifacts/eval/loss_ratio_summary.md`.  
  - **Verification:**  
    - CI fails if any seed violates the ratio, fulfilling SC‑007.  

---  

### Mapping of tasks to functional & success criteria  

| FR | Covered by task(s) |
|----|--------------------|
| FR‑001 | T001, T002, T003 |
| FR‑002 | T005 |
| FR‑003 | T005, T006 (RAM checks) |
| FR‑004 | T008 (concatenation) |
| FR‑005 | T008 |
| FR‑006 | T009 (report framing) |
| FR‑007 | T001 (page‑count check) |
| FR‑008 | T007 |
| FR‑009 | T006 (re‑train baseline per seed) |

| SC | Covered by task(s) |
|----|--------------------|
| SC‑001 | T005 (MSE vs. baseline) |
| SC‑002 | T008 (accuracy/F1) |
| SC‑003 | T008 (paired test p‑value) |
| SC‑004 | T005, T006 (RAM measurement) |
| SC‑005 | T012 (runtime measurement) |
| SC‑006 | T001 (page‑count check) |
| SC‑007 | T005 (loss‑ratio check) & T013 (aggregate verification) |

---  

*All tasks are unchecked; they will be marked complete by the CI pipeline when their verification steps succeed.*  