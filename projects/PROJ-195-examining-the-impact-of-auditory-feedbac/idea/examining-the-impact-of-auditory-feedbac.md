---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Examining the Impact of Auditory Feedback on Motor Sequence Learning

**Field**: neuroscience

## Research question

How does perturbing auditory feedback during motor sequence learning alter neural activity in motor‑ and auditory‑related cortices, and how are these changes linked to behavioral performance?

## Motivation

Auditory cues are routinely used to scaffold motor skill acquisition, yet the precise neural mechanisms that detect and adapt to mismatched auditory feedback remain unclear. Understanding these mechanisms could inform rehabilitation protocols that rely on sensory feedback (e.g., stroke or Parkinson’s therapy).

## Related work

- [An adapting auditory‑motor feedback loop can contribute to generating vocal repetition (2015)](http://arxiv.org/abs/1501.00527v1) — Shows that sensory‑motor loops integrate auditory feedback to shape sequential actions, providing a theoretical basis for feedback‑driven motor adaptation.  
- [Augmented visual, auditory, haptic, and multimodal feedback in motor learning: A review (2012)](https://doi.org/10.3758/s13423-012-0333-8) — Reviews how different feedback modalities influence motor learning, highlighting auditory feedback as a potent driver of performance gains.  
- [RLHF‑Blender: A Configurable Interactive Interface for Learning from Diverse Human Feedback (2023)](http://arxiv.org/abs/2308.04332v1) — Discusses frameworks for gathering and modeling human feedback, relevant for designing controlled auditory perturbations.  
- [Evaluation of a congruent auditory feedback for Motor Imagery BCI (2018)](http://arxiv.org/abs/1805.07064v2) — Demonstrates that congruent auditory feedback improves motor‑imagery BCI performance, suggesting measurable behavioral effects of auditory cues.

## Expected results

We anticipate that delayed or pitch‑shifted auditory feedback will (1) increase BOLD responses in auditory cortex, superior temporal gyrus, and cerebellum relative to normal feedback, and (2) be associated with slower reaction times and reduced tapping accuracy. A significant interaction between feedback condition and brain activation (paired‑sample t‑test across subjects, *p* < 0.05, FDR‑corrected) would support the hypothesis that auditory‑motor error signals drive adaptive changes.

## Methodology sketch

- **Dataset acquisition** – Download the OpenNeuro finger‑tapping dataset *ds000115* (https://openneuro.org/datasets/ds000115) which includes auditory cue manipulations (normal, delayed, pitch‑shifted).  
- **Preprocessing** – Run `fmriprep` (Docker image) on the GHA runner to perform slice‑time correction, motion correction, spatial normalization, and smoothing (≤6 mm).  
- **Condition definition** – Use the provided event files to label trials by feedback type (normal, delayed, pitch‑shifted).  
- **First‑level GLM** – For each participant, fit a voxel‑wise GLM with `nilearn` (regressors: feedback condition, motion parameters). Obtain contrast maps for *perturbed > normal* feedback.  
- **Group analysis** – Stack contrast maps across subjects and run a paired‑sample t‑test (`nilearn.mass_univariate`) comparing perturbed vs. normal feedback. Apply cluster‑wise FDR correction.  
- **Behavioral linkage** – Extract trial‑wise reaction times and accuracy from the event files; compute subject‑level mean RT/accuracy per condition. Correlate these behavioral metrics with subject‑level contrast values in regions of interest (auditory cortex, SMA, cerebellum) using Pearson’s *r*.  
- **Visualization** – Generate thresholded statistical maps and scatter plots of brain‑behavior correlations with `matplotlib`/`seaborn`.  
- **Statistical validation** – Report effect sizes (Cohen’s *d*), confidence intervals, and perform a post‑hoc power analysis to confirm adequacy of the sample size (≈30 participants).  

All steps rely on open‑source Python packages (`nibabel`, `nilearn`, `pandas`, `statsmodels`) and data that can be downloaded within the 6‑hour GHA window.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A (no similar fleshed‑out idea found).
- Verdict: **NOT a duplicate**
