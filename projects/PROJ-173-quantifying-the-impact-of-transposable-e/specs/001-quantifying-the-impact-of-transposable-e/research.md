# Research: Quantifying the Impact of Transposable Element Activity on Gene Expression Variation in Drosophila

## Executive Summary

This research phase defines the statistical and data strategy for the project. Given the absence of a verified public dataset containing matched TE-genotype and RNA-seq data for *Drosophila* DGRP lines, the project adopts a **Mock/Synthetic Dataset** strategy (FR-001) to validate the entire analysis pipeline. The core methodology relies on linear models with population structure covariates, Benjamini-Hochberg FDR correction, and Freedman-Lane permutation testing. All methods are selected for CPU-tractability on GitHub Actions free-tier runners.

## Dataset Strategy

### Primary Dataset: Mock/Synthetic Data
**Status**: No verified public source found for matched TE-genotype + RNA-seq in DGRP lines.
**Strategy**: Generate synthetic data that mimics the statistical properties of the DGRP population structure and TE-gene relationships, with explicit decoupling of generation mechanisms to avoid tautological validation.
**Generation Logic**:
1.  **Lines**: Simulate a moderate number of lines.
2.  **Latent Structure**: Generate a latent population structure vector $Z$ (multivariate normal).
3.  **Population Structure (PCs)**: Generate PC1, PC2, PC3 as linear combinations of $Z$ plus small independent noise.
4.  **TE Genotypes**: Generate TE presence as a function of $Z$ (to simulate confounding) plus independent noise, ensuring correlation exists but is not deterministic. **Crucially, this allows the permutation test to validate if the model correctly absorbs the confounding signal.**
5.  **Gene Expression**:
    *   **Signal Subset**: For a known subset of TE-gene pairs, generate expression as `log2_TPM = beta * TE_presence + beta_pc * PC1 + noise`.
    *   **Null Subset**: For the majority of pairs, generate expression as `log2_TPM = beta_pc * PC1 + noise` (no TE effect).
    *   **Pure Confounding Test**: For a specific subset, generate expression as `log2_TPM = beta_pc * PC1 + noise` where TE is correlated with PC but has **zero** true effect. This allows the pipeline to return a "null" result, proving the control efficacy is not tautological.
6.  **Coordinates**: Simulate genomic coordinates based on Drosophila Release 6 gene models to define proximal windows (≤5 kb).
7.  **TE-Aware Flag**: The generator sets `quantification_method: "TEaware"` in the output metadata to satisfy Principle VII.

**Source Reference**: No external URL cited. Generation logic is defined in `code/data_generator.py`.

### Secondary Dataset: Independent Replication (Mock)
**Status**: No verified public source found.
**Strategy**: Generate a second independent mock dataset with different random seeds.
**Scenario A (Signal Replication)**: Same signal logic as primary. Used to test power and concordance rate against the *expected* concordance rate (calculated from power).
**Scenario B (Null Replication)**: No signal injected. Used to test the binomial test against the null of 0.5 (random concordance).
**Purpose**: Validate the replication pipeline (US-2) and binomial concordance test (FR-016) under both conditions.

## Statistical Methodology

### 1. Association Analysis (FR-004, FR-005)
- **Model**: `gene_expression ~ TE_presence + PC1 + PC2 + PC3`
- **Estimator**: Ordinary Least Squares (OLS) via `statsmodels`.
- **Effect Size**: Coefficient of `TE_presence` (log2-fold change).
- **Confidence Interval**:
  1.  Perform **Shapiro-Wilk test** on residuals.
  2.  If $p \ge 0.05$: Use a Wald CI (assuming normality).
  3.  If $p < 0.05$: Use **Bootstrap CI** (1000 resamples, percentile method).
- **Multiple Testing**: Benjamini-Hochberg (BH) correction across all tested pairs. Threshold: adj_p < 0.05.
- **Handling Missing Data**: Exclude lines with missing expression for specific genes (FR-009).

### 2. Collinearity Diagnostics (FR-007, SC-006)
- **Metric**: Variance Inflation Factor (VIF) for `TE_presence` in the presence of PCs.
- **Threshold**: VIF > 5.
- **Action**: Flag with `vif_flag = true`. Exclude from causal claims; report as associational only.

### 3. Monomorphic Filtering (FR-008)
- **Filter**: Exclude TEs with presence frequency < 5% or > 95%.
- **Rationale**: Monomorphic variants have no variance to explain expression differences; power is zero.

### 4. Ambiguous TE-Gene Assignment (FR-011)
- **Logic**: If a TE coordinate overlaps multiple gene transcription start/end regions within the proximal window.
- **Action**: Flag with `ambiguous_flag = true`. Exclude from primary testing.

