# Research: llmXive follow-up: extending "Foundation Protocol: A Coordination Layer for Agentic Society"

## Research Question

What is the functional relationship between context compression (via graph-traversal depth limits) and policy-violation error rates in multi-agent workflows, and where is the "safe operating zone" threshold?

## Dataset Strategy

### Verified Datasets

The project relies on a **synthetic dataset** generated programmatically to ensure full control over variables (delegation depth, policy complexity) and ground-truth validity. No external open-source dataset exists that contains the specific "policy graph" and "compression error" variables required for this controlled experiment.

**Source**: The data generation logic is derived from the `pm4py` synthetic event log generation pattern, adapted for the specific "Foundation Protocol" graph structure. This approach is verified to produce reproducible, structured data suitable for statistical analysis.

- **Install**: `pip install pm4py` (used for log structure verification, though the core generator uses `networkx` for graph logic).
- **Verified**: The generation recipe produces records with fields: `workflow_id`, `delegation_depth`, `policy_complexity`, `policy_nodes`, `ground_truth_state`, `actual_token_reduction_percentage`.
- **Access Recipe**: The data is generated on-the-fly by the `src/services/generator.py` script using a deterministic seed. No external download is required.

| Dataset Name | Source Type | Programmatic Loader | Notes |
| :--- | :--- | :--- | :--- |
| Synthetic Workflow Graphs | Local Generation (pm4py-inspired) | `src/services/generator.py` | Generates a diverse set of unique workflows with varying depth and complexity. |
| Execution Logs | Local Simulation | `src/services/executor.py` | Simulates "Full" and "Compressed" execution against Oracle. |

### Data Generation & Simulation Logic

1.  **Workflow Generation**:
    -   **Method**: Directed graph construction using `networkx`.
    -   **Parameters**: workflows. Delegation depth: Uniform distribution (minimum depth defined). Policy complexity: Varies (multiple constraints per workflow).
    -   **Seed**: Fixed random seed (e.g., `42`) for reproducibility (Constitution Principle I).
    -   **Validation**: Each workflow is validated to ensure it is solvable by the Oracle (no "impossible" workflows). Invalid workflows are flagged (`is_valid=False`) and excluded from the error rate calculation denominator (Total Valid Workflows) to prevent selection bias.
    -   **Adaptive Sampling**: An initial pilot run (depths 0, 5, 10) identifies the approximate inflection point. Subsequent runs densify depth steps (e.g., k=4, 5, 6, 7, 8) near the anticipated % error threshold to ensure sufficient sampling density for accurate threshold detection.

2.  **Oracle Policy Engine (Simulated Agent)**:
    -   **Role**: Independent ground-truth validator.
    -   **Logic**: A deterministic state machine that acts as a **simulated agent**. It attempts to **deduce** the validity of a workflow step based on the *provided* context. It fails only if the required policy logic **cannot be deduced** from the available nodes, not merely because a node is missing. This prevents the tautology of "missing node = error" and models the actual reasoning capability of the agent.
    -   **Independence**: The Oracle logic is distinct from the compression algorithm. The compression algorithm *removes* nodes; the Oracle *attempts to deduce* validity from what remains. This prevents circular validation (Constitution Principle VI).

3.  **Compression Simulation**:
    -   **Algorithm**: Breadth-First Search (BFS) or Depth-First Search (DFS) with a configurable depth limit `k`.
    -   **Metric**: Token count calculated via `tiktoken` (**model: cl100k_base**) on the serialized policy subgraph.
    -   **Variants**: Runs executed at depths `k` determined by adaptive sampling (e.g., 0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10).
    -   **Edge Cases**:
 - `k=0`: No context passed. Records `context_reduction_pct` as `"[deferred]"` string and error rate as [deferred] (if policy required).
        -   Single-node graph: Records `context_reduction_pct` as `"[deferred]"` string.
        -   Invalid workflows: Excluded from the denominator of the error rate calculation.

## Statistical Analysis Plan

### Methodology

1.  **Regression Analysis (GLMM)**:
    -   **Model**: Generalized Linear Mixed-Effects Model (GLMM) with a logit link function.
    -   **Fixed Effects**: Context reduction percentage (continuous), Policy complexity, Delegation depth.
    -   **Random Effects**: Random intercepts for `workflow_id` to account for hierarchical clustering (multiple observations per workflow).
    -   **Hypothesis**: The relationship is monotonic and non-linear. The analysis will explicitly **test for monotonicity** (e.g., using isotonic regression or trend tests) rather than assuming it.
    -   **Significance**: P-values calculated for model coefficients.
    -   **Multiplicity**: **Trend tests (Cochran-Armitage)** used for ordered depth comparisons. Bonferroni correction is reserved only for non-ordered secondary pairwise checks, not the primary threshold detection.

2.  **Threshold Detection**:
    -   **Target**: Identify the `Context Reduction %` where `Error Rate` first exceeds 1%.
    -   **Method**: Interpolation from the GLMM's fitted curve and confidence band.
    -   **Confidence**: **A sufficient number of bootstrap resamples** to generate a high-confidence interval for the threshold estimate (SC-004, Verified Fact). The threshold value will be **rounded to 2 decimal places**.
    -   **Output**: `threshold_report.json` and `tradeoff_curve.csv` will contain `threshold_confidence_lower` and `threshold_confidence_upper`.

3.  **Power Analysis**:
    -   **Assumption**: Medium effect size.
    -   **Sample Size**: A sufficient number of workflows across adaptive depth steps provides sufficient power to detect the threshold effect, especially with the densified sampling near the inflection point.

### Compute Feasibility

-   **CPU-First**: All operations (graph traversal, tokenization, GLMM via `statsmodels`) are CPU-native. No GPU is required.
-   **Memory**: 500 small graphs and JSON logs fit comfortably within 7GB RAM.
-   **Time**: Estimated runtime < 2 hours on 2 vCPU.

## Decision/Rationale

-   **Synthetic Data**: Chosen over real data because no public dataset contains the specific "policy graph" and "compression error" variables required. Synthetic generation allows precise control over the independent variable (compression depth) and ground truth.
-   **CPU-Only**: The simulation does not involve LLM inference, only graph algorithms and token counting. Running on CPU ensures fidelity to the "edge device" constraints mentioned in the motivation.
-   **Oracle Independence**: The strict separation of the Oracle from the execution engine is mandated by Constitution Principle VI to ensure the validity of the error metric. The Oracle simulates deduction, not simple presence checks.
-   **GLMM vs. Standard Regression**: GLMM is chosen to account for the non-independence of observations (multiple depths per workflow), preventing inflated Type I error rates.
-   **Adaptive Sampling**: Ensures sufficient data density near the critical threshold, addressing the power analysis concern for threshold detection.
