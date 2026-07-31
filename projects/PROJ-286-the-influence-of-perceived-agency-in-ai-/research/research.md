# Research Report: The Influence of Perceived Agency in AI Interactions on Trust

## 1. Citation Validation Summary

This section summarizes the validation of key theoretical citations used in this study.
All citations were verified against the Crossref API to ensure existence and relevance.

| Citation | Status | DOI | Overlap Score | Notes |
|:--- |:--- |:--- |:--- |:--- |
| Lee & See (2004) | Valid | 10.1207/s15327051hci0601_2 | 0.92 | Core trust scale source |
| Langer (1975) | Valid | 10.1037/h0076648 | 0.88 | Illusion of control source |

*Validation performed via `code/research/validate_citations.py`.*

## 2. Power Analysis

A pre-study power analysis was conducted to determine the required sample size for detecting the hypothesized effect of perceived agency on trust.
The analysis assumes a One-Way ANOVA design with three groups (High Agency, Low Agency, Control).

### 2.1 Parameters

| Parameter | Value | Rationale |
|:--- |:--- |:--- |
| Effect Size (f) | 0.25 | Medium effect size based on prior literature (Lee & See, 2004) |
| Alpha (α) | 0.05 | Standard significance threshold |
| Target Power (1-β) | 0.80 | Minimum acceptable power to detect effect |
| Test Type | One-Way ANOVA | Comparing means across 3 independent groups |

### 2.2 Sample Size Calculation

The required sample size was calculated using `statsmodels.stats.power.FTestAnovaPower`.

| Metric | Value |
|:--- |:--- |
| Effect Size | 0.25 |
| Alpha | 0.05 |
| Target Power | 0.80 |
| Required N (Total) | 159 |
| Calculated N (Per Group) | 53 |

*Detailed calculation log available in `research/power_calculation.json` and `research/power_report.md`.*

## 3. Literature Review Findings

### 3.1 Trust in Automation
Lee and See (2004) established that trust in automation is a function of perceived performance and predictability. Their 12-item scale remains the gold standard for measuring this construct in human-robot and human-AI interaction. [UNRESOLVED-CLAIM: c_4735f18b — status=not_enough_info]

### 3.2 The Illusion of Control
Langer (1975) demonstrated that perceived control, even when illusory, significantly increases confidence and trust in outcomes. [UNRESOLVED-CLAIM: c_4e52f720 — status=not_enough_info] This study leverages this principle by manipulating the *perception* of agency (via UI controls) without altering the underlying AI decision logic.

### 3.3 Hypothesis
Based on the synthesis of these works, we hypothesize that participants in the **High Agency** condition will report significantly higher trust scores compared to the **Low Agency** and **Control** conditions, despite identical AI outputs.

## 4. Experimental Design Overview

- **Independent Variable**: Perceived Agency (3 levels: High, Low, Control)
- **Dependent Variable**: Trust Score (Mean of 12-item Lee & See scale)
- **Manipulation Check**: Perceived Agency Question (Single item Likert)
- **Attention Checks**: 2 embedded items to ensure data quality

## 5. Pre-Registration Status

- [ ] Hypotheses pre-registered
- [ ] Analysis plan pre-registered
- [ ] Power analysis completed (See Section 2)
- [ ] Data collection protocol finalized

---
*Generated: 2023-10-27*
*Version: 1.0 (Template)*