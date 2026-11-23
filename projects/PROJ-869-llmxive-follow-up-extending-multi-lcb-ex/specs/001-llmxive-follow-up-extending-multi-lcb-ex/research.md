# Research: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

## 1. Problem Statement & Hypothesis

**Problem**: LLMs often fail to generate correct code in low-resource languages (Rust, Kotlin) even when they succeed in Python, suggesting a bottleneck in syntax/idiom translation rather than algorithmic reasoning.

**Hypothesis**: Providing a "Partial Logic Trace" (first 3 algorithmic steps of a ground-truth Python solution) as a few-shot anchor significantly improves the model's ability to complete the logic in the target language, bridging the gap between reasoning capability and syntactic execution.

**Null Hypothesis ($H_0$)**: The "guided" condition (with anchor) yields no statistically significant improvement in Pass@1 over the "blind" condition (without anchor) for the same set of tasks where the model previously failed blindly.

**Alternative Hypothesis ($H_1$)**: The "guided" condition yields a statistically significant improvement in Pass@1 (p < 0.05, McNemar's test).

## 2. Dataset Strategy

### Verified Datasets
The study relies exclusively on the **Multi-LCB (LiveCodeBench Extended)** dataset, which contains algorithmic problems with ground-truth solutions in multiple languages.

| Dataset Name | Source URL | Verified Status | Usage |
|--------------|------------|-----------------|-------|
| LCB Test Set (Parquet) | ` | Verified | Primary source of problems, Python ground truth, and test cases. |
| LCB-F Test Set (Parquet) | ` | Verified | Supplementary test set for diversity. |
| LCB Train Set (Parquet) | ` | Verified | Used for initial model warm-up or validation if needed (not primary eval). |

**Data Access Method**:
- The implementation will use the `datasets` library with `streaming=True` to avoid loading the full dataset into memory (exceeding 7GB RAM).
- Data will be cached locally in `data/raw/` with SHA-256 checksums recorded in `state/` to satisfy Constitution Principle III.
- **No access-gated data**: All selected datasets are public and directly downloadable without credentials.

### Dataset Variable Fit
- **Predictors**: Problem difficulty, topic, target language.
- **Outcomes**: Pass@1 (binary), Error Type (categorical).
- **Covariates**: Model temperature, anchor step count (fixed at 3).
- **Fit Check**: The dataset contains the required variables: `problem_statement`, `python_solution` (for anchor extraction), `test_cases` (for execution), and `metadata` (difficulty/topic). No missing variables detected.

## 3. Methodology & Statistical Rigor

### Experimental Design
1. **Task Selection (Stratified Sampling)**:
 - Identify tasks where the model previously failed in the target language (Pass@1 < 1.0) but succeeded in Python.
 - Apply a **Stochasticity Filter**: Re-run the "blind" condition 3 times.
 - **Critical Constraint**: All 3 runs MUST use fixed random seed (42) and fixed temperature (0.7) to ensure reproducibility.
 - Retain only tasks that fail in ≥ 2 of 3 runs.
 - **Attrition Handling**: If < 200 tasks remain, sample replacements from the next pool, maintaining stratification (Topic ≤ 30%, Difficulty balanced).
 - **Final Set**: Target N=200 tasks (stratified by Difficulty, Topic, Language Pair). *Note: If the filtered set is < 50 or the baseline is too low, the study reports the limitation.*

2. **Intervention (Logic Anchor)**:
 - **Anchor Extraction**: Parse the ground-truth Python solution into an AST. Extract the first distinct algorithmic operations (e.g., initialization, loop entry, recursive call).
 - **Format**: Serialize as **language-agnostic pseudo-code only** (NOT Python syntax) to avoid the translation confound.
 - **Prompt Construction**:
 - *Blind*: `[Problem Statement] + [Target Language] + [Instruction]`
 - *Guided*: `[Problem Statement] + [Partial Logic Trace (Pseudo-code)] + [Target Language] + [Instruction: "Complete the logic based on these steps"]`

3. **Execution & Verification**:
 - Run inference on the CPU-only runner (quantized model, small context).
 - **Re-verify Baseline**: Re-run the "blind" condition on the **final filtered set** to establish the exact "Blind" state for the paired test. This ensures the paired data (Blind vs. Guided) comes from the same execution context.
 - Execute generated code in a sandboxed subprocess with a **10-second timeout** per test case.
 - Record Pass/Fail and error logs.

4. **Statistical Analysis**:
 - **Primary Test**: Paired McNemar's test comparing Pass@1 (Blind vs. Guided) on the *same* tasks, using the **re-verified** blind baseline.
 - **Bias Correction**: Perform **Bootstrap Resampling** (1000 iterations) to account for the selection bias introduced by the "hard task" filter.
 - **Significance Threshold**: $\alpha = 0.05$.
 - **Multiple Comparisons**: If analyzing multiple languages/topics separately, apply Bonferroni correction ($\alpha_{adj} = 0.05 / k$).
 - **Power & Bias Mitigation**: If the observed baseline Pass@1 is < 0.05 or the sample size is < 50, the study will switch to descriptive statistics or an exact binomial test and explicitly report the power limitation.

### Power & Bias Analysis
- **Selection Bias**: The "Stochasticity Filter" selects tasks specifically for high failure rates in the blind condition. Consequently, the baseline Pass@1 for this subset is expected to be significantly lower than the population average (potentially < 0.1).
- **Power Justification**: The **Target N=200** sample size is calculated to detect a moderate effect size (Cohen's $h \approx 0.3$) *given the filtered baseline*. However, if the baseline is extremely low (e.g., 0.05), the absolute improvement required for significance may be small, but the relative improvement will be large.
- **Mitigation**: We will explicitly report the observed baseline Pass@1 for the filtered set. The use of Bootstrap Resampling (1000 iterations) is critical here to generate robust confidence intervals that do not rely on the asymptotic assumptions of McNemar's test, which may be unstable with highly skewed data (many failures, few successes). **Crucially, if the baseline is 0.0 or the sample size is insufficient, the study will not force a McNemar's test but will instead report the limitation and use descriptive statistics.**

### Paired Data Integrity
- **Re-verified Baseline**: The "blind" condition state for the final test is **not** the aggregate from the filter phase (fail ≥ 2/3). Instead, the "blind" condition is **re-executed** on the final filtered set using the same seed (42) and temperature (0.7). This ensures that the "Blind" outcome in the paired test is the exact result of the execution that generated the "Guided" outcome, eliminating any risk of stochasticity drift between the filter and the main run.
- **Pairing Validity**: The paired test compares the *same* task ID under two conditions (Blind vs. Guided), both executed in the same run context. This ensures the paired nature of the data is preserved.

### Causal Inference & Assumptions
- **Observational Nature**: The "guided" condition is an intervention, but the study is not a randomized controlled trial (RCT) of the model's internal state. Findings are framed as **associational improvements** in code generation performance.
- **Collinearity**: The "Partial Logic Trace" is derived from the ground truth, which is definitionally related to the correct solution. We do not claim "independent effects" of the trace; rather, we measure the *utility* of the trace as a scaffold.
- **Measurement Validity**: The "Pass" metric relies on the Multi-LCB test suite, which is a standard benchmark for algorithmic correctness.
- **Metric Definition**: The primary metric is "Completion of Remaining Steps" (Pass@1 given 3 steps), acknowledging that providing the first 3 steps of the solution inherently makes the task easier than solving from scratch. This is a measure of *scaffolding utility*, not *de novo* reasoning.

## 4. Compute Feasibility

### CPU-First Strategy
- **Model**: `meta-llama/Llama-2-7b-hf` (or similar 7B model) loaded with `torch_dtype=torch.float16` and `device_map="cpu"` (or `bitsandbytes` 8-bit if memory permits, but default CPU float16 is preferred for stability on 7GB RAM).
- **Optimization**:
 - Batch size = 1 (sequential processing).
 - Max context = 2048 tokens (to fit in RAM).
 - Streaming dataset loading to avoid OOM.
- **Time Budget**: A substantial number of tasks across multiple conditions involving deferred inference and execution will incur deferred costs and overhead. Well within the -hour limit.

### GPU Escape Hatch
- **Trigger**: If the model fails to load or inference is too slow on CPU (e.g., > 30s per task), the execution stage will auto-offload to a Kaggle GPU.
- **Scaled GPU Form**: If offloaded, run `device="cuda"` with `load_in_8bit=True` to fit larger models or faster inference. The plan does *not* simulate GPU behavior; it relies on the real offload mechanism.

## 5. Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Infinite Loop in Generated Code** | Runner crash, timeout exhaustion. | Hard 10s timeout per test case; `subprocess` kill on timeout. |
| **Memory Overflow (OOM)** | Process killed on CI. | Streaming dataset; batch size 1; model quantization. |
| **Anchor Extraction Failure** | Task skipped, dataset size reduced. | Fallback to "skip task" logic; dynamic adjustment of target N. |
| **Sandbox Dependency Missing** | False "Runtime Error". | Pre-verify sandbox environment; log "Env Missing" as distinct error. |
| **Low Pass@1 Baseline** | Statistical power insufficient. | **Dynamic Power Adjustment**: If baseline < 0.05 or N < 50, report limitation and use descriptive statistics or exact binomial test. |
| **Selection Bias** | Invalid p-value interpretation. | Use Bootstrap Resampling to account for non-random sampling of "hard" tasks; re-verify baseline to ensure pairing integrity. |

## 6. Decision Rationale

- **Why McNemar's?** The data is paired (same task, two conditions). McNemar's is the standard test for binary paired data (Pass/Fail) and controls for task difficulty variance.
- **Why Bootstrap?** The task selection (filtering for "hard" tasks) introduces selection bias. Bootstrap resampling provides a more robust estimate of the confidence interval for the improvement.
- **Why CPU-First?** The project must run on GitHub Actions free tier. GPU access is an "escape hatch," not the default. CPU-optimized models (quantized) are sufficient for inference on 7B parameter models.
- **Why Streaming?** The full dataset may exceed available RAM capacity. Streaming ensures we can process the full real dataset (or a large sample) without OOM errors.
- **Why Pseudo-code?** Using Python syntax for the anchor in a Rust/Kotlin target would conflate "logic scaffolding" with "syntax translation." Pseudo-code isolates the logic transfer hypothesis.
- **Why Re-verify Baseline?** To ensure the "Blind" state in the final paired test is the exact result of the execution that generated the "Guided" outcome, eliminating any risk of stochasticity drift between the filter and the main run.
