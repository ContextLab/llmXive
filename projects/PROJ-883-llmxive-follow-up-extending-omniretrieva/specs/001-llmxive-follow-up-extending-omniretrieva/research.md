# Research: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Research Objectives

This research aims to validate the hypothesis that "structural mismatch cost" manifests as a non-linear increase in end-to-end latency for high-complexity queries when a retrieval system incorrectly routes a query to a graph-based source (or other mismatched source) under CPU constraints.

**Primary Hypothesis**: The "mismatch cost" (Latency_Router_Selected - Latency_Optimal) scales non-linearly with Query Complexity for graph sources, showing a significant "knee point" (spike) at higher depths.

**Secondary Hypothesis**: Translation error rates (deviation from optimal plan) remain stable or increase slightly, but the *cost* of those errors (latency penalty) is the dominant factor.

## Dataset Strategy

The study utilizes subsets of verified public datasets to construct the heterogeneous environment. No new datasets are invented.

| Dataset Role | Source Name | Verified URL | Usage Strategy |
| :--- | :--- | :--- | :--- |
| **Text Corpus** | MS MARCO | https://huggingface.co/datasets/microsoft/ms_marco/resolve/main/v1.1/test-00000-of-00001.parquet | Used to simulate text retrieval. Subsampled to a representative subset of documents. |
| **Relational Source** | DBpedia (Structured) | https://huggingface.co/datasets/dbpedia/dbpedia_14 | Used to extract schema (tables/columns) and statistics for SQL simulation. |
| **Graph Source** | DBpedia (Structured) | https://huggingface.co/datasets/dbpedia/dbpedia_14 | Used to construct a subgraph of entities and relations for traversal simulation. |
| **Relational Fallback** | Spider Benchmark | https://huggingface.co/datasets/spider | Used ONLY if DBpedia lacks sufficient relational schema depth. |
| **Graph Fallback** | Erdős-Rényi Generator | N/A (Algorithmic) | Used ONLY if DBpedia lacks sufficient graph connectivity. Generates random graphs seeded with DBpedia node counts. |

**Dataset Variable Fit Verification**:
- **Text**: MS MARCO contains `text` and `query` fields sufficient for simulating retrieval latency.
- **Relational/Graph**: The `dbpedia/dbpedia_14` dataset contains structured metadata (subjects, predicates, objects) required to construct the schema for SQL simulation and the adjacency list for Graph simulation. The plan explicitly avoids using the text-classification variant (`fancyzhx/dbpedia_14`) which lacks structural data.
- **Synthetic Query Generation**: The actual query instances are **synthetically generated** based on the schema extracted from the datasets. This ensures exact control over "plan depth" (complexity) which is not present as a field in the raw datasets. The raw datasets provide the *structural constraints* (e.g., join keys, node degrees) necessary for realistic simulation.
- **Fallback Logic**: If `dbpedia/dbpedia_14` lacks sufficient connectivity for depth-4+ graph queries, the system will synthesize a graph using an **Erdős-Rényi** generator (not Spider, which is relational) to preserve the graph modality. Spider is used only as a fallback for relational schema depth.

## Methodology

### 1. Environment Simulation
- **CPU Throttling**: Instead of `RLIMIT_CPU` (which kills the process), the system uses `resource.getrusage` to track CPU time. A "throttled speed" is enforced by introducing a **Virtual Delay** proportional to the CPU time consumed (e.g., if 1s CPU time is used, wait 9s to simulate a 10x slower CPU). This ensures latency measures computational cost, not signal handling overhead.
- **I/O Throttling**: A controlled I/O delay queue is implemented. For every read operation, a fixed delay is added to simulate network/disk latency., satisfying Constitution Principle VI.

### 2. Query Generation (Synthetic)
- Generate 500 queries partitioned by **Exact Plan Depth**: 1, 2, 3, 4+.
- **Ground Truth (CBO)**: A deterministic **Cost-Based Optimizer (CBO)** generates the optimal plan. It uses **actual dataset statistics** (node degree, table cardinality) extracted from the downloaded DBpedia/Spider subsets to calculate the true minimum cost. This ensures independence from synthetic generation parameters.
- **System Under Test (SUT)**: A **Greedy Heuristic with Depth-Limited Lookahead (Depth=2)** and **randomized tie-breaking** generates the plan.
 - **Rationale**: With a lookahead of 2, the SUT can successfully solve queries of depth 1 and 2 (matching the Ground Truth), establishing a valid baseline error rate of [deferred] for low complexity. Errors occur at depth 3+ where the lookahead is insufficient. This creates a non-trivial distribution of errors (not [deferred] failure) to validate SC-002.
