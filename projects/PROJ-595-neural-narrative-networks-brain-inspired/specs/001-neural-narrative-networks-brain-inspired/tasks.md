# Tasks: Neural Narrative Networks

**Input**: `spec.md`, `plan.md`, `research.md`, `data-model.md`, contracts, and existing artifacts.  
All tasks are written as markdown check‑boxes. Checked boxes (`[X]`) indicate completed work that has been verified; unchecked boxes (`[ ]`) are pending or need revision. Dependencies are expressed in the description or by ordering; tasks that can run in parallel are marked with `[P]`.

---

## Phase 0 – Plan Alignment (completed)

- [X] T000 Update `plan.md` to reference OpenNeuro dataset **ds001495** (matches FR‑001).  
- [X] T000.1 Clarify baseline as **TinyLSTM (quantized transformer)** in `plan.md` (matches FR‑004).

---

## Phase 1 – Project Setup (completed)

- [X] T001 Create project directories `code/`, `data/raw/`, `data/processed/`, `data/results/`, `tests/`. Add `code/__init__.py` and a standard `.gitignore`.  
- [X] T002 Add `code/requirements.txt` with pinned versions for `torch`, `datasets`, `nibabel`, `nilearn`, `numpy`, `pandas`, `scikit-learn`, `matplotlib`, `nltk`, `pytest`. **Depends on T001**.  
- [X] T003 Add minimal `pyproject.toml` configuring `ruff` and `black`. **Depends on T001**.  
- [X] T004 Add `.ruff.toml` with the project's linting rule set. **Depends on T001**.

---

## Phase 2 – Foundational Utilities (completed)

- [X] T006 [P] Implement `code/utils/schema_validation.py` with validators for neural, text, and RSA contracts.  
- [X] T007 [P] Implement `code/utils/checksums.py` for SHA‑256 hashing of files.  
- [X] T008 [P] Add `code/config.py` exposing `random_seed`, `cpu_only=True`, `max_ram_gb=7`, and a `set_seed()` helper.  
- [X] T009 [P] Add `code/utils/logging_config.py` that writes to `logs/pipeline.log` and emits error codes E001–E004.  
- [X] T018 [P] Implement `code/utils/loaders.py::load_chunked_fMRI()` for streaming large NIfTI files without exceeding RAM.

---

## Phase 3 – Data Ingestion & Pre‑processing (User Story 1, P1)

| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T012** | Download OpenNeuro ds001495 via `datasets.load_dataset('openneuro/ds001495', split='train')`. Verify the dataset ID and split exist; abort with **E001** if not. Save raw files under `data/raw/openneuro_ds001495/` and a checksum manifest `checksums.txt`. | – | FR‑001 |
| **T013** | Fetch Harvard‑Oxford masks for left/right hippocampus and dorsolateral prefrontal cortex using `nilearn.datasets.fetch_atlas_harvard_oxford('cort-maxprob-thr25-2mm')`. If a mask cannot be fetched, create a spherical mask (radius 10 mm) at MNI coordinates (L‑hipp x=‑24 y=‑33 z=‑12, R‑hipp x= 24 y=‑33 z=‑12, DLPFC x= ±40 y= 36 z= 28). If both methods fail, raise **"ROI definition failed: neither precomputed mask nor Harvard‑Oxford coordinates available."** Save mask paths to `data/processed/mask_paths.json`. | – | FR‑001 |
| **T014** | **Extract left hippocampus BOLD timecourses**. Scan `data/raw/openneuro_ds001495/` for all `sub-*/func/*task-narratives_bold.nii.gz`. Load each NIfTI, apply the left‑hippocampus mask from T013, average voxels, and store a 2‑D array `[n_timepoints,]` per subject. Concatenate across subjects (order by natural sort of subject IDs) and save as `data/processed/neural/roi_left_hipp.npy`. Verify file exists, non‑empty, and shape matches `(n_subjects, n_timepoints)`. | T012, T013 | FR‑001 |
| **T015** | **Extract right hippocampus BOLD timecourses** (same procedure as T014, using the right‑hippocampus mask). Output: `data/processed/neural/roi_right_hipp.npy`. | T012, T013 | FR‑001 |
| **T016** | **Extract dorsolateral prefrontal cortex BOLD timecourses** (same procedure, using DLPFC mask). Output: `data/processed/neural/roi_dlpfc.npy`. | T012, T013 | FR‑001 |
| **T020** | Combine the three ROI `.npy` files into a long‑form CSV `data/processed/neural/roi_timecourses.csv` with columns `subject_id`, `roi`, `timepoint`, `signal`. Signal values are z‑scored float32. **Do not run in parallel with T014‑T016** – must wait until they finish. | T014, T015, T016 | FR‑001 |
| **T021** | Validate `roi_timecourses.csv` against `neural-data.schema.yaml` using `code/utils/schema_validation.py`. Log success or detailed validation errors. | T020 | — |
| **T022** | Store the validation result (JSON) at `data/processed/neural/validation_report.json`. | T021 | — |
| **T023** | Download the ROCStories corpus from HuggingFace (`jamestran/roc_stories`; fallback `mit/rocstories`). Verify the dataset ID and that a `'train'` split exists; abort with **E001** if not. Sample 1 000 stories (`shuffle(seed=42).select(range(1000))`) and write to `data/text/rocstories_sample.jsonl` (fields `story_id`, `story`). | – | FR‑004 |
| **T023.1** | Parse `rocstories_sample.jsonl` to ensure each record contains an `event_boundaries` field. If missing, infer boundaries via `nltk.sent_tokenize` and add them, logging a warning. Save the enriched file as `data/text/rocstories_sample_boundaries.jsonl`. | T023 | — |
| **T025** | Compute per‑event mean BOLD signals for each ROI using the `event_boundaries` from `rocstories_sample_boundaries.jsonl`. Interpolate timepoints to event boundaries with `scipy.interpolate.interp1d` (linear, `fill_value='extrapolate'`). Save intermediate averages to `data/processed/neural/event_averages_tmp.csv`. | T020, T023.1 | FR‑001 |
| **T026** | Consolidate `event_averages_tmp.csv` into the final table `data/processed/neural/event_averages.csv` with columns `subject_id`, `event_id`, `roi`, `mean_signal`. Validate against the neural schema. | T025 | FR‑001 |
| **T027** | Generate a provenance log `data/processed/neural/derivation_logs.json` documenting source file hashes, transformation steps, interpolation parameters, and output hashes for all files created in Phase 3. | T026 | — |
| **T028** | Run `code/utils/checksums.py` to update the project‑wide checksum manifest with all new files from Phase 3 (including `derivation_logs.json`). | T027 | — |

