# Research: llmXive follow-up: extending "Multi-LCB: Extending LiveCodeBench to Multiple Programming Languages"

## Research Questions

1. **Primary**: Is there an **associational improvement** in the **Logic-Compliant Pass@1 (LC-Pass@1)** rate of LLMs generating code in target languages (rust, kotlin) when provided a "Partial Logic Trace" (first 3 steps of a Python solution) as a few-shot anchor, compared to a blind baseline, **specifically for tasks exhibiting high stochastic failure (≥2/3 runs)**?
2. **Secondary**: What is the dominant failure mode for "guided" generations? (Syntax, Library, Runtime, or Logic Transfer Failure?)
3. **Methodological**: Can a CPU-only inference pipeline (using CodeLlama-1.5B via GGUF) process 200 stratified tasks with full sandbox execution within a 6-hour window on a GitHub Actions free-tier runner?

## Dataset Strategy

### Source Verification
The study relies on the **Multi-LCB** dataset (LiveCodeBench extended to multiple languages).
* **Source**: HuggingFace datasets `huypn16/LCB-R` and `huypn16/LCB-R-F`.
* **Verified URLs**:
 * `
 * `
* **Variable Fit**: The dataset contains problem statements and ground-truth Python solutions. **CRITICAL GAP**: The cited datasets (LCB-R, LCB-R-F) are primarily Python-only and **do not contain ground-truth solutions in target languages (rust/kotlin)** required for the "Logic Transfer Failure" verification (FR-004) or cross-language comparison.
* **Missing Variable Check**: The study requires "previous failed output" from the model (handled by blind run) AND **ground-truth solutions in target languages**. The latter is missing from the cited sources.

### Data Gap & Feasibility Block
**Status**: **BLOCKED**.
The study cannot proceed as designed without a verified source for multilingual ground-truth solutions (rust/kotlin). The plan assumes the existence of a "Multi-LCB" extension with these fields. If the verified datasets do not contain them, the "Logic Transfer Failure" metric (FR-004) cannot be computed for cross-language transfer.
**Action**: The implementation agent must search for a verified multilingual dataset (e.g., a specific fork or extension of LiveCodeBench with rust/kotlin solutions). If no verified source is found, the study MUST be re-scoped to **Python-to-Python Logic Fidelity** (see Plan.md Fallback Strategy) or abandon the "Logic Transfer Failure" metric.

### Selection Protocol (FR-006) - Adherence & Risk Acknowledgement
*Note: The source spec (FR-006) mandates a "Stochasticity Filter" (fail ≥2/3 runs). This plan **strictly adheres** to this requirement to maintain spec compliance, while explicitly acknowledging the resulting statistical bias.*

1. **Initial Pool**: Select tasks where the model (blind run) fails in target language (rust/kotlin) at least once in a pilot run.
2. **Stochasticity Filter (FR-006)**: Include the task **only if** it fails in **≥ 2 of the 3** blind runs.
 * **Risk**: This filter introduces **selection bias (regression to the mean)**. By selecting only the "hardest" or most stochastic tasks, the baseline Pass@1 is artificially depressed. Any intervention is statistically likely to show improvement on this subset.
 * **Mitigation**: The study results will be explicitly framed as applying **only** to this specific subset of "high-failure" tasks. No claims of generalizability to the full dataset will be made. The p-value is valid for the null hypothesis within this subset, but the effect size is confounded by the selection process.
3. **Stratification**: Ensure the final set (n=200) is stratified by Difficulty (Easy/Medium/Hard) and Topic (DP, Graphs, Math).
4. **Attrition**: If < 200 tasks remain, sample replacements from the next available pool, maintaining stratification.
5. **Bias Acknowledgement**: The selected set will consist of "hard" tasks where the model struggles. The statistical results will be explicitly framed as applying only to this subset, not the general population of coding tasks.

## Methodology & Statistical Rigor

### Experimental Design
* **Design**: Within-subjects (Paired). Each task in the final set is evaluated under two conditions:
 1. **Blind**: Standard prompt (Problem Statement + few-shot examples of *other* problems, no logic anchor).
 2. **Guided**: Prompt includes Problem Statement + **Partial Logic Trace** (first 3 steps of Python solution).
* **Unit of Analysis**: Task ID.
* **Outcome**: Binary Pass/Fail (based on sandbox execution of test cases AND AST structural comparison).

