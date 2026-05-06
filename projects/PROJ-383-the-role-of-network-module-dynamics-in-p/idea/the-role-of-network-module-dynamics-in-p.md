---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# The Role of Network Module Dynamics in Predicting Individual Differences in Working Memory Capacity

**Field**: neuroscience

## Research question

To what extent does the temporal flexibility of resting-state functional network modules predict individual variation in working memory capacity?

## Motivation

Static functional connectivity patterns explain a portion of variance in cognitive performance, but the brain operates as a dynamic system that reconfigures its network architecture over time. If the ability to flexibly reorganize network modules during rest reflects a cognitive reserve mechanism, it could provide a more sensitive biomarker for working memory capacity than static connectivity alone. This project addresses the gap between theoretical network flexibility and empirical individual differences in human cognition.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and OpenAlex using terms such as "dynamic functional connectivity working memory", "network module flexibility cognition", and "resting state reorganization individual differences". We retrieved 7 results, but most focused on static connectivity, theoretical network models, or task-based activation rather than dynamic module reconfiguration metrics in resting-state fMRI.

### What is known

- [The Cognitive Neuroscience of Working Memory (2014)](https://doi.org/10.1146/annurev-psych-010814-015031) — Establishes the foundational link between working memory capacity and neural coordination mechanisms, though primarily focusing on static or task-evoked activity.
- [Dissociable Intrinsic Connectivity Networks for Salience Processing and Executive Control (2007)](https://doi.org/10.1523/jneurosci.5587-06.2007) — Demonstrates that task-free connectivity can isolate individual differences in executive control networks, supporting the use of resting-state data for cognitive phenotyping.
- [Cross-Frequency Coupling Increases Memory Capacity in Oscillatory Neural Networks (2022)](http://arxiv.org/abs/2204.07163v1) — Provides theoretical evidence that network dynamics (specifically oscillatory coupling) constrain memory capacity, suggesting dynamic properties are mechanistically relevant.

### What is NOT known

There is no published work that directly quantifies the *temporal flexibility* of community structure (e.g., node switching probability) in *resting-state* fMRI and correlates it with *individual working memory capacity scores* in a healthy adult cohort. Existing dynamic connectivity studies often focus on clinical populations or task-based states rather than resting-state individual differences.

### Why this gap matters

Filling this gap would clarify whether the brain's intrinsic capacity to reconfigure networks is a trait-like predictor of cognitive performance. This could inform models of cognitive reserve and guide interventions aimed at enhancing network flexibility to improve memory function.

### How this project addresses the gap

This project will compute sliding-window community detection on resting-state fMRI time series to derive a flexibility metric, then correlate this metric with standardized working memory scores. This directly operationalizes the "dynamic flexibility" concept missing from the static literature to test its predictive power for individual capacity.

## Expected results

We expect to find a positive correlation between network module flexibility and working memory capacity, indicating that individuals with more adaptable resting-state networks perform better on memory tasks. A null result would suggest that static connectivity or other dynamic features (e.g., integration time) are more relevant, which would still refine theoretical models of cognitive control.

## Methodology sketch

- Download resting-state fMRI preprocessed time series for a subset of 100 subjects from the Human Connectome Project (OpenNeuro dataset ds000224) to ensure fit within 7GB RAM.
- Download corresponding working memory task behavioral scores (2-back accuracy) from the same HCP release metadata.
- Compute time-varying functional connectivity matrices using a sliding window approach (window length = 60s, step = 10s) with Pearson correlation.
- Apply the Louvain community detection algorithm to each windowed connectivity matrix to identify network modules.
- Calculate the "flexibility" metric for each node (probability of changing community assignment across windows) and average across the whole brain.
- Perform a Pearson correlation test between the whole-brain flexibility metric and individual working memory scores.
- Validate significance using a non-parametric permutation test (1,000 permutations) to control for multiple comparisons and motion artifacts.

## Duplicate-check

- Reviewed existing ideas: None.
- Closest match: None (similarity sketch: N/A).
- Verdict: NOT a duplicate
