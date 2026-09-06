# Research: llmXive follow-up: extending "OmniOpt: Taxonomy, Geometry, and Benchmarking of Modern Optimizers"

## Executive Summary

This research investigates whether the spectral signature of the initial gradient covariance matrix (computed over the first 100 training steps) is **associated** with the rank-ordered performance of optimizer families (e.g., Adam, SGD, Lion) for a given architecture and task, as defined by the OmniOpt benchmark. The hypothesis is that "pre-flight" spectral diagnostics (Condition Number, Spectral Entropy) can serve as a proxy for identifying the optimal optimizer family, acknowledging that this measures an association between initial geometry and final outcome, not a causal prediction.

**Critical Limitation**: The predictor uses features from a **SGD probe run** (t=0 to t=100) but maps to labels derived from **full training runs** of various optimizers (t=0 to t=100k). This creates a "category error" where the feature source (SGD) differs from the label source (e.g., Adam). The study explicitly acknowledges this mismatch and frames the result as a test of whether initial geometry is invariant to the optimizer choice, rather than a direct prediction of a specific optimizer's trajectory.

## Dataset Strategy

### Verified Datasets

| Dataset | Purpose | Source / URL | Access Method |
| :--- | :--- | :--- | :--- |
| **TinyImageNet** | Proxy dataset for gradient extraction (US-1). | https://huggingface.co/datasets/Multimodal-Fatima/TinyImagenet_train/resolve/main/data/train-00000-of-00001-18bc3231d015f1e8.parquet | `datasets.load_dataset(..., streaming=True)` |
| **OmniOpt Benchmark** | Ground truth labels for "optimal mechanism family" (US-2). | **Primary**: Published "OmniOpt" Paper Tables (static, verified). **Secondary**: Re-run sub-experiments via `re_run_omniopt_subexperiment.py` (if primary source is missing). | Static lookup table (`data/omniopt_lookup.json`) OR re-run via `re_run_omniopt_subexperiment.py`. |

### Data Acquisition Plan

1.  **TinyImageNet**: The pipeline will stream the Parquet file directly from Hugging Face to avoid downloading the full dataset into RAM. A fixed seed will select a representative subset (e.g., 1000 samples) for the 100-step proxy training to ensure CPU feasibility (US-1, AC-2).
2.  **OmniOpt Labels**: 
    - **Primary Source**: The `data/omniopt_lookup.json` file will be populated from the published "OmniOpt" paper tables. This ensures a verified, canonical source.
    - **Secondary Source**: If the primary source is missing an entry for a specific architecture, the system will execute the `re_run_omniopt_subexperiment.py` script to run the specific 100k-step benchmark for that architecture/optimizer pair within the 6-hour CI window.
    - **Fallback**: If the re-run fails or exceeds the time budget, the sample is excluded. The primary source remains the canonical reference.

### Data Hygiene & Validation

-   **Checksums**: The TinyImageNet Parquet file checksum will be verified upon download.
-   **Integrity**: The `omniopt_lookup.json` will be versioned and checksummed.
-   **Missing Data**: Any model/architecture combination missing from the OmniOpt lookup will be flagged and excluded from the training set, with the exclusion logged.

## Methodological Rigor

### Spectral Feature Extraction (US-1, FR-001, FR-002)

1.  **Gradient Covariance**: Compute $G = \frac{1}{B} \sum_{b=1}^{B} \nabla \theta_b \nabla \theta_b^T$ over the first 100 steps.
    -   *Feasibility*: For 50M parameters, $G$ is too large for full EVD. We will use **Lanczos iteration** (via `scipy.sparse.linalg.eigsh`) to compute only the top $k$ eigenvalues (minimum 10, target 50). This reduces complexity from $O(N^3)$ to $O(k \cdot \text{nnz})$.
    -   *Memory Management*: `torch.no_grad()` is used. Gradients are aggregated immediately and deleted. Batch size is capped to ensure a manageable memory footprint per step. Aggressive garbage collection is enforced.
2.  **Features**:
    -   **Spectral Radius**: $\lambda_{max}$.
    -   **Condition Number**: $\kappa = \lambda_{max} / (\lambda_{min} + \epsilon)$ (with regularization $\lambda_{min} \leftarrow \lambda_{min} + \epsilon$ to handle singularity).
    -   **Spectral Entropy**: $H = -\sum p_i \log p_i$, where $p_i = \lambda_i / \sum \lambda_j$ for the top $k$ eigenvalues.
        -   *Rationale*: Power-law MLE on 50 points is statistically unsound (high variance). Spectral Entropy is a robust, well-defined metric for spectrum "flatness" that does not require distributional assumptions.
        -   *Note*: The `spec.md` requirement for "tail decay exponent" is a blocking inconsistency. This plan uses "Spectral Entropy" and flags the spec for update.

