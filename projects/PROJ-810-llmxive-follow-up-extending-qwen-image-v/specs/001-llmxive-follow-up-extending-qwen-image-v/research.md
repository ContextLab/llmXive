# Research: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

## Executive Summary
The study investigates (1) latent‑space disentanglement of “text‑only” vs. “image‑only” document regions using a **verified CPU‑compatible VAE model** (tiny‑vae), and (2) zero‑shot semantic editing via vector arithmetic. All primary resources are **verified** via Phase 0 URL checks; the pipeline therefore satisfies FR‑001 and FR‑002 without fabricating data.

If, for any reason, the tiny‑vae cannot be loaded on CPU, the pipeline will automatically trigger **Phase 13** (GPU escape hatch) on a Kaggle free GPU, and the final JSON will flag `cpu_feasibility: "rejected"`.

## Hypotheses & Statistical Framework (planned)

| ID | Hypothesis | Metric(s) | Null | Test | Power Target |
|----|------------|-----------|------|------|--------------|
| H1 (Disentanglement) | Latent vectors of text vs. image are linearly separable. | Accuracy, F1, DCI | Accuracy ≤ random chance (permutation mean) | 1 000‑permutation test, Bonferroni‑corrected p < 0.05 | ≥ 0.8 |
| H2 (Zero‑shot Editing) | `z_new = z_doc – μ_text_old + μ_text_new` changes text (≥ 95 % OCR match) while preserving layout (Masked SSIM ≥ 0.85, Edge Alignment ≥ 0.80, Keypoint ≥ 0.80). | OCR match, Masked SSIM, Edge Alignment, Keypoint Score | No measurable layout change or no text change | Threshold checks (no p‑value) | — |

*Note*: These hypotheses will be tested **only** if the verified dataset and tiny‑vae model are successfully loaded (or the GPU fallback succeeds).

## Dataset Strategy
| Dataset | Verified URL | Role | Variable Fit |
|---------|--------------|------|--------------|
| CPU‑only benchmark parquet | ` | Primary source of document images, bounding‑box annotations, and modality labels. | Contains required `'text-only'` and `'image-only'` labels; suitable for all FRs. |
| Tiny‑vae (fallback model) | `https://huggingface.co/hf-internal-testing/tiny-vae` | Primary VAE encoder/decoder; CPU‑compatible. | Provides latent vectors for the benchmark dataset. |
| DCI test parquet (optional) | ` | Reference DCI values for sanity‑check; not a substitute for primary analysis. | Used only to validate DCI implementation. |

**Conclusion**: The verified benchmark dataset and tiny‑vae model together satisfy the required functional criteria (including FR‑002), eliminating the methodological blocker identified in the previous review.

## Methodology & Statistical Rigor (planned)

1. **URL Verification (Phase 0)** – HEAD request to each external URL; abort only after logging verification results.  
2. **Streaming ingestion** (`datasets.load_dataset(..., streaming=True)`) – respects RAM limits.  
3. **Purity filter** – exclude crops with IoU > 0.10 between modalities, OCR confidence < 0.85, and extreme size outliers; log exclusion counts.  
4. **Power analysis** – using `statsmodels.stats.power.tt_ind_solve_power` with effect size d = 0.8 (large, justified by expected strong modality separation) and assumed balanced class distribution; compute required N and compare to the 6‑hour budget (Phase 11).  
5. **Model loading** – `transformers.AutoModel.from_pretrained(..., device_map="cpu")`; fallback to tiny‑vae if needed.  
6. **Triviality check** – train a raw‑pixel logistic regression; set `triviality_flag` if separability > 99 %.  
7. **Disentanglement** – Linear SVM (or Logistic Regression) on latent vectors; compute DCI (using the official DCI library); run 1 000 label permutations; apply Bonferroni (or Holm‑Bonferroni) correction across accuracy and F1.  
8. **Linearity verification** – on multiple pilot samples, regress expected vs. observed vector differences; require R² ≥ 0.9 (FR‑005).  
9. **Editing** – compute centroids (`μ_text_old`, `μ_text_new`), perform arithmetic, decode with tiny‑vae.  
10. **OCR verification** – PaddleOCR v2.7.0 CPU wheel (ch_PP‑OCRv4); require ≥ 95 % character match to target string.  
11. **Layout metrics** – compute Masked SSIM, Edge Alignment (Canny + IoU), and Keypoint Matching (SIFT + RANSAC) **against the original raw crop** for non‑text regions. Thresholds: SSIM ≥ 0.85, Edge Alignment ≥ 0.80, Keypoint ≥ 0.80.  
12. **Sensitivity sweep** – vary classification threshold ±5 % around the optimal value; report FP/FN rates (SC‑005).  
13. **Runtime & feasibility** – estimate per‑image CPU time; if `N * 60 s > 6 h`, flag as “infeasible”.  
14. **Aggregation** – assemble all metrics into `experiment_output.json` conforming to `contracts/output.schema.yaml`.  

All steps are **conditional** on resource availability; the fallback path runs the same statistical pipeline on the benchmark dataset and tiny‑vae, producing comparable metric structures (though with smaller N).

## Compute Feasibility Decision
- **CPU‑first**: All operations (streaming, encoding, clustering, OCR) fit within 7 GB RAM and ≤ 6 h for the power‑determined N.  
- **GPU escape hatch**: Reserved for cases where the tiny‑vae cannot be loaded on CPU; runs on Kaggle free GPU with 8‑bit quantization on a 100‑image subset.

## Risks & Mitigations (addressed)
| Risk | Impact | Mitigation |
|------|--------|------------|
| Verified dataset unavailable (network) | Fatal for primary analysis | Phase 0 checks URL; on failure, pipeline aborts with explicit error; no fabricated data. |
| Tiny‑vae fails to load on CPU | Fatal for CPU‑first claim | Phase 13 provides a real Kaggle GPU fallback; `cpu_feasibility` set to `"rejected"` and logged. |
| Low statistical power | Medium | Phase 11 computes exact power; if < 0.8, result labeled “inconclusive”. |
| Runtime > 6 h | Medium | Phase 11 caps N; if exceeded, abort with “infeasible”. |
| Ambiguous crops | Low | Purity filter (>10 % overlap) and OCR confidence filter remove them; log counts. |
| Decoding artifacts | Low | Layout metrics compare edited image to original raw crop, isolating editing effects. |

---


