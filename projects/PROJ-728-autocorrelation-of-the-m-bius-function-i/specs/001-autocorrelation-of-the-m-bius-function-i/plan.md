# Implementation Plan: Autocorrelation of the Möbius Function in Short Intervals

**Branch**: `001-autocorrelation-mobius` | **Date**: 2026-06-17 | **Spec**: `spec.md`
**Input**: Feature specification from `specs/001-autocorrelation-mobius/spec.md`

## Summary

This project implements a computational verification of Chowla's conjecture by computing the normalized autocorrelation of the Möbius function $\mu(n)$ over short intervals ($L \in \{10^3, 10^4, 10^5\}$) up to $N=10^7$. The technical approach involves: (1) a linear-time sieve to generate $\mu(n)$ exactly; (2) sliding-window autocorrelation computation; (3) a **block-permutation** statistical significance test to generate null distributions that preserve local structure while randomizing long-range order; and (4) visualization of results against **two distinct baselines**: (a) the permutation-derived confidence bands (testing the random-sign heuristic) and (b) a **theoretical variance benchmark** derived from the Prime Number Theorem (PNT) (testing arithmetic consistency). The implementation is CPU-first, relying on `numpy` for vectorized arithmetic and `scipy` for statistical testing, ensuring execution within the GitHub Actions free-tier limits (2 CPU, ~7 GB RAM, ≤6h).

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `numpy` (vectorized array ops), `scipy` (statistics, KS test), `matplotlib` (visualization), `pandas` (data I/O for `autocorrelation_stats.csv`), `pytest` (testing).  
**Storage**: In-memory arrays (byte-dtype for $\mu$), CSV for statistical outputs, PNG for visualizations, JSON for validation metrics.  
**Testing**: `pytest` (unit tests for sieve, autocorrelation math; integration tests for pipeline).  
**Target Platform**: Linux (GitHub Actions runner).  
**Project Type**: Computational research script / CLI.  
**Performance Goals**: Full pipeline (Sieve $N=10^7$, Correlation, 1,000 block-permutations, Viz) ≤ 6 hours; Peak RAM < 7 GB.  
**Constraints**: Must use exact integer arithmetic for the sieve and summation; block-permutation must preserve zero-density and local structure; no GPU required (CPU-tractable).  
**Scale/Scope**: $N=10^7$ integers (10 MB array), ~100 randomized intervals per length, 1,000 block-permutations per interval.

> **Dataset-variable fit**: The "dataset" is the deterministic sequence $\mu(n)$ for $n \in [1, 10^7]$. No external data is required. The plan generates this data internally, satisfying the requirement for a "verified dataset" by construction (the sieve is the generator).

## Constitution Check

*GATE: Must pass before Phase 0 research.*

| Principle | Compliance Status | Implementation Detail |
| :--- | :--- | :--- |
| **I. Reproducibility** | ✅ Compliant | Random seeds pinned in `code/`. Deterministic sieve. `requirements.txt` pins versions. |
| **II. Verified Accuracy** | ✅ Compliant | Chowla's conjecture and the Prime Number Theorem (PNT) serve as the theoretical baselines. The plan explicitly separates the "random-sign heuristic" test (permutation) from the "arithmetic consistency" test (PNT variance), ensuring alignment with Principle II by using verified mathematical theorems as reference sources. |
| **III. Data Hygiene** | ✅ Compliant | Generated $\mu$ array is treated as "raw data" (checksummed in state). No in-place modification. |
| **IV. Single Source of Truth** | ✅ Compliant | All stats/figures trace to `data/raw/mobius.npy` and `code/`. |
| **V. Versioning** | ✅ Compliant | Content hashes tracked in state file. |
| **VI. Deterministic Arithmetic** | ✅ Compliant | Sieve uses integer logic. Autocorrelation **sums** use `int64` accumulation to prevent float errors before normalization. The **final normalized metric** is stored as `float64`, satisfying the mandate that the sum is exact while the metric is a ratio. |
| **VII. Statistical Null Validation** | ✅ Compliant | Plan mandates exactly 1,000 **block-permutations** per window, preserving zero-density and local structure. P-values are derived from this envelope. Crucially, the plan adds a **Theoretical Variance Benchmark** (PNT) to avoid circular reasoning in interpreting uniformity, distinguishing "random fluctuation" from "arithmetic structure". |

