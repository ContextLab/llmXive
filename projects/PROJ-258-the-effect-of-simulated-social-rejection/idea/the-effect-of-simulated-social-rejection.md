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

- **Data source**: Download preprocessed fMRI datasets from OpenNeuro (e.g., ds000208 Cyberball dataset) or NeuroVault using `wget`/`curl` with explicit DOIs listed for reproducibility.
- **Participants**: Secondary analysis of existing datasets (N ≥ 30 per condition) to avoid new experimental collection.
- **Task paradigm**: Extract Cyberball social exclusion task and subsequent reward feedback task from existing fMRI session logs.
- **Preprocessing**: Use CPU-compatible fMRI pipelines (FSL/AFNI) on preprocessed BOLD data only; no raw-to-preprocessed conversion to stay within 7GB RAM constraints.
- **ROI analysis**: Extract BOLD signal from ventral striatum and mPFC using Harvard-Oxford atlas masks applied to preprocessed data.
- **Statistical test**: 2×2 mixed ANOVA (condition × time) with post-hoc t-tests; effect sizes computed via Cohen's d using Python/NumPy.
- **Reproducibility**: All analysis scripts stored in GitHub repository with Docker container for environment consistency.
- **Limitations**: No primary data collection; relies on dataset availability and matching rejection/reward paradigms.

## Duplicate-check

- Reviewed existing ideas: None available in current corpus.
- Closest match: No direct matches found.
- Verdict: **rejected — out of scope** (requires fMRI scanner and specialized neuroimaging hardware incompatible with GitHub Actions free-tier constraints; preprocessing even preprocessed datasets exceeds 7GB RAM and 6-hour job limits for N≥30 participants)
