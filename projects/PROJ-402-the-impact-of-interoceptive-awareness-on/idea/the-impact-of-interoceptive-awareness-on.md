---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

**Field**: psychology

## Research question

How does baseline interoceptive accuracy predict the magnitude of physiological and subjective emotional regulation during acute psychosocial stress?

## Motivation

Stress-related disorders are prevalent, yet individual variability in regulatory capacity remains poorly understood. While stress interventions exist, the role of trait interoceptive awareness (the ability to sense internal bodily states) as a predictor of naturalistic regulation is under-explored in open data. Addressing this gap could enable personalized stress-management strategies based on biological traits rather than generic interventions.

## Literature gap analysis

### What we searched

Queries included "interoceptive awareness stress regulation", "heartbeat perception task TSST", and "physiological stress prediction public dataset" across Semantic Scholar and arXiv. The provided literature block contained three results, only one of which was tangentially related to stress regulation mechanisms.

### What is known

- [Road to Serenity: Individual Variations in the Efficacy of Unobtrusive Respiratory Guidance for Driving Stress Regulation (2024)](http://arxiv.org/abs/2406.09777v1) — Establishes that physiological interventions (respiratory guidance) can modulate stress responses, but focuses on external regulation aids rather than internal trait-based prediction.

### What is NOT known

No published work has explicitly correlated baseline interoceptive accuracy (measured via heartbeat perception tasks) with physiological stress reactivity (HRV) in publicly available psychophysiological datasets. Existing stress literature focuses on interventions or subjective self-report without linking to the specific trait of interoceptive sensitivity.

### Why this gap matters

Understanding whether interoceptive awareness is a stable predictor of stress resilience would inform clinical screening for anxiety disorders. If high interoception predicts better regulation, resources could be allocated to interoceptive training for at-risk populations.

### How this project addresses the gap

This project audits open-source psychophysiological datasets (e.g., OpenNeuro, WESAD) for the co-occurrence of interoception tasks and stress paradigms. Where direct data is absent, it analyzes proxy correlations between resting-state physiological markers and stress reactivity to infer the potential role of interoceptive sensitivity.

## Expected results

We expect to find a weak-to-moderate positive correlation between baseline interoceptive accuracy and HRV recovery rates during the post-stressor period. If no direct data exists, the result will be a feasibility report confirming the scarcity of this specific multimodal data in current open repositories, guiding future data collection efforts.

## Methodology sketch

- Download the WESAD dataset (wearable stress and affect detection) via `wget` from Zenodo (DOI: 10.5281/zenodo.1292932) to assess physiological stress markers.
- Search OpenNeuro for studies containing "TSST" and "heartbeat" or "interoception" keywords; download specific subject-level BIDS data if available.
- Preprocess ECG/PPG signals using Python `hrv-analysis` to compute RMSSD and SDNN metrics for baseline and stress phases.
- Extract self-reported stress ratings (PANAS or similar) from associated metadata JSON files.
- Compute Pearson correlation coefficients between baseline physiological stability (proxy for interoceptive capacity) and stress reactivity (change in HRV).
- Perform linear regression to test if baseline metrics significantly predict post-stress recovery slope (alpha < 0.05).
- Generate plots of HRV trajectories overlaid with stress phase markers using `matplotlib`.
- Document data availability findings in a final `data_audit.md` if direct interoception tasks are missing from the datasets.

## Duplicate-check

- Reviewed existing ideas: None provided in current session context.
- Closest match: N/A.
- Verdict: NOT a duplicate.
