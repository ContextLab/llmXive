# Implementation Plan: Residue Distribution of Euler's Totient Function Modulo Small Primes

**Branch**: `001-residue-distribution-totient` | **Date**: 2026-07-04 | **Spec**: `specs/001-residue-distribution-totient/spec.md`
**Input**: Feature specification from `/specs/001-residue-distribution-totient/spec.md`

## Summary

This feature implements an empirical investigation into the *rate of convergence* and *deviation magnitude* of Euler's totient function residues $\phi(n) \pmod p$ for small primes $p \in \{5, 7, 11\}$ and other small primes over a large range $n \in [1, N]$. The technical approach involves a linear sieve algorithm implemented in Python with arbitrary-precision integer arithmetic (Constitution Principle VI) to generate residue counts. 

Crucially, the statistical analysis **does not** test a naive uniformity hypothesis (which is a known theorem). Instead, it compares observed deviations against the **theoretical asymptotic distribution with specific error bounds** (Lebowitz-Lockard 2021; Pollack & Roy 2024). To address the dependence structure of the $\phi(n)$ sequence, the plan employs a **Block Bootstrap** procedure to estimate the null distribution of test statistics, ensuring valid p-values for the dependent data. The primary metric is the "error term residual" (ratio of observed deviation to predicted error bound).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy` (array operations), `scipy` (statistics), `matplotlib` (visualization), `pytest` (testing), `psutil` (memory monitoring).  
**Storage**: Local file system (`data/` for computed residues, `results/` for plots/reports). No external database.  
**Testing**: `pytest` with unit tests for sieve correctness and integration tests for statistical pipeline.  
**Target Platform**: GitHub Actions free-tier runner (Linux, 2 CPU, ~7 GB RAM, no GPU).  
**Project Type**: CLI/Computational Research Tool.  
**Performance Goals**: Complete computation for $N=5,000,000$ within 1 hour; peak memory < 6 GB (% of 7 GB limit).  
**Constraints**: Strict adherence to arbitrary-precision arithmetic; no GPU usage; deterministic execution (random seeds pinned).  
**Scale/Scope**: Processing $N$ up to several million integers; supporting specific prime moduli.

> Domain-specific empirical specifics (exact counts, dataset sizes, measured quantities) are deferred to the research/implementation phase. For any quantity stated here, cite its source/reference rather than asserting a measured value.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Implementation Strategy |
|-----------|--------|-------------------------|
| **I. Reproducibility** | PASS | All random seeds pinned in `code/`; `requirements.txt` pins versions; `data/` files checksummed. |
| **II. Verified Accuracy** | PASS | Citations (Lebowitz-Lockard 2021, Pollack & Roy 2024) will be validated by Reference-Validator before use in reports. |
| **III. Data Hygiene** | PASS | Raw sieve output saved as immutable files; checksums recorded in state YAML; no in-place modification. |
| **IV. Single Source of Truth** | PASS | All statistics in reports derived programmatically from `data/` files via `code/` scripts. |
| **V. Versioning Discipline** | PASS | Content hashes tracked; state file updated on artifact changes. |
| **VI. Deterministic Arithmetic Integrity** | PASS | **Critical**: Python's native `int` (arbitrary precision) used for all $\phi(n)$ calculations; no floating-point intermediates in residue logic. |
| **VII. Empirical Statistical Rigor** | PASS | Test thresholds fixed; **Block Bootstrap** implemented to handle sequence dependence; deviation magnitude measured against theoretical error bounds $O(N^{1-\delta})$ to avoid circular uniformity testing. |

## Project Structure

### Documentation (this feature)

```text
specs/001-residue-distribution-totient/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output (generated later)
```

### Source Code (repository root)

```text
projects/PROJ-771-residue-distribution-of-euler-s-totient-/
├── code/
│   ├── __init__.py
│   ├── sieve.py                 # Linear sieve implementation (FR-001)
│   ├── stats.py                 # Block Bootstrap & Deviation Logic (FR-003)
│   ├── visualize.py             # Plot generation (FR-005)
│   ├── run_analysis.py          # Main orchestrator
│   └── requirements.txt         # Pinned dependencies
├── data/
│   ├── raw/
│   │   └── residues_{prime}_{N}.json  # Computed residue counts (ResidueDataset schema)
│   └── processed/
│       └── stats_{prime}_{N}.json     # Statistical test results (StatisticalResult schema)
├── results/
│   ├── plots/                   # PNG/SVG artifacts
│   └── reports/                 # Summary JSON/Markdown
├── tests/
│   ├── unit/
│   │   ├── test_sieve.py
│   │   └── test_stats.py
│   └── integration/
│       └── test_pipeline.py
└── state/
    └── projects/PROJ-771-residue-distribution-of-euler-s-totient-.yaml
