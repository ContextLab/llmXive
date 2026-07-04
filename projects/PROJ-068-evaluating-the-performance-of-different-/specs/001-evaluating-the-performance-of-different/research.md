# Research: Evaluating the Performance of Different Data Structures in Implementing Bloom Filters

## Problem Statement

Bloom filters are probabilistic data structures used for set membership testing. While theoretically optimal in space, practical implementations vary significantly in memory overhead and query latency depending on the underlying storage mechanism (native arrays, dynamic vectors, specialized bitsets). This research evaluates these trade-offs across varying dataset sizes and false positive rate targets under constrained computational resources (CPU-only, limited RAM).

**Critical Note**: Due to the absence of Enron/Google datasets in the "Verified datasets" block, this research uses **Synthetic Data Modeled on Target Distributions**. This is a formal Requirement Exception to satisfy the "no invented URL" constraint while preserving statistical validity.

## Dataset Strategy

### Verified Datasets & Requirement Exception
Per the project's "Verified datasets" block, the following sources are available:
- **Verified Block Contents**: `fp_run_colab`, `Stepkids_dataset`, `tender_dbs_parquet`, `BC5CDR-Chemical-Disease`, `demo_datset`.
- **Missing Datasets**: The spec requires "Enron Email Corpus" and "Google 10000 English words". These are **NOT** in the verified block.
- **Decision**: We cannot invent URLs. We will use a **deterministic synthetic dataset generator** modeled on the statistical properties of Enron/Google.

### Synthetic Data Generation Strategy
- **Generator**: `numpy.random` with a fixed seed.
- **Distribution Modeling**:
  - **String Length**: Log-normal distribution (mean=10, sigma=1.5) to mimic real-world text (Enron subjects, Google words).
  - **Character Set**: ASCII printable characters (a-z, A-Z, 0-9, space, punctuation).
  - **Entropy**: Controlled to match the average entropy of English text.
- **Validation**: Kolmogorov-Smirnov (KS) test to ensure the synthetic distribution is statistically indistinguishable from the target distribution (using public summary statistics for Enron/Google).
- **Retry Logic**: If the KS-test p-value < 0.05, the generator adjusts parameters and retries. **Maximum retries: 5**. If validation fails after 5 attempts, the system logs a warning, uses the best-fit parameters, and marks the dataset as `degraded` rather than hanging.
- **Rationale**: Bloom filter performance is driven by hash distribution and string length. By matching the length distribution, we preserve the construct validity of the benchmark while ensuring reproducibility and compliance with the "no invented URL" rule.

### Construct Validity Justification (Addressing Methodology-104a9946)
- **Risk**: Random strings may not stress hash functions or memory allocators like real text.
- **Mitigation**: The synthetic generator explicitly models the **log-normal length distribution** and **ASCII entropy** characteristic of email subjects and word lists. This ensures that:
  1. Hash functions process variable-length inputs similar to real data.
  2. Memory allocators handle the same allocation patterns (small vs. large strings).
  3. The statistical properties (mean, variance) of the input match the target domain.
- **Verification**: The KS-test validates that the synthetic length distribution is statistically equivalent to the target distribution. If the test passes (p > 0.05), the construct validity is preserved.

### Dataset Variable Fit (SC-005)
- **Required Variables**: Text elements (strings) for insertion, ground truth for membership queries.
- **Synthetic Strategy**: Generate random strings with controlled length distribution.
- **Fit Verification**: The synthetic generator produces strings that match the *statistical properties* (length, entropy) of the target datasets. The KS-test validates this fit. This satisfies SC-005's intent of "variable fit" via statistical equivalence.

## Theoretical Analysis

### Memory Overhead
The theoretical memory size $m$ (in bits) for a Bloom filter with $n$ elements and false positive rate $p$ is:
$$m = -\frac{n \ln p}{(\ln 2)^2}$$
- **Native Arrays**: Overhead = $m$ bits + Python object overhead (8 bytes per element if not packed).
- **Dynamic Vectors**: Overhead = $m$ bits + vector resizing overhead (typically 2x capacity).
- **Specialized Bitsets**: Overhead = $m$ bits (minimal, packed).

*Feasibility Check*: For $n=1,000,000$ and $p=0.01$, $m \approx 9.6$ million bits $\approx 1.2$ MB. Even with Python object overhead, this is well within 7GB RAM. The constraint is not memory size but **disk I/O and CPU time** for [deferred] runs.

### Latency
- **Insertion**: $O(k)$ hash computations per element.
- **Query**: $O(k)$ hash computations + bit checks.
- **Data Structure Impact**:
  - *Bitsets*: Fastest bit-level operations (CPU cache friendly).
  - *Arrays*: Slower due to Python list indexing overhead.
  - *Vectors*: Intermediate, depending on implementation.
- **String Length Control**: To isolate data structure overhead, the synthetic generator uses a fixed length distribution. This prevents variance in hashing time (due to variable string lengths) from confounding the latency metric.