### Statistical Analysis (FR-005, SC-002)
* **Test**: McNemar's test (paired, binary outcome) comparing LC-Pass@1 rates between Blind and Guided conditions on the *same* 200 tasks.
* **Significance**: Alpha = 0.05.
* **Power Justification**: With n=200 paired observations, the study has sufficient power to detect a moderate effect size (e.g., a 10-15% absolute improvement in LC-Pass@1) assuming a baseline failure rate of >50%. If the baseline failure rate is low, power is reduced; this will be acknowledged in the report.
* **Causal Inference**: This is an observational intervention (no randomization of tasks to conditions; all tasks get both). Findings will be framed as **associational improvements** in generation correctness, not causal proof of "reasoning transfer."
* **Multiple Comparisons**: Only one primary hypothesis test (McNemar's) is performed. If secondary analyses (e.g., per-language) are conducted, a Bonferroni correction will be applied to the alpha threshold.
* **Limitations**: The p-value applies only to the selected subset of "hard" tasks (filtered by FR-006). The selection bias (regression to the mean) means the observed improvement may be partially an artifact of the selection process. The study explicitly limits its claims to this subset.

### Measurement Validity
* **Logic Anchor**: Validated by AST parsing of the ground-truth Python solution. The "first 3 steps" are defined by distinct algorithmic operations (initialization, loop entry, recursive call) to ensure they represent the core logic, not just syntax.
* **LC-Pass@1**: Validated by the Multi-LCB execution harness (test suite) AND **AST Structural Comparison**.
* **Error Categorization**: Deterministic rules based on execution logs (FR-004).
 * **Logic Transfer Failure**: Detected via **AST structural comparison** between the generated code and the anchor steps. If the generated code passes tests but its AST structure significantly deviates from the anchor (e.g., different control flow structure for the same logic), it is flagged as "Logic Transfer Failure."
 * **Caveat**: AST comparison is a heuristic. It may miss semantic equivalence achieved via different syntax or false positives if the anchor steps are too rigid. This limitation will be noted in the report.

### Compute Feasibility & Constraints
* **Hardware**: GitHub Actions Free Tier (2 CPU, 7GB RAM, No GPU).
* **Model Strategy**:
 * **Primary**: Use **CodeLlama-1.5B** model in standard precision (float16) or **7B model quantized to Q4_K_M via GGUF** (via `llama-cpp-python`).
 * **Memory Calculation**:
 * 1.5B model: ~2GB RAM (fits easily).
 * 7B GGUF (Q4_K_M): ~4.5GB RAM (fits within 7GB).
 * Large-scale float16 models: ~14GB RAM (OOM).
 * **NO** `bitsandbytes` (requires CUDA).
 * **NO** GPU device mapping.
 * **Quantization**: Use `llama-cpp-python` for GGUF loading on CPU.
* **Runtime**:
 * Inference time per task (1.5B): ~10-15s (CPU).
 * Inference time per task (7B GGUF): ~30-40s (CPU).
 * Sandbox execution: <10s per test case.
 * **Parallelization**: Tasks are processed in parallel batches (max 4 concurrent) using `joblib` to maximize CPU utilization and meet the 6h limit.
 * **Total Budget**: 200 tasks * 2 conditions * [deferred] = [deferred] ([deferred]) + overhead. Feasible within 6h.

## Risk Assessment & Mitigation

| Risk | Impact | Mitigation |
|:--- |:--- |:--- |
| **Model OOM on CPU** | High (Pipeline fails) | Use 1.5B model or GGUF-quantized 7B. Stream dataset. |
| **Infinite Loop in Sandbox** | High (Runner hangs) | Enforce hard 10s timeout per test case (FR-003). |
| **Logic Anchor Extraction Fails** | Medium (Data loss) | Skip task, log "Anchor Extraction Failed", adjust N dynamically. |
| **Data Gap (No Multilingual Ground Truth)** | **Critical** (Study invalid) | **Block study** until verified multilingual dataset found, or re-scope to Python-only. |
| **Logic Transfer Detection False Neg** | Medium (Metric inflation) | Refine AST comparison; manual spot-check of a subset. |
| **Selection Bias (FR-006)** | **High** (Validity of improvement metric) | **Adhere to spec** (FR-006) but **explicitly acknowledge** the bias in the report. Frame results as valid *only* for the "high-failure" subset. Do not claim generalizability. |

## References & Verified Datasets

* **Multi-LCB (LCB-R)**: `
* **Multi-LCB (LCB-R-F)**: `
* **LiveCodeBench (Original)**: (Referenced conceptually; dataset used is the extended version above).

*Note: No other dataset URLs are cited. All sources are from the verified block. The study is blocked if these sources do not contain the required multilingual ground truths.*