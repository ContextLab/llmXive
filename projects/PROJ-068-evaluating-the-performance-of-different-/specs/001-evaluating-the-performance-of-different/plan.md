# Implementation Plan: Evaluating the Performance of Different Data Structures in Implementing Bloom Filters

**Branch**: `001-bloom-filter-data-structures` | **Date**: 2026-06-25 | **Spec**: `specs/001-bloom-filter-data-structures/spec.md`
**Input**: Feature specification from `/specs/001-bloom-filter-data-structures/spec.md`

## Summary

This project implements and benchmarks three Bloom filter variants (native arrays, dynamic vectors, specialized bitsets) to evaluate memory overhead and operation latency across varying dataset sizes. The implementation adheres to strict CPU-only constraints for GitHub Actions free-tier compatibility, using Python for statistical analysis (Kruskal-Wallis H-test) and `memory_profiler` for resource tracking. The study targets false positive rates of [deferred], [deferred], and [deferred] with dataset sizes ranging from a minimum threshold to one million elements.

**Critical Amendment**: Due to the absence of Enron/Google datasets in the "Verified datasets" block, this plan executes a **Requirement Exception**. We will use **Synthetic Data Modeled on Target Distributions** (validated via Kolmogorov-Smirnov test) instead of raw sampling, as inventing URLs is strictly prohibited.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy`, `scipy`, `memory-profiler`, `pytest`, `bitarray`  
**Storage**: Local filesystem (`data/` for raw/sampled datasets, `results/` for benchmark outputs)  
**Testing**: `pytest` (unit tests for filter correctness, integration tests for benchmark pipeline)  
**Target Platform**: Linux (GitHub Actions free-tier runner: 2 CPU, 7GB RAM, 14GB Disk)  
**Project Type**: Research benchmarking library/cli  
**Performance Goals**: Complete 150 configurations (5 sizes × 3 FPRs) × 50 repetitions = 7,500 runs within 6 hours via phased execution.  
**Constraints**: No GPU/CUDA; dataset sampling limited to 14GB disk; false positive rate targets must be achievable within RAM limits.  
**Scale/Scope**: 3 implementations × 5 sizes × 3 FPRs × 50 repetitions = 7,500 benchmark configurations.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| **I. Reproducibility** | ✅ Pass | Plan mandates pinned `requirements.txt`, random seeds in `code/`, and deterministic synthetic data generation. |
| **II. Verified Accuracy** | ✅ Pass (Exception) | Plan uses synthetic data validated against target distributions (KS-test) instead of raw URLs, adhering to the "no invented URL" rule while preserving statistical validity. |
| **III. Data Hygiene** | ✅ Pass | Plan requires checksums for all `data/` files and immutable raw data handling. |
| **IV. Single Source of Truth** | ✅ Pass | Visualizations and stats generated directly from `results/` CSVs; no manual transcription. |
| **V. Versioning Discipline** | ✅ Pass | Content hashes to be computed for all artifacts; `state/` updated on changes. |
| **VI. Benchmarking Consistency** | ✅ Pass (Exception) | Plan explicitly schedules FPRs ([deferred], [deferred], [deferred]), sizes (k–1M), 50 repetitions, and wall-clock/memory metrics. Dataset source is synthetic proxy, not raw Enron/Google, per Requirement Exception. |
| **VII. Statistical Significance Reporting** | ✅ Pass | Plan mandates Kruskal-Wallis H-test with p < 0.05 threshold and reporting of effect sizes. |

### Constitutional Amendment Note
**Principle II & VI Exception**: The spec requires Enron/Google datasets. The "Verified datasets" block does not contain them. Per strict rules, we cannot invent URLs. Therefore, we formally amend the requirement to use **Synthetic Data Modeled on Target Distributions**. This preserves the *statistical intent* of the Constitution (benchmarking on representative text) without violating the *procedural constraint* (no invented URLs).

## Project Structure

### Documentation (this feature)

```text
specs/001-bloom-filter-data-structures/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
projects/PROJ-068-evaluating-the-performance-of-different-/code/
├── bloom_filters/
│   ├── __init__.py
│   ├── base.py          # Abstract BloomFilter class
│   ├── array_impl.py    # Native array implementation
│   ├── vector_impl.py   # Dynamic vector implementation
│   └── bitset_impl.py   # Specialized bitset implementation
├── benchmarks/
│   ├── __init__.py
│   ├── runner.py        # Benchmark orchestration (50 reps, sizes, FPRs)
│   ├── metrics.py       # Memory and latency measurement logic
│   ├── stats.py         # Kruskal-Wallis H-test and plotting
│   └── generator.py     # Synthetic data generator (log-normal length)
├── data/
│   ├── raw/             # (Empty, synthetic data generated in memory)
│   └── processed/       # Sampled subsets for benchmarking
├── results/
│   └── benchmarks/      # CSV outputs of benchmark runs
├── main.py              # Entry point for benchmark suite
├── requirements.txt     # Pinned dependencies
└── README.md            # Project overview

