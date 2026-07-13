# Research: llmXive follow-up: extending "VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understandin"

## 1. Problem Definition

The research question is whether the structural complexity of video QA questions—defined by the number of distinct entity hops in the ground-truth knowledge graph—exhibits a non-linear threshold effect on reasoning accuracy. Specifically, we hypothesize a "reasoning cliff" where accuracy drops catastrophically beyond a specific hop count (e.g., >2 hops) rather than degrading linearly.

## 2. Dataset Strategy

The analysis relies on the **VideoKR-SFT** dataset and its associated **Knowledge Graph**.

### Verified Sources & Data Availability Gate
Per the project constraints, we strictly use verified sources. The "Verified datasets" block provided in the prompt does not contain a working URL for `VideoKR-SFT`.
*   **Action**: The pipeline implements a **Data Availability Gate** in `code/ingest/download_data.py`.
    1.  The script checks for the dataset in `data/raw/`.
    2.  If missing, it attempts to fetch from the canonical source defined in `code/utils/config.py`.
    3.  If the fetch fails or the source is not in the verified list, the pipeline **halts immediately** with error code `E_DATA_MISSING` and a clear message: "VideoKR-SFT dataset not found in verified sources. Analysis cannot proceed."
    4.  **No URL is fabricated.** If the dataset is unavailable, the project remains in a blocked state until a verified source is provided.

### Sampling Strategy (Two-Stage)
To ensure statistical power for rare high-hop questions (3+ hops) within the 7 GB RAM limit:
1. **Pilot Phase**: Load a small random subset (e.g., [deferred] records) and perform full annotation (including entity linking and graph traversal) to estimate the distribution of `chain_length`.
2.  **Oversampling Phase**: Based on the pilot distribution, construct the final analysis dataset by:
    *   Including all records with `chain_length` >= 3 (if available).
 * Randomly sampling a fixed number of records for `chain_length` 1 and 2 to balance the dataset (e.g., [deferred] total, with at least 2,000 in the 3+ bin).
    *   This ensures N >= 50 for the 3+ hop bin, preventing underpowered tests.

## 3. Methodology

### 3.1 Structural Annotation (FR-001, FR-002)
*   **Input**: VideoKR-SFT records (Question, Answer) + Knowledge Graph.
*   **Process**:
    1.  **Entity Linking**: Use `code/utils/entity_linker.py` (fuzzy string matching or lightweight CPU embeddings) to map entities mentioned in the question to nodes in the Knowledge Graph.
        *   *Failure Handling*: If entities cannot be mapped, the record is labeled `status="mapping_failure"`. These are excluded from accuracy calculation but counted in the "unresolvable" rate.
    2.  **Graph Traversal**: For mapped records, compute the **shortest path** (BFS) between the query node and answer node.
    3.  **Disconnection Handling**: If no path exists, label `status="disconnected"`.
    4.  **Bias Check**: Calculate the rate of `disconnected` and `mapping_failure` per hop-count bin. If high-hop bins have significantly higher failure rates, a sensitivity analysis (Section 3.4) will be triggered.
    5.  **Assignment**: Assign `chain_length` = path_length (number of edges).
*   **Output**: Annotated CSV with `chain_length`, `status`, and `correctness`.

### 3.2 Accuracy Stratification (FR-003)
*   **Process**: Group data by `chain_length` (1, 2, 3+).
*   **Metric**: Accuracy = `sum(correct) / count(total)` per bin.
*   **Output**: Summary table and bar plot.

### 3.3 Threshold Detection (FR-004) - Permutation Test
*   **Null Hypothesis ($H_0$)**: Accuracy is linearly related to hop count (or follows a smooth trend).
*   **Alternative Hypothesis ($H_1$)**: Accuracy exhibits a non-linear "cliff" at a specific knot $k$.
*   **Test Statistic**: The difference in fit (e.g., residual sum of squares) between a linear model and a piecewise linear model with a knot at $k$.
*   **Procedure**:
    1.  **Grid Search**: Identify the optimal knot $k_{opt}$ in the range [2, 3, 4] that maximizes the test statistic on the observed data.
 2. **Permutation**: Shuffle the `correctness` labels [deferred] times. For each shuffle:
        *   Re-run the grid search to find the maximum test statistic ($T_{max}^{perm}$).
    3.  **P-Value Calculation**: $p = \frac{\text{count}(T_{max}^{perm} \ge T_{obs}) + 1}{\text{total permutations} + 1}$.
    4.  **Significance**: If $p < 0.05$, reject $H_0$. This approach inherently corrects for the multiple testing problem (grid search) without needing Bonferroni.
*   **Cliff Magnitude**: Additionally, calculate the absolute accuracy drop $\Delta = \text{Acc}(k) - \text{Acc}(k+1)$. The "cliff" is only confirmed if $p < 0.05$ AND $\Delta > \text{[deferred threshold]}$.

### 3.4 Sensitivity Analysis (FR-005) & Bias Check
*   **Threshold Sweep**: Re-run the permutation test with fixed knots at 2, 3, and 4 to visualize stability.
*   **Disconnection Bias**:
    *   Compare the "disconnected" rate across bins.
    *   **Imputation Test**: Re-calculate accuracy for high-hop bins assuming all `disconnected` and `mapping_failure` records are **incorrect**. If the "cliff" disappears under this worst-case scenario, the result is flagged as sensitive to bias.
*   **Output**: Table of p-values, effect sizes, and bias flags across definitions.

## 4. Statistical Rigor

*   **Multiple Comparisons**: Handled via the Permutation Test (generating a null distribution of the *maximum* statistic across the grid).
*   **Power**: Ensured by the two-stage oversampling strategy (target N >= 50 for 3+ hop bin).
*   **Causal Inference**: Observational study. Claims framed as "associational".
*   **Collinearity**: Hop count is the primary predictor.
*   **Model Selection**: **No GAMs** used. GAMs are inappropriate for low-cardinality discrete ordinal variables (1-5 hops) and risk overfitting. The Permutation Test for change-point is the correct tool.

## 5. Compute Feasibility

*   **Hardware**: 2 CPU cores, 7 GB RAM.
*   **Strategy**:
    *   **Sampling**: Two-stage sampling ensures dataset fits in RAM.
    *   **Graph**: `networkx` for BFS (efficient).
    *   **Permutation**: 10,000 permutations are CPU-intensive but feasible within 6 hours for a sample size of ~10k. Parallelization (via `joblib`) will be used if possible within the runner constraints.
    *   **No GPU**: All methods are CPU-native.

## 6. Risk Management

*   **Risk**: VideoKR-SFT dataset URL is unreachable.
    *   **Mitigation**: Data Availability Gate halts pipeline with `E_DATA_MISSING`.
*   **Risk**: Graph is too large for RAM.
    *   **Mitigation**: Subgraph extraction for the oversampled set.
*   **Risk**: 3+ hop bin is empty.
    *   **Mitigation**: Oversampling strategy ensures N >= 50.
*   **Risk**: Entity linking fails for many questions.
    *   **Mitigation**: Report "mapping_failure" rate; sensitivity analysis with imputation.
