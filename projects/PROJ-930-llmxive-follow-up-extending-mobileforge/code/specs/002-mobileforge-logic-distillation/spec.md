# MobileForge Logic Distillation Specification

## User Stories

### US-1: Data Extraction
As a researcher, I want to extract clean `(UI_state, Corrective_Hint, Action)` triples from MobileForge logs so that I can train a distilled model without coordinate-based visual grounding.

### US-2: CPU-Tractable Training
As a researcher, I want to train a T5-small (Encoder-Decoder) model on a standard CPU so that I can achieve sequence generation capabilities without GPU infrastructure.

### US-3: Statistical Validation
As a researcher, I want to evaluate the distilled model against a TinyLlama baseline using McNemar's test on paired binary outcomes so that I can rigorously validate performance improvements with appropriate statistical power.

## Functional Requirements

### FR-001: Log Parsing
The system must parse raw MobileForge logs to extract UI states, hints, and actions.

### FR-002: Model Architecture
The distilled model MUST be an **Encoder-Decoder architecture (e.g., T5-small)**.
*Justification*: Sequence generation requires an Encoder-Decoder architecture; encoder-only models (like DistilBERT) cannot natively generate variable-length sequences.

### FR-003: Sample Size Determination
The evaluation set size N must be determined by **A priori power analysis** (see FR-007), not a fixed arbitrary number like "500".

### FR-004: Hint Purity
The extraction pipeline must filter out any hints containing coordinate-based visual grounding (e.g., `[x,y]` or pixel references).

### FR-005: Statistical Significance Testing
The evaluation pipeline MUST perform **McNemar's test** for paired proportions when comparing binary success/fail outcomes between the Distilled Model and the Baseline.
*Justification*: Binary success/fail outcomes require a test for paired proportions, not continuous means (paired t-test).

### FR-006: Sensitivity Analysis
The system must perform sensitivity analysis across "inconsistency tolerance" thresholds to verify robustness.

### FR-007: Power Analysis
The system MUST conduct **A priori power analysis** to determine the required sample size (N) before execution, ensuring statistical power ≥ 0.8.
*Justification*: Post-hoc power analysis is tautological; a priori analysis validates sample size sufficiency before execution.

## Success Criteria

### SC-001: Dataset Quality
The extracted `ExtractionDataset` must contain ≥ 5,000 valid triples with no nulls in key fields and zero coordinate-based hints.

### SC-002: Training Convergence
The T5-small training loop must achieve a final loss ≤ 0.5 on CPU within 6 hours.

### SC-003: Evaluation Pairing
The Distilled Model and Baseline must be evaluated on the exact same set of task IDs to enable valid paired statistical testing.

### SC-004: Statistical Significance
The comparison between Distilled and Baseline must yield a p-value < 0.05 from **McNemar's test** with statistical power ≥ 0.8.

### SC-005: Robustness
Sensitivity analysis must show stable results across varied significance thresholds.

### SC-006: Power Measurement
The final report must reference **McNemar's test** as the primary method for statistical power measurement and significance validation.

## Data Model

### ExtractionDataset
- `triples`: List of `(UI_state, Hint, Action)`
- `metadata`: Source log paths, filter parameters

### DistilledModel
- `weights`: Model parameters (T5-small)
- `config`: Architecture and hyperparameters
- `training_log`: Loss history, duration

### EvaluationResult
- `task_id`: Unique identifier
- `distilled_success`: Boolean
- `baseline_success`: Boolean
- `metrics`: Success Rate, Step Efficiency

## Appendix: Statistical Methodology

### Why McNemar's Test?
Since we are comparing two models (Distilled vs. Baseline) on the **same** set of tasks (paired design), and the outcome is binary (Success/Fail), the appropriate statistical test is **McNemar's test**. This test evaluates whether the marginal frequencies of the 2x2 contingency table are equal, effectively testing if the discordant pairs (where one model succeeds and the other fails) are balanced. A paired t-test is inappropriate here because it assumes continuous, normally distributed data, whereas our outcomes are binary proportions.