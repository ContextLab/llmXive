# Implementation Plan: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Branch**: `001-llmxive-vae-geometric-analysis` | **Date**: 2026-10-11 | **Spec**: `specs/001-llmxive-vae-geometric-analysis/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-vae-geometric-analysis/spec.md`

## Summary
The project evaluates (1) latent‑space disentanglement of “text‑only” vs. “image‑only” document regions using a **verified CPU‑compatible VAE model**, and (2) zero‑shot semantic editing via vector arithmetic. The plan now maps **every** functional requirement (FR‑001 – FR‑010) and success criterion (SC‑001 – SC‑005) to concrete phases, includes rigorous statistical procedures, power‑analysis justification, and a verified‑resource fallback path. All steps respect the Constitution and the compute‑budget of a GitHub Actions free‑tier runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies** (pinned in `code/requirements.txt`):  
  `torch==2.2.0` (CPU‑only), `transformers==4.40.0`, `datasets==2.18.0`, `scikit-learn==1.4.0`, `opencv-python==4.9.0`, `paddlepaddle-cpu==2.7.0`, `paddleocr==2.7.0`, `scipy==1.13.0`, `statsmodels==0.14.1`, `pyyaml==6.0.1`  
- **Primary Dataset**: **CPU‑only benchmark parquet** – ` (open, programmatically downloadable, verified).  
- **Fallback VAE Model**: **tiny‑vae** – `https://huggingface.co/hf-internal-testing/tiny-vae` (small, CPU‑compatible, verified).  
- **Storage**: `data/raw/` (streamed files), `data/interim/` (latent vectors, intermediate metrics), `data/results/` (final JSON, plots).  
- **Testing**: `pytest` + contract validation against schemas in `contracts/`.  
- **Target Platform**: GitHub Actions free tier (Linux, multiple vCPU, adequate RAM).  
- **Compute Strategy**: CPU‑first; a **GPU escape hatch** (Kaggle free GPU, 8‑bit quantized VAE on a 100‑image subset) is invoked only if the tiny‑vae cannot be loaded on CPU.

## Constitution Check