### 5. Permutation Testing (FR-006, SC-005)
- **Method**: Freedman-Lane (residual permutation).
  1. Fit null model: `gene_expression ~ PC1 + PC2 + PC3`.
  2. Extract residuals.
  3. Shuffle residuals.
  4. Create permuted response: `fitted_null + shuffled_residuals`.
  5. Refit full model: `permuted_response ~ TE_presence + PC1 + PC2 + PC3`.
  6. Record raw t-statistic for `TE_presence`.
- **Iterations**: 1000 (target).
- **Null Distribution**: Array of raw t-statistics.
- **Validation Goal**: **Pipeline Logic & Estimator Consistency**.
  *   For **Signal Pairs**: Verify observed t-statistic exceeds 95th percentile of null (confirms estimator recovers signal).
  *   For **Null Pairs**: Verify observed t-statistic does *not* exceed 95th percentile (confirms no false positives).
  *   For **Pure Confounding Pairs**: Verify model correctly estimates null effect (confirms PC control efficacy is not tautological).
- **Timeout Handling**:
  1.  **Benchmark**: Before full run, estimate time per fit on 10 pairs.
  2.  **Projection**: If `projected_time > 4.5 hours`, reduce iterations to 100 (or 500 if time permits).
  3.  **Output**: Report `iterations_completed` and note reduction in metadata.

### 6. Replication Analysis (US-2, FR-010, FR-016)
- **Input**: Significant pairs from Primary Analysis.
- **Test**: Binomial test.
  *   **Scenario A (Signal)**: Null hypothesis = Expected concordance rate (calculated from power).
  *   **Scenario B (Null)**: Null hypothesis = 0.5 (random chance).
- **Output**: Concordance rate, binomial p-value, and scenario label.

## Compute Feasibility & Resource Planning

**Target Environment**: GitHub Actions Free Tier (multi-core CPU, standard RAM allocation, 6h limit).

| Task | Estimated Resource Usage | Mitigation Strategy |
| :--- | :--- | :--- |
| **Data Generation** | < 1 min, < 100 MB | Pure Python/Numpy. No external I/O. |
| **Linear Model Fitting** | ~1-2 min for 5000 pairs | `statsmodels` is CPU efficient. Vectorized operations where possible. |
| **VIF Calculation** | < 1 min | Matrix inversion on small design matrices (4x4). |
| **Permutation (1000 iters)** | **Variable** (1-4 hours estimated) | **Critical**: Implement **Benchmark Step** to measure per-fit time. If projected time > 4.5h, dynamically reduce iterations to 100 or 500. |
| **Memory** | < 4 GB | Keep data in memory as Pandas DataFrames. Sample genes/TEs if necessary to stay under 7 GB. |
| **Disk** | < 1 GB | Output CSVs/Parquet. No large intermediate files. |

**Risk**: Permutation testing may exceed 6 hours on 2 cores.
**Mitigation**:
1.  **Benchmark**: Measure time for 10 iterations at start.
2.  **Dynamic Reduction**: If `time_per_iter * 1000 > 4.5h`, set `n_permutations = 100` (or 500).
3.  **Progress Tracking**: Save intermediate results every 100 iterations.
4.  **Documentation**: Log the reduction in `output.schema.yaml` metadata.

## Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use Mock Data** | No verified public dataset exists (per "Verified datasets" block). Spec requires testing the pipeline logic (US-1). |
| **Freedman-Lane Permutation** | Required to preserve LD structure between TE and PCs. Simple shuffling is invalid. |
| **VIF Threshold = 5** | Standard threshold for "high collinearity" in regression diagnostics. |
| **BH Correction** | Standard for FDR control in genomics. More powerful than Bonferroni for correlated tests. |
| **Exclude Monomorphic TEs** | Statistically impossible to estimate effect size without variance. |
| **Dynamic Iteration Reduction** | Prevents CI timeout; ensures pipeline completes even on slow runners. |
| **Shapiro-Wilk + Bootstrap** | Ensures valid CIs even when normality assumption is violated (common with small N and binary predictors). |

## Limitations

1.  **Biological Validity**: Results are based on synthetic data. Real biological signal validation requires a real dataset (out of scope).
2.  **Power**: With only 50-100 lines, power to detect small effect sizes (<0.3 log2FC) is limited.
3.  **Permutation Time**: 1000 iterations on 2 cores may approach the 6h limit. Implementation includes benchmark and dynamic reduction.
4.  **Collinearity**: If the TE itself drives population structure, the R² reduction metric may be misleading (Spec Assumption). However, the "Pure Confounding" test case allows us to verify the model handles this correctly.
5.  **Replication Null**: The binomial test against 0.5 is only valid if the second dataset has no signal. The plan explicitly distinguishes between "Signal Replication" and "Null Replication" scenarios.