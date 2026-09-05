# Research: Quantifying Neural Representation Drift During Skill Learning

## 1. Dataset Strategy

The project requires a dataset containing multi-day electrophysiology (spike counts or sorted units) and corresponding trial-level behavioral logs (success/failure, kinematics) for the same subjects.

### Verified Datasets
Based on the provided verified list, the following sources are available. **Critical Note**: The spec assumes the `ds004xxx` OpenNeuro dataset contains both neural and behavioral data. The verified list contains OpenNeuro data (`clane9/openneuro-fslr64k`), but this specific dataset is fMRI (fslr64k) and **does not** contain the required electrophysiology (spike counts) or trial-level behavioral logs for motor learning.

*   **RSA (parquet)**: `https://huggingface.co/datasets/rsalshalan/MGB3/resolve/main/data/test-00000-of-00001.parquet`
    *   *Relevance*: Unverified relevance to neural drift. Likely unrelated (MGB3 is often auditory or generic).
*   **RDM (json)**: `https://huggingface.co/datasets/rdmpage/autotrain-data-inat2018/...`
    *   *Relevance*: These are image classification datasets (iNaturalist, PageX). Not suitable for electrophysiology drift analysis.
*   **OpenNeuro (parquet)**: `https://huggingface.co/datasets/clane9/openneuro-fslr64k/...`
    *   *Relevance*: This is fMRI data (surface-based fslr64k). **It does not contain spike counts or trial-level motor learning logs.**

**Decision**: No verified dataset in the provided list contains the specific combination of **electrophysiology (spike counts)** and **trial-level behavioral logs** required for this study.
*   **Action**: The implementation plan must be reframed to use a **Synthetic Dataset Generator** for the primary development and testing of the pipeline (as allowed by the spec's "Independent Test" for US-1), while the research phase will explicitly state that **no open-source electrophysiology dataset with the required variables is currently available in the verified list**.
*   **Fallback**: If the project must proceed with real data, the spec's assumption about `ds004xxx` is **invalid** based on the verified list. The pipeline will be designed to accept the *format* of such a dataset, but the research output will be based on synthetic data with known ground-truth drift parameters.

### Data Processing Strategy (Synthetic)
Since no real dataset fits the criteria:
1.  **Generator**: Implement `synthetic_data.py` to generate:
    *   `N` subjects, `D` days.
    *   `U` units with Gaussian tuning curves.
    *   **Drift Mechanism**: Random rotation of tuning curve axes over days to simulate known drift rate `b_true`.
    *   **Behavior**: Learning curve (success rate) correlated with drift speed.
2.  **Validation**: Compare recovered `b` against `b_true`.

## 2. Statistical Rigor & Methodology

### Drift Quantification (FR-004, FR-005)
*   **Metric**: Pairwise Pearson correlation distance between daily population activity vectors.
    *   *Rationale*: Standard for Representational Similarity Analysis (RSA).
*   **Model**: Linear regression `drift(t) = a + b·t`.
    *   *Handling Non-Linearity*: If residuals show non-linearity, fit exponential decay `a·exp(-b·t) + c` (per Constitution Principle VII) and compare AIC. Default to linear if fit is poor but report "non-drifting" if `b` is not significantly different from 0.
*   **Multiple Comparison Correction**: If testing multiple metrics (Pearson, Cosine, Mahalanobis), apply Bonferroni correction to the family of p-values (FR-007).

### Correlation & Hypothesis Testing (FR-006)
*   **Primary Test**: Pearson correlation between drift rate `b` and learning speed (time to reach success).
*   **Significance**: Permutation test (10,000 shuffles) to generate null distribution.
    *   *Power Limitation*: If N < 15, explicitly state the limitation in the report (US-2, SC-002).
*   **Mixed Effects**: Fit Linear Mixed-Effects Model (LMM) with `Subject` as random intercept to account for repeated measures (if applicable) or subject-level variance.

### Robustness & Sensitivity (FR-008)
*   **Metric Sweep**: Re-run drift calculation with Cosine and Mahalanobis distances. Report variance in `b`.
*   **Threshold Sweep**: Re-run unit stability filter at 70%, 80%, 90%. Plot `b` vs. Threshold.
*   **Split-Half**: Randomly split trials into two halves; calculate `b` for each; compute correlation.

## 3. Compute Feasibility (CPU-First)

*   **Environment**: GitHub Actions (2 CPU, 7 GB RAM).
*   **Strategy**:
    *   **Streaming**: If real data were available, stream via `datasets` library.
    *   **Synthetic Data**: Generate on-the-fly or load pre-generated synthetic matrices (small size).
    *   **Libraries**: `scipy`, `statsmodels`, `scikit-learn` (CPU only). No GPU dependencies.
    *   **Memory**: Population matrices are `Units × Conditions`. For 100 units × 20 conditions, this is negligible. The bottleneck is the permutation test (10k shuffles).
    *   **Optimization**: Use vectorized numpy operations for permutation shuffles. Limit iterations if memory/time constraints are tight (e.g., 1,000 shuffles for initial run, 10,000 for final).

## 4. Dataset-Variable Fit (Critical Gap)

*   **Required Variables**: Spike counts (per unit, per trial, per day), Behavioral success (per trial, per day), Subject ID.
*   **Verified Availability**: **None**. The verified OpenNeuro dataset is fMRI. The other verified datasets are image classification.
*   **Conclusion**: The study **cannot** be performed on the verified datasets. The plan proceeds with **synthetic data** that strictly mimics the required variable structure, allowing the pipeline to be built and validated (US-1) while acknowledging the lack of real-world data for the final hypothesis test (US-2). The paper will explicitly state: "Due to the unavailability of open-source electrophysiology datasets with trial-level behavioral logs, this study validates the pipeline on synthetic data with ground-truth drift parameters."

## 5. Decision/Rationale

*   **Why Synthetic Data?** The verified dataset list contains no electrophysiology data. Fabricating a URL or using fMRI data would violate Constitution Principle II (Verified Accuracy) and the "Dataset-Variable Fit" rule.
*   **Why Linear Drift?** Spec FR-005 mandates a linear model. Constitution Principle VII mentions exponential decay as a validation target. The plan implements linear as primary, with exponential as a robustness check.
*   **Why CPU-Only?** The spec (FR-010) and GitHub Actions constraints mandate CPU. The statistical methods (OLS, Permutation, LMM) are CPU-tractable.
