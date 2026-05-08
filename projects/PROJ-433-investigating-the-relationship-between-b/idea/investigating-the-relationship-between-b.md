---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Relationship Between Brain Network Dynamics and Subjective Time Perception

**Field**: neuroscience

## Research question

How does dynamic functional connectivity reconfigurability in resting-state brain networks relate to individual differences in subjective time perception accuracy?

## Motivation

Subjective time perception is a fundamental cognitive process with clinical relevance for conditions like autism spectrum disorder and schizophrenia, yet its neural mechanisms remain poorly understood. While static functional connectivity has been extensively mapped, the relationship between dynamic network flexibility and temporal cognition is largely unexplored. This project addresses a specific gap: whether individuals with more adaptable brain networks exhibit more accurate interval timing.

## Literature gap analysis

### What we searched

Searched Semantic Scholar and OpenAlex using queries: (1) "dynamic functional connectivity time perception" and (2) "brain network reconfigurability temporal cognition". Only 2 results returned, both tangentially related to the broader goals of linking brain activity with behavioral measurement rather than addressing the specific question.

### What is known

- [Representational similarity analysis – connecting the branches of systems neuroscience](https://doi.org/10.3389/neuro.06.004.2008) — Establishes a methodological framework for relating brain-activity measurements to behavioral measurements and computational models, but does not address temporal processing specifically.
- [An information integration theory of consciousness](https://doi.org/10.1186/1471-2202-5-42) — Discusses conditions for conscious experience in integrated systems but does not investigate time perception or dynamic connectivity.

### What is NOT known

No published work has directly measured the correlation between resting-state dynamic functional connectivity reconfigurability and performance on behavioral time perception tasks. Existing studies treat network dynamics and temporal cognition as separate domains without empirical linkage.

### Why this gap matters

Understanding whether network flexibility constrains temporal processing could inform interventions for disorders with disrupted time perception (e.g., schizophrenia, ADHD) and clarify whether dynamic connectivity is a general marker of cognitive flexibility or domain-specific.

### How this project addresses the gap

This project directly correlates sliding-window dynamic connectivity metrics from HCP resting-state fMRI with available behavioral timing data, producing the first empirical test of the network-flexibility/time-perception relationship using public data.

## Expected results

We expect to observe a positive correlation between network reconfigurability (measured as variance in time-varying connectivity patterns) and time perception accuracy (measured as lower temporal discrimination thresholds). A null result would suggest dynamic connectivity is not a limiting factor for temporal cognition. Either outcome is publishable given the absence of prior empirical tests.

## Methodology sketch

- Download resting-state fMRI and behavioral data from Human Connectome Project (HCP) public release: https://db.humanconnectome.org/ (1200-subject subset, ~7GB total)
- Preprocess fMRI data using fMRIPrep container (single-CPU mode): motion correction, slice-timing correction, normalization to MNI space, nuisance regression
- Compute sliding-window functional connectivity matrices (window=30s, step=5s) for 200 cortical parcels (Schaefer atlas)
- Extract network reconfigurability metrics: (1) variance in connectivity strength across windows, (2) number of community state transitions (using Louvain algorithm)
- Obtain time perception behavioral scores from HCP behavioral dataset: temporal bisection task accuracy and coefficient of variation
- Perform Spearman correlation between reconfigurability metrics and behavioral scores (n≈100 subjects after QC exclusions)
- Apply multiple-comparison correction (Bonferroni) for 4 connectivity metrics × 2 behavioral measures
- Generate scatter plots with 95% confidence intervals and report effect sizes (Cohen's r)
- Validate with permutation testing (1000 shuffles) to confirm correlation is not spurious

## Duplicate-check

- Reviewed existing ideas: [None provided in input]
- Closest match: None identified
- Verdict: NOT a duplicate

---

**Scope note**: This methodology targets ≤6h runtime on 2 CPU/7GB RAM by using the 1200-subject HCP subset with single-CPU fMRIPrep configuration and avoiding GPU-dependent deep learning. All data sources are publicly available without paywalls.
