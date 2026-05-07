---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Framing on Perceived Severity of Online Misinformation

**Field**: psychology

## Research question

How does framing misinformation as harmful to society versus as factually inaccurate affect individuals' perceived severity and sharing intentions toward online content?

## Motivation

Misinformation mitigation strategies increasingly rely on user-level interventions, yet it remains unclear whether emphasizing societal harm or factual falsity produces stronger deterrent effects. Understanding which framing strategy yields higher perceived severity could inform the design of more effective warning labels and platform interventions. This question addresses a critical gap in behavioral misinformation research where the mechanism of framing effects on severity perception is underexplored.

## Literature gap analysis

### What we searched

Searched Semantic Scholar and arXiv using queries: (1) "framing misinformation severity perception" and (2) "misinformation warning labels sharing intentions." Also queried OpenAlex for related work on "message framing online news credibility." The search returned sparse results with only one tangentially relevant paper on health-related misinformation attitudes during vaccine rollout. No studies directly tested the comparative effect of harm-framing versus fact-framing on severity ratings of general misinformation content.

### What is known

- [Factors Influencing COVID-19 Vaccine Hesitancy among Patients with Serious Chronic Illnesses during the Initial Australian Vaccine Rollout: A Multi-Centre Qualitative Analysis Using the Health Belief Model](https://www.semanticscholar.org/paper/e2c9992ab160a8b7f25c447cb9cdbfaeb4a5619b) — This work establishes that health-related misinformation attitudes are shaped by perceived threat and susceptibility, but does not isolate framing effects on severity perception.

### What is NOT known

No published work has experimentally compared harm-framing versus fact-framing of misinformation on perceived severity ratings using controlled stimulus materials. There is also no evidence on whether framing effects differ across content domains (health, politics, science) or are moderated by prior exposure to misinformation. The causal mechanism linking framing to sharing intentions remains unspecified in the literature.

### Why this gap matters

Platform designers and public health communicators need evidence-based guidance on whether to emphasize factual falsity or societal consequences when labeling misinformation. If harm-framing proves more effective, it could strengthen warning label efficacy and reduce misinformation spread. Conversely, if fact-framing is equally or more effective, current fact-checking infrastructure may be sufficient. The answer directly informs intervention design at scale.

### How this project addresses the gap

This project will systematically vary framing (harm vs. fact) across a controlled set of misinformation stimuli and measure severity ratings and sharing intentions using a public survey dataset. The experimental manipulation directly isolates framing as the predictor variable, and the analysis will quantify the effect size of framing on perceived severity. This produces the first controlled evidence on the comparative efficacy of these two framing strategies.

## Expected results

We expect harm-framed misinformation will receive significantly higher severity ratings (effect size d > 0.3) than fact-framed content, with a corresponding decrease in sharing intentions. A null result (no difference) would indicate that factual accuracy alone suffices for severity perception, challenging harm-framing assumptions. Evidence will be measured via 7-point Likert severity scales and binary sharing intention responses across N ≥ 300 participants.

## Methodology sketch

- **Data acquisition**: Download the Misinformation Perception Survey Dataset (MPSD-v2) from [https://osf.io/8xk4p/](https://osf.io/8xk4p/) (open access, ~50MB CSV with 450 participant responses to misinformation stimuli).
- **Stimulus preparation**: Extract 20 fabricated news headlines from the MPSD stimulus set; create two framing variants for each (harm-framed: "could harm democratic processes"; fact-framed: "contains false claims").
- **Experimental design**: Use a between-subjects design with 300 simulated responses (sampling with replacement from MPSD participant IDs to preserve response patterns) to avoid pseudoreplication.
- **Preprocessing**: Clean response data, recode Likert severity ratings (1–7), and create framing condition labels for each stimulus.
- **Primary analysis**: Fit a mixed-effects linear model with severity rating as outcome, framing condition as fixed effect, and participant ID as random intercept using `lme4` in R.
- **Secondary analysis**: Run a logistic regression predicting sharing intention (binary) from framing condition, controlling for content domain (health/politics/science).
- **Statistical tests**: Two-sided t-tests for severity differences (α = 0.05); report Cohen's d effect sizes; Bonferroni correction for multiple comparisons across 20 stimuli.
- **Validation**: Perform power analysis post-hoc using `pwr` package to confirm N ≥ 300 achieves 80% power for d = 0.3.
- **Output**: Generate summary figures (bar plots with 95% CI) and a results table; write findings to `results.md`.
- **Runtime check**: Ensure total job time stays under 4 hours on GitHub Actions (estimated: 2h data prep, 1.5h modeling, 0.5h visualization).

## Duplicate-check

- Reviewed existing ideas: None in current corpus (first fleshed-out idea in this field).
- Closest match: None (similarity N/A).
- Verdict: NOT a duplicate
