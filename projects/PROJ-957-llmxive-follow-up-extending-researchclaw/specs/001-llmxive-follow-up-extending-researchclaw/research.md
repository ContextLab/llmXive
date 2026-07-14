# Research: llmXive follow-up: extending "ResearchClawBench: A Benchmark for End-to-End Autonomous Scientific Re"

## Executive Summary

This research validates whether injecting domain-specific procedural scaffolds into autonomous scientific agents improves "Protocol Alignment" without degrading "Scientific Core" reasoning. The study targets 10 tasks from the ResearchClawBench dataset previously flagged for "experimental protocol mismatch". We compare Zero-Shot vs. Scaffolded conditions using 7 agents, applying paired statistical tests (t-test/Wilcoxon) and a TOST equivalence test (margin=5) to ensure safety.

## Dataset Strategy

### Verified Datasets
- **ResearchClawBench**: NO verified source found (do NOT cite a URL for it).
  - **Status**: The spec assumes the existence of a metadata field `failure_mode` or similar identifying "experimental protocol mismatch".
  - **Action**: The system MUST attempt to load the dataset from the canonical source referenced in the original study (arXiv:2606.07591) or the project's internal data registry. If the dataset is not available via a verified URL or a standard loader (e.g., `datasets.load_dataset`), the system MUST abort with a critical error (FR-006) and log the missing source.
  - **Constraint**: If the dataset lacks the specific "protocol mismatch" metadata, the experiment cannot proceed. A `failure_mode_audit.csv` will be generated if partial data is available, but the primary analysis requires the 10 specific tasks.
  - **Fallback**: If the specific metadata is missing, the system will attempt to infer the failure mode via text classification (with a warning) or abort. It will NOT invent a dataset.

### Data Selection & Filtering
1. **Load**: Fetch the full ResearchClawBench dataset.
2. **Filter**: Select tasks where `failure_mode` == "experimental protocol mismatch" (or equivalent metadata key).
3. **Subset**: If >10 tasks exist, select the first 10 (deterministic sort by task ID). If <10, abort (FR-006).
4. **Persist**: Write the 10-task subset to `data/processed/10_tasks_protocol_mismatch.json` with a SHA-256 checksum.

## Experimental Design

### Conditions
1. **Zero-Shot**: Agent receives the standard task description and hidden target paper.
2. **Scaffolded**: Agent receives the task description + hidden target paper + a domain-specific procedural template (injected into the system prompt).

### Templates
- **Source**: Curated from open-access laboratory manuals (Curated Template Set v1.0).
- **Storage**: `assets/templates/TEMPLATE-001-v1.0.md`.
- **Validation**: Templates are validated against task constraints via `constraint_keywords` (FR-007). Conflicts trigger exclusion and logging.

### Agents
- **Scope**: 7 autonomous agents from the original study.
- **Execution**: Each agent runs on all tasks in both conditions.
- **Constraints**: 6-hour timeout per run; concurrency limit of 7; total wall-clock budget 24 hours.

## Statistical Analysis Plan

### Metrics
- **Protocol Alignment (0-50)**: Measures adherence to procedural steps.
- **Scientific Core**: Measures the quality of the scientific hypothesis/reasoning.

### Tests
1. **Protocol Alignment**:
   - **Test**: Paired t-test (if normality holds) or Wilcoxon signed-rank test (if non-normal).
   - **Normality Check**: Shapiro-Wilk test on the difference scores.
   - **Output**: p-value, test statistic, effect size (Cohen's d or rank-biserial r), 95% CI.
   - **Hypothesis**: Scaffolded > Zero-Shot.
   - **Power**: With N=10, power to detect moderate effect (d=0.5) is <0.4. Results with p < 0.05 will be reported as "suggestive" but not definitive due to low power.

2. **Scientific Core**:
   - **Test**: Two One-Sided Tests (TOST) for equivalence.
   - **Margin**: 5 points (10% of the 0-50 scale, a standard MCID convention).
   - **Output**: TOST p-values (lower and upper), equivalence conclusion ("safe" if p < 0.05 for both).
   - **Hypothesis**: No significant difference (equivalence) within the margin.
   - **Power**: With N=10, power to detect equivalence within this narrow margin is extremely low (<0.1). A non-significant result will be reported as "inconclusive" regarding safety, not as proof of equivalence.

### Agent Variance
- **Strategy**: The analysis will treat 'Agent' as a blocking factor (using a mixed-effects model or stratified analysis) to account for agent-specific variance. If a simple paired test is used, the limitation will be explicitly reported.

## Decision Rationale

### CPU-Only Execution
The plan explicitly avoids GPU/CUDA dependencies to ensure compatibility with the GitHub Actions free-tier runner (limited CPU and RAM resources). Agents are selected/implemented to be CPU-tractable. If an agent requires GPU, it is excluded or replaced with a CPU-compatible variant, documented in `agents/loader.py`.

### Statistical Test Selection
The plan adheres to FR-005 by performing a normality check (Shapiro-Wilk). If the assumption of normality is violated (p < 0.05), the non-parametric Wilcoxon test is used. This ensures robustness against the small sample size (N=10).

### Equivalence Testing (TOST)
Standard t-tests cannot prove "no difference". TOST is used to establish that the Scaffolded condition does not degrade scientific reasoning beyond a clinically meaningful margin. This aligns with the safety-bound requirement of FR-005.

## Scientific Soundness & Interpretation

### Causal Interpretation
The study tests "instruction following" vs "autonomous retrieval". The improvement in "Protocol Alignment" reflects the efficacy of the scaffold in providing the correct protocol, not necessarily improved autonomous reasoning. The metric improvement is expected if the agent follows the provided text.

### Rubric Independence
The "Scientific Core" rubric is designed to ignore procedural text and focus solely on the hypothesis/reasoning content. The dummy test (FR-008) validates that the rubric scores steps, not scaffold text.

### TOST Interpretation
Given the low power (N=10), a non-significant TOST result (failure to reject non-equivalence) is the default outcome and will be reported as "inconclusive" regarding safety, not as proof of equivalence. The test is underpowered to prove the null hypothesis of equivalence.

## Risks & Mitigations

| Risk | Mitigation |
| :--- | :--- |
| **Dataset Missing Metadata** | FR-006: System aborts with critical error if "protocol mismatch" flag is missing. |
| **Scaffold Conflict** | FR-007: `validator.py` checks constraints; conflicts logged and excluded from analysis. |
| **Timeouts** | 6-hour timeout per run; failed runs excluded from statistical calculation. |
| **Low Statistical Power** | Explicitly reported in final analysis; results interpreted as "inconclusive" if not significant. |
| **Rubric Bias** | FR-008: Contract test with dummy outputs (Set A vs. Set B) validates rubric sensitivity to steps vs. text. |
