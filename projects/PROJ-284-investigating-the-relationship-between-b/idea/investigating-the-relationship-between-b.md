---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Brain Network Dynamics and Individual Differences in Proprioceptive Accuracy

**Field**: neuroscience

## Research question

Can resting-state functional connectivity patterns in sensorimotor networks predict individual variations in proprioceptive acuity? Specifically, do measures of network integration and modularity correlate with joint position sense performance across healthy adults?

## Motivation

Proprioception is fundamental for motor control and body awareness, yet its neural basis remains incompletely understood. Identifying structural or functional biomarkers could inform rehabilitation strategies for conditions affecting body awareness (e.g., stroke, cerebellar degeneration). Public neuroimaging datasets now provide sufficient resting-state fMRI data to explore this without new data collection.

## Related work

- TODO — lit-search returned no directly relevant results. The provided search result concerns fNIRS-based brain-computer interfaces and does not address resting-state connectivity or proprioception specifically.

## Expected results

We expect to find positive correlations between sensorimotor network integration (e.g., participation coefficient) and proprioceptive accuracy scores. If no significant relationships emerge, this would suggest proprioceptive individual differences arise from factors not captured by resting-state connectivity alone. Evidence threshold: correlation coefficients >0.3 with p<0.05 after multiple-comparison correction.

## Methodology sketch

- Download resting-state fMRI data from Human Connectome Project (HCP) S1200 release via HCP API (https://db.humanconnectome.org)
- Filter for participants with available proprioceptive or sensorimotor behavioral measures (or use HCP's existing task data as proxy)
- Preprocess fMRI data using FSL FEAT or AFNI (standard pipeline: motion correction, slice-time correction, normalization, smoothing)
- Construct brain parcellation using AAL or Schaefer atlas (200–400 regions)
- Compute functional connectivity matrices (Pearson correlation between region time series)
- Extract graph-theoretic metrics: modularity, global efficiency, participation coefficient, within-module degree
- Obtain proprioceptive performance data from HCP behavioral database or supplement from OpenNeuro (search "proprioception" or "joint position")
- Perform Spearman or Pearson correlation between network metrics and proprioceptive accuracy scores
- Apply Bonferroni or FDR correction for multiple comparisons across network measures
- Visualize significant correlations with scatter plots and network diagrams (using Python: matplotlib, seaborn, networkx)

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: N/A
- Verdict: NOT a duplicate
