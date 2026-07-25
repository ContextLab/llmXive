# Research: llmXive follow-up: extending "AutoResearchClaw"

## Problem Statement

Autonomous research agents like AutoResearchClaw (ARC) often fail due to specific structural error patterns. This project investigates whether these failure modes can be distilled into deterministic rules (heuristic engine) that outperform probabilistic retrieval (LLM-based baseline) in terms of **Steps-to-Pivot** (capped at 50) and Success Rate, specifically under resource-constrained conditions. The study addresses the circular validity threat by establishing a human-validated ground truth for failure types before distillation.

## Dataset Strategy

The study relies on the **ARC-Bench** dataset, specifically the 25-topic subset containing failure-resolution pairs.

| Dataset | Source URL | Format | Access Method | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **ARC-Bench (25-Topic Subset)** | `https://huggingface.co/datasets/claw-ai-lab/arc-bench/resolve/main/data/arc_bench_25_topics.parquet` | Parquet | `datasets.load_dataset(..., streaming=True)` | Verified source. Contains `error_trace`, `resolution_path`, `task_prompt`. |
| **Baseline Logs** | Generated | JSON/CSV | `code/engine/baseline_runner.py` | Baseline agent is re-run on the test set (N=500) within the 6-hour limit on Standard Resources. |

**Dataset Fit Verification**:
- **Requirement**: The dataset must contain `error_trace`, `resolution_path`, and `task_prompt`.
- **Verification**: The verified ARC-Bench parquet files contain these fields. `error_trace` maps to `raw_error_log`, `resolution_path` to `ground_truth_resolution`, and `task_prompt` to `task_context`.
- **Gap Handling**: If specific execution metadata is missing, the system will infer `Steps-to-Pivot` based on simulated step counts (capped at 50) and record it as 'Censored' if the cap is reached.

**Data Availability & Feasibility**:
- **Access**: All datasets are open and directly downloadable via HuggingFace `datasets` library with `streaming=True`. No credentials or data-use agreements are required.
- **Size**: The full dataset is large; the plan uses streaming + `itertools.islice` fallback to avoid memory overflow. A sample of ~100 cases for human validation, and a held-out test set of **N=500** for evaluation (to ensure sufficient power for the interaction term).
- **No Gated Data**: No access-gated data (e.g., ADNI, UK Biobank) is used.

## Methodology & Statistical Rigor