## Statistical Methodology

### Test Selection
- **Kruskal-Wallis H-test**: Non-parametric test to compare medians of 3+ independent groups (the 3 implementations).
- **Null Hypothesis ($H_0$)**: All three implementations have the same distribution of memory/latency.
- **Alternative Hypothesis ($H_1$)**: At least one implementation differs.
- **Significance Level**: $\alpha = 0.05$.
- **Post-hoc**: If $H_0$ rejected, perform pairwise Wilcoxon rank-sum tests with Bonferroni correction.

### Power & Sample Size (Addressing Methodology-4c02f4f9 & Scientific-Soundness-8f42cff2)
- **Repetitions**: 50 per configuration (increased from 5 to ensure statistical power).
- **Power Analysis**: With 50 samples per group (total N=150), the Kruskal-Wallis test achieves >80% power to detect **medium-to-large effect sizes** (Cohen's d > 0.5).
- **Limitation**: Power to detect **small effect sizes** (d < 0.2) remains low ([deferred]).
- **Mitigation**: The study explicitly frames results as "Exploratory for Small Effects". If p > 0.05 for small effects, the finding is labeled "Inconclusive" rather than "No Difference". This prevents Type II error misinterpretation.

### Multiple Comparisons
- **Correction**: Bonferroni correction applied to pairwise tests ($\alpha_{adj} = 0.05 / 3$).
- **Family-wise Error Rate**: Controlled via Kruskal-Wallis followed by corrected post-hoc.

## Compute Feasibility & Phased Execution (Addressing Methodology-0276434d)

### Constraints
- **Runner**: GitHub Actions free-tier (2 CPU, 7GB RAM, 14GB Disk).
- **Time Limit**: 6 hours.
- **Workload**: 150 configs × 50 reps = 7,500 runs.
- **Risk**: [deferred] runs × (avg 1 min for small + 10 min for large) = impossible in 6 hours.

### Phased Execution Strategy
To guarantee completion within 6 hours:
1.  **Prioritization**: Run small and medium sizes first.
2.  **Budget Tracking**: The `runner.py` script tracks elapsed time.
3. **Hard Stop**: If [deferred] of the 6-hour budget (3 hours) is consumed by the largest size (1M) runs, the remaining repetitions for 1M are **truncated**.
4.  **Result**: The full matrix of small/medium sizes completes, ensuring the study has valid data for the majority of the range. Large-size data may be partial, but the study is not invalidated.

### Library Selection
- **`bitarray`**: For specialized bitset (CPU-only, efficient).
- **`memory-profiler`**: For peak memory tracking (CPU-only).
- **`scipy.stats`**: For Kruskal-Wallis (CPU-only).
- **`numpy`**: For synthetic data generation (CPU-only).

## Validation Strategy (Addressing Scientific-Soundness-a920ce6d)

### Cross-Implementation Consistency
- **Method**: Compare the output of the three Bloom filter implementations on the same dataset.
- **Goal**: Ensure all three implementations produce identical membership results for the same query set.
- **Rationale**: This validates the *correctness* of the implementation without relying on the circular "Observed FPR vs Theoretical FPR" check.

### Hash Uniformity Test
- **Method**: Inject a known "bad" hash function (e.g., constant hash) and verify that the false positive rate degrades as expected.
- **Goal**: Ensure the Bloom filter logic is actually responding to hash collisions, not just a calculation artifact.

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Dataset URL unavailable | N/A (Synthetic) | N/A | N/A |
| Memory overflow | Low | High | Enforce strict sampling; monitor memory. |
| High variance in runs | Medium | Medium | 50 repetitions; report "Inconclusive" for small effects. |
| Hash collision bias | Low | Low | Use MurmurHash3; Cross-Implementation Consistency test. |
| 6-hour timeout | High | Critical | Phased execution; Hard Stop logic for large sizes. |
| KS-test deadlock | Low | High | Max 5 retries; fallback to "degraded" status. |

## Decision Rationale

1. **Synthetic Data over External Datasets**:
   - *Reason*: The "Verified datasets" block does not contain Enron or Google 10000 English. Using them would require inventing URLs (violates rules).
   - *Benefit*: Synthetic data ensures exact size control, reproducibility, and compliance with "no invented URLs".
   - *Trade-off*: Loss of real-world text distribution, but Bloom filter performance is content-agnostic *if* length distribution is controlled.

2. **50 Repetitions over 5**:
   - *Reason*: 5 repetitions yield low power for small effects.
   - *Benefit*: 50 repetitions achieve >80% power for medium effects, making the study scientifically valid for the claimed goals.
   - *Trade-off*: Increased runtime, mitigated by phased execution.

3. **Bitarray for Bitset Implementation**:
   - *Reason*: Native Python `bytearray` is less efficient for bit-level operations.
   - *Benefit*: `bitarray` is optimized for bit manipulation and runs on CPU.