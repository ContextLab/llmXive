# Research Plan

## Objective
To investigate the relationship between resting-state brain network topology and susceptibility to visual illusions (Müller-Lyer and Ponzo).

## Hypothesis
Individuals with higher global efficiency and lower path length in visual and frontoparietal networks will exhibit lower susceptibility to visual illusions.

## Methodology
1. **Data Source**: OpenNeuro ds004285 (resting-state fMRI + behavioral data).
2. **Preprocessing**: fMRIPrep for motion correction, normalization, and smoothing.
3. **Time Series Extraction**: Schaefer parcellation (200 ROIs).
4. **Connectivity**: Pearson correlation matrices.
5. **Topology Metrics**: Modularity, path length, clustering, efficiency, small-worldness (using BCTPy).
6. **Analysis**: Pearson/Spearman correlations with FDR correction.

## Expected Outcomes
- Identification of significant correlations between specific network metrics and illusion susceptibility.
- A reproducible pipeline for network-behavior analysis.

## Limitations
- Associational nature of findings.
- Reliance on existing data (limited control over stimulus parameters).
- Exclusion of high-motion subjects.
