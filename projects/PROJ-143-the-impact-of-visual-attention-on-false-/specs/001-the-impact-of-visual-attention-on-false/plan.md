# Implementation Plan: The Impact of Visual Attention on False Memory Formation

**Branch**: `feature-visual-attention-false-memory` | **Date**: 2026-06-25 | **Spec**: `specs/feature-visual-attention-false-memory/spec.md`

## Summary

This project implements a computational pipeline to test the **associational hypothesis** that heightened visual attention to salient but irrelevant scene elements is *associated* with a higher likelihood of false memory formation. The system will download Visual Genome images, compute saliency maps using a CPU-compatible deep visual attention model, and correlate these scores with false-memory flags derived from human recall transcripts (aligned via FR-011). The analysis includes Pearson correlation, mixed-effects logistic regression, and robustness checks against saliency thresholds and model variants, all constrained to run on a CPU-only GitHub Actions runner.

**Critical Note**: This study is **observational**. No causal claims (e.g., "increases") will be made. The analysis is strictly correlational.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU wheel), `scikit-learn`, `pandas`, `numpy`, `statsmodels`, `datasets` (HuggingFace), `opencv-python-headless`, `pillow`  
**Storage**: Local file system (`data/raw`, `data/processed`), HuggingFace cache  
**Testing**: `pytest` (unit tests for data linking, contract validation)  
**Target Platform**: Linux (GitHub Actions free-tier: CPU, 7 GB RAM)  
**Project Type**: Computational research pipeline / data analysis  
**Performance Goals**: Complete full pipeline on **sampled dataset (50 images)** within 6 hours; memory usage < 7 GB.  
**Constraints**: No GPU; no large-model fine-tuning; all data must be verifiable against Visual Genome ground truth; strict adherence to FR-001 through FR-011.  
**Scale/Scope**: **Sampled subset of Visual Genome (approx. small number of images)** to ensure CPU feasibility; analysis unit is object-level across participants.

**Dataset Gap Acknowledgement**: The plan relies on a verified source for Visual Genome and recall transcripts. If these are not provided (see Research.md), the project is blocked.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Status | Action / Notes |
|-----------|--------|----------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; dataset sources (Visual Genome, SALICON) are canonical and cached; `requirements.txt` will pin versions. |
| **II. Verified Accuracy** | **FAIL/Blocked** | **Critical Gap**: No verified URLs for Visual Genome, SALICON, or OpenNeuro in the provided block. The project cannot proceed until verified sources are provided. |
| **III. Data Hygiene** | PASS | Checksums recorded for raw data; no in-place modification; PII scan enforced on commit. |
| **IV. Single Source of Truth** | PASS | All statistics derived from `data/processed` and `code/`; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | PASS | Content hashes for artifacts; `state/` updated on change. |
| **VI. Participant Ethics** | **FAIL/Blocked** | **Requirement**: IRB approval and consent forms MUST be present in `data/ethics/` before data collection. If not, the project halts. |
| **VII. Stimulus Standardization** | PASS | Visual Genome images serve as standardized stimuli; metadata CSV will list IDs and saliency parameters. |

## Project Structure

### Documentation (this feature)

```text
specs/feature-visual-attention-false-memory/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── download.py          # Visual Genome & SALICON downloaders
│   ├── preprocessing.py     # Image resizing, mask extraction, saliency inference
│   └── linking.py           # Image ID to recall transcript alignment (FR-011)
├── analysis/
│   ├── saliency.py          # Saliency model wrapper (CPU)
│   ├── metrics.py           # Pearson r, mixed-effects, FDR correction
│   └── robustness.py        # Sensitivity analysis (thresholds, model variants)
├── utils/
│   ├── logging.py           # Exclusion logging (FR-011)
│   └── validation.py        # Secondary verification for false memories (FR-005)
└── main.py                  # Orchestration script

tests/
├── contract/                # Schema validation tests
├── integration/             # End-to-end pipeline test on single image
└── unit/                    # Data linking, mask extraction tests

data/
├── raw/                     # Downloaded Visual Genome, SALICON
├── processed/               # Saliency maps, false-memory flags, aggregated stats
└── ethics/                  # De-identification logs (if applicable)
```

**Structure Decision**: Single-project structure (`src/`, `tests/`, `data/`) is selected to minimize overhead and align with the computational research nature of the project. No separate backend/frontend required.

## Complexity Tracking

No violations detected. The complexity is managed by:
- Sampling the dataset to fit CPU constraints (50 images).
- Using pre-trained CPU-compatible models.
- Strict adherence to the constitution’s reproducibility and data hygiene rules.
- Explicit blocking on dataset verification and ethics approval.

## Methodology Details

### 1. Data Acquisition & Preprocessing
- **Visual Genome**: Download images and region annotations. Filter for images with valid object masks.
- **Recall Transcripts**: Align with Visual Genome IDs using FR-011 protocol. **If no match is found, exclude the pair and log "ID Mismatch"**.
- **Saliency Model**: Load a pre-trained CPU-compatible model (e.g., `torch` with `cpu` device). Generate fixation maps for each image. **Images will be downsampled to 224x224** to fit memory.

### 2. False Memory Coding (FR-005)
- For each object in an image:
  - Check if it appears in the recall transcript.
  - Check if it is absent from Visual Genome ground truth.
 - **Secondary Verification**: A subset of flagged items ([deferred]) will undergo **Consensus Coding** by 3 independent raters. If >66% agree the object is absent, it is confirmed as a false memory.
  - Flag as false memory if (a), (b), and (c) are met.

### 3. Statistical Analysis
- **Primary Test**: Pearson correlation (r) between object saliency and false-memory rate (aggregated across participants).
- **Secondary Test**: Mixed-effects logistic regression with random intercepts for participants and items. **Confounders (object size, category, image complexity) will be included as covariates.**
- **Correction**: Benjamini-Hochberg FDR for item-wise tests (FR-008).
- **Robustness**: Sensitivity analysis over a range of percentile thresholds and alternative saliency models (ViT-B/16 CAM).
- **Random Effects Test**: Explicitly test and report p-values for random intercepts (SC-002).
- **Inconclusive Flag**: Calculate the rate of unverified false memories. If >10%, flag the study as "inconclusive" (SC-006).

### 4. Power Analysis (FR-010)
- Target: Detect r = 0.30 with 80% power, α = 0.01.
- **Unit of Analysis**: Number of *objects* with valid data.
- Calculate required sample size. If the dataset is insufficient, document the shortfall (SC-005).

### 5. Noise Analysis
- Correlate saliency with "VG annotation density" to ensure the "false memory" signal is not just a proxy for dataset noise. If the correlation is driven by noise, the result is invalidated.

## Confounder Control

- **Object Size**: Extracted from bounding box area.
- **Category**: Categorical variable (encoded).
- **Image Complexity**: Number of objects per image.
- **Model**: These will be included as covariates in the mixed-effects model to reduce bias.

## Dataset Gap Mitigation

- **Visual Genome**: If no verified URL is provided, the pipeline will halt with an error.
- **Recall Transcripts**: If no verified recall dataset with VG IDs exists, the project is blocked. The plan will not simulate recall data for scientific results.
- **Fallback**: If the user provides a verified subset (e.g., COCO with recall), the plan will adapt to that dataset.
