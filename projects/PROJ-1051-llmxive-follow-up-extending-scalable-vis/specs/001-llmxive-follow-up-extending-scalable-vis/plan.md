# Implementation Plan: llmXive follow-up: extending "Scalable Visual Pretraining for Language Intelligence"

**Branch**: `001-llmxive-layout-distillation` | **Date**: 2026-10-15 | **Spec**: [spec.md](../specs/001-llmxive-layout-distillation/spec.md)  
**Input**: Feature specification from `/specs/001-llmxive-layout-distillation/spec.md`

## Summary
The pipeline will (1) programmatically load a **layout-aware scientific document corpus** containing text, images, and layout annotations, (2) run a **CPU‑only frozen ResNet‑18 visual encoder** to obtain 512‑dim visual layout latents (ground‑truth targets), (3) train a **pruned DistilBERT (≈50 M parameters)** to predict those latents from plain text using MSE loss, (4) build an **augmented representation** by concatenating the BERT `[CLS]` embedding with the predicted latent, (5) evaluate the augmented model against a **DocVQA** downstream reasoning benchmark using a separate validation/test split, and (6) report paired statistical tests, power analysis, and independence diagnostics. All steps respect the ≤ 7 GB RAM, ≤ 6 h wall‑clock, CPU‑only constraints.

## Technical Context
- **Language/Version**: Python 3.11  
- **Primary Dependencies**: `torch==2.3.0`, `torchvision==0.18.0`, `transformers==4.44.0`, `datasets==2.20.0`, `numpy`, `pandas`, `pyarrow`, `tqdm`, `jsonschema`, `scikit-learn`, `psutil`, `mlflow`, `Pillow==10.3.0`  
- **Storage**: File‑system under `data/` (raw, processed, results)  
- **Testing**: `pytest` (unit, contract, integration)  
- **Target Platform**: Linux (GitHub Actions) – **CPU‑only** (no CUDA)  
- **Constraints**: ≤ 7 GB RAM, ≤ 6 h total runtime, deterministic seeds, reproducible hashes.  

## Constitution Check
| Principle | Check |
|-----------|-------|
| I. Reproducibility | All scripts are deterministic; seeds are pinned; the same programmatic dataset loader is used on every CI run. |
| II. Verified Accuracy | Uses programmatic loaders for the layout-aware corpus and DocVQA benchmark; no fabricated URLs. |
| III. Data Hygiene | Every downloaded file’s SHA‑256 checksum is recorded; transformations write new files with provenance metadata. |
| IV. Single Source of Truth | `data-model.md` (and its JSON schema) is the authoritative definition of all entities. |
| V. Versioning Discipline | Content hashes are stored in `state/projects/PROJ-1051-...yaml`. |
| VI. Resource‑Constrained Computational Efficiency | Pipeline stays within ≤ 7 GB RAM, ≤ 6 h wall‑clock, and runs entirely on CPU. |
| VII. Latent Space Fidelity via Distillation | Evaluation includes paired t‑tests (30 seeds) for MSE improvement and downstream accuracy gain, with Bonferroni correction. |

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
└── tasks.md
```

### Source Code
```
src/
├── data/
│   ├── download.py          # Programmatic fetch of layout corpus & DocVQA; record checksums
│   ├── preprocess.py        # Validate against schema, produce DocumentPair parquet
│   └── latent_generator.py  # CPU‑only ResNet‑18 inference → visual_latent
├── models/
│   ├── distilled.py         # Pruned DistilBERT + projection head
│   └── baseline.py          # Text‑only baseline with RANDOM projection head (capacity control)
├── eval/
│   ├── downstream.py        # DocVQA evaluation (Val/Test split), paired tests, independence checks
│   └── stats.py             # Shapiro‑Wilk, t‑test / Wilcoxon, power calculation
├── utils/
│   ├── split_generator.py   # Deterministic train/val/test split
│   └── seed.py              # Central seed registry
└── cli/
    └── run_pipeline.py      # End‑to‑end orchestrator