### Ground Truth Labeling (US-2, FR-003)

-   **Label Definition**: The optimizer achieving the lowest final validation loss after a fixed number of training steps in the OmniOpt benchmark.
-   **Ground Truth Optimizer Field**: The `OptimalMechanismLabel` entity includes a `ground_truth_optimizer` field to explicitly record which optimizer generated the label (e.g., "Adam", "SGD"). This distinguishes it from the `probe_optimizer` (SGD) used for feature extraction.
-   **Tie-Breaking**: If multiple optimizers share the best loss (within $\epsilon=10^{-4}$), the system will select the one with the lowest computational overhead (pre-defined priority: Adam > Lion > SGD) or exclude the sample if ambiguity is high.
-   **Exclusion**: Samples with no label in the lookup table are excluded (US-2, AC-2).

### Correlation Analysis (US-3, FR-004, FR-005)

1.  **Method**:
    -   **Primary**: Spearman Rank Correlation ($\rho$) between spectral features (Condition Number, Spectral Entropy) and the rank-ordered performance of optimizers.
    -   *Justification*: Classification (LogReg/RF) is statistically invalid for N=20 (overfitting). Spearman correlation is robust for small N and tests for monotonic association.
2.  **Validation**:
    -   **Significance**: Monte Carlo Permutation Test (sufficient iterations) to construct the null distribution.
    -   *Feasibility*: An exact permutation test (a factorial number of permutations) is computationally infeasible. The Monte Carlo approximation is used, acknowledging the p-value is an estimate.
    -   **Threshold**: $p < 0.05$ required to reject the null hypothesis that spectral features are uncorrelated with optimizer performance (US-3, AC-3, SC-002).
3.  **Robustness Check**:
    -   For a subset of models, features will be extracted using a small batch of Adam steps to verify that the spectral signature is consistent regardless of the probe optimizer (addressing the confounding variable concern). If inconsistent, the study is limited to the SGD probe only, with that limitation explicitly stated.

### Statistical Rigor & Assumptions

-   **Multiple Comparisons**: Since we are testing multiple features (Cond Num, Entropy), we will apply a **Bonferroni correction** to the p-values.
-   **Power Limitation**: With a limited sample size (N < 20 if data source is limited), the statistical power is low. The plan explicitly acknowledges this limitation. The study is exploratory; a non-significant result does not disprove the hypothesis, but a significant result is strong evidence.
-   **Causal Claims**: The study is **observational**. We do not claim that spectral features *cause* optimizer performance, only that they are *associated* with it.
-   **Collinearity**: Spectral radius and condition number may be correlated. We will report Variance Inflation Factors (VIF) and, if high, rely on Regularized Logistic Regression (L2) to handle collinearity (if classification were attempted, but it is not).
-   **Spec Inconsistency**: The `spec.md` Success Criteria (SC-005) requires a minimum of 20 diverse architectures. If the OmniOpt paper does not provide 20 diverse pairs, the study is framed as an exploratory case study with N < 20. The `spec.md` must be updated to reflect this (Flagged for Kickback).

## Compute Feasibility (CPU-First)

-   **Eigenvalue Decomposition**: Full EVD of a very large-scale matrix is impossible. We use **Lanczos** for top $k$ eigenvalues (min 10). This is feasible on CPU for a subset of the batch.
-   **Memory**: Streaming TinyImageNet, `torch.no_grad()`, small batch size (16), and aggressive garbage collection ensure RAM usage stays < 7GB.
-   **Runtime**: 20 models * (100 steps + EVD + MLE) is estimated at < 3 hours on 2 CPU cores.
-   **GPU Escape Hatch**: Not required. The Lanczos method and correlation analysis are CPU-tractable. No CUDA kernels are needed.

## Decision/Rationale

-   **Why Streaming?**: To fit the disk and RAM constraints and avoid downloading the full dataset.
-   **Why Lanczos?**: Full EVD is $O(N^3)$ and impossible for large $N$. Lanczos is $O(k \cdot \text{nnz})$ and sufficient for spectral radius and tail decay estimation.
-   **Why Spectral Entropy?**: Power-law MLE on 50 points is statistically unsound. Entropy is robust and well-defined.
-   **Why Spearman Correlation?**: Classification is invalid for N=20. Spearman correlation is robust for small N and tests for monotonic association.
-   **Why Monte Carlo Permutation Test?**: An exact test (20!) is infeasible. Monte Carlo provides a robust approximation.
-   **Why Two-Tier Ground Truth?**: No verified URL exists for OmniOpt data. The primary source (Paper Tables) ensures reproducibility; the secondary source (Re-run) ensures coverage if the primary is missing.