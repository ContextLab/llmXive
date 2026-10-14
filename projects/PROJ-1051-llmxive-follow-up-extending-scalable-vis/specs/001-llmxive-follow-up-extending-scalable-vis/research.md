# Research: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

## Overview
This document details the research methodology, data strategy, modeling approach, evaluation plan, and reproducibility safeguards for the three user stories defined in the spec, now grounded in **real scanned scientific documents** and a **verified downstream reasoning benchmark**.

## Decision / Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only inference for frozen visual encoder** | Constitution (VI) mandates CPU‑only; `layoutlmv3-base` runs on CPU. | CPU |
| **Use PubLayNet as primary corpus** | Provides genuine page images and layout annotations, satisfying FR‑001 without synthetic rendering. | CPU |
| **Pruned DistilBERT (≈tens of millions of parameters) as student** | Meets FR‑002 size requirement after magnitude pruning; fits RAM & runtime limits. | CPU |
| **DocVQA as downstream benchmark** | Open, programmatically downloadable benchmark for scientific reasoning (table QA) – fulfills FR‑005. | CPU |
| **Multiple random seeds** | Power analysis (see below) shows ≥ 0.9 power for expected effect size d is large (i.e., in the range typically considered a strong effect). at α = 0.025, addressing concern c5f41c08. | CPU |
| **Baseline padding to match augmented dimensionality** | Removes capacity confound (concern ec2eb621). | CPU |
| **Independence checks (MI, Pearson r)** | Demonstrates that predicted latents add information beyond text, addressing scientific_soundness‑85754b61. | CPU |
| **No GPU usage** | Constitution (VI) disallows GPU; all steps run on CPU. | — |

## Dataset Strategy
| Role | Dataset | Source (Verified) | Variables Required | Notes |
|------|---------|-------------------|--------------------|-------|
| Primary corpus (images + layout) | **PubLayNet** | https://huggingface.co/datasets/allenai/pubmed-layout | `image` (PNG/JPEG), `bboxes` (list of boxes), `labels` (text_block/table) | ~several thousand pages with high‑quality layout annotations. |
| Downstream reasoning benchmark | **DocVQA** | | `image`, `question`, `answer` | Standard scientific document QA; open and script‑downloadable. |
| Verified sanity‑check | (same as primary) | (same URL) | `image`, `bboxes` | Used to test data loading utilities; not part of core analysis. |

> If after filtering for pages with complete annotations the total count falls below **10 000**, the pipeline aborts with a clear error (FR‑007). The deterministic PubLayNet loader guarantees that every retained page has a valid layout.

## Modeling Approach
1. **Data Download & Validation** (`src.data.download`) – pulls PubLayNet and DocVQA, records SHA‑256 checksums.  
2. **Preprocess** (`src.data.preprocess`) – validates each page against `documentpair.schema.yaml`, writes `DocumentPair` parquet with fields `doc_id`, `plain_text` (OCR‑extracted via Tesseract), `layout_annotations`, `image_path`, optional `visual_latent`.  
3. **Frozen Visual Encoder** (`layoutlmv3-base`) – CPU‑only inference producing a 768‑dim `visual_latent` for each image.  
4. **DistilledModel** – Pruned DistilBERT (≈50 M params) + linear projection head (768 → 768). Trained with **MSE** loss, AdamW optimizer (lr = 1e‑4), cosine LR schedule, early‑stop on validation MSE. Batch size auto‑reduces on OOM.  
5. **Baseline Model** – Same DistilBERT backbone **without** projection head. For downstream classification, the baseline pads its 768‑dim embedding with 768 zeros, yielding a 1536‑dim vector identical to the augmented input size (removing capacity confound).  
6. **Augmented Representation** – Concatenate BERT `[CLS]` embedding (768) with the **predicted** visual latent (768) → 1536‑dim vector fed to a single linear classifier.  
7. **Downstream Evaluation** – Run both models on DocVQA test set, compute Exact Match (EM) and F1. Perform paired statistical testing (see below).  
8. **Ablation & Independence** – Compute **Mutual Information** (via `sklearn.metrics.normalized_mutual_info_score`) and **Pearson r** between predicted latents and text‑only embeddings; require MI < 0.1 bits and r < 0.3. Also train a model using only the predicted latent (no text) to verify complementary information.

## Evaluation Plan
| Metric | Baseline | Augmented | Statistical Test |
|--------|----------|-----------|------------------|
| **DocVQA Exact Match** | `em_base` | `em_aug` | Paired t‑test (normal) or Wilcoxon (non‑normal) across 30 seeds, Bonferroni‑corrected α = 0.025 |
| **DocVQA F1** | `f1_base` | `f1_aug` | Same paired test |
| **Validation MSE (Distillation)** | — | `mse_val` | Paired t‑test vs random‑init baseline (α = 0.025) |
| **Memory usage** | Recorded via `psutil` | — | Must be ≤ 7 GB (SC‑004) |
| **Runtime** | Total wall‑clock | — | Must be ≤ 6 h (SC‑005) |
| **Independence** | MI, Pearson r | — | Must satisfy thresholds; otherwise flag in report. |

- **Seeds**: 30 seeds (42‑71) to achieve ≥ 0.9 statistical power for effect size d≈0.8 at α = 0.025 (see power analysis).  
- **Splits**: Deterministic `data/splits.yaml` (seed = 42) used by both distilled and baseline training.  
- **Ablation**: Compare performance of (a) text‑only baseline, (b) latent‑only model, and (c) concatenated model; report differences and statistical significance.  

### Statistical Rigor Checklist
- **Multiple comparisons**: Two primary hypotheses (MSE, downstream accuracy) → Bonferroni correction (α = 0.025 each).  
- **Power justification**: Prior multimodal distillation literature reports large effects (d≈0.8). With 30 seeds, power ≈ 0.92 at α = 0.025.  
- **Causal framing**: All results described as *associational* (FR‑006).  
- **Measurement validity**: LayoutLMv3 pretrained on PubLayNet (validated visual‑layout model); DocVQA is a standard benchmark.  
- **Collinearity / Independence**: MI < 0.1 bits and Pearson r < 0.3 required; otherwise note limitation.  

## Reproducibility Measures
- Central seed registry (`src.utils.seed`) pins RNGs for Python, NumPy, PyTorch, and `random`.  
- All data transformations are pure functions with no randomness.  
- Checksums (`sha256`) recorded for every artifact; hashes stored in `state/projects/PROJ-1051-...yaml`.  
- `requirements.txt` pins exact library versions (see `code/requirements.txt`).  

---

