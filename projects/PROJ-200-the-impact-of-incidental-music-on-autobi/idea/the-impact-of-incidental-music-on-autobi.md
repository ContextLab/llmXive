---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Incidental Music on Autobiographical Memory Retrieval

**Field**: psychology  

## Research question

Does exposure to music that was frequently heard during adolescence serve as an effective cue for retrieving vivid, emotionally rich autobiographical memories later in life?

## Motivation

Understanding how incidental auditory cues from a sensitive developmental period influence memory retrieval can illuminate mechanisms of musical nostalgia and identity formation. While prior work has examined involuntary autobiographical memories (IAMs) in general, the specific role of adolescent music exposure as a cue remains underexplored.

## Related work

- [Involuntary autobiographical memories and their relation to other forms of spontaneous thoughts (2020)](https://doi.org/10.1098/rstb.2019.0693) — Discusses the spontaneous emergence of autobiographical memories and provides a theoretical framework for cue‑driven retrieval, relevant for interpreting music‑evoked memories.

## Expected results

We anticipate finding a positive association between the frequency of adolescent music exposure (as measured by historic listening logs) and the vividness/emotional valence of autobiographical memories cued by the same tracks in adulthood. A statistically significant regression coefficient (p < 0.05) for adolescent exposure in a mixed‑effects model would confirm the hypothesis; a null or negative effect would falsify it.

## Methodology sketch

- **Data acquisition**
  - Download the *Million Song Dataset* (MSD) and the public *Last.fm 1‑Billion Dataset* (via Zenodo DOI: 10.5281/zenodo.2592305) to obtain user‑level listening histories.
  - Obtain a publicly available autobiographical memory questionnaire dataset (e.g., the *Autobiographical Memory Test* dataset from OpenPsych, DOI: 10.5281/zenodo.4291234).
- **Participant selection**
  - Identify participants in the music logs who have self‑reported age and birth year, allowing reconstruction of listening behavior between ages 12‑18.
  - Match these participants to respondents in the memory questionnaire using anonymized IDs (if available) or via a shared crowdsourcing platform (e.g., Prolific) where both data sources can be linked ethically.
- **Feature engineering**
  - For each participant, compute the **Adolescent Exposure Score**: proportion of total listening events that occurred during ages 12‑18 for each track.
  - Compute a **Current Exposure Indicator** for each track (listened to at least once in the past 30 days).
  - Extract memory‑cue items from the questionnaire that specify a music‑related cue; record vividness (0‑100) and emotional valence (−5 to +5) ratings.
- **Cue‑matching**
  - Match tracks from the adolescent exposure list to current exposure tracks; flag matches as **Music Cues**.
  - For each cue, link the corresponding memory rating (vividness, valence).
- **Statistical analysis**
  - Fit a linear mixed‑effects model:  
    `MemoryScore ~ AdolescentExposureScore * CurrentCue + Age + Gender + (1|Participant)`.
  - Test the interaction term to assess whether adolescent exposure amplifies the effect of current cues.
  - Perform robustness checks using bootstrapped confidence intervals (10 000 resamples) and Bayesian model comparison (BF > 3 as supportive).
- **Control analyses**
  - Repeat the model with **Non‑music cues** (e.g., visual or olfactory) to verify specificity.
  - Include a random permutation of adolescent exposure scores to confirm that observed effects are not due to chance alignment.
- **Reproducibility**
  - All code will be written in Python (pandas, numpy, statsmodels, pymc3) and packaged as a Jupyter notebook.
  - Data download scripts will use `wget`/`curl` with checksums; intermediate files will be stored under 2 GB to stay within runner limits.
  - Final figures (scatter plots, model diagnostics) will be saved as PNG/HTML for easy inspection.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: none.
- Verdict: NOT a duplicate.
