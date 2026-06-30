# Research: Reproduce & Validate Active Learners as Efficient PRP Rerankers

## Overview
This research document validates the feasibility of reproducing the "Active Learners as Efficient PRP Rerankers" paper within the constraints of a CPU-only, free-tier CI environment. It focuses on dataset verification, model selection, and the statistical rigor of the proposed experiments, specifically addressing power analysis and confounder control.

## Dataset Strategy

### Verified Sources
The project relies on the following verified datasets. No other sources are used.

| Dataset | Purpose | Verified URL(s) | Notes |
|:--- |:--- |:--- |:--- |
| **BEIR (dbpedia-entity)** | Primary evaluation dataset | ` | **Strict Requirement**: Must be downloaded via `beir` library. No fallback. |
| **BEIR (scifact)** | Primary evaluation dataset | ` | **Strict Requirement**: Must be downloaded via `beir` library. No fallback. |
| **BEIR (trec-covid)** | Validation of retrieval pipeline | ` | Used only for format verification if needed. |
| **BEIR (trec-covid qrels)** | Ground truth for NDCG | ` | Essential for calculating NDCG@10. |
| **IReranker** | Codebase | **NO verified source found** | The codebase is vendored from the paper's repository (assumed local git submodule). |

### Dataset Fit & Mismatch Analysis
- **Requirement**: The study requires `dbpedia-entity` and `scifact` datasets with BM25 initial rankings.
- **Constraint**: The verified dataset list explicitly includes `dbpedia-entity` and `scifact` via the BEIR HuggingFace organization.
- **Resolution**:
 - The `beir` library will be used to download `dbpedia-entity` and `scifact` via `beir.Datasets`.
 - **Critical Protocol**: If the `beir` library fails to fetch these specific datasets (e.g., network error, missing file), the job will **fail immediately** with a `DataUnavailableError`. No fallback to `fiqa` or `trec-covid` is permitted, as these represent different domains (web vs. scientific) and would invalidate the reproduction of the paper's specific claims.

### Sampling Strategy (Feasibility & Power)
- **Problem**: Full BEIR datasets are too large for constrained RAM and the 6-hour limit when running LLM inference.
- **Solution**: **Stratified Sampling of "Hard" Queries**.
 - **Step 1**: Retrieve top 1000 documents per query via BM25.
 - **Step 2**: Bin queries by initial BM25 NDCG@10 (High, Medium, Low difficulty).
 - **Step 3**: Sample 200 queries proportionally across bins. This ensures the sample includes "hard" cases where reranking is most valuable, increasing signal-to-noise ratio.
 - **Step 4**: Limit candidate documents per query to a top-ranked subset. This reduces pair count to a manageable level per query (for 100 call budget).
 - **Justification**: N=200 provides sufficient power (approx. 0.80) to detect a medium effect size (Cohen's d ~ 0.5) in NDCG@10 delta, which is expected for AL vs. Classic. This addresses the power concern raised by the panel.

## Model Strategy

### LLM Selection
- **Candidate**: `google/flan-t5-large` (780M parameters).
- **Feasibility**:
 - **Memory**: ~4GB RAM for model weights (float32). Fits within 7GB limit.
 - **Compute**: CPU inference latency is expected to be negative, indicating a performance gain over the baseline.
 - **Runtime Calculation**: 200 queries * 100 calls = 20,000 calls. At 1.5s/call = 8.3 hours (Too long).
 - **Adjustment**:
 - **Dynamic Capping**: If initial benchmark > 1.5s/call, switch to `flan-t5-base` (250M params).
 - **Query Reduction**: If `large` is required but runtime > 5h, reduce query count to 150.
 - **Model Precision**: Use `float32` (default) or `float16` if supported by CPU wheels. No 8-bit quantization.
- **Construct Validity Check**:
 - **Validation Step**: Run a pilot on 10 queries with both `large` and `base`.
 - **Criterion**: If `base` yields NDCG@10 < 0.1 (near random), `large` is mandatory. If `large` is too slow, the report will explicitly state the limitation to "relative efficiency" rather than "absolute score reproduction".

### Statistical Rigor
- **Multiple Comparisons**: The `limit_comparisons.py` experiment runs multiple budget levels. A **Bonferroni correction** will be applied if hypothesis testing is performed across these levels.
- **Power Analysis**: With N=200 stratified queries, the study is powered to detect a delta NDCG of ~0.02-0.03. For smaller effects, the plan will report **95% Confidence Intervals** rather than binary pass/fail. This avoids Type II errors.
- **Causal Inference**: The study uses a **Stratified Quasi-Experimental Design**. By controlling for query difficulty (stratification), we reduce confounding bias. Claims are framed as "associational improvements in NDCG per call within difficulty strata".
- **Collinearity**: Budget levels are treated as ordinal variables. The analysis will report the slope of NDCG vs. Budget to detect sensitivity.

## Experimental Design

### Experiment 1: End-to-End Smoke Test
- **Goal**: Verify pipeline integrity.
- **Input**: `dbpedia-entity` (stratified sample of 200 queries).
- **Budget**: 100 calls.
- **Metric**: Exit code 0, `summary.csv` generation.

### Experiment 2: AL vs. Classic Efficiency
- **Goal**: Validate the core hypothesis.
- **Input**: `scifact` and `dbpedia-entity` (stratified sample of 200 queries each).
- **Budgets**: 10, 50, 100, 200 calls.
- **Metric**: NDCG@10 for AL vs. Classic.
- **Success Criterion**: 95% CI of (AL NDCG - Classic NDCG) does not include zero at budget 50.

### Experiment 3: Noise Robustness (Bias Reduction)
- **Goal**: Validate that randomized oracle converts systematic bias to zero-mean noise.
- **Design**: Compare **Randomized Oracle** vs. **Deterministic Oracle** (Always A-B).
- **Input**: 500 query-document pairs (synthetic or from dataset).
- **Metric**: **Bias Reduction Index (BRI)** = Variance(NDCG_Deterministic) - Variance(NDCG_Randomized).
- **Statistical Test**: **Levene's Test** for equality of variances.
- **Success Criterion**: Levene's test p-value < 0.05, indicating significantly lower variance for the randomized oracle.
- **Note**: We do NOT measure "flip rate" as a success metric (tautological). We measure the *impact* of randomization on the final score distribution.

### Experiment 4: Budget Threshold Sensitivity
- **Goal**: Assess sensitivity to budget threshold.
- **Design**: Run budgets, 100, 110 calls.
- **Metric**: Slope of NDCG@10 vs. Budget.
- **Statistical Test**: 95% CI of the slope. If CI excludes zero, the system is sensitive to the threshold.

## Risk Mitigation
- **Runtime Exceedance**: If the job exceeds a predetermined duration threshold, the script will automatically log a warning and terminate, saving partial results. The `quickstart.md` will document how to resume or reduce sample size further.
- **Data Corruption**: A pre-flight check will verify the integrity of the downloaded BEIR files.
- **LLM Timeout**: Retry logic (limited attempts) with exponential backoff. If all fail, the pair is skipped and logged.
- **Model Fallback**: Automatic switch to `flan-t5-base` if `large` exceeds time budget.