---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages

**Field**: neuroscience

## Research question

Does the intrinsic network centrality architecture of the waking brain predict the degree of neural synchrony observed across different sleep stages? This question distinguishes between two independent data sources: centrality derived from resting-state functional connectivity measured during wakefulness, and synchrony metrics computed from electrophysiological recordings during sleep.

## Motivation

Sleep is critical for cognitive restoration and memory consolidation, yet the relationship between an individual's baseline network architecture and sleep-stage dynamics remains unclear. Understanding whether waking network topology constrains or enables specific patterns of neural synchrony during sleep would clarify how the brain's structural-functional organization supports sleep-dependent processes.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using combinations of: "network centrality sleep", "neural synchrony sleep stages", "functional connectivity sleep fMRI", and "centrality metrics neural synchrony". We also broadened to "sleep stage classification" and "sleep EEG connectivity" to capture methodological precedents. The literature returned primarily sleep staging classification papers and conceptual synchrony reviews, with no studies directly addressing the centrality-synchrony relationship across sleep stages.

### What is known

- [Neural synchrony in cortical networks: history, concept and current status (2009)](https://doi.org/10.3389/neuro.07.017.2009) — Establishes the conceptual framework for neural synchrony in cortical networks but does not address sleep-stage specificity or centrality relationships.
- [Replay and Time Compression of Recurring Spike Sequences in the Hippocampus (1999)](https://doi.org/10.1523/jneurosci.19-21-09497.1999) — Documents spike sequence coordination during slow-wave sleep in rats, providing evidence that sleep-stage-specific synchrony exists but not how it relates to network centrality.

### What is NOT known

No published work has quantified the relationship between resting-state network centrality metrics and neural synchrony measures across human sleep stages (N1, N2, N3, REM). Specifically, there is no evidence on whether individuals with higher hub centrality in default mode or frontoparietal networks exhibit distinct synchrony patterns during slow-wave versus REM sleep.

### Why this gap matters

Filling this gap would clarify whether sleep-stage dynamics are constrained by stable individual differences in network architecture, which has implications for understanding sleep disorders and individual variability in sleep-dependent cognitive benefits. If centrality predicts synchrony, it could identify biomarkers for sleep-related cognitive dysfunction.

### How this project addresses the gap

We will download publicly available sleep EEG/fMRI datasets, compute centrality from waking resting-state connectivity, extract synchrony metrics from sleep-stage epochs, and test for cross-sleep-stage correlations. This directly produces the previously-unavailable evidence linking network topology to sleep-stage synchrony.

## Expected results

We expect to find that individuals with higher eigenvector centrality in frontoparietal networks exhibit stronger phase-locking during N3 slow-wave sleep compared to REM sleep. A null result (no correlation) would be equally informative, suggesting sleep-stage dynamics are independent of baseline network architecture. We require at least n=30 subjects with complete waking and sleep recordings to achieve statistical power for detecting medium-effect correlations.

## Methodology sketch

- Download Sleep-EDF dataset (PhysioNet: https://physionet.org/content/sleep-edfx/1.0.0/) containing both waking resting-state and sleep-stage EEG recordings.
- Preprocess EEG data: bandpass filter (0.5–45 Hz), remove artifacts using ICA, segment into 30-second epochs by sleep stage.
- Construct functional connectivity matrices from waking resting-state data using coherence in theta and alpha bands.
- Compute centrality metrics (degree, betweenness, eigenvector) for each node using NetworkX on the connectivity matrices.
- Calculate neural synchrony for each sleep stage using phase-locking value (PLV) across electrode pairs.
- Perform Pearson correlation between centrality metrics and synchrony scores, stratified by sleep stage (Wake, N1, N2, N3, REM).
- Apply Bonferroni correction for multiple comparisons across centrality measures and sleep stages.
- Validate findings using a second dataset (SHHS: https://www.ncbi.nlm.nih.gov/projects/gap/cgi-bin/study.cgi?studyId=shhs1) if available.

## Duplicate-check

- Reviewed existing ideas: [Investigating the Impact of Network Centrality on Neural Synchrony During Sleep Stages].
- Closest match: None found in current corpus.
- Verdict: NOT a duplicate
