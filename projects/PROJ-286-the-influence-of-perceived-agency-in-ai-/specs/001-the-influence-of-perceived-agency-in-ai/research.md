# Research Protocol: The Influence of Perceived Agency in AI Interactions on Trust

## Literature Review Summary

This study investigates the relationship between perceived agency and trust in AI systems.
Key theoretical foundations include:

- **Lee & See (2004)**: Establishes the multidimensional nature of trust in automation,
 highlighting reliability, predictability, and purpose as core components.
- **Langer (1975)**: Introduces the concept of mindfulness and the illusion of control,
 suggesting that perceived agency can influence trust independent of actual performance.

## Methodology & Power Analysis

The study employs a between-subjects design with three conditions: High Agency, Low Agency, and Control.
The primary outcome measure is the trust score derived from the Lee & See (2004) scale.

### Statistical Power Analysis

A pre-study power analysis was conducted using `statsmodels` to determine the required sample size.
The analysis assumed a One-Way ANOVA with the following parameters:

- **Effect Size (f)**: 0.25 (Medium effect)
- **Alpha Level**: 0.05
- **Target Power**: 0.80
- **Test Type**: F-test (ANOVA)

### Power Calculation Results

The following table summarizes the power analysis results and the required sample size for the study.

| Effect Size | Alpha | Target Power | Required N | Calculated N |
|:--- |:--- |:--- |:--- |:--- |
| 0.25 | 0.05 | 0.80 | 159 | 159 |

*Note: The 'Calculated N' represents the total number of participants required across all three groups to achieve the target power.*

## Data Collection Plan

Data will be collected via a web-based interface (Streamlit) presenting the experimental task.
Participants will be randomized into one of the three conditions.
Adherence rates, trust scores, and attention check results will be recorded.

## Ethical Considerations

The study protocol adheres to standard ethical guidelines for human subjects research.
Informed consent will be obtained prior to participation.
Data will be anonymized and stored securely.

## References

1. Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50-80.
2. Langer, E. J. (1975). The illusion of control. *Journal of Personality and Social Psychology*, 32(2), 311-328.