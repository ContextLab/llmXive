# Research: NatureBench Abstraction Distance Analysis

## Dataset Strategy

| Dataset Name | Description | Source / Loader | Status |
| :--- | :--- | :--- | :--- |
| **NatureBench** | 90 scientific tasks with method descriptions, SOTA values, and domain clusters. | `huggingface.co/datasets/naturebench` (Hypothesized) | **UNVERIFIED** (Pivot to SWE-bench if missing) |
| **SWE-bench** | [deferred] software engineering tasks with problem statements and test outputs. | `datasets.load_dataset("princeton-nlp/SWE-bench")` | **VERIFIED** |

**Pivot Strategy**:
- If NatureBench is not found in the verified list, the system automatically pivots to SWE-bench.
- **Mapping**:
  - `problem_statement` -> `method_description`
  - `test_output` -> `ground_truth_sota` (extracted from test results)
  - `domain_cluster` -> Derived from repository name or task category.
- This ensures the study can proceed with valid, verified data.

## Methodology

### 1. Abstraction Distance Quantification
The independent variable is derived from the "Gold Standard Method List" (external to the text).
- **Metric**: "Novelty Index" = `(Unique Functions in Gold Standard - Standard Functions) / Total Unique Functions`.
- **Standard Library Registry**: A curated list of standard functions (e.g., `numpy.array`, `pandas.DataFrame`).
- **Rubric**:
  - **Score 1**: ≥80% Standard (Low Novelty).
 - **Score 2**: 50–[deferred] Standard.
 - **Score 3**: 20–[deferred] Standard.
 - **Score 4**: 1–[deferred] Standard.
  - **Score 5**: ≤19% Standard (High Novelty).
- **Validation**: A subset of tasks will be rated by domain experts. Krippendorff's Alpha will be calculated. If Alpha ≥ 0.7, automated scores for all 90 tasks are accepted as "Expert Proxy" scores.

### 2. Agent Execution & Failure Classification
- **Agents**: Three distinct open-source agents (SWE-agent, OpenHands, `swe-agent-light`).
- **Timeout**: Hard -hour limit per task.
- **Failure Hierarchy** (Strict Priority):
  1.  **Syntax Error**: Invalid code.
  2.  **Wrong Method Choice**: Valid code, but method used is NOT in Gold Standard.
  3.  **Data Mismatch**: Valid code, method in Gold Standard, but numerical output error > 0.05.
  4.  **Timeout**: Execution exceeded time limit.
- **Outcome**: Binary "Wrong Method Choice" (1) vs. Not (0) for correlation.

### 3. Statistical Analysis
- **Primary Test**: **Logistic Regression** to model `P(Wrong Method Choice) ~ Abstraction Distance`. This is appropriate for binary outcomes and ordinal predictors.
- **Secondary Test**: Spearman's Rank Correlation ($\rho$) (descriptive).
- **Confidence Intervals**: Binomial proportion confidence intervals for failure rates within `domain_cluster`.
  - **Method**: Clopper-Pearson for $n < 30$, Wilson for $n \ge 30$.
  - **Aggregation**: If any cluster has $n < 10$, merge into "Cross-Domain" group.
- **Power Analysis**: With N=90, the study is powered to detect a medium effect size (rho ≈ 0.3) at [deferred] power. If the dataset is pivoted to a smaller subset (e.g., <50 tasks), the study will be labeled "Exploratory" and will not claim statistical significance.

## Decision Rationale (Compute Constraints)
- **Why Batched Execution?** The spec requires 90 tasks * 4 hours = 360 hours of compute. The free tier imposes a time limit on each job.
  - **Decision**: Process multiple tasks per job, running a scalable batch of jobs configured for parallel execution. Total wall-clock time is expected to be substantial. This exceeds the 24h target but ensures the study is executed on real agents.
- **Why Real Agents?** Rule-based proxies cannot generate stochastic, non-deterministic failures. The study requires real agent behavior to test the correlation between abstraction distance and failure.
- **Why Logistic Regression?** Spearman's Rank Correlation is less robust for binary outcomes. Logistic Regression provides a direct probability model and is the standard for this type of analysis.