---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

**Field**: neuroscience

## Research question

Can network centrality metrics (degree, betweenness, eigenvector centrality) derived from structural or functional connectivity matrices predict the magnitude of functional synchrony between brain regions during resting-state fMRI?

## Motivation

Understanding how topological hub regions influence functional coordination is critical for models of efficient brain communication. While resting-state networks are well-documented, the relationship between network position and local synchrony remains underexplored. This analysis could identify whether high-centrality regions act as synchronization anchors that organize large-scale functional dynamics.

## Related work

- [Dynamic changes in network synchrony reveal resting-state functional networks (2014)](http://arxiv.org/abs/1412.5931v1) — Establishes that spontaneous fMRI activity exhibits complex spatial-temporal co-activity patterns relevant to network synchrony analysis.
- [Consistency of Regions of Interest as nodes of functional brain networks measured by fMRI (2017)](http://arxiv.org/abs/1704.07635v1) — Validates ROI-based parcellation approaches for constructing functional brain network graphs from fMRI BOLD time series.
- [Fractal-driven distortion of resting state functional networks in fMRI: a simulation study (2012)](http://arxiv.org/abs/1208.0924v1) — Demonstrates scale-invariant properties in resting-state networks that may affect centrality measurements and interpretation.
- [Automatic artifact removal of resting-state fMRI with Deep Neural Networks (2020)](http://arxiv.org/abs/2011.12113v2) — Provides preprocessing techniques for cleaning fMRI data before network construction, improving signal reliability.
- [Information thermodynamics: from physics to neuroscience (2024)](http://arxiv.org/abs/2409.17599v1) — Offers theoretical framework for understanding information integration in brain networks relevant to hub function.

## Expected results

We expect to find a positive correlation between node centrality measures and mean functional connectivity strength (synchrony) with other regions. Statistical significance will be confirmed through permutation testing (n=1000) with p<0.05 corrected for multiple comparisons. Effect sizes (Cohen's d) should exceed 0.5 to demonstrate practical relevance beyond statistical significance.

## Methodology sketch

- Download resting-state fMRI data from Human Connectome Project (HCP) public repository: https://www.humanconnectome.org/study/hcp-young-adult/data-releases (1200 Subjects release, filtered to n=100 for feasibility)
- Preprocess BOLD time series using fMRIPrep-lite or FSL FEAT: motion correction, slice-timing correction, nuisance regression (CSF, white matter, global signal)
- Parcellate brain into 200-400 ROIs using Schaefer 400 atlas or AAL3 (download from https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal)
- Construct functional connectivity matrix by computing Pearson correlation between all ROI time series pairs
- Compute centrality metrics (degree, betweenness, eigenvector) using NetworkX Python library on thresholded connectivity graphs
- Calculate mean functional synchrony per ROI as average absolute correlation with all other ROIs
- Perform Spearman correlation between each centrality metric and mean synchrony across all nodes
- Apply permutation testing (1000 random node label shuffles) to assess null distribution of correlations
- Generate scatter plots with regression lines and confidence intervals for visualization
- Run analysis on single HCP subject first (30 min runtime), then scale to batch processing (4 hours for 100 subjects)

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: N/A (no prior ideas on centrality-synchrony relationship).
- Verdict: NOT a duplicate
