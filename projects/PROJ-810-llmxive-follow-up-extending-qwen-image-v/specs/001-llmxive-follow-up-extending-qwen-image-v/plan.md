# Implementation Plan: llmXive follow-up: extending "Qwen-Image-VAE-2.0 Technical Report"

**Branch**: `001-llmxive-vae-geometric-analysis` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-follow-up-extending-qwen-image-v/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-follow-up-extending-qwen-image-v/spec.md`

## Summary

This project extends the "Qwen-Image-VAE-2.0 Technical Report" by empirically validating the geometric disentanglement of text and image modalities in the VAE's latent space using the **OmniDoc-1** dataset. The primary technical approach involves: (1) downloading and parsing the OmniDoc-1 dataset to extract text-only and image-only region crops using ground-truth bounding box metadata; (2) establishing a **Gold Standard** label set via manual annotation of a stratified subset to break circularity; (3) encoding crops into latent vectors using the pre-trained Qwen-Image-VAE-2.0 model (with DINOv2 fallback) in CPU-only mode; (4) training a lightweight Linear SVM on the Gold Standard to test for linear separability (US-01), including **Spatial Randomization Controls** and **Cross-Document Direction Consistency** tests; (5) performing vector arithmetic to demonstrate zero-shot semantic editing (US-02), including **Global Mean** and **Unrelated Document Controls**; and (6) conducting robustness checks including permutation tests, threshold sensitivity analysis, and pre-study power justification (US-03). All operations are constrained to a vCPU, limited RAM, CPU-only environment.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `datasets` (HuggingFace), `scikit-learn`, `pandas`, `numpy`, `Pillow`, `opencv-python` (headless), `paddleocr` (CPU-only), `tesseract` (for independent validation), `scipy`, `matplotlib`  
**Storage**: Local filesystem (`data/raw/`, `data/processed/`), HuggingFace Hub cache  
**Testing**: `pytest` (unit/integration), custom validation scripts for contract adherence  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 vCPU, 7 GB RAM)  
**Project Type**: Computational research pipeline / CLI tool  
**Performance Goals**: Total runtime ≤ 6 hours; per-image encoding/decoding < 60 seconds; memory usage < 6 GB  
**Constraints**: No GPU/CUDA; no model fine-tuning; strict adherence to dataset variable availability (OmniDoc-1 only); CPU-tractable methods only  
**Scale/Scope**: Subset of OmniDoc-1 dataset (sampled to fit RAM); analysis of a large collection of latent vectors; generation of a set of edited images for validation  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | **PASS** | Plan mandates pinned seeds, isolated `requirements.txt`, and end-to-end runnable scripts in `code/`. |
| **II. Verified Accuracy** | **PASS** | Citations for OmniDoc-1 strictly limited to verified HuggingFace URL; no fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming raw data; derivations (crops, latents) written to new files; PII scan mentioned. |
| **IV. Single Source of Truth** | **PASS** | All metrics (accuracy, SSIM, OCR Accuracy) computed by code (`code/analysis/separability_test.py`, `code/analysis/editing_arithmetic.py`) and traced to `data/` artifacts. **Linearity Verified** flag is programmatically derived from `separability_test.py` (T024) via Cross-Document Direction Consistency check. |
| **V. Versioning Discipline** | **PASS** | Artifacts will carry content hashes; plan updates `state` timestamps upon change. |
| **VI. Latent Space Geometric Integrity** | **PASS** | Plan explicitly uses ground-truth bounding boxes for region extraction, permutation tests, **triviality_flag** computation (raw pixel check in `separability_test.py`), and direction consistency tests. |
| **VII. CPU-First Zero-Shot Editing** | **PASS** | All models (VAE/DINOv2, SVM, OCR) are selected for CPU compatibility; no GPU/quantization dependencies. **OCR Accuracy** metric explicitly linked to `contracts/output_metrics.schema.yaml` via `code/analysis/editing_arithmetic.py`. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-qwen-image-v/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── latent_vector.schema.yaml
│   └── output_metrics.schema.yaml
└── tasks.md             # Phase 2 output (created by /speckit-tasks)
```

### Source Code (repository root)

```text
code/
├── data/
│   ├── download_omnidoc.py       # Downloads and checksums raw parquet
│   ├── preprocess_crops.py       # Extracts text/image regions using bounding boxes (excludes ambiguous rows)
│   └── encode_latents.py         # Encodes crops to latent vectors (CPU)
├── analysis/
│   ├── separability_test.py      # Trains Linear SVM, PCA, permutation test, triviality check, linearity_verified flag (US-01)
│   ├── editing_arithmetic.py     # Vector arithmetic, decoding, SSIM/OCR eval, null control (US-02)
│   └── robustness_checks.py      # Threshold sweep, power analysis (US-03)
├── utils/
│   ├── config.py                 # Seed pinning, path constants
│   └── metrics.py                # SSIM, LPIPS, F1, accuracy helpers
├── main.py                       # Orchestration script
└── requirements.txt              # Pinned dependencies

tests/
├── contract/                     # Validates outputs against schema contracts
├── integration/                  # Runs full pipeline on small sample
└── unit/                         # Tests for metrics, data parsing
```

**Structure Decision**: Single project structure (`code/`) selected to maintain a linear research pipeline. Data flows from `download` → `preprocess` → `encode` → `analysis`. This minimizes I/O overhead and simplifies dependency management on the constrained runner.

## Task Ordering & Dependencies

*Critical for execution on CI. Tasks must run in this order.*

1.  **T017**: `encode_latents.py` (Latent Encoding) - *Produces latent vectors.*
2.  **T025**: `separability_test.py` (Centroid Computation) - *Depends on T017. Computes $\mu_{text}$, $\mu_{image}$.*
3.  **T024**: `separability_test.py` (Linearity Verification) - *Depends on T025. Verifies direction consistency and PCA separation. Computes `triviality_flag` and `linearity_verified`.*
4.  **T018**: `separability_test.py` (SVM Training) - *Depends on T017 (Gold Standard subset). Produces optimal boundary.*
5.  **T020**: `separability_test.py` (Permutation Test) - *Depends on T018.*
6.  **T022**: `editing_arithmetic.py` (Vector Arithmetic) - *Depends on T025. Includes Global Mean and Unrelated Document Controls.*
7.  **T023**: `editing_arithmetic.py` (Null Hypothesis Control) - *Depends on T025 (shuffled centroids).*
8.  **T031**: `robustness_checks.py` (Threshold Sweep) - *Depends on T018 (optimal boundary) and T020. Sweeps thresholds around the optimal boundary.*

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | Constitution Check passed. | N/A |