```

**Structure Decision**: Single project structure selected. The workflow is linear (Sieve -> Stats -> Visualize), making a monolithic `code/` directory with modular scripts more maintainable than a microservices approach. `data/` is strictly separated into `raw` (immutable sieve output) and `processed` (derived stats) to satisfy Constitution Principle III. The JSON files in `data/` are the **direct serialized forms** of the `ResidueDataset` and `StatisticalResult` entities defined in `data-model.md` and validated against `contracts/*.schema.yaml`.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Arbitrary Precision** | Required by Constitution Principle VI to prevent overflow in $\phi(n)$ for large $N$. | 64-bit integers are insufficient for $\phi(n)$ bit-growth over "several million" integers; using `float` would violate arithmetic integrity. |
| **Block Bootstrap** | Required to handle the dependence structure of $\phi(n)$ and estimate valid p-values (Methodology Concern). | Standard $\chi^2$ p-values are invalid for dependent sequences; Monte Carlo simulation of uniform data is circular and does not reflect the actual data generation process. |
| **Memory Monitoring** | Required by FR-007 to prevent CI failure. | Standard Python scripts do not self-limit memory; `psutil` integration is necessary to enforce the 7 GB hard limit. |

## Resource Guard Logic (FR-007)

To satisfy FR-007, the `run_analysis.py` orchestrator will implement a `MemoryGuard` class:
1.  **Polling**: `psutil` will poll memory usage at regular intervals during the sieve loop (or every [deferred] of N, whichever is larger).
2.  **Threshold**: If `peak_memory_mb` exceeds a substantial majority of the system limit, the process will raise a `MemoryLimitExceeded` exception.
3.  **Graceful Failure**: The exception will trigger a cleanup routine, saving the current partial state (if any) to a temporary file and logging the specific $n$ where the limit was reached, preventing silent data corruption or CI crash.
4.  **Reporting**: The `ExecutionMetadata` in the output JSON will include the `peak_memory_mb` and `limit_reached` flag.

## Statistical Methodology (FR-003, FR-004)

The plan implements the following statistical pipeline to address the dependence structure and theoretical bounds:
1.  **Data Generation**: Compute $\phi(n) \pmod p$ for $n \in [1, N]$.
2.  **Deviation Calculation**: Compute $D = \max_k |O_k - E_k^{theo}|$, where $E_k^{theo}$ is the theoretical expectation with error term correction.
3.  **Null Distribution Estimation**: Use **Block Bootstrap** to resample contiguous blocks of the residue sequence to generate a null distribution of $D$.
    - **Procedure**: Divide the sequence into $B$ contiguous blocks of size $L$. Resample these blocks with replacement to create $M$ synthetic datasets. Compute $D$ for each.
    - **Fallback for Small $N$**: If $N$ is too small to form valid blocks (e.g., $N < 100$), the system will report the raw deviation magnitude $D$ without a p-value and flag the limitation.
    - **No Circular Simulation**: No Monte Carlo simulation of uniform data will be performed.
4.  **Hypothesis Testing**: The p-value is the proportion of bootstrap samples where $D_{boot} \ge D_{obs}$.
5.  **Multiple Testing**: A Bonferroni correction ($\alpha_{adj} = 0.05/4$) will be noted in the report, though the primary analysis uses $\alpha=0.05$.
