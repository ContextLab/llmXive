---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Alpha Oscillations and Working Memory Capacity

**Field**: neuroscience

## Research question

How do alpha-band (8-12 Hz) oscillation power and inter-site phase synchronization during working memory delay periods relate to individual differences in working memory capacity?

## Motivation

Alpha oscillations are theorized to play an active role in maintaining information during working memory tasks, yet the precise relationship between alpha dynamics and individual capacity limits remains unclear. Understanding this relationship could reveal whether alpha oscillations serve as a mechanistic substrate for working memory maintenance or merely reflect inhibitory processes. This distinction has implications for developing non-invasive biomarkers for cognitive capacity and for constraining neurophysiological models of working memory.

## Related work

- [Working Memory Capacity Is Negatively Associated with Memory Load Modulation of Alpha Oscillations in Retention of Verbal Working Memory](https://www.semanticscholar.org/paper/59b9bb2b5a8e345698befb36b0546c5e9cf82735) — Directly demonstrates that individual working memory capacity predicts alpha oscillation modulation during verbal working memory retention, establishing a foundation for this inquiry.
- [Working Memory and Cross-Frequency Coupling of Neuronal Oscillations](https://www.semanticscholar.org/paper/de968fe73d8d3317312162112014dd4333ec9e38) — Reviews how neuronal oscillations, including alpha band activity, support working memory function across multiple cognitive domains.
- [Theta, alpha and gamma traveling waves in a multi-item working memory model](http://arxiv.org/abs/2103.15266v1) — Computational modeling study proposing mechanisms by which alpha oscillations could support multi-item working memory, providing theoretical grounding for the proposed analysis.

## Expected results

We expect to observe a significant negative correlation between alpha power during delay periods and working memory performance, consistent with the hypothesis that alpha reflects active maintenance or gating mechanisms. Individual differences in phase synchronization across frontal-parietal networks should predict capacity limits beyond alpha power alone, with stronger synchronization associated with higher capacity. Effect sizes comparable to existing literature (r ≈ 0.3-0.5) would provide evidence for alpha oscillations as a viable biomarker for working memory capacity.

## Methodology sketch

- Download publicly available EEG datasets from OpenNeuro (e.g., ds000246, ds003474) containing n-back or change-detection working memory tasks with behavioral performance measures
- Preprocess EEG data using MNE-Python: bandpass filter (1-40 Hz), remove artifacts via ICA, re-reference to average mastoids, segment into trial epochs aligned to task events
- Extract alpha-band (8-12 Hz) power from frontal (F3, F4, Fz) and parietal (P3, P4, Pz) electrode sites during the delay period of each trial
- Compute pairwise phase locking value (PLV) between frontal-parietal electrode pairs during the same delay period using the Hilbert transform method
- Calculate individual working memory capacity estimates from behavioral accuracy (e.g., k-scores from change detection or d' from n-back tasks)
- Perform Pearson/Spearman correlation analyses between alpha power metrics and working memory capacity, with PLV metrics as secondary predictors
- Apply Bonferroni correction for multiple comparisons across electrode sites and frequency bands; report effect sizes and confidence intervals
- Validate findings through split-half reliability analysis and permutation testing to assess robustness

## Duplicate-check

- Reviewed existing ideas: None provided in input corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate
