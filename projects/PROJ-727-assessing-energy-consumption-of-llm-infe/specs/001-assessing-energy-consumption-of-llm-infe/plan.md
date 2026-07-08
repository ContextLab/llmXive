# Plan: Assessing Energy Consumption of LLM Inference for Code Completion

## Implementation Strategy
The project will be implemented in phases, starting with setup and foundational tasks, followed by user stories in priority order.

## Phase 1: Setup
- Create project structure
- Initialize Python environment
- Configure linting and formatting

## Phase 2: Foundational
- **CRITICAL**: This phase must be completed before any user story implementation.
- **FR-001 Amendment**: Update spec and plan to replace 'StarCoder-base' with 'StarCoder-1B' due to RAM constraints.
- Create configuration files
- Download HumanEval dataset
- Implement calibration script
- Create versioning logic
- Implement environment verification

## Phase 3: User Story 1 (MVP)
- Implement inference logic
- Evaluate completions
- Handle edge cases
- Aggregate results
- Add logging

## Phase 4: User Story 2
- Implement ANOVA
- Implement Tukey HSD
- Implement regression
- Perform sensitivity analysis
- Generate stats report

## Phase 5: User Story 3
- Implement visualization logic
- Generate bar plot
- Generate scatter plot
- Calculate scatter slope

## Phase 6: Polish
- Update documentation
- Clean up code
- Verify pipeline execution
- Final validation

## Feasibility Notes
- **RAM Constraint**: Standard CPU-only environments (e.g., GitHub Actions) have limited RAM (typically 7GB-16GB).
- **Model Substitution**: The original target model "StarCoder-base" is too large for CPU inference without quantization.
- **Authorized Substitution**: Per FR-001, "StarCoder-1B" is used instead. This model is small enough to fit in memory while still providing meaningful code completion results.
- **No Quantization**: The project explicitly forbids GPU quantization or 8-bit loading to maintain consistency in measurement methodology.
- **Execution Time**: The full pipeline must complete within 6 hours on a free-tier runner.

## Risk Mitigation
- **OOM Errors**: Models are loaded sequentially and unloaded explicitly to free RAM.
- **Calibration Failure**: The calibration script will exit with code 1 if `codecarbon` fails to detect power draw accurately.
- **Data Integrity**: All analysis uses real HumanEval data and real `codecarbon` logs. No synthetic data is used.

## Dependencies
- Python 3.10+
- transformers
- torch-cpu
- codecarbon
- pandas
- numpy
- scipy
- statsmodels
- matplotlib
- seaborn
- human-eval
- huggingface_hub