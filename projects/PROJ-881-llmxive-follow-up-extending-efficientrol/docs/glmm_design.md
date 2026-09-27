# Mixed-Effects Logistic Regression (GLMM) Design Document

## Overview

This document details the design of the Mixed-Effects Logistic Regression (GLMM) model structure
used to predict token validity from entropy values in the llmXive follow-up project. The model
accounts for the hierarchical structure of the data where tokens are nested within sequences,
and sequences are nested within task types.

## Statistical Model

### Base Formula

The primary model specification follows the lme4-style formula syntax:

```
validity ~ entropy + (1 | sequence_id) + (1 | task_type)
```

Where:
- `validity`: Binary outcome variable (1 = valid token, 0 = invalid token)
- `entropy`: Continuous predictor (Shannon entropy at the token position)
- `sequence_id`: Random intercept for each unique generation sequence
- `task_type`: Random intercept for task type (GSM8K vs MiniGrid)

### Extended Formula with Layer Effects

To capture signal decay across layers, we support two strategies:

#### Strategy 1: Continuous Layer Covariate

```
validity ~ entropy + layer_index + entropy:layer_index + (1 | sequence_id)
```

This models:
- Main effect of entropy
- Main effect of layer position
- Interaction between entropy and layer (captures decay)

#### Strategy 2: Layer Pooling (Early/Mid/Late)

When layer sparsity is high or the continuous approach fails to converge:

```
validity ~ entropy + layer_pool + entropy:layer_pool + (1 | sequence_id)
```

Where `layer_pool` is a categorical variable with levels:
- `early`: Layers 0-33% of total layers
- `mid`: Layers 34-66% of total layers
- `late`: Layers 67-100% of total layers

## Stratification Strategy

### Primary Stratification: Task Type

The model supports stratified analysis by task type:

1. **Combined Model**: Includes `task_type` as a random intercept
2. **Stratified Models**: Fit separate models for GSM8K and MiniGrid

When the dataset contains only one task type, the formula automatically drops the `task_type`
component to avoid rank deficiency errors in pymer4.

### Secondary Stratification: Sequence Length

For decay analysis (SC-004), we split data by median sequence length:

- **Short sequences**: Below median length
- **Long sequences**: At or above median length

Each subset receives independent model fitting to compare predictive power decay.

## Random Effects Structure

### Random Intercepts for Sequence ID

Each `sequence_id` receives a random intercept to account for:
- Shared context within a generation
- Correlation between tokens in the same sequence
- Sequence-specific baseline validity rates

Formula component: `(1 | sequence_id)`

### Random Intercepts for Task Type

When both task types are present:
- Accounts for baseline differences between GSM8K and MiniGrid
- Allows task-specific intercept shifts

Formula component: `(1 | task_type)`

## Model Fitting Procedure

### Implementation Library

- **Library**: `pymer4` (Python wrapper for R's lme4)
- **Backend**: Uses R's `lmer`/`glmer` functions via rpy2

### Fitting Steps

1. **Data Preparation**
 - Load entropy profiles from `data/entropy_profiles_merged.jsonl`
 - Filter for non-null entropy values
 - Encode validity as binary (0/1)
 - Create sequence_id and task_type identifiers

2. **Model Selection**
 - Check layer sparsity
 - If sparsity > threshold (0.3), use pooling strategy
 - Otherwise, use continuous layer covariate

3. **Convergence Handling**
 - Attempt fit with default settings
 - If convergence fails, try:
 - Different optimizer (bobyqa)
 - Reduced complexity (remove interaction term)
 - Switch to pooling strategy

4. **Perfect Separation Detection**
 - Check for zero valid or zero invalid tokens in subsets
 - If detected, skip fit and log warning
 - Return result object with `significant=False`

## Output Specifications

### Model Fitting Results (`results/model_fitting.json`)

```json
{
 "fixed_effects": {
 "entropy": {
 "coefficient": -2.34,
 "std_error": 0.45,
 "z_value": -5.20,
 "p_value": 0.0001
 },
 "layer_index": {
 "coefficient": -0.12,
 "std_error": 0.05,
 "z_value": -2.40,
 "p_value": 0.0164
 },
 "entropy:layer_index": {
 "coefficient": 0.08,
 "std_error": 0.03,
 "z_value": 2.67,
 "p_value": 0.0076
 }
 },
 "random_effects": {
 "sequence_id": {
 "variance": 0.45,
 "std_dev": 0.67
 },
 "task_type": {
 "variance": 0.12,
 "std_dev": 0.35
 }
 },
 "model_fit": {
 "AIC": 1234.5,
 "BIC": 1267.8,
 "log_likelihood": -612.3,
 "converged": true
 },
 "performance": {
 "AUC_ROC": 0.82,
 "accuracy": 0.76,
 "precision": 0.79,
 "recall": 0.73
 },
 "strategy_used": "continuous_layer",
 "n_observations": 15000,
 "n_sequences": 500,
 "n_task_types": 2
}
```

## Assumptions and Diagnostics

### Model Assumptions

1. **Independence**: Tokens are independent given random effects
2. **Linearity**: Log-odds of validity is linear in entropy and layer
3. **Normality**: Random effects follow normal distribution
4. **Homoscedasticity**: Residual variance is constant

### Diagnostic Checks

- **Residual plots**: Check for systematic patterns
- **QQ plots**: Assess normality of random effects
- **VIF scores**: Check for multicollinearity
- **Convergence warnings**: Monitor optimization success

## Integration Points

### Input Data

- Source: `data/entropy_profiles_merged.jsonl` (T025 output)
- Required fields: `prompt_id`, `token_index`, `validity`, `entropy`, `layer_id`, `sequence_id`, `task_type`

### Downstream Consumers

1. **Threshold Optimization** (T032): Uses model coefficients to find optimal entropy threshold
2. **Sensitivity Analysis** (T033a): Extracts p-values for multiple-comparison correction
3. **Decay Analysis** (T035): Compares AUC-ROC across short/long sequence subsets
4. **Final Report** (T037): Aggregates all model metrics

## Error Handling

### Graceful Degradation

- **Single task type**: Drop `task_type` from formula
- **Convergence failure**: Try alternative optimizer, then pooling strategy
- **Perfect separation**: Skip fit, return non-significant result
- **Empty dataset**: Raise `RuntimeError` with descriptive message

### Logging

- Warnings logged for non-significant results (p >= 0.05)
- Information logged for strategy switches
- Errors logged with full traceback for debugging

## References

- Barr, D. J., et al. (2013). Random effects structure for confirmatory hypothesis testing. *Journal of Memory and Language*
- Bates, D., et al. (2015). Fitting linear mixed-effects models using lme4. *Journal of Statistical Software*
- pymer4 documentation: 