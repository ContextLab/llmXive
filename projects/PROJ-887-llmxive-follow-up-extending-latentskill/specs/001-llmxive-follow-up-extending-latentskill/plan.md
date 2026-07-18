# Implementation Plan: llmXive follow-up: extending "LatentSkill: From In-Context Textual Skills to In-Weight Latent Skills"

**Branch**: `001-lattentskill-retrieval-geometry` | **Date**: 2026-07-14 | **Spec**: `specs/001-lattentskill-retrieval-geometry/spec.md`
**Input**: Feature specification from `/specs/001-lattentskill-retrieval-geometry/spec.md`

## Summary

This project implements a CPU-only retrieval and interpolation mechanism to replace the hypernetwork in the "LatentSkill" framework. The primary requirement is to ingest pre-trained LoRA adapters (A and B matrices) from ALFWorld and Search-QA benchmarks, flatten them into normalized high-dimensional vectors, and construct a "Skill Vector Database." The technical approach involves using frozen sentence-transformers for text embeddings to query this database, applying three approximation strategies (nearest-neighbor, arithmetic mean, cosine-weighted mean), and validating the results against a baseline using environment logic (task success) on a -core CPU runner.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU only), `numpy`, `scikit-learn`, `sentence-transformers` (all-MiniLM-L6-v2), `transformers` (quantized base model), `pandas`, `scipy` (statistical tests), `llama-cpp-python` (CPU-optimized inference).  
**Storage**: Local filesystem (`data/` for raw weights, `artifacts/` for vector indices and synthesized adapters).  
**Testing**: `pytest` (unit tests for vector math, integration tests for retrieval pipeline).  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, 7 GB RAM, No GPU).  
**Project Type**: Research/Computational Experiment  
**Performance Goals**: Skill selection latency < 1s; Total job runtime < 6h; Memory footprint < 6.5 GB (leaving GB headroom).  
**Constraints**: No GPU/CUDA; **Primary Quantization**: `llama-cpp-python` (GGUF format); `bitsandbytes` explicitly excluded for CPU inference due to CUDA dependency and memory overhead. Strict adherence to FR-006 (Benjamini-Hochberg correction).  
**Scale/Scope**: Multiple LoRA adapters (inferred from typical benchmark sizes); + runs per task.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
| :--- | :--- | :--- |
| **I. Reproducibility** | **Compliant** | Plan mandates pinned `requirements.txt`, random seeds, and static index generation before evaluation. |
| **II. Verified Accuracy** | **Compliant** | All dataset references will be validated against the `# Verified datasets` block. **Implementation**: The `src/validate/citation_check.py` script will be invoked in the CI pre-run step to verify URLs before execution. |
| **III. Data Hygiene** | **Compliant** | Raw LoRA weights preserved; derived vectors written to new files with checksums. |
| **IV. Single Source of Truth** | **Compliant** | Success metrics trace to `data/` results and `code/` execution logs. |
| **V. Versioning Discipline** | **Compliant** | **Protocol**: The `Advancement-Evaluator` agent updates `state/projects/...yaml` with content hashes for every artifact change. The `src/utils/versioning.py` script computes SHA256 hashes and updates the state file automatically upon artifact write. |
| **VI. Parameter-Space Linearity** | **Compliant** | Plan explicitly includes FR-007 (Spearman correlation) and FR-005 (Permutation tests) to validate linearity. |
| **VII. Edge-Deployment Latency** | **Compliant** | Plan mandates benchmarking on the 2-core CPU runner (SC-003). |

## Project Structure

### Documentation (this feature)

```text
specs/001-lattentskill-retrieval-geometry/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   ├── skill-vector.schema.yaml
│   └── evaluation-result.schema.yaml
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── ingestion/
│   ├── __init__.py
│   ├── download_weights.py       # NEW: Download or generate proxy weights
│   └── flatten_lora.py           # FR-001: Ingest and flatten LoRA
├── retrieval/
│   ├── __init__.py
│   ├── vector_db.py              # FR-001: Build index
│   ├── query.py                  # FR-002: Text embedding generation
│   └── strategies.py             # FR-003: NN, Mean, Weighted Mean
├── evaluation/
│   ├── __init__.py
│   ├── runner.py                 # FR-004: Apply adapter & run env
│   └── stats.py                  # FR-005, FR-006: Permutation tests & BH correction
├── validation/
│   └── linearity_check.py        # FR-007: Text-weight alignment
├── validate/
│   └── citation_check.py         # NEW: Reference-Validator implementation
├── utils/
│   ├── config.py                 # Seed pinning, path resolution
│   └── versioning.py             # NEW: State file hash updates
└── main.py                       # Orchestration script

tests/
├── contract/
│   └── test_schemas.py           # Validates JSON/YAML against contracts
├── unit/
│   └── test_strategies.py
└── integration/
    └── test_pipeline.py

data/
├── raw/                      # Downloaded LoRA weights (read-only)
├── processed/                # Flattened vectors, indices
└── results/                  # Evaluation logs, stats

artifacts/
└── synthesized_adapters/     # Generated LoRA weights for novel tasks
```

**Structure Decision**: Single `src/` layout chosen for research code simplicity, avoiding unnecessary microservice abstraction. The `contracts/` directory in `specs/` holds the schemas for validation, while `tests/contract/` enforces them.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **None** | The complexity is driven by the scientific requirements (FR-006, FR-007) and hardware constraints (CPU-only, 7GB RAM). | N/A |