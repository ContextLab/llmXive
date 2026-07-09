# Research Plan: The Effect of Anticipated Regret on Choice Deferral

## 1. Introduction

This research investigates the relationship between **anticipated regret** and **choice deferral**.
While choice deferral is often attributed to decision complexity or loss aversion, we hypothesize that
the specific psychological construct of *anticipated regret*—the fear of making a suboptimal choice
that one will later regret—is a primary driver.

## 2. Research Questions

- **RQ1**: Does a higher magnitude of anticipated regret predict a higher probability of choice deferral?
- **RQ2**: Is the effect of anticipated regret on deferral distinct from general loss aversion?
- **RQ3**: How robust is this effect across different proxy definitions (Opportunity Cost vs. Risk Variance)?

## 3. Data Sources

### 3.1 Primary Dataset
- **Source**: HuggingFace `zhehuderek/textual_decisionmaking_data`
- **Rationale**: Provides structured decision scenarios with attributes necessary to calculate regret proxies.
- **Trace**: Replaces deprecated OpenML Task ID and invalid Kaggle URL (see T008.2).

### 3.2 Secondary Dataset (Robustness)
- **Source**: HuggingFace `PhillyMac/Decision_Making_Content_1`
- **Rationale**: Used for out-of-sample validation of the regret-deferral relationship.

## 4. Spec Amendments & Methodology Resolutions

### 4.1 Deprecation of Original Sources (FR-001)
The originally cited OpenML task and Kaggle dataset were verified as inaccessible or lacking required variables (T008.1).
We formally amend FR-001 to utilize the HuggingFace datasets listed above.

### 4.2 Operational Definition of Regret (FR-002)
The original spec proposed "Standard Deviation of Expected Utility (EU)" as the regret proxy.
We amend this to **Min-Max Regret** (Opportunity Cost) as the primary operational definition.
- **Reasoning**: SD of EU is circular and does not capture the "pain of comparison" inherent in regret.
- **Formula**: `Regret = max(Utility(All Options)) - Utility(Chosen Option)`.
- **Proxy Implementation**: Calculated via `calculate_min_max_regret` in `code/features.py`.
- **Note**: The SD of EU calculation is retained in `code/features.py` as `calculate_sd_normalized_eu` solely for comparative sensitivity analysis (T010.5).

### 4.3 Covariate Mapping (FR-003)
The "price variance" metric specified in FR-003 is reclassified.
- It is **NOT** used in the `regret_proxy` calculation.
- It is used as the `perceived_risk` **covariate** in the mixed-effects model to control for risk aversion distinct from regret.
- If `perceived_risk` scores are missing, `price_variance` will be computed and substituted (T018).

### 4.4 Sensitivity Analysis Scope (FR-005)
The sensitivity analysis now covers **six** variations to ensure robustness:
1. Min-Max Regret (Opportunity Cost) - Primary
2. Utility Variance (SD of Normalized EU) - Spec Legacy
3. Price Variance
4. Attribute Entropy
5. Attribute Range
6. Price Variance (Duplicate for cross-check)

### 4.5 Self-Report Validation (SC-006)
Validation against self-reported regret is conditional.
- If self-report data is present: Correlation with `regret_proxy` must be > 0.3.
- If missing: The check is marked "N/A" and does not block the pipeline (T008.6).

---

## 5. Distinguishing Regret from Loss Aversion

### 5.1 Theoretical Distinction
A critical challenge in this domain is disentangling **Anticipated Regret** from **Loss Aversion**.
- **Loss Aversion** (Kahneman & Tversky): The pain of losing is psychologically about twice as powerful as the pleasure of gaining. It is a general sensitivity to negative outcomes.
- **Anticipated Regret**: The specific emotional pain expected from realizing one made a *wrong choice* compared to a foregone alternative. It requires counterfactual thinking ("If I had chosen X, I would be better off").

System 1 often conflates these; a traveler hesitating to book a flight may fear the loss of money (Loss Aversion) or the pain of realizing they booked the wrong flight when a cheaper one appears later (Regret).

### 5.2 Operational Definitions in this Study

To isolate these constructs, we define them operationally as follows:

| Construct | Operational Definition | Calculation Source |
|:--- |:--- |:--- |
| **Anticipated Regret** | **Opportunity Cost**: The difference between the utility of the best available option and the utility of the chosen (or deferred) option. | `code/features.py`: `calculate_min_max_regret` |
| **Loss Aversion** | **Potential Loss Magnitude**: The absolute magnitude of the worst possible outcome relative to the reference point, independent of the chosen option's relative performance. | `code/features.py`: `calculate_potential_loss_magnitude` |

### 5.3 Statistical Control Strategy

To ensure the observed effect on choice deferral is driven by regret and not merely general loss aversion, we implement a **statistical control strategy**:

1. **Independent Metric Calculation**:
 We calculate `potential_loss_magnitude` separately from the `regret_proxy`. This metric captures the raw "sting" of the worst-case scenario (e.g., the price of the most expensive flight) without considering the relative quality of the chosen option.

2. **Covariate Inclusion**:
 In the Mixed-Effects Logistic Regression model (implemented in `code/modeling.py`), we include **both** variables:
 - **Independent Variable**: `regret_proxy` (Min-Max Regret)
 - **Control Covariate**: `potential_loss_magnitude` (Loss Aversion proxy)

3. **Interpretation**:
 - If the coefficient for `regret_proxy` remains significant after controlling for `potential_loss_magnitude`, we conclude that the *relative* comparison (regret) drives deferral, not just the *absolute* magnitude of potential loss.
 - If `potential_loss_magnitude` absorbs the effect, the behavior is better explained by general loss aversion.

### 5.4 Implementation Verification

- **T044**: Implemented `calculate_potential_loss_magnitude` in `code/features.py`.
- **T045**: Added `potential_loss_magnitude` as a mandatory covariate in the model formula.
- **T046**: Added diagnostic logic `compute_regret_loss_correlation` to verify that the two metrics are not perfectly collinear (r < 0.9), ensuring the statistical control is valid.

This strategy directly addresses the concern raised in the Kahneman review regarding the conflation of System 1 heuristics, providing a rigorous method to isolate the specific psychological mechanism of anticipated regret.

---

## 6. Analysis Plan

1. **Data Ingestion**: Load and validate HuggingFace datasets.
2. **Feature Engineering**: Compute `regret_proxy` (Min-Max) and `potential_loss_magnitude`.
3. **Modeling**: Fit Mixed-Effects Logistic Regression with random intercepts for `participant_id`.
 - Model 1: Deferral ~ Regret + Option Count
 - Model 2: Deferral ~ Regret + Option Count + Loss Magnitude (Control)
4. **Robustness**: Repeat on secondary dataset and with alternative proxy definitions.
5. **Reporting**: Generate `data/results/coefficients.csv` and `data/results/robustness_report.md`.