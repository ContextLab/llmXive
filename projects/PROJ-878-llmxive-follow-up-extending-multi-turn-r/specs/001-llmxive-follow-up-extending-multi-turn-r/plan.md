# Implementation Plan: llmXive follow-up: extending "Multi-Turn Reflective Masking Elicits Reasoning in Mask Diffusion Mode"

**Branch**: `001-llmxive-topological-limits` | **Date**: 2026-08-18 | **Spec**: `specs/001-llmxive-topological-limits/spec.md`
**Input**: Feature specification from `/specs/001-llmxive-topological-limits/spec.md`

## Summary

This feature implements a controlled empirical study to investigate the relationship between the topological complexity of logical dependency graphs (specifically `nesting_depth` and `branching_factor`) and the convergence behavior of the Reflective Masking (RM) inference loop in Mask Diffusion Models. The plan involves: (1) generating a synthetic dataset of logical puzzles with explicit, verified topological metadata derived from directed acyclic graphs (DAGs) using a **Deterministic Template Engine** and **Stratified Orthogonalization**; (2) executing the RM loop on a CPU-only environment with a bounded turn limit, validated by an **Independent Logical Validator (ILV)** that checks logical path traversal rather than string matching; and (3) performing **Survival Analysis (Cox Proportional Hazards)** and **Segmented Regression** to identify non-linear degradation patterns and "tipping points," explicitly handling censored data.

## Technical Context

**Language/Version**: Python 3.11  
**Primary Dependencies**: `torch` (CPU-only), `transformers`, `datasets` (Hugging Face), `networkx` (graph generation/analysis), `lifelines` (Survival Analysis), `scikit-learn` (Segmented Regression), `pandas`, `numpy`, `pytest`  
**Storage**: Local filesystem (`data/` for generated JSONL, `results/` for logs); no external database.  
**Testing**: `pytest` (unit tests for graph generation, integration tests for RM loop + ILV, contract tests for schema validation).  
**Target Platform**: Linux (GitHub Actions free-tier runner: standard CPU allocation, standard RAM, and sufficient disk space for typical CI/CD workflows (e.g., source code, dependencies, and build artifacts).).  
**Performance Goals**: Complete generation of 500 instances in <30 mins; complete RM execution on 500 instances in <6 hours on CPU.  
**Constraints**: CPU-only execution (no CUDA); strict memory limits; hard turn limit for primary runs (a defined threshold); extended validation subset (sufficiently large to ensure statistical robustness).  
**Scale/Scope**: synthetic logical puzzle instances; pre-trained Mask Diffusion Model (CPU-loaded).

> **Note on Dataset**: The GSM8K dataset is used *only* as a structural seed for the synthetic generator. The mathematical content is replaced by synthetic logical deduction problems to ensure topological control. The original GSM8K answers are not used for validation.

## Constitution Check

*Gates determined based on `constitution.md`*

| Principle | Status | Verification / Action |
|-----------|--------|-----------------------|
| **I. Reproducibility** | **Pass** | Random seeds pinned in `code/generate.py` and `code/execute.py`. `requirements.txt` will pin all versions. |
| **II. Verified Accuracy** | **Pass** | Citations to "Multi-Turn Reflective Masking" paper and GSM8K will be validated against primary sources. |
| **III. Data Hygiene** | **Pass** | Generated `data/` files will be checksummed. No in-place modifications; derivations written to new files. |
| **IV. Single Source of Truth** | **Pass** | All statistics in `paper/` will be derived programmatically from `data/results.csv`. |
| **V. Versioning Discipline** | **Pass** | Content hashes for `data/` and `code/` will be recorded in `state/` upon artifact write. |
| **VI. Topological Metric Traceability** | **Pass** | `nesting_depth` and `branching_factor` will be calculated by `networkx` and stored explicitly in `data/` for every instance. |
| **VII. Synthetic Graph Construction Integrity** | **Pass** | Generation script will log exact seeds and parameters; DAG validity (acyclic, solvable) will be enforced before inclusion. |

## Project Structure

### Documentation (this feature)

