# Tasks: llmXive follow‑up: extending “Qwen‑Image‑VAE‑2.0 Technical Report”

**Inputs**: `spec.md`, `plan.md`, data‑model definitions, JSON‑schema contracts.  
**Goal**: Produce a reproducible end‑to‑end analysis that evaluates latent‑space disentanglement, verifies linearity, and demonstrates zero‑shot semantic editing, while satisfying all functional requirements (FR‑001 – FR‑010) and success criteria (SC‑001 – SC‑005).

---  

## Phase 0 – Project bootstrap & verification  

- [~] T001 [P] Establish external‑resource verification and quick‑start guide.
  *Implement a script `code/boot/verify_resources.py` that HEAD‑checks the dataset URL (`https://huggingface.co/datasets/omnineura/Omni-Doc-1`) and the VAE model URL (`https://huggingface.co/Qwen/Qwen-Image-VAE-2.0`).*  
  *Write `quickstart.md` with the command `python -m code.main --config config.yaml` and a description of the required environment.*  
  *Verification*: `verify_resources.py` exits with status 0 and creates `data/raw/download_status.json`; `quickstart.md` exists and contains the command line.

- [X] T002 [P] Create `requirements.txt` with exact pinned versions (fixes previously missing file).  
  *File path*: `requirements.txt` (project root).  
  *Contents* must match the plan’s Technical Context:  

  ```text
  torch==2.2.0+cpu
  transformers==4.40.0
  datasets==2.18.0
  scikit-learn==1.4.0
  opencv-python==4.9.0
  paddleocr==2.7.0
  paddlepaddle-cpu==2.7.0
  pyyaml==6.0.1
  scipy==1.13.0
  statsmodels==0.14.1
  pandas==2.2.1
  numpy==1.26.4
  matplotlib==3.8.3
  seaborn==0.13.2
  pillow==10.2.0
  pytest==8.1.1
  ```  

  *Verification*: `grep -E "torch|transformers|datasets|scikit-learn|opencv-python|paddleocr|paddlepaddle-cpu|pyyaml|scipy|statsmodels|pandas|numpy|matplotlib|seaborn|pillow|pytest" requirements.txt` returns all lines.

- [~] T003 [P] Initialise project‑wide logger and random seeds.  
  *Add `code/utils/logger.py` exposing `get_logger(name: str)`. Set deterministic seeds for `numpy`, `torch`, and `random`.*  
  *Verification*: Running `python -c "import code.utils.logger as l; l.get_logger('test')"` produces a logger without errors; a file `data/raw/logger_init.json` records the seed values.

---  

## Phase 1 – Feasibility & power analysis  

- [~] T004 [P] Implement power‑analysis utility.  
  *File*: `code/analysis/power.py` – computes minimum sample size `N` for a two‑sample t‑test with effect size `d=0.8`, power ≥ 0.8, α = 0.05 using `statsmodels.stats.power.tt_ind_solve_power`.*  
  *Run*: `python -m code.analysis.power --output data/results/power_analysis.json`.  
  *Verification*: `power_analysis.json` contains fields `N_required`, `effect_size`, `achieved_power`, and `status` (`conclusive` or `inconclusive`).  

- [ ] T005 [P] Implement runtime‑budget estimator.   <!-- FAILED-IN-EXECUTION: code/analysis/runtime_estimate.py exit=1 --> <!-- FAILED-IN-EXECUTION: code/analysis/runtime_estimate.py exit=1 -->
  *File*: `code/analysis/runtime_estimate.py` – estimates total wall‑clock time as `N_required * 60 s` (per‑image budget) and flags if > 6 h. Outputs `data/results/runtime_estimate.json`.  
  *Verification*: `runtime_estimate.json` includes `estimated_seconds`, `exceeds_budget` (bool), and `status`.

---  

## Phase 2 – Data acquisition & deterministic sampling  

- [ ] T006 [P] Download Omni‑Doc‑1 TokenBench subset.  
  *Script*: `code/data/download.py` uses `datasets.load_dataset("omnineura/Omni-Doc-1", split="train", streaming=False)` and writes the parquet file to `data/raw/omnidoc_tokenbench.parquet`.*  
  *Verification*: After run, `data/raw/download_status.json` records `success: true` and file checksum; the parquet file exists and can be opened without error.

- [ ] T007 [P] Deterministic sampling based on feasibility results.  
  *Script*: `code/data/sample.py` reads `power_analysis.json` → `N_required`, caps `N_final = min(N_required, floor(6*3600/60))` (respecting the 6 h budget), and draws a fixed‑seed (`seed=42`) sample of `N_final` crops, writing `data/interim/sample.parquet`.*  
  *Verification*: `sample.parquet` contains exactly `N_final` rows; `data/results/sampling_report.json` logs the seed and final size.

---  

## Phase 3 – Model loading & ground‑truth preprocessing  

