# Research: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

## Overview
This document outlines the research methodology, data strategy, modeling approach, evaluation plan, and reproducibility safeguards for the three user stories defined in the spec.

## Decision / Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only inference for frozen visual encoder** | Constitution (VI) mandates CPU‑only pipeline; `layoutlmv3-base` can run on CPU (weights saved with `map_location="cpu"`). | CPU |
| **DistilledModel = 20 M‑parameter pruned DistilBERT** | Fits within 7 GB RAM and ≤6 h runtime on CPU for ≤10 k examples. | CPU |
| **Downstream benchmark = *conditionally* used** | No verified open‑source layout‑reasoning benchmark is currently available. If a verified dataset becomes available, it will be used; otherwise we report intrinsic MSE results only. | CPU |
| **Paired statistical testing across multiple random seeds** | Power analysis (see plan) indicates a high level of statistical power for an effect size of approximately d ≈ 0.8.; increased seed count also improves normality of the sampling distribution. | CPU |
| **No GPU usage** | Constitution (VI) disallows GPU except for scaled‑down off‑load; all components run on CPU. | — |

## Dataset Strategy
| Role | Dataset | Source (Verified) | Variables Required | Notes |
|------|---------|-------------------|--------------------|-------|
| Primary corpus (text + layout) | `docbank` (subset) | | `plain_text`, `layout_annotations` | Provides ≥10 000 pages with bounding‑box annotations. |
| Fallback corpus | `pubmed-layout` (open subset) | | Same as primary | Used only if primary subset falls short of the 10 k page minimum. |
| **Verified dataset (sanity‑check)** | MixSub‑LLaMA‑3.2 Text‑Only Overlap CPU Score | https://huggingface.co/datasets/AdityaMayukhSom/MixSub-LLaMA-3.2-Text-Only-Overlap-CPU-Score/resolve/main/data/train-00000-of-00001.parquet | `text` | Used to test data loading utilities; not part of the core visual‑layout study. |

> **Important**: If after attempting both primary and fallback sources the total valid page count is < 10 000, the pipeline aborts with a clear error (FR‑007).

## Modeling Approach
1. **Frozen Visual Encoder**  
   - Architecture: `layoutlmv3-base` (layout‑aware ViT) saved for CPU inference.  
   - Inference: `torch.no_grad()`; output is a fixed‑dimensional vector (`D=768`).  
2. **DistilledModel**  
   - Base: Pruned DistilBERT (~20 M parameters).  
   - Head: Linear projection from `[CLS]` embedding (size = 768) to visual latent dimension (`D`).  
   - Loss: **Mean Squared Error (MSE)** between predicted and frozen‑encoder latents.  
   - Optimizer: AdamW (lr = 1e‑4, weight decay = 0.01).  
   - Scheduler: Linear warm‑up for first [deferred] steps, then cosine decay.  
   - Early‑stop: Patience = 3 epochs on validation MSE.  
   - **MSE justification**: We will compute a secondary **layout‑similarity score** (IoU of bounding boxes) and report Pearson r between this score and Euclidean distance in latent space; a strong correlation validates MSE as a proxy for layout semantics.  
3. **Baseline Text‑Only Model**  
   - Same pruned DistilBERT architecture but without the projection head; trained on the same text inputs for the downstream task.  
4. **Augmented Representation**  
   - Concatenate the BERT `[CLS]` embedding with the predicted visual latent representation, resulting in a combined vector whose dimensionality is twice that of each individual component. fed to downstream classifier.  

## Evaluation Plan
| Metric | Baseline | Augmented | Statistical Test |
|--------|----------|-----------|------------------|
| Accuracy / F1 (if downstream dataset available) | `acc_base` | `acc_aug` | Paired t‑test (or Wilcoxon if normality fails) across 15 seeds (α = 0.025 per Bonferroni) |
| Validation MSE (Distillation) | — | `mse_val` | Paired t‑test vs random‑init baseline (α = 0.025) |
| Memory usage | Recorded via `psutil` | — | Must be ≤ 7 GB (SC‑004) |
| Runtime | Total wall‑clock time | — | Must be ≤ 6 h (SC‑005) |

All seeds (15) are fixed (`seed=42…56`). The baseline model is **re‑trained for each seed** to satisfy FR‑009. A single deterministic split file (`data/splits.yaml`) is generated once (global seed = 42) and consumed by both distilled and baseline training scripts, guaranteeing identical data partitions.

If a verified downstream reasoning benchmark is unavailable, we will report only the intrinsic MSE results and the associated statistical validation.

## Statistical Rigor Checklist
- **Multiple comparisons**: Two primary hypotheses (MSE improvement, downstream accuracy). Family‑wise error controlled by Bonferroni (α = 0.025 per test).  
- **Power justification**: 15 seeds give ≈ 0.78 power for d ≈ 0.8 at α = 0.025.  
- **Causal inference**: Findings framed as *associational* per FR‑006.  
- **Measurement validity**: LayoutLM (latest version) pretrained on PubLayNet; layout annotations derived from DocBank (verified).  
- **Collinearity**: Predicted latent and text embedding Pearson r will be reported (< 0.3 expected).  
- **Normality check**: Shapiro‑Wilk test; fallback to Wilcoxon signed‑rank if p < 0.05.  

## Reproducibility Measures
- All random seeds pinned in `src/utils/seed.py`.  
- Deterministic data shuffling (`torch.utils.data.RandomSampler` with `generator=torch.Generator().manual_seed(seed)`).  
- Checkpoints and logs stored under `artifacts/` with content hashes.  
- `requirements.txt` pins exact library versions (see `code/requirements.txt`).  

---

