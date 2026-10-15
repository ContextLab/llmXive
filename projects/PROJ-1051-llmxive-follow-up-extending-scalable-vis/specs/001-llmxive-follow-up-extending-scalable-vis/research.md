# Research: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

## Overview
This document details the research methodology, data strategy, modeling approach, evaluation plan, and reproducibility safeguards for the three user stories defined in the spec.

## Decision / Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only inference for frozen visual encoder** | Constitution (VI) mandates CPU‑only; ResNet‑18 runs comfortably on CPU. | CPU |
| **Programmatic layout-aware dataset load** | Ensures the presence of images and bounding boxes required for visual latent generation (FR-001), avoiding text-only datasets. | CPU |
| **Pruned DistilBERT (≈ reduced‑parameter model) as student** | Meets FR‑002 size requirement after pruning; fits RAM & runtime limits. | CPU |
| **DocVQA with Val/Test split** | Prevents overfitting of hyperparameters to the test set, ensuring internal validity of reported gains. | CPU |
| **Baseline with random projection head** | Controls for parameter capacity; ensures any gain is due to the *quality* of the latent, not the presence of extra weights. | CPU |
| **Construct Validity Analysis** | Validates that ImageNet-pretrained ResNet-18 actually captures layout-relevant features in scientific documents. | CPU |
| **Multiple random seeds (several)** | Power analysis shows ≥ 0.9 power for expected large effect size at α = 0.025. | CPU |

## Dataset Strategy
| Role | Dataset | Source (Verified) | Variables Required | Notes |
|------|---------|-------------------|--------------------|-------|
| Primary corpus (text + layout) | **Layout-Aware Corpus** | `datasets.load_dataset("llmXive/layout-distillation")` (or fallback `pubmed-layout`) | `plain_text`, `layout_annotations`, `image` | Programmatic load ensures multimodal pairing. |
| Downstream reasoning benchmark | **DocVQA** | `datasets.load_dataset("docvqa")` | `image`, `question`, `answer` | Standard scientific document QA. |

> If after filtering for rows with complete `layout_annotations` and images the total count falls below **10 000**, the pipeline aborts with a clear error (FR‑007).

## Modeling Approach
1. **Data Download & Validation** (`src.data.download`) – pulls the layout corpus and DocVQA via programmatic loaders, records SHA‑256 checksums.  
2. **Preprocess** (`src.data.preprocess`) – validates each row against `documentpair.schema.yaml`, writes `DocumentPair` parquet.  
3. **Frozen Visual Encoder** (`ResNet‑18`) – CPU‑only inference producing a 512‑dim `visual_latent`.
4. **Construct Validity Check** – Correlate `visual_latent` with layout-complexity metrics (e.g., block count). Require $|r| > 0.2$ to proceed.
5. **DistilledModel** – Pruned DistilBERT (≈50 M params) + linear projection head (high‑dimensional input → 512). Trained with **MSE** loss, AdamW, early‑stop on validation MSE.
6. **Baseline Model** – Same DistilBERT backbone + **frozen random projection head** (768 → 512). This matches the augmented model's capacity and dimensionality.
7. **Augmented Representation** – Concatenate BERT `[CLS]` (768) with predicted visual latent (512) → 1280‑dim vector.
8. **Downstream Evaluation (MANDATORY)** – Split DocVQA into **Validation ([deferred])** and **Test ([deferred])**. Tune hyperparameters on Validation; report final EM/F1 on Test.

## Evaluation Plan
| Metric | Baseline | Augmented | Statistical Test |
|--------|----------|-----------|------------------|
| **DocVQA Exact Match** | `em_base` | `em_aug` | Paired t‑test (normal) or Wilcoxon (non‑normal) across multiple seeds, Bonferroni‑corrected α = 0.025 |
| **DocVQA F1** | `f1_base` | `f1_aug` | Same paired test |
| **Validation MSE (Distillation)** | — | `mse_val` | Paired t‑test vs random‑init baseline (α = 0.025) |
| **Memory usage** | Recorded via `psutil` | — | Must be ≤ 7 GB (SC‑004) |
| **Runtime** | Total wall‑clock | — | Must be ≤ 6 h (SC‑005) |
| **Independence** | MI, Pearson r | — | Must satisfy thresholds (MI < 0.1, r < 0.3). |
| **Latent‑only Ablation** | — | Model using only predicted latent | Paired test vs baseline to confirm added information. |

### Statistical Rigor Checklist
- **Multiple comparisons**: Two primary hypotheses (MSE, downstream accuracy) → Bonferroni correction (α = 0.025 each).
- **Power justification**: With 30 seeds, power ≈ 0.92 for d≈0.8 at α = 0.025.
- **Causal framing**: All results described as *associational* (FR‑006).
- **Measurement validity**: ResNet-18 construct validity verified via layout-correlation check. DocVQA is a standard benchmark.
- **Collinearity / Independence**: MI < 0.1 bits and Pearson r < 0.3 required.

## Reproducibility Measures
- Central seed registry (`src.utils.seed`) pins RNGs.
- All data transformations are pure functions.
- Checksums (`sha256`) recorded for every artifact.
- `requirements.txt` pins exact library versions.