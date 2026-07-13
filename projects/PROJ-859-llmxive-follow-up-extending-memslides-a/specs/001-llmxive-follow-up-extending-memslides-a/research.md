# Research: Trace Compressibility Analysis

## Research Question
What structural properties of multi-turn tool-execution traces determine their compressibility into symbolic rules without degrading the fidelity of persona-aligned agent behavior?

## Methodology

### 1. Data Synthesis Strategy
Since no verified external source exists for the specific "MemSlides" multi-turn tool traces required for this analysis, we will generate a **synthetic dataset** based on the MemSlides benchmark schema.
- **Source**: Internal synthetic generator (`code/generators/synthetic_trace.py`).
- **Rationale**: The research question focuses on *structural* properties (entropy, repetition, variance) rather than specific real-world content. A synthetic dataset allows controlled variation of these properties to establish causal links.
- **Verification**: The generator will be validated against the schema constraints to ensure structural integrity (Constitution Principle VI). It will explicitly log `exact_tool_sequence` and `raw_arg_variance` to ensure metrics are mathematically derivable.

**Dataset Variables**:
- `trace_id`: Unique identifier.
- `tool_sequence`: List of tool calls (e.g., `insert_chart`, `format_text`).
- `arguments`: Semantic content of tool arguments.
- `final_state`: Ground-truth slide state representation.
- `raw_arg_variance`: Pre-calculated variance value stored in the trace for verification.

### 2. Structural Metric Extraction
For each trace, the following metrics will be computed:
- **Sequence Entropy**: Measures the randomness/complexity of the tool sequence.
- **Tool-Repetition Frequency**: Count of repeated tool types relative to sequence length.
- **Argument Semantic Variance**: Calculated using the `sentence-transformers/all-MiniLM-L6-v2` model (CPU-tractable). The metric is the **mean pairwise cosine distance** between argument embeddings within a trace. This ensures the metric measures semantic diversity, not just token length.

*Handling Missing Data*:
- If arguments are empty, semantic variance is imputed to `0.0` with a warning log.
- Traces with zero repetitions are recorded as high-complexity data points.

### 3. Rule Induction & Compressibility Score
**Crucial Distinction**: To answer "what properties determine *compressibility*", we do not train a global classifier. Instead, we perform **Per-Trace Rule Induction**:
1. For each trace $T$, we train a lightweight model (Decision Tree/RuleFit) to predict the **ground-truth `final_state`** of $T$ using only the structural metrics of $T$ (and potentially a small context window).
2. We measure the **Fidelity**: Does the induced rule set reproduce the `final_state` of $T$ within a tolerance (e.g., >90%)?
3. We measure the **Compression Ratio**: $Size(Rules_T) / Size(Trace_T)$.
4. **Compressibility Score**: Defined as $1 / (Size(Rules_T) / Size(Trace_T))$ if Fidelity $\ge$ Threshold, else 0.

This approach measures the compressibility of *each specific trace* based on its structural properties, rather than measuring the accuracy of a global model.

### 4. Benchmarking & Statistical Analysis
- **Baseline**: Raw memory agent (retrieves full trace context).
- **Compressed (Global)**: Uses a **global rule set** induced from the training data to benchmark latency and aggregate accuracy (FR-004/005).
- **Compressed (Per-Trace)**: Uses the per-trace rules to calculate the Compressibility Score.
- **Metrics**:
  - **Edit Accuracy**: Fraction of edits matching ground truth (for global benchmark).
  - **Retrieval Latency**: Time from instruction to context-ready.
  - **Fidelity Loss**: $1 - \text{Accuracy}_{compressed}$ (bounded 0 to 1).
- **Statistical Test**:
  - **Primary**: **Beta Regression** modeling **Fidelity Loss** (outcome, bounded 0-1) against Structural Metrics (predictors). This avoids the issue of negative values in "difference" metrics.
  - **Secondary**: **Multiple Linear Regression (MLR)** if Fidelity Loss is transformed to log-odds (satisfying Constitution Principle VII as a robustness check).
  - **Correlation**: Spearman correlation between Structural Metrics and the **Per-Trace Compressibility Score**.
  - **Multiple Comparisons**: Bonferroni correction applied to all regression tests.

## Dataset Strategy

| Dataset Name | Source / Loader | Verified URL | Notes |
| :--- | :--- | :--- | :--- |
| Synthetic MemSlides Traces | `code/generators/synthetic_trace.py` | N/A | Generated internally. No external URL. |
| Held-out Test Set | `code/generators/synthetic_trace.py` (seeded) | N/A | Generated internally. |

*Note: As per the "Verified datasets" block, no external URLs are available for MemSlides, RuleFit, or CPU-tractable methods. All data is synthetic.*

## Statistical Rigor & Assumptions

- **Causal Inference**: This is an observational study on synthetic data. Claims will be framed as associational unless the synthetic generation process explicitly randomizes the structural properties (which it will).
- **Power Analysis**: The sample size will be [deferred] but determined to ensure sufficient power for detecting medium effect sizes in regression. If power is limited, this will be explicitly acknowledged.
- **Collinearity**: Structural metrics (e.g., entropy and repetition) may be correlated. Variance Inflation Factor (VIF) will be checked. If collinearity is high, models will be reported with caution, and descriptive statistics will be prioritized over independent effect claims.
- **Measurement Validity**: "Edit Accuracy" is a standard proxy for fidelity. "Retrieval Latency" is measured via wall-clock time in a controlled environment. "Argument Semantic Variance" uses a validated embedding model (`all-MiniLM-L6-v2`) and cosine distance to ensure construct validity.

## Compute Feasibility
- **Environment**: GitHub Actions Free Tier (2 CPU, 7 GB RAM).
- **Model**: Decision Tree/RuleFit (CPU-tractable). `sentence-transformers/all-MiniLM-L6-v2` is CPU-optimized.
- **Data**: Subset to ~7 GB RAM limit.
- **Runtime**: Pipeline designed to complete within 6 hours.
- **No GPU**: All operations are CPU-only. No CUDA dependencies.