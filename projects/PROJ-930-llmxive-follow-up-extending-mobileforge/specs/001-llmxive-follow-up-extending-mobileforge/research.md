# Research: MobileForge Logic Distillation

## Research Question

To what extent does the "hint-contextualized" feedback signal in HiFPO capture *associational* logical reasoning patterns that can be distilled into a lightweight, CPU-tractable model for GUI action planning, independent of the visual policy's representation learning?

## Hypothesis

The "hint" signal contains sufficient logical structure to allow a small, Encoder-Decoder model (T5-small, ≤100M params) to outperform a non-distilled base LLM (TinyLlama) on GUI planning tasks when evaluated on unseen tasks *with the same hint context*, provided the training data is strictly filtered for "failed-then-success" trajectories. Claims are framed as *associational* due to the observational nature of the data.

## Dataset Strategy

### Verified Sources
The plan relies exclusively on the following verified datasets. No other sources are used.

| Dataset Name | Verified URL | Role | Notes |
|:--- |:--- |:--- |:--- |
| **MobileForge Generated Tasks** | ` | Primary Training Source | Contains trajectories, hints, and actions. |
| **MobileForge Exploration** | ` | Context Metadata | App metadata for UI state parsing. |
| **MobileForge Benchmark** | ` | Validation Reference | Manifest for benchmark results. |
| **AndroidWorld Tasks** | *See "Evaluation Data" section* | Evaluation Set | Logically disjoint set of unseen tasks. |

### Data Extraction & Filtering
1. **Source**: The `generated_tasks_26020301-all.csv` will be downloaded via `datasets.load_dataset` (streaming mode if size > 7GB) or direct URL fetch.
2. **Filtering Logic**:
 * Identify trajectories where `initial_status == "failed"` AND `post_hint_status == "success"`.
 * **Constraint Check**: Verify `Corrective_Hint` contains no coordinate-based visual grounding (regex check for pixel coordinates or bounding boxes).
 * **Completeness**: Ensure `UI_state_description`, `Corrective_Hint`, and `Optimal_Action_Sequence` are non-null.
3. **Output**: A processed Parquet file (`data/processed/extraction_dataset.parquet`) containing ≥ [deferred] valid triples.
 * *Note*: The spec assumes ≥5,000 valid triples. If the verified source yields fewer, the plan will explicitly report the shortage and adjust the training sample size, noting the power limitation.
4. **Pre-Training Ablation**: A control model will be trained on `UI_state` only (no hint) to verify the hint is the primary driver of success, addressing construct validity.

### Evaluation Data
* **Source**: AndroidWorld tasks (logically disjoint from training).
* **Acquisition**: The plan assumes access to the AndroidWorld benchmark suite (DOI: 10.48550/arXiv.2405.14793). Since a direct download URL for the *evaluation tasks* is not in the verified block, the implementation will use the public AndroidWorld repository or a verified Hugging Face mirror if available in the code execution environment.
* **Constraint**: A set of tasks must be disjoint from the training set to ensure generalizability.
* **Generalizability Scope**: Primary evaluation is restricted to tasks with "high-confidence hints" (filtered via heuristic) to match the training distribution. A secondary "Stress Test" will evaluate performance on ambiguous hints to measure distribution shift.

## Model Strategy

### Architecture
* **Type**: Encoder-Decoder Transformer (T5-small).
* **Parameters**: ≤ 100M.
* **Rationale**: T5-small is required for variable-length sequence generation (action sequences). Encoder-only models (DistilBERT) cannot natively generate sequences without reformulating the task as classification, which contradicts the goal.
* **Input**: Concatenation of `[UI_state_description] + [Corrective_Hint]`.
* **Output**: Token sequence representing the `Optimal_Action_Sequence`.

### Training Constraints
* **Hardware**: CPU-only (GitHub Actions runner).
* **Memory**: ≤ 7GB RAM.
* **Time**: ≤ 6 hours.
* **Strategy**:
 * Use `torch.no_grad()` where possible.
 * Batch size tuned to fit RAM (likely in the low double digits).
 * Learning rate warmup and cosine decay.
 * **No GPU**: Explicitly set `device="cpu"` in the training loop.

### Baseline
* **Model**: TinyLlama (non-distilled, base version).
* **Role**: Primary baseline for the paired statistical test (FR-005).
* **Condition**: Evaluated **with the same hint context** as the distilled model. This ensures the test measures "does distillation help?" (comparing two models with hints) rather than "does a hint help?".
* **Inference**: Run on CPU with quantization (if needed) to fit RAM.

### Ablation Study (Constitution Principle VII)
* **Condition**: "Generic retry" prompt.
* **Logic**: Replace `Corrective_Hint` with a generic prompt: "Try again" or "Retry the task".
* **Purpose**: Verify that performance gains are specifically due to the hint-contextualized reasoning and not merely the presence of additional text context.
* **Integration**: This is a secondary comparison. The primary statistical test (FR-005) is against the TinyLlama baseline.

## Statistical Rigor & Methodology

### Statistical Tests
1. **Primary Test**: **McNemar's Test** (for paired binary outcomes).
 * **Unit of Analysis**: Each of the 500 unseen tasks.
 * **Pairing**: For each task `i`, measure `Success_i_distilled` and `Success_i_baseline`.
 * **Rationale**: Success is binary (0/1). McNemar's test is appropriate for paired binary data, avoiding the normality assumption issues of a t-test on binary data.
 * **Correction**: If multiple metrics (Success Rate, Step Efficiency) are tested, apply Bonferroni or Holm correction.
2. **Effect Size & Power**: **Observed Effect Size Reporting**.
 * **Input**: Observed effect size (Cohen's d or odds ratio) from the McNemar's test.
 * **Goal**: Report the observed effect size and confidence intervals. **Post-hoc power analysis is not performed** due to tautology.
 * **A Priori Analysis**: An a priori power analysis is conducted to justify N=500 for a moderate effect size in binary outcomes, acknowledging that high variance in observational data may reduce power.
3. **Sensitivity Analysis**:
 * Sweep `inconsistency_tolerance` threshold across a range of values.
 * Measure variance in Success Rate.
 * **Target**: Variance ≤ 5% (SC-005).

### Causal & Validity Assumptions
* **Observational Nature**: The training data is observational (logs). Claims are framed as "associational" unless the randomization of hints in the original study is verified.
* **Measurement Validity**: `Corrective_Hint` is assumed to be the primary driver of the "success" in the filtered trajectories (verified via Pre-Training Ablation).
* **Collinearity**: `UI_state_description` and `Corrective_Hint` may be correlated. The model architecture (Encoder-Decoder) handles this, but independent effects are not claimed; the *combination* is the predictor.
* **Confounding Control**: Task difficulty and UI complexity are controlled via propensity scoring and difficulty matching in the evaluation set selection.

### Generalizability Limitation
* **Selection Bias**: Training on "failed-then-success" cases introduces selection bias. The model learns a distribution of "hints that worked".
* **Mitigation**: The evaluation includes a "Stress Test" on ambiguous hints to measure the distribution shift. Primary claims are limited to "high-confidence hint" tasks.

## Compute Feasibility

### CPU-First Strategy
* **Training**: T5-small (≤100M params) on a subset of the data (or full if streaming) is feasible on 2-core/7GB RAM.
* **Inference**: A batch of tasks × 3 models (Distilled, Baseline, Ablation) × [deferred]/task = [deferred] total inference time. Well within 6h limit.
* **Streaming**: If the MobileForge CSV exceeds memory, use `datasets.load_dataset(..., streaming=True)` to process in chunks.

### GPU Escape Hatch (Not Required)
* This project is designed to be **fully CPU-tractable**. No GPU escape hatch is needed. If the CPU run fails due to RAM, the plan will switch to a smaller batch size or a smaller model variant (e.g., T5-small-tiny), not a GPU run.

## Risks & Mitigations

| Risk | Mitigation |
|:--- |:--- |
| **Dataset Insufficiency** (<5k triples) | Report actual count; adjust N for power analysis; explicitly state power limitation. |
| **Model Non-Convergence** | Monitor loss; if no convergence, flag as "Model Failure" and analyze dataset quality (ablation). |
| **Emulator Crashes** | Retry logic (attempts); mark as "Environment Error" and exclude from success rate. |
| **Hint Ambiguity** | Strict regex filtering to exclude non-linguistic hints; 'Stress Test' for generalization. |
| **Selection Bias** | 'Stress Test' on ambiguous hints; 'Confounding Control' via difficulty matching. |
| **Distribution Shift** | Explicitly report failure rate on ambiguous hints; limit primary claims to 'high-confidence hint' tasks. |
| **Generic Retry Prompt** | If the ablation fails, it indicates the model relies on the hint. This is a successful validation of the hypothesis. |
| **Spec Conflict (Encoder-Only)** | Plan uses T5-small (Encoder-Decoder) for sequence generation. Spec.md requires kickback to update FR-002. |
| **Spec Conflict (Post-Hoc Power)** | Plan uses A Priori analysis and observed effect size. Spec.md requires kickback to update Assumptions. |