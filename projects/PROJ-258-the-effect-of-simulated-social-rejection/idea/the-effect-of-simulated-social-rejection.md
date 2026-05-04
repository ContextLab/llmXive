---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Effect of Simulated Social Rejection on Neural Responses to Positive Feedback

**Field**: psychology

## Research question

How does prior simulated social rejection (via Cyberball paradigm) modulate neural activation in reward-related brain regions when individuals subsequently receive positive feedback on a cognitive task?

## Motivation

Social rejection is a well-documented stressor with lasting psychological consequences, yet the extent to which it dampens subsequent reward processing remains unclear. Understanding this mechanism could inform interventions for conditions involving reward deficits, such as depression and social anxiety. However, existing work has not systematically linked rejection-induced neural changes to subsequent positive feedback processing.

## Related work

- [Effects of Online Self-Disclosure on Social Feedback During the COVID-19 Pandemic (2022)](http://arxiv.org/abs/2209.10682v2) — Examines relationships between self-disclosure and social feedback during a crisis period, relevant for understanding how social feedback contexts affect psychological outcomes.
- [Opinion Polarization by Learning from Social Feedback (2017)](http://arxiv.org/abs/1704.02890v3) — Explores how social feedback shapes opinion dynamics, providing theoretical grounding for feedback-dependent neural processing.
- [The emulation theory of representation: Motor control, imagery, and perception (2004)](https://doi.org/10.1017/s0140525x04000093) — Offers a framework for understanding representational functions of the brain that may apply to social-emotional processing.

## Expected results

Individuals exposed to simulated social rejection will show reduced activation in ventral striatum and medial prefrontal cortex during positive feedback compared to a control group. This effect should be measurable via group-level contrasts with medium effect size (Cohen's d ≥ 0.5). Evidence would be considered strong if p < 0.05 with FDR correction across reward-related ROIs.

## Methodology sketch

- **Data source**: Use publicly available fMRI datasets from OpenNeuro or NeuroVault containing social rejection paradigms (e.g., Cyberball studies) with DOIs listed for download.
- **Participants**: Secondary analysis of existing datasets (N ≥ 30 per condition) to avoid new experimental collection.
- **Task paradigm**: Cyberball social exclusion task followed by reward feedback task (extracted from existing fMRI sessions).
- **Preprocessing**: Standard fMRI pipeline (realignment, normalization, smoothing) using FSL or AFNI on CPU-compatible workflows.
- **ROI analysis**: Extract BOLD signal from ventral striatum and mPFC using established atlases (e.g., Harvard-Oxford).
- **Statistical test**: 2×2 mixed ANOVA (condition × time) with post-hoc t-tests; effect sizes computed via Cohen's d.
- **Reproducibility**: All code stored in GitHub repository; analysis scripts documented for peer review.
- **Limitations**: No primary data collection; relies on dataset availability and matching rejection/reward paradigms.

## Duplicate-check

- Reviewed existing ideas: None available in current corpus.
- Closest match: No direct matches found.
- Verdict: **rejected — out of scope** (requires fMRI scanner and specialized neuroimaging hardware incompatible with GitHub Actions free-tier constraints)
