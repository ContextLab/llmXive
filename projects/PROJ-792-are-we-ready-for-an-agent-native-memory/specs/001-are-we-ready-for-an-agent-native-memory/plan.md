# Implementation Plan: Are We Ready For An Agent-Native Memory System?

**Branch**: `792-are-we-ready-for-an-agent-native-memory` | **Date**: 2026-06-26 | **Spec**: `specs/792-are-we-ready-for-an-agent-native-memory/spec.md`
**Input**: Feature specification from `/specs/792-are-we-ready-for-an-agent-native-memory/spec.md`

## Summary

This project reproduces and validates the *technical execution* of the evaluation pipeline described in the paper "Are We Ready For An Agent-Native Memory System?" by executing the vendored `awesome-agent-memory` codebase on a constrained CI environment (CPU-only, 7GB RAM). 

**Critical Scope Limitation**: Due to the absence of verified datasets containing true multi-turn dialogue or long-horizon planning sequences, this reproduction **cannot** validate the claim that systems maintain "coherence across temporal scales" in a naturalistic setting. Instead, the project:
1.  Uses static text datasets as proxies for **Representation** and **Retrieval** stress tests.
2.  Implements a **Synthetic Update Protocol** to simulate "Maintenance" (updates) on static data, explicitly acknowledging this does not validate true temporal coherence.
3.  Focuses on the *mechanical feasibility* of running the pipeline, measuring cost and performance under resource constraints.

The primary goal is to determine if current agent memory architectures can be executed and evaluated within free-tier CI limits, while explicitly flagging the limitations in validating the paper's core cognitive claims.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `datasets`, `pandas`, `scikit-learn`, `numpy`, `huggingface_hub`, `sentence-transformers` (CPU build), `pytest`  
**Storage**: Local filesystem (temporary artifacts in `data/`, `results/`)  
**Testing**: `pytest` (unit tests for ingestion, integration tests for pipeline execution)  
**Target Platform**: Linux (GitHub Actions free-tier runner: limited CPU, 7GB RAM)  
**Project Type**: Computational Research / Reproduction Study  
**Performance Goals**: Complete evaluation of 3 systems within 6 hours; memory usage < 6.5GB (leaving 0.5GB buffer)  
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization requiring CUDA; automatic downsampling for large datasets; deterministic output where possible (seeds).  
**Scale/Scope**: Multiple memory systems, a benchmark dataset (subsampled + synthetic updates), core module evaluations.

> **Dataset Fit Note**: The verified dataset (MixSub-LLaMA) is text-only and static. It is suitable for testing Representation and Retrieval. It **lacks** the temporal structure required to validate "Maintenance" in a naturalistic sense. The plan addresses this by using a **Synthetic Update Protocol** to inject artificial updates, explicitly labeling results as "Proxy Evaluation" rather than a full reproduction of the original paper's specific dialogue benchmarks.

## Constitution Check

*Note: No project-specific `constitution.md` was supplied. This check maps to standard research integrity principles.*

1.  **Reproducibility**: The plan mandates fixed random seeds and explicit version pinning for all dependencies to ensure <5% variance (SC-005).
2.  **Resource Honesty**: The plan explicitly avoids GPU dependencies and defines a hard memory cap with automatic fallback strategies, ensuring the project runs on free-tier CI (FR-001, FR-004).
3.  **Data Integrity**: The plan verifies dataset schemas against the codebase requirements before execution and logs any deviations or downsampling (FR-002).
4.  **Scientific Rigor**: The plan explicitly states that results are "descriptive/indicative" only due to the proxy nature of the data and the underpowered sample size. It does not make causal claims about agent behavior.
5.  **Transparency**: All deviations from the original paper (e.g., dataset substitution, synthetic updates, model downsizing) are logged and reported in the final summary.

## Project Structure

### Documentation (this feature)

```text
specs/792-are-we-ready-for-an-agent-native-memory/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (contains input schema + new outputs)
│   └── evaluation_metrics.schema.yaml  # Input contract (verified) + extended
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── ingestion/
│   ├── __init__.py
│   ├── loader.py          # Handles dataset loading and schema validation
│   └── preprocessor.py    # Downsampling and context truncation logic
├── evaluation/
│   ├── __init__.py
│   ├── runner.py          # Main evaluation orchestrator
│   ├── modules/
│   │   ├── representation.py
│   │   ├── extraction.py
│   │   ├── retrieval.py
│   │   └── maintenance.py
│   └── metrics.py         # Precision, recall, cost calculation
├── analysis/
│   ├── __init__.py
│   ├── aggregator.py      # Cost-performance trade-off analysis
│   └── report_gen.py      # Summary report generation
├── config/
│   └── defaults.yaml      # Memory limits, seeds, model paths
└── utils/
    ├── memory_guard.py    # RAM monitoring and OOM prevention
    └── logging.py

tests/
├── contract/
│   ├── test_ingestion_schema.py
│   └── test_metrics_schema.py
├── integration/
│   └── test_full_pipeline.py
└── unit/
    ├── test_downsampling.py
    └── test_memory_guard.py
```

**Structure Decision**: A modular `src/` layout is chosen to separate ingestion, evaluation, and analysis phases. This aligns with the sequential dependency of the workflow (Data -> Evaluation -> Analysis) and facilitates the "smoke test" nature of US-1 before full execution. The `contracts/` directory includes the pre-existing input schema and will be extended with new schemas if necessary.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Automatic Memory Guard | Required to prevent OOM on 7GB runner for large datasets (US-2, FR-004). | Hard-limiting dataset size statically is too rigid; dynamic detection allows running larger subsets if RAM permits. |
| CPU-Only Model Substitution | Original paper likely used LLM APIs or heavy models; CI has no GPU. | Using a heavy model would crash the runner. A small CPU model (TinyLlama) or rule-based baseline is necessary for feasibility. |
| Dataset Subset & Synthetic Updates | Original datasets lack temporal structure for Maintenance testing. | Running on full datasets exceeds RAM. A representative subset with synthetic updates is the only path to a runnable reproduction. |