# Research: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Executive Summary
We investigate whether the latent space of **Qwen‑Image‑VAE‑2.0** cleanly separates *text‑only* from *image‑only* document regions and whether simple vector arithmetic can swap textual content while preserving layout. Using the **Omni‑Doc‑1 (TokenBench subset)** dataset, we encode purified crops, train a Linear SVM, and evaluate disentanglement with DCI scores, permutation tests, and Bonferroni‑corrected significance. A pilot linearity validation (R² ≥ 0.9) precedes zero‑shot editing; edited outputs are assessed with OCR, Masked SSIM, Edge Alignment Score, and a SIFT‑based Keypoint Matching Score.

## Hypotheses & Statistical Framework
| ID | Hypothesis | Metric(s) | Null | Significance Test | Power Target |
|----|------------|-----------|------|-------------------|--------------|
| **H1** (Disentanglement) | Latent vectors of text vs. image are linearly separable. | Accuracy, F1, DCI | Accuracy ≤ random chance (permutation mean). | 1 000‑permutation test, Bonferroni‑corrected p < 0.05. | Power ≥ 0.8 for effect size *d* > 0.8. |
| **H2** (Zero‑shot Editing) | `z_new = z_doc – μ_text_old + μ_text_new` yields edited images with changed text (≥ 95 % OCR match) and preserved layout (Masked SSIM ≥ 0.85, Edge Alignment ≥ 0.80, Keypoint ≥ 0.80). | OCR match, Masked SSIM, Edge Alignment Score, Keypoint Matching Score | No measurable layout change (SSIM < 0.85 etc.) or no text change. | Threshold checks; no p‑value needed for continuous scores. | Not a hypothesis test; feasibility assessed via runtime ≤ 60 s per image. |

## Dataset Strategy
| Dataset | Verified URL | Role | Variable Fit Check |
|---------|--------------|------|--------------------|
| **Omni‑Doc‑1 (TokenBench subset)** | `https://huggingface.co/datasets/omnineura/Omni-Doc-1` | Source of document images, bounding‑box annotations, modality labels. | Provides `image`, `bbox`, `modality` fields required by FR‑001, FR‑003. |
| **DCI test parquet (for optional DCI metric)** | `https://huggingface.co/datasets/Mouwiya/image-in-Words400_DCI_Test/resolve/main/data/test-00000-of-00001.parquet` | Supplies DCI reference values if needed. | Contains `latent`‑level DCI columns; used only for reporting, not for primary analysis. |
| **CPU‑only benchmark parquet (optional sanity check)** | `https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet` | Provides a small CPU‑friendly sanity‑check dataset; not used for primary results. | Not required for FRs; included for debugging. |

**Note**: The TokenBench subset itself has *no* verified external URL; we therefore rely on the Omni‑Doc‑1 HF repository, which contains the required TokenBench split.

## Methodology & Statistical Rigor
1. **Streaming Ingestion** – `datasets.load_dataset(..., streaming=True)` to respect the 7 GB RAM limit.  
2. **Purity Filtering** – Compute IoU between text and image boxes; drop any crop with IoU > 0.1. Also drop crops where OCR confidence < 0.8.  
3. **Power Analysis** – Using `statsmodels.stats.power.tt_ind_solve_power`, estimate required `N` for power ≥ 0.8 given large effect size (Cohen’s d = 0.8). If `N * 60 s > 6 h`, mark result **inconclusive**.  
4. **Model Loading** – Attempt CPU load of `Qwen/Qwen-Image-VAE-2.0`. If `torch.cuda.is_available()` is **False** and loading fails, record `cpu_feasibility: rejected` and invoke the GPU escape hatch (scaled‑down).  
5. **Triviality Check** – Train a raw‑pixel logistic regression on the *same* unlabeled crops; if baseline accuracy > 90 % the disentanglement claim is flagged as **trivial**.  
6. **Disentanglement** – Linear SVM (`LinearSVC`) on latent vectors; compute Accuracy, F1, DCI (using `dci` package). Perform 1 000 permutations of modality labels; obtain empirical p‑value. Apply Bonferroni correction across Accuracy & F1 (FR‑009).  
7. **Linearity Validation** – For 10 pilot samples, compute `Δ = μ_text_new – μ_text_old` and test `z_doc + Δ ≈ z_target` via linear regression; require R² ≥ 0.9 (FR‑005).  
8. **Editing Pipeline** – Compute centroids, perform vector arithmetic, decode with VAE, generate baseline reconstruction.  
9. **OCR Verification** – PaddleOCR v2.7.0 (CPU wheel) with `ch_PP-OCRv4`; require ≥ 95 % character‑level match to target string.  
10. **Layout Metrics** –  
    - **Masked SSIM** (non‑text mask) ≥ 0.85.  
    - **Edge Alignment Score**: Canny edges → IoU ≥ 0.80.  
    - **Keypoint Matching Score**: SIFT + RANSAC inlier ratio ≥ 0.6 and matching ratio ≥ 0.75; overall score ≥ 0.80. (FR‑010)  
11. **Sensitivity Sweep** – Vary SVM decision threshold ±5 % around optimal; log FPR/FNR.  
12. **Reporting** – Consolidate all metrics into a JSON adhering to `contracts/output.schema.yaml`. Include flags (`triviality_flag`, `cpu_feasibility`, `linearity_verified`).  

## Compute Feasibility Decision
- **CPU‑First**: All components (VAE encoder, PaddleOCR, scikit‑learn) have CPU‑only wheels and are estimated to process a single crop in ≤ 0.5 s; total runtime ≤ 6 h for the power‑determined `N`.  
- **GPU Escape Hatch**: Activated only if the VAE cannot be instantiated on CPU. The fallback runs on a Kaggle free GPU with 8‑bit quantization, limited to 100 images, and records `cpu_feasibility: rejected`.  

## Risks & Mitigations
| Risk | Impact | Mitigation |
|------|--------|------------|
| Dataset missing `modality`/`bbox` | Fatal | Abort early with clear error; no downstream fabrication. |
| VAE OOM on CPU | High | GPU escape hatch; flag hypothesis as rejected. |
| Low power (≤ 0.8) | Medium | Report “Inconclusive” with exact power value. |
| Runtime > 6 h | Medium | Reduce `N` to the maximum feasible under the time budget; update power analysis accordingly. |
| Ambiguous crops | Low | Purity filter excludes them; log exclusion rate. |

---
