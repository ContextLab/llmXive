# Research: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Research Question

Does the end-to-end latency of heterogeneous retrieval systems exhibit a significant interaction effect (steepening slope) or monotonic increase as query logical depth (complexity) increases, specifically when executed under CPU-constrained environments?

## Background & Motivation

The "OmniRetrieval" concept posits a unified router for heterogeneous sources (Text, Relational, Graph). While theoretically efficient, the "translation" of a unified query plan into native execution plans for graph sources (e.g., recursive joins) may incur disproportionate overhead on CPU-constrained hardware compared to text or relational sources. This research aims to quantify that "structural mismatch cost."

## Dataset Strategy

This study utilizes a **hybrid approach**:
1. **Reference Data**: We utilize subsets of verified datasets to establish schema validity and parameter ranges for synthetic query generation.
 * **MS MARCO**: Used to derive text corpus sizes and token distribution for text engine simulation.
 * Source: `
 * **DBpedia**: Used to derive graph density and relational join patterns for graph/relational engine simulation.
 * Source: `

2. **Synthetic Generation**: The actual experimental data is **not** drawn directly from these datasets. Instead, a deterministic, rule-based synthetic query generator constructs queries with **controlled logical depth** (1, 2, 3+ hops). This ensures the independent variable (complexity) is not confounded by other dataset-specific features (e.g., token length, data skew). The generator uses the schema characteristics of the verified datasets to ensure structural realism.

**Dataset Fit**: The verified datasets provide the necessary structural metadata (e.g., join keys, edge definitions) to construct valid high-complexity synthetic queries. If a specific dataset lacks required structural depth, the rule-based generator serves as the mandatory fallback to ensure structural depth is always available.

## Methodology

### 1. Synthetic Query Generation
* **Generator**: A Python script (`synthetic_query_gen.py`) constructs logical plans.
* **Complexity Levels**:
 * **Low**: Depth 1-2 (Single-hop or simple join).
 * **High**: Depth 3+ (Recursive joins, multi-hop graph traversal).
* **Control**: Random seeds are fixed. The generator ensures balanced distribution across source types (Text, Relational, Graph).
* **Constraint**: The generator is strictly limited to a predefined maximum number of queries (enforced by a hard `while` loop check: `if count >= 500: break`).

### 2. Execution Environment
* **Hardware Constraint**: Simulated via Python `resource` module or `cgroups` (if available) to enforce strict CPU time limits per query (e.g., a defined budget).
* **Engines**:
 * **Text**: **Whoosh** (in-memory, pure Python) for text retrieval.
 * **Relational**: **DuckDB** (in-memory) for SQL execution.
 * **Graph**: **NetworkX** (in-memory) for graph traversal.
* **Throttling**: All engines run under a simulated CPU constraint (CPU-burner loops). **Crucially**, the number of CPU-burner loop iterations is **proportional to the query's logical depth** (e.g., `iterations = base * depth`). This ensures the "structural mismatch cost" is driven by the interaction of complexity and the simulated constraint, not just fixed Python overhead. **All latency is measured via `time.perf_counter()` during real execution of the query on the engine.** The CPU-burner loop injects a complexity-proportional delay *on top of* this real execution time to simulate the constraint.

### 3. Metrics Collection
* **Latency**: End-to-end time in milliseconds measured via `time.perf_counter()` during **real execution** (not simulated). The artificial delay (proportional to depth) is added to this real execution time to simulate the constraint.
* **Translation Error**: Binary flag (0/1) comparing the generated plan against a ground-truth plan from a **separate, deterministic, exhaustive, rule-based solver** (`exact_solver.py`). The solver is independent of the router and computes the optimal plan based on the schema using an exhaustive search, ensuring the comparison is not tautological. The router uses heuristics; the solver uses exhaustive search. The error measures the router's deviation from the optimal plan.
* **Timeout**: Binary flag for queries exceeding the 60-second safety limit.
* **Baseline**: `cpu_burner_ms` measures the deterministic CPU-burner loop time to subtract Python interpreter overhead.

### 4. Statistical Analysis
* **Model**: **Linear Mixed-Effects Model (LMM)** using `statsmodels`.
 * Formula: `latency ~ complexity * source_type + (1|query_id)`.
 * Goal: Test the significance of the interaction term `complexity:source_type`. A significant positive interaction indicates that the slope of latency vs. complexity is steeper for Graph sources than for Text/Relational sources (the "mismatch cost").
* **Trend Test**: **Jonckheere-Terpstra test** for ordered alternatives.
 * Goal: Detect if latency monotonically increases with complexity for Graph sources, without assuming a linear relationship.
* **Hypothesis**: The interaction term for Graph sources will be positive and significant (p < 0.05), indicating a steeper latency increase.
* **Sensitivity Analysis**: Sweeping the complexity cutoff {2, 3, 4} to ensure the "spike" is robust.

## Construct Validity & Limitations

* **Simulated Engines**: While the logic is real, the engines are lightweight simulations. To ensure construct validity, the simulation includes artificial delays **scaled by query depth** (CPU-burner loops) to mimic I/O wait and context switching that scales with complexity. This ensures the "mismatch cost" is driven by algorithmic complexity, not just Python overhead. **Crucially, all base latency is measured via real execution.**
* **Observational Framing**: The study measures system behavior under constraint. It does not claim causal effects on general hardware performance, but rather associational measurements of the specific "structural mismatch" phenomenon.
* **Discrete Complexity**: The use of LMM with discrete complexity levels is handled by treating complexity as a continuous predictor to estimate the slope, with a non-parametric trend test as a robustness check.

## Decision & Rationale

| Decision | Rationale |
|----------|-----------|
| **Use Synthetic Queries** | Real-world queries have uncontrolled complexity distributions. Synthetic generation allows precise manipulation of the independent variable (depth) to isolate the "structural mismatch" effect. |
| **LMM + Trend Test over ANOVA/GAM** | The hypothesis posits "non-linear" or "monotonic" scaling. ANOVA assumes linear main effects and cannot capture interaction slopes. GAM is inappropriate for 3-4 discrete points. LMM allows testing the *slope* difference (interaction), and Jonckheere-Terpstra tests for monotonic trends without distributional assumptions. |
| **CPU Throttling Simulation** | The hypothesis is about "edge deployment" constraints. Running on unconstrained hardware would yield misleadingly low latencies, failing to reveal the mismatch cost. |
| **Reference Datasets for Schema Only** | Using full MS MARCO/DBpedia would exceed memory limits and introduce noise. Using them only for schema/parameter extraction ensures validity while maintaining feasibility on a resource-constrained runner. |
| **Exact Solver vs. Heuristic Router** | The router is a heuristic approximation; the solver is an exact, schema-driven algorithm using exhaustive search. This ensures the "translation error" is a valid measure of router performance, not a tautology. The solver is independent of the generator's heuristics. |
| **Real Latency Measurement** | Latency is measured via `time.perf_counter()` during real execution, not simulated. The "CPU-burner" is only for baseline subtraction and complexity-proportional delay injection. |
| **Engine Selection** | **Whoosh** (text), **DuckDB** (relational), **NetworkX** (graph) are selected for their CPU-only compatibility and ability to simulate I/O/complexity overheads. |
| **Complexity Handling** | Complexity is treated as a continuous predictor in LMM to estimate slope, with a non-parametric trend test as a robustness check. |
