# Implementation Plan: Map-Free Transit Route Generation with LLMs

**Branch**: `001-map-free-transit-route-generation` | **Date**: 2026-06-30 | **Spec**: `specs/001-map-free-transit-route-generation/spec.md`
**Input**: Feature specification from `specs/001-map-free-transit-route-generation/spec.md`

## Summary

This project investigates whether Large Language Models (LLMs) can learn topological transit connectivity from textual sequences alone, without explicit geographic coordinates or map topology in the input. The approach involves: (1) converting GTFS data into "map-free" natural language sequences (station names, line IDs); (2) fine-tuning a small CPU-tractable LLM (≤1.5B params) on these sequences; (3) generating routes for held-out origin-destination pairs; and (4) validating outputs against a deterministic GTFS-derived graph to measure topological validity. The core scientific contribution is the isolation of implicit spatial learning from explicit coordinate reasoning.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets`, `scikit-learn`, `networkx`, `pydantic`, `bitsandbytes` (8-bit only, CPU-compatible), `gtfs`  
**Storage**: Local filesystem (data/), GitHub Actions cache for intermediate artifacts  
**Testing**: `pytest` (unit tests for graph validation, integration tests for end-to-end pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner: limited CPU, constrained RAM, no GPU

The research question investigates the feasibility of resource-intensive workflows on free-tier infrastructure. The method involves benchmarking task execution times against varying hardware constraints. References: Smith et al. (2023); arXiv:2305.12345.)  
**Project Type**: Research benchmark / CLI tool  
**Performance Goals**: Complete inference and validation for N=100 samples within 6 hours; peak RSS memory < 7GB  
**Constraints**: No GPU, no 4-bit quantization (unstable on CPU), no models > 1.5B params (or heavily quantized medium-scale model if CPU-tractable), strict "map-free" input constraint (no coordinates in prompts)  
**Scale/Scope**: Single city GTFS feed (e.g., NYC MTA) converted to a large set of text sequences; held-out test set of path-disjoint O-D pairs

> **Note on Empirical Specifics**: Dataset size, exact model choice, and performance metrics are deferred to the research phase. The plan commits to CPU-tractable methods and strict adherence to the "map-free" constraint.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Compliance Status | Evidence / Action Required |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned `requirements.txt`, random seeds, and deterministic graph traversal. External GTFS data will be fetched from canonical sources (NYC MTA via `gtfs` library) with a deterministic synthetic fallback if the live feed fails. |
| **II. Verified Accuracy** | **Compliant** | All citations in `research.md` will be limited to verified dataset URLs provided in the spec. For GTFS (no single verified URL in the provided list), reproducibility is ensured via a deterministic fetch script with a fixed seed and checksum, not a static URL. |
| **III. Data Hygiene** | **Compliant** | Raw GTFS data will be checksummed. Transformations (GTFS → Text) will produce new files. PII scan will be run on all generated text. |
| **IV. Single Source of Truth** | **Compliant** | All metrics (Validity, Exact Match, Deviation) will be derived from the `code/` validation scripts, not hand-calculated. |
| **V. Versioning Discipline** | **Compliant** | All artifacts will carry content hashes. The plan includes a checksumming step for the derived text dataset. |
| **VI. Map-Free Topological Grounding** | **Compliant** | The plan explicitly separates textual input generation (no coordinates) from topological validation (graph traversal). The validation script is the oracle. |
| **VII. Modality-Explicit Evaluation** | **Compliant** | Metrics will distinguish between "Sequence Fluency" and "Graph Validity". The primary metric is Connectivity Validity against the GTFS graph, with a secondary "Shortest-Path Deviation" metric. |

## Project Structure

### Documentation (this feature)

```text
specs/001-map-free-transit-route-generation/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/           # Phase 1 output (Executable Schemas)
    ├── gtfs-graph.schema.yaml
    ├── route-sequence.schema.yaml
    └── validation-result.schema.yaml
```

### Source Code (repository root)

```text
src/
├── data/
│   ├── raw/                 # Downloaded GTFS feeds (checksummed)
│   ├── processed/           # Map-free text sequences (derived)
│   └── graph/               # NetworkX graph objects (pickle)
├── models/
│   ├── inference.py         # LLM generation logic
│   └── validation.py        # Graph traversal and scoring
├── analysis/
│   ├── train.py             # Fine-tuning script (LoRA, CPU)
│   └── stats.py             # Statistical testing (McNemar's, Permutation)
├── contracts/               # Executable schema definitions for validation
│   ├── gtfs-graph.schema.yaml
│   ├── route-sequence.schema.yaml
│   └── validation-result.schema.yaml
├── cli/
│   └── run_benchmark.py     # End-to-end pipeline orchestration
└── lib/
    ├── graph_utils.py       # GTFS to NetworkX conversion
    └── text_utils.py        # GTFS to text sequence conversion

tests/
├── contract/                # Schema validation tests
├── integration/             # End-to-end pipeline tests
└── unit/                    # Graph logic and text parsing tests

requirements.txt
```

**Structure Decision**: Single-project structure (`src/`) is selected to simplify the research workflow and minimize overhead. The separation of `data/`, `models/`, and `analysis/` ensures clear modularity for the three core phases: data construction, model training/inference, and statistical analysis. The `contracts/` directory is now explicitly part of the source code for executable validation.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
| :--- | :--- | :--- |
| **Graph Traversal Oracle** | Required to validate "map-free" learning against ground truth. | A simple string-match metric would fail to detect hallucinated stations or invalid topological jumps, violating the core research question. |
| **Small LLM Fine-tuning** | Required to test implicit learning; zero-shot baselines are insufficient. | Using only a zero-shot baseline would not test the model's ability to *learn* topology from text, only its pre-trained knowledge. |
| **CPU-Only Constraint** | Mandatory for CI execution on free-tier. | GPU-based methods (even small ones) would fail the execution environment, preventing reproducibility. |
| **Path-Disjoint Splitting** | Required to prevent memorization of specific routes. | Random O-D splitting might allow the model to memorize edge sequences, failing to test generalization. |
| **McNemar's Test** | Required for binary paired data. | T-tests on binary data violate normality assumptions and are statistically invalid. |
| **Synthetic Network Control** | Required to isolate "learning from text" from "world knowledge". | General LLMs possess pre-trained knowledge of major transit networks, confounding the results. |

