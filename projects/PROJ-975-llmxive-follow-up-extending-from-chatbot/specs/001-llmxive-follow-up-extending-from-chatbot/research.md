# Research: llmXive follow-up: extending "From Chatbot to Digital Colleague"

## Research Question

At what library size (tipping point) does semantic redundancy in a "Digital Colleague" agent's skill library cause a statistically significant decline in task success, and can a periodic "Skill Pruning" heuristic mitigate this degradation?

## Literature Context

The "Digital Colleague" paradigm posits that persistent, skill-based agents outperform stateless chatbots. However, retrieval noise increases with library size. This project synthesizes concepts from:
1.  **Retrieval-Augmented Generation (RAG)**: Performance degradation due to irrelevant context (Noise).
2.  **Skill Library Management**: The trade-off between capability coverage and retrieval precision.
3.  **Piecewise Linear Regression**: A statistical method for identifying structural breaks (tipping points) in performance curves.

## Dataset Strategy

Since no public dataset exists with *controlled semantic overlap* and *deterministic ground-truth skill paths* for code execution, this project generates a **Synthetic Dataset**.

| Dataset Component | Source/Method | Justification |
| :--- | :--- | :--- |
| **Tasks** | `code/generate_data.py` (Synthetic) | Requires a substantial set of unique multi-step problems with known ground-truth skill sequences. |
| **Skills** | `code/generate_data.py` (Synthetic) | A set of Python functions with programmatically adjusted cosine similarity (Low/Med/High). |
| **Ground Truth** | `code/generate_data.py` (Synthetic) | Deterministic paths independent of retrieval logic to measure fidelity. |

**Note**: The "Dataset" is generated locally at runtime. No external download is required, satisfying CI constraints.

## Methodology

### 1. Data Generation
- **Tasks**: 500 synthetic problems, each requiring 3-5 deterministic actions.
- **Skills**: 100 Python functions. Embeddings generated via `sentence-transformers/all-MiniLM-L6-v2`.
- **Overlap Control**:
  - *Low*: Mean cosine < 0.30.
  - *Medium*: Mean cosine > 0.50.
  - *High*: Mean cosine > 0.80.
- **Verification**: Mean pairwise similarity calculated; `maximal_overlap_detected` flag raised if > 0.95.

### 2. Agent Execution Loop
- **Configurations**: Library sizes **[10, 20, 30, 40, 50, 60, 70, 80, 90, 100]**. (Expanded from 4 to 10 levels to support Piecewise Regression).
- **Metrics**: Task Success (Binary), Latency (ms), Token Usage, Retrieval Precision (Jaccard), Retrieval Diversity (Inverse Variance of top-k similarities against **query task embedding**).
- **Pruning**: Enabled in experimental runs. Triggered **strictly every 10 tasks**. Removes skills with `usage_count == 0` AND `min_cosine_sim < 0.70`.

### 3. Statistical Analysis
- **Primary Method**: **Piecewise Linear Regression** (FR-005).
  - Model: `Success_Rate ~ Library_Size` with a single breakpoint `x0`.
  - Goal: Identify `x0` where the slope significantly changes (tipping point).
  - *Note*: Logistic Regression is **NOT** the primary method; it is retained only as a secondary sensitivity analysis for binary outcomes.
- **Secondary Analysis**:
  - **Pruning Effect**: Paired t-test (or non-parametric equivalent) comparing Pruned vs. Baseline success rates at each library size.
  - **Collinearity**: Variance Inflation Factor (VIF) for predictors "Library Size" and "Mean Pairwise Similarity" (FR-007). Target VIF < 5.0. **Action**: If VIF >= 5.0, the model is invalid for independent effect interpretation.

## Decision Rationale

- **Why Synthetic Data?** Public datasets (e.g., HumanEval) do not allow control over "semantic overlap" between skills, which is the independent variable of interest.
- **Why Piecewise Regression?** The hypothesis predicts a *threshold* effect (tipping point), not a linear decline. Piecewise regression is the standard method for detecting structural breaks.
- **Why 10 Library Sizes?** 4 levels are insufficient for breakpoint estimation. 10 levels provide necessary degrees of freedom for statistical validity.
- **Why CPU-First?** The dataset is small (500 tasks, 100 skills). Embedding 100 strings takes milliseconds. No GPU is required, ensuring CI feasibility.

## Limitations

- **External Validity**: Results are valid within the synthetic simulation. Generalization to real-world chaotic environments is associative.
- **Power**: A substantial number of tasks distributed across 10 groups (approximately 50 per group) provides [deferred] power to detect large effect sizes (Cohen's h > 0.4). Subtle tipping points may be missed.
- **Embedding Model**: `all-MiniLM-L6-v2` is a lightweight proxy; more advanced models may yield different overlap metrics.