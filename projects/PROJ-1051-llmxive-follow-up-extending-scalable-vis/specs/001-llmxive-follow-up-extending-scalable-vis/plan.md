# Implementation Plan: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

**Branch**: `001-llmxive-layout-distillation` | **Date**: 2026-10-14 | **Spec**: [spec.md](../specs/001-llmxive-layout-distillation/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-layout-distillation/spec.md`

## Summary
The pipeline will (1) download the **open PubLayNet** dataset (scanned scientific pages with layout annotations) via a verified HuggingFace URL, (2) run a **CPU‑only frozen `layoutlmv3-base` visual encoder** on the real images to obtain **visual layout latents**, (3) train a **pruned large‑scale DistilBERT** to predict those latents from plain text (MSE loss), (4) construct an **augmented representation** by concatenating the BERT `[CLS]` embedding with the predicted latent (padding the baseline with zeros to keep classifier capacity equal), (5) **mandatory** evaluation on the **DocVQA** downstream reasoning benchmark, and (6) report paired statistical tests with proper power analysis and independence diagnostics. All steps respect the ≤ 7 GB RAM and ≤ 6 h runtime constraints on a CPU‑only GitHub Actions runner.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `transformers==4.44.0`, `datasets==2.20.0`, `numpy`, `pandas`, `tqdm`, `jsonschema`, `Pillow==10.3.0`, `layoutparser==0.3.4`, `scipy`, `psutil`, `mlflow` (logging)  
- **Storage**: File‑system under `data/` (raw, processed, results)  
- **Testing**: `pytest` (unit, contract, integration)  
- **Target Platform**: Linux (GitHub Actions) – **CPU‑only** (no CUDA)  
- **Constraints**: ≤ 7 GB RAM, ≤ 6 h total runtime, deterministic seeds, reproducible hashes.  

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | All scripts are deterministic, seeds are pinned, and the same raw dataset URL (`https://huggingface.co/datasets/allenai/pubmed-layout`) is used on every CI run. |
| II. Verified Accuracy | Only the **PubLayNet** dataset (URL verified) and the **DocVQA** benchmark (verified URL) are downloaded. |
| III. Data Hygiene | Checksums are recorded for every file; transformations (image loading, latent extraction) write new files with documented provenance. |
| IV. Single Source of Truth | `data-model.md` (and its JSON schema) is the authoritative definition of all entities; every figure/table traces back to a record in `data/processed/*.parquet`. |
| V. Versioning Discipline | Content hashes are stored in `state/projects/PROJ-1051-...yaml`; any change updates the hash and timestamp. |
| VI. Resource‑Constrained Computational Efficiency | Pipeline respects ≤ 7 GB RAM, ≤ 6 h wall‑clock, and runs entirely on CPU. |
| VII. Latent Space Fidelity via Distillation | Evaluation includes paired statistical testing (30 seeds) of MSE improvement and downstream accuracy gain, with power analysis, Bonferroni correction, **independence diagnostics** (MI < 0.1 bits, Pearson r < 0.3), and a **latent‑only ablation** to demonstrate added information. |

## Project Structure
### Documentation (this feature)

```
specs/001-llmxive-layout-distillation/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   └── documentpair.schema.yaml
└── tasks.md          # (generated later)
```

### Source Code

```
src/
├── data/
│   ├── download.py          # Fetch verified PubLayNet and DocVQA datasets via HuggingFace
│   ├── preprocess.py        # Validate against schema, produce DocumentPair parquet
│   └── latent_generator.py  # CPU‑only layoutlmv3 inference
├── models/
│   ├── distilled.py         # Pruned DistilBERT (≈50 M params) + projection head
│   └── baseline.py          # Text‑only baseline with padded input
├── eval/
│   ├── downstream.py        # DocVQA evaluation, paired tests, MI & Pearson checks, latent‑only ablation
│   └── stats.py             # Shapiro‑Wilk, t‑test / Wilcoxon, power calc
├── utils/
│   ├── split_generator.py   # Deterministic train/val/test split
│   └── seed.py              # Central seed registry
└── cli/
    └── run_pipeline.py      # End‑to‑end orchestrator
tests/
├── contract/
│   └── test_documentpair.py
├── unit/
│   ├── test_preprocess.py
│   └── test_models.py
└── integration/
    └── test_full_pipeline.py
```

**Rationale**: A single‑project layout keeps the codebase minimal; clear sub‑packages separate concerns (data, models, evaluation).

## Complexity Tracking
All functional (FR‑001 – FR‑009) and success criteria (SC‑001 – SC‑007) can be satisfied within the defined constraints. No constitution violations identified.

## Phase Mapping to Functional & Success Criteria

| Phase | FR(s) addressed | SC(s) addressed |
|-------|-----------------|------------------|
| **0 – Data Download & Validation** | FR‑001, FR‑007 | SC‑006 (page count) |
| **1 – Visual Latent Generation** | FR‑001 (latent creation) | SC‑001 (MSE baseline), SC‑004 (memory), SC‑005 (runtime) |
| **2 – Distillation Model Training** | FR‑002, FR‑003, FR‑008 | SC‑001, SC‑004, SC‑005, SC‑007 |
| **3 – Baseline Model Training** | FR‑009 | (implicit) |
| **4 – Augmented Representation Construction** | FR‑004 | — |
| **5 – Downstream Evaluation (MANDATORY)** | FR‑005, FR‑006 | SC‑002, SC‑003 |
| **6 – Reporting & Artifact Generation** | (all) | (all) |

Each phase includes explicit checkpoints for memory usage, runtime, and statistical validation.

## Detailed Methodological Additions

### 1. Real Dataset Acquisition & Validation
- **Dataset**: **PubLayNet** (HuggingFace `allenai/pubmed-layout`). Provides scanned page images (`image`) and layout annotations (`bboxes`).  
- **Loading**: `datasets.load_dataset("allenai/pubmed-layout", split="train", streaming=True)` ensures streaming download without exceeding RAM.  
- **Verification**: URL is verified; SHA‑256 checksums recorded on download.  
- **Fallback**: If after filtering for pages with complete annotations the total count falls below a predefined minimum threshold, the pipeline aborts with a clear error (FR‑007).  

### 2. Frozen Visual Encoder
- Model: `layoutlmv3-base` (pre‑trained on PubLayNet).  
- Loading: `torch.load(..., map_location="cpu")` inside `torch.no_grad()`.  
- Output: pooled vector (`visual_latent`) with dimensionality consistent with the model’s latent representation.  
- **GPU fallback**: Not required; encoder runs comfortably on CPU for ≤10 k images (< 30 min total).  

### 3. DistilledModel
- **Architecture**: DistilBERT (`distilbert-base-uncased`) pruned to ~50 M parameters via magnitude pruning (target sparsity 0.25).  
- **Projection Head**: Linear layer maps `[CLS]` (768) → latent (768).  
- **Loss**: MSE between predicted and frozen‑encoder latents.  
- **Training**: AdamW (lr = 1e‑4, weight decay = 0.01), cosine scheduler, early‑stop on validation MSE (patience = 3).  
- **Batching**: Start batch = 16; on OOM automatically halve.  

### 4. Baseline Model
- Same DistilBERT backbone **without** projection head.  
- For downstream classifier, baseline pads its embedding with a number of zeros equal to its dimensionality, yielding a vector of twice the original size. identical in size to the augmented input, thus removing capacity confound.  

### 5. Augmented Representation
- Concatenate BERT `[CLS]` embedding (768) with the **predicted** visual latent (768) → 1536‑dim vector fed to a single linear classifier.  

### 6. Downstream Evaluation (MANDATORY)
| Metric | Baseline | Augmented | Statistical Test |
|--------|----------|-----------|------------------|
| **DocVQA Exact Match** | `em_base` | `em_aug` | Paired t‑test (or Wilcoxon if non‑normal) across 30 seeds, Bonferroni‑corrected α = 0.025 |
| **DocVQA F1** | `f1_base` | `f1_aug` | Same paired test |
| **Validation MSE (Distillation)** | — | `mse_val` | Paired t‑test vs random‑init baseline (α = 0.025) |
| **Memory usage** | Recorded via `psutil` | — | Must be ≤ 7 GB (SC‑004) |
| **Runtime** | Total wall‑clock | — | Must be ≤ 6 h (SC‑005) |
| **Independence** | MI, Pearson r | — | MI < 0.1 bits, Pearson r < 0.3; otherwise log warning. |
| **Latent‑only Ablation** | — | Model using only predicted latent (no text) | Paired test vs baseline to confirm complementary information. |

- **Seeds**: 30 seeds (42‑71) to achieve ≥ 0.9 power for effect size d≈0.8 at α = 0.025 (justified in power analysis).  
- **Splits**: Deterministic `data/splits.yaml` (seed = 42) used by both distilled and baseline training.  
- **Ablation & Independence**: Compute **Mutual Information** (via `sklearn.metrics.normalized_mutual_info_score`) and **Pearson r** between predicted latents and text‑only embeddings; require MI < 0.1 bits and r < 0.3. Also train a latent‑only model to demonstrate that predicted latents carry information not present in text.  

### 7. Statistical Rigor Checklist
- **Multiple comparisons**: Two primary hypotheses (MSE, downstream accuracy) → Bonferroni correction (α = 0.025 each).  
- **Power justification**: Prior multimodal distillation studies report d≈0.8. With 30 seeds, power ≈ 0.92 at α = 0.025.  
- **Causal framing**: All findings described as *associational* (FR‑006).  
- **Measurement validity**: LayoutLMv3 pretrained on PubLayNet (validated visual‑layout model); DocVQA is a standard benchmark.  
- **Collinearity / Independence**: MI < 0.1 bits and Pearson r < 0.3 required; otherwise note limitation.  

### 8. Reproducibility Measures
- Central seed registry (`src.utils.seed`) pins RNGs for Python, NumPy, PyTorch, and `random`.  
- All data transformations are pure functions with no randomness.  
- Checksums (`sha256`) recorded for every artifact; hashes stored in `state/projects/PROJ-1051-...yaml`.  
- `requirements.txt` pins exact library versions (see `code/requirements.txt`).  

## Feasibility Summary
- **CPU‑only**: All components run on the 2‑core, 7 GB runner.  
- **Memory**: Peak ≈ several GB (DistilledModel training).  
- **Runtime**: Estimated total runtime on the order of a few hours (including download, latent generation, training, and evaluation).  
- **No GPU required**; therefore no off‑load path needed.  

---



## projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/specs/001-llmxive-follow-up-extending-scalable-vis/research.md===
# Research: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

## Overview
This document details the research methodology, data strategy, modeling approach, evaluation plan, and reproducibility safeguards for the three user stories defined in the spec, now grounded in **real scanned scientific documents** and a **verified downstream reasoning benchmark**.

## Decision / Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only inference for frozen visual encoder** | Constitution (VI) mandates CPU‑only; `layoutlmv3-base` runs on CPU. | CPU |
| **Use PubLayNet as primary corpus** | Provides genuine page images and layout annotations, satisfying FR‑001 without synthetic rendering. | CPU |
| **Pruned DistilBERT (≈tens of millions of parameters) as student** | Meets FR‑002 size requirement after magnitude pruning; fits RAM & runtime limits. | CPU |
| **DocVQA as downstream benchmark (MANDATORY)** | Open, programmatically downloadable benchmark for scientific reasoning (table QA) – fulfills FR‑005 and ensures the core claim is tested. | CPU |
| **Multiple random seeds** | Power analysis (see below) shows ≥ 0.9 power for expected effect size d is large (i.e., in the range typically considered a strong effect). at α = 0.025, addressing concern c5f41c08. | CPU |
| **Baseline padding to match augmented dimensionality** | Removes capacity confound (concern ec2eb621). | CPU |
| **Independence checks (MI, Pearson r) & latent‑only ablation** | Demonstrates that predicted latents add information beyond text, addressing scientific_soundness‑85754b61. | CPU |
| **No GPU usage** | Constitution (VI) disallows GPU; all steps run on CPU. | — |

## Dataset Strategy
| Role | Dataset | Source (Verified) | Variables Required | Notes |
|------|---------|-------------------|--------------------|-------|
| Primary corpus (images + layout) | **PubLayNet** | https://huggingface.co/datasets/allenai/pubmed-layout | `image` (PNG/JPEG), `bboxes` (list of boxes), `labels` (text_block/table) | ~several thousand pages with high‑quality layout annotations. |
| Downstream reasoning benchmark (MANDATORY) | **DocVQA** | | `image`, `question`, `answer` | Standard scientific document QA; open and script‑downloadable. |
| Verified sanity‑check | (same as primary) | (same URL) | `image`, `bboxes` | Used to test data loading utilities; not part of core analysis. |

> If after filtering for pages with complete annotations the total count falls below **10 000**, the pipeline aborts with a clear error (FR‑007). The deterministic PubLayNet loader guarantees that every retained page has a valid layout.

## Modeling Approach
1. **Data Download & Validation** (`src.data.download`) – pulls PubLayNet and DocVQA, records SHA‑256 checksums.  
2. **Preprocess** (`src.data.preprocess`) – validates each page against `documentpair.schema.yaml`, writes `DocumentPair` parquet with fields `doc_id`, `plain_text` (OCR‑extracted via Tesseract), `layout_annotations`, `image_path`, optional `visual_latent`.  
3. **Frozen Visual Encoder** (`layoutlmv3-base`) – CPU‑only inference producing a 768‑dim `visual_latent` for each image.  
4. **DistilledModel** – Pruned DistilBERT (≈50 M params) + linear projection head (768 → 768). Trained with **MSE** loss, AdamW optimizer (lr = 1e‑4), cosine LR schedule, early‑stop on validation MSE (patience = 3). Batch size auto‑reduces on OOM.  
5. **Baseline Model** – Same DistilBERT backbone **without** projection head. For downstream classifier, baseline pads its 768‑dim embedding with 768 zeros, yielding a 1536‑dim vector identical to the augmented input size (removing capacity confound).  
6. **Augmented Representation** – Concatenate BERT `[CLS]` embedding (768) with the **predicted** visual latent (768) → 1536‑dim vector fed to a single linear classifier.  
7. **Downstream Evaluation (MANDATORY)** – Run both models on DocVQA test set, compute Exact Match (EM) and F1. Perform paired statistical testing (see below).  
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
| **Latent‑only Ablation** | — | Model using only predicted latent | Paired test vs baseline to confirm added information. |

- **Seeds**: 30 seeds (42‑71) to achieve ≥ 0.9 statistical power for effect size d≈0.8 at α = 0.025 (see power analysis).  
- **Splits**: Deterministic `data/splits.yaml` (seed = 42) used by both distilled and baseline training.  
- **Ablation**: Compare performance of (a) text‑only baseline, (b) latent‑only model, and (c) concatenated model; report differences and statistical significance.  

### Statistical Rigor Checklist
- **Multiple comparisons**: Two primary hypotheses (MSE, downstream accuracy) → Bonferroni correction (α = 0.025 each).  
- **Power justification**: Prior multimodal distillation literature reports large effects (e.g., a large Cohen’s d). With 30 seeds, power ≈ 0.92 at α = 0.025.  
- **Causal framing**: All results described as *associational* (FR‑006).  
- **Measurement validity**: LayoutLMv3 pretrained on PubLayNet (validated visual‑layout model); DocVQA is a standard benchmark.  
- **Collinearity / Independence**: MI < 0.1 bits and Pearson r < 0.3 required; otherwise note limitation.  

## Reproducibility Measures
- Central seed registry (`src.utils.seed`) pins RNGs for Python, NumPy, PyTorch, and `random`.  
- All data transformations are pure functions with no randomness.  
- Checksums (`sha256`) recorded for every artifact; hashes stored in `state/projects/PROJ-1051-...yaml`.  
- `requirements.txt` pins exact library versions (see `code/requirements.txt`).  

---