---

## Phase 4 – Brain‑Inspired Model Generation (User Story 2, P2)

| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T031a** | Implement `code/models/sparse_autoencoder.py` containing class `SparseAutoencoder` (≤ 2 M parameters) with L1 sparsity regularizer and property `sparsity_ratio = (activations>0).float().mean()`. Enforce ≤ 0.20 during training. **Verification**: unit test checks class import, parameter count, and that `sparsity_ratio` is computed. | – | FR‑002, SC‑001 |
| **T032** | Implement `code/models/gating_module.py` defining `PrefrontalGating` that receives hidden states and a coherence mask, outputting gated representations. **Verification**: import test and existence of `forward` method. | – | FR‑003 |
| **T033** | Wire the SAE and gating module together in `code/models/brain_inspired.py` exposing a `forward(story_tensor)` that returns gated hidden states. **Verification**: import `brain_inspired`, instantiate with dummy inputs, run `forward`, and assert output shape. | T031a, T032 | FR‑002, FR‑003 |
| **T034** | Implement the baseline **TinyLSTM** in `code/models/baseline_lstm.py`. Quantize dynamically (`torch.quantization.quantize_dynamic`) for CPU‑only execution and ensure total parameters ≤ 2 M. **Verification**: check parameter count and that the model’s `quantized` attribute is True. | – | FR‑004 |
| **T035** | Train the brain‑inspired model on the **pre‑training** ROCStories sample (`data/text/rocstories_sample.jsonl`). Use 10 epochs, batch size 32, Adam lr 1e‑3. After each epoch compute `sparsity_ratio`; if > 0.20, retry with a new seed (max 3 retries). Save final weights to `data/results/brain_inspired_weights.pt`. Log final sparsity ratio and training seed in `data/results/training_log.json`. **Verification**: confirm weight file exists, sparsity ≤ 0.20, and training log records seed. | T031a, T032, T023 | FR‑002, SC‑001 |
| **T036** | Generate **hidden‑state representations** for the **held‑out fMRI story set** (`data/text/fMRI_story_transcripts.jsonl`). Load the intersection of story IDs between the fMRI transcripts and the ROCStories pre‑training set. Run the brain‑inspired model (from T035) on each story, collect hidden states, and save as `data/results/brain_inspired_hidden.npy`. **Verification**: file contains ≥ 100 unique story representations (matching the fMRI test set size). | T035, T025 | FR‑004, SC‑001 |
| **T037** | Generate baseline hidden states for the same story set using the TinyLSTM model. Save to `data/results/baseline_hidden.npy`. **Verification**: file contains the same number of story representations as `brain_inspired_hidden.npy`. | T034, T025 | FR‑004 |
| **T038** | Monitor peak RAM during T036 and T037 using `psutil`. Write a JSON report `data/results/memory_profile.json` with keys `peak_gb` and `timestamp`. Ensure `peak_gb < 7.0`. **Verification**: JSON exists and `peak_gb` ≤ 7.0. | T036, T037 | SC‑002 |
| **T039** | Update the global checksum manifest with all new model artifacts (`*_weights.pt`, `*_hidden.npy`, `memory_profile.json`). | T038 | — |
| **T040** | **Generate ≥ 1 000 unique stories** with the brain‑inspired model. Sample 1 200 story prompts from `rocstories_sample.jsonl`, run the model to produce full narratives, and write to `data/results/brain_inspired_stories.jsonl`. **Verification**: count ≥ 1 000 and all entries have non‑empty `story_text`. | T035, T023 | FR‑004, SC‑005 |
| **T041** | **Generate ≥ 1 000 unique stories** with the baseline TinyLSTM. Use the same 1 200 prompts, generate narratives, and write to `data/results/baseline_stories.jsonl`. **Verification**: count ≥ 1 000 and all entries have non‑empty `story_text`. | T034, T023 | FR‑004, SC‑005 |
| **T053** | Run the Reference‑Validator Agent on all citations in `spec.md`, `plan.md`, and the `code/` package. Fail the task if any citation is unresolved. **Verification**: agent returns a zero‑error report. | – | — |

