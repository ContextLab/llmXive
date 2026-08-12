# Research: llmXive Follow-up: Trace Compressibility Analysis

## Problem Statement

The core research question is: *What structural properties of multi-turn tool-execution traces determine their compressibility into symbolic rules without degrading the fidelity of persona-aligned agent behavior?*

This research aims to operationalize "compressibility" by correlating quantitative structural metrics (sequence entropy, tool-repetition frequency, argument semantic variance) with the fidelity loss (Edit Accuracy difference) when replacing raw memory with a symbolic rule bank.

## Dataset Strategy

### Synthetic Data Generation
Since no verified public source exists for the specific "MemSlides" multi-turn tool-execution traces required for this analysis, and the spec assumes the ability to generate a synthetic dataset that mimics real-world distributions, the plan relies on **synthetic generation** based on the MemSlides benchmark schema.

- **Source**: Synthetic generator (`code/synthesis/generator.py`) implementing the MemSlides schema logic.
- **Rationale**: The spec (US-1) explicitly requires a synthetic dataset of multi-turn revision sessions. The "Verified datasets" block confirms NO verified source exists for MemSlides, RuleFit, or CPU-tractable methods. Therefore, a programmatic generator is the only feasible, non-fabricated approach.
- **Volume**: The generator will produce [deferred] distinct sessions for the Training Set and [deferred] for the Held-Out Set, ensuring variation in sequence length and tool types (FR-001).
- **Integrity**: Per Constitution Principle VI, the generator will log exact tool sequences and argument variances to `data/raw/logs/trace_integrity.log` to ensure trace structural integrity.

### Structural Diversity for Held-Out Set
To address the concern that the Held-Out Set might be too similar to the Training Set (leading to constant-zero fidelity loss):
- **Strategy**: The Held-Out Set is generated using a **different random seed** and a **perturbed distribution**. Specifically, the generator will apply a `variance_multiplier` (e.g., 1.5x) to the sequence length and tool repetition parameters for the Held-Out Set.
- **Rationale**: This ensures the Held-Out Set contains traces with higher structural complexity and diversity than the Training Set. This deliberate perturbation guarantees that the `Edit Accuracy` difference (outcome variable) will exhibit sufficient variance for meaningful correlation analysis, avoiding a degenerate case where all traces have identical fidelity loss.
- **Artifact**: `data/processed/validation_proxy.json` (if proxy exists) or a log entry documenting the perturbation parameters.

### External Validation Proxy (T000)
To address construct validity concerns regarding synthetic data:
- **Strategy**: Attempt to validate the synthetic distribution against a small, verified proxy dataset (e.g., a subset of a public tool-use dataset if available).
- **Outcome**: If a proxy is unavailable, the project will explicitly document this limitation and frame all results as "Internal Validity" based on the synthetic generation logic.
- **Artifact**: `data/processed/validation_proxy.json`.

## Methodology

### 1. Structural Metric Extraction (FR-002)
For each generated trace (both Training and Held-Out), the system will compute:
- **Sequence Entropy**: Measure of unpredictability in the tool call sequence.
- **Tool-Repetition Frequency**: Count of repeated tool calls within a session.
- **Argument Semantic Variance**: Variance in the semantic embeddings of tool arguments (using a lightweight embedding model or hash-based approximation if full embeddings exceed memory).

*Statistical Rigor*: These metrics are descriptive statistics. No hypothesis testing is performed at this stage.

### 2. Rule Induction (FR-003) - Two-Stage Design
To avoid circular dependencies, the rule induction and fidelity measurement are strictly separated:
1.  **Training Phase**: A **CPU-tractable rule-induction model** (Decision Tree Classifier) is trained on the **Training Set**. The target is to predict the final slide state (or sequence of edits) from the structural metrics.
2.  **Evaluation Phase**: The induced rules are **applied to the Held-Out Set**. The "Compressed Agent" executes these rules to generate edits for new, unseen revision requests.
3.  **Fidelity Loss**: The "Compressed Accuracy" is measured against the ground truth of the **Held-Out Set** tasks. This ensures the fidelity loss is an emergent property of the trace structure's compressibility on unseen data, not a reconstruction artifact of the training data.

