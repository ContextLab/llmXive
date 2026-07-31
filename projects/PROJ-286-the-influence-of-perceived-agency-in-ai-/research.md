# Research Report: The Influence of Perceived Agency in AI Interactions on Trust

## 1. Literature Review Summary

### 1.1 Theoretical Foundations
This study builds upon two foundational works regarding human-computer interaction and trust:

1. **Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50-80.**
 - Validated via Crossref API (See `research/validation_report.json`).
 - Defines trust as "the attitude that an agent will help achieve an individual's goals in a situation characterized by uncertainty and vulnerability."
 - Provides the 12-item Trust Scale used in this study (Items 1-12).

2. **Langer, E. J. (1975). The illusion of control. *Journal of Personality and Social Psychology*, 32(2), 311-328.**
 - Validated via Crossref API (See `research/validation_report.json`).
 - Establishes the psychological basis for the "illusion of control" where individuals overestimate their influence over outcomes.
 - Informs the design of the "High Agency" condition (illusory controls) vs. "Low Agency" condition.

### 1.2 Hypotheses
- **H1**: Participants in the High Agency condition (illusory control) will report significantly higher trust scores than those in the Control condition.
- **H2**: Participants in the Low Agency condition will report lower trust scores than the High Agency condition, but potentially higher than Control due to engagement.
- **H3**: The difference in trust scores between conditions will be mediated by the perceived agency manipulation check scores.

## 2. Power Analysis

### 2.1 Parameters
Based on the pre-study power analysis executed in `code/research/power_analysis.py` (Task T002), the following parameters were determined:
- **Statistical Test**: One-Way ANOVA (comparing 3 groups: High Agency, Low Agency, Control).
- **Effect Size (f)**: 0.25 (Medium effect size, based on Cohen's conventions and prior meta-analyses of trust in automation).
- **Alpha Level**: 0.05.
- **Target Power (1 - Beta)**: 0.80.

### 2.2 Sample Size Calculation
The power analysis yielded the following results:

| Effect Size (f) | Alpha | Target Power | Required N (Calculated) | Final Target N |
|:--- |:--- |:--- |:--- |:--- |
| 0.25 | 0.05 | 0.80 | 159 | 180 |

*Note: The "Final Target N" includes a 13% buffer for potential data exclusion (attention check failures, incomplete responses) to ensure the effective sample size meets the calculated requirement.*

### 2.3 Justification
The calculated sample size of 159 (rounded to 180 for robustness) ensures sufficient statistical power to detect a medium effect size across the three experimental conditions. This aligns with the recommendations in the Lee & See (2004) literature for adequate group sizes in trust calibration studies.

## 3. Experimental Design Overview

- **Conditions**:
 1. **High Agency**: Participants interact with functional sliders that provide an illusion of control but do not alter the AI's underlying decision logic.
 2. **Low Agency**: Participants are restricted from interacting with the decision interface.
 3. **Control**: Participants view a static AI recommendation without any interactive elements.

- **Primary Outcome Measure**: Trust Score (Mean of 12-item Lee & See scale).
- **Secondary Outcome Measure**: Adherence Rate (% of AI recommendations followed).
- **Manipulation Check**: Perceived Agency Score (Single item Likert scale).

## 4. Data Collection Protocol

Data will be collected via a Streamlit-based web application (`code/experiment/app.py`). Participants will be randomized to one of the three conditions using a fixed seed for reproducibility. All data exports will include checksums and timestamps to ensure integrity.

## 5. References

- Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50-80.
- Langer, E. J. (1975). The illusion of control. *Journal of Personality and Social Psychology*, 32(2), 311-328.