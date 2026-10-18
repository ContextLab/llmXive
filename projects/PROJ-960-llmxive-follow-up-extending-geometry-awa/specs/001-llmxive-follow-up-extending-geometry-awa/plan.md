# Implementation Plan: Geometry-Aware Representation Denoising for Robust Multi-view 3D Reconstruction

**Branch**: `001-geometry-aware-denoising` | **Date**: 2026-09-20  
**Spec**: `specs/001-geometry-aware-denoising/spec.md`

## Summary

This project extends the GARD (Geometry-Aware Representation Denoising) framework by implementing a deterministic, CPU-efficient graph Laplacian filter that preserves robust structural signatures (Laplacian eigenmodes and curvature) while suppressing noise in multi-view 3D reconstruction. The core innovation is replacing expensive diffusion-based denoising with a lightweight spectral filter that recovers ≥85% of diffusion-baseline robustness while achieving ≥100× speedup on CPU hardware. The research validates this hypothesis through spectral analysis (identifying eigenmode–robustness correlations), sensitivity analysis (parameter sweeps), and comparative benchmarking (Wilcoxon signed-rank test) on the Depth Anything 3 (DA3) benchmark dataset.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: PyTorch (CPU wheels), scikit-learn, scipy, numpy, pandas, matplotlib, networkx, datasets (HuggingFace)  
**Storage**: Local filesystem (parquet/zarr for datasets, numpy/pickle for intermediate features)  
**Testing**: pytest with contract-based validation  
**Target Platform**: GitHub Actions free-tier runner (2 CPU cores, ~7 GB RAM, ~14 GB disk, no GPU)  
**Project Type**: Research analysis pipeline (reproducible scientific study)  
**Performance Goals**: Deterministic filter inference ≤1% of diffusion baseline latency on CPU; full pipeline (50 scenes) completes within 6-hour CI job limit  
**Constraints**: CPU-only (no CUDA); <7 GB peak RAM per batch; <14 GB disk for intermediate features; all methods must run deterministically with pinned random seeds  
**Scale/Scope**: 50 test scenes from DA3 benchmark; feature graphs with ~1000–5000 nodes per scene; sensitivity sweeps over k ∈ {5, 10, 15}; spectral analysis with Bonferroni correction for ~10 tests

## Constitution Check

**Principle I (Reproducibility)**: ✓ All random seeds pinned; DA3 dataset fetched from verified HuggingFace source on every run; `requirements.txt` pins all dependencies; every result is re-runnable on fresh CI.

**Principle II (Verified Accuracy)**: ✓ All citations in `research.md` verified against primary sources (GARD repo, DA3 dataset, scipy/networkx documentation); title-token overlap ≥0.7 enforced.

**Principle III (Data Hygiene)**: ✓ Raw DA3 parquet checksummed and recorded in project state; all feature extractions produce new intermediate files with documented derivation; no PII in committed data.

**Principle IV (Single Source of Truth)**: ✓ Every figure, table, and statistic in the paper traces to exactly one row in `data/` and one code block in `code/`; derived numbers computed programmatically, never hand-typed.

**Principle V (Versioning Discipline)**: ✓ All artifacts carry content hashes; stale review records invalidated on change; `updated_at` timestamp refreshed on each research-stage artifact change.

**Principle VI (Deterministic Structural Enforcement)**: ✓ **CRITICAL**: All denoising operations implemented as deterministic graph Laplacian filters with NO stochastic components, NO iterative sampling, NO random initialization. Feature maps frozen from GARD encoder; only deterministic spectral operators applied. This ensures decoupling of reconstruction quality from generative overhead.

**Principle VII (CPU-Centric Latency Benchmarking)**: ✓ Inference latency and peak memory measured on single CPU core; ≥100× speedup vs. diffusion baseline is a primary success criterion alongside Chamfer Distance; all performance claims grounded in CPU-bound benchmarks.

## Project Structure

### Documentation (this feature)

