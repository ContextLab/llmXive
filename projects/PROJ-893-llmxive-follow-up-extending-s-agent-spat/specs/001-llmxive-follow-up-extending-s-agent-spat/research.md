# Research: llmXive follow-up: extending "S-Agent: Spatial Tool-Use Elicits Reasoning for Spatial Intelligence"

## Executive Summary

This research investigates whether symbolic Constraint Satisfaction Problem (CSP) solving, driven solely by extracted 3D geometric evidence, can replicate the spatial reasoning performance of a neural Vision-Language Model (VLM) on the S-Agent-300K dataset. The hypothesis is that if the CSP solver achieves ≥85% of the VLM baseline accuracy (with an absolute floor of [deferred] Exact Match), the "reasoning" in S-Agent is primarily geometric and can be decoupled from neural semantic disambiguation. If the solver fails significantly, the failure modes will be categorized to determine if the deficit is due to insufficient geometric data ("Geometric Ambiguity") or missing semantic context ("Semantic Gap").

## Dataset Strategy

The study relies on the **S-Agent-300K** dataset (specifically the static multi-view subset). The plan strictly prioritizes this dataset. **No proxy datasets** (e.g., Cspk, yoonlee) will be used for the primary analysis unless a **Distributional Validity Gate** confirms statistical equivalence.

### Verified Datasets & Availability Gate

*Note: The following URLs are the only verified sources for data referenced in this study. If the specific S-Agent-300K split is not directly listed below, the study will not proceed with a proxy for the primary analysis. Instead, it will trigger a 'Data Availability Gate' failure and pivot to a 'Pilot' study on a verified proxy, clearly labeled as such.*

**Primary Data Source (S-Agent-300K):**
- **S-Agent-300K Static Subset**: *Not currently in the user-provided verified block.*
 - **Status**: **BLOCKING**. If the S-Agent-300K dataset cannot be programmatically downloaded from a verified source (e.g., Hugging Face, Zenodo) using the credentials or public link provided in the project's `data/` config, the primary analysis cannot proceed.
 - **Fallback Strategy**: If S-Agent-300K is unavailable, the study will pivot to a **Pilot Study** using a verified proxy dataset (e.g., a subset of `Csplk/hipcam` if it contains the required 3D coordinates and object relations). Results from the Pilot will be explicitly labeled as "Pilot/Proxy" and not generalizable to S-Agent.

**Verified Proxies (For Pilot Only):**
- **CSP Geometric Constraints (Pilot)**:
 - Source: ` (Verified)
 - *Usage*: Only if S-Agent-300K is unavailable. Used to test the CSP engine feasibility.
- **VLM Baseline & Ground Truth (Pilot)**:
 - Source: ` (Verified)
 - *Usage*: Only if S-Agent-300K is unavailable. Used to test the benchmarking pipeline.

### Distributional Validity Gate (MANDATORY)

To address the concern that proxy datasets may lack the same distribution of spatial complexity, the following gate is enforced **before** the main solver execution. This is a hard blocking condition for the primary analysis.

1. **Metric Extraction**: Extract key statistical features from the available dataset (proxy or target) for a representative sample (n=100):
 - **Object Density**: Mean and variance of objects per scene.
 - **Spatial Variance**: Mean and variance of inter-object distances (Euclidean).
 - **Relation Type Distribution**: Frequency distribution of spatial relations (e.g., "left_of", "above", "in_front_of").
 - **Task Complexity**: Mean number of constraints per scene.

2. **Statistical Comparison**:
 - **If S-Agent-300K reference data is available**: Perform **Kolmogorov-Smirnov (KS) tests** comparing the proxy distribution against the S-Agent reference for each metric.
 - **If S-Agent-300K is unavailable**: The study proceeds **only** if the proxy's distribution is documented as representative of the target domain (e.g., via a cited paper or dataset card). If no documentation exists, the study is aborted or labeled "Pilot/Proxy - Unverified Distribution".

