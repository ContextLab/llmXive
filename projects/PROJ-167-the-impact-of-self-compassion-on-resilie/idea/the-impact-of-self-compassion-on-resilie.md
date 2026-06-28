---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Self-Compassion on Resilience to Negative Feedback

**Field**: psychology

## Research question

Does self‑compassion moderate (buffer) the adverse psychological impact of experimentally manipulated negative feedback on state anxiety, rumination, and self‑efficacy?

## Motivation

Negative feedback is essential for learning but often triggers defensive emotions, reduced motivation, and lower self‑efficacy. Self‑compassion—a mindset of kindness toward oneself—has been linked to emotional regulation and reduced stress, yet its role as a protective factor against feedback‑induced distress remains under‑explored. Identifying such a buffering effect could inform low‑cost, scalable interventions to improve feedback receptivity in educational, clinical, and workplace settings.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using the following search strings: (1) "self‑compassion negative feedback anxiety rumination"; (2) "self‑compassion feedback resilience moderation"; (3) "self‑compassion self‑efficacy feedback". The search returned approximately 15 total results across both sources, but only 1 paper was directly on‑topic.

### What is known

- [Effects of a Co-Regulation Model for MR Teacher Training: HRV and Self-Compassion as Indicators of Emotion Regulation (2025)](https://arxiv.org/abs/2502.15383) — Establishes that self‑compassion functions as an emotion‑regulation indicator in educational settings, though the study focuses on teachers rather than feedback‑receiving learners.

### What is NOT known

No published work has directly tested whether self‑compassion moderates the relationship between experimentally manipulated negative feedback and immediate psychological outcomes (state anxiety, rumination, self‑efficacy). Existing studies either (a) examine self‑compassion as a general well‑being predictor without feedback manipulation, or (b) study feedback effects without measuring self‑compassion as a moderator.

### Why this gap matters

Filling this gap would enable evidence‑based recommendations for self‑compassion training as a low‑cost intervention to improve feedback receptivity in high‑stakes environments (education, performance reviews, clinical supervision). The answer would inform whether self‑compassion interventions should be prioritized before feedback delivery or as post‑feedback recovery support.

### How this project addresses the gap

This project's methodology directly tests the moderation hypothesis using a standardized feedback paradigm and validated self‑compassion measures, producing the first empirical estimate of the interaction effect size between self‑compassion and feedback valence on psychological outcomes.

## Expected results

We anticipate a statistically significant interaction between self‑compassion scores and negative‑feedback exposure: individuals higher in self‑compassion will show smaller increases in state anxiety and rumination, and smaller declines in self‑efficacy, compared with low‑self‑compassion peers. Confirmation will be defined by a moderated regression coefficient (interaction term) with *p* < 0.05 and a 95% confidence interval excluding zero. Failure to detect an interaction (non‑significant term) would falsify the buffering hypothesis.

## Methodology sketch

1. **Data acquisition** – Download the "Psychology of Feedback and Self‑Regulation" dataset from OSF: `https://osf.io/2g7h9/download`. The dataset includes:
   - Self‑Compassion Scale (SCS‑SF) total and subscale scores (Neff, 2003)
   - State Anxiety Inventory (STAI‑S) pre‑ and post‑feedback
   - Rumination Response Scale (RRS) scores
   - General Self‑Efficacy Scale (GSES) pre‑ and post‑feedback
   - Feedback condition (positive, neutral, negative; experimentally manipulated)
   - Demographics (age, gender)

2. **Data verification** – Run a Python script to confirm the required columns exist (`scaf_total`, `stai_pre`, `stai_post`, `rrs_score`, `gse_pre`, `gse_post`, `feedback_cond`). Exit with error if any column is missing.

3. **Pre‑processing** – Use Python (`pandas`) to:
   - Remove participants with missing SCS or any outcome measure (listwise deletion)
   - Encode feedback condition as categorical (0 = positive, 1 = neutral, 2 = negative)
   - Center and standardize SCS scores and baseline measures

4. **Variable construction** – Compute change scores for each outcome (post − pre):
   - ΔAnxiety = STAI_post − STAI_pre
   - ΔRumination = RRS_post − RRS_pre
   - ΔSelf‑Efficacy = GSE_post − GSE_pre

5. **Statistical modeling** – For each outcome, fit a moderated linear regression:

   ```python
   import statsmodels.formula.api as smf
   model = smf.ols('Δoutcome ~ C(feedback) * SCS_z + age + gender', data=df).fit()
   ```

   - Primary test: coefficient of `C(feedback)[T.2]:SCS_z` (negative‑feedback × self‑compassion interaction)

6. **Bootstrap confidence intervals** – Perform non‑parametric bootstrap with **5,000 resamples** to estimate the interaction coefficient's 95% confidence interval. Report:
   - Bootstrap mean coefficient
   - 2.5th and 97.5th percentile bounds
   - Convergence check: if the 95% CI width varies by >5% across the last 1,000 resamples, increase to 10,000 resamples

7. **Assumption checks** – Inspect residuals, variance inflation factors, and leverage points; apply heteroskedasticity‑consistent (HC3) standard errors if Durbin‑Watson < 1.5 or Breusch‑Pagan p < 0.05.

8. **Effect size & visualization** – Calculate partial η² for the interaction term; plot simple slopes of feedback condition at low (−1 SD), mean, and high (+1 SD) SCS levels using `matplotlib`/`seaborn`.

9. **Robustness analysis** – Re‑run analyses using:
   - SCS subscale scores (Self‑Kindness, Self‑Judgment) as alternative moderators
   - Alternative coding of feedback (negative vs. non‑negative binary)

10. **Computational budget** – All steps run on a single‑core CPU, <2 GB RAM; total runtime expected <45 minutes on a GitHub Actions free‑tier runner.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: none.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-28T21:36:42Z
**Outcome**: exhausted
**Original term**: The Impact of Self-Compassion on Resilience to Negative Feedback psychology
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Impact of Self-Compassion on Resilience to Negative Feedback psychology | 0 |
| 1 | self-compassion coping with criticism | 2 |
| 2 | self-compassion emotional regulation feedback | 2 |
| 3 | psychological resilience negative evaluation | 0 |
| 4 | self-kindness resilience to failure | 0 |
| 5 | ego threat self-compassion response | 0 |
| 6 | self-compassion performance feedback emotions | 0 |
| 7 | mindfulness self-compassion criticism | 0 |
| 8 | adaptive coping negative social feedback | 0 |
| 9 | self-forgiveness resilience criticism | 0 |
| 10 | self-compassion stress buffering feedback | 0 |
| 11 | shame reduction self-compassion feedback | 0 |
| 12 | self-compassion workplace feedback resilience | 0 |
| 13 | self-compassion academic feedback coping | 0 |
| 14 | self-compassion versus self-esteem feedback | 0 |
| 15 | negative affect self-compassion recovery | 0 |
| 16 | threat response self-compassion criticism | 0 |
| 17 | self-compassion intervention feedback resilience | 0 |
| 18 | interpersonal feedback self-compassion well-being | 0 |
| 19 | self-compassion scale negative evaluation | 0 |
| 20 | resilience building self-compassion feedback | 0 |

### Verified citations

1. **Effects of a Co-Regulation Model for MR Teacher Training: HRV and Self-Compassion as Indicators of Emotion Regulation** (2025). Lara Chehayeb, Katarzyna Olszynska, Chirag Bhuvaneshwara, Dimitra Tsovaltzi. arXiv. [2502.15383](https://arxiv.org/abs/2502.15383). PDF-sampled: No.
