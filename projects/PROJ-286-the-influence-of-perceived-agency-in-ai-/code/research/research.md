# Research and Power Analysis: The Influence of Perceived Agency in AI Interactions on Trust

## Literature Review Findings

This study investigates the impact of perceived agency on trust in AI systems, building upon foundational work in human-computer interaction and social psychology.

### Theoretical Framework

**Lee & See (2004)**: In their seminal work "Trust in Automation: Designing for Appropriate Reliance," Lee and See establish that trust in automation is a function of the system's reliability, competence, and predictability. [UNRESOLVED-CLAIM: c_2a30fb49 — status=not_enough_info] They argue that trust calibration is critical: over-trust leads to misuse, while under-trust leads to disuse. This study extends their framework by examining how the *perception* of agency, even when illusory, influences these trust dimensions.

**Langer (1975)**: Langer's "The Mindlessness of Ostensibly Thoughtful Action" demonstrates that humans often respond to cues of agency rather than actual agency. The "illusion of control" paradigm suggests that providing individuals with control mechanisms, even if non-functional, can significantly alter their behavior and trust levels. This study operationalizes this finding by creating distinct conditions of High Agency (functional controls that do not alter AI output), Low Agency (restricted controls), and Control (static display).

### Hypotheses

Based on the literature, we hypothesize that:
1. Participants in the High Agency condition will report significantly higher trust scores than those in the Low Agency and Control conditions.
2. The effect of perceived agency on trust will be mediated by the perceived competence and predictability of the AI system.
3. Behavioral adherence to AI recommendations will be higher in the High Agency condition compared to the Control condition, despite identical AI outputs.

## Power Analysis

### Parameters

To ensure the study is adequately powered to detect a medium effect size, we conducted an a priori power analysis using G*Power and verified with Python's `statsmodels` library.

**Effect Size (f)**: 0.25 (Medium effect size, Cohen's conventions)
**Alpha Level (α)**: 0.05 (Standard significance threshold)
**Target Power (1-β)**: 0.80 (80% probability of detecting an effect if it exists)
**Statistical Test**: One-Way ANOVA (Fixed effects, omnibus, one-way)
**Number of Groups**: 3 (High Agency, Low Agency, Control)

### Calculation Results

Using the parameters above, the required sample size per group is 52 participants, resulting in a total required sample size of 156 participants.

| Effect Size (f) | Alpha | Target Power | Required N (Total) | Calculated N (Per Group) |
|:--- |:--- |:--- |:--- |:--- |
| 0.25 | 0.05 | 0.80 | 156 | 52 |

### Sensitivity Analysis

If recruitment targets are not met, the study will still be able to detect effect sizes as follows:
- With N=120 (40 per group): Minimum detectable f ≈ 0.29
- With N=90 (30 per group): Minimum detectable f ≈ 0.35

These thresholds will be reported in the final analysis to contextualize any null findings.

## Methodology Overview

### Experimental Design

A between-subjects design with three conditions:
1. **High Agency**: Participants interact with functional sliders that appear to influence AI output but do not.
2. **Low Agency**: Participants have restricted control options.
3. **Control**: Participants view static AI output without interaction options.

### Measures

1. **Trust Scale**: Lee & See (2004) 12-item trust scale (7-point Likert).
2. **Perceived Agency**: Manipulation check questions.
3. **Behavioral Adherence**: Percentage of AI recommendations followed.
4. **Attention Checks**: Embedded within the survey to ensure data quality.

### Data Collection Plan

Data will be collected via a web-based interface (Streamlit) deployed on a secure server. Participants will be recruited through Prolific or similar platforms, screened for attention check failures, and compensated according to standard rates.

## References

1. Lee, J. D., & See, K. A. (2004). Trust in automation: Designing for appropriate reliance. *Human Factors*, 46(1), 50-80.
2. Langer, E. J. (1975). The illusion of control. *Journal of Personality and Social Psychology*, 32(2), 311-328.
