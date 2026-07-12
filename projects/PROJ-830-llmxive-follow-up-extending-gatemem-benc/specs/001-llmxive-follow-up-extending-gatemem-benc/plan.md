# Implementation Plan: GateMem Gatekeeper Extension

**Branch**: `001-gatekeeper-memory-governance` | **Date**: 2026-07-12 | **Spec**: `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`
**Input**: Feature specification from `specs/001-llmxive-follow-up-extending-gatemem-benc/spec.md`

## Summary

This project extends the "GateMem" benchmark by implementing a lightweight, CPU-tractable rule-based gatekeeper. The system intercepts user queries, validates them against role-based access policies and active deletion logs using a frozen DistilBERT intent classifier and deterministic regex logic, and filters memory chunks before they reach the LLM. The primary goal is to measure improvements in Access Control (leakage reduction) and Forgetting (deletion compliance) while ensuring Utility degradation remains within an acceptable margin., all within the constraints of a free-tier CPU-only CI runner.

Crucially, this plan addresses construct validity by distinguishing between "Hard Leaks" (exact string matches, deterministic) and "Soft Leaks" (semantic paraphrasing, probabilistic). Statistical analysis will focus on the reduction of Soft Leaks using permutation tests to account for the deterministic nature of Hard Leaks and the small sample size of domains.

## Technical Context

**Language/Version**: Python 3.11
**Primary Dependencies**: `transformers` (CPU-only), `scikit-learn`, `pandas`, `pytest`, `torch` (CPU build), `datasets` (HuggingFace), `sentence-transformers` (for semantic leakage detection)
**Storage**: Local JSON/JSONL files in `data/` (derived from GateMem), SQLite for deletion logs (optional, or in-memory dict)
**Testing**: `pytest` (unit, integration, contract)
**Target Platform**: Linux (GitHub Actions free-tier runner: CPU, ~7 GB RAM)
**Project Type**: Research pipeline / Benchmark extension
**Performance Goals**: < 6 hours total runtime for full evaluation; < 7 GB peak RAM; CPU-only inference.
**Constraints**: No GPU/CUDA; no 8-bit/4-bit quantization; deterministic rule engine; strict adherence to GateMem ground-truth annotations.
**Scale/Scope**: Evaluation across GateMem domains (medical, office, education, household) with sensitivity analysis on confidence thresholds.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Principle I (Reproducibility)**: Plan ensures all random seeds are pinned in `code/` scripts and external datasets are fetched via canonical HuggingFace URLs. The pipeline is designed to run end-to-end in a fresh CI environment.
- **Principle II (Verified Accuracy)**: **NEW STEP**: The plan includes a "Reference Validation" phase that explicitly invokes the Reference-Validator Agent to verify the GateMem dataset URL and perform the `title-token-overlap` check (≥0.7) before any data download or analysis.
- **Principle III (Data Hygiene)**: Raw data will be downloaded to `data/raw/` and checksummed. All processed data (e.g., filtered logs, annotated outputs) will be written to `data/processed/` with derivation notes.
- **Principle IV (Single Source of Truth)**: All metrics (Access Control, Forgetting, Utility) will be calculated programmatically from `code/` and `data/` artifacts. No manual entry of statistics in the paper.
- **Principle V (Versioning Discipline)**: **NEW STEP**: The plan includes a "Versioning & State Update" phase that explicitly generates content hashes for `data/` and `code/` artifacts and updates the `state/...yaml` file's `artifact_hashes` map upon changes, ensuring compliance with the Constitution.
- **Principle VI (CPU-First Deployment Validation)**: The plan explicitly selects `transformers` with `torch` CPU builds and avoids any GPU-specific libraries (bitsandbytes, CUDA). The DistilBERT model is specified as "frozen" and "default precision" to fit RAM limits.
- **Principle VII (Deterministic Governance Enforcement)**: The gatekeeper logic is split: DistilBERT for semantic intent (with fixed seeds) and a deterministic regex/logic engine for rule enforcement. The plan ensures the "Leakage Detector" uses a hybrid approach (exact + semantic) to avoid stochastic variance in the *decision* logic while measuring *semantic* leakage.

