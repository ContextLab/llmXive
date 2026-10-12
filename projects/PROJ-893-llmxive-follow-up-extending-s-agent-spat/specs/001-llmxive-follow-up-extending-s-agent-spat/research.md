# Research: Symbolic Spatial Reasoning vs. VLM Baselines

## Research Question

Can a deterministic Constraint Satisfaction Problem (CSP) solver, operating on explicit 3D
geometric constraints extracted from multi-view scenes, achieve accuracy comparable to a
Vision-Language Model (VLM) baseline (S-Agent) on spatial reasoning tasks, while offering
superior interpretability and latency?

Specifically, we investigate:
1. **Accuracy Gap**: What is the Exact Match and F1-score difference between the symbolic
   solver and the S-Agent VLM baseline on a stratified sample of n=1,000 static multi-view
   scenes?
2. **Latency Efficiency**: How does the wall-clock latency of the CPU-bound symbolic solver
   compare to the VLM inference latency?
3. **Failure Modes**: To what extent do solver failures arise from "Geometric Ambiguity"
   (insufficient constraints) versus "Semantic Gap" (missing non-geometric context that the
   VLM uses to disambiguate)?

## Methodology

### Data Source
The target dataset is the S-Agent-300K multi-view spatial reasoning corpus (see "Verified
Datasets" below for the canonical access status). We perform a stratified random sample of
exactly n=1,000 scenes, stratified by `object_density` and `scene_complexity` to ensure
representative coverage of the distribution. If those stratification columns are absent from
the retrieved dataset, the pipeline aborts with a 'Distributional Validity Gate Failure' and
the pilot/proxy path (T007b) is evaluated instead.

### Pipeline Stages
1. **Data Extraction (FR-001, FR-007)**: Parse raw scene files to extract geometric
   constraints (coordinates, object relations) into a canonical JSON format. Malformed or
   missing scenes are excluded and logged in `data/results/exclusion_log.json` with
   `total_scenes`, `excluded_count`, and `excluded_ids`.
2. **Symbolic Solver (FR-002)**: Implement a deterministic CSP solver using
   `python-constraint` to solve spatial counting and relative-positioning tasks based *only*
   on the extracted geometric constraints. VLM tool-call traces are strictly excluded from
   solver input (Constitution Principle VII).
3. **Baseline Comparison**: Retrieve the original S-Agent VLM predictions and ground-truth
   labels for the same scene IDs; the VLM baseline must come from the canonical source, never
   a simulated proxy.
4. **Benchmarking (FR-003, FR-004, FR-005)**: Compute Exact Match, F1-score, and per-scene
   latency metrics; perform McNemar's test for statistical significance of the paired
   accuracy difference.
5. **Failure Analysis (FR-006)**: Categorize scenes where the symbolic solver fails while the
   VLM succeeds as either "Geometric Ambiguity" (insufficient constraints) or "Semantic Gap"
   (sufficient constraints but incorrect inference), and report the semantic-gap proportion.

### Constraints & Verification
- **Stratified Sampling**: Ensures no distributional bias in the evaluation set; KS-tests on
  object density and spatial variance act as a hard Distributional Validity Gate.
- **Deterministic Execution**: The symbolic solver is fully deterministic; identical inputs
  yield identical outputs.
- **Verified Accuracy**: All citations and dataset references below are validated against the
  "Verified Datasets" block (title-token-overlap >= 0.7) by
  `code/validate/validate_research_citations.py` before the pipeline proceeds.

## Verified Datasets

| Dataset / Source | Canonical ID / URL | Status |
|:--- |:--- |:--- |
| **S-Agent-300K** (S-AgentK) | `llmXive/S-AgentK` (HuggingFace Hub) | **UNVERIFIED / UNREACHABLE**: the Hub repository was not found at execution time (`Repository Not Found for url: https://huggingface.co/api/models/llmXive/S-AgentK`). The pipeline must fail loudly rather than fall back to synthetic data until a verified canonical ID is confirmed. |
| **Making Large Language Models Better Reasoners with Alignment** | https://arxiv.org/abs/2309.02144 | Verified citation (arXiv 2309.02144, 2023; Peiyi Wang, Lei Li, Liang Chen, Feifan Song, Binghuai Lin, et al.). |

**Access Note**: The only programmatically verified external source at the time of writing is
the arXiv citation above. The S-Agent-300K dataset identifier is carried over from the
planning documents but has NOT been verified as reachable; per the real-data policy, no
proxy, mirror, or synthetic stand-in may be substituted for it. Downstream download tasks
(T006, T006c, T033) must abort with a clear error until a verified canonical HuggingFace ID
or URL for the S-Agent dataset is established.

## Expected Outcomes

- A benchmark report (`data/results/benchmark_results.csv`) containing per-scene metrics and
  a single global McNemar p-value.
- A sensitivity analysis (`data/results/sensitivity_analysis.csv`) sweeping the success
  threshold (SC-005, primary point 0.85).
- A failure analysis report (`data/results/failure_analysis_report.md`) quantifying the
  "Semantic Gap" proportion.
- Validation or refutation of the hypothesis that symbolic methods can match VLM accuracy on
  geometrically constrained tasks at substantially lower latency.