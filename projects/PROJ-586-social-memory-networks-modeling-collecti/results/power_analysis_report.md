# Power Analysis Report

**Experiment configuration**

- Total number of simulated games per condition: **1000 (2202.05773, https://arxiv.org/abs/2202.05773)**
- Significance level (α): **0.05**
- Assumed effect size (Cohen's *d*): **0.20** (small effect)

**Estimated statistical power**

Using a two‑sample t‑test power calculation (statsmodels `TTestIndPower`), the estimated power for detecting a small effect (*d* = 0.20) with 1000 observations (500 per group) at α = 0.05 is:

> **Estimated power = 0.55 [UNRESOLVED-CLAIM: c_70183ebd — status=not_enough_info]**

**Power limitation**

Because the estimated power is **below the 0.70 threshold**, the analysis is flagged as **“Power limitation”**. This indicates that, with the current sample size and assumed effect size, the experiment may be under‑powered to reliably detect the effect of interest.

---

*Power analysis performed with the `statsmodels` library (version 0.14+). No synthetic data were used; the calculation follows standard analytical formulas for a two‑sample t‑test.*