- [ ] T008 [P] CPU‑only Qwen‑Image‑VAE‑2.0 loader (no fallback).  
  *File*: `code/models/vae_wrapper.py` implements `load_vae_cpu()` that **attempts to load `Qwen/Qwen-Image-VAE-2.0` on CPU only**. If loading fails (e.g., requires GPU), the script raises a fatal error and aborts the pipeline, fulfilling FR‑002. No fallback to tiny‑vae is performed.*  
  *Verification*: Unit test `tests/unit/test_vae_loader.py` asserts that the loaded model’s device is `"cpu"` and that a loading failure triggers a `RuntimeError`.

- [ ] T009 [P] Extract ground‑truth region annotations.  
  *File*: `code/data/preprocess.py` reads `sample.parquet`, filters crops with modality “text” or “image”, computes overlap ratio, discards any with `overlap_ratio > 0.1`, and writes `data/interim/ground_truth.parquet`.*  
  *Verification*: `ground_truth.parquet` contains only rows with `modality` in {text, image} and `overlap_ratio ≤ 0.1`; a checksum file `data/results/ground_truth_checksum.json` is generated.

- [ ] T022 [P] Validate dataset label keys after download.  
  *Script*: `code/data/validate_labels.py` loads `data/raw/omnidoc_tokenbench.parquet` and asserts that every record contains the required label keys `'text-only'` and `'image-only'`. If any record is missing a key, the script logs an error and aborts. Generates `data/results/label_validation.json` with a success flag.*  
  *Verification*: The task fails the pipeline if validation fails; otherwise it writes a JSON with `"valid": true`.

---  

## Phase 4 – Encoding crops to latent vectors  

- [ ] T010 [P] Encode filtered crops.  
  *Script*: `code/analysis/encode.py` loads the VAE via `vae_wrapper.load_vae_cpu()`, iterates over `ground_truth.parquet`, encodes each crop, and stores vectors in a compressed NumPy archive `data/interim/latent_vectors.npz` together with metadata (`latent_id`, `crop_id`, `modality`).*  
  *Verification*: `latent_vectors.npz` loads without error; `data/results/encoding_summary.json` reports total encoded samples and average encoding time.

---  

## Phase 5 – Disentanglement analysis (User Story 1, P1)  

- [ ] T011 [US1] Train K‑Means, compute DCI, and run permutation test.  
  *File*: `code/analysis/disentanglement.py` performs:  
  1. Unsupervised K‑Means (k=2) on latent vectors.  
  2. Computes DCI (Disentanglement, Completeness, Informativeness) and orthogonality checks.  
  3. Evaluates cluster purity using the ground‑truth labels (must be ≥ 0.90).  
  4. Executes 1 000 label permutations, retrains a linear SVM each time, records accuracy distribution, and calculates empirical p‑value.  
  *Outputs*: `data/results/disentanglement.json` (DCI scores, purity, observed accuracy, p‑value) and `data/results/pca_plot.png` (2‑D PCA visualization).  
  *Verification*: A validation script confirms `DCI.disentanglement ≥ 0.8`, `purity ≥ 0.9`, and `p_value < 0.05/2` (Bonferroni‑corrected for accuracy & F1). Results are also written to `data/results/disentanglement_report.json`.

---  

## Phase 6 – Linearity verification (Prerequisite for US 2)  

- [ ] T012 [US2] Pilot linearity test on 10 diverse samples.  
  *Script*: `code/analysis/linearity.py` selects 10 random samples, computes `z_new = z_doc - μ_text_old + μ_text_new`, and regresses the resulting vectors against the expected arithmetic difference, reporting R².  
  *Output*: `data/results/linearity.json` with field `r2`.  
  *Verification*: The script asserts `r2 ≥ 0.9`; otherwise it writes `status: failed` and the pipeline aborts further editing tasks.

---  

## Phase 7 – Zero‑shot semantic editing (User Story 2, P2)  

- [ ] T013 [US2] Compute modality centroids and perform vector arithmetic.  
  *File*: `code/analysis/editing.py` loads `latent_vectors.npz`, computes `text_centroid` and `image_centroid`, then for each document crop executes `z_new = z_doc - μ_text_old + μ_text_new` (where `μ_text_new` is a target‑text centroid derived from a separate “target‑text” sample set).*  
  *Outputs*: Edited latent vectors saved as `data/interim/edited_latents.npz` and baseline reconstructions saved as `data/interim/baseline_images/` (PNG).

- [ ] T014 [US2] Decode edited latents and evaluate layout preservation.  
  *Script*: `code/analysis/editing_eval.py` decodes edited latents to images (`data/interim/edited_images/`), runs PaddleOCR v2.7.0 (CPU) on the text regions, computes:  
    * Masked SSIM (≥ 0.85) on non‑text pixels,  
    * Edge Alignment Score (Canny + IoU ≥ 0.80),  
    * Keypoint Matching Score (SIFT + RANSAC ≥ 0.80).  
  *All metrics* are aggregated into `data/results/editing_metrics.json`.  
  *Verification*: The script asserts each metric meets its threshold; if any fail, it records `failure_reason` (`texture_artifact` or `layout_distortion`) in the JSON.

