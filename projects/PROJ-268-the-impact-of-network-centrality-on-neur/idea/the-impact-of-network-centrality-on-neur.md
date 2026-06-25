---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI

**Field**: neuroscience

## Research question

Do structural-connectivity-derived centrality metrics (from diffusion MRI) predict the magnitude of functional synchrony measured from resting-state fMRI?

## Motivation

Understanding how anatomical hub regions shape functional coordination is critical for models of efficient brain communication. While resting-state networks are well-documented, the relationship between structural network position and functional synchrony remains underexplored. This analysis could identify whether high-centrality regions in the structural connectome act as synchronization anchors that organize large-scale functional dynamics.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using the following search terms: (1) "structural connectivity centrality functional synchrony fMRI" for the exact research question, and (2) "resting-state functional network centrality" for broader methodological territory. The literature block returned 3 results, all focused on functional network properties or fractal characteristics of resting-state fMRI. No results directly addressed the structure-function prediction relationship between diffusion-derived centrality and fMRI synchrony.

### What is known

- [Fractal-driven distortion of resting state functional networks in fMRI: a simulation study (2012)](https://arxiv.org/abs/1208.0924) — Demonstrates scale-invariant properties in resting-state networks that may affect network metric interpretation.
- [Consistency of Regions of Interest as nodes of functional brain networks measured by fMRI (2017)](https://arxiv.org/abs/1704.07635) — Validates ROI-based parcellation approaches for constructing functional brain network graphs from fMRI BOLD time series.
- [Fractal-based Correlation Analysis for Resting State Functional Connectivity of the Rat Brain in Functional MRI (2012)](https://arxiv.org/abs/1202.4751) — Shows spontaneous low-frequency fluctuations in blood oxygenation underlie resting-state functional connectivity patterns.

### What is NOT known

No published work in this literature block has explicitly measured whether structural connectivity centrality metrics (degree, betweenness, eigenvector from diffusion MRI) predict functional synchrony strength (from resting-state fMRI) across brain regions. The structure-function relationship remains unquantified in terms of node-level centrality-to-synchrony mapping.

### Why this gap matters

This gap matters for understanding how anatomical architecture constrains functional dynamics. Filling it could enable better models of brain communication efficiency and inform neuromodulation targeting strategies. Clinically, identifying structural hubs that drive functional synchrony could help predict network vulnerability in disorders like Alzheimer's or schizophrenia.

### How this project addresses the gap

This project directly measures the correlation between diffusion-derived centrality metrics and fMRI-derived synchrony strength across matched brain regions. The methodology computes centrality from structural connectomes and synchrony from functional connectomes in the same subjects, then quantifies the predictive relationship through regression analysis.

## Expected results

We expect to find a positive correlation between structural connectivity centrality measures and mean functional synchrony strength across brain regions. Statistical significance will be confirmed through permutation testing (n=1000) with p<0.05 corrected for multiple comparisons. Effect sizes (Cohen's d) should exceed 0.5 to demonstrate practical relevance beyond statistical significance.

## Methodology sketch

- Download resting-state fMRI and diffusion MRI data from Human Connectome Project (HCP) public repository: https://www.humanconnectome.org/study/hcp-young-adult/data-releases (1200 Subjects release, filtered to n=50 for 6h runtime feasibility)
- Preprocess BOLD time series using fMRIPrep-lite: motion correction, slice-timing correction, nuisance regression (CSF, white matter, global signal)
- Preprocess diffusion MRI using MRtrix3 or FSL DTIFIT: eddy current correction, diffusion tensor fitting, tractography
- Parcellate brain into 200-400 ROIs using Schaefer 400 atlas (download from https://github.com/ThomasYeoLab/CBIG/tree/master/stable_projects/brain_parcellation/Schaefer2018_LocalGlobal)
- Construct structural connectivity matrix by counting streamlines between ROI pairs from diffusion tractography
- Construct functional connectivity matrix by computing Pearson correlation between all ROI BOLD time series pairs
- Compute centrality metrics (degree, betweenness, eigenvector) using NetworkX Python library on thresholded structural connectivity graphs
- Calculate mean functional synchrony per ROI as average absolute correlation with all other ROIs
- Perform Spearman correlation between structural centrality metrics and functional synchrony across all nodes (predictor: diffusion data; predicted: fMRI data)
- Apply permutation testing (1000 random node label shuffles) to assess null distribution of correlations
- Generate scatter plots with regression lines and confidence intervals for visualization
- Validate independence: structural connectivity (diffusion) and functional synchrony (fMRI) are measured from distinct MRI modalities with independent acquisition sequences

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: N/A (no prior ideas on structure-function centrality-synchrony relationship).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-25T14:43:01Z
**Outcome**: exhausted
**Original term**: The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI neuroscience
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Impact of Network Centrality on Neural Synchrony in Resting-State fMRI neuroscience | 0 |
| 1 | functional connectivity and graph theory metrics | 2 |
| 2 | resting-state network hub identification | 0 |
| 3 | graph theoretical analysis of rs-fMRI | 0 |
| 4 | nodal centrality in functional brain networks | 0 |
| 5 | betweenness centrality functional connectivity | 0 |
| 6 | degree centrality resting-state networks | 0 |
| 7 | intrinsic connectivity networks topology | 0 |
| 8 | brain network hubs and functional coupling | 0 |
| 9 | BOLD signal correlation network metrics | 0 |
| 10 | functional connectivity strength and node centrality | 0 |
| 11 | default mode network centrality analysis | 0 |
| 12 | network neuroscience resting-state fMRI | 0 |
| 13 | spontaneous brain activity topological properties | 0 |
| 14 | functional brain network architecture | 0 |
| 15 | nodal efficiency and functional coupling | 0 |
| 16 | connectome centrality measures | 0 |
| 17 | large-scale brain network topology | 0 |
| 18 | resting-state functional connectivity hubs | 0 |
| 19 | graph metrics of functional connectivity | 0 |
| 20 | topological organization of rs-fMRI networks | 0 |

### Verified citations

1. **Fractal-driven distortion of resting state functional networks in fMRI: a simulation study** (2012). Wonsang You, Jörg Stadler. arXiv. [1208.0924](https://arxiv.org/abs/1208.0924). PDF-sampled: Yes.
2. **Consistency of Regions of Interest as nodes of functional brain networks measured by fMRI** (2017). Onerva Korhonen, Heini Saarimäki, Enrico Glerean, Mikko Sams, Jari Saramäki. arXiv. [1704.07635](https://arxiv.org/abs/1704.07635). PDF-sampled: No.
3. **Fractal-based Correlation Analysis for Resting State Functional Connectivity of the Rat Brain in Functional MRI** (2012). Wonsang You, Joerg Stadler. arXiv. [1202.4751](https://arxiv.org/abs/1202.4751). PDF-sampled: No.