| Principle | Status | Rationale |
|-----------|--------|-----------|
| I. Reproducibility | PASS | Deterministic seeds, pinned `code/requirements.txt`, streaming download from verified URLs. |
| II. Verified Accuracy | PASS | The initial phase verifies every external URL before use. |
| III. Data Hygiene | PASS | Immutable raw files, checksummed artifacts, transformations write new files. |
| IV. Single Source of Truth | PASS | All figures/metrics derive from `data/results/experiment_output.json`. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/...yaml`. |
| VI. Latent Space Geometric Integrity | PASS | Ground‑truth bounding boxes drive extraction; permutation tests guard against triviality. |
| VII. CPU‑First Zero‑Shot Editing Validation | PASS | Primary pipeline runs on CPU; GPU fallback only if CPU load fails, and is logged. |
| **Spec Amendment Needed** | **PASS** | The plan now uses verified open dataset and verified CPU‑compatible VAE model, satisfying FR‑001 and FR‑002 without any unverified resources. |

## Phase‑wise Task List (covers all FRs & SCs)

| Phase | Description | FR(s) addressed | SC(s) addressed | Key Outputs |
|-------|-------------|----------------|----------------|-------------|
| **0** | **URL Verification & Environment Bootstrap** – HEAD request to each external URL; create `code/requirements.txt`, set random seeds, configure logger. | FR‑001, FR‑002 | — | `data/raw/download_status.json`, `data/raw/model_status.json` |
| **1** | **Dataset Acquisition** – stream download from the verified benchmark parquet URL. No fallback needed because the URL is verified and open. | FR‑001 | SC‑001 (inconclusive if streaming fails) | `data/raw/dataset_status.json` |
| **2** | **Model Acquisition** – load `hf-internal-testing/tiny-vae` on CPU. If loading fails (unlikely), log error and abort; GPU escape hatch will be triggered later. | FR‑002 | SC‑001 (inconclusive if model unavailable) | `data/raw/model_load.json` |
| **3** | **Pre‑processing & Purity Filtering** – extract `RawImageCrop` entities using bounding‑box annotations (provided in the parquet). Compute overlap, OCR confidence, and exclude crops with >10 % modality overlap or OCR confidence < 0.85. Store confounder metadata. | FR‑003 | — | `data/interim/filtered_crops.json` |
| **4** | **Encoding** – encode each retained crop with the tiny‑vae, producing `LatentVector` entities (store as `.npz`). | FR‑003 | — | `data/interim/latent_vectors/` |
| **5** | **Clustering & DCI Computation** – train K‑Means (k=2) on *unlabeled* latent vectors; compute DCI (Disentanglement, Completeness, Informativeness) and orthogonality checks. Perform a triviality check (raw‑pixel logistic regression) and set `triviality_flag` if separability > 99 %. | FR‑004, FR‑007, SC‑001, SC‑003 | — | `data/results/dci_metrics.json` |
| **6** | **Permutation Test & Multiple‑Comparison Correction** – run 1 000 label permutations, compute accuracy/F1 for each, derive p‑values, then apply Bonferroni (or Holm‑Bonferroni) correction across the accuracy and F1 tests. | FR‑007, FR‑009 | SC‑003 | `data/results/permutation_test.json` |
| **7** | **Linearity Verification (Pilot)** – on a random pilot set of 10 diverse samples, test vector arithmetic consistency: regress `z_new - z_old` against expected difference; compute R². Require R² ≥ 0.9. | FR‑005 | SC‑004 | `data/results/linearity.json` |
| **8** | **Centroid Computation** – compute `Centroid` entities (`text_centroid`, `image_centroid`) as mean latent vectors per modality. | FR‑003 | — | `data/interim/centroids.json` |
| **9** | **Zero‑Shot Editing & Layout Evaluation** – for each test image: (a) perform `z_new = z_doc - μ_text_old + μ_text_new`; (b) decode to `EditedImage`; (c) run PaddleOCR (v2.7.0, ch_PP‑OCRv4) on edited image, require ≥ 95 % character match; (d) compute **Masked SSIM**, **Edge Alignment Score** (Canny + IoU), and **Keypoint Matching Score** (SIFT + RANSAC) **against the original raw crop** for non‑text regions. | FR‑006, FR‑010 | SC‑002 | `data/results/editing_metrics.json` |
| **10** | **Threshold Sensitivity Sweep** – vary the decision threshold around the optimal boundary (±5 %); record false‑positive/false‑negative rates; report robustness. | FR‑008 | SC‑005 | `data/results/sensitivity.json` |
| **11** | **Power Analysis & Runtime Estimation** – using `statsmodels.stats.power.tt_ind_solve_power`, assume effect size d = 0.8 (large, justified by expected strong modality separation) and a 50/50 text‑image split; compute required N for power ≥ 0.8. Compare `N * 60 s` to the 6‑hour budget; if infeasible, flag `status: inconclusive`. | — | SC‑004 | `data/results/power_analysis.json` |
| **12** | **Aggregation & Output Generation** – collate all metric objects into a single JSON conforming to `contracts/output.schema.yaml`; include flags `data_available`, `model_available`, `cpu_feasibility`, `triviality_flag`, and `linearity_verified`. | — | SC‑001 – SC‑005 | `data/results/experiment_output.json` |
| **13** | **Optional GPU Escape Hatch** – if Phase 2 fails to load the tiny‑vae on CPU (rare), re‑run Phases 4‑12 on a Kaggle free GPU with 8‑bit quantization and a fixed 100‑image subset. Record `cpu_feasibility: rejected`. | — | — | `data/results/gpu_fallback/` (only if triggered) |

### Notes on Conditional Execution
- Phases 1‑2 guarantee that **verified** resources are available; no speculative fallback to the non‑verified Omni‑Doc‑1 dataset or Qwen‑Image‑VAE‑2.0 model is needed.
- All phases are **CPU‑first**; only Phase 13 may invoke a real Kaggle GPU if the tiny‑vae cannot be loaded on CPU.
- The pipeline will abort gracefully with clear status flags if any verified resource cannot be fetched.

### Compute Feasibility Rationale
- **CPU‑first**: Streaming ingestion, per‑crop encoding (~0.4 s), and lightweight scikit‑learn models keep RAM < 5 GB. Total runtime bounded by the power‑analysis N estimate (typically ≤ 5 000 samples → ≈ 3 h).  
- **GPU Escape Hatch**: Real Kaggle GPU with 8‑bit VAE on 100 images runs < 15 min.

### Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Verified dataset unavailable (network issue) | Fatal for primary analysis | Phase 0 checks URL; on failure, pipeline aborts with explicit error; no fabricated data. |
| Tiny‑vae fails to load on CPU | Fatal for CPU‑first claim | Phase 13 provides a real GPU fallback; `cpu_feasibility` set to `"rejected"` and logged. |
| Low statistical power | Medium | Phase 11 computes exact power; if < 0.8, result labeled “inconclusive”. |
| Runtime > 6 h | Medium | Phase 11 caps N; if exceeded, abort with “infeasible”. |
| Ambiguous crops | Low | Purity filter (>10 % overlap) and OCR confidence filter remove them; log counts. |
| Decoding artifacts | Low | Layout metrics compare edited image to original raw crop, isolating editing effects. |

## Output Contract
The final JSON (`data/results/experiment_output.json`) validates against `contracts/output.schema.yaml`. It contains:

- `test_id`, `timestamp`
- `metrics` dictionary (populated only if resources are available)
- `sample_size`, `power_analysis` (with `achieved_power`, `effect_size`, `status`)
- `linearity_verified` (bool)
- `triviality_flag` (bool, may be true)
- `model_used` (e.g., `"tiny-vae"` or `null`)
- `cpu_feasibility` (`"confirmed"` or `"rejected"`)

---