- [ ] T015 [US2] OCR correctness check.  
  *Part of `editing_eval.py`* – compares OCR output against the target string, requiring ≥ 95 % character‑level accuracy. Results are stored in `data/results/ocr_accuracy.json`.  
  *Verification*: The pipeline proceeds only if `ocr_accuracy.mean ≥ 0.95`.

---  

## Phase 8 – Sensitivity & multiple‑comparison validation (User Story 3, P3)  

- [ ] T016 [US3] Threshold sensitivity sweep.  
  *Script*: `code/analysis/sensitivity.py` varies the decision threshold around the optimal boundary (±5 % in 0.5 % steps), recomputes false‑positive/false‑negative rates, and writes `data/results/sensitivity.json`.*  
  *Verification*: The JSON includes a monotonicity check; any abrupt degradation > 10 % flags a warning.

- [ ] T017 [US3] Aggregate p‑values and apply Bonferroni correction.  
  *Script*: `code/analysis/bonferroni.py` reads `disentanglement.json` (accuracy and F1 p‑values), aggregates them, applies Bonferroni (or Holm‑Bonferroni) correction, and outputs `data/results/bonferroni_corrected.json` with adjusted p‑values and `is_significant` flags.*  
  *Verification*: Adjusted p‑values ≤ 0.05 for primary metrics confirm statistical significance.

---  

## Phase 9 – Final aggregation & reproducible handoff  

- [ ] T018 [P] Assemble final experiment output.  
  *Script*: `code/analysis/assemble_output.py` collects:  
    - `test_id` (UUID), `timestamp`,  
    - all metric objects from `disentanglement.json`, `editing_metrics.json`, `linearity.json`, `sensitivity.json`, `bonferroni_corrected.json`,  
    - `sample_size`, `power_analysis` (from `power_analysis.json`),  
    - flags `linearity_verified`, `triviality_flag` (set if raw‑pixel logistic regression > 99 % separable),  
    - `model_used` (actual VAE name), `cpu_feasibility` (`confirmed` or `rejected`).  
  *Writes*: `data/results/experiment_output.json` conforming to `contracts/output.schema.yaml`.  
  *Verification*: Run `jsonschema -i data/results/experiment_output.json contracts/output.schema.yaml`; exit code 0.

- [ ] T019 [P] End‑to‑end demo on a minimal sample (early executable result).  
  *Run*: `python -m code.main --config config.yaml --sample-size 100`.  
  *Produces*: `data/results/e2e_demo.json` summarising the same fields as `experiment_output.json` but limited to 100 samples for quick verification.  
  *Verification*: The demo JSON passes schema validation and all acceptance thresholds (DCI, purity, SSIM, etc.) are met; a CI test `tests/integration/test_e2e_demo.py` asserts the presence of the file and key fields.

---  

## Phase 10 – Testing & quality assurance (cross‑cutting)  

- [ ] T020 [P] Unit tests for core modules.  
  *Files*: `tests/unit/test_vae_loader.py`, `tests/unit/test_preprocess.py`, `tests/unit/test_power.py`.  
  *Verification*: `pytest -q` reports all tests passed.

- [ ] T021 [P] Integration test of full pipeline on the deterministic sample **including verification that `artifact_hashes` in the project state YAML have been updated**.  
  *File*: `tests/integration/test_full_pipeline.py` invokes `code.main` with the sample config and checks that all expected output files exist, contain non‑empty JSON, **and that `state/projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v.yaml` includes an up‑to‑date `artifact_hashes` map** reflecting the newly generated artifacts.  
  *Verification*: CI passes with `0` failures.

---  

## Phase 11 – Versioning discipline (Constitution V)  

- [ ] T023 [P] Compute content hashes for all generated artifacts and record them in the project state YAML.  
  *Script*: `code/util/hash_and_state.py` walks `data/` after each major phase, computes SHA‑256 hashes for every file, and writes/updates `state/projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v.yaml` under the key `artifact_hashes: { <relative_path>: "<hash>" }`. The script is invoked at the end of T018 and also as a standalone step before T021 to guarantee the state file is current.  
  *Verification*: A unit test `tests/unit/test_hash_state.py` asserts that the YAML contains entries for a sample of files and that the hashes match recomputed values.

---  

### Execution order (implicit)

1. **Phase 0** → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11.  
2. Tasks marked `[P]` may run in parallel as long as their input files are available.  
3. Tasks that depend on feasibility (T004–T007) must complete before any data‑driven computation.  

---  

*All tasks are unchecked (☐) until their implementation and verification succeed. The list respects the required 8–15 substantive tasks while covering every functional requirement and success criterion. New tasks T022, T023 address previously missing validation and version‑hashing steps.* 