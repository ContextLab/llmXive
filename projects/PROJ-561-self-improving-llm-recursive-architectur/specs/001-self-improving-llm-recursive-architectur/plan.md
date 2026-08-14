# Implementation Plan: Self-improving LLM: recursive architecture refinement and re‑training

**Branch**: `001-self-improving-llm-recursive-architectur` | **Date**: 2026-06-16
**Spec**: `projects/PROJ-561-self-improving-llm-recursive-architectur/specs/001-self-improving-llm-recursive-architectur/spec.md`
**Input**: Feature specification from `/specs/001-self-improving-llm-recursive-architectur/spec.md`

## Summary

This project implements a recursive pipeline where a GPT-2 124M model proposes architectural modifications, an external oracle validates them, and the model is re-trained on a subset of OpenWebText. The system executes up to three cycles, evaluating performance on GSMK, ARC-Challenge, and BoolQ benchmarks. The plan ensures strict adherence to the project constitution, particularly regarding reproducibility, data hygiene, and the separation of generative (modification proposal) and verification (evaluation) logic to prevent infinite regression. The implementation prioritizes CPU feasibility on GitHub Actions free-tier runners, utilizing streaming data access and a fallback strategy to reduce training subset size if time constraints are threatened.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `torch` (CPU backend), `transformers`, `datasets`, `scikit-learn`, `pandas`, `psutil`, `pyyaml`
**Storage**: Local filesystem (`data/raw`, `data/processed`, `results`)
**Testing**: `pytest` (unit tests for schema, config, and pipeline logic)
**Target Platform**: GitHub Actions `ubuntu-latest` (Free Tier: 2 CPU, ~7 GB RAM, no GPU)
**Project Type**: Research Pipeline / CLI Tool
**Performance Goals**: Complete 3 cycles within 12 hours; Peak RAM < 7 GB; Disk < 14 GB
**Constraints**: No CUDA operations; Parameter count increase ≤ 30% from baseline; Strict separation of generative and verification logic (Constitution VII).
**Scale/Scope**: refinement cycles; A substantial number of training samples per cycle (fallback to a reduced subset if time-constrained); Multiple benchmarks per cycle.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence / Plan Action |
| :--- | :--- | :--- |
| **I. Reproducibility** | PASS | `requirements.txt` will pin all dependencies. Random seeds will be set in `code/utils/random.py`. External datasets fetched via `datasets` library with verified URLs. |
| **II. Verified Accuracy** | PASS | All dataset URLs in `research.md` are from the verified block. **Runtime Check**: A pre-flight step in `code/utils/data_loader.py` will verify URLs against primary sources before execution. |
| **III. Data Hygiene** | PASS | `code/utils/data_loader.py` will implement checksumming (SHA-256) for all downloaded raw files. Derivations written to new files. |
| **IV. Single Source of Truth** | PASS | All metrics written to `results/trajectory.json` and `results/logs/cycle_N.log`. No hand-typed numbers in reports. |
| **V. Versioning Discipline** | PASS | **Explicit Step**: A 'State File Update' step will hash artifacts and update `state/...yaml` after each cycle. |
| **VI. Performance Metric Attribution** | PASS | Comparison logic explicitly compares pre-modification vs. post-modification states for each cycle. |
| **VII. Data Source Independence** | PASS | **Critical**: The "External Oracle" (FR-021) and "Distinctness Validator" (FR-020) are implemented in `utils/validation.py`, separate from the "Model Proposal" module. Evaluation data is held-out. |

## Project Structure

### Documentation (this feature)

```text
specs/001-self-improving-llm-recursive-architectur/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
code/
├── __init__.py
├── config.py                # FR-004, FR-003, FR-019, FR-020, FR-021, FR-011 (CONFIG ONLY)
├── main.py                  # Entry point, orchestrates cycles
├── utils/
│   ├── __init__.py
│   ├── logging.py           # FR-009, FR-012, JSON logging
│   ├── random.py            # Constitution I: Seed pinning
│   ├── data_loader.py       # Constitution III: Checksums, streaming, URL verification
│   └── validation.py        # FR-021: Oracle logic, FR-020: Distinctness, FR-011: Backoff
├── models/
│   ├── __init__.py
│   ├── loader.py            # FR-001: CPU loading
│   └── modifier.py          # FR-002, FR-019: Apply modification
├── pipeline/
│   ├── __init__.py
│   ├── evaluator.py         # FR-005, FR-006: Benchmarks & Stats
│   ├── trainer.py           # FR-004: Training loop, FLOPs
│   ├── attempt_tracker.py   # FR-012, FR-007: Retry logic (generates log events)
│   └── trajectory.py        # FR-009, FR-010: Regression & Trade-offs
└── tests/
    ├── __init__.py
    ├── unit/
    │   ├── test_config.py
    │   ├── test_schema.py   # T013
    │   ├── test_trainer.py  # T017a, T017b
    │   └── test_attempt_tracker.py # T090
    └── integration/
        └── test_full_pipeline.py

data/
├── raw/                     # Downloaded datasets (checksummed)
└── processed/               # Derived subsets

results/
├── logs/                    # JSON logs per cycle
└── trajectory.json          # Aggregated metrics
```