## Project Structure

### Documentation (this feature)

```text
specs/001-autocorrelation-mobius/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-728-autocorrelation-of-the-mobius-function-i/
├── code/
│   ├── __init__.py
│   ├── sieve.py                 # Linear sieve for Möbius function
│   ├── autocorrelation.py       # Sliding window correlation logic
│   ├── permutation.py           # Block-permutation null distribution generation
│   ├── viz.py                   # Heatmap and confidence band plotting
│   └── main.py                  # Pipeline orchestration
├── data/
│   ├── raw/
│   │   └── mobius_array.npy     # Generated $\mu(n)$ for $1..10^7$
│   └── processed/
│       ├── autocorrelation_stats.csv
│       ├── p_values.csv
│       └── uniformity_test.json # SC-005 validation output
├── outputs/
│   └── figures/
│       ├── heatmap_L1000.png
│       ├── heatmap_L10000.png
│       └── heatmap_L100000.png
├── tests/
│   ├── unit/
│   │   ├── test_sieve.py
│   │   └── test_autocorrelation.py
│   └── integration/
│       └── test_pipeline.py
├── requirements.txt
└── pyproject.toml
```

**Structure Decision**: Single project structure. The logic is linear (Sieve -> Correlation -> Permutation -> Viz) and fits comfortably in a single `code/` directory without needing microservices or complex frontend/backend splits.

## Complexity Tracking

No violations found. The complexity is managed by:
1.  **Memory**: Storing $\mu$ as a compact integer type keeps $10^7$ elements at ~10 MB, well below 7 GB.
2.  **Compute**: Block-permutations are parallelizable (per interval) but run sequentially in the plan to ensure memory safety; 1,000 permutations of $L=10^5$ with block size 100 is computationally cheap on CPU.
3.  **Statistical Rigor**: The plan explicitly handles the "zero-density" constraint, **block-permutation** to preserve local structure, **theoretical variance benchmark** (PNT), and multiple-comparison correction (via Benjamini-Hochberg and KS test) to satisfy SC-005.

## Implementation Phases

### Phase 1: Data Generation & Preprocessing

**Task 1.1: Generate Möbius Sequence with Randomized Sampling**
- Implement linear sieve in `code/sieve.py` to generate $\mu(n)$ for $1 \le n \le 10^7$.
- Store as `int8` array in `data/raw/mobius_array.npy`.
- **Sampling Strategy**: Instead of fixed stride, implement **Randomized Stratified Sampling**. Select $M=100$ window start positions per length $L$ using a fixed random seed, ensuring uniform coverage across $[1, N-L]$ to avoid periodic bias with prime gaps.
- *Deliverable*: `data/raw/mobius_array.npy` and a list of sampled window indices.

**Task 1.2: Edge Case Handling**
- Implement logic to detect windows where all $\mu(n) = 0$ (or near-zero density).
- If detected, skip the permutation test for that window and record a `warning_flag` in the output CSV.
- *Deliverable*: Updated `code/autocorrelation.py` with edge case guards.

### Phase 2: Statistical Analysis

**Task 2.1: Compute Autocorrelation**
- Compute normalized autocorrelation $r_{k, L}(h)$ for all lags $h \in \{1, \dots, \lfloor L/2 \rfloor\}$ for each sampled window.
- Use `int64` for summation to ensure exact arithmetic, then cast to `float64` for normalization.
- *Deliverable*: Intermediate array of observed correlations.

**Task 2.2: Theoretical Variance Benchmark (PNT Baseline)**
- **Action**: Compute the theoretical variance of the autocorrelation sum under the Prime Number Theorem (PNT) assumption.
- **Method**: Under the assumption that $\mu(n)$ behaves like a random variable with $P(\mu=0) = 1 - 6/\pi^2$ and $P(\mu=\pm 1) = 3/\pi^2$, the expected variance of the sum is derived analytically ($Var \approx \sigma^2 / L$).
- **Purpose**: This provides a non-circular arithmetic baseline. We compare the observed variance against this theoretical value to distinguish "random fluctuation" (consistent with PNT) from "arithmetic structure" (deviation from PNT).
- *Deliverable*: A column `theoretical_variance` in the output CSV and a comparison metric.

