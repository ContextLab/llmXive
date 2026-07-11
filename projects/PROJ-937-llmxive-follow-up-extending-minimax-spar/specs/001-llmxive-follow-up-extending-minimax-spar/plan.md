# Implementation Plan: llmXive follow-up: extending "MiniMax Sparse Attention"

**Branch**: `001-llmxive-sparse-attention-heuristics` | **Date**: 2026-07-11 | **Spec**: [link]
**Input**: Feature specification from `/specs/001-llmxive-sparse-attention-heuristics/spec.md`

## Summary

This feature implements a zero-parameter heuristic selector to replace the learned "Index Branch" in the MiniMax-M3 model for long-context retrieval tasks. The plan validates whether local statistical properties (Block Entropy, Local Gradient Magnitude, Recency-Weighted Bias) can approximate the information-selection capability of the dense attention baseline. The implementation targets a CPU-only GitHub Actions runner, executing the RULER benchmark (Needle In A Haystack, Multi-Hop) with a frozen model, measuring Exact Match/F1 accuracy, computational overhead, and statistical significance (TOST equivalence test) against a % tolerance threshold.

**Addressed Requirements**:
- **FR-001**: Addressed by `code/models/mini_max_wrapper.py` (frozen mode, Index Branch disable).
- **FR-002**: Addressed by `code/heuristics/gradient_magnitude.py` (CPU-only gradient calc).
- **FR-003**: Addressed by `code/heuristics/block_entropy.py` and `recency_bias.py`.
- **FR-004**: Addressed by `code/main.py` (RULER execution).
- **FR-005**: Addressed by `code/analysis/stats.py` (TOST implementation).
- **FR-006**: Addressed by `code/main.py` and `code/analysis/stats.py` (Sensitivity sweep).
- **SC-001**: Addressed by TOST margin (±2%).
- **SC-002**: Addressed by TOST p-value (alpha=0.05).
- **SC-003**: Addressed by separate timing logs for heuristic vs. inference.
- **SC-004**: Addressed by sensitivity curve generation.
- **SC-005**: Addressed by GGUF -bit quantization and streaming.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `llama-cpp-python` (CPU-only, GGUF), `datasets`, `scipy`, `pandas`, `numpy`, `pytest`, `transformers` (for metadata only).  
**Storage**: Local `data/` directory for cached RULER tasks and model weights; no persistent database.  
**Testing**: `pytest` for unit tests of heuristic logic; `pytest` integration tests for RULER task execution.  
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, GB RAM, no GPU).  
**Project Type**: Research tool / Benchmarking suite.  
**Performance Goals**: Complete RULER tasks within 6 hours; memory footprint < 6 GB during inference.  
**Constraints**: No GPU usage; **MUST use GGUF low-bit quantization** via `llama-cpp-python` to fit model in RAM; strict block alignment for gradient/entropy calculation.  
**Scale/Scope**: RULER tasks, A small number of heuristics will be explored. 

The research question is: Can automated heuristic selection improve the performance of algorithm configuration tools?

The method is: We will implement a runtime system that selects from a set of pre-defined heuristics based on problem features.

(Smith et al., 2020), baseline, sensitivity thresholds (k=10,20,30).

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **I. Reproducibility**: Plan mandates pinned `requirements.txt`, fixed random seeds in `code/`, and re-fetching of canonical RULER datasets from HuggingFace on every run.
- **II. Verified Accuracy**: All dataset citations (RULER) are restricted to the verified official URLs provided in the spec. No fabricated URLs.
- **III. Data Hygiene**: Raw RULER JSONL/Parquet files downloaded to `data/raw/` will be **checksummed (SHA-256) immediately** and the hash recorded in `state/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar.yaml`. No in-place modification.
- **IV. Single Source of Truth**: All accuracy metrics and latency logs will be written to CSV/JSON artifacts in `data/`; the final paper will reference these artifacts directly.
- **V. Versioning Discipline**: Every artifact under this project carries a content hash. The `state/projects/PROJ-937-llmxive-follow-up-extending-minimax-spar.yaml` file will be updated with new checksums upon any artifact change.
- **VI. Zero-Parameter Heuristic Fidelity**: The plan explicitly isolates the computational cost of these heuristics from the frozen MiniMax-M3 model inference. The "Index Branch" will be programmatically disabled. **Metrics will log 'heuristic_time' and 'inference_time' separately** to ensure routing overhead is not conflated.
- **VII. Block-Granular Statistical Validity**: The data processing pipeline will enforce strict block alignment (fixed-size chunks) matching the MiniMax Sparse Attention granularity. **Statistical analysis will only aggregate results where block boundaries align with the original RULER benchmark tasks** to ensure validity.

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-sparse-attention-heuristics/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (not created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-937-llmxive-follow-up-extending-minimax-spar/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point for RULER benchmark execution
│   ├── models/
│   │   ├── __init__.py
│   │   └── mini_max_wrapper.py # Wrapper to disable Index Branch and inject heuristics (Addressed by FR-001)
│   ├── heuristics/
│   │   ├── __init__.py
│   │   ├── gradient_magnitude.py # Addressed by FR-002
│   │   ├── block_entropy.py      # Addressed by FR-003
│   │   └── recency_bias.py       # Addressed by FR-003
│   ├── data/
│   │   ├── __init__.py
│   │   └── ruler_loader.py     # Downloads and parses RULER tasks (Addressed by FR-004)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── stats.py            # TOST, sensitivity analysis (Addressed by FR-005, FR-006)
│   │   └── metrics.py          # Exact Match, F1 calculation
│   └── utils/
│       ├── __init__.py
│       └── logging.py          # CPU time/memory logging (Addressed by SC-003)
├── data/
│   ├── raw/                    # Downloaded RULER JSONL/Parquet (Checksummed per Constitution III)
│   └── processed/              # Block-aligned, sampled tasks
├── tests/
│   ├── unit/
│   │   ├── test_heuristics.py
│   │   └── test_metrics.py
│   └── integration/
│       └── test_ruler_run.py
└── requirements.txt
```

**Structure Decision**: Single project structure selected to simplify dependency management for the research workflow. The `code/` directory is split by domain (models, heuristics, data, analysis) to enforce separation of concerns between the frozen model wrapper, the heuristic logic, and the statistical analysis, ensuring the "Zero-Parameter Heuristic Fidelity" principle is maintained.

## Complexity Tracking

No complexity violations identified. The constraints (CPU-only, 7GB RAM) are addressed by:
1.  **Quantization**: Using GGUF 4-bit quantization via `llama-cpp-python` to fit the model in RAM.
2.  **Sampling**: Limiting RULER tasks to a representative subset if full load exceeds memory.
3.  **Gradient Batching**: Calculating input gradients on small batches (≤4 sequences) to fit in RAM.
4.  **Streaming**: Processing tasks one-by-one to avoid OOM.