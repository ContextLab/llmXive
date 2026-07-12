# Research: llmXive follow-up: extending "From Chatbot to Digital Colleague"

## Executive Summary

This research investigates the "tipping point" where increasing library size in a "Digital Colleague" agent leads to retrieval noise that degrades task success. We utilize a synthetic environment to control semantic overlap and ground-truth validity, allowing for causal inference regarding the interaction between library size, redundancy, and pruning interventions. The study is designed to run entirely on CPU-constrained CI infrastructure.

**Methodological Correction**: To address statistical validity concerns with discrete predictors, this study replaces the originally proposed Piecewise Linear Regression with **Logistic Regression with a Quadratic Term** (and categorical factors) to model the non-linear decline in success rates.

## Dataset Strategy

Since this project relies on a **synthetic dataset** generated programmatically, no external URL is required. The data generation process is the source of truth.

| Dataset Name | Source/Loader | Variables | Validation Status |
|--------------|---------------|-----------|-------------------|
| Synthetic Tasks | `code/generate_data.py` | `task_id`, `description`, `ground_truth_path` (list of skill_ids), `complexity` | Generated internally; ground-truth is deterministic and independent of retrieval (dual-seed mechanism). |
| Synthetic Skills | `code/generate_data.py` | `skill_id`, `code_snippet`, `embedding_vector`, `semantic_group` | Generated internally; overlap controlled via cosine similarity constraints. |
| Experiment Logs | `code/agent.py` | `run_id`, `task_id`, `library_size`, `pruning_enabled`, `execution_success`, `retrieval_precision`, `pruning_risk_count` | Logged during execution; validated against `contracts/experiment_log.schema.yaml`. |

**Dataset-variable fit**: The synthetic generator explicitly constructs every variable required for the analysis (task complexity, skill overlap, ground-truth paths). There are no missing variables.

## Methodology

### 1. Pilot Study (New Phase)
Before the full experiment, a **Pilot Study** with 50 tasks will be executed across all library sizes.
- **Purpose**: Estimate variance and effect size to confirm the 500-task sample size is sufficient.
- **Action**: If the pilot shows ceiling effects (success rate > 95%) or floor effects (< 5%), task complexity parameters (e.g., number of steps, semantic noise) will be adjusted before the full run.
- **Outcome**: Validated parameters for the main experiment.

### 2. Data Generation (FR-001, FR-002)
- **Task Generation**: A set of tasks is generated. Each task is a multi-step problem requiring several deterministic actions.
- **Skill Library**: A set of Python functions is generated. Embeddings are created using `sentence-transformers/all-MiniLM-L6-v2` (CPU).
- **Overlap Control**:
  - **Low**: Mean pairwise cosine similarity < 0.30.
 - **Medium**: Mean > 0.50, of pairs > 0.50.
 - **High**: Mean > 0.80, of pairs > 0.80.
- **Ground Truth Independence**: Two distinct random seeds are used. Seed A generates the skill embeddings. Seed B assigns the ground-truth solution paths. This ensures no correlation between the retrieval space and the solution space.

### 3. Agent Execution (FR-003, FR-006)
- **Configurations**: Library sizes of, 30, 50, 100.
- **Retrieval**: Top-k (k=5) skills retrieved via cosine similarity.
- **Execution**: The agent attempts to execute the retrieved code snippets.
- **Metrics Recorded**:
  - **Execution Fidelity**: Binary (1 if retrieved code runs without error and matches expected output, 0 otherwise). **This is the primary outcome metric, distinct from retrieval precision.**
  - **Retrieval Precision**: Jaccard similarity between retrieved set and ground-truth set. (Secondary diagnostic metric).
  - **Retrieval Diversity**: Inverse variance of cosine similarities of top-k skills.
  - **Latency/Token Usage**: Measured per task.
  - **Pruning Risk Count**: Number of skills pruned that had high similarity to ground-truth skills (indicating potential harm).

### 4. Safe Pruning Intervention (FR-004, US-3)
- **Heuristic**: After a periodic interval of tasks, scan library.
- **Logic**: Remove skill if `usage_count == 0` AND `min_cosine_similarity_to_any_other_skill < 0.70`.
- **Risk Logging**: If a removed skill has a high cosine similarity (> 0.85) to any skill in the *ground-truth path of a recent task*, increment `pruning_risk_count`.
- **Analysis Strategy**: Instead of treating Pruning as an independent variable, the analysis will stratify results by `pruning_risk_count` to account for the causal entanglement where noise triggers pruning of useful skills.

### 5. Statistical Analysis (Corrected Methodology)
- **Tipping Point Detection**: **Logistic Regression** with `execution_success` as the dependent variable.
  - **Predictors**: `library_size` (categorical), `library_size^2` (quadratic term), `pruning_enabled` (binary), `pruning_risk_count` (continuous).
  - **Rationale**: Piecewise Linear Regression is invalid for 4 discrete points. Logistic regression with a quadratic term captures the non-linear decline (tipping point) appropriate for discrete experimental levels.
- **Collinearity Check**: Calculate Variance Inflation Factor (VIF) for predictors.
- **Significance**: P-values reported for the effect of pruning and library size on Execution Fidelity.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: If multiple statistical tests are run (e.g., for each library size), a Bonferroni correction or False Discovery Rate (FDR) control will be applied to the p-values.
- **Power Justification**: The sample size is determined by the Pilot Study variance estimates. If the pilot indicates low variance, the sample size is sufficient for medium effect sizes. If variance is high, the complexity parameters are adjusted to increase effect size before the full run.
- **Causal Inference**: Because the environment is synthetic and tasks are randomly assigned to library configurations, the study supports **causal claims** regarding the effect of library size and pruning *within the simulation*. Generalization to real-world chaotic environments remains **associational**.
- **Measurement Validity**: `sentence-transformers` embeddings are used as a proxy for semantic overlap. **Execution Fidelity** is validated against the deterministic ground-truth output, not just the retrieval set.
- **Collinearity**: "Library size" and "semantic overlap" are treated as distinct factors. If they become correlated (e.g., larger libraries naturally drift to higher overlap), the VIF diagnostic will flag this. If VIF > 5.0, the model will be adjusted or the interpretation qualified.

## Compute Feasibility

- **Memory**: The dataset (a set of tasks, 100 skills) is small. Embeddings (a set of vectors with a moderate dimensionality) are negligible. The primary memory load is the Python process and `sentence-transformers` model (~100MB). Total RAM usage expected < 2 GB.
- **CPU**: Embedding a representative set of skills once, then executing a larger batch of tasks (or retrieving from cache) is trivial for 2 vCPU. The bottleneck is the agent execution loop, which is deterministic and fast.
- **Time**: Estimated runtime < 2 hours for full experiment, well within the CI limit.
- **No GPU**: `sentence-transformers` is configured to run on CPU. No CUDA dependencies.

## Decision Log

| Decision | Rationale | Alternative Rejected |
|----------|-----------|----------------------|
| **Synthetic Data** | Allows precise control over overlap and ground truth, impossible with real-world data. | Real-world datasets lack ground-truth "solution paths" for multi-step code tasks. |
| **Logistic Regression (Quadratic)** | Statistically valid for discrete predictors (10, 30, 50, 100) and models non-linear decline. | Piecewise Linear Regression is underpowered and produces artifact breakpoints on sparse data. |
| **Execution Fidelity Metric** | Measures actual task success (code execution) independent of retrieval set. | Retrieval Precision alone is circular and confounded with the retrieval mechanism. |
| **Safe Pruning with Risk Logging** | Acknowledges the causal entanglement of pruning and noise; allows stratified analysis. | Blind pruning treats the intervention as independent, which is methodologically unsound. |
| **CPU-only `sentence-transformers`** | Ensures compatibility with GitHub Actions free tier. | GPU-accelerated models are unnecessary for 100-500 vectors and would violate constraints. |
| **Pilot Study** | Ensures sample size is adequate for observed variance, avoiding ceiling/floor effects. | Fixed 500-task run without pilot risks being underpowered or uninformative. |