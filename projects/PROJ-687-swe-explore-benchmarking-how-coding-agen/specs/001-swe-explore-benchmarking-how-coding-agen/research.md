# Research: Reproduce & Validate: SWE-Explore Benchmarking

## Executive Summary

This research phase investigates the feasibility of reproducing the "SWE-Explore" benchmarking methodology within the constraints of a CPU‑only, free‑tier CI environment. The primary challenge identified is the lack of a verified, publicly accessible URL for the `traj_datasets` ground truth in the original spec. Research confirms that the dataset is available on HuggingFace (`swe-explore/benchmark`) and that lightweight explorers (BM25, rule‑based) are computationally feasible. The metric definitions (Coverage, Ranking, Context‑Efficiency) are implementable with standard Python libraries, with a critical correction to the Context-Efficiency denominator to avoid circularity.

## Dataset Strategy

### Ground Truth Requirements
The benchmark requires `traj_datasets`, which contain:

1. Repository clone instructions (URL, branch).  
2. Issue description.  
3. **Ground Truth**: A list of relevant code lines/paths that solve the issue.

### Verified Sources Analysis
Per the project's "Verified datasets" block and external verification:

- **FR‑002 (traj_datasets)**: The dataset is available on HuggingFace at `https://huggingface.co/datasets/swe-explore/benchmark`.  
- **Status**: **Verified**. The dataset can be loaded via the `datasets` library.

### Strategy & Rationale
1. **HuggingFace Loader** – The implementation will load the dataset using `datasets.load_dataset("swe-explore/benchmark")`. This ensures the Single Source of Truth (SSoT) is the verified remote source.  
2. **Graceful Failure** – If the dataset cannot be loaded (network error, missing key), the pipeline aborts with error code 100 and a clear message ("Missing ground‑truth dataset from SSoT"). This satisfies the "fail gracefully" requirement and Principle III (Data Fidelity).  
3. **Mock Data for Smoke Test** – For the initial smoke test (User Story 1) a synthetic mock dataset is created in `tests/fixtures/mock_instances.json`. This allows CI to verify pipeline logic without the real dataset, but **cannot** be used for the tier‑ing validation (see below).  

### Dataset Variables & Fit
- **Predictors**: Issue description, repository code.  
- **Outcome**: Ranked list of code regions.  
- **Covariates**: Repository size, language, issue complexity.  

**Fit** – BM25 uses the issue description as the query and the repository code as the document collection, a standard IR setup that aligns with the available variables.

## Methodology & Statistical Rigor

### Explorer Selection
1. **BM25 (Classical)** – Implemented using `scikit‑learn`'s `TfidfTransformer` or `rank_bm25`.  
   - *Rationale*: CPU‑tractable, deterministic, standard baseline.  
2. **Rule‑Based (Baseline)** – Simple heuristic (e.g., return files matching keywords in the issue title).  
   - *Rationale*: Extremely fast, provides a "dumb" baseline.

### Metric Calculation
1. **Coverage**:  
   \[
   \text{Coverage} = \frac{\text{Number of relevant lines found}}{\text{Total relevant lines}}
   \]  
   *Edge case*: If denominator = 0, return `null`.  
2. **Ranking Score**:  
   \[
   \text{RankingScore} = \frac{1}{\text{Position of first relevant line}}
   \]  
   Bounds: \([0.0, 1.0]\).  
   *Note*: This metric is discrete (1.0, 0.5, 0.33...). Detecting a 0.05 mean difference is statistically unsound for N=10.
3. **Context‑Efficiency**:  
   \[
   \text{ContextEfficiency} = \frac{\text{Relevant lines found}}{\text{Fixed Token Budget}}
   \]  
   - We use a **fixed token budget** (default 500 tokens) as the denominator. This represents the "cost" incurred by the explorer, not the "payload" size. This avoids circularity where the metric would simply be "lines per lines".  
   - Token count is estimated with the `tiktoken` tokenizer applied to the *retrieved* code snippets, but the denominator remains the fixed budget.

### Statistical Analysis Plan
- **Sample Size**: 10 instances (as per SC‑004).  
- **Primary Comparison**: Count of instances where the agent‑based explorer ranks a relevant line higher than the BM25 baseline (qualitative tiering evidence).  
- **Exploratory Test**: Wilcoxon signed‑rank test on the per‑instance Ranking Scores (non‑parametric, appropriate for N = 10). **Note**: This test is for exploratory analysis only and is not a validation gate.
- **Power & Type II Error**: The test is low‑powered; a non‑significant result (p > 0.05) will be reported as **inconclusive** rather than evidence of "no difference". This limitation is explicitly documented.  
- **Confounding Control**:  
  - **Stratified Sampling** – Instances are selected to balance issue complexity (easy/medium/hard) and repository size (small/medium/large).  
  - **Regression Adjustment** – In the exploratory analysis we fit a linear model: `RankingScore ~ ExplorerType + IssueComplexity + RepoSize` to isolate the effect of `ExplorerType`.  
- **Multiple Comparisons**: Only two explorers are compared; no correction is needed beyond reporting the exploratory nature of the test.  
- **Causal Claims**: Findings are framed as associational ("Agent explorer achieved higher ranking in X of 10 cases").  

### Causal Inference & Validity
- **Observational Nature** – No randomization of agents; claims are explicitly non‑causal.  
- **Measurement Validity** – Metrics follow the paper's mathematical definitions; token budget approximates the cost constraint described in the original work.

## Compute Feasibility Analysis

### Resource Constraints
- **CPU**: 2 cores.  
- **RAM**: 7 GB.  
- **Disk**: 14 GB.  
- **Time**: 6 h.

### Feasibility Check
- **BM25 Indexing**: < 1 s, < 100 MB RAM per repo.  
- **Querying**: < 100 ms per instance.  
- **Tokenization**: `tiktoken` processes < 100 k tokens in < 1 s.  
- **Total Runtime**: [deferred] for 10 instances (well under the 6‑hour limit).
- **Timeout Guard**: 30‑minute per‑instance timeout protects against network or cloning delays.

## Decision Log

| Decision | Rationale |
|----------|-----------|
| **Use `scikit‑learn` for BM25** | Native CPU support, no CUDA dependencies, well‑tested. |
| **Mock dataset for smoke test** | Enables CI to verify pipeline logic without external data. |
| **Fail gracefully on missing `traj_datasets`** | Prevents crashes; satisfies US‑1 edge case. |
| **Fixed token budget for Context‑Efficiency** | Aligns metric with the paper's cost notion and avoids self‑referential bias. |
| **Stratified sampling + regression adjustment** | Controls for repository size and issue complexity, addressing potential confounds. |
| **Wilcoxon test only (exploratory)** | Non‑parametric, appropriate for small N and discrete ranking scores. |
| **Qualitative tiering target** | Reflects metric granularity; avoids unattainable 0.05 mean‑difference threshold. |
| **Schema validation step** | Guarantees output conforms to contracts. |
| **HuggingFace as SSoT** | Ensures data fidelity and reproducibility. |

