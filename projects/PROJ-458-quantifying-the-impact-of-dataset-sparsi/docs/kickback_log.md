# Kickback Log: Spec vs Plan Deviations

This document records formal deviations between the Project Specification (`spec.md`) and the Implementation Plan (`plan.md`). These deviations were identified during the Kickback & Spec Alignment phase and dictate the implementation strategy.

## Log Entries

### FR-003: Baseline Definition
- **Spec**: Uses "[deferred]" terminology for full dataset.
- **Plan**: Defines a 'Representative Stratified Sample (RSS)' baseline with specific size configuration (`RSS_SIZE`).
- **Decision**: Implementation follows the **Plan**. The `sparsity_generation.py` module implements RSS capping.
- **Status**: Logged (T010).

### Assumptions: Authentication
- **Spec**: Assumes 'no authentication barriers'.
- **Plan**: Requires `MP_API_KEY` configuration via `.env`.
- **Decision**: Implementation follows the **Plan**. `config.py` and `data_ingestion.py` enforce API key presence.
- **Status**: Logged (T011).

### FR-006: Statistical Method
- **Spec**: Mandates 'Repeated Measures ANOVA'.
- **Plan**: Mandates 'Linear Mixed-Effects Modeling (LMM)' due to nested data structure (sparsity levels within seeds).
- **Decision**: Implementation follows the **Plan**. `statistical_analysis.py` and `model_training.py` use `statsmodels.MixedLM`.
- **Status**: Logged (T012).

### SC-001: Metrics
- **Spec**: Lists basic metrics.
- **Plan**: Includes 'Predictive Variance' and 'Calibration Slope' metrics.
- **Decision**: Implementation follows the **Plan**. `model_training.py` calculates these extended metrics.
- **Status**: Logged (T013).

### FR-007: Sensitivity Threshold
- **Spec**: Ambiguous requirement for sensitivity analysis.
- **Plan**: Specifies a 'slope variance < 10%' threshold.
- **Decision**: Implementation follows the **Plan**. `statistical_analysis.py` (T047) implements this explicit check.
- **Status**: Logged (T014).