3. **Decision Logic (Hard Gate)**:
 - **Pass**: If all KS-tests yield p > 0.05 (no significant difference) OR if the proxy is documented as representative.
 - **Fail**: If any KS-test yields p < 0.05. The study is **ABORTED** for the primary analysis. It may proceed as a "Pilot/Proxy - Distributional Mismatch" study, but results must be explicitly caveated as not generalizable to S-Agent-300K. The `distributional_match` field in the output schema will record `is_valid_proxy: false` and the specific p-values.

**Variable Check**: The study requires 3D coordinates, object relations, and ground-truth spatial answers (count/position). The S-Agent-300K dataset is assumed to contain these. The pilot proxies are checked for these variables; if missing, the pilot is aborted.
**Gap Mitigation**: If S-Agent-300K is unavailable and no verified proxy contains the required variables, the study is **aborted** (no fabrication).
**Streaming**: If the dataset exceeds memory, the pipeline will use `pandas.read_parquet(..., engine='pyarrow')` with chunking or `huggingface_hub` streaming.

## Methodology

### Phase 0: Distributional Validity Check (GATE)
1. **Extract Features**: Run `code/data/validate_distribution.py` to compute object density, spatial variance, and relation distributions from a sample.
2. **Compare**: Perform KS-tests against S-Agent-300K reference (if available) or check documentation.
3. **Gate**: If p < 0.05, flag the run as "Pilot/Proxy - Distributional Mismatch". **STOP** primary analysis. Proceed only with explicit "Pilot" labeling.

### Phase 1: Data Extraction & Preprocessing
1. **Download**: Fetch the S-Agent-300K dataset (or verified proxy for Pilot) using `huggingface_hub` or direct URL download.
2. **Sampling**: Perform a stratified random sampling of n=1,000 scenes (or as many as available).
3. **Constraint Extraction**: Parse the raw data to extract:
 - Object coordinates (x, y, z).
 - Relative relations (e.g., "A is left of B", "C is above D").
 - **Semantic Labels**: Explicit object class labels (e.g., "cup", "plate") required for the CSP variables.
 - *Exclusion*: Scenes with missing geometry or missing semantic labels are logged and excluded (FR-007).
4. **Format**: Convert extracted constraints into a standardized JSON/CSV format compatible with the CSP solver.

### Phase 2: Symbolic CSP Solver Execution
1. **Model Formulation**: Translate geometric constraints and semantic labels into a CSP using `python-constraint` or `ortools`.
 - **Semantic Mapping**: The solver uses *provided* semantic labels to define variables (e.g., `count_cups`). It does *not* infer labels from geometry.
 - Variables: Object positions, counts.
 - Domains: Discrete spatial bins or continuous ranges (discretized for solver).
 - Constraints: Hard geometric rules derived from the data.
2. **Execution**: Run the solver on the [deferred] scenes.
 - **CPU-First**: The solver runs entirely on CPU (no GPU).
 - **Timeout**: 60 seconds per scene (FR-004).
 - **Output**: JSON predictions with status (Solved, No Solution, Ambiguous).

### Phase 3: Benchmarking & Analysis
1. **Metric Calculation**:
 - **Exact Match**: Compare symbolic prediction vs. ground truth.
 - **F1-Score**: Calculate for counting tasks.
 - **Latency**: Measure wall-clock time per scene on a multi-core CPU.
2. **Statistical Testing**:
 - **McNemar's Test**: Compare paired accuracy (Symbolic vs. VLM).
 - **Power Analysis**: See below.
3. **Failure Analysis (Ground-Truth Projection)**:
 - Categorize failures where Symbolic != Ground Truth and VLM == Ground Truth.
 - **Ground-Truth Constraint Projection**: For each failure, project the *Ground Truth* solution onto the extracted geometric constraints.
 - If the GT solution **violates** the extracted constraints: Classify as **"Geometric Ambiguity"** (the input data was insufficient to represent the true state).
 - If the GT solution **satisfies** the extracted constraints but the solver failed: Classify as **"Semantic Gap"** (the solver missed a logical inference despite sufficient data).
 - This uses the GT as the oracle to distinguish data insufficiency from solver failure.

## Statistical Rigor & Assumptions

