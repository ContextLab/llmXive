# Research: EnterpriseClawBench Reproduction & Validation

## 1. Problem Statement & Objectives

The objective is to reproduce the **EnterpriseClawBench** benchmark construction and evaluation pipeline using the provided git submodule. The primary goals are:
1.  **Verify Integrity**: Ensure the pipeline runs without errors on a minimal dataset (Smoke Test).
2.  **Validate Protocol**: Confirm the evaluation logic (Judge) produces deterministic and correct scores.
3.  **Reproduce Metrics**: Aggregate results to match the *structural trends* of the statistical claims in the source paper.

This research focuses on the feasibility of running this pipeline on a CPU-only, 7GB RAM environment and identifying any data gaps between the provided `raw_session_example` and the full 852-task dataset described in the paper.

## 2. Dataset Strategy

The implementation relies on data provided within the `EnterpriseClawBench` submodule.

| Dataset Name | Source / URL | Usage in Plan | Status |
| :--- | :--- | :--- | :--- |
| `raw_session_example` | Local (Submodule: `external/EnterpriseClawBench/raw_session_example/`) | **Smoke Test**: Used for FR-001, FR-002, FR-003. Contains minimal sessions for pipeline validation. | **Verified** (Local) |
| `example_runs` | Local (Submodule: `external/EnterpriseClawBench/example_runs/`) | **Evaluation Test**: Used for FR-004, FR-005. Contains pre-generated artifacts for judge validation. | **Verified** (Local) |
| Full Enterprise Dataset | NO verified source found | **Reproduction**: The full 852-task dataset is **not** available in the verified sources. The plan uses the local examples as a proxy for structural validation (SC-004) but acknowledges variance. | **Not Available** |

**Dataset Fit Analysis**:
- The `raw_session_example` is sufficient for the **Smoke Test** (US-1) as it covers the necessary schema for turn extraction and task packaging.
- The `example_runs` are sufficient for **Evaluation Protocol** (US-2) as they provide the artifacts needed to test the judge logic.
- **Gap**: The full dataset required for exact statistical reproduction (US-3, SC-004) is not present. The plan will compare the *distribution* of the local sample against the paper's *reported* distribution, noting that the absolute counts will differ due to sampling.

## 3. Methodology & Statistical Rigor

### 3.1 Construction Pipeline
The construction pipeline is a deterministic data transformation process.
- **Method**: Sequential execution of stages (Inventory → Turn Extraction → ... → Pack Writer).
- **Validation**: Each output `task.json` is validated against a schema (see `contracts/task.schema.yaml`).
- **Rigor**: No statistical inference is required here; the focus is on **completeness** (SC-002) and **error handling** (FR-001).

### 3.2 Evaluation Protocol
The evaluation uses a "Judge" (LLM or rule-based) to score artifacts.
- **Method**: Rule-based scoring for `artifact_delivery`, `visual_quality`, etc., with LLM for `semantic_rubric`.
- **Statistical Considerations**:
  - **Determinism**: To satisfy SC-003, the plan enforces `temperature=0` and a fixed `seed` for the LLM judge. If the provider does not support these parameters, the plan defaults to a **rule-based scoring mode** for the smoke test. This ensures the "difference must be 0" criterion is achievable.
  - **Sample Size**: The sample size is limited by the `example_runs` (N < 10). Power analysis is not applicable for this validation step; the focus is on **logic correctness**, not population inference.
  - **Causal Claims**: None. The plan strictly validates the *scoring mechanism*, not the causal effect of the agents.

### 3.3 Statistical Reproduction
- **Method**: Aggregation of task counts and role distributions.
- **Logical Contradiction Resolution**: The original SC-004 required < 5% variance in absolute counts. Since the full dataset is unavailable, this is impossible. The methodology is revised to validate **structural trends** (relative proportions) instead.
- **Bias and Sampling Limitations**: The `example_runs` dataset may be cherry-picked (non-representative). Therefore, the comparison is **qualitative** (does the pipeline produce the *right shape* of distribution?) rather than **quantitative** (does it produce the *exact numbers*?). The plan explicitly acknowledges that any variance observed is likely due to sample bias, not pipeline error.
- **Variance Threshold**: SC-004 is reinterpreted to check for alignment in the *rank order* of role class frequencies (e.g., if "Analyst" is the most common in the paper, it should be the most common in the sample).

## 4. Compute Feasibility Analysis

| Component | Requirement | Feasibility on Free Tier (2 CPU, 7GB RAM) |
| :--- | :--- | :--- |
| **Pipeline Execution** | Python 3.10, Pandas, PyYAML | **High**: Low memory footprint. |
| **LLM Calls (Judge)** | API requests (External) | **Medium**: Dependent on API rate limits. Retry logic (FR-007) prevents hangs. Deterministic settings (temperature=0) may increase latency slightly but remain CPU-tractable. |
| **Disk Usage** | < 14 GB | **High**: `raw_session_example` and `example_runs` are small (< 500MB). |
| **Parallelism** | Limited | **High**: Plan uses sequential processing for smoke test to ensure stability. |

**Conclusion**: The plan is fully feasible on the free tier provided the `smoke.yaml` configuration is used. Full-scale reproduction of the 852 tasks is deferred to a larger compute environment.

## 5. Decision Log

| Decision | Rationale |
| :--- | :--- |
| **Use `smoke.yaml` for CI** | Ensures rapid feedback (< 10 mins) and validates the pipeline without resource exhaustion. |
| **No modification to submodule code** | Adheres to the "Reproduction" goal. Any bugs found will be reported, not patched. |
| **Fallback to `unscorable` on API failure** | Prevents CI crashes due to external LLM unavailability (FR-007). |
| **Statistical comparison on distribution trends, not absolute count** | Acknowledges the missing full dataset and the bias in `example_runs` while still validating the *nature* of the benchmark. |
| **Enforce deterministic LLM settings or fallback to rule-based** | Addresses the methodological concern that LLMs are inherently non-deterministic, ensuring SC-003 remains valid. |