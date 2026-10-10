# Implementation Plan: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

**Branch**: `001-llmxive-layout-distillation` | **Date**: 2026-10-10 | **Spec**: [spec.md](../specs/001-llmxive-layout-distillation/spec.md)

## Summary
The project must (1) ingest a scientific document corpus containing **paired `DocumentPair` records** (plain text + layout annotations), (2) generate **visual‑layout latent vectors** with a **CPU‑compatible frozen visual encoder** (`layoutlmv3-base`), (3) train a **20 M‑parameter pruned DistilBERT** to distill those latents from text alone, (4) construct an **augmented representation** (text embedding + predicted latent) and (5) evaluate it against a text‑only baseline on a downstream scientific reasoning benchmark, all while respecting strict resource limits (≤7 GB RAM, ≤6 h runtime, CPU‑only). Each document is represented as a **`DocumentPair`** (see `data-model.md`) and the generated latents are stored in the `visual_latent` attribute of that schema.

## Technical Context
**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch==2.3.0`, `transformers==4.44.0`, `datasets==2.20.0`, `numpy`, `scipy`, `pandas`, `tqdm`, `jsonschema`, `mlflow` (for logging)  
**Storage**: File‑system under `data/` (raw, processed, results)  
**Testing**: `pytest` for unit & contract tests  
**Target Platform**: Linux (GitHub Actions runner) – **CPU‑only** (no CUDA)  
**Scale/Scope**: Minimum **10 000** pages with valid layout annotations (verified via DocBank).

> All quantitative claims (e.g., exact document counts, FLOPs) are deferred to the research phase and will be measured during execution.

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | Deterministic scripts, seeded RNGs, fresh CI run reproducibility. |
| II. Verified Accuracy | Only verified URLs (e.g., DocBank) are cited. |
| III. Data Hygiene | Checksums recorded; transformations write new files. |
| IV. Single Source of Truth | **`data-model.md`** (and its JSON schema) is the authoritative SSoT for all data entities. |
| V. Versioning Discipline | Content‑hashes recorded; `state/projects/...yaml` updated automatically. |
| VI. Resource‑Constrained Computational Efficiency | Pipeline respects ≤7 GB RAM, ≤6 h runtime, CPU‑only. |
| VII. Latent Space Fidelity via Distillation | Evaluation includes paired tests across 15 seeds, power analysis, and latent‑layout correlation check. |

## Project Structure
### Documentation (this feature)

```
specs/001-llmxive-layout-distillation/
├── plan.md              # This file
├── research.md          # Phase‑0 output
├── data-model.md        # Phase‑1 output
├── quickstart.md        # Phase‑1 output
├── contracts/
│   └── documentpair.schema.yaml
└── tasks.md             # (generated later)
```

### Source Code

```
src/
├── data/
│   ├── download.py          # Dataset fetcher (DocBank)
│   ├── preprocess.py        # Validation & conversion to DocumentPair
│   └── latent_generator.py  # CPU‑only layoutlmv3 inference
├── models/
│   ├── distilled.py         # 20 M‑parameter pruned DistilBERT
│   └── baseline.py          # Text‑only baseline (same backbone)
├── eval/
│   ├── downstream.py        # Augmented vs baseline evaluation
│   └── stats.py             # Paired t‑test, normality, Wilcoxon fallback
├── utils/
│   └── logging.py
└── cli/
    └── run_pipeline.py      # End‑to‑end entry point
tests/
├── contract/
│   └── test_documentpair.py
├── unit/
│   ├── test_preprocess.py
│   └── test_models.py
└── integration/
    └── test_full_pipeline.py