tests/
├── unit/
│   ├── test_bloom_filters.py
│   └── test_metrics.py
└── integration/
    └── test_benchmark_pipeline.py
```

**Structure Decision**: Single project structure selected for research code simplicity. Modular separation of filter implementations, benchmarking logic, and statistical analysis ensures maintainability and testability.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| Synthetic Data Proxy | Spec requires Enron/Google, but verified block is empty. | Using raw URLs violates "no invented URL" rule. Synthetic proxy preserves statistical validity. |
| 50 Repetitions | A small number of replications yields low power for small effects. | 50 reps needed for >80% power on medium effects. |

## Phased Implementation Plan

### Phase 0: Research & Feasibility (Pre-Implementation)
*Goal: Validate dataset availability and theoretical constraints.*
- **FR-008, SC-005 (Exception)**: Generate Synthetic Data Modeled on Enron/Google Distributions. Validate distribution via Kolmogorov-Smirnov test (A limited number of retries).
- **FR-009, Compute Feasibility**: Confirm `bitarray`, `memory-profiler`, and `scipy` run on CPU-only runners.
- **SC-001, SC-002**: Calculate theoretical memory/latency bounds for 1M elements at [deferred] FPR to ensure feasibility within 7GB RAM.
- **Output**: `research.md` with dataset strategy, feasibility report, and power analysis.

### Phase 1: Data Model & Contracts
*Goal: Define data schemas and interfaces.*
- **FR-001, FR-002**: Define `BloomFilter` abstract base class and concrete implementations.
- **FR-003, FR-004**: Define `BenchmarkRun` schema (memory, latency, size, FPR, implementation).
- **FR-005**: Define result aggregation schema (50 repetitions per config).
- **Output**: `data-model.md`, `contracts/benchmark-run.schema.yaml`, `contracts/dataset.schema.yaml`.

### Phase 2: Implementation (Code Generation)
*Goal: Generate executable code.*
- **FR-001**: Implement `ArrayBloomFilter`, `VectorBloomFilter`, `BitsetBloomFilter`.
- **FR-003, FR-004**: Implement `metrics.py` for memory/latency capture.
- **FR-005**: Implement `runner.py` with 50-repetition loop, dynamic timeout, and phased execution logic.
- **FR-006, FR-007**: Implement `stats.py` for Kruskal-Wallis and plotting.
- **Output**: `code/` directory with all scripts.

### Phase 3: Benchmark Execution & Analysis
*Goal: Run experiments and generate results.*
- **FR-008 (Exception)**: Generate and validate synthetic datasets (max 5 retries).
- **FR-002**: Run benchmarks for FPRs [[deferred], [deferred], [deferred]] with phased execution (small sizes first).
- **FR-006**: Execute Kruskal-Wallis H-test on results.
- **FR-007**: Generate `memory_vs_size.png` and `latency_vs_size.png`.
- **Output**: `results/` CSVs and plots.

### Phase 4: Validation & Documentation
*Goal: Verify correctness and finalize reports.*
- **US-1, AC2**: Verify FPR ≤ 2% for non-members via Cross-Implementation Consistency (not circular theoretical check).
- **US-1, AC3**: Verify consistency across implementations.
- **SC-003, SC-004**: Confirm p-values and coefficient of variation.
- **Output**: `quickstart.md`, final `paper/` draft (if applicable).

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Dataset download fails | N/A (Synthetic data generated locally). |
| Memory overflow (>7GB) | Enforce strict dataset sampling; monitor memory usage per run; fail gracefully if limit exceeded. |
| High variance (>20% CV) | Increase repetitions to a sufficient number to ensure statistical robustness.; log variance metrics; report "Inconclusive" for small effects. |
| Hash collision false positives | Use deterministic MurmurHash3; verify observed FPR via Cross-Implementation Consistency. |
| 6-hour timeout exceeded | **Phased Execution**: Run small sizes first. **Hard Stop**: If [deferred] budget consumed by large sizes, truncate remaining large-size runs to ensure full matrix of smaller sizes completes. |
| KS-test validation deadlock | **Retry Limit**: A limited number of attempts. If failed, proceed with best-fit parameters and log "degraded" status. |

## Requirement Exception Log

| Spec ID | Requirement | Exception Reason | Mitigation Strategy |
|---------|-------------|------------------|---------------------|
| FR-008 | Sample Enron/Google | Not in Verified Datasets block; cannot invent URLs. | Use Synthetic Data Modeled on Distributions (validated via KS-test). |
| US-2 | Benchmark on Enron/Google | Same as above. | Benchmark on Synthetic Proxy; report statistical equivalence. |
| SC-005 | Verify fit for Enron/Google | Same as above. | Verify fit of Synthetic Proxy via KS-test against target distribution parameters. |