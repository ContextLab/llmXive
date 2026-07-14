# Research: llmXive follow-up: extending "Where Do Deep-Research Agents Go Wrong? Span-Level Error Localization"

## Problem Statement
Deep-research agents often fail due to "collapse" in their reasoning process. This study investigates whether early-stage topological signatures (specifically low connectivity) in the claim-dependency graph of a trajectory can predict this collapse before the final outcome is known. The hypothesis is that successful trajectories exhibit higher structural interdependence in their early reasoning spans compared to those that eventually fail.

## Dataset Strategy

### Verified Datasets
The following datasets are used, citing only the verified URLs provided in the project context:

| Dataset Name | Description | Verified URL | Usage |
|:--- |:--- |:--- |:--- |
| **TELBench** | Collection of annotated deep-research trajectories with success/failure labels. | ` | Primary source of trajectories, spans, and ground-truth labels. |

*Note: The other URLs listed in the project context (DAG, F1-score benchmarks) are not used for this specific analysis as they do not contain the raw trajectory text required for graph construction. This study relies exclusively on TELBench.*

### Dataset Variable Fit
* **Required Variables**: Semantic spans (text), trajectory ID, final success/failure label.
* **Availability**: TELBench contains these fields.
* **Gap Analysis**: The study requires "co-reference and citation logic" to be inferred from text. TELBench provides the raw text. The plan does **not** rely on pre-labeled error spans for graph construction (Constitution Principle VI), ensuring the dataset fit is valid for the *predictor* variables. The *target* variable (success/failure) is available for validation.

## Methodology

### 1. Graph Construction (Independent of Ground Truth)
* **Input**: First [deferred]% of semantic spans from a trajectory.
* **Logic**:
 * Nodes: Individual semantic claims.
 * Edges: Inferred via textual co-reference and explicit citations.
 * **Implementation**: Uses `spaCy` (dependency parsing and pronoun resolution) and regex for explicit citations (e.g., "[1]"). This replaces vague "regex" with a standard, CPU-tractable NLP library.
 * **Constraint**: No use of ground-truth error annotations during this phase.
* **Construct Validity Note**: Since edge detection relies on heuristics, the study will perform a manual spot-check of 50 graphs to estimate edge detection accuracy. If accuracy is low, the "Connectivity" metric will be framed as a "heuristic proxy" rather than a ground-truth structural measure.
* **Output**: Directed Acyclic Graph (DAG) per trajectory.

### 2. Topological Metrics
* **Global Connectivity**: $\frac{\text{actual edges}}{\text{possible edges}}$. Normalized measure of graph density.
* **Collinearity Handling**: Branching Factor and Connectivity are linearly dependent for a fixed node count. To avoid multicollinearity, the study will use **Global Connectivity** as the primary predictor. If multivariate analysis is required, PCA will be applied to raw graph statistics before modeling.
* **Normalization**: The metric is divided by node count to ensure it measures *structure* rather than *volume*.

### 3. Prediction & Validation
* **Threshold Selection**: The threshold is **not** a fixed percentile of the success class (which creates circular logic). Instead, the threshold is determined by maximizing the **F1-score** (or Youden's J statistic) on the **validation split** ([deferred] of data). This ensures the cutoff is data-driven based on the separation of the success and failure distributions.
 * *Rationale*: This avoids the "self-fulfilling prophecy" where the threshold is defined by the positive class alone. It tests whether the distributions actually overlap or are distinct.
* **Evaluation**:
 * Compare predicted "Collapse" (metric < threshold) vs. Actual "Failure" on the **test split** ([deferred] of data).
 * Metrics: Precision, Recall, F1-score.
 * Significance: Pearson/Spearman correlation between early connectivity and final outcome (p < 0.05).
* **Null Hypothesis Testing**: A **permutation test** (shuffling labels 1000 times) will be performed to generate a null distribution of the correlation coefficient. The observed correlation must significantly exceed this null distribution to claim a non-trivial relationship.
* **Power Analysis**: A post-hoc power analysis will be conducted using the effect size (Cohen's d) from the training split. If power < 0.8, the study will explicitly report this limitation and interpret non-significant results with caution.
* **Sensitivity Analysis**: Thresholds swept at {0.01, 0.05, 0.1} and percentiles at {10, 20, 30} to ensure robustness (SC-004). Results will be reported as a full table, and the "best" threshold will be selected based on the highest F1-score on the validation set.

## Statistical Rigor & Assumptions

* **Multiple Comparisons**: If multiple metrics were tested independently, a Bonferroni correction would be applied. However, due to collinearity, only the primary metric (Global Connectivity) is tested, mitigating this risk.
* **Power Analysis**: As noted, a formal post-hoc power analysis is included. This addresses the risk of Type II errors.
* **Causal Inference**: The study uses observational data. No randomization of topological structures exists. **All claims are framed as associational.** We do not claim low connectivity *causes* collapse, but that it is a *predictive signature*.
* **Measurement Validity**: The validity of "co-reference" detection relies on `spaCy` heuristics. This is a limitation acknowledged in the discussion, and a manual spot-check is performed to quantify it.
* **Collinearity**: Branching Factor and Connectivity are mathematically related. The study uses only Global Connectivity as the primary predictor to avoid multicollinearity issues in significance testing.

## Decision Rationale (Compute Feasibility)

* **CPU-Only**: The plan explicitly avoids LLM-based co-reference resolution in favor of `spaCy` (CPU mode) and deterministic regex. This ensures the pipeline runs within the 6-hour GitHub Actions limit on 2 CPU cores.
* **Sampling**: If the full TELBench dataset exceeds memory, the pipeline will process trajectories in batches, writing intermediate results to disk, ensuring < 7 GB RAM usage.
* **Library Choice**: `networkx` is used for graph algorithms as it is pure Python/C and highly optimized for small-to-medium graphs (typical of reasoning trajectories). `spaCy`'s `en_core_web_sm` model is lightweight and CPU-tractable.