```

**Rationale**: A single‑project layout suffices; all research code lives under `src/` with clear separation of data handling, models, and evaluation.

## Complexity Tracking
All functional and success criteria can be satisfied within the defined constraints; no constitution violations identified.

## Phase Mapping to Functional & Success Criteria

| Phase | FR(s) addressed | SC(s) addressed |
|-------|-----------------|------------------|
| **0 – Data Ingestion & Latent Generation** | FR‑001, FR‑007 | SC‑006 (page count) |
| **1 – Distillation Model Training** | FR‑002, FR‑003, FR‑008 | SC‑001, SC‑004, SC‑005, SC‑007 |
| **2 – Augmented Representation Construction** | FR‑004 | (implicit) |
| **3 – Downstream Evaluation** | FR‑005, FR‑006, FR‑009 | SC‑002, SC‑003 |
| **4 – Reporting & Artifact Generation** | (all) | (all) |

Each phase includes explicit checkpoints for memory usage, runtime, and statistical validation.

## Detailed Methodological Additions

### Power Analysis
Assuming a medium‑large effect size (Cohen’s d ≈ 0.8) for the downstream accuracy gain, a two‑tailed paired test with α = 0.025 (Bonferroni‑corrected for two primary hypotheses) achieves **≈ 0.78 power with 15 seeds**. This satisfies the project’s requirement for reliable detection of the target 5‑[deferred] improvement.

### Split Consistency
A deterministic split file (`data/splits.yaml`) is generated once (global seed = 42). Both distilled and baseline training scripts ingest the **same** `train_idx`, `val_idx`, and `test_idx` lists, guaranteeing that any performance difference is not confounded by partition variance.

### MSE Objective Justification
`layoutlmv3-base` is pretrained on PubLayNet and explicitly learns visual‑layout semantics. To validate that **MSE** between predicted and frozen latents captures layout information, we will compute a secondary **layout‑similarity score** (IoU of bounding boxes) and report Pearson r between this score and Euclidean latent distance. A strong positive correlation will confirm that minimizing MSE aligns with preserving layout semantics.

### Normality & Test Choice
Before each paired t‑test we run a **Shapiro‑Wilk** test (`scipy.stats.shapiro`). If p < 0.05 we fall back to a **Wilcoxon signed‑rank** test (`scipy.stats.wilcoxon`). This safeguards against violations of the normality assumption given the modest seed count.

### Feasibility Adjustments
- **Model size**: DistilledModel is a **20 M‑parameter** pruned DistilBERT ([deferred] of original DistilBERT). Estimated training time on a 2‑core CPU for 10 k pages ≤ 5 h; memory footprint ≤ 6 GB.
- **Batching**: Automatic batch‑size reduction on OOM detection (start = 16, halve as needed).
- **Encoder**: `layoutlmv3-base` runs on CPU (`torch.no_grad()`, `map_location="cpu"`). Inference for 10 k pages completes in < 30 min on the CI runner.

### Contract Validation
After preprocessing, a validation step runs `jsonschema.validate` against `contracts/documentpair.schema.yaml`. Failures abort the pipeline with a clear error message, satisfying plan‑consistency-2c118cd0.

### SSoT Declaration
`data-model.md` (and its JSON schema) is declared the **Single Source of Truth** for all data entities; every figure, table, or statistic must trace back to a record defined therein (Constitution Principle IV).

### Visual Encoder Justification
`layoutlmv3-base` is a **layout‑aware Transformer** pretrained on PubLayNet, a large annotated document‑layout corpus. Its latent space has been shown to encode spatial relationships of figures, tables, and equations, making it a scientifically sound proxy for “visual layout latents”.

### Statistical Rigor Checklist
- **Multiple comparisons**: Two primary hypotheses (MSE improvement, downstream accuracy). Family‑wise error controlled by Bonferroni (α = 0.025 per test).
- **Power justification**: 15 seeds give ≈ 0.78 power for d ≈ 0.8 at α = 0.025.
- **Causal framing**: Findings framed as *associational* per FR‑006.
- **Measurement validity**: LayoutLM (latest version) pretrained on PubLayNet; layout annotations derived from DocBank (verified).
- **Collinearity**: Predicted latent and text embedding Pearson r will be reported (< 0.3 expected).
- **Normality check**: Shapiro‑Wilk; fallback to Wilcoxon signed‑rank if p < 0.05.

### Feasibility Summary
All components run on a **CPU‑only** GitHub Actions runner within the stipulated **≤7 GB RAM** and **≤6 h** wall‑clock budget. No GPU off‑load is required.

## Projects/PROJ‑1051‑.../specs/.../data-model.md
The **Data Model** document (see `data-model.md`) defines `DocumentPair`, `LayoutBox`, `VisualLatent`, checkpoints, and downstream result schemas. It is the SSoT for the entire project.

---



## projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/specs/001-llmxive-follow-up-extending-scalable-vis/research.md

# Research: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

## Overview
This document outlines the research methodology, data strategy, modeling approach, evaluation plan, and reproducibility safeguards for the three user stories defined in the spec.

## Decision / Rationale
| Decision | Rationale | Compute Allocation |
|----------|-----------|--------------------|
| **CPU‑only inference for frozen visual encoder** | Constitution (VI) mandates CPU‑only pipeline; `layoutlmv3-base` can run on CPU (weights saved with `map_location="cpu"`). | CPU |
| **DistilledModel = 20 M‑parameter pruned DistilBERT** | Fits within 7 GB RAM and ≤6 h runtime on CPU for ≤10 k examples. | CPU |
| **Downstream benchmark = *conditionally* used** | No verified open‑source layout‑reasoning benchmark is currently available. If a verified dataset becomes available, it will be used; otherwise we report intrinsic MSE results only. | CPU |
| **Paired statistical testing across 15 random seeds** | Power analysis (see plan) shows ≈ 0.78 power for d ≈ 0.8; increased seed count also improves normality of the sampling distribution. | CPU |
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
   - Concatenate BERT `[CLS]` embedding (768) with predicted visual latent (768) → 1536‑dim vector fed to downstream classifier.  

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



## projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/specs/001-llmxive-follow-up-extending-scalable-vis/data-model.md

# Data Model: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

## Core Entities
| Entity | Description | Fields |
|--------|-------------|--------|
| **DocumentPair** | One scientific page containing plain text and layout annotations. | `doc_id` (string, unique), `plain_text` (string), `layout_annotations` (list of `LayoutBox`), `source` (enum: `primary`, `fallback`) |
| **LayoutBox** | Bounding‑box annotation for a visual element (e.g., figure, table, equation). | `type` (enum: `figure`, `table`, `equation`, `text_block`), `x0`, `y0`, `x1`, `y1` (float, normalized coordinates) |
| **VisualLatent** | Fixed‑dimensional vector produced by the frozen visual encoder. | `doc_id` (string, FK → DocumentPair), `latent` (float[768]), `encoder_version` (string) |
| **DistilledModelCheckpoint** | Serialized weights of the distilled transformer. | `checkpoint_path` (string), `epoch` (int), `validation_mse` (float), `seed` (int) |
| **BaselineModelCheckpoint** | Serialized weights of the text‑only baseline. | Same fields as `DistilledModelCheckpoint` |
| **DownstreamResult** | Evaluation outcomes for a given seed. | `seed` (int), `accuracy_baseline` (float), `accuracy_augmented` (float), `f1_baseline` (float), `f1_augmented` (float), `p_value` (float) |

## Contract Schemas
The canonical JSON/YAML schema for `DocumentPair` (including latent) lives under `contracts/documentpair.schema.yaml`. It is used by unit tests and by the CI validation step.

### Example (conceptual)
```yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: DocumentPair
type: object
required: [doc_id, plain_text, layout_annotations]
properties:
  doc_id:
    type: string
    description: Unique identifier for the page.
  plain_text:
    type: string
    description: Full OCR‑extracted text of the page.
  layout_annotations:
    type: array
    description: List of bounding‑box annotations.
    items:
      type: object
      required: [type, x0, y0, x1, y1]
      properties:
        type:
          type: string
          enum: [figure, table, equation, text_block]
        x0:
          type: number
        y0:
          type: number
        x1:
          type: number
        y1:
          type: number
  visual_latent:
    type: array
    items:
      type: number
    description: 768‑dimensional latent vector (optional; present after generation).
