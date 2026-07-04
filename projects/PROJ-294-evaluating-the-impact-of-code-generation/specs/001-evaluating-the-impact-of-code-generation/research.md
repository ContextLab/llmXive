# Research: Evaluating the Impact of Code Generation Models on Code Testability

## Dataset Strategy

The study relies on the **HumanEval** benchmark, a standard dataset for evaluating code generation models. The dataset is accessed via the HuggingFace `datasets` library to ensure reproducibility and integrity.

| Dataset Name | Purpose | Verified Source URL | Loading Strategy |
|--------------|---------|---------------------|------------------|
| HumanEval | Primary source of task prompts and human reference solutions. | ` | `datasets.load_dataset("openai/openai_humaneval")` |

**Note**: Model details (e.g., CodeLlama-7B) are referenced via their official HuggingFace model cards (not loaded as datasets). No other datasets are loaded for analysis.

**Dataset Fit Verification**:
- **Required Variables**: `prompt` (task description), `canonical_solution` (human reference), `test` (test suite).
- **Verification**: The HumanEval dataset from the verified URL contains exactly these fields. No additional variables (e.g., post-task anxiety) are required for this study.
- **Mismatch Handling**: If the dataset structure changes, the pipeline will fail at the `download_data.py` stage, logging the error and halting execution (per Constitution Principle III).

## Methodology & Statistical Rigor

### Operational Definition of Testability
This study operationalizes "testability" through two proxies:
1. **Structural Testability**: Measured by Cyclomatic Complexity and Halstead Volume. Higher values imply harder-to-test code (maintenance cost proxy).
2. **Functional Testability**: Measured by Branch Coverage on the *provided* HumanEval test suite. This is **not** a claim that the code is "testable" in a broad sense, but rather that the *provided test suite* is effective at covering the branches of the generated code. This metric is used to compare how well the HumanEval tests cover human vs. LLM code.

**Clarification on Causality**: The paired design (same task, different model) allows us to make a causal claim about the **Model Effect** on the solution's properties *within that specific task*. We are testing whether the model *causes* a difference in complexity or coverage for a given task, not whether the dataset as a whole is different.

### Statistical Tests
1. **Wilcoxon Signed-Rank Test**: Used for continuous metrics (Cyclomatic Complexity, Halstead Volume).
 * **Rationale**: Data is paired and may not be normally distributed.
 * **Multiple Comparison Correction**: Since two continuous metrics are tested, the **Benjamini-Hochberg** procedure will be applied to control the False Discovery Rate (FDR) at $\alpha = 0.05$.
2. **Permutation Test (Randomization Test)**: Used for **Branch Coverage %**.
 * **Rationale**: Coverage is bounded [0, 100] and often exhibits floor/ceiling effects or bimodality. Wilcoxon assumes symmetric differences, which may not hold. The permutation test makes no distributional assumptions and is robust to ties.
 * **Fallback**: If the permutation test is computationally prohibitive (unlikely for n=50), Wilcoxon will be used with a caveat in the report regarding distributional assumptions.
3. **McNemar's Test**: Used for binary pass-rate outcomes (Pass/Fail).
 * **Rationale**: Tests for marginal homogeneity in paired binary data.
 * **Assumption**: Requires sufficient discordant pairs. If discordant pairs < 25, Fisher's Exact Test will be used as a fallback.
4. **Power Analysis**:
 * **A Priori**: Calculated for paired t-test (equivalent to Wilcoxon for planning) with effect size $d=0.5$, $\alpha=0.05$, power $\ge 0.8$. Target $n \approx 38$.
 * **Post Hoc**: Calculated after data collection using observed effect sizes to validate achieved power.

### Collinearity Handling
Cyclomatic Complexity and Halstead Volume are definitionally correlated. The plan will **not** use them as independent predictors in a single regression model. Instead, they will be tested as separate univariate outcomes. Their correlation will be reported descriptively in the results, but no causal claims about one predicting the other will be made.

## Compute Feasibility & Constraints

### Environment
- **Platform**: GitHub Actions free-tier (2 CPU, ~7GB RAM, ~14GB Disk).
- **GPU**: None.
- **Time Limit**: 6 hours.

### Model Strategy
1. **Primary Model**: `Salesforce/codegen-350M-mono`.
 * **Feasibility**: ~350M parameters fits easily in CPU RAM. No quantization needed.
 * **Library**: `transformers` with `torch` (CPU).
2. **Sensitivity Model**: `CodeLlama-7B`.
 * **Feasibility**: Large-scale parameter counts exceed available RAM in full precision. 4-bit quantization locally is high-risk.
 * **Primary Strategy**: Use **HuggingFace Inference API** for CodeLlama-7B to avoid local memory constraints.
 * **Fallback Strategy**: If API fails, attempt local 4-bit quantization using `bitsandbytes` (if available on CPU) or switch to `CodeLlama-3B` (smaller, fits in RAM).
 * **Protocol**: If the fallback to CodeLlama-3B is triggered, it applies to **all** tasks in the sensitivity subset to maintain a clean comparison. If the fallback fails for any task, that task is excluded from the sensitivity analysis.

### Data Handling
- **Subset**: A subset of tasks is processed.
- **Memory**: Intermediate metrics stored in JSON/CSV, not large in-memory DataFrames.
- **Disk**: Generated code and logs are cleaned up or archived to `state/` only if successful.

## Sensitivity Analysis Protocol

To avoid confounding model size with model architecture, the sensitivity analysis follows a strict protocol:
1. **Disjoint Subset**: 10 tasks are randomly selected from the original 50 to be used *only* for sensitivity analysis. A subset of the remaining data is used for the primary analysis.
2. **Uniform Model**: All 10 sensitivity tasks must be generated by the same model (either 7B or 3B). If the API fails for one task, the pipeline attempts the fallback for *all* 10 tasks.
3. **Reporting**: Results are compared to the primary model's metrics for the same 10 tasks. If the fallback model is used, the report explicitly states "Sensitivity Analysis: CodeLlama-3B (Fallback)".

## Risk Mitigation

| Risk | Mitigation Strategy |
|------|---------------------|
| **Model Inference Failure** | Retry logic (3 attempts) per FR-002. If all fail, mark as missing and exclude from paired analysis (FR-002). |
| **Memory Overflow** | Use `torch.no_grad()` and explicit garbage collection. Fallback to smaller model or API if 7B quantization fails. |
| **Dataset Unavailability** | Pin exact commit hash and record SHA256. If URL changes, pipeline halts with error (Constitution Principle VII). |
| **Statistical Power Insufficiency** | A priori power analysis targets $n \ge 38$. If $n < 40$ is achieved, the report will explicitly state the reduced power and interpret results with caution (FR-008). |
| **API Rate Limits** | Sensitivity analysis via API may be rate-limited. Fallback to CodeLlama-3B or skip sensitivity analysis if API fails (FR-009). |

## References
- **Zhou et al., 2023**: Source for effect size $d=0.5$ assumption (as per spec).
- **HumanEval Dataset**: OpenAI (verified via HuggingFace).
- **McNemar Test**: Standard statistical method (no specific URL required).
- **Permutation Test**: Standard statistical method for bounded data (no specific URL required).