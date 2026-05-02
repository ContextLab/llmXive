---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Metacognitive Awareness on Reality Testing

**Field**: psychology

## Research question

Do individuals with higher metacognitive awareness exhibit more accurate reality testing, as measured by reduced source‑monitoring errors on ambiguous perceptual tasks?

## Motivation

Reality testing deficits underlie psychotic‑like experiences and several clinical conditions. While metacognition is linked to self‑regulation and insight, its specific contribution to distinguishing internal thoughts from external events remains unclear. Demonstrating a protective relationship would suggest that enhancing metacognitive awareness could be a low‑cost target for early interventions.

## Related work

- [Knowing your own heart: Distinguishing interoceptive accuracy from interoceptive awareness (2014)](https://doi.org/10.1016/j.biopsycho.2014.11.004) — Shows that interoceptive awareness, a facet of metacognition, predicts performance on tasks requiring internal‑external discrimination, providing a theoretical bridge to reality‑testing abilities.

## Expected results

We anticipate a moderate positive correlation (r ≈ 0.30–0.45) between scores on the Metacognition Awareness Questionnaire (MAQ) and accuracy on source‑monitoring tasks. A regression controlling for general cognitive ability should retain significance, indicating a unique contribution of metacognitive awareness. Null results would suggest that reality‑testing deficits are driven by other mechanisms.

## Methodology sketch

1. **Data acquisition**
   - Download the OpenNeuro “Source‑Monitoring” dataset (DOI: 10.18112/openneuro.ds003386.v1.0.0) containing stimulus files and participant responses.
   - Retrieve the Metacognition Awareness Questionnaire (MAQ) items from the public repository (https://osf.io/maqt7/).

2. **Participant selection**
   - Use the existing 120 participants in the OpenNeuro dataset (healthy adults, ages 18‑35). No new data collection required.

3. **Pre‑processing**
   - Parse stimulus logs to extract trial‑wise source labels (imagined vs. perceived) and participant responses.
   - Score MAQ responses (0–4 Likert) to produce a continuous metacognitive awareness score per participant.

4. **Compute reality‑testing performance**
   - Calculate source‑monitoring accuracy (hits + correct rejections / total trials) for each participant.
   - Derive signal‑detection measures (d′, criterion) to capture bias.

5. **Statistical analysis**
   - Perform Pearson correlation between MAQ scores and source‑monitoring accuracy/d′.
   - Run a hierarchical linear regression: Step 1 – include age, gender, and a brief working‑memory span (from the dataset); Step 2 – add MAQ score to test incremental variance.
   - Check assumptions (normality, homoscedasticity) and apply bootstrapped confidence intervals (1,000 resamples) to ensure robustness.

6. **Robustness checks**
   - Replicate the analysis using only ambiguous visual stimuli (e.g., degraded images) versus auditory stimuli to test modality specificity.
   - Conduct a mediation analysis to explore whether interoceptive awareness (if available in the dataset) mediates the MAQ–reality‑testing link.

7. **Reproducibility**
   - Implement the pipeline in a Python notebook using `pandas`, `numpy`, `scipy`, and `statsmodels`.
   - Containerize the environment with a `requirements.txt` (≈ 30 MB) to guarantee execution within the 7 GB RAM, 2‑CPU GitHub Actions runner (< 30 min total runtime).

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A (no similar fleshed‑out ideas identified).
- Verdict: **NOT a duplicate**.