## Project Structure

### Documentation (this feature)

```text
specs/001-gatekeeper-memory-governance/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (generated in Phase 1)
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-830-llmxive-follow-up-extending-gatemem-benc/
├── code/
│   ├── __init__.py
│   ├── gatekeeper/
│   │   ├── __init__.py
│   │   ├── classifier.py       # DistilBERT intent classification (CPU)
│   │   ├── rules.py            # Deterministic regex/logic engine
│   │   └── pipeline.py         # Orchestration: Query -> Gate -> LLM
│   ├── metrics/
│   │   ├── __init__.py
│   │   ├── leakage_detector.py # Hybrid: Exact + Semantic (Sentence-Transformers)
│   │   ├── calculator.py       # Access Control, Forgetting, Utility scores
│   │   └── utility_judge.py    # LLM-as-a-Judge for utility (Context-Aware)
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── stats.py            # Permutation tests, Wilcoxon, Bootstrapping
│   │   └── profiler.py         # Latency and memory tracking
│   ├── data/
│   │   ├── loader.py           # GateMem data ingestion (Aggregates 4 domains)
│   │   └── preprocess.py       # Data cleaning/formatting
│   └── main.py                 # Entry point for pipeline execution
├── data/
│   ├── raw/                    # Downloaded GateMem JSONL (All domains)
│   ├── processed/              # Filtered logs, model outputs
│   └── logs/                   # Execution logs, timing data
├── tests/
│   ├── unit/
│   │   ├── test_rules.py
│   │   └── test_classifier.py
│   ├── integration/
│   │   └── test_pipeline.py
│   └── contract/
│       └── test_schemas.py
├── requirements.txt
└── README.md
```

**Structure Decision**: A modular Python package structure under `code/` is selected to separate concerns (Gatekeeper, Metrics, Analysis). This aligns with the research nature of the project, allowing independent testing of the rule engine, the classifier, and the statistical analysis. The `data/` directory follows the strict separation of raw and processed data mandated by Principle III.

## Implementation Phases

### Phase 0: Research & Validation (Current)
- **0.1**: Reference Validation: Invoke Reference-Validator Agent to verify GateMem dataset URL and title-token overlap.
- **0.2**: Dataset Verification: Confirm presence of `leak-target` and `role` fields in the actual dataset. If missing, define fallback strategy (synthetic injection or rule-log based metrics).
- **0.3**: Power Analysis: Calculate minimum detectable effect size (MDES) for n=4 domains. Document limitations.

### Phase 1: Data Model & Contracts
- **1.1**: Define Data Model: Specify structures for Query, MemoryChunk, DeletionLog, and EvaluationResult (including `semantic_leak_score`).
- **1.2**: Generate Contracts: Create `contracts/dataset.schema.yaml`, `contracts/metrics.schema.yaml`, `contracts/output.schema.yaml`.
- **1.3**: Versioning Setup: Implement hash generation script for `data/` and `code/`.

### Phase 2: Implementation
- **2.1**: Implement Gatekeeper: DistilBERT classifier + Deterministic Rule Engine.
- **2.2**: Implement Leakage Detector: Hybrid (Exact + Semantic) detector.
- **2.3**: Implement Metrics Calculator: Access Control (Semantic), Forgetting, Utility (Context-Aware).
- **2.4**: Implement Statistical Analysis: Permutation tests, Wilcoxon, Bootstrapping.

### Phase 3: Execution & Reporting
- **3.1**: Run Pipeline: Execute on full dataset.
- **3.2**: Update State: Generate hashes and update `state/...yaml` `artifact_hashes`.
- **3.3**: Generate Paper: Write results to `paper/` based on `data/processed/`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| N/A | N/A | The project adheres to the CPU-only constraint and modular design is standard for research pipelines. No complexity violations identified. |