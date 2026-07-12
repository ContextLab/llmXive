# Implementation Plan: llmXive Follow-up: Extending PerceptionDLM Parallel Region Perception

**Branch**: `001-llmxive-perceptiondlm-overflow` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-perceptiondl/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-perceptiondl/spec.md`

## Summary

This feature implements a computational research pipeline to quantify the "structural consistency tax" of the PerceptionDLM model when processing images with 20–50 regions in parallel, simulating context overflow. The system generates synthetic overflow datasets using the verified COCO-Stuff dataset, executes parallel batched inference versus a sequential autoregressive baseline (using the SAME PerceptionDLM model), calculates a "Geometric Consistency Score" based on spatial relation consistency, and visualizes the Pareto frontier to identify the tipping point where parallel efficiency is outweighed by consistency loss. The entire pipeline is constrained to run on a CPU-only GitHub Actions runner with a limited number of cores and constrained memory..

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `diffusers`, `spacy`, `pandas`, `scikit-learn`, `matplotlib`, `datasets` (HuggingFace), `huggingface_hub`  
**Storage**: Local `data/` directory for synthetic images and JSON annotations; `data/processed/` for regression results.  
**Testing**: `pytest` for unit tests of metric calculation and synthetic generation logic.  
**Target Platform**: Linux (GitHub Actions free-tier runner).  
**Project Type**: Research pipeline / CLI tool.  
**Performance Goals**: Complete regression analysis (n≥50 images per bin) within 6 hours; Peak RSS < 7 GB.  
**Constraints**: No GPU/CUDA; no 8-bit quantization; strict memory limits; synthetic data generation must guarantee non-overlapping bounding boxes.  
**Scale/Scope**: A variable number of region-count bins (20, 30, 50 regions), 50 images per bin (total synthetic samples).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Implementation Strategy |
|-----------|-------------------|-------------------------|
| **I. Reproducibility** | **Compliant** | Random seeds pinned in `code/` (e.g., `random.seed(42)`). Dataset fetched via `huggingface_hub` with specific revision. |
| **II. Verified Accuracy** | **Compliant** | All citations verified. Dataset URL (COCO-Stuff) validated in `research.md`. No unverified sources used. |
| **III. Data Hygiene** | **Compliant** | Raw data (source images) preserved; synthetic derivations written to new files with checksums recorded in `state/`. |
| **IV. Single Source of Truth** | **Compliant** | All metrics (Geometric Consistency Score, BLEU-4) computed by code and stored in CSV; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | **Compliant** | Artifacts hashed (specifically `data/synthetic/*.json`, `data/processed/*.csv`); `state/` file updated with checksums. |
| **VI. Context-Overflow Characterization** | **Compliant** | Synthetic generation logic explicitly creates 20–50 non-overlapping boxes (mandated by US-2, FR-001) to trigger fragmentation. |
| **VII. Parallelism vs. Coherence Trade-off** | **Compliant** | Pipeline compares parallel (batched) vs. sequential (same model, context-reset) modes and generates Pareto frontier plot. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-follow-up-extending-perceptiondl/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── synthetic_image.schema.yaml
│   └── regression_result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-833-llmxive-follow-up-extending-perceptiondl/
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── config.py             # Paths, seeds, hyperparameters
│   ├── synthetic/
│   │   ├── generator.py      # Non-overlapping box generation
│   │   └── validator.py      # Overlap check
│   ├── models/
│   │   ├── parallel_runner.py # PerceptionDLM batch inference
│   │   └── sequential_runner.py # PerceptionDLM sequential inference (context-reset)
│   ├── metrics/
│   │   ├── consistency.py    # Geometric Consistency Score (spaCy + geometry)
│   │   └── bleu.py           # BLEU-4 calculation
│   ├── analysis/
│   │   ├── regression.py     # Degradation curve fitting
│   │   └── plotting.py       # Pareto frontier visualization
│   └── main.py               # Pipeline orchestration
├── data/
│   ├── raw/                  # Source images (if cached)
│   ├── synthetic/            # Generated images + annotations
│   └── processed/            # Regression CSVs, plots
├── tests/
│   ├── unit/
│   │   └── test_synthetic.py
│   └── contract/
│       └── test_schemas.py
└── state/
    └── projects/PROJ-833-llmxive-follow-up-extending-perceptiondl.yaml
```

**Structure Decision**: Single project structure selected to minimize overhead for a research pipeline. All modules are placed under `code/` to ensure reproducibility and easy testing.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Data Generation** | Native datasets lack 20–50 region images. | Using existing small-region images would fail to test the "overflow" hypothesis (US-2). |
| **Dual Inference Engines (Same Model)** | Must compare Parallel vs. Sequential modes of the SAME model. | Using a different model (e.g., LLaVA) would introduce architecture confounds (US-1). |
| **Geometric Consistency Metric** | Human labels unavailable for synthetic data. | Using generic BLEU alone ignores spatial relations, failing SC-001 (now Geometric Consistency). |
| **Increased Sample Size** | A limited number of samples per bin was underpowered for non-linear regression. | Increasing the number of samples per bin improves power.; fallback to a predefined minimum threshold if memory/time constraints hit. |