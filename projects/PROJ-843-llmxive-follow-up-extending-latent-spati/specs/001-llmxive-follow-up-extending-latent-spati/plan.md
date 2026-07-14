# Implementation Plan: llmXive follow-up: extending "Latent Spatial Memory for Video World Models"

**Branch**: `001-gene-regulation` | **Date**: 2026-07-12 | **Spec**: `specs/001-gene-regulation/spec.md`
**Input**: Feature specification from `/specs/001-gene-regulation/spec.md`

## Summary

This project implements a CPU-tractable research pipeline to evaluate "Sparse Epipolar Geometry" against "Dense Depth" baselines for video world models. The system stratifies the RealEstate dataset by scene dynamics (static/slow/fast) and texture (high/low), extracts sparse SIFT/ORB features, computes fundamental matrices via RANSAC, and performs latent-space warping with RBF interpolation. The study measures a unified **Geometric Error** (Photometric Consistency on a held-out frame) for both methods, validates the hypothesis that sparse methods offer significant computational savings in specific operational boundaries while maintaining geometric consistency, and performs a Two-Way ANOVA to test for interaction effects.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `opencv-python` (CPU), `scikit-learn`, `scipy`, `pandas`, `numpy`, `torch` (CPU-only wheels), `datasets` (HuggingFace), `imageio`, `pytest`, `memory_profiler`
**Storage**: Local file system (`data/raw`, `data/processed`, `data/stratified`), HuggingFace datasets cache
**Testing**: `pytest` (unit tests for feature extraction, integration tests for pipeline phases)
**Target Platform**: Linux (GitHub Actions Free Tier: Multiple CPU cores, several GB RAM, no GPU)
**Project Type**: Computational research pipeline / CLI
**Performance Goals**: Full pipeline execution ≤ 6 hours on CPU; Peak RAM < 7 GB; Sparse method inference time ≤ 60% of dense baseline (target ≥40% reduction).
**Constraints**: No GPU/CUDA; No dense depth map generation for sparse path; RANSAC must handle low-texture failure gracefully; Memory-safe batch processing.
**Scale/Scope**: A set of video sequences (a representative sample per stratum) from RealEstate10K test set.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | All random seeds pinned in `code/utils/seeds.py`. Data fetched via `datasets.load_dataset` with specific revision. `requirements.txt` pins exact versions. |
| **II. Verified Accuracy** | **PASS** | All dataset URLs sourced exclusively from the `# Verified datasets` block. Citations in `research.md` validated via a dedicated `validate_citations` phase (Phase 0.5) before data processing. |
| **III. Data Hygiene** | **PASS** | Raw data (`data/raw`) is immutable. Derived data (`data/stratified`, `data/features`) gets new filenames with content hashes recorded in `state.yaml`. PII scan excluded (video frames). |
| **IV. Single Source of Truth** | **PASS** | Metrics (Unified Geometric Error, Time, RAM) are written to `data/results/metrics.json`. The paper will read *only* from this file. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Content hashes for `plan.md`, `research.md`, and `data-model.md` are recorded in a `manifest.json` generated alongside the plan. The **CI pipeline** updates `state.yaml` with these hashes *after* the artifact is written and validated. |
| **VI. Sparse-Geometry Operational Boundaries** | **PASS** | The plan explicitly stratifies by motion/texture (FR-001) and reports failure modes (edge cases) as required. |
| **VII. CPU-Efficiency Benchmarking** | **PASS** | `memory_profiler` and `time` decorators used. No GPU code paths. `torch` installed via CPU-only wheels with explicit index constraint. |

## Project Structure

### Documentation (this feature)

```text
specs/001-gene-regulation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   └── metrics.schema.yaml
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-843-llmxive-follow-up-extending-latent-spati/
├── code/
│   ├── __init__.py
│   ├── config.py                # Paths, thresholds, seeds
│   ├── data/
│   │   ├── download.py          # Fetch RealEstate10K
│   │   ├── stratify.py          # FR-001: Motion/Texture stratification
│   │   └── extract_features.py  # FR-002: SIFT/ORB extraction
│   ├── geometry/
│   │   ├── solver.py            # FR-003: RANSAC Fundamental Matrix
│   │   └── warp.py              # FR-004: RBF Latent Warping
│   ├── eval/
│   │   ├── metrics.py           # FR-005/SC-001/SC-002: Unified Geometric Error
│   │   ├── anova.py             # FR-005: Two-way ANOVA
│   │   └── sensitivity.py       # FR-006: Threshold sweep
│   ├── utils/
│   │   ├── seeds.py             # Reproducibility
│   │   └── memory_monitor.py    # FR-007: RAM/Time logging
│   └── main.py                  # Orchestrator
├── data/
│   ├── raw/                     # Downloaded tar.gz (immutable)
│   ├── processed/               # Extracted frames
│   ├── stratified/              # 4 subsets
│   ├── features/                # .npy descriptors
│   └── results/                 # Metrics JSON, ANOVA tables
├── tests/
│   ├── unit/
│   │   ├── test_stratify.py
│   │   └── test_solver.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen to minimize overhead for a research pipeline. Modular separation (`data`, `geometry`, `eval`) ensures testability of individual FRs.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **RBF Interpolation on CPU** | Required by FR-004 for occlusion filling without dense depth. | Standard linear interpolation fails to maintain geometric smoothness in latent space; dense depth is explicitly forbidden by the sparse hypothesis. |
| **Stratified Sampling** | Required by FR-001 to test interaction effects (SC-004). | Random sampling would obscure the "operational boundary" (low texture/high motion) which is the core research question (Constitution VI). |
| **Unified Metric for ANOVA** | Required to validly compare Dense vs. Sparse methods (Methodology Concern). | Comparing different metrics (WorldScore vs. Reprojection Error) is a category error; a single Photometric Consistency metric on held-out frames allows valid statistical testing. |
