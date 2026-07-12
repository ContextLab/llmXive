# Implementation Plan: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Branch**: `001-llmxive-vae-geometric-analysis` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-vae-geometric-analysis/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-vae-geometric-analysis/spec.md`

## Summary

This project investigates the geometric structure of the Qwen-Image-VAE-2.0 latent space by testing the hypothesis that "text-only" and "image-only" regions of document images are linearly separable. The technical approach involves downloading the OmniDoc dataset, extracting latent vectors from cropped regions defined by ground-truth bounding boxes, training a lightweight Linear SVM for modality classification, and performing vector arithmetic to demonstrate zero-shot semantic editing. The implementation strictly adheres to CPU-only constraints (vCPU, 7 GB RAM) and requires rigorous statistical validation (permutation tests, Bonferroni correction) to ensure methodological soundness.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU wheel), `transformers`, `datasets`, `scikit-learn`, `opencv-python-headless`, `paddleocr`, `pyyaml`, `pandas`, `numpy`, `matplotlib`, `seaborn`, `pillow`  
**Storage**: Local filesystem (`data/raw`, `data/processed`, `data/interim`) for parquet and image artifacts; no external database.  
**Testing**: `pytest` with `pytest-cov` for unit tests; contract tests against YAML schemas.  
**Target Platform**: Linux (GitHub Actions free-tier runner: A limited CPU allocation, 7 GB RAM, no GPU).  
**Project Type**: Computational Research / Data Analysis Pipeline  
**Performance Goals**: Complete full analysis pipeline within 6 hours; single image edit < 60 seconds.  
**Constraints**: No CUDA/GPU usage; no model fine-tuning; memory usage < 7 GB; strict adherence to ground-truth bounding boxes for region isolation.  
**Scale/Scope**: Analysis of a sampled subset of the OmniDoc dataset (N images determined by power analysis).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

**Requirements.txt Content (Pinned Versions for Reproducibility)**:
```text
torch==2.2.0+cpu
transformers==4.40.0
datasets==2.18.0
scikit-learn==1.4.0
opencv-python-headless==4.9.0.80
paddleocr==2.7.3
pyyaml==6.0.1
pandas==2.2.1
numpy==1.26.4
matplotlib==3.8.3
seaborn==0.13.2
pillow==10.2.0
pytest==8.1.1
pytest-cov==5.0.0
```

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/`. Datasets fetched from canonical HF URLs. `requirements.txt` pins versions (see Technical Context). |
| **II. Verified Accuracy** | **Compliant** | The **Reference-Validator Agent** runs a pre-check on every artifact write: it parses `research.md` and `spec.md`, extracts all URLs, and cross-references them against the `# Verified datasets` block. Any URL not in the block is flagged as `unreachable` or `mismatch`. Citations are restricted to the verified block. |
| **III. Data Hygiene** | **Compliant** | Raw data preserved in `data/raw`. Checksums recorded in state file. No in-place modification. |
| **IV. Single Source of Truth** | **Compliant** | All metrics (accuracy, SSIM, F1) computed by code and traced to specific data rows. |
| **V. Versioning Discipline** | **Compliant** | **Mechanism**: On write, `code/utils/versioning.py` computes the SHA-256 hash of the artifact content, updates the `state/projects/...yaml` `updated_at` timestamp, and records the new hash in the `artifact_hashes` map. This workflow is automated in the CI pipeline. |
| **VI. Latent Space Geometric Integrity** | **Compliant** | Disentanglement validated using ground-truth bounding boxes from OmniDoc. Permutation tests required for significance. Cross-region generalization used to avoid tautology. |
| **VII. CPU-First Zero-Shot Editing** | **Compliant** | All models (VAE, SVM, OCR) configured for CPU. No quantization or GPU-specific ops. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-vae-geometric-analysis/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── latent_vector.schema.yaml
│   ├── output.schema.yaml
│   └── output_metrics.schema.yaml
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-810-llmxive-follow-up-extending-qwen-image-v/
├── code/
│   ├── __init__.py
│   ├── config.py              # Paths, seeds, hyperparameters
│   ├── data/
│   │   ├── download.py        # FR-001: Dataset fetching
│   │   ├── preprocess.py      # FR-003: Cropping & vector extraction
│   │   └── loaders.py         # Dataset loading logic
│   ├── models/
│   │   ├── vae_wrapper.py     # FR-002: Qwen-Image-VAE-2.0 CPU loader
│   │   ├── classifiers.py     # FR-004: Linear SVM/LogReg
│   │   └── editing.py         # FR-005: Vector arithmetic logic
│   ├── analysis/
│   │   ├── separability.py    # FR-004, FR-007: SVM training & permutation
│   │   ├── editing_eval.py    # FR-006, FR-010: SSIM, Keypoint matching
│   │   └── stats.py           # FR-008, FR-009: Sensitivity & Bonferroni
│   ├── utils/
│   │   └── versioning.py      # Implements Constitution Principle V workflow
│   └── main.py                # Orchestration
├── data/
│   ├── raw/                   # Downloaded parquet/images
│   ├── processed/             # Latent vectors, cropped images
│   └── interim/               # Intermediate stats
├── tests/
│   ├── contract/              # Schema validation
│   ├── integration/           # Pipeline end-to-end
│   └── unit/                  # Component logic
├── requirements.txt
└── README.md
```

**Structure Decision**: Adopted a modular `code/` structure separating data ingestion, model loading, analysis, and evaluation to ensure testability and adherence to the "Single Source of Truth" principle. The separation of `data/` into `raw`, `processed`, and `interim` enforces Data Hygiene.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Complex Evaluation Metrics (SSIM + Keypoint)** | Required by FR-006 and FR-010 to distinguish layout preservation from texture artifacts. | A simple pixel-wise MSE would fail to detect layout shifts vs. texture noise, violating US-02 acceptance criteria. |
| **Permutation Testing** | Required by FR-007 to establish statistical significance against random chance. | Standard p-values assume distributional normality which may not hold for high-dimensional latent vectors; permutation is robust. |
| **CPU-Only Constraint** | Mandatory by SC-004 and Constitution Principle VII. | GPU-accelerated methods are faster but would render the project non-reproducible on the target CI environment, failing the "Reproducibility" gate. |
| **Cross-Region Generalization** | Required to avoid tautology (methodology-5cc67bc0). | Training on isolated crops and testing on them would prove only that the VAE encodes spatial location, not semantic modality. |
| **Linearity & Orthogonality Checks** | Required to validate the vector arithmetic assumption (methodology-41dfeb9c). | Without these checks, the editing operation is a guess; if the space is not linear/orthogonal, the edit fails. |
| **Halt on Contamination** | Required to prevent invalid editing (scientific_soundness-7a0d6325). | If the text centroid contains layout features, subtraction destroys the image; the pipeline must halt rather than produce garbage. |