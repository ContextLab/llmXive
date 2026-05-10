---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Brain Network Dynamics and Creative Problem Solving

**Field**: neuroscience

## Research question

How does the dynamic reconfiguration of functional brain networks during rest predict individual differences in divergent thinking performance?

## Motivation

Understanding the neural basis of creative cognition has implications for education, innovation, and clinical assessment of cognitive flexibility. While static functional connectivity patterns have been linked to creative ability, less is known about whether network flexibility—the degree to which brain regions change their community allegiance over time—provides additional predictive power. This work addresses that gap by testing whether individuals with more adaptable resting-state networks exhibit superior performance on standardized divergent thinking tasks.

## Related work

- [Robust prediction of individual creative ability from brain functional connectivity (2018)](https://doi.org/10.1073/pnas.1713532115) — Establishes that static functional connectivity patterns between frontal and parietal regions can predict individual creative ability with moderate accuracy.
- [Neural Activity When People Solve Verbal Problems with Insight (2004)](https://doi.org/10.1371/journal.pbio.0020097) — Demonstrates that insight-based problem solving involves distinct neural activation patterns, providing precedent for linking neural measures to creative cognition.
- [Consistency of Regions of Interest as nodes of functional brain networks measured by fMRI (2017)](http://arxiv.org/abs/1704.07635v1) — Documents how ROI selection affects functional network construction, informing methodology for reproducible network metric computation.
- [Regions of Interest as nodes of dynamic functional brain networks (2017)](http://arxiv.org/abs/1710.04056v2) — Establishes that network properties depend critically on node definition, supporting careful ROI selection for dynamic connectivity analysis.

## Expected results

We expect to observe a positive correlation between resting-state network flexibility (measured as temporal variation in module allegiance) and divergent thinking scores, with effect sizes comparable to prior static connectivity work. A null result—no significant relationship after controlling for demographic variables and static connectivity—would indicate that dynamic reconfiguration adds no unique predictive value beyond established static patterns. Either outcome would be informative: confirmation would validate dynamic metrics as biomarkers of creative potential, while null findings would suggest static connectivity captures the relevant variance.

## Methodology sketch

- Download resting-state fMRI and behavioral data from the Human Connectome Project (HCP) public release (https://db.humanconnectome.org/)
- Preprocess fMRI data using standard pipeline (motion correction, normalization, band-pass filtering 0.01-0.1 Hz)
- Define ROIs using the HCP-MMP atlas (360 cortical regions)
- Compute sliding-window functional connectivity (window size: 30s, step: 5s)
- Apply community detection (Louvain algorithm) to each window to obtain module allegiance matrices
- Calculate network flexibility as the proportion of time each ROI changes community membership
- Extract divergent thinking scores from HCP behavioral assessments (Alternate Uses Task or equivalent)
- Fit linear regression model: creativity score ~ network flexibility + age + sex + education + static connectivity strength
- Perform 10,000 permutation tests to assess significance (shuffling creativity scores while preserving network structure)
- Generate diagnostic plots: scatter of flexibility vs. creativity, residual plots, and cross-validation performance

## Duplicate-check

- Reviewed existing ideas: None in current corpus.
- Closest match: None identified.
- Verdict: NOT a duplicate

**Note on scope**: The HCP dataset (N≈1000) and analyses described fit within 6-hour GHA job limits using Python (nilearn, networkx, scikit-learn). No GPU or HPC resources required; all data publicly available with direct download URLs.
