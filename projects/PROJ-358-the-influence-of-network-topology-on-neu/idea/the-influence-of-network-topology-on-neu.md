---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# The Influence of Network Topology on Neural Synchrony During Cognitive Tasks

**Field**: neuroscience

## Research question

How does the baseline topological organization of resting-state brain networks relate to the degree of neural synchrony exhibited during working memory task performance?

## Motivation

Understanding whether individual differences in baseline brain network architecture predict dynamic neural communication during cognitive tasks could reveal mechanistic links between brain organization and cognitive function. This addresses a gap in the literature where network topology and neural synchrony have been studied separately, but their interrelationship across resting and task states remains underexplored.

## Related work

- [The Role of Oscillations and Synchrony in Cortical Networks and Their Putative Relevance for the Pathophysiology of Schizophrenia](https://doi.org/10.1093/schbul/sbn062) — Establishes that neural oscillations and synchronization represent a versatile signal for flexible communication within and between cortical areas.
- [Graph theoretical analysis of complex networks in the brain](https://doi.org/10.1186/1753-4631-1-3) — Foundational work demonstrating small-world and scale-free properties of brain networks from a network perspective.
- [Is the ADHD brain wired differently? A review on structural and functional connectivity in attention deficit hyperactivity disorder](https://doi.org/10.1002/hbm.21058) — Reviews connectivity differences in neuropsychiatric disorders, supporting the premise that network properties relate to cognitive function.

## Expected results

We expect to observe a significant positive correlation between resting-state network efficiency (e.g., shorter characteristic path length, higher clustering coefficient) and task-based neural synchrony metrics. Either finding—significant correlation or null result—would be informative: the former would suggest baseline architecture constrains dynamic communication, while the latter would indicate task-state synchrony is more state-dependent than trait-dependent.

## Methodology sketch

- Download publicly available resting-state and task-based fMRI data from the Human Connectome Project (HCP) via their API (N≈100 subjects for feasibility within 6h compute budget)
- Preprocess fMRI data: motion correction, spatial normalization to MNI space, temporal filtering (0.01-0.1 Hz), and nuisance regression
- Parcellate brains into 200 regions using a standard atlas (e.g., Schaefer 200) and extract time-series for each region
- Compute resting-state functional connectivity matrix (Pearson correlation between all region pairs)
- Calculate graph-theoretical metrics from resting-state connectivity: clustering coefficient, characteristic path length, global efficiency
- For task-based fMRI data, compute neural synchrony using phase-locking value (PLV) between region pairs during working memory task epochs
- Aggregate synchrony metrics across task-relevant networks (e.g., frontoparietal, default mode)
- Perform Pearson correlation analysis between resting-state topology metrics and task-based synchrony metrics across subjects
- Apply multiple-comparison correction (Bonferroni or FDR) for the number of graph metrics tested
- Generate scatter plots with regression lines showing topology-synchrony relationships with 95% confidence intervals

## Duplicate-check

- Reviewed existing ideas: None available in corpus for this analysis.
- Closest match: None identified.
- Verdict: NOT a duplicate
