# Research: llmXive Follow-up: Extending EnterpriseClawBench

## 1. Research Questions & Hypotheses

**Primary Question**: To what extent can syntactic and pragmatic features of execution traces predict the feasibility of correcting agent failures via syntax rewriting?

**Hypothesis (H1)**: Syntactic and pragmatic features (syntax tree depth, token frequency, error recovery markers) contain sufficient signal to distinguish between failures caused by syntax mismatches (correctable) and those caused by fundamental reasoning gaps (unfixable).

**Null Hypothesis (H0)**: These features show no distinctiveness between correctable and unfixable failures (p > threshold after correction).

## 2. Dataset Strategy

**Target Dataset**: EnterpriseClawBench ("Benchmarking Agents from Real Workplace Sessions").

**Availability Status**:
- **Verified Source**: **NO verified source found** for EnterpriseClawBench in the provided dataset list.
- **Action Plan**:
  1. The pipeline is designed to accept the dataset via a local file path or a verified hash if the user provides the data locally.
  2. If the dataset is not provided locally, the pipeline will pause at the data-loading step with a clear error: "EnterpriseClawBench source not verified. Please provide data locally with a valid checksum."
  3. **No URL will be fabricated.** The research will proceed only if the data is present and verified.

**Local Data Schema Definition**:
The local data **MUST** conform to the following schema to ensure feasibility:
- `trace_id`: Unique identifier.
- `task_id`: Task identifier.
- `status`: "success" or "failed".
- `raw_log_content`: The full raw log.
- `paired_trace_id`: **REQUIRED** for failed traces. Must point to a successful trace for the same task where only syntax tokens differ. If `status` is "failed" and `paired_trace_id` is missing/null, the pipeline halts.
- `outcome_label`: "success" or "failed".

**Alternative/Supplementary Data**:
- The verified datasets listed (KisanVaani, jailbreaks-only, HF-Users) are **not** suitable for this specific research as they do not contain the required "agent execution traces" with "tool-call sequences" and "syntax tree" structures. They will not be substituted.

**Data Requirements**:
- Raw execution logs containing: System Prompt, Failed Trace, **Paired Successful Trace**, Outcome Label.
- Ground truth for "correctable" vs. "unfixable" (to be derived via the Rule-Based Oracle).

## 3. Methodology

### Phase 1: Feature Extraction (FR-001)
- **Input**: Raw execution logs.
- **Grammar & Parser Feasibility Check**: Before extraction, the system validates that the `raw_log_content` matches a defined tool-call grammar (e.g., JSON schema or Python AST). If logs are unstructured text or proprietary formats without a parseable structure, the pipeline halts with "Parser Feasibility Check Failed".
- **Process**:
  - Parse logs to reconstruct syntax trees (AST) for tool calls using the defined grammar.
  - Calculate **Syntax Tree Depth** (max depth of the AST).
  - Calculate **Token Frequency** (distribution of tokens per trace).
  - Identify **Pragmatic Markers**:
    - *Error Recovery Attempts*: Count of retry loops.
    - *State Transition Errors*: Flags for invalid state jumps.
    - *Ambiguity Flags*: Default to "neutral" if markers are ambiguous (Edge Case handling).
- **Output**: Structured JSON records with feature vectors and `status` (success/failure).

### Phase 2: Label Derivation via Rule-Based Oracle (FR-002)
- **Paired Trace Requirement**: For every trace with `status: failed`, the system checks for a `paired_trace_id` pointing to a successful trace. If missing, the pipeline halts and logs the specific trace ID.
- **Logic**: A distinct module identifies "correctable" failures based on **outcome-based criteria**.
  - A failure is labeled `correctable` ONLY if a human-verified fix exists in the dataset (via the paired trace) that modifies **ONLY** syntax tokens (typos, bracket mismatches) while preserving semantic intent.
  - This logic is **independent** of the predictor features to prevent data leakage.
- **Output**: Training triplets `(System_Prompt, Failed_Trace_Structure, Successful_Correction_Structure)` with binary labels.

