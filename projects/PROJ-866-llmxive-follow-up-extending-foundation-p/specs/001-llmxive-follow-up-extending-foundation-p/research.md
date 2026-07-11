# Research: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

## Research Question
What is the functional relationship between **actual context compression percentage** (via graph-traversal depth limits) and policy-violation error rates in multi-agent workflows, and where is the "safe operating zone" (error ≤ 1%)?

## Dataset Strategy

Since this study relies on **synthetic data generation** rather than external datasets, the "dataset" is the output of the `synthetic_workflow.py` generator. The generator is verified to produce:
- **A set of unique workflows**.
- **Delegation Depth**: Uniform distribution 1-20.
- **Policy Complexity**: Uniform distribution 1-10 constraints.
- **Variables**: Workflow ID, Depth, Complexity, Policy Nodes, Ground Truth State, **Actual Token Reduction %**.

**Verified Sources**:
- No external dataset URL is required. The generator logic itself is the source.
- **Tokenization**: Uses `tiktoken` (cl100k_base), a standard library with verified accuracy for LLM context simulation.
- **Graph Library**: Uses `networkx`, verified for DAG generation and traversal.

**Dataset Strategy Table**:
| Component | Source/Method | Verification Status |
|-----------|---------------|---------------------|
| Workflow Graphs | `synthetic_workflow.py` (Deterministic Python) | Verified logic (Phase 0) |
| Policy Rules | Embedded in graph metadata (synthetic) | Verified logic (Phase 0) |
| Token Counts | `tiktoken` (cl100k_base) | Verified library |
| Ground Truth | `oracle_policy.py` (Independent Rule-Based Validator) | Verified logic (Phase 0) |

## Methodology

### 1. Data Generation (FR-001)
- **Method**: Python `networkx` to generate Directed Acyclic Graphs (DAGs).
- **Parameters**:
  - `N = 500` workflows.
  - `Depth ~ Uniform(1, 20)`.
  - `Complexity ~ Uniform(1, 10)`.
  - `Seed`: Fixed (e.g., 42) for reproducibility.
- **Output**: JSON file `data/raw/workflows.json`.

### 2. Execution Engines
- **Oracle Policy Engine (Ground Truth)**:
  - A distinct, rule-based validator that defines the "correct" policy satisfaction for a given workflow.
  - **Independence**: Logically separate from execution engines to prevent circular validation.
- **Full Context Engine (Baseline Simulator)**:
  - Traverses the entire policy graph.
  - Calculates total token count using `tiktoken`.
  - Validates against `oracle_policy.py`.
  - Records `ground_truth_violations` (deviations between Full Context simulator and Oracle).
- **Compressed Context Engine**:
  - Applies BFS/DFS with `max_depth` parameter (e.g., 2, 4, 6, 8, 10).
  - Extracts subgraph.
  - Calculates token count of subgraph.
  - Validates against `oracle_policy.py`.
  - Records `compression_violations`.
  - **Key Metric**: Calculates **Actual Token Reduction %** = `(Full_Tokens - Compressed_Tokens) / Full_Tokens` for **each workflow**.
- **Compression Levels**: 5 levels (including "None" and "Max") to establish a curve.

### 3. Statistical Analysis (FR-005, FR-006)
- **Dependent Variable**: Policy-violation error (Binary: 1 if violation detected, 0 otherwise).
- **Independent Variable**: **Actual Token Reduction %** (Continuous, calculated per workflow).
- **Covariates**: Graph Depth, Policy Complexity (to control for confounding).
- **Model**: **Logistic Regression** on the 500 individual workflow observations.
  - Formula: `logit(P(Violation)) = β0 + β1*(Reduction %) + β2*(Depth) + β3*(Complexity)`.
  - This approach utilizes the full variance in token reduction, avoiding the statistical underpowering of fitting a curve to 5 aggregated points.
- **Threshold Identification**: Solve the logistic equation for `P(Violation) = 0.01` ([deferred] error) to find the specific `Reduction %` threshold.
- **Confidence Interval**: Bootstrap (a sufficient number of resamples) to derive 95% CI for the threshold.
- **Secondary Robustness Check**: Pairwise comparisons of error rates across the 5 discrete depth levels with **Bonferroni correction** to confirm monotonicity, but not as the primary method for threshold estimation.

## Decision Rationale

### Why Synthetic Data?
- **Control**: Real multi-agent logs are noisy and lack ground truth. Synthetic data allows precise control over depth and complexity variables.
- **Reproducibility**: Deterministic generation ensures the exact same dataset can be regenerated for verification (Constitution Principle I).
- **Ethics**: No PII or sensitive data involved.

### Why `tiktoken`?
- **Accuracy**: Node count is a poor proxy for context size. `tiktoken` provides the actual token count used by LLMs (FR-009).
- **CPU Efficiency**: `tiktoken` is a pure Python/C extension library that runs efficiently on CPU.

### Why Logistic Regression on Individual Observations?
- **Statistical Validity**: Fitting a non-linear curve to 5 aggregated points is underpowered and prone to overfitting. Using 500 individual data points with a continuous predictor (actual reduction %) provides sufficient power to robustly estimate the threshold.
- **Handling Confounding**: By including Depth and Complexity as covariates, we control for the fact that token reduction is not randomized but depends on graph topology.

### Why `tiktoken`?
- **Accuracy**: Node count is a poor proxy for context size. `tiktoken` provides the actual token count used by LLMs (FR-009).
- **CPU Efficiency**: `tiktoken` is a pure Python/C extension library that runs efficiently on CPU.

### Why Non-Linear Regression?
- **Hypothesis**: The relationship is expected to be non-linear (diminishing returns). Small compressions may have 0 error, but beyond a threshold, errors spike. A linear model would miss this critical "safe zone" boundary.

## Statistical Rigor Checklist

- **Multiple Comparisons**: Bonferroni correction applied as a secondary check for pairwise depth comparisons.
- **Sample Size**: A sufficient number of individual observations will be collected to provide adequate power for logistic regression (assuming medium effect size).
- **Causal Claims**: The study claims an *associational* relationship between **token reduction %** and error. While **compression depth** is randomized, **token reduction %** is observational (confounded by graph topology). The regression model controls for these confounders (Depth, Complexity) to isolate the effect of token reduction.
- **Measurement Validity**: `tiktoken` is the industry standard for token counting; `networkx` is the standard for graph traversal.
- **Collinearity**: Depth and complexity are generated independently and included as covariates to mitigate collinearity with token reduction.

## Risk Assessment

- **Risk**: Generator produces invalid workflows (impossible to satisfy).
  - **Mitigation**: Filter out invalid workflows in Phase 0; record count of excluded workflows.
- **Risk**: CPU timeout on GitHub Actions.
  - **Mitigation**: Profile execution time in Phase 0; if > 3 hours, reduce sample size or optimize graph generation.
- **Risk**: Memory overflow.
  - **Mitigation**: Stream execution logs; do not load all 500 graphs into memory simultaneously if possible (process in batches).