### Power Analysis & Sample Size Justification
The study uses McNemar's test to compare paired accuracy (Symbolic vs. VLM).
- **Null Hypothesis ($H_0$)**: The proportion of discordant pairs where Symbolic is correct and VLM is wrong ($p_{12}$) equals the proportion where VLM is correct and Symbolic is wrong ($p_{21}$).
- **Success Criterion (SC-005)**: Symbolic Accuracy $\ge$ [deferred] of VLM Accuracy.
 - Let VLM Accuracy = $A_{vlm}$. Symbolic Accuracy = $A_{sym}$.
 - We test for a gap where $A_{sym} < 0.85 \times A_{vlm}$.
 - Assume a conservative VLM accuracy of $A_{vlm} = 0.80$ ([deferred]).
 - Target Symbolic Accuracy (Success) = $0.85 \times 0.80 = 0.68$.
 - We want to detect a difference of $\delta = 0.12$ in the discordant pair proportions (simplified approximation for McNemar's).
 - **Minimum Detectable Effect Size (MDES)**: For McNemar's test with $\alpha=0.05$ and Power=0.80, the required sample size $N$ is approximately:
 $$N \approx \frac{(Z_{\alpha/2} + Z_{\beta})^2 \times (p_{12} + p_{21})}{(p_{12} - p_{21})^2}$$
 Assuming $p_{12} \approx 0.05$ (Symbolic wins) and $p_{21} \approx 0.17$ (VLM wins, representing the [deferred] gap), the discordant sum is 0.22.
 $$N \approx \frac{(1.96 + 0.84)^2 \times 0.22}{(0.12)^2} \approx \frac{7.84 \times 0.22}{0.0144} \approx 120$$
 - **Conclusion**: With $n=1,000$, we have >80% power to detect the specific effect size implied by the 85% threshold (a ~12% gap in accuracy). The sample size is sufficient.

### Causal Inference
The study is observational. We compare two methods on the *same* data. We frame results as "The symbolic method achieves X% of the VLM's performance," avoiding causal claims that "geometry causes reasoning."

### Baseline Integrity
The VLM baseline is defined as a **frozen, external model** evaluated on a held-out test set. If the S-Agent-300K labels were generated by a VLM, we will use a *different* frozen VLM (or the original S-Agent model if distinct from the label generator) to ensure the comparison is not circular. The ground truth is treated as an independent measure of spatial reasoning, not a proxy for the VLM's training distribution.

### Measurement Validity
Ground truth is assumed accurate (SC-001). The CSP solver's "No Solution" status is treated as a valid negative prediction for failure analysis.

### Collinearity
Geometric constraints are treated as a joint system. We do not claim independent effects of individual coordinates; the solver respects the joint constraint satisfaction.

## Compute Feasibility & GPU Escape Hatch

- **CPU-First**: The CSP solver is a classical algorithm (backtracking/constraint propagation) that runs efficiently on CPU. It does not require a GPU.
- **GPU Escape Hatch**: Not applicable for the symbolic solver. If the VLM baseline requires a GPU for re-evaluation (if not pre-computed), the plan will use the "GPU escape hatch" (Kaggle auto-offload) for that specific step only, using a small, quantized model if necessary. However, the spec implies using *existing* VLM baseline predictions, so no new VLM inference is planned.
- **Memory**: A scene sample and associated constraints will easily fit in available RAM. Streaming will be used if the raw download is large.

## Decision/Rationale

| Decision | Rationale |
|----------|-----------|
| **Use `python-constraint`** | Lightweight, pure Python, no external C++ dependencies, fits CPU-first requirement. |
| **Sample n=1,000** | Balances statistical power (MDES >12% gap) with the 6-hour CI limit and 7 GB RAM constraint. |
| **Strict Exclusion of VLM Traces** | Required by FR-001 and Constitution Principle VII to isolate the "geometric" capability. |
| **Categorize Failures (GT Projection)** | Required by US-3 to answer the "Why" of the research question, using GT as the oracle for sufficiency. |
| **Absolute Performance Floor** | Added to SC-005 to prevent success if the VLM baseline is weak (e.g., <70% absolute accuracy). |
| **Distributional Validity Gate** | Required to ensure proxy datasets are statistically equivalent to S-Agent-300K, preventing external validity failure. This is a hard blocking condition. |