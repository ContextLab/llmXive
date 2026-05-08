---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Simulated Social Status on Risk-Taking Behavior

**Field**: psychology

## Research question

Does observing higher-status agents engaging in risky behavior increase an individual's subsequent risk-taking, and does observing lower-status agents engaging in risky behavior decrease it?

## Motivation

Understanding how perceived social hierarchies shape decision-making is critical for addressing harmful risk-taking in online environments where status cues are ubiquitous. This work addresses a gap in experimental evidence on whether status markers alone (independent of actual competence or resources) can shift risk preferences through observational learning mechanisms.

## Literature gap analysis

### What we searched

Two queries were run against Semantic Scholar, arXiv, and OpenAlex: (1) "social status risk taking behavior psychology" and (2) "social hierarchy decision making experiment". The verified literature search returned only 2 results, neither of which directly addresses the research question on social status and risk-taking behavior.

### What is known

- [Modeling Influencer Marketing Campaigns in Social Networks (2021)](http://arxiv.org/abs/2106.01750v3) — Discusses how social media influencers facilitate information sharing and advertising, but does not measure status effects on risk-taking behavior.
- [Coordinated Behavior on Social Media in 2019 UK General Election (2020)](http://arxiv.org/abs/2008.08370v2) — Examines coordinated information operations and disinformation spread, but does not address individual risk preferences or status cues.

### What is NOT known

No published work in the verified literature directly examines the causal relationship between simulated social status markers and individual risk-taking decisions. Existing work focuses on information diffusion and coordinated behavior rather than individual-level decision-making under status manipulation. The specific interaction between observed agent status level and observed behavior type on subsequent risk-taking remains untested.

### Why this gap matters

Filling this gap would clarify whether online platforms' status systems inadvertently encourage risky behavior through observational channels, enabling evidence-based design of safer digital environments. This has practical implications for social media, gaming platforms, and online financial services where status markers are prominent.

### How this project addresses the gap

The methodology will manipulate both agent status level (high/low) and observed behavior (risky/conservative) in a factorial design using existing public datasets, then measure subsequent risk-taking in standardized tasks. This isolates the interaction effect that prior work has not tested.

## Expected results

We expect a significant interaction between observed agent status and observed behavior, where observing high-status agents take risks increases participants' own risk-taking more than observing low-status agents take risks. This would be confirmed by a mixed-effects logistic regression showing a positive status×behavior interaction coefficient (p < 0.05, effect size d > 0.4). A null result would be equally informative, suggesting status cues do not transmit risk preferences through observation.

## Methodology sketch

- Identify existing public datasets containing social status manipulation and risk-taking measures from Open Science Framework (OSF), ICPSR, or similar repositories.
- Preprocess data to extract condition assignments (status level, observed behavior) and outcome measures (risk-taking scores).
- Calculate descriptive statistics for each condition (mean risk-taking, SD, N).
- Fit mixed-effects logistic regression: `risk_taking ~ status_level * observed_behavior + (1|participant_id)`.
- Test interaction term significance; if p < 0.05, conduct post-hoc pairwise comparisons with Bonferroni correction.
- Generate effect size plots (forest plot of condition means with 95% CI).
- Conduct sensitivity analysis excluding outliers (>3 SD from condition mean).
- Document all code and data processing steps in reproducible R/Python script.
- Produce summary table of model coefficients, standard errors, and p-values.

## Duplicate-check

- Reviewed existing ideas: [N/A — no existing_idea_paths provided for this run].
- Closest match: [N/A — duplicate check requires existing_idea_paths input].
- Verdict: NOT a duplicate (pending duplicate-check against project corpus).
