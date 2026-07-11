# Implementation Plan: llmXive Follow-up: Extending MulTaBench

**Branch**: `001-llmxive-mulTabench-extension` | **Date**: 2026-07-11 | **Spec**: `specs/001-llmxive-mulTabench-extension/spec.md`

## Summary

This project extends the MulTaBench benchmark by implementing a "CPU-Conditioned" multimodal learning approach. The core technical strategy involves generating frozen embeddings for unstructured data (images/text) using CLIP ViT-B/32 and Sentence-BERT on a CPU-only environment, then training a lightweight, trainable projection module (MLP or attention) that uses normalized tabular features as a query to modulate these embeddings. The goal is to recover performance lost by not fine-tuning the backbone, specifically analyzing the correlation between recovery efficacy and tabular structural properties (cardinality, sparsity, missingness). The entire pipeline is constrained to run on GitHub Actions free-tier runners (limited CPU and RAM resources, time-limited execution) without GPU acceleration.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only build), `transformers`, `sentence-transformers`, `scikit-learn`, `pandas`, `pyarrow`, `numpy`, `requests`, `pyyaml`, `bayesian-optimization` (for analysis)  
**Storage**: Local file system (`data/` for raw/derived, `artifacts/` for embeddings/metrics)  
**Testing**: `pytest` (unit tests for data loaders, integration tests for pipeline steps, gradient inspection)  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Project Type**: Research/Computational Pipeline  
**Performance Goals**: ≤60 min for embedding generation, ≤5h for training/evaluation, peak RAM ≤7GB.  
**Constraints**: No GPU/CUDA, no model fine-tuning (frozen backbones), deterministic seeds (`random_seed=42` for primary run, 5 seeds for sensitivity), batch processing for memory safety.  
**Scale/Scope**: A subset of initial datasets from MulTaBench (alphabetically) for validation, with the full set included if feasible within time limits.

> Note: MulTaBench raw data availability is conditional on local user setup. No public URL exists in the verified dataset block. The implementation relies on local data ingestion scripts.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

- **I. Reproducibility**: Plan mandates pinned seeds (`random_seed=42` for primary, specific seeds for sensitivity) in all scripts and explicit version pinning in `pyproject.toml`. External data fetching logic is deterministic based on local file presence.
- **II. Verified Accuracy**: The plan explicitly cites the MulTaBench paper (arXiv:2605.10616). It acknowledges the lack of a public URL and mandates a local SHA-256 checksum verification step in `data/README.md` to satisfy 'Data Hygiene' conditionally. All "GPU-Tuned" baselines are treated as constants from the paper.
- **III. Data Hygiene**: The plan includes a `data/` directory structure with checksum validation steps (Phase 0) and mandates that raw data is never modified in place; all transformations produce new files (e.g., `embeddings_v1.parquet`).
- **IV. Single Source of Truth**: The `data-model.md` defines strict schemas for `FrozenEmbedding` and `TabularMetadata`. A global `run_id` is generated at the start of the pipeline and injected into the `FrozenEmbedding` parquet files. This `run_id` is propagated to `EvaluationMetrics`, ensuring every metric row traces back to a specific embedding row via the shared ID.
- **V. Versioning Discipline**: The plan explicitly schedules Phase 4: "Update State". This phase executes `code/pipelines/update_state.py` to calculate SHA-256 hashes of all generated artifacts and update `state/projects/PROJ-823-llmxive-follow-up-extending-multabench-b.yaml` with the new `updated_at` timestamp and `artifact_hashes`.
- **VI. Frozen-Backbone Integrity**: The implementation strategy explicitly disables gradient tracking (`torch.no_grad()`) for CLIP and BERT backbones. A concrete unit test `tests/test_projection.py::test_frozen_backbone_gradients` is scheduled in Phase 2 to verify zero weight updates during the projection training.
- **VII. Tabular Feature Conditionability Analysis**: The plan explicitly schedules the computation of cardinality, missingness, sparsity, and variance as a distinct phase (FR-003) prior to model training, ensuring the correlation analysis (FR-006) has the necessary inputs.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-mulTabench-extension/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── frozen_embedding.schema.yaml
│   ├── tabular_metadata.schema.yaml
│   └── evaluation_metrics.schema.yaml
└── tasks.md             # Phase 2 output (not created here)
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py            # Global config, seeds, paths
├── data_loader.py       # MulTaBench ingestion, validation
├── embeddings/
│   ├── __init__.py
│   ├── generator.py     # CLIP/SBERT frozen embedding generation
│   └── utils.py         # Batch processing, memory management
├── models/
│   ├── __init__.py
│   ├── projection.py    # Lightweight MLP/Attention module
│   └── trainer.py       # Training loop for projection layer
├── analysis/
│   ├── __init__.py
│   ├── metadata_stats.py # Cardinality, sparsity, missingness
│   └── correlation.py    # Pearson/Spearman, Bootstrap, Bayesian estimation
├── pipelines/
│   ├── __init__.py
│   ├── run_baseline.py  # FR-001: Frozen baseline generation (5 seeds for sensitivity)
│   ├── run_conditioned.py # FR-002: Conditioned training
│   ├── run_analysis.py  # FR-003/005/006: Stats & correlation
│   └── update_state.py  # Phase 4: Update state YAML
├── utils/
│   ├── logging.py
│   └── memory_monitor.py # Peak RAM tracking
└── tests/
    ├── test_embeddings.py
    ├── test_projection.py # Contains test_frozen_backbone_gradients
    └── test_analysis.py

data/
├── raw/                 # MulTaBench raw files (checksummed)
├── processed/           # Normalized tabular, embeddings
└── artifacts/           # Final metrics, reports

pyproject.toml           # Primary dependency source
requirements.txt         # Generated from pyproject.toml for CI
```

**Structure Decision**: Single project structure under `code/` is selected to minimize overhead and simplify dependency management for a CPU-bound research pipeline. The modular separation (`embeddings`, `models`, `analysis`) ensures clear separation of concerns for the three functional requirements (FR-001, FR-002, FR-003). `pyproject.toml` is the primary source of truth for dependencies.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Batch Processing Strategy | Required to stay within feasible RAM limits for large image datasets. | Loading all images into memory at once would exceed RAM limits on CI runners. |
| FDR Correction (Benjamini-Hochberg) | Required by FR-006 to control false discoveries across multiple metadata correlations. | Standard p-value thresholding would inflate Type I error rates due to multiple comparisons. |
| Two-Stage Pipeline (Frozen then Project) | Required to isolate the effect of the projection layer (US-001 vs US-002). | Joint training would conflate backbone fine-tuning with projection efficacy. |
| 5-Seed Sensitivity Analysis | Required to account for variance in P_frozen (scientific soundness concern). | A single deterministic run would mask the uncertainty in the baseline, leading to invalid correlation analysis. |

## Implementation Phases

1.  **Phase 0: Research & Data Validation**: Verify local data checksums, confirm dataset structure.
2.  **Phase 1: Frozen Embedding Generation**: Generate embeddings for images/text (CLIP/SBERT) with `random_seed=42` and 4 additional seeds for sensitivity. Output `FrozenEmbedding` parquet files with `run_id`.
3.  **Phase 2: Tabular-Conditioned Projection**: Train the projection layer. Verify frozen backbone integrity via `tests/test_projection.py`.
4.  **Phase 3: Statistical Analysis**: Compute metadata stats, recovery ratios (averaged over 5 seeds), and perform correlation analysis with Bayesian estimation.
5.  **Phase 4: Update State**: Execute `update_state.py` to hash artifacts and update `state/projects/...yaml`.