```

## Phase Mapping to Functional & Success Criteria

| Phase | FR(s) addressed | SC(s) addressed |
|-------|-----------------|------------------|
| **0 – Data Download & Validation** | FR‑001, FR‑007 | SC‑006 (page count) |
| **1 – Visual Latent Generation** | FR‑001 (latent creation) | SC‑001 (MSE baseline), SC‑004 (memory), SC‑005 (runtime) |
| **2 – Distillation Model Training** | FR‑002, FR‑003, FR‑008 | SC‑001, SC‑004, SC‑005, SC‑007 |
| **3 – Baseline Model Training** | FR‑009 | — |
| **4 – Augmented Representation Construction** | FR‑004 | — |
| **5 – Downstream Evaluation (MANDATORY)** | FR‑005, FR‑006 | SC‑002, SC‑003 |
| **6 – Reporting & Artifact Generation** | (all) | (all) |

## Detailed Methodological Additions

### 1. Layout-Aware Dataset Acquisition
- **Dataset**: Programmatic load of the `llmXive-layout-distillation` subset (or `pubmed-layout` fallback) via `datasets.load_dataset`.
- **Verification**: Ensure the dataset contains `plain_text`, `layout_annotations`, and associated `image` paths/bytes.
- **Schema Check**: Each row must contain `plain_text` (string) and `layout_annotations` (list of bounding boxes). Rows missing `layout_annotations` or images are logged and skipped (fulfills FR‑001 & FR‑007).

### 2. Frozen Visual Encoder & Construct Validity
- **Model**: **ResNet‑18** from `torchvision.models.resnet18(pretrained=True)`.
- **Inference**: Loaded with `torch.no_grad()` on CPU.
- **Construct Validity Analysis**: To ensure ResNet-18 captures layout, the system will compute the correlation (Pearson r) between the generated latents and a simple layout-complexity metric (e.g., number of detected bounding boxes per page). A correlation $|r| > 0.2$ is required to validate the construct before proceeding to distillation.

### 3. DistilledModel
- **Architecture**: DistilBERT (`distilbert-base-uncased`) pruned to ~50 M parameters.
- **Projection Head**: Linear layer maps BERT `[CLS]` (768) → 512.
- **Loss**: MSE between predicted and ResNet latents.
- **Training**: AdamW, cosine LR schedule, early‑stop on validation MSE.

### 4. Baseline Model (Capacity Control)
- **Architecture**: Same DistilBERT backbone.
- **Projection Head**: A **frozen random linear layer** (768 → 512) is used. This ensures the baseline has the exact same parameter count and input dimensionality (1280) as the augmented model, removing capacity as a confound.

### 5. Augmented Representation
- Concatenate BERT `[CLS]` (768) with **predicted** ResNet latent (512) → 1280‑dim vector.

### 6. Downstream Evaluation (MANDATORY)
- **DocVQA Split**: The DocVQA dataset is split into **Validation ([deferred])** and **Test ([deferred])**.
- **Hyperparameter Tuning**: Learning rate and early-stop patience for the final classifier are tuned on the Validation set.
- **Final Reporting**: Final Accuracy/F1 are reported ONLY on the held-out Test set.
- **Statistical Tests**: Paired t‑tests (30 seeds), Bonferroni α = 0.025.

### 7. Statistical Rigor Checklist
- **Multiple comparisons**: Bonferroni correction (α = 0.025).
- **Power justification**: 30 seeds give > 0.9 power for d≈0.8 at α = 0.025.
- **Causal framing**: All findings described as *associational* (FR‑006).
- **Collinearity / Independence**: MI < 0.1 bits and Pearson r < 0.3 between predicted latents and text embeddings.

## Compute Feasibility Summary
- **CPU‑only**: All components run on the 2‑core, 7 GB runner.
- **Memory**: Peak ≈ moderate memory usage.
- **Runtime**: Estimated ≈ 4 h total.
- **No GPU**: No off‑load required.