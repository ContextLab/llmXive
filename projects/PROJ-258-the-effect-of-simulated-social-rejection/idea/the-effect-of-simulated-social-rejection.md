---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

**Field**: psychology

## Research question

How does prior simulated social rejection (via Cyberball paradigm) modulate subsequent responses to positive feedback in behavioral measures that proxy reward processing?

## Motivation

Social rejection is a well-documented stressor with lasting psychological consequences, yet the extent to which it dampens subsequent reward processing remains unclear. Understanding this mechanism could inform interventions for conditions involving reward deficits, such as depression and social anxiety. However, existing work has not systematically linked rejection-induced changes to subsequent positive feedback processing using publicly available behavioral data.

## Related work

- [Effects of Online Self-Disclosure on Social Feedback During the COVID-19 Pandemic (2022)](http://arxiv.org/abs/2209.10682v2) — Examines relationships between self-disclosure and social feedback during a crisis period, relevant for understanding how social feedback contexts affect psychological outcomes.
- [Opinion Polarization by Learning from Social Feedback (2017)](http://arxiv.org/abs/1704.02890v3) — Explores how social feedback shapes opinion dynamics, providing theoretical grounding for feedback-dependent processing.
- [The emulation theory of representation: Motor control, imagery, and perception (2004)](https://doi.org/10.1017/s0140525x04000093) — Offers a framework for understanding representational functions of the brain that may apply to social-emotional processing.

## Expected results

Individuals exposed to simulated social rejection will show reduced behavioral indicators of reward sensitivity (slower reaction times to positive feedback, lower self-reported satisfaction) compared to a control group. This effect should be measurable via group-level contrasts with medium effect size (Cohen's d ≥ 0.5). Evidence would be considered strong if p < 0.05 with FDR correction across multiple behavioral measures.

## Methodology sketch

- **Data source**: Download existing behavioral datasets from OpenNeuro (e.g., ds000208 Cyberball dataset with behavioral measures) or ICPSR social psychology repositories using `wget`/`curl` with explicit DOIs listed.
- **Participants**: Secondary analysis of existing datasets (N ≥ 30 per condition) to avoid new experimental collection.
- **Task paradigm**: Extract Cyberball social exclusion task behavioral outcomes and subsequent reward feedback task response times from existing session logs.
- **Preprocessing**: Clean and normalize behavioral data using Python/pandas; no raw-to-preprocessed conversion needed (CPU-compatible, <7GB RAM).
- **Outcome measures**: Extract reaction times to positive feedback, self-reported mood ratings, and task persistence as proxies for reward sensitivity.
- **Statistical test**: 2×2 mixed ANOVA (condition × time) with post-hoc t-tests; effect sizes computed via Cohen's d using Python/NumPy/SciPy.
- **Reproducibility**: All analysis scripts stored in GitHub repository; environment documented in requirements.txt for GHA compatibility.
- **Limitations**: Behavioral proxies cannot directly measure neural activation; relies on dataset availability and matching rejection/reward paradigms.

## Duplicate-check

- Reviewed existing ideas: None available in current corpus.
- Closest match: No direct matches found.
- Verdict: NOT a duplicate (adapted from neuroimaging to behavioral methodology to fit GHA constraints)
