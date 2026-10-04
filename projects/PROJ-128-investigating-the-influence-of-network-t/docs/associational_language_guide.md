# Associational Language Guide

## Purpose

This document provides guidelines for maintaining "associational" framing throughout all project outputs, as required by FR-007 and Constitution Principle VI.

## Core Principle

**We do not claim causality.** All relationships between structural connectivity and dynamic functional states are described as **associations**, **correlations**, or **statistical relationships**.

## Forbidden Language

Avoid these terms when describing findings:
- "predict" (in a causal sense)
- "cause" / "causes"
- "drives" / "driving"
- "influences" (implying causation)
- "determines" / "determined by"
- "results in" / "leads to"
- "mechanism" (when implying causal pathway)
- "effect" (when implying causal effect)

## Preferred Language

Use these terms instead:
- "is associated with"
- "correlates with"
- "is linked to"
- "shows a relationship with"
- "co-occurs with"
- "is statistically related to"
- "variation in X corresponds to variation in Y"
- "X and Y are correlated"

## Examples

### ❌ Incorrect (Causal)
> "Structural global efficiency **predicts** the dwell time of recurrent activity patterns."

> "Higher modularity **drives** increased stability of functional states."

> "Tractography artifacts **cause** spurious correlations."

### ✅ Correct (Associational)
> "Structural global efficiency **is associated with** the dwell time of recurrent activity patterns."

> "Higher modularity **correlates with** increased stability of functional states."

> "Tractography artifacts **may contribute to** spurious correlations."

## Report Templates

### Abstract
```
This study investigates the association between topological properties of structural
brain networks and dynamic functional states. We find that [metric A] is
statistically associated with [metric B] (r=0.XX, p<0.05, FDR-corrected).
These findings suggest a relationship between structural connectivity and
spontaneous activity patterns, though causal mechanisms remain to be determined.
```

### Results
```
Correlation analysis revealed that structural global efficiency is associated with
mean dwell time (r=0.XX, p=0.XX). After FDR correction, [X] of [Y] tests
remained significant. Sensitivity analyses indicate that these associations are
robust to variations in [parameter].
```

### Discussion
```
Our findings demonstrate an association between structural network topology and
dynamic functional states. While these results are consistent with theoretical
models suggesting that structural connectivity constrains functional dynamics,
we cannot infer causality from this observational analysis. Future work with
interventional designs would be required to establish causal mechanisms.
```

## Automated Compliance

The project includes an automated checker:
```bash
python code/reports/audit_associational_language.py
```

This script scans all reports and flags potential causal language.

## Tractography Sensitivity Note

When discussing tractography false-positive concerns (Yeh et al., 2018):

❌ "Tractography errors **cause** the correlation to disappear."

✅ "The correlation **is no longer observed** at high confidence thresholds,
suggesting that the original finding **may be influenced by** tractography
false-positives."

## Review Checklist

Before finalizing any report, verify:
- [ ] No causal verbs (predict, cause, drive, determine)
- [ ] All relationships described as "associated with" or "correlated with"
- [ ] Causal language in discussion is qualified with "may", "suggests", "potentially"
- [ ] Tractography sensitivity section explicitly states uncertainty about artifacts
- [ ] Limitations section acknowledges observational nature of the study

## References

- FR-007: Mandatory "associational" framing requirement
- Constitution Principle VI: Independence and non-causal interpretation
- Yeh et al., 2018: Tractography false-positive rates