*Feasibility*: Decision Trees are well-known to run efficiently on CPU for datasets of this scale.

### 3. Benchmarking & Fidelity Analysis (FR-004, FR-005)
- **Baseline**: A reference agent using raw memory (retrieval of full traces) is run on the **Held-Out Set**.
- **Compressed**: The agent using the induced symbolic rule bank is run on the **Held-Out Set**.
- **Metrics**:
  - **Edit Accuracy**: Fraction of edits matching ground truth (measured on Held-Out tasks).
  - **Retrieval Latency**: Time to context-ready.
- **Comparison**: Both agents will be evaluated on the **Held-Out Set** to ensure independence from the training process.

### 4. Correlation & Sensitivity Analysis (FR-006, FR-007)
- **Correlation (FR-006)**: A **Multiple Linear Regression** is performed (per Constitution Principle VII) to correlate structural metrics (predictors) with the `accuracy_diff` (Baseline - Compressed) outcome.
  - *Dataset*: The regression uses the **Held-Out Set** exclusively to ensure predictors and outcome are independent of the rule induction training.
  - *Assumptions*: If linearity or normality assumptions are violated, the plan switches to **Spearman Correlation** as a fallback, documented in the report.
  - *Multiple Comparisons*: If multiple metrics are tested, a Bonferroni correction will be applied.
- **Sensitivity (FR-007)**: A sweep over the **compression_threshold** parameter will be performed to report how fidelity rates vary.
  - *Correction*: `compression_ratio` is a **derived outcome**, not an independent variable in the sweep. The sweep varies the threshold to observe changes in fidelity rates. The sensitivity report will list `threshold`, `fidelity_rate`, and `compression_ratio` (derived).

## Statistical Rigor & Assumptions

- **Sample Size**: The synthetic dataset size is [deferred]. A power analysis will be conducted in the implementation phase to determine the minimum N required to detect a significant correlation (assuming a medium effect size). If N is insufficient, the limitation will be explicitly stated.
- **Causal Claims**: No causal claims will be made. The analysis is associational: "Structural property X is correlated with compressibility."
- **Measurement Validity**: The structural metrics (entropy, repetition, variance) are assumed to be sufficient proxies for "structural properties" (Assumption A4).
- **Collinearity**: If predictors (e.g., entropy and repetition) are definitionally related, their independent effects will not be claimed; instead, the relationship will be reported descriptively.
- **Multiple Comparisons**: Corrected via Bonferroni or False Discovery Rate (FDR) if multiple metrics are tested.

## Compute Feasibility (CPU-First)

- **Method Selection**: All methods (Decision Tree, Multiple Linear Regression) are CPU-tractable. No GPU is required.
- **Resource Constraints**: The pipeline is designed to run on a GitHub Actions free-tier runner (2 CPU, ~7 GB RAM).
- **Data Streaming**: If the synthetic dataset exceeds memory, `pandas` will be used with chunking or `datasets` library with streaming enabled.
- **No Fabrication**: No synthetic stand-ins for GPU work are planned, as no GPU work is required.

## Decision/Rationale

| Decision | Rationale |
| :--- | :--- |
| **Synthetic Data** | No verified public dataset exists for MemSlides traces. Synthetic generation is the only feasible, non-fabricated approach. |
| **Perturbed Held-Out Set** | Ensures structural diversity and variance in the outcome variable (fidelity loss), preventing degenerate correlation results. |
| **Two-Stage Design** | Separates rule induction (Training Set) from fidelity measurement (Held-Out Set) to avoid circular dependency and ensure scientific validity. |
| **Decision Tree** | CPU-tractable, interpretable, and suitable for rule induction. Fits within memory constraints. |
| **Multiple Linear Regression** | Mandated by Constitution Principle VII. Fallback to Spearman if assumptions fail. |
| **Sweep Compression Threshold** | Directly addresses FR-007. `compression_ratio` is an outcome, not a sweep variable. |
| **No GPU** | The chosen methods do not require GPU acceleration. CPU-first approach ensures CI feasibility. |