```text
specs/001-llmxive-topological-limits/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
projects/PROJ-878-llmxive-follow-up-extending-multi-turn-r/
├── data/
│   ├── raw/             # Generated synthetic dataset (JSONL)
│   ├── processed/       # Execution logs (CSV/JSON)
│   └── checksums.txt    # SHA-256 hashes
├── code/
│   ├── __init__.py
│   ├── requirements.txt
│   ├── graph_generator.py    # Synthetic data generation (FR-001, FR-006, FR-007)
│   ├── rm_executor.py        # Reflective Masking execution + ILV (FR-002, FR-003, FR-008)
│   ├── analyzer.py           # Statistical analysis (Cox PH, Segmented Regression) (FR-004, FR-005)
│   └── utils/
│       ├── graph_utils.py    # DAG validation, metric calculation, ILV logic
│       └── logging_utils.py
├── tests/
│   ├── test_graph_generator.py
│   ├── test_rm_executor.py
│   └── test_analyzer.py
└── results/
    └── paper_figures/
```

**Structure Decision**: Single project structure selected. The workflow is linear (Generate -> Execute -> Analyze), making a monolithic `code/` directory with modular scripts the most efficient pattern for a research pipeline. No separate backend/frontend is required.

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| **Synthetic Data Generation** | Required to control `nesting_depth` and `branching_factor` explicitly. | Real-world datasets (GSM8K) do not have controlled, explicit topological metadata for logical dependency graphs; using them would introduce confounding variables. |
| **CPU-Only Constraint** | Mandatory for CI feasibility (free-tier runner). | GPU execution is not available on the target CI environment; planning for GPU would result in immediate failure or require a complex offload mechanism not yet established for this specific CPU-bound research loop. |
| **Extended Budget Run (Extended duration)

The specific value to remove/generalize: 'Extended duration'

Rewritten passage:
Extended Budget Run (Extended duration)

The research question investigates the long-term stability of the system under sustained computational load. The method involves conducting a simulation with a significantly extended number of turns to observe emergent behaviors over time. References: [Citation preserved verbatim].** | Required to distinguish budget exhaustion from reasoning failure (FR-008). | A single 50-turn limit cannot differentiate between "cannot solve" and "needs more time"; the extended run is a necessary diagnostic step. |
| **Survival Analysis (Cox PH)** | Required to handle censored data (turn limits). | Standard correlation (Spearman/Pearson) is invalid for censored data as it treats the cap as a true value, biasing results. |
| **Independent Logical Validator (ILV)** | Required to verify reasoning, not just string matching. | String matching allows the model to converge on the solution string without traversing the logical graph, invalidating the correlation with topology. |
| **Stratified Orthogonalization** | Required to decouple `nesting_depth` and `branching_factor`. | Random generation often couples these variables (e.g., high depth implies low branching), making it impossible to isolate their individual effects on convergence. |

## Methodology

### Phase 1: Synthetic Data Generation with Stratified Orthogonalization
1.  **Algorithm**: Implement `graph_generator.py` using `networkx`.
2.  **Stratified Orthogonalization**:
    *   Define a target grid of (depth, branching) pairs.
    *   **Rejection Sampling**: Generate candidate graphs. Calculate correlation between `nesting_depth` and `branching_factor`. If |r| >= 0.2, reject and resample. This ensures variables are decoupled.
    *   Construct layers to satisfy depth `d` and edges to satisfy branching factor `b` while maintaining acyclicity.
3.  **Deterministic Text Generation**:
    *   **Mechanism**: Use a **Deterministic Template Engine** (not an LLM) to map the DAG structure directly to a formal logical template (e.g., "If A then B; If B then C...").
    *   **Isomorphism**: The text prompt is a strict isomorphism of the graph. No stochastic ambiguity.
    *   **Ground Truth**: Select a valid ground-truth path (randomized path perturbation) to avoid tautological validation.
4.  **Validation**: Enforce acyclicity and solvability. Discard invalid instances.
5.  **Output**: JSONL with `instance_id`, `text`, `ground_truth_path`, `nesting_depth`, `branching_factor`, `graph_structure`, `is_orthogonal`.