### Phase 0: Ground Truth Establishment (Pre-Distillation)
1.  **Sampling**: Select a stratified random sample of failure cases from ARC-Bench.
2.  **Human Annotation**: Human experts annotate these 100 cases with `structural_feature` (Syntactic, Logical, Semantic, Missing Context, Unstructured, or **None (Success)**).
3.  **LLM Validation**: Run the LLM annotator on these 100 cases. Calculate inter-rater agreement (Cohen's Kappa) against human labels.
4.  **Threshold**: If agreement < 0.85, revise the prompt or model and re-run. **Distillation proceeds only if agreement >= 0.85**. This establishes the LLM as a validated proxy for the gold standard.

### Phase 1: Failure Annotation & Rule Distillation (US-1)
1.  **Ingestion**: Stream ARC-Bench parquet files. Filter for entries with non-empty `error_trace`.
2.  **Annotation**: Use the validated LLM to classify each failure into: `Syntactic`, `Logical`, `Semantic`, `Missing Context`, `Unstructured`, or `None (Success)`.
    - *Validation*: Spot-check a representative sample of data against the human gold standard to confirm consistency.
3.  **Distillation**: Convert annotated failures into `If-Condition-Then-Action` rules.
    - *Syntactic*: Regex-based deterministic rules.
    - *Semantic*: Probabilistic retrieval instructions or flags for baseline fallback.
    - *Coverage*: Target ≥90% of patterns covered.
4.  **Coverage Validation**: Run the distilled rules against a held-out validation set. If coverage <90%, re-run distillation with adjusted prompts. **This step explicitly measures the ≥90% threshold required by FR-002.**

### Phase 2: Rule Engine Execution & Baseline Comparison (US-2)
1.  **Rule Engine**: Execute the distilled rule library on a held-out test set of **N=500** tasks.
    - *Constraint*: Runs on a multi-core CPU with sufficient RAM.
    - *Resource Monitoring*: Log `peak_memory` and `cpu_time` via `psutil` to `resource_usage.log`.
2.  **Baseline**: Execute the full AutoResearchClaw agent on the **same** 500 tasks.
    - *Constraint*: Runs on **Standard Resources** (4 CPU, 16 GB RAM) as per FR-004 (separate CI job).
    - *Resource Monitoring*: Log `peak_memory` and `cpu_time`.
3.  **Metrics**:
    - `Steps-to-Pivot`: Number of steps from error detection to successful pivot. **Capped at 50**. If >50, record as 50 and flag as `Censored`. (Replaces 'Time-to-Pivot' to avoid network variance).
    - `Success`: Binary (1 if pivot successful, 0 otherwise).
    - *Stratification*: Metrics recorded per `structural_feature`.
    - *Resource Covariate*: Record resource usage to model potential confounding.

### Phase 3: Statistical Analysis (US-3)
1.  **Model**: Mixed-effects Tobit Regression (for censored time data) and Logistic Regression (for success).
    - *Fixed Effects*: `Method` (Rule vs. Baseline), `Failure Type` (including 'None'), `Interaction (Method * Failure Type)`, `Resource_Covariate`.
    - *Random Effect*: `Task ID`.
    - *Equation (Tobit)*: `Steps = β0 + β1(Method) + β2(FailureType) + β3(Method*FailureType) + u_TaskID + ε` (censored at 50).
2.  **Hypothesis Tests**:
    - **SC-001 (Time/Steps)**: **Wilcoxon Signed-Rank Test** on `Steps-to-Pivot` (handling censored data) between Rule and Baseline. (Paired T-Test used if normality holds).
    - **SC-002 (Success)**: **Chi-Square Test** or Logistic Regression coefficient for `Method` stratified by `Failure Type`.
    - **SC-003 (Interaction)**: Significance of `β3` in the mixed-effects model.
    - **SC-004 (Error Taxonomy)**: Proportion of failures in 'Coverage Gap' vs. 'Distillation Error'.
    - **SC-005 (Resources)**: Compare `total_compute_time` and `peak_memory` (from `resource_usage.log`) against GitHub Actions limits.
3.  **Error Taxonomy**: Categorize rule engine failures into "Coverage Gap" vs. "Distillation Error".

## Compute Feasibility

- **CPU-First**:
    - Data Ingestion: `datasets` streaming + `itertools.islice` fallback.
    - Annotation/Distillation: `transformers` with `load_in_8bit` or `INT4` on CPU. If this exceeds 7 GB RAM, the sample size is reduced or the model is further quantized (e.g., 4-bit).
    - Baseline Simulation: Runs on **Standard Resources** (4 CPU, 16 GB RAM) as per FR-004. This is executed on a separate GitHub Actions job with a larger runner or external resource to ensure the comparison is valid.
- **GPU Policy**:
    - **NO GPU for primary analysis**. If the INT4 model fails to load on CPU (OOM), the run is aborted or scaled down. GPU results are excluded from the primary analysis to satisfy Constitution Principle VII.

## Decision Rationale

- **Why Streaming + Fallback?** The ARC-Bench dataset is large; loading it fully would crash the CI runner. Streaming ensures the full dataset is accessible without memory overflow. `itertools.islice` provides a fallback if streaming fails.
- **Why INT4?** Full LLMs require >16 GB RAM. INT4 quantization allows inference within the 7 GB constraint.
- **Why Mixed-Effects with Censoring?** Tasks have inherent difficulty variance. Ignoring `Task ID` as a random effect would bias the significance. Handling censored data (steps > 50) prevents statistical singularity.
- **Why Human-in-the-Loop?** LLM annotations alone are noisy. A gold standard sample validates the LLM before distillation, breaking the circular validity threat.
- **Why Dual Resources?** FR-004 requires the baseline to represent 'standard' capability. We run it on standard resources (separate job) to answer the research question, while the Rule Engine is constrained to test its viability on consumer hardware.
- **Why No Synthetic Data?** The hypothesis relies on real failure structures. Synthetic data would not capture the complexity of real agent errors.
- **Why Steps-to-Pivot?** 'Time-to-Pivot' is confounded by network jitter. 'Steps-to-Pivot' (capped) is a robust measure of agent reasoning speed.