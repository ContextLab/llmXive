# Spec: Assessing Energy Consumption of LLM Inference for Code Completion

## Overview
This project assesses the energy consumption (kWh) and runtime of LLM inference for code completion tasks using CPU-only execution. The study compares three models: GPT-2-small, CodeBERT, and StarCoder-1B.

## Functional Requirements

### FR-001: Model Substitution Authorization
Due to RAM constraints on standard CPU-only execution environments (e.g., GitHub Actions free-tier), the original specification target of "StarCoder-base" is hereby replaced with **StarCoder-1B**.
- **Justification**: StarCoder-base exceeds available memory for CPU inference without quantization. StarCoder-1B provides a comparable code-generation capability while fitting within the 16GB RAM constraint.
- **Impact**: All subsequent tasks, data collection, and analysis must reference "StarCoder-1B" as the largest model.
- **Precedence**: This amendment supersedes any prior references to "StarCoder-base" in user stories or design documents.

### FR-002: Energy Measurement
The system must measure energy consumption in kWh using `codecarbon` during inference.

### FR-003: Token Counting
The system must count the number of tokens generated for each problem.

### FR-004: Evaluation
Generated completions must be evaluated against the HumanEval test suite to determine pass/fail status.

### FR-005: Statistical Analysis
The system must perform Repeated-Measures ANOVA, Tukey HSD, and linear regression on the collected data.

### FR-006: Visualization
The system must generate bar plots (Energy/Token vs Model) and scatter plots (Energy/Correct vs Accuracy).

### FR-007: Environment Verification
The system must verify the environment by running a trivial dummy test case before full execution.

### FR-008: Observational Regression
Linear regression must be framed as observational (Parameter Count vs Energy/Token), not causal.

### FR-009: Edge Case Handling
The system must record `null` energy if calibration fails and `null` tokens if 0 tokens are generated.

### FR-010: Calibration Validation
The calibration script must validate `codecarbon` power draw detection and exit with code 1 if deviation > 10%.

### FR-011: Data Aggregation
The system must filter out rows with `null` energy or 0 tokens during aggregation.

### FR-012: Sensitivity Analysis
The system must perform a sensitivity analysis by perturbing energy values by ±10% and comparing p-values.

## User Stories

### US-1: Quantify Energy-to-Token Metrics
**As a** researcher,
**I want to** execute inference for GPT-2-small, CodeBERT, and StarCoder-1B on HumanEval using CPU,
**So that** I can log energy (kWh), runtime, and tokens.

**Acceptance Criteria**:
- Models are loaded sequentially to manage RAM.
- `codecarbon` logs are generated for all three models.
- Results are saved to `data/processed/energy_results_raw.csv`.
- **Constraint**: StarCoder-1B is used instead of StarCoder-base per FR-001.

### US-2: Statistical Analysis
**As a** researcher,
**I want to** perform statistical analysis on the collected data,
**So that** I can determine if differences in energy consumption are significant.

**Acceptance Criteria**:
- Repeated-Measures ANOVA is performed.
- Tukey HSD post-hoc tests are run.
- Linear regression is calculated.
- Sensitivity analysis is included.

### US-3: Visualization
**As a** researcher,
**I want to** generate visualizations of the results,
**So that** I can present the sustainability trade-offs clearly.

**Acceptance Criteria**:
- Bar plot of Energy per Token vs Model.
- Scatter plot of Energy per Correct Solution vs Accuracy.
- All plots include titles, axis labels, and legends.

## Data Model
- **Raw Data**: `data/raw/human_eval_data.jsonl`
- **Processed Data**: `data/processed/energy_results_aggregated.csv`
- **Statistics**: `data/processed/stats_report.csv`
- **Figures**: `data/processed/energy_bar.png`, `data/processed/tradeoff_scatter.png`

## Constraints
- CPU-only execution only.
- No GPU quantization or 8-bit loading.
- StarCoder-1B is the largest model (FR-001).
- Maximum runtime of 6 hours on free-tier runners.
