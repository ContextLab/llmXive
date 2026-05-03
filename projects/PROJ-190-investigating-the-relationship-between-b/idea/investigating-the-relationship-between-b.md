---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Brain Network Efficiency and Fluid Intelligence  

**Field**: neuroscience  

## Research question  

Do graph‑theoretical measures of brain network efficiency derived from resting‑state fMRI predict individual differences in fluid intelligence, and is efficiency within the frontoparietal network a stronger predictor than global efficiency?  

## Motivation  

Fluid intelligence varies widely across healthy adults, yet the neurobiological mechanisms that support this variation are not fully understood. Prior work has linked functional connectivity patterns to cognitive ability, but the specific contribution of network efficiency—how easily information can travel across the brain—has received limited empirical attention. Clarifying this relationship would deepen mechanistic models of intelligence and could inform biomarkers for cognitive health.  

## Related work  

- [A brain basis of dynamical intelligence for AI and computational neuroscience (2021)](http://arxiv.org/abs/2105.07284v2) — Discusses dynamical properties of brain networks that support intelligent behavior, providing a theoretical backdrop for efficiency‑based metrics.  
- [The role of prefrontal cortex in cognitive control and executive function (2021)](https://doi.org/10.1038/s41386-021-01132-0) — Highlights the prefrontal–parietal circuitry as central to high‑level cognition, supporting the focus on frontoparietal efficiency.  
- [Regions of Interest as nodes of dynamic functional brain networks (2017)](http://arxiv.org/abs/1710.04056v2) — Shows how ROI‑based node definitions affect functional network properties, guiding our node selection strategy.  
- [Consistency of Regions of Interest as nodes of functional brain networks measured by fMRI (2017)](http://arxiv.org/abs/1704.07635v1) — Provides evidence that ROI‑based networks are reproducible across subjects, justifying their use for efficiency calculations.  

## Expected results  

We anticipate that higher global efficiency will correlate positively with fluid‑intelligence scores (r ≈ 0.2–0.3). Moreover, efficiency computed within a frontoparietal subgraph is expected to show a stronger association (r ≈ 0.35) and remain significant after controlling for age, sex, and head‑motion covariates. A failure to find these relationships would suggest that efficiency alone does not capture the neural substrate of fluid intelligence.  

## Methodology sketch  

- **Data acquisition**: Download the HCP 1200‑subject release (resting‑state fMRI and NIH Toolbox Fluid Intelligence scores) from https://db.humanconnectome.org.  
- **Preprocessing**: Use the minimally preprocessed HCP pipelines; apply additional nuisance regression (motion, WM/CSF) and band‑pass filter (0.01–0.1 Hz) with Nilearn.  
- **Node definition**: Parcellate each brain into 200 cortical ROIs using the Schaefer atlas (publicly available at https://github.com/ThomasYeoLab/CBIG).  
- **Functional connectivity**: Compute Pearson correlation matrices for each subject; retain only positive edges.  
- **Graph construction**: Threshold matrices at a proportional density (e.g., 20 %) to ensure comparable sparsity across subjects; convert to binary graphs with NetworkX.  
- **Efficiency metrics**: Calculate global efficiency and characteristic path length for each whole‑brain graph. Extract the frontoparietal subgraph (ROIs belonging to the Yeo‑7 “Frontoparietal” network) and compute subgraph efficiency.  
- **Statistical analysis**:  
  1. Perform Pearson/Spearman correlations between each efficiency metric and fluid‑intelligence scores.  
  2. Fit multiple linear regression models including age, sex, and mean framewise displacement as covariates.  
  3. Apply permutation testing (10 000 permutations) to obtain family‑wise corrected p‑values.  
- **Robustness checks**: Repeat analyses with alternative parcellations (e.g., 400‑ROI) and with weighted‑graph efficiency to verify stability.  
- **Reproducibility**: Package the entire workflow in a Snakemake pipeline; all scripts, environment file, and dataset URLs will be archived in the repository.  

## Duplicate-check  

- Reviewed existing ideas: *(none provided)*.  
- Closest match: *(no close match identified)*.  
- Verdict: **NOT a duplicate**.
