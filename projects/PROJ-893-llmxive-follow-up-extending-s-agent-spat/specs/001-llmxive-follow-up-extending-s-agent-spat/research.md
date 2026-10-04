# Research: Symbolic Spatial Reasoning vs. VLM Baselines

## Research Question

Can a deterministic Constraint Satisfaction Problem (CSP) solver, operating on explicit 3D geometric constraints extracted from multi-view scenes, achieve accuracy comparable to a Vision-Language Model (VLM) baseline (S-Agent) on spatial reasoning tasks, while offering superior interpretability and latency?

Specifically, we investigate:
1. **Accuracy Gap**: What is the Exact Match and F1-score difference between the symbolic solver and the S-Agent VLM baseline on a stratified sample of 1,000 static multi-view scenes?
2. **Latency Efficiency**: How does the wall-clock latency of the CPU-bound symbolic solver compare to the VLM inference latency?
3. **Failure Modes**: To what extent do solver failures arise from "Geometric Ambiguity" (insufficient constraints) versus "Semantic Gap" (VLM hallucination or misinterpretation of spatial prepositions)?

## Methodology

### Data Source
We utilize the **S-Agent-300K** dataset, a large-scale collection of multi-view spatial reasoning scenes. We perform a stratified random sample of exactly `n=1,000` scenes, stratified by `object_density` and `scene_complexity` to ensure representative coverage of the distribution.

### Pipeline Stages
1. **Data Extraction**: Parse raw scene files to extract geometric constraints (relative positions, orientations, occlusions) into a canonical JSON format. Invalid or malformed scenes are excluded and logged.
2. **Symbolic Solver**: Implement a CSP solver using `python-constraint` to deduce the correct spatial configuration (e.g., counting objects, identifying relative positions) based *only* on the extracted constraints.
3. **Baseline Comparison**: Retrieve the original S-Agent VLM predictions and ground-truth labels for the same scene IDs.
4. **Benchmarking**: Compute Exact Match, F1-score, and latency metrics. Perform McNemar's test for statistical significance.
5. **Failure Analysis**: Categorize mismatches between the symbolic solver and ground truth to distinguish between solver limitations and VLM errors.

### Constraints & Verification
- **Stratified Sampling**: Ensures no distributional bias in the evaluation set.
- **Deterministic Execution**: The symbolic solver must be fully deterministic (no stochasticity).
- **Verified Accuracy**: All citations and dataset references are validated against the "Verified Datasets" block below.

## Verified Datasets

The following dataset is the canonical source for this research. All downstream processing relies on this specific identifier and version.

| Dataset Name | HuggingFace ID | Description |
|:--- |:--- |:--- |
| **S-Agent-300K** | `llmXive/S-AgentK` | The primary multi-view spatial reasoning dataset containing 300,000 scenes with geometric metadata and VLM baseline labels. |

**Access Note**: Access to `llmXive/S-AgentK` requires authentication via `huggingface_hub`. The dataset includes columns `object_density`, `scene_complexity`, `geometry`, and `ground_truth`.

## Expected Outcomes

- A benchmark report (`data/results/benchmark_results.csv`) containing per-scene metrics and a global p-value.
- A failure analysis report (`data/results/failure_analysis_report.md`) quantifying the "Semantic Gap".
- Validation of the hypothesis that symbolic methods can match VLM accuracy on geometrically constrained tasks with lower latency.