**Structure Decision**: Single project structure under `code/` to minimize overhead. `config.py` holds parameters only; validation logic (FR-020, FR-021) is in `utils/validation.py` to ensure separation of concerns.

## Project Phases (Explicit Step Mapping)

### Phase 0: Pre-flight & Data Loading
1.  **Step 1.0: Pre-flight URL Verification** (FR-002, Constitution II): Verify all dataset URLs against primary sources before download.
2.  **Step 1.1: API Retry with Backoff** (FR-011): Implement exponential backoff for HuggingFace calls. Max a limited number of retries.
3.  **Step 1.2: Data Download & Checksumming** (Constitution III): Download datasets (OpenWebText, GSM8K, ARC, BoolQ) and record SHA-256 hashes.

### Phase 1: Baseline & Capability Check
1.  **Step 2.0: Model Loading** (FR-001): Load GPT 124M on CPU.
2.  **Step 2.1: Baseline Capability Check** (Scientific Soundness): Evaluate baseline on benchmarks. If performance is near-random (<10% on GSM8K/ARC), flag limitation and proceed with caution or switch to zero-shot baseline.
3.  **Step 2.2: Record Baseline Metrics** (SC-001, SC-002): Store Cycle 0 metrics.

### Phase 2: Refinement Cycle Loop (Repeat up to 3 times)
1.  **Step 3.0: Proposal Generation**: Prompt model for architectural modification.
2.  **Step 3.1: Parameter Constraint Check** (FR-019, FR-003): Validate proposed change does not exceed a moderate parameter increase. Reject if violated.
3.  **Step 3.2: Distinctness Validation** (FR-020, FR-002): Compare proposal against history. Ensure Hamming distance >= 1 or >5% parameter change. Reject if not distinct.
4.  **Step 3.3: External Oracle Check** (FR-021): Validate proposal against fixed heuristics (e.g., parameter efficiency).
5. **Step 3.4: Training** (FR-004): Train for 1 epoch. **Fallback**: If estimated time > 2h, reduce training subset to [deferred] samples.
6.  **Step 3.5: FLOPs Calculation** (FR-008): Use `torch.profiler` to record FLOPs with appropriate precision.
7.  **Step 3.6: Evaluation** (FR-005): Evaluate on GSMK, ARC, and BoolQ

The research question remains: To what extent can the proposed method improve reasoning performance across diverse benchmark tasks?

The method remains: We will employ a zero-shot prompting strategy with chain-of-thought reasoning on standard natural language understanding and reasoning benchmarks.

References:
Clark et al. (2018) [arXiv:1803.05457]
Kwiatkowski et al. (2019) [DOI: 10.1162/tacl_a_00276].
8.  **Step 3.7: Statistical Analysis** (FR-006): Perform paired bootstrap with a sufficient number of resamples and Bonferroni correction. Calculate p-values.
9.  **Step 3.8: Early Termination Check** (FR-015): If degradation >= 5% from baseline, terminate loop.
10. **Step 3.9: State File Update** (Constitution V): Hash artifacts and update `state/...yaml`.

### Phase 3: Trajectory & Trade-off Analysis
1.  **Step 4.1: Linear Regression Fit** (FR-009): Fit linear model to performance data. Report slope, intercept, R2, trend.
2.  **Step 4.2: Trade-off Calculation** (FR-010): Compute performance-per-FLOP and performance-per-hour.
3.  **Step 4.3: Capacity Normalization** (Methodology): Analyze if improvements correlate with parameter count or topology.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| External Oracle (FR-021) | Prevents circular validation where the model validates its own changes. | A simple self-check would allow infinite regression and bias, violating Constitution VII. |
| Attempt Tracker (FR-012) | Handles transient training failures without halting the entire experiment. | A simple retry loop without logging or cycle counting would obscure failure modes and violate FR-007. |
| Streaming Data Loader | Essential for fitting >7GB RAM constraints with large datasets. | Loading full OpenWebText into RAM would crash the GitHub Actions runner. |
| Pre-flight URL Check | Ensures data source stability (Constitution II). | Relying on static URLs without runtime verification risks using stale or moved data. |
| FLOPs Profiler | Required for cost-effectiveness analysis (FR-008). | Estimating FLOPs theoretically ignores hardware-specific overhead and memory access patterns. |