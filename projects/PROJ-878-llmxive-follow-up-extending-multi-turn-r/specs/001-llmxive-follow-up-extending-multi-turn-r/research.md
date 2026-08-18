# Research: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

## Research Question

How does the topological complexity (specifically `nesting_depth` and `branching_factor`) of logical dependency graphs influence the convergence speed and success rate of the Reflective Masking (RM) inference loop in Mask Diffusion Models?

## Theoretical Background

The "Multi-Turn Reflective Masking" paper posits that iterative masking can elicit reasoning in diffusion models. This study hypothesizes that there is a **non-linear degradation** in performance as the topological complexity of the problem increases. Specifically, we anticipate a "tipping point" in `nesting_depth` beyond which the RM loop fails to converge within a bounded number of turns, or converges significantly slower.

## Dataset Strategy

### Primary Data Source: Synthetic Generation with Orthogonalization
The study requires explicit control over `nesting_depth` and `branching_factor`. No existing public dataset provides logical puzzles with these specific, verified topological metrics attached to every instance. Therefore, we will generate a synthetic dataset with a **Stratified Orthogonalization** strategy to decouple these variables.

**Generation Strategy**:
1. **Seed Structure**: Use the GSM8K dataset structure as a *conceptual* seed for problem types (mathematical/logical deduction), but **do not** use GSM8K data directly for the analysis.
2. **Graph Construction**: For each instance, generate a Directed Acyclic Graph (DAG) where:
 * Nodes represent logical propositions/steps.
 * Edges represent dependency relations.
 * `nesting_depth` = Length of the longest path (DAG diameter).
 * `branching_factor` = Average in-degree of non-root nodes.
3. **Stratified Orthogonalization**:
 * Define a target grid of (depth, branching) pairs.
 * Sample pairs such that the correlation between `nesting_depth` and `branching_factor` in the final dataset is < 0.2.
 * If a random sample creates high collinearity, reject and resample until the orthogonality constraint is met.
4. **Deterministic Text Construction**:
 * Do NOT use an LLM to generate the puzzle text.
 * Use a **Template Engine** that maps the DAG structure directly to a formal logical template (e.g., "If A then B; If B then C...").
 * This ensures the natural language prompt is a strict isomorphism of the graph, eliminating stochastic ambiguity in the ground truth.
5. **Validation**: Enforce acyclicity and solvability (unique ground-truth path) before inclusion.