### Phase 3: Model Training (FR-003 - Corrected)
- **Model**: **scikit-learn Classifier** (Random Forest or Logistic Regression).
  - *Rationale*: T5-small is a sequence-to-sequence model designed for text-to-text tasks. The input here is a numerical feature vector (depth, counts). A standard classifier is methodologically appropriate and computationally lighter. **The spec (FR-003) requires a kickback to update this requirement.**
- **Hardware**: CPU-only (float32).
- **Training**:
  - Input: Feature vectors.
  - Target: Binary classification (Correctable vs. Unfixable).
  - **Convergence Check**: Loss derivative < 1e-4 for 5 consecutive epochs (or accuracy plateau).
  - **Fallback**: If accuracy does not exceed random baseline after 10 epochs, switch to a simple heuristic model (rule-based syntax correction) and log the failure.
- **Resource Guardrails**:
  - Streaming/Chunking for large logs to stay under 7GB RAM.
  - Memory logging (FR-006/007) to verify constraints.

### Phase 4: Evaluation & Statistical Analysis (FR-004, FR-005)
- **Metric**: Artifact Delivery Score (ADS).
- **Intervention**:
  - **If Predictor predicts "correctable"**: Apply the **Syntax Rewriter** (a T5-small text-to-text model trained on the paired traces) to fix the syntax.
  - **If Predictor predicts "unfixable"**: **No intervention** (default to baseline).
- **Comparison**: Baseline vs. Adapter-Enhanced (Baseline + Rewriter for predicted correctable) on the held-out **120-task Lite set**.
- **Statistical Test**:
  - If ADS is binary per task: **McNemar's test**.
  - If ADS is continuous and normal: **Paired t-test**.
  - Otherwise: **Wilcoxon signed-rank test**.
  - **Control Condition**: The test compares the ADS of the "Baseline" configuration against the "Adapter-Enhanced" configuration where the Rewriter is applied *only* when predicted correctable, and *no change* is made for unfixable predictions.
- **Significance**: p-value compared against a pre-study determined threshold.
- **Additional Metric**: **Rewriter Success Rate** (percentage of "correctable" predictions where the rewriter actually improved the outcome) to decouple predictor accuracy from rewriter efficacy.

## 4. Statistical Rigor & Limitations

- **Multiple Comparisons**: If multiple feature subsets are tested, Bonferroni or Benjamini-Hochberg FDR correction will be applied (SC-001).
- **Power Analysis**: A pre-study power analysis will be conducted to determine the minimum detectable effect size. If the expected effect is below this range, the study notes the limitation.
- **Causal Inference**: Since this is an observational study of existing traces, all claims are framed as **associational predictions**, not causal effects.
- **Collinearity**: If predictors are definitionally related (e.g., token frequency and syntax depth), independent effects will not be claimed; relationships will be reported descriptively.
- **Dataset Variable Fit**: The plan explicitly acknowledges that EnterpriseClawBench *must* contain the required variables (traces, outcomes, paired traces). If the local data lacks these, the plan halts. No external dataset will be used to substitute missing variables.

## 5. Compute Feasibility

- **Constraint**: 2 CPU cores, ~7GB RAM, 6h runtime.
- **Strategy**:
  - **Model**: scikit-learn classifier is extremely lightweight on CPU. T5-small (if used for rewriter) is run in float32 on CPU with batch size 1.
  - **Data**: Sampled or streamed processing to avoid loading full logs into RAM.
  - **Libraries**: `transformers` (CPU mode), `scikit-learn` (no CUDA dependencies).
  - **No GPU**: No quantization requiring CUDA, no mixed-precision training.

## 6. Risk Management

- **Risk**: Dataset not available. **Mitigation**: Pipeline halts with clear error; no fabrication of URLs.
- **Risk**: Dataset lacks paired traces. **Mitigation**: Pipeline halts at Phase 2 with specific trace IDs.
- **Risk**: Model fails to converge. **Mitigation**: Fallback to rule-based heuristic; report as a finding.
- **Risk**: Memory OOM. **Mitigation**: Chunking strategy; peak memory logging.
- **Risk**: Ambiguous markers. **Mitigation**: "Neutral" classification or manual review flag.
- **Risk**: Parser failure. **Mitigation**: Pipeline halts at Phase 1 if grammar does not match.