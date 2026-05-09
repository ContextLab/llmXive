---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Brain Network Dynamics and Anticipatory Reward Processing

**Field**: neuroscience

## Research question

How does the flexibility of resting-state functional brain networks relate to the magnitude of anticipatory reward responses in the ventral striatum?

## Motivation

Understanding whether trait-like network dynamics predict state-dependent reward processing could identify stable biomarkers for disorders characterized by reward deficits (e.g., depression, addiction). This addresses the gap between static connectivity models and the dynamic nature of brain function during motivation.

## Literature gap analysis

### What we searched

Queries included "resting state dynamic functional connectivity reward anticipation", "fMRI reward processing connectivity", and "dynamic brain networks controllability". Sources queried were Semantic Scholar and arXiv via the Lit-Search tool.

### What is known

- [Consistency of Regions of Interest as nodes of functional brain networks measured by fMRI (2017)](http://arxiv.org/abs/1704.07635v1) — Establishes the methodological foundation for defining functional networks using fMRI BOLD time series mapped to nodes.
- [Regions of Interest as nodes of dynamic functional brain networks (2017)](http://arxiv.org/abs/1710.04056v2) — Demonstrates that functional network properties depend heavily on how ROIs are chosen for dynamic connectivity analysis.
- [Uniqueness Analysis of Controllability Scores and Their Application to Brain Networks (2024)](http://arxiv.org/abs/2408.03023v4) — Provides theoretical context for assessing node importance and network controllability, relevant to defining network flexibility.

### What is NOT known

No published work in the search results directly measures the correlation between resting-state dynamic functional connectivity metrics and specific task-evoked anticipatory reward signals in the ventral striatum. Existing literature focuses on node definition methodology rather than the specific link between resting dynamics and reward motivation.

### Why this gap matters

Filling this gap would clarify if resting-state network flexibility serves as a predictive trait marker for reward sensitivity, enabling earlier identification of individuals at risk for reward-processing disorders without requiring task-specific scanning.

### How this project addresses the gap

This project directly correlates dynamic connectivity metrics derived from resting-state fMRI with BOLD signal changes during a reward anticipation task using the same subjects, providing empirical evidence for the relationship identified as unknown in the literature.

## Expected results

We expect to find a positive correlation between network flexibility (measured by state switching frequency in dynamic FC) and ventral striatum activation during reward cue anticipation. A null result would suggest resting-state dynamics are distinct from task-specific reward engagement, challenging the trait-marker hypothesis.

## Methodology sketch

- Download minimally preprocessed HCP resting-state and task-fMRI data for a subsample of N=50 subjects to fit 7GB RAM / 6h runtime constraints.
- Extract BOLD time series from a standard atlas (e.g., Power 264) to define network nodes.
- Compute dynamic functional connectivity using a sliding window approach on resting-state data to calculate flexibility metrics.
- Extract mean BOLD signal change in the ventral striatum ROI during reward cue epochs from the task-fMRI data.
- Perform Pearson correlation analysis between individual flexibility scores and reward activation magnitude.
- Apply permutation testing (1000 iterations) to establish statistical significance thresholds.

## Duplicate-check

- Reviewed existing ideas: None provided in corpus.
- Closest match: N/A.
- Verdict: NOT a duplicate
