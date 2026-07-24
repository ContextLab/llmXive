# Implementation Plan: Memory Palaces in LLMs: Spatial Reasoning for Enhanced Episodic Recall

**Branch**: `PROJ-596-memory-palaces-in-llms-spatial-reasoning` | **Date**: 2026-06-16 | **Spec**: `specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/spec.md`
**Input**: Feature specification from `/specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/spec.md`

## Summary

This project implements a spatial-memory transformer variant and a non-spatial baseline to test whether explicit spatial organization of episodic memories is **associated** with enhanced recall accuracy. The system fine-tunes quantized `gpt2-medium` models on three sequential memory benchmarks (bAbI task 3, LAMBADA, Story Cloze) across five random seeds. It measures exact-match recall, computes interference distance metrics, and performs paired statistical testing with multiple comparison corrections. The implementation strictly adheres to CPU-first constraints (1 CPU core, ≤6 GB RAM, ≤5 hours runtime) with a scaled-down GPU escape hatch for any CUDA-dependent operations.

**Note on Spec Discrepancy**: The source spec (spec.md) contains unresolved placeholders in the Assumptions section and FR-010 (e.g., '[deferred]', '[Citation]'). This plan resolves those values to concrete implementation logic ([deferred] subsample cap, Bonferroni correction) to ensure executability. The spec requires a separate revision to align with these resolved values.

## Technical Context

**Language/Version**: Python  
**Primary Dependencies**: `transformers`, `datasets`, `scikit-learn`, `scipy`, `bitsandbytes==0.41.0` (CPU-compatible), `torch` (CPU mode)  
**Storage**: Local file system for cached datasets (`~/.cache/huggingface`), temporary CSV/JSON logs in `data/`  
**Testing**: `pytest` for unit tests; `pytest` for integration tests against contracts  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research/Computational Experiment  
**Performance Goals**: Complete 15 runs (3 datasets × 5 seeds) + statistical analysis within 5 hours; peak RAM ≤ 6 GB  
**Constraints**: No local GPU; 4-bit quantization mandatory for base model; dataset subsampling to [deferred] if RAM > 6 GB
**Scale/Scope**: Moderate total dataset size; a memory grid of moderate capacity; 3 epochs per run  

> Empirical specifics (exact dataset counts, runtime measurements) are deferred to the research/implementation phase.

## Constitution Check

*Gates determined based on `projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/.specify/memory/constitution.md`*

- **I. Reproducibility**: Plan mandates pinned random seeds (a small, fixed set) and canonical dataset sources (Hugging Face). All code will be versioned in `code/`. A `requirements.txt` file MUST exist at `projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/code/` pinning every dependency.
- **II. Verified Accuracy**: Citations in `research.md` are limited to the verified dataset URLs provided in the spec. The plan includes a verification step to check dataset reachability before execution. No external URLs are invented.
- **III. Data Hygiene**: Datasets will be downloaded via `datasets.load_dataset` with streaming enabled. Checksums will be recorded in `state/` upon download.
- **IV. Single Source of Truth**: All metrics (recall, interference distance) will be logged to `data/results/` and referenced exclusively in the final report.
- **V. Versioning Discipline**: Artifacts will carry content hashes. The plan itself is versioned 1.0.0.
- **VI. Computational Resource Constraints**: The plan explicitly designs for a single CPU core, sufficient RAM, and 5-hour runtime. Batch size reduction logic (FR-010) is included, resolving the spec's placeholder to a [deferred] cap.
- **VII. Benchmark Standardization**: Evaluation is restricted to bAbI task 3, LAMBADA, and Story Cloze. No alternative metrics or private datasets are introduced.

## Project Structure

### Documentation (this feature)

```text
specs/PROJ-596-memory-palaces-in-llms-spatial-reasoning/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── dataset.schema.yaml
│   ├── dataset_manifest.schema.yaml
│   ├── result.schema.yaml
│   ├── results.schema.yaml
│   ├── statistical_analysis.schema.yaml
│   ├── training_run.schema.yaml
│   └── spatial_mapping.md # Formal mapping document
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-596-memory-palaces-in-llms-spatial-reasoning/
├── code/
│   ├── __init__.py
│   ├── main.py              # Entry point for training/evaluation
│   ├── models/
│   │   ├── __init__.py
│   │   ├── spatial_memory.py # Spatial slot implementation
│   │   └── baseline.py      # Non-spatial baseline
│   ├── data/
│   │   ├── loaders.py       # Dataset loading with streaming
│   │   └── preprocess.py    # Chunking and coordinate assignment
│   ├── analysis/
│   │   ├── stats.py         # T-tests, effect sizes, corrections
│   │   └── metrics.py       # Interference distance, slot occupancy
│   └── utils/
│       ├── memory_monitor.py # RSS tracking and batch reduction
│       └── config.py        # Hyperparameter management
├── data/
│   ├── raw/                 # Downloaded datasets (symlinks or cache)
│   └── results/             # Logs, metrics, JSON summaries
├── tests/
│   ├── unit/
│   │   ├── test_memory_slots.py
│   │   └── test_stats.py
│   └── contract/
│       └── test_schemas.py
├── artifacts/
│   └── results/             # Final run summaries
└── docs/
    └── contracts/
        └── spatial_mapping.md # Formal mapping document
```

**Structure Decision**: Single project structure selected to minimize overhead and ensure tight coupling between data loading, model training, and analysis within the 5-hour constraint.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Spatial Memory Module | Required by FR-001/FR-002 to test the hypothesis. | A non-spatial baseline alone cannot answer the research question. |
| Batch Size Reduction Logic | Required by FR-010 to handle OOM on free-tier. | Static batch size risks runtime failure on larger datasets. |
| Statistical Correction | Required by FR-006 to control family-wise error. | Uncorrected p-values inflate false-positive rates across 3 datasets. |