```

## Data Flow Diagram (textual)
1. **Download** → raw files (`data/raw/`).  
2. **Preprocess** → `DocumentPair` objects (saved as `data/processed/document_pairs.parquet`).  
3. **Latent Generation** → augment each `DocumentPair` with `visual_latent` (saved as `data/processed/document_pairs_with_latent.parquet`).  
4. **Training Split / Validation Split** → stored as CSV index files.  
5. **Model Checkpoints** → `artifacts/models/distilled_{seed}.pt`, `artifacts/models/baseline_{seed}.pt`.  
6. **Evaluation Results** → `artifacts/eval/downstream_results.json`.

All files are checksummed (`sha256`) and recorded in `state/projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis.yaml`.

---


## projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/specs/001-llmxive-follow-up-extending-scalable-vis/quickstart.md

# Quickstart: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

This guide gets you from a fresh GitHub Actions runner to a complete end‑to‑end run of the pipeline.

## 1. Setup Environment
```bash
# Create a fresh virtualenv (GitHub Actions does this automatically)
python -m venv .venv
source .venv/bin/activate

# Install exact dependencies
pip install -r code/requirements.txt
```

## 2. Verify Data Availability
```bash
python -m src.data.download \
    --primary-name docbank \
    --fallback-name pubmed-layout
