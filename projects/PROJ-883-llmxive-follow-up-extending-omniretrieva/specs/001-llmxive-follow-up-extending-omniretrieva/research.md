# Research: llmXive Follow-up: Structural Mismatch Cost in Heterogeneous Retrieval

## Research Question

Does the end-to-end latency of a unified retrieval router exhibit a non-linear scaling penalty (structural mismatch cost) when executing high-complexity (multi-hop) queries against graph-based knowledge sources compared to text or relational sources, under strict CPU constraints?

## Hypothesis

**H1**: There is a statistically significant interaction effect between `query_complexity` (plan depth) and `source_type` on `latency_ms`. Specifically, the slope of latency increase with complexity will be significantly steeper for `graph` sources than for `text` or `relational` sources.

**H2**: Translation error rates (deviation from ground-truth greedy plan) will remain stable across complexity levels, indicating the bottleneck is execution overhead, not planning accuracy.

## Dataset Strategy

The study relies on three verified datasets. We will sample subsets to fit the available RAM constraint and ensure structural depth for synthetic query generation.

| Source Type | Dataset Name | Verified URL | Usage Strategy |
|:--- |:--- |:--- |:--- |
| **Text** | MS MARCO (subset) | ` | Extract text chunks. Synthetic queries simulate retrieval by chaining chunk lookups. |
| **Relational** | Spider (Subset) | ` (Public Benchmark) | Use the **Spider 'train' split**. This dataset is verified to contain complex multi-join queries (depth > 3) by design. We will use the schema to construct the SQLite DB and the queries to verify depth. |
| **Graph** | DBpedia -10 (RDF) | `https://wiki.dbpedia.org/services-resources/datasets/dbpedia-2022-10` | Use the **DBpedia 2022-10 RDF dump**. This provides explicit `rdf:type`, `owl:sameAs`, and property edges. We will load this into `rdflib` and traverse the **real** graph structure. |

**Data Availability Note**:
- **Spider**: The 'train' split is verified to contain complex queries, satisfying the requirement for depth > 3 in the Relational source.
- **DBpedia**: The 2022-10 RDF dump provides the explicit edge definitions required for the Graph source, eliminating the need for synthetic edge construction.
- **MS MARCO**: Used for text retrieval simulation.

**Synthetic Fallback Protocol (Addressing T005/T041)**:
If the verified datasets lack sufficient structural depth (e.g., insufficient entity connections for depth > 3 queries):
1. The `query_generator.py` will detect the deficiency.
2. **ABORT CONDITION**: If the deficiency occurs in the **primary analysis range** (depth 1-3), the run **ABORTS** with error code `ERR_DEPTH_INSUFFICIENT`. No primary analysis is performed on synthetic data.
3. **Stress Test Only**: If depth > 3 is needed for stress testing, a synthetic graph may be generated *only* using the schema inferred from the verified dataset.
4. A `synthetic_flag` will be set to `true` in the `execution_logs.csv` for any query derived from synthetic topology.
5. The `synthetic_flag` must be `0` for all queries in the primary ANCOVA analysis (depth 1-3).

## Methodology

### 1. Query Generation
- **Input**: Verified datasets (Spider schema, DBpedia RDF, MS MARCO chunks).
- **Process**: Generate a sufficient number of queries per complexity level (Depth 1, 2, 3, 4+).
- **Mechanism**:
 - *Depth 1*: Single lookup (e.g., "Find entity X").
 - *Depth 2*: Chain of 2 lookups (e.g., "Find entity related to X, then find Y related to that").
 - *Depth 3+*: Recursive chains.
- **Ground Truth**: **FR-008**: A deterministic, rule-based reference engine (`ground_truth_engine.py`) calculates the optimal path (lowest cost) for every query using the **real** engine's statistics. This plan is stored as `ground_truth_plan`.

### 2. Execution Engine
- **Environment**: 2 CPU cores, 7GB RAM.
- **Throttling**:
 - Primary: `cgroups` (if runner has permissions) to limit CPU share.
 - Fallback: Strict `time` measurement with a note. If `cgroups` fails, the test suite will flag the run as "unthrottled" but still record latency (valid for relative comparison if load is constant).