- **Router Simulation**: A "Router" component selects the source type for execution.
  - The Router uses a **Noisy Cost Estimate** (CBO Cost + Gaussian Noise) to select a source.
  - For a subset of queries, the Router will select a **Mismatched Source** (e.g., routing a Text query to the Graph engine) due to the noise.
  - **Mismatch Cost**: Calculated as `Latency_Router_Selected - Latency_Optimal` for the *same* query execution flow. This isolates the penalty of the routing decision itself, not just engine speed.

### 3. Execution Loop
- For each query:
  1. **Route**: Router selects a source type based on Noisy Cost Estimate.
  2. **Execute (Selected)**: Measure wall-clock time (latency_ms) under CPU/I/O throttling.
  3. **Execute (Optimal)**: Measure wall-clock time for the Optimal Source (calculated by CBO) for the same query.
  4. **Compare**: Compare Router's plan vs. CBO plan (Translation Error).
  5. **Calculate Cost**: `Delta_Latency = Latency_Selected - Latency_Optimal`.
  6. **Log**: Record `query_id`, `source_type`, `complexity_level`, `latency_ms`, `mismatch_flag`, `delta_latency`.

### 4. Statistical Analysis
- **Non-Linearity Test**: Perform **Segmented Regression** (Piecewise Linear Fit) on `Delta_Latency` vs. `Complexity` for Graph sources. Identify the "knee point" (spike) and compare the slope before and after. This directly tests the "non-linear" hypothesis.
- **Polynomial Regression**: Perform a secondary check using polynomial terms to confirm curvature.
- **Group Differences**: Perform **Two-Way ANOVA** on `Delta_Latency` with factors `Complexity` and `Source_Type`.
- **Post-Hoc**: **Tukey HSD** to identify specific pairwise differences between source types and complexity levels.
- **Sensitivity**: Sweep complexity cutoffs (2, 3, 4) to find "spike points".

## Decision Rationale & Risks

**Why Synthetic Queries?**
Real-world datasets do not have a labeled "plan depth" or "execution complexity" field. To rigorously test the non-linear scaling hypothesis, we must control the independent variable (complexity) exactly. Synthetic generation based on real schemas ensures validity while allowing experimental control.

**Why CBO vs. Heuristic?**
If the SUT used the same logic as the Ground Truth, the "Translation Error" would be [deferred] by definition. By defining the SUT as a "Greedy Heuristic with Depth=2" and the CBO as "Full Lookahead", we ensure the error metric is a valid measure of sub-optimality that is not tautologically [deferred] for all non-trivial queries.

**Why Segmented Regression?**
With only 4 discrete complexity levels, standard ANOVA cannot distinguish between linear and non-linear trends. Segmented Regression explicitly tests for a "knee point" (structural mismatch cost spike), which is the core hypothesis.

**Risk: Dataset Mismatch**
If the DBpedia subset lacks sufficient connectivity for depth-4+ graph queries, the simulation will fail.
*Mitigation*: The graph construction algorithm will synthesize a graph using an **Erdős-Rényi** generator (seeded with DBpedia node counts) if the raw data is sparse, ensuring the structural depth required for the experiment exists. (Spider is used only for Relational fallback).

**Risk: CPU Throttling Failure**
If `resource.getrusage` is unavailable (e.g., non-Linux), latency measurements are invalid.
*Mitigation*: The `main.py` script will perform a pre-flight check. If throttling cannot be enforced, the run aborts with error code 1.

**Compute Feasibility**
- **Memory**: All data is subsampled (<500MB). Graphs are kept in memory (NetworkX) but pruned to relevant subgraphs.
- **Time**: 500 queries x 3 sources x 2 modes (Optimal/Selected) = 3000 runs. Even with low average latency, total time is [deferred]. Well within 6h limit.
- **CPU**: No heavy ML models. Only lightweight traversal and SQL parsing.

## Success Criteria Mapping

| Success Criteria | Measurement Method |
| :--- | :--- |
| **SC-001** (Non-linear scaling) | Segmented Regression p-value < 0.05 for the "knee point" + Slope Ratio calculation. |
| **SC-002** (Error stability) | Absolute difference in error rates (Low vs High complexity). |
| **SC-003** (Significance) | ANOVA interaction p-value < 0.05. |
| **SC-004** (Robustness) | Consistency of "spike point" across sensitivity sweeps. |