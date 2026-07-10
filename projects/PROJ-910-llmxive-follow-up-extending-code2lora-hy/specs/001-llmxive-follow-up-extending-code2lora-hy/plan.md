# Implementation Plan: llmXive follow-up: extending "Code2LoRA: Hypernetwork-Generated Adapters for Code Language Models under Software Evolution"

**Branch**: `001-ast-based-adapter-generation` | **Date**: 2026-07-10 | **Spec**: `specs/001-ast-based-adapter-generation/spec.md`
**Input**: Feature specification from `specs/001-ast-based-adapter-generation/spec.md`

## Summary

This project extends the Code2LoRA framework by replacing the heavy neural repository encoder with a static-analysis-based feature extractor. The system extracts syntactic metrics (cyclomatic complexity, depth of inheritance, import graph centrality, token histograms) from Python source files using the standard `ast` module. These features are mapped to the original embedding dimension via a lightweight Multi-Layer Perceptron (MLP) to generate repository-specific LoRA adapters. The goal is to achieve adapter generation with at least one order of magnitude lower latency while maintaining >80% of the baseline neural encoder's accuracy on RepoPeftBench assertion-completion tasks, all within the constraints of a GitHub Actions free-tier runner (limited CPU and RAM).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `transformers`, `peft`, `torch` (CPU-only), `scikit-learn`, `networkx`, `llama-cpp-python`, `ast`, `tokenize`  
**Storage**: Local filesystem for datasets and checkpoints; GitHub Actions ephemeral storage (limited capacity)

The research question, method, and references remain unchanged as per the planning document requirements.  
**Testing**: `pytest` with `pytest-cov`  
**Target Platform**: Linux (GitHub Actions free-tier runner)  
**Project Type**: Research pipeline / CLI tool  
**Performance Goals**: Adapter generation < 6 hours; latency reduction ≥ 10x vs baseline; memory usage < 6 GB  
**Constraints**: No GPU; no external heavy parsers; deterministic AST extraction; **Hard Constraint: Base model size ≤ 1.5B parameters** (TinyLlama-1.1B or CodeLlama-1.3B); strict adherence to RAM limits  
**Scale/Scope**: Single repository analysis; test set subset of RepoPeftBench (Python subset)  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Implementation Detail |
|-----------|-------------------|----------------------|
| **I. Reproducibility** | ✅ Compliant | Random seeds pinned in `code/`; datasets fetched from canonical HuggingFace URL; `requirements.txt` pins all versions. |
| **II. Verified Accuracy** | ✅ Compliant | All citations (e.g., Code2LoRA baseline, RepoPeftBench) verified against primary sources before inclusion in research/paper. |
| **III. Data Hygiene** | ✅ Compliant | Raw data checksummed in `state/`; derivations (feature vectors) written to new files; no in-place modification. |
| **IV. Single Source of Truth** | ✅ Compliant | All figures/stats trace to `data/` rows and `code/` blocks; no hand-typed numbers in paper. |
| **V. Versioning Discipline** | ✅ Compliant | Content hashes for all artifacts; `updated_at` timestamp updated on change. |
| **VI. Static-Analysis Fidelity** | ✅ Compliant | AST feature extraction uses standard `ast` module; deterministic; verifiable against source commits. |
| **VII. Performance-Latency Trade-off** | ✅ Compliant | Paired measurements of exact-match accuracy and generation latency recorded; **Paired t-test** (per Constitution) planned for significance, with Wilcoxon as secondary check if normality fails. |

## Project Structure

### Documentation (this feature)

```text
specs/001-ast-based-adapter-generation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── tasks.md             # Phase 2 output (moved to specs dir for consistency)
└── contracts/           # Phase 1 output
```

### Source Code (repository root)

```text
projects/PROJ-910-llmxive-follow-up-extending-code2lora-hy/
├── code/
│   ├── __init__.py
│   ├── main.py                 # Entry point for CLI
│   ├── feature_extractor/
│   │   ├── __init__.py
│   │   ├── ast_parser.py       # FR-001, FR-007: AST parsing & metrics
│   │   └── graph_builder.py    # Import graph centrality
│   ├── hypernetwork/
│   │   ├── __init__.py
│   │   ├── mlp_projection.py   # FR-002: MLP mapping
│   │   └── adapter_generator.py# FR-003: Adapter generation logic
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── runner.py           # FR-004: RepoPeftBench evaluation
│   │   └── sensitivity.py      # FR-005: Sensitivity analysis
│   └── utils/
│       ├── config.py           # Random seeds, paths
│       └── logging.py          # FR-007, FR-008, FR-009: Error handling
├── data/
│   ├── raw/                    # Downloaded RepoPeftBench parquet
│   ├── processed/              # Feature vectors (checksummed)
│   └── adapters/               # Generated .safetensors files
├── tests/
│   ├── contract/               # Schema validation tests
│   ├── integration/            # End-to-end pipeline tests
│   └── unit/                   # AST parser, MLP unit tests
├── requirements.txt
└── README.md
```

**Structure Decision**: Single project structure chosen for simplicity and alignment with research pipeline nature. All modules are organized by functional responsibility (feature extraction, hypernetwork, evaluation).

## Complexity Tracking

> No violations detected. Complexity is managed via modular design and strict resource constraints.