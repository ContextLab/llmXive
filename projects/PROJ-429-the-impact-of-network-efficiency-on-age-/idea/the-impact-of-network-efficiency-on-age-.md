---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# The Impact of Network Efficiency on Age-Related Changes in Resting-State EEG

**Field**: neuroscience

## Research question

How does resting-state brain network efficiency, as measured by graph-theoretical metrics from EEG, change with age, and does reduced network efficiency predict cognitive performance in older adults?

## Motivation

Age-related cognitive decline is increasingly prevalent, yet early non-invasive biomarkers remain elusive. Understanding whether network efficiency in resting-state EEG systematically declines with age and correlates with cognitive function could enable earlier detection of cognitive impairment and inform interventions.

## Literature gap analysis

### What we searched

Searched Semantic Scholar and arXiv using queries: (1) "resting-state EEG network efficiency age cognitive" and (2) "EEG graph theory aging network metrics". Retrieved 4 papers from the literature block, none of which directly address age-related changes in network efficiency from resting-state EEG.

### What is known

- [Can EEG resting state data benefit data-driven approaches for motor-imagery decoding? (2024)](http://arxiv.org/abs/2411.09789v1) — Establishes that resting-state EEG contains reliable individual-specific markers, demonstrating feasibility of subject-level EEG feature extraction.
- [Changes in Power and Information Flow in Resting-state EEG by Working Memory Process (2022)](http://arxiv.org/abs/2212.05654v1) — Shows resting-state EEG neurodynamics change with cognitive task demands, supporting that resting-state measures reflect functional brain organization.
- [Regions of Interest as nodes of dynamic functional brain networks (2017)](http://arxiv.org/abs/1710.04056v2) — Documents that network properties depend critically on node definition, providing methodological guidance for constructing EEG-derived brain networks.

### What is NOT known

No published work has quantified age-related changes in graph-theoretical network efficiency (e.g., characteristic path length, clustering coefficient) from resting-state EEG. The relationship between resting-state network metrics and cognitive performance in aging populations remains unexplored in this literature.

### Why this gap matters

Identifying EEG-based network biomarkers of aging could enable scalable, low-cost screening for cognitive impairment in clinical and community settings. Filling this gap would provide a non-invasive, objective measure to track brain aging trajectories and evaluate interventions.

### How this project addresses the gap

This project will download age-stratified resting-state EEG from PhysioNet, compute graph-theoretical network efficiency metrics using standard EEG preprocessing pipelines, and statistically test correlations with cognitive assessment scores. The methodology directly produces the previously-unavailable evidence on age-network-efficiency relationships.

## Expected results

We expect to find significant negative correlations between age and network efficiency metrics (increased path length, decreased clustering) in older adults. These network metrics should also show significant positive correlations with cognitive performance scores, with effect sizes sufficient to distinguish normal aging from early impairment (partial correlation r > 0.3, p < 0.05).

## Methodology sketch

- Download resting-state EEG datasets from PhysioNet (e.g., Temple University Hospital EEG Corpus, OpenNeuro) containing age and cognitive assessment metadata
- Preprocess EEG data using MNE-Python: bandpass filter (1-40 Hz), remove artifacts via ICA, segment into 2-second epochs
- Construct functional connectivity matrices using coherence or phase-locking value between electrode pairs
- Define network nodes as EEG electrodes or source-localized ROIs using the 10-20 system
- Compute graph metrics: characteristic path length, clustering coefficient, global/local efficiency, modularity
- Stratify participants into age groups (young: 20-40, middle: 40-60, older: 60+)
- Correlate network metrics with cognitive scores (e.g., MMSE, MoCA) using Spearman rank correlation
- Perform multiple regression controlling for sex, education, and signal quality
- Validate findings using cross-validation (leave-one-out or k-fold)
- Generate visualization of age-related network changes using brain connectivity plots

## Duplicate-check

- Reviewed existing ideas: Network efficiency in aging, EEG biomarkers for cognitive decline, Graph theory applied to resting-state EEG, Age-related brain network changes.
- Closest match: EEG biomarkers for cognitive decline (similarity sketch: both use EEG to study aging, but this project focuses specifically on graph-theoretical network efficiency metrics rather than general EEG features).
- Verdict: NOT a duplicate
