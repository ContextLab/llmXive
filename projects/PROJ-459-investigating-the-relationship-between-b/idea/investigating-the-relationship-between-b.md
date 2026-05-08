---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Brain Network Dynamics and Musical Genre Preference

**Field**: neuroscience

## Research question

How do individual differences in resting-state functional connectivity patterns relate to musical genre preference?

## Motivation

Musical taste varies substantially across individuals, yet the neural substrates underlying these preferences remain poorly understood. While prior work has examined music-evoked emotions in fMRI, no published study has investigated whether baseline brain network architecture predicts aesthetic preferences for specific musical genres. Addressing this gap could inform models of how individual brain organization shapes complex aesthetic experiences.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using search terms including "musical genre preference fMRI," "resting-state connectivity music," "brain networks aesthetic preference," and "functional connectivity musical taste." The literature block returned four papers: three methodological papers on fMRI network construction (ROI consistency, dynamic network nodes, controllability scores) and one study on music-evoked emotions (happy/sad with/without lyrics). No papers directly examined the relationship between resting-state functional connectivity and musical genre preference.

### What is known

- [A Functional MRI Study of Happy and Sad Emotions in Music with and without Lyrics (2011)](https://doi.org/10.3389/fpsyg.2011.00308) — This work establishes that fMRI can detect neural responses to musical emotions, though it focuses on induced emotions rather than stable genre preferences.
- [Consistency of Regions of Interest as nodes of functional brain networks measured by fMRI (2017)](http://arxiv.org/abs/1704.07635v1) — This work establishes methodological standards for constructing functional brain networks from fMRI data, which are prerequisites for measuring individual connectivity patterns.
- [Regions of Interest as nodes of dynamic functional brain networks (2017)](http://arxiv.org/abs/1710.04056v2) — This work establishes how ROI selection affects dynamic network metrics, informing how to compute the network measures needed for this analysis.

### What is NOT known

No published work has measured whether resting-state functional connectivity metrics (e.g., global efficiency, modularity, dynamic reconfiguration) correlate with self-reported musical genre preferences in healthy adults. The existing music-fMRI literature focuses on task-based emotional responses rather than trait-level preference patterns.

### Why this gap matters

Understanding whether brain network architecture predicts aesthetic preferences could inform theories of individual differences in sensory processing and reward valuation. This has implications for personalized music recommendation systems, therapeutic applications in music therapy, and fundamental models of how neural variability shapes subjective experience.

### How this project addresses the gap

This project will compute resting-state functional connectivity metrics from publicly available fMRI datasets and correlate them with genre preference scores. The methodology directly produces the previously-unavailable evidence linking baseline brain network organization to musical taste.

## Expected results

We expect to find modest but statistically significant correlations between specific network metrics (particularly default mode network integration and auditory cortex connectivity) and preference for certain genres (e.g., classical vs. electronic). A null result would be equally informative, suggesting that musical preference is shaped by factors outside baseline functional architecture (e.g., cultural exposure, learning history). Correlation coefficients ≥0.3 with p<0.05 after multiple-comparison correction would constitute publishable evidence.

## Methodology sketch

- Download resting-state fMRI data from OpenNeuro (e.g., ds000030, ds000208) and associated behavioral metadata containing musical preference questionnaires
- Preprocess fMRI data using fMRIPrep (Docker container) to obtain standardized BOLD time series
- Define cortical ROIs using the Schaefer-400 atlas to extract regional time courses
- Compute static functional connectivity matrices (Pearson correlation between ROI time series)
- Calculate network metrics: global efficiency, modularity, and mean within-module degree for default mode, auditory, and salience networks
- Compute dynamic functional connectivity using sliding-window analysis (window=30 TRs, step=5 TRs) to extract reconfiguration metrics
- Obtain genre preference scores from self-report surveys (e.g., STOMP-R or custom Likert-scale questionnaire)
- Perform Spearman correlation between each network metric and each genre preference score
- Apply Benjamini-Hochberg correction for multiple comparisons across all metric-genre pairs
- Generate visualization figures (correlation heatmaps, network diagrams) and statistical summary tables

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: None identified.
- Verdict: NOT a duplicate
