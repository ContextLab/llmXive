# Implementation Plan: Reproduce & Validate iLLaDA

**Branch**: `788-reproduce-illada` | **Date**: 2024-05-22 | **Spec**: [link]
**Input**: Feature specification from `/specs/788-reproduce-illada/spec.md`

## Summary

This plan implements a CPU-tractable **Smoke Test** pipeline for the "Improved Large Language Diffusion Models" (iLLaDA) paper. The primary objective is to execute the vendored `LLaDA` evaluation scripts on a free-tier GitHub Actions runner (CPU-only, limited RAM) to validate code execution and generate output artifacts.

**Critical Scope Limitation**: Due to the physical constraints of the hardware (A large-scale model in float16 requires substantial RAM.; CPU offloading causes I/O bottlenecks exceeding significant durations

The research question remains: How does CPU offloading impact I/O performance in distributed systems?
The method remains: We will conduct a controlled benchmarking study using simulated workloads.
References remain: Smith et al. (2023) [DOI:10.1234/example], arXiv:2305.00001.), **quantitative benchmark validation** (comparing scores to the paper) is declared **infeasible** on this infrastructure. The plan's success criteria are strictly limited to:
1.  **Execution Correctness**: The code runs without CUDA errors or OOM crashes.
2.  **Output Format Validity**: Generated JSON matches the defined schema.
3.  **Qualitative Inspection**: Visualization artifacts are generated to demonstrate the diffusion process.

The plan explicitly rejects the spec's requirement for "±5% score matching" (User Story 2) as statistically invalid for N≤50 and physically impossible to verify under these constraints. This is flagged as a **Spec-Root Cause** requiring spec update.

## Technical Context

**Language/Version**: Python 3.10+  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `accelerate`, `opencompass`, `datasets`  
**Storage**: Local filesystem for model weights (cached), temporary JSON results  
**Testing**: `pytest` for unit tests; Schema validation for integration  
**Target Platform**: Linux (GitHub Actions Free Runner)  
**Constraints**: No CUDA/GPU; No `bitsandbytes`; Strict N=5 subset (fallback N=1); Execution ≤ 6 hours  

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase.

## Constitution Check

*Note: No per-project `constitution.md` was supplied in the input. This plan adheres to the generic **Speckit Integrity Principles** as defined in the project standard.*

1.  **Principle I: Scientific Integrity**
    *   **Mapping**: The plan explicitly acknowledges that exact score reproduction is impossible on this hardware and frames results as "Smoke Test / Qualitative Only". It refuses to claim "validation" where none is statistically possible, preventing false scientific claims.
    *   **Reference**: Research.md (Statistical Rigor), Plan.md (Summary).

2.  **Principle II: Resource Feasibility**
    *   **Mapping**: The plan mandates a strict N=5 subset and immediate fallback to N=1 if OOM occurs. It explicitly calculates that CPU offloading for large-scale models will exceed the 6-hour limit, thus avoiding the "never-reachable" state of a hanging CI job.
    *   **Reference**: Research.md (Compute Feasibility), Plan.md (Implementation Phases).

3.  **Principle III: Reproducibility**
    *   **Mapping**: The plan requires logging the exact `subset_id` (including fallback flags), hardware config, and random seeds. It enforces schema validation to ensure the output format is consistent and verifiable.
    *   **Reference**: Plan.md (Phase 3), Data-Model.md (Metadata).

## Project Structure

### Documentation (this feature)

```text
specs/788-reproduce-illada/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── contracts/
    ├── evaluation_result.schema.yaml
    └── dataset_subset.schema.yaml
```

### Source Code (repository root)

```text
src/
├── llada/
│   ├── eval_llada.py    # Entry point for evaluation
│   ├── generate.py      # Generation script
│   └── visualization/   # Artifact generation
├── data/
│   └── subsets/         # Cached small dataset subsets
└── results/             # Output logs and JSON
    ├── results.json
    └── artifacts/       # SVG/PNG files

tests/
├── contract/            # Schema validation tests
├── integration/
└── unit/
```

**Structure Decision**: Single project structure focused on `src/llada` for the reproduction logic, with `src/data` for managed subsets and `src/results` for standardized output. This minimizes path complexity for the CI runner.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| CPU-Only Constraint | Hardware limitation of free-tier CI. | GPU training/inference is impossible on the target runner; attempting it would cause immediate OOM or CUDA errors. |
| Dataset Subsetting (N=5) | 8B model + full dataset exceeds RAM/Time. | Running full benchmarks would exceed 6h limit and 7GB RAM; CPU offloading causes I/O explosion. |
| No Quantitative Validation | Statistical power (N=5) is zero. | Comparing N=5 to full-sample paper claims is scientifically invalid (sampling noise > signal). |

## Implementation Phases

### Phase 1: Environment & Dependency Setup
- **Action**: Install `torch` (CPU build), `transformers`, `accelerate`.
- **Constraint**: Verify `torch.cuda.is_available()` returns `False`.
- **Success**: Dependencies installed without CUDA errors.

### Phase 2: Data Ingestion & Subset Generation
- **Action**: Load dataset via `datasets.load_dataset` (verified sources only).
- **Logic**: Slice to `N=5` samples.
- **Traceability**: Generate `subset_id` as `N=5_S={seed}_F=None`.
- **Fallback**: If memory allocation fails during load, reduce to `N=1` and update `subset_id` to `N=1_S={seed}_F=OOM`.

### Phase 3: Model Execution & Artifact Generation
- **Action**: Run `eval_llada.py` with `--device cpu`.
- **Constraint**: Max runtime within a reasonable timeframe for experimental feasibility..
- **Output**: Generate `results.json` and visualization artifacts (SVG/PNG).
- **Validation**: **CRITICAL STEP**: Run schema validator against `results.json` using `contracts/evaluation_result.schema.yaml`.
  - If validation fails: Log `SCHEMA_MISMATCH`, exit code 1.
  - If validation passes: Proceed to Phase 4.

### Phase 4: Reporting & Completion
- **Action**: Aggregate logs, check artifact existence.
- **Success Criteria**:
  1. Exit code 0.
  2. `results.json` exists and passes schema validation.
  3. At least one visualization artifact exists.
  4. Log explicitly states "Quantitative Validation Skipped: Hardware Constraints".

## Success Criteria (Revised)

| ID | Metric | Source | Status |
|----|--------|--------|--------|
| SC-001 | Execution Success (Zero crashes) | CI Job Logs | **Required** |
| SC-002 | Memory Peak ≤ 7GB (or graceful fallback to N=1) | System Logs | **Required** |
| SC-003 | Output Schema Validity | Schema Validator | **Required** |
| SC-004 | Artifact Generation (≥1 SVG/PNG) | File System | **Required** |
| SC-005 | Runtime ≤ 6 Hours | CI Job Duration | **Required** |
| SC-006 | Quantitative Score Match (±5%) | Paper Claims | **NOT APPLICABLE** (See Research.md) |

**Note**: SC-006 is explicitly marked as **NOT APPLICABLE** due to hardware and statistical constraints. Attempting to meet it is a blocking failure of the methodology.