- **Engines**:
 - *Text*: Simple vector search or keyword match.
 - *Relational*: SQLite in-memory database populated with **Spider** data.
 - *Graph*: `rdflib` traversal on **DBpedia 2022-10** RDF graph.
- **Latency Measurement**: **Strictly Real Execution Only**. `latency_ms` is measured from the actual wall-clock time of the engine execution. **No artificial delays** (e.g., `time.sleep`, CPU burners) proportional to complexity are added. If the engine returns instantly, the latency is recorded as instant.

### 3. Metrics Collection
- **Latency**: Wall-clock time (ms) per query.
- **Translation Error**: Binary (1 if generated plan != ground truth plan).
- **Success Flag**: 1 if query completed, 0 if timeout (>60s) or engine error.

### 4. Statistical Analysis
- **Primary Test**: **ANCOVA** (Analysis of Covariance).
 - Factors: `source_type` (Categorical).
 - Covariate: `complexity_level` (Continuous Integer).
 - Dependent Variable: `latency_ms`.
 - Interaction Term: `source_type * complexity_level`.
 - Threshold: p < 0.05 for H1 support.
- **Post-hoc**: Tukey HSD to identify specific pairwise differences between source types at high complexity.
- **Sensitivity Analysis (FR-007)**:
 - **Sweep**: Iterate over a range of cutoffs.
 - **Model**: Fit a piecewise linear regression (segmented regression) for each cutoff.
 - **Metric**: Calculate `spike_point` (x-value where absolute difference in slope is maximized) and `slope_change` (difference in slopes).
 - **Output**: `sensitivity_analysis.json` with `{"cutoff": <int>, "spike_point": <float>, "slope_change": <float>}`.

## Statistical Rigor & Assumptions

- **Multiple Comparisons**: Tukey HSD controls family-wise error rate for pairwise comparisons.
- **Power**: With 500 queries per level, we have >0.99 power to detect medium effect sizes (f=0.25) for the interaction term. **Note**: This power calculation assumes the effect exists. The experimental design (using real DBpedia topology with high diameter and complex cycles) is specifically chosen to trigger the 'structural mismatch' in the RDFLib engine, ensuring the effect is not an artifact of synthetic sparsity. If the effect is zero, the study correctly concludes no mismatch cost exists under these conditions.
- **Causal Framing**: Findings are associational regarding system behavior under constraint. No random assignment to hardware; the "hardware" is fixed (CPU-constrained). The "treatment" is the query complexity and source type.
- **Collinearity**: Complexity and source type are orthogonal by design (synthetic queries generated for all combinations).
- **Measurement Validity**: Ground truth is derived from an independent, deterministic engine (FR-008) on **real data**, preventing circularity.
- **Construct Validity**: The "structural mismatch cost" is measured by the difference in *native* engine performance (SQLite vs. RDFLib) on real data structures, not by synthetic simulation.

## Design Validity & Control Mechanism

**Addressing Engine-Efficiency Confound**:
The hypothesis posits that the "structural mismatch" arises from the *graph engine's* inability to efficiently execute join-heavy queries (which are native to relational engines).
- **Control**: We use the **same logical query structure** (e.g., a 3-hop path) across all engines.
- **Mechanism**:
 - **Relational (SQLite)**: Optimized for joins. Latency scales linearly or sub-linearly with depth.
 - **Graph (RDFLib)**: Optimized for traversal. Latency scales exponentially or super-linearly with depth for join-heavy patterns due to lack of native join optimization.
- **Result**: The "interaction effect" (steeper slope for Graph) is a direct measure of the *structural mismatch* (using a traversal engine for a join task), not merely a difference in raw CPU speed. This isolates the variable of interest.

## Decision Rationale

- **CPU-First**: All methods (SQLite, NetworkX, RDFLib, Scipy) are CPU-tractable. No GPU is required or planned.
- **Data Strategy**: Using Spider (Relational) and DBpedia 2022-10 (Graph) ensures we use verified, downloadable data with explicit structural depth and edge definitions.
- **Fallback Logic**: Explicit `synthetic_flag` and **hard abort** logic ensures we do not violate Data Hygiene (Principle III) or Fidelity (Principle VI).