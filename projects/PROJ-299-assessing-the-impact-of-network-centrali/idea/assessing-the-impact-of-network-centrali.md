---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Assessing the Impact of Network Centrality on Age-Related Cognitive Decline

**Field**: neuroscience

## Research question

Do network centrality metrics (degree, betweenness, closeness) derived from resting-state fMRI data in older adults predict performance on standardized cognitive assessments, particularly within the default mode and frontoparietal networks?

## Motivation

Age-related cognitive decline affects millions globally, yet the neural mechanisms linking brain network topology to cognitive function remain incompletely characterized. Understanding whether specific centrality alterations in key cognitive networks predict decline could identify early biomarkers for at-risk individuals. This analysis leverages publicly available neuroimaging data to address this gap without requiring new data collection.

## Related work

- [The Impact of Social Isolation on Subjective Cognitive Decline in Older Adults: A Study Based on Network Analysis and Longitudinal Model (2025)](http://arxiv.org/abs/2506.13914v2) — Demonstrates network analysis approaches for studying cognitive decline in older adults, though focused on social rather than neural networks.
- [Deep Learning for Cognitive Neuroscience (2019)](http://arxiv.org/abs/1903.01458v1) — Reviews computational approaches in cognitive neuroscience, including neural network models relevant to analyzing brain imaging data.

## Expected results

We expect to find that decreased centrality in hub regions of the default mode network (e.g., posterior cingulate, medial prefrontal cortex) correlates with poorer episodic memory performance. A statistically significant negative correlation (p < 0.05, effect size r > 0.3) would support the hypothesis that network topology changes precede or accompany cognitive decline.

## Methodology sketch

- Download ADNI resting-state fMRI data and cognitive assessment scores via ADNI portal (adni.loni.usc.edu; requires registration, free for academic use)
- Preprocess fMRI data using FSL/AFNI on CPU: motion correction, slice-time correction, normalization to MNI space, bandpass filtering (0.01-0.1 Hz)
- Define 90-region atlas (AAL) and extract mean time series per region
- Compute functional connectivity matrix (Pearson correlation) for each participant
- Calculate centrality metrics (degree, betweenness, closeness) using NetworkX library (Python, CPU-efficient)
- Extract mean centrality values for default mode and frontoparietal network nodes
- Perform linear regression with cognitive scores (ADAS-Cog, MMSE, processing speed) as dependent variables and centrality metrics as predictors
- Control for age, sex, and education as covariates
- Apply Bonferroni correction for multiple comparisons across 3 centrality metrics × 3 cognitive domains
- Generate correlation plots and regression coefficient tables for visualization

## Duplicate-check

- Reviewed existing ideas: None available in current context.
- Closest match: None identified.
- Verdict: NOT a duplicate

**Feasibility note**: This methodology is designed for GitHub Actions free-tier execution. All software (FSL, AFNI, NetworkX, Python) is open-source and CPU-compatible. ADNI data download and preprocessing may require ~4-5 hours; graph analysis and statistics ~1 hour. Total runtime fits within 6-hour limit.