---

## Phase 5 – Neural Similarity Analysis & Validation (User Story 3, P3)

| ID | Description | Dependencies | FR/SC |
|----|-------------|--------------|-------|
| **T042** | Compute RSA matrices for both models vs. each ROI. Load `roi_timecourses.csv` (Phase 3) and the hidden‑state files (`brain_inspired_hidden.npy`, `baseline_hidden.npy`). Build representational dissimilarity matrices (RDMs) using 1 – Pearson correlation. For each ROI, correlate the neural RDM with the model RDM, producing a similarity score. Save CSV files `data/results/rsa_brain_inspired_<roi>.csv` and `data/results/rsa_baseline_<roi>.csv`. | T020, T036, T037 | FR‑005 |
| **T043** | Perform a permutation test on the **difference** of RSA similarity scores (brain‑inspired – baseline). Run **2 000** permutations (shuffle story labels) with early‑stopping when variance of the last 1 000 p‑values < 0.001. Apply Holm‑Bonferroni correction across the three ROIs. Save results to `data/results/permutation_test_results.json` containing `observed_difference`, `p_value`, `permutations`, `convergence_variance`, `is_significant`. Abort with **E006** if convergence not achieved. | T042 | FR‑006, SC‑003 |
| **T044** | Validate the RSA CSVs and permutation JSON against `rsa-output.schema.yaml` using `code/utils/schema_validation.py`. Write a consolidated validation report to `data/results/rsa_validation_report.json`. | T042, T043 | — |
| **T045** | Create visualizations: heatmaps of each RSA matrix (`data/results/rsa_<model>_<roi>_heatmap.png`) and a bar plot with 95 % confidence intervals comparing brain‑inspired vs. baseline RSA scores across ROIs (`data/results/rsa_comparison_barplot.png`). Save all figures under `data/results/figures/`. | T042, T043 | FR‑007 |
| **T046** | Assemble a final results summary CSV `data/results/results_summary.csv` containing: `sparsity_ratio` (from T035), `peak_ram_gb` (T038), RSA similarity per ROI for both models, `p_value`, `is_significant`, and counts of generated stories from T040/T041. This file is the canonical hand‑off to the paper pipeline. **Verification**: CSV exists and includes all required columns. | T038, T042, T043, T045, T040, T041 | SC‑004, SC‑005 |

---

## Phase 6 – Verification, Reporting & Handoff (optional polish)

- [ ] T050 [US?] Run the full end‑to‑end pipeline from `code/main.py` to confirm that, starting from raw data, all intermediate artifacts are produced and the final `results_summary.csv` matches the specifications.   <!-- FAILED: unspecified -->
- [~] T051 [US?] Generate a reproducibility manifest `manifest.json` listing dataset URLs, exact commit hash of the repository, software versions (from `requirements.txt`), and all checksum values.  
- [~] T052 [US?] Update `README.md` to include a concise “How to reproduce” section pointing to `manifest.json` and the command `python -m code.main`.  

*(These polish tasks can be executed after the core research tasks are green‑checked; they are not required for the scientific verdict but improve transparency.)*

--- 

### Execution Order Summary

1. **Infrastructure** – Phases 0‑2 (already completed).  
2. **Data Layer** – Phase 3 tasks (`T012` → `T028`).  
3. **Model Layer** – Phase 4 tasks (`T031a` → `T041`, `T053`).  
4. **Analysis Layer** – Phase 5 tasks (`T042` → `T046`).  
5. **Polish / Handoff** – Phase 6 (optional).  

All pending tasks respect data‑flow dependencies, stay within the CPU‑only budget (≤ 7 GB RAM), and generate **real** artifacts from verified data sources. The first end‑to‑end runnable step is `T012` → `T020` → `T021` → `T023` → `T025` → `T026`, which produces the CSV needed for a minimal RSA run. Subsequent tasks build on these outputs to complete the full study.  