**Task 2.3: Block-Permutation Null Distribution**
- Implement **Block-Permutation** in `code/permutation.py`.
- **Method**: Divide the window of length $L$ into $B$ blocks (e.g., block size $b=100$). Shuffle the order of these blocks while preserving the content of each block (local structure).
- Generate [deferred] such permuted sequences per window, preserving the global zero-count.
- Compute autocorrelation for each permuted sequence.
- **Purpose**: Tests the "random-sign heuristic" (is $\mu$ indistinguishable from a shuffled version of itself?).
- *Deliverable*: Null distribution of [deferred] values per (window, lag).

**Task 2.4: Multiple Comparison Correction**
- Apply the **Benjamini-Hochberg (BH)** procedure to control the False Discovery Rate (FDR) across all tested lags and intervals.
- Calculate adjusted p-values.
- *Deliverable*: `adjusted_p_value` column in output CSV.

**Task 2.5: Output Generation**
- Use `pandas` to write `data/processed/autocorrelation_stats.csv` with columns: `interval_start`, `interval_length`, `lag`, `autocorrelation`, `p_value`, `adjusted_p_value`, `ci_lower`, `ci_upper`, `zero_count`, `sensitivity_flag`, `theoretical_variance`.
- *Deliverable*: Final CSV file.

### Phase 3: Sensitivity Analysis

**Task 3.1: Zero-Density Sensitivity**
- Re-run the permutation test (Task 2.3) with zero-counts adjusted by ±5% and ±10% of the observed count.
- Compare the resulting p-values with the original.
- *Deliverable*: `sensitivity_flag` ("stable", "sensitive", "not_applicable") in the output CSV.

### Phase 4: Visualization & Validation

**Task 4.1: Heatmap Generation**
- Generate heatmaps for each $L$ showing autocorrelation values, overlaying:
  1. The theoretical zero line.
  2. The 95% confidence envelope from the **block-permutation null** (random-sign heuristic test).
  3. A visual indicator for deviations from the **theoretical variance benchmark** (PNT test).
- *Deliverable*: PNG files in `outputs/figures/`.

**Task 4.2: Uniformity Validation (SC-005)**
- Perform a **Kolmogorov-Smirnov (KS) test** on the distribution of p-values.
- **Interpretation Update**: If the null holds (Möbius is random), p-values are uniform. If non-uniform, it indicates $\mu$ is distinguishable from its shuffled version. This is reported as evidence *for or against* the random-sign heuristic, not a direct proof of Chowla's Conjecture.
- Save the KS statistic and p-value to `data/processed/uniformity_test.json`.
- *Deliverable*: `uniformity_test.json` file.

## Compute Feasibility & Rationale

**Decision**: CPU-first execution.

**Rationale**:
1.  **Sieve**: $O(N)$ integer operations. $10^7$ ops is ~0.1s on modern CPU.
2.  **Autocorrelation**: Optimized via sliding window. With $L=10^5$, $N=10^7$, and 100 sampled windows, this is feasible.
3.  **Block-Permutation**: 1,000 permutations of length $10^5$ with block size 100. $10^3 \times 100$ shuffles per window. For 100 windows, this is well within the 6h limit.
4.  **GPU**: Not required. No matrix multiplication or deep learning models are involved.

**Feasibility Check**:
- **RAM**: $10^7$ `int8` = 10 MB. Intermediate arrays for permutation = 100 MB max. **Safe** (< 7 GB).
- **Disk**: Output CSVs, PNGs, and JSON < 50 MB. **Safe** (< 14 GB).
- **Time**: Estimated total runtime < 4 hours. **Safe** (< 6h).

## Limitations & Assumptions

- **Observational Nature**: The study is computational, not experimental. We cannot "randomize" the Möbius function; we can only test if its structure *resembles* a random process.
- **Window Selection**: We use **Randomized Stratified Sampling** to avoid periodic bias. We cannot test *every* possible window of length $L$ in $N=10^7$ due to time constraints.
- **Zero-Density**: The permutation test assumes the observed zero-density is the true parameter. The sensitivity analysis (FR-007) addresses uncertainty in this parameter.
- **Theoretical Variance**: The theoretical variance benchmark assumes the Prime Number Theorem holds. Deviations from this benchmark may indicate arithmetic structure.
- **Interpretation of Uniformity**: Uniform p-values indicate the data is indistinguishable from a shuffled version (validating the heuristic), not that Chowla's Conjecture is proven. Non-uniform p-values indicate a violation of the heuristic.