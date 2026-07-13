# Implementation Plan: llmXive Follow-up: Extending "Your UnEmbedding Matrix is Secretly a Feature Lens for Text Embeddings"

**Branch**: `001-llmxive-crosslingual-edge-spectrum` | **Date**: 2026-07-13 | **Spec**: `specs/001-llmxive-crosslingual-edge-spectrum/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-crosslingual-edge-spectrum/spec.md`

## Summary

This project implements a CPU-tractable pipeline to extract the "edge spectrum" (top-$k$ singular vectors) of unembedding matrices from three distinct LLMs (Llama-3-8B, BLOOM-7B, Qwen-1.5-7B) and compute frequency-weighted "average token" vectors to measure cross-lingual anisotropy. The approach strictly adheres to the 7GB RAM constraint by using `scikit-learn`'s `TruncatedSVD` (randomized SVD) to avoid materializing full matrices, and performs Orthogonal Procrustes alignment to enable valid cross-lingual comparisons. Statistical significance is determined via a permutation test with a spherical null baseline, with sensitivity analysis on iteration counts to ensure p-value convergence.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `scikit-learn`, `transformers`, `safetensors`, `pandas`, `numpy`, `requests`  
**Storage**: Local `data/` directory for intermediate CSVs (singular values, vectors, frequency counts) and checksummed raw frequency subsets.  
**Testing**: `pytest` for unit tests on projection logic and permutation stability; integration tests via GitHub Actions runner memory profiling.  
**Target Platform**: Linux (GitHub Actions Free Tier: 2 CPU, ~7 GB RAM, no GPU).  
**Project Type**: Computational Research Pipeline  
**Performance Goals**: Peak RAM ≤ 7 GB; Total runtime ≤ 60 minutes (per SC-004); SVD error ≤ 1e-3 on subsamples.  
**Constraints**: No GPU usage; No full SVD; No model training; Strict adherence to verified dataset URLs; All random seeds pinned.  
**Scale/Scope**: 3 Models × 50 Singular Vectors; Permutation N ∈ {100, 1000, 10000}; ~100k tokens per language frequency list.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Evidence / Plan Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | **PASS** | Plan mandates pinned random seeds in `code/` and deterministic `TruncatedSVD` with fixed seed. Data fetched from canonical HF/CC sources. |
| **II. Verified Accuracy** | **PASS** | Plan requires all dataset URLs to be sourced *only* from the `# Verified datasets` block in the runtime context. No fabricated URLs. |
| **III. Data Hygiene** | **PASS** | Plan includes checksumming of all downloaded frequency files. No in-place modification; derivations saved as new files (e.g., `freq_eng_aligned.csv`). |
| **IV. Single Source of Truth** | **PASS** | All statistics in the final report will be generated programmatically from `data/` artifacts. No hand-typed numbers. |
| **V. Versioning Discipline** | **PASS** | Implementation will generate content hashes for all `data/` and `code/` artifacts to update the state YAML. |
| **VI. Cross-Lingual Spectral Isolation** | **PASS** | Plan explicitly separates frequency lists (RedPajama/CC) from model weights. Logic ensures English frequencies are only used with Llama/BLOOM, not Qwen. |
| **VII. Non-Circular Validation** | **PASS** | Permutation test uses independent spherical null generation. Validation relies on structural SVD properties, not downstream model predictions. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-crosslingual-edge-spectrum/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-880-llmxive-follow-up-extending-your-unembed/
├── code/
│   ├── requirements.txt
│   ├── __init__.py
│   ├── config.py            # Paths, seeds, hyperparameters (k=50)
│   ├── data_ingestion.py    # Download frequency lists, verify checksums
│   ├── svd_extraction.py    # TruncatedSVD for unembedding matrices
│   ├── alignment.py         # Procrustes alignment logic
│   ├── projection.py        # Average vector calculation & projection
│   ├── stats.py             # Permutation test & p-value convergence
│   └── report.py            # Generate final CSV/JSON results
├── data/
│   ├── raw/                 # Downloaded frequency lists (checksummed)
│   ├── processed/           # Aligned vectors, SVD outputs
│   └── results/             # Final statistics, top-loading tokens
├── tests/
│   ├── unit/                # Test projection logic, permutation stability
│   └── integration/         # Memory profiling, end-to-end small run
└── docs/
    └── constitution.md      # Project constitution
```

**Structure Decision**: Single project structure (`code/`, `data/`, `tests/`) selected to minimize I/O overhead and simplify dependency management for a CPU-bound research pipeline. The `contracts/` directory will house the YAML schemas for data validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Randomized SVD** | Required to fit 7B parameter model unembedding matrices (approx. 50k x 4096) into 7GB RAM. | Full SVD (`numpy.linalg.svd`) requires O(N^3) memory and would OOM on the CI runner. |
| **Procrustes Alignment** | Essential for valid cross-lingual comparison of subspaces which may be rotated differently. | Direct cosine similarity without alignment would conflate rotational differences with semantic shifts. |
| **Permutation Sweep** | Required to satisfy SC-006 (p-value stability) and ensure statistical rigor. | Single N=1000 run is insufficient to prove convergence; a sweep is needed to detect instability. |

## Phase Execution Order

1.  **Phase 0: Research & Dataset Verification**
    *   Verify availability of unembedding matrices for Llama-3, BLOOM, Qwen.
    *   Confirm frequency list URLs (RedPajama/CC) and downloadability.
    *   Validate `TruncatedSVD` memory footprint on a subset.
2.  **Phase 1: Data Model & Contracts**
    *   Define schemas for SVD outputs, frequency lists, and alignment results.
    *   Establish checksum protocols for `data/`.
3.  **Phase 2: Implementation (SVD & Alignment)**
    *   Implement `svd_extraction.py` with streaming memory checks.
    *   Implement `alignment.py` for Procrustes.
4.  **Phase 3: Implementation (Projection & Stats)**
    *   Implement `projection.py` for average vectors.
    *   Implement `stats.py` for permutation tests and convergence sweeps.
5.  **Phase 4: Reporting**
    *   Generate top-loading token lists and final statistics.