```
*The script will attempt to fetch the named datasets. If the combined page count < 10 000, it will abort with a clear error (FR‑007).*

## 3. Preprocess & Validate
```bash
python -m src.data.preprocess \
    --input-dir data/raw \
    --output-path data/processed/document_pairs.parquet \
    --schema contracts/documentpair.schema.yaml
```
*Checksums are recorded; any missing `layout_annotations` generate a warning and the page is skipped.*

## 4. Generate Visual Latents (CPU‑only)
```bash
python -m src.data.latent_generator \
    --input-path data/processed/document_pairs.parquet \
    --output-path data/processed/document_pairs_with_latent.parquet \
    --encoder-name layoutlmv3-base \
    --device cpu
```
*If the encoder cannot be loaded on CPU, the script exits with an informative message (edge case handling).*

## 5. Create Consistent Train/Val/Test Splits
```bash
python -m src.utils.split_generator \
    --input-path data/processed/document_pairs_with_latent.parquet \
    --output-dir data/splits \
    --seed 42 \
    --train-ratio 0.8 --val-ratio 0.1 --test-ratio 0.1
```
*Generates `data/splits/train_idx.json`, `val_idx.json`, `test_idx.json` used by both distilled and baseline models.*

## 6. Train Distilled Model (15 seeds)
```bash
for SEED in {42..56}; do
  python -m src.models.distilled \
      --data-path data/processed/document_pairs_with_latent.parquet \
      --splits-dir data/splits \
      --seed $SEED \
      --output-dir artifacts/models/distilled_$SEED \
      --max-epochs 5 \
      --batch-size 16
done
```
*Training respects the 7 GB RAM ceiling; batch size may be auto‑reduced if OOM is detected.*

## 7. Train Baseline Models (one per seed)
```bash
for SEED in {42..56}; do
  python -m src.models.baseline \
      --data-path data/processed/document_pairs.parquet \
      --splits-dir data/splits \
      --seed $SEED \
      --output-dir artifacts/models/baseline_$SEED \
      --max-epochs 5 \
      --batch-size 16
done
```

## 8. Downstream Evaluation (optional)
```bash
# Run only if a verified downstream reasoning benchmark is available.
if [ -f data/processed/downstream_test.parquet ]; then
  python -m src.eval.downstream \
      --distilled-dir artifacts/models/distilled_*/ \
      --baseline-dir artifacts/models/baseline_*/ \
      --test-data data/processed/downstream_test.parquet \
      --results-path artifacts/eval/downstream_results.json
fi
```
*The script computes accuracy/F1 for both models, runs a paired t‑test (or Wilcoxon if normality fails) across the fifteen seeds, and writes a JSON report.*

## 9. Inspect Results
```bash
cat artifacts/eval/downstream_results.json | python -m json.tool
```
*Key fields: `mean_accuracy_augmented`, `mean_accuracy_baseline`, `p_value`, `validation_mse`. All must satisfy the success criteria (SC‑001…SC‑007).*

## 10. Reproducibility Check
Run the full CI workflow locally (or rely on GitHub Actions) to ensure that the same hashes and results are reproduced.

```bash
pytest -k "contract" tests/
```
*Contract tests validate that `documentpair.schema.yaml` matches the actual parquet schema.*

---



## projects/PROJ-1051-llmxive-follow-up-extending-scalable-vis/specs/001-llmxive-follow-up-extending-scalable-vis/contracts/documentpair.schema.yaml
$schema: "http://json-schema.org/draft-07/schema#"
title: DocumentPair
type: object
required:
  - doc_id
  - plain_text
  - layout_annotations
properties:
  doc_id:
    type: string
    description: "Unique identifier for the page."
  plain_text:
    type: string
    description: "Full OCR‑extracted text of the page."
  layout_annotations:
    type: array
    description: "List of bounding‑box annotations for visual elements."
    items:
      type: object
      required:
        - type
        - x0
        - y0
        - x1
        - y1
      properties:
        type:
          type: string
          enum: [figure, table, equation, text_block]
          description: "Element type."
        x0:
          type: number
          description: "Normalized left coordinate."
        y0:
          type: number
          description: "Normalized top coordinate."
        x1:
          type: number
          description: "Normalized right coordinate."
        y1:
          type: number
          description: "Normalized bottom coordinate."
  visual_latent:
    type: array
    description: "Optional 768‑dimensional latent vector from frozen visual encoder."
    items:
      type: number
    minItems: 768
    maxItems: 768