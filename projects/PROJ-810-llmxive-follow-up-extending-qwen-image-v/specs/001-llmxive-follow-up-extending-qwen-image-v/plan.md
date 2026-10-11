# Implementation Plan: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Branch**: `001-llmxive-vae-geometric-analysis` | **Date**: 2026-10-11 | **Spec**: `specs/001-llmxive-vae-geometric-analysis/spec.md`  
**Input**: Feature specification from `/specs/001-llmxive-vae-geometric-analysis/spec.md`

## Summary
The project validates geometric disentanglement of the Qwen‑Image‑VAE‑2.0 latent space on the Omni‑Doc‑1 (TokenBench subset) dataset, then demonstrates zero‑shot semantic editing via vector arithmetic. The pipeline proceeds in deterministic phases, each explicitly addressing a functional requirement (FR‑001 – FR‑010) and success criterion (SC‑001 – SC‑005).

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.2.0` (CPU‑only), `transformers==4.40.0`, `datasets==2.18.0`, `scikit-learn==1.4.0`, `opencv-python==4.9.0`, `paddlepaddle‑cpu==2.7.0`, `paddleocr==2.7.0`, `scipy==1.13.0`, `statsmodels==0.14.1`, `pyyaml==6.0.1`  
- **Storage**: `data/raw/` (streamed parquet), `data/interim/` (latent vectors, cropped images), `data/results/` (metrics, plots)  
- **Testing**: `pytest` for unit & contract tests (see `contracts/`).  
- **Target Platform**: GitHub Actions free tier (Linux, 2 vCPU, ~7 GB RAM).  
- **Constraints**: CPU‑first execution; if any step OOMs or raises `ImportError`, the **CPU‑First Feasibility** hypothesis is rejected and a single‑GPU Kaggle escape hatch runs a *scaled‑down* demo (N = 100 images, 8‑bit quantized VAE).  
- **Scale/Scope**: Full Omni‑Doc‑1 dataset streamed; effective sample size `N` determined by power analysis (target power ≥ 0.8) and runtime budget (≤ 6 h).  

## Constitution Check
| Principle | Status | How the plan satisfies it |
|-----------|--------|---------------------------|
| I. Reproducibility | PASS | `requirements.txt` pinned, deterministic seeds, streaming download from a fixed HF URL. |
| II. Verified Accuracy | PASS | All external URLs (HF dataset, VAE model) are explicitly cited; no fabricated sources. |
| III. Data Hygiene | PASS | Checksums recorded, raw data immutable, all transformations produce new files in `data/interim/`. |
| IV. Single Source of Truth | PASS | Every figure/metric is generated from JSON files under `data/results/`; the paper will reference those files directly. |
| V. Versioning Discipline | PASS | Content hashes stored in `state/...yaml` for every artifact (latent vectors, edited images, metrics). |
| VI. Latent Space Geometric Integrity | PASS | Ground‑truth bounding boxes drive extraction; permutation tests, triviality check, and linearity validation guard against artefacts. |
| VII. CPU‑First Zero‑Shot Editing Validation | PASS | Primary pipeline runs on CPU; GPU is only an *escape hatch* and, if used, the plan records `cpu_feasibility: rejected`. |

## Phase‑wise Task List (covers all FRs & SCs)

| Phase | Description | FR(s) addressed | SC(s) addressed | Key Outputs |
|-------|-------------|----------------|----------------|-------------|
| **0** | **Project bootstrap** – create `requirements.txt`, pin seeds, configure logger. | — | — | `requirements.txt`, `code/src/__init__.py` |
| **1** | **Dataset download & validation** – stream `omnineura/Omni-Doc-1`; verify fields `modality`, `bbox`. Compute checksum, abort with clear error if missing. | FR‑001 | SC‑001 (power analysis) | `data/raw/` checksum file |
| **2** | **Purity filtering** – compute IoU for each bounding box; drop crops with IoU > 0.1 or OCR‑confidence < 0.8. | FR‑003 | SC‑001 | `data/interim/pure_crops.parquet` |
| **3** | **Model loading (CPU‑first)** – `transformers.AutoModel.from_pretrained("Qwen/Qwen-Image-VAE-2.0", torch_dtype=torch.float32, device_map="cpu")`. If OOM, raise `ModelUnavailableError`. | FR‑002 | SC‑004 | Log of model size, device |
| **4** | **Latent extraction** – encode each pure crop, store vectors as `.npy`. | FR‑003 | SC‑001 | `data/interim/latent_vectors.npy` |
| **5** | **Triviality check** – train a raw‑pixel logistic regression on the same unlabeled crops; report baseline accuracy. | FR‑004 (indirect) | SC‑001 | `triviality_flag` |
| **6** | **Disentanglement analysis** – train Linear SVM on latent vectors (train/val split). Compute Accuracy, F1. Perform 1 000‑permutation test, obtain p‑value. Apply Bonferroni correction (FR‑009). | FR‑004, FR‑007, FR‑008, FR‑009 | SC‑001, SC‑003 | `metrics.json` (accuracy, f1, p‑values, corrected p‑values) |
| **7** | **Linearity validation** – on a pilot set of 10 diverse samples, compute vector differences for text‑swap pairs; fit linear regression, report R². | FR‑005 | SC‑004 | `linearity_R2` |
| **8** | **Centroid computation** – mean vectors for text and image clusters (`μ_text`, `μ_image`). | FR‑005 | — | `centroids.npy` |
| **9** | **Zero‑shot editing** – for each test image: `z_new = z_doc - μ_text_old + μ_text_new`; decode with VAE; also generate baseline reconstruction (`decode(encode(z_doc))`). | FR‑006, FR‑010 | SC‑002 | `edited_images/`, `baseline_images/` |
| **10** | **OCR verification** – run PaddleOCR (CPU wheel) on edited image; compute character‑level match to target string (≥ 95%). | FR‑006 | SC‑002 | `ocr_results.json` |
| **11** | **Layout‑preservation metrics** – Masked SSIM (non‑text region), Edge Alignment Score (Canny + IoU), Keypoint Matching Score (SIFT + RANSAC). | FR‑006, FR‑010 | SC‑002 | `layout_metrics.json` |
| **12** | **Sensitivity analysis** – sweep SVM decision threshold ±5 % around optimal; log FPR/FNR curves. | FR‑008 | SC‑005 | `threshold_sweep.csv` |
| **13** | **Runtime & power reporting** – estimate per‑image CPU time; compute max feasible N under 6 h; report achieved power. | FR‑001 (indirect) | SC‑004 | `runtime_power.json` |
| **14** | **GPU escape hatch (conditional)** – if Phase 3 fails, rerun Phases 4‑11 on Kaggle GPU with `device="cuda"` and 8‑bit quantization, N = 100, log `cpu_feasibility: rejected`. | – | – | `gpu_demo/` |
| **15** | **Final aggregation** – assemble `output.schema.yaml`‑conformant JSON containing all metrics, power analysis, flags, and feasibility status. | – | SC‑001 – SC‑005 | `data/results/experiment_output.json` |

## Compute Feasibility Decision Rationale
- **CPU‑first**: The VAE encoder (≈ 3 GB) plus PaddleOCR (≈ 1 GB) fit comfortably inside the 7 GB limit when processed one crop at a time. All other steps are lightweight (scikit‑learn, NumPy).  
- **GPU fallback**: Reserved only for the *demonstration* of editing when CPU cannot load the model. The fallback runs on a Kaggle free GPU with `load_in_8bit=True` and a fixed seed (42) on 100 images, staying well under the 9‑hour kernel limit.

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset missing required fields | Fatal | Pre‑run validation aborts with explicit “Data Unavailable” message. |
| Model OOM on CPU | High | Trigger GPU escape hatch; record `cpu_feasibility: rejected`. |
| Low statistical power (power < 0.8) | Medium | Report “Inconclusive” with exact power value; do not fabricate additional samples. |
| Runtime exceeds 6 h | Medium | Perform power‑driven sample‑size reduction; if still infeasible, report “Inconclusive”. |
| Ambiguous regions (IoU > 0.1) | Low | Purity filter removes them; log count of excluded crops. |

## Output Contract
The pipeline must emit the following files (validated against the schemas in `contracts/`):
1. `data/results/metrics.json` (per‑metric values & significance).  
2. `data/results/plots/` (PCA scatter, edited image examples).  
3. `data/results/power_analysis.json`.  
4. `data/results/runtime_analysis.json`.  
5. `data/results/experiment_output.json` (conforms to `contracts/output.schema.yaml`).  

---