```text
specs/001-geometry-aware-denoising/
├── plan.md                    # This file
├── research.md                # Phase 0: methodology, dataset strategy, hypothesis
├── data-model.md              # Phase 1: feature graph schema, output tensors
├── quickstart.md              # Phase 1: minimal reproducible example
├── contracts/
│   ├── feature-graph.schema.yaml
│   ├── reconstruction-output.schema.yaml
│   └── spectral-analysis.schema.yaml
└── tasks.md                   # Phase 2: detailed implementation task list
```

### Source Code (repository root)

```text
src/
├── gard_denoising/
│   ├── __init__.py
│   ├── graph_construction.py       # k-NN graph builder, edge weighting
│   ├── spectral_filter.py          # Laplacian eigendecomposition, filtering
│   ├── curvature_analysis.py       # Curvature estimation from feature graphs
│   ├── reconstruction.py           # GARD decoder + 3D reconstruction head
│   ├── metrics.py                  # Chamfer Distance, F-score, MSE
│   └── benchmarking.py             # Latency/memory profiling, Wilcoxon test
├── data_loaders/
│   ├── da3_loader.py               # DA3 dataset streaming + batching
│   └── gard_feature_extractor.py   # GARD encoder wrapper (CPU-only)
└── utils/
    ├── logging.py                  # Structured logging (llmxive_toolkit.get_logger)
    └── paths.py                    # Output folder creation (llmxive_toolkit.paths)

tests/
├── contract/
│   ├── test_feature_graph_schema.py
│   ├── test_reconstruction_output_schema.py
│   └── test_spectral_analysis_schema.py
├── unit/
│   ├── test_graph_construction.py
│   ├── test_spectral_filter.py
│   ├── test_curvature_analysis.py
│   └── test_metrics.py
└── integration/
    ├── test_end_to_end_denoising.py
    └── test_benchmarking_pipeline.py

data/
├── raw/
│   └── da3_benchmark/              # Streamed from HuggingFace, checksummed
├── processed/
│   ├── feature_maps/               # Extracted from GARD encoder (frozen)
│   ├── feature_graphs/             # k-NN graph structures (parquet)
│   ├── spectral_properties/        # Eigenvalues, eigenvectors, curvature (numpy/pickle)
│   ├── reconstructions/            # Outputs from deterministic filter + diffusion baseline
│   └── metrics/                    # Chamfer Distance, F-score, latency tables (CSV)
└── metadata/
    ├── checksums.yaml              # Data integrity records
    └── derivation_log.txt          # Lineage for all transformed files

code/
├── 00_extract_features.py          # GARD encoder → feature maps (batch processing)
├── 01_construct_graphs.py          # Feature maps → k-NN graphs
├── 02_spectral_analysis.py         # Eigendecomposition, curvature, correlation analysis
├── 03_optimize_filter.py           # Validation-set optimization of filter parameters
├── 04_apply_deterministic_filter.py # Apply optimized filter to test set
├── 05_run_diffusion_baseline.py    # Diffusion baseline (if available in GARD repo)
├── 06_compute_metrics.py           # Chamfer Distance, F-score, latency
├── 07_sensitivity_analysis.py      # Parameter sweep (k ∈ {5, 10, 15})
├── 08_statistical_testing.py       # Wilcoxon signed-rank test, Bonferroni correction
└── 09_generate_report.py           # Summary tables, figures, final report

requirements.txt                    # Pinned dependencies (Python 3.11)
```

**Structure Decision**: Single-project layout (Option 1) with clear separation of data-loading, core algorithms, metrics, and benchmarking. Feature extraction, graph construction, spectral analysis, and filtering are logically grouped in `src/gard_denoising/`. Tests follow the contract-unit-integration hierarchy. Data flows through `data/raw/` → `data/processed/` with checksums and lineage tracked in `data/metadata/`. Code scripts are numbered sequentially to enforce task ordering (data download before feature extraction, feature extraction before graph construction, etc.).

## Complexity Tracking

No constitution violations. The project is a single, focused research study on CPU hardware with no multi-project entanglement, no architectural scaffolding, and no generic API requirements.

---