### Phase 2: CPU-Feasible Execution with Independent Logical Validation
1.  **Model**: Load pre-trained Mask Diffusion Model (CPU-only, `device="cpu"`).
2.  **Reflective Masking Loop**:
    *   Input: Puzzle text.
    *   Loop: Mask -> Predict -> Unmask -> Check Convergence.
    *   **Termination**: A maximum turn limit for the primary phase, with a higher limit for the extended validation subset..
3.  **Independent Logical Validator (ILV)**:
    *   **Mechanism**: Parse the model's step-by-step output into a formal logic graph.
    *   **Verification**: Verify that the model's path traverses edges present in the original DAG.
    *   **Metric**: Calculate `path_coverage` (percentage of model steps matching DAG edges).
    *   **Success Criteria**: A run is "success" only if `path_coverage` >= 0.95 AND the final state matches the ground truth logic. String matching alone is insufficient.
4.  **Metrics**: `turns_to_converge` (censored if limit hit), `convergence_status`, `path_coverage`.
5.  **Batching**: Process in small batches to stay within available RAM constraints..
6.  **Output**: `results/execution_log.csv`.

### Phase 3: Statistical Analysis with Survival Methods
1.  **Survival Analysis (Cox Proportional Hazards)**:
    *   **Event**: Convergence (Success).
    *   **Censoring**: Instances hitting the turn limit (50/1000) are treated as **right-censored**, not numerical values.
    *   **Model**: `H(t) = H0(t) * exp(beta_depth * depth + beta_branch * branch)`.
    *   **Reasoning**: This prevents bias in correlation estimates caused by censored data. **Spearman correlation is explicitly excluded** for the primary inference on turn-count data due to censoring, though it is calculated as a descriptive statistic to satisfy FR-004.
2.  **Tipping Point Detection**:
    *   **Method**: **Segmented Regression (Piecewise Linear Regression)** to identify the specific `nesting_depth` where the hazard ratio or slope of convergence time changes significantly.
    *   **Reasoning**: Standard GLM cannot detect structural breaks; piecewise regression is required.
3.  **Sensitivity Analysis**: Re-evaluate failure rates at multiple thresholds of turn counts.
4.  **Extended Budget Analysis**: Compare 50-turn failures vs. 1000-turn convergences to quantify "budget exhaustion" vs. "reasoning failure."

## Statistical Rigor & Constraints

*   **Multiple Comparisons**: Apply Bonferroni correction for multiple tests (depth vs. hazard, branching vs. hazard).
*   **Power Analysis**: With N=500, sufficient power for moderate effect sizes in survival analysis. Specific calculation deferred to script (`[deferred]`).
*   **Causal Inference**: Framed as associational (correlation) unless synthetic nature allows causal interpretation of structural effect.
*   **Measurement Validity**: `nesting_depth` and `branching_factor` are mathematically defined. Text is deterministic mapping.
*   **Collinearity**: Generation enforces orthogonality (|r| < 0.2). Verified in dataset before analysis.
*   **Censored Data Handling**: **All** convergence time analyses use Survival Analysis (Cox PH) to properly handle right-censored data.

## Compute Feasibility (CPU-First)

*   **Model**: Pre-trained Mask Diffusion Model (CPU-optimized).
*   **Hardware**: GitHub Actions Free Tier (CPU, moderate RAM).
*   **Strategy**:
    *   Use `torch` with `device="cpu"`.
    *   Stream data generation and processing.
    *   **GPU Escape Hatch**: If the model strictly requires CUDA, scale down to N=50 and use Kaggle GPU offload.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Model OOM on CPU** | High | Use smaller batch sizes; stream data; reduce N if needed. |
| **Infinite Loop** | High | Hard turn limit (50/1000) enforced. |
| **Invalid Graphs** | Medium | Strict validation loop; discard and regenerate. |
| **No Convergence** | Medium | Record as "failure" (censored); analyze using Survival Analysis. |
| **High Collinearity** | High | Generation algorithm enforces orthogonal sampling; if correlation > 0.2, regenerate. |
| **String Matching Bias** | High | ILV validates logical path traversal, not just final string. |
| **Stochastic Text Ambiguity** | High | Deterministic Template Engine ensures strict isomorphism between text and graph. |