**Verified Datasets (for reference/seed only)**:
* **GSM8K**: Used only for structural inspiration, not direct data consumption.
 * Source: `
 * *Note*: We do not cite this as the analysis dataset. The analysis dataset is the locally generated synthetic JSONL.

### Data Feasibility
* **Size**: 500 instances (small enough for full RAM processing, large enough for statistical significance).
* **Format**: JSONL (streamable, easy to parse).
* **Download**: N/A (Generated locally).

## Methodology

### Phase 1: Synthetic Data Generation with Orthogonalization
1. Implement `graph_generator.py` using `networkx`.
2. Algorithm:
 * Initialize empty DAG.
 * **Stratified Sampling**: Select (depth, branching) pairs from a grid to ensure low correlation (|r| < 0.2).
 * Construct layers to satisfy depth `d`.
 * Add edges to satisfy branching factor `b` while maintaining acyclicity.
 * **Deterministic Text Generation**: Instantiate a formal logic template with node labels and edge dependencies. No LLM generation.
 * Select a valid ground-truth path (randomized path perturbation) to avoid tautological validation.
 * **Output**: JSONL with `instance_id`, `text`, `ground_truth`, `nesting_depth`, `branching_factor`, `graph_structure`, `is_orthogonal`.
3. **Validation**: Run `validate_graph.py` to ensure acyclicity and solvability. Discard invalid instances.

### Phase 2: CPU-Feasible Execution with Independent Validation
1. Load pre-trained Mask Diffusion Model (CPU-only).
2. Implement `rm_executor.py` with the Reflective Masking loop:
 * Input: Puzzle text.
 * Loop: Mask -> Predict -> Unmask -> Check Convergence.
 * **Termination**: Max 50 turns (Primary) or 1000 turns (Extended validation subset).
 * **Independent Logical Validator (ILV)**:
 * Parse the model's step-by-step output into a formal logic graph.
 * Verify that the model's path traverses edges present in the original DAG.
 * Calculate `path_coverage` (percentage of model steps matching DAG edges).
 * **Metrics**: `turns_to_converge`, `convergence_status` (success/failure), `path_coverage`, `final_token_sequence`.
3. **Batching**: Process in small batches to stay within ~7 GB RAM.
4. **Output**: `results/execution_log.csv`.

### Phase 3: Statistical Analysis with Survival Methods
1. **Survival Analysis**: Use **Cox Proportional Hazards (Cox PH)** models to analyze the relationship between topological metrics and convergence time.
 * **Event**: Convergence (Success).
 * **Censoring**: Instances hitting the turn limit (50/1000) are treated as right-censored data, not numerical values.
 * This prevents bias in correlation estimates caused by censored data.
 * *Note on Spearman*: While FR-004 requires a Spearman correlation, it is calculated only as a descriptive statistic. It is **not** used for primary inference because standard correlation is invalid for heavily censored data (where many values are capped at 50), which would bias the coefficient towards zero.
2. **Tipping Point Detection**: Implement **Segmented Regression (Piecewise Linear Regression)** to identify the specific `nesting_depth` where the hazard ratio or slope of convergence time changes significantly.
3. **Sensitivity Analysis**: Re-evaluate failure rates at varying thresholds.
4. **Extended Budget Analysis**: Compare 50-turn failures vs. 1000-turn convergences to quantify "budget exhaustion" vs. "reasoning failure."

## Statistical Rigor & Constraints

* **Multiple Comparisons**: We will run multiple tests (depth vs. hazard, branching vs. hazard). We will apply a Bonferroni correction or report family-wise error rate where applicable.
* **Power Analysis**: With N=500, we have sufficient power to detect moderate effect sizes in survival analysis (Hazard Ratio > 1.5) at p < 0.05. The specific power calculation will be deferred to the analysis script (`[deferred]`).
* **Causal Inference**: This is an observational study on synthetic data. We control the independent variables (topology) but the model's behavior is stochastic. Claims will be framed as associational (correlation) unless the synthetic nature allows for a causal interpretation of the *structural* effect.
* **Measurement Validity**: `nesting_depth` and `branching_factor` are mathematically defined and explicitly calculated from the generated graph. The text is a deterministic mapping of the graph, ensuring high validity.
* **Collinearity**: The generation process explicitly enforces orthogonality (|r| < 0.2) between `nesting_depth` and `branching_factor`. We will verify this in the dataset before analysis.
* **Censored Data Handling**: All convergence time analyses will use Survival Analysis (Cox PH) to properly handle right-censored data (instances hitting the turn limit).

## Compute Feasibility (CPU-First)

* **Model**: Pre-trained Mask Diffusion Model (CPU-optimized).
* **Hardware**: GitHub Actions Free Tier (2 CPU, ~7 GB RAM).
* **Strategy**:
 * Use `torch` with `device="cpu"`.
 * Do NOT use 8-bit quantization (requires CUDA kernels).
 * Stream data generation and processing to avoid loading 500 full graphs into memory simultaneously if needed (though 500 small graphs will likely fit).
 * **GPU Escape Hatch**: If the model *strictly* requires CUDA (e.g., specific kernel dependencies), we will scale down to a subset (N=50) and use the Kaggle GPU offload mechanism. However, the plan assumes a CPU-tractable form exists as per the spec's "CPU-only" constraint.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Model OOM on CPU** | High | Use smaller batch sizes; stream data; if impossible, reduce N to a feasible sample size. |
| **Infinite Loop** | High | Hard turn limit (50/1000) enforced in code. |
| **Invalid Graphs** | Medium | Strict validation loop; discard and regenerate until 500 valid instances are collected. |
| **No Convergence** | Medium | Record as "failure" (censored); analyze using Survival Analysis. |
| **High Collinearity** | High | Generation algorithm enforces orthogonal sampling; if correlation > 0.2, regenerate. |
| **Stochastic Text Ambiguity** | High | Deterministic Template Engine ensures strict isomorphism between text and graph. |
| **String Matching Bias** | High | ILV validates logical path traversal, not just final string. |