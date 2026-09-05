# Implementation Plan: llmXive follow-up: extending "Scaling Mixture-of-Experts Video Pretraining for Embodied Intelligence"

**Branch**: `001-llmxive-physical-validator` | **Date**: 2026-09-05 | **Spec**: `specs/001-llmxive-physical-validator/spec.md`
**Input**: Feature specification from `specs/001-llmxive-physical-validator/spec.md`

## Summary

This project validates the hypothesis that internal activation patterns of pre-trained video models (specifically MoE architectures, with a ViT fallback) encode physical laws. The technical approach involves: (1) extracting latent vectors and expert activation masks from intermediate DiT/ViT layers on a CPU-only environment; (2) generating independent ground-truth labels ("valid"/"invalid") by reconstructing 3D states via monocular depth estimation (with kinematic consistency checks) and simulating them in a CPU-based physics engine (PyBullet); and (3) training a lightweight classifier to predict physical validity. The pipeline is constrained to run within 6 hours on a CPU-only CI runner with 7 GB RAM, employing frame subsampling, streaming, and dynamic power analysis to ensure feasibility.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets`, `pybullet`, `scikit-learn`, `opencv-python-headless`, `monodepth2` (default), `shap` (for KernelSHAP), `huggingface-hub`  
**Storage**: Local temporary files under `data/` (streamed/processed), NumPy arrays for features, CSV/JSON for labels.  
**Testing**: `pytest` (unit tests for extraction logic, integration tests for pipeline flow).  
**Target Platform**: Linux (GitHub Actions Free Tier: standard vCPU allocation, ~7 GB RAM).  
**Project Type**: Research Pipeline / Data Analysis.  
**Performance Goals**: Feature extraction < 2 hours (sampled), Physics simulation < 2 hours, Classifier training < 30 minutes. Total pipeline < 6 hours.  
**Constraints**: GB RAM limit (requires chunking/subsampling), No local GPU (CPU-only inference for foundation model), < 14 GB disk (streaming required).  
**Scale/Scope**: Subset of BridgeData/RoboNet video clips (sampled to fit memory), Binary classification task.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*Gates determined based on `projects/PROJ-1030-llmxive-follow-up-extending-scaling-mixt/.specify/memory/constitution.md`*

| Principle | Compliance Status | Evidence in Plan |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned `requirements.txt`, fixed random seeds, and streaming from canonical HF URLs. |
| **II. Verified Accuracy** | **Compliant** | All dataset URLs are restricted to the "Verified datasets" block; no fabricated citations. |
| **III. Data Hygiene** | **Compliant** | Raw data streamed/downloaded to `data/raw`. MD5 checksums generated immediately upon download and recorded in `data/raw/.checksums.json`, then merged into `state/manifest.yaml`. Processed features/labels written to `data/processed` with checksums. |
| **IV. Single Source of Truth** | **Compliant** | Metrics derived solely from `data/processed` via `code/` scripts; no hand-typed numbers in reports. |
| **V. Versioning Discipline** | **Compliant** | `main_pipeline.py` computes SHA-256 hashes for all artifacts. If a hash mismatch is detected against `state/manifest.yaml`, the script explicitly writes a 'stale' flag to the relevant review record in `state/` before proceeding, invalidating the stale record as required. |
| **VI. Latent-Space Grounding** | **Compliant** | Explicitly separates feature extraction (Video Model) from labeling (Depth + Physics). Includes 'Prior Audit' to switch to SfM if priors overlap. |
| **VII. CPU-Tractable Efficiency** | **Compliant** | All models selected for CPU feasibility. `KernelSHAP` approximated with limited samples. Chunking strategy defined. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-physical-validator/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-1030-llmxive-follow-up-extending-scaling-mixt/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── extract_features.py       # FR-001, FR-002, FR-006
│   ├── generate_labels.py        # FR-003, FR-008 (Generates EstimatedState3D & PhysicalLabel)
│   ├── train_classifier.py       # FR-004, FR-005
│   ├── utils/
│   │   ├── memory_manager.py     # Chunking logic
│   │   ├── physics_sim.py        # PyBullet wrapper (with scale normalization)
│   │   └── prior_audit.py        # Checks for shared priors
│   └── main_pipeline.py          # Orchestration (Hash validation & state update)
├── data/
│   ├── raw/                      # Streamed/downloaded clips (temp)
│   │   └── .checksums.json       # Raw data checksums
│   ├── processed/
│   │   ├── features.npy          # Activation patterns
│   │   ├── labels.csv            # Physical validity
│   │   └── metadata.json         # Reconstruction confidence
├── tests/
│   ├── unit/
│   │   └── test_extract.py
│   └── integration/
│       └── test_pipeline.py
└── docs/
    └── figures/
```

**Structure Decision**: Single project structure (`code/`) selected to maintain tight coupling between extraction, labeling, and training scripts, facilitating the 6-hour CI job constraint. Modular `utils/` ensures memory management, physics logic, and prior auditing are reusable and testable.

## Traceability Matrix

| Script | Generates | Consumes | FRs Addressed |
| :--- | :--- | :--- | :--- |
| `extract_features.py` | `ActivationPattern` (features.npy) | `VideoClip` (raw) | FR-001, FR-002, FR-006 |
| `generate_labels.py` | `EstimatedState3D` (intermediate), `PhysicalLabel` (labels.csv) | `VideoClip` (raw) | FR-003, FR-008 |
| `train_classifier.py` | `ClassifierModel`, `Metrics` | `ActivationPattern`, `PhysicalLabel` | FR-004, FR-005 |
| `main_pipeline.py` | `state/manifest.yaml` (updated) | All artifacts | FR-001-008 |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **3D Reconstruction + Physics Engine** | Essential for independent ground truth (Constitution VI). | Using model-generated labels or heuristic rules would introduce circularity, violating the core hypothesis test. |
| **Streaming/Chunking Strategy** | Mandatory to fit 7 GB RAM with large video models (FR-006). | Loading full videos or models into memory would crash the runner immediately. |
| **Separate Labeling Pipeline** | Required to decouple features from labels (FR-003). | Using the same model for both would make the classification task trivial and scientifically invalid. |
| **Prior Audit & SfM Fallback** | Required to prevent circular validation if depth/video models share priors (Scientific Soundness). | Assuming independence without verification risks measuring shared biases. |
