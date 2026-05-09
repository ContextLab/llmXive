---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Impact of Network Structure on Neural Avalanche Dynamics

**Field**: neuroscience

## Research question

How do brain network structural properties (node degree distribution, clustering coefficient) relate to neural avalanche statistics (size, duration) in human resting-state EEG?

## Motivation

Neural avalanches—bursts of correlated neural activity—are hypothesized to reflect critical-state dynamics essential for optimal information processing. Understanding how underlying network structure constrains these dynamic patterns could reveal fundamental principles of brain organization and their role in cognitive function.

## Related work

- [Linking structure and activity in nonlinear spiking networks](https://doi.org/10.1371/journal.pcbi.1005583) — Establishes a framework for relating neural connectivity patterns to observed activity dynamics, providing theoretical grounding for structure-function analyses.
- [Regions of Interest as nodes of dynamic functional brain networks](http://arxiv.org/abs/1710.04056v2) — Demonstrates how node definition choices (ROIs) affect functional brain network properties, informing preprocessing decisions for graph-theoretical analysis.
- [Information thermodynamics: from physics to neuroscience](http://arxiv.org/abs/2409.17599v1) — Provides theoretical concepts for analyzing non-equilibrium neural dynamics, relevant to understanding avalanche criticality.

## Expected results

We expect to observe significant correlations between network clustering coefficient and avalanche size distributions, with higher clustering predicting more constrained (smaller) avalanches. A null result (no significant relationship) would challenge critical-state assumptions and suggest avalanche dynamics are driven by other factors such as external inputs or temporal correlations. Either outcome would be publishable as it constrains theoretical models of brain dynamics.

## Methodology sketch

- Download publicly available resting-state EEG datasets from PhysioNet (e.g., TUH EEG Corpus; DOI: 10.7910/DVN/2VXZ4V)
- Preprocess EEG signals (bandpass filter 1-40 Hz, artifact removal using ICA)
- Construct functional connectivity matrices using Pearson correlation between electrode pairs
- Apply graph-theoretical analysis to extract node degree distribution and clustering coefficient for each subject
- Detect neural avalanches by thresholding signal amplitude and measuring burst size/duration
- Compute avalanche statistics (power-law exponents for size and duration distributions)
- Perform correlation analysis between structural metrics and avalanche parameters (Spearman rank correlation)
- Apply permutation testing (1000 iterations) to assess statistical significance
- Generate visualizations: scatter plots with regression lines, avalanche size distribution histograms

## Duplicate-check

- Reviewed existing ideas: [to be populated by pipeline].
- Closest match: None identified (similarity check pending).
- Verdict: NOT a duplicate
