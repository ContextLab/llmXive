# Research: Reproduce & Validate ProRL

## 1. Dataset Strategy

### Verified Sources
The project relies on the `Books` dataset provided via the project submodule.
- **Source Repository**: The dataset is sourced from the ProRL repository submodule: ` (or the specific upstream URL defined in the project's `.gitmodules`).
- **Status**: NO verified external URL found for the specific `Books` dataset version required by the ProRL paper in the provided "Verified datasets" list. The data is local to the submodule.
- **Variable Fit Check**:
 - **Required**: User-item interaction sequences, item embeddings (`qwen3-embedding-8b-pca.sem_ids`).
 - **Critical Dependency**: The file `qwen3-embedding-8b-pca.sem_ids` must exist in `datasets/Books/`. This is a pre-computed artifact from the ProRL paper, not generated on-the-fly.
 - **Risk**: If `sem_ids` are missing, the pre-training phase cannot initialize the backbone.
 - **Mitigation**: The pipeline will abort with a "Missing Critical Resource" error if this file is absent.

### Dataset Size & Embedding Feasibility
- **Problem**: The full `Books` dataset and its 8B-model embeddings (`qwen3-embedding-8b-pca.sem_ids`) likely exceed the 7GB RAM limit of the free-tier runner.
- **Feasibility Check**: In Phase 0, the system will check the file size of `sem_ids`. If > 6GB, the pipeline will abort with a specific error: "Dataset/Embeddings too large for 7GB RAM limit."
- **Sampling Strategy (Stratified)**:
 - If the dataset is accessible but large, the system will apply **Stratified Sampling by Item Popularity**.
 - **Method**: Items are binned by interaction count (Head, Body, Tail). A proportional number of items are sampled from each bin to preserve the long-tail distribution.
 - **Validation**: A "Distribution Validation Step" will compare the interaction density and item popularity histograms of the sampled subset against the full dataset (if accessible) or a reference distribution. If the Kullback-Leibler divergence exceeds a threshold, the sampling parameters are adjusted or the run is aborted.
 - **Rationale**: Simple random sampling or `head()` truncation would distort the popularity bias, invalidating HitRate/NDCG metrics. Stratified sampling preserves the statistical properties required for the RL policy to learn.

## 2. Algorithm & Methodology

### ProRL Core Components
1. **Pre-training**: Initializes the recommendation backbone using the interaction data.
 - **Method**: Supervised learning (next-item prediction).
 - **Constraint**: Must run on CPU.
2. **Rectified Policy Gradient (RL)**: Optimizes the proactive policy.
 - **Method**: Policy Gradient with Rectification.
 - **Constraint**: Must run on CPU; no CUDA-specific kernels.

### Power & Validity Analysis
- **Sample Size Limitation**: The effective sample size is drastically reduced due to RAM constraints (likely < 100k interactions vs. millions in the full dataset).
- **Statistical Power**: The plan **cannot** perform a formal power analysis to detect the effect sizes claimed in the paper. The reduced sample size means the RL policy may not converge to the same performance level.
- **Reframed Goal**: This project is a **Feasibility and Implementation Fidelity Demonstration**.
 - **Success Metric**: "The code runs without error, produces valid artifacts, and the metrics are non-zero and exceed a Random Baseline."
 - **Failure Mode**: If metrics do not match the paper's claims, the result is interpreted as "Under-powered due to resource constraints" rather than "Algorithm failure."
- **Causal Claims**: The reproduction focuses on *implementation fidelity* (does the code run?), not necessarily *causal inference* validity of the paper's claims. The report will frame results as "Observed Performance under Resource Constraints."

## 3. Statistical Rigor & Limitations

- **Variance Reporting**:
 - Ideally, the evaluation will be run 3 times with different random seeds to compute standard deviation.
 - **Constraint**: If time (6h) or RAM prevents multiple runs, the report will explicitly state: "Single-run point estimate; variance not computed due to resource constraints."
 - The metrics schema includes fields for `std_dev_hit_rate` and `std_dev_ndcg` (nullable) to allow for this if feasible.
- **Baseline Comparison**:
 - The system will compute a **Random Baseline** (uniform sampling) and a **Greedy Baseline** (popularity-based).
 - If the paper's reported baseline metrics are available in the code/config, they will be included in the report for comparison.
 - **Scientific Validity**: A result is considered "valid" if ProRL > Random Baseline. Matching the paper's exact numbers is not expected due to sampling.

## 4. Computational Feasibility

### Hardware Constraints
- **Target**: GitHub Actions Free Tier (multi-core CPU, ~7GB RAM, 14GB Disk, 6h limit).
- **GPU**: **Strictly Prohibited**.
- **Library Compatibility**:
 - `torch`: Must use `torch==2.x+cpu` (no CUDA).
 - `transformers`: Standard CPU build.
 - `bitsandbytes`: **Must be excluded**. If the code imports it, the plan requires a patch to remove or mock it.

### Runtime Estimation
- **Pre-training**: Estimated 1-2 hours for a sampled dataset on 2 vCPU.
- **RL Training**: Estimated 2-3 hours for 100 epochs on sampled data.
- **Buffer**: 1 hour for data loading, distribution validation, and report generation.
- **Total**: ~5-6 hours (fits within 6h limit if sampling is aggressive).

## 5. Decision Log

| Decision | Rationale |
|----------|-----------|
| **CPU-Only Execution** | Required by spec (FR-001, FR-002) and CI constraints. |
| **Stratified Sampling** | Necessary to preserve distributional properties (popularity bias) for valid metric estimation, unlike random sampling. |
| **Abort on Missing `sem_ids`** | Prevents silent failure; ensures dataset-variable fit. |
| **Abort on Size > 6GB** | Prevents OOM; ensures the plan is honest about hardware limits. |
| **No Quantization** | `bitsandbytes` requires CUDA; default float32 is required for CPU stability. |
| **Reframed Goal** | "Feasibility Demonstration" is the only scientifically sound claim given the resource constraints. |