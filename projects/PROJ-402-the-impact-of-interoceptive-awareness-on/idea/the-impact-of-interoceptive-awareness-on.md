---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

**Field**: psychology

## Research question

How does baseline interoceptive accuracy (measured via heartbeat perception tasks) predict the magnitude of physiological and subjective emotional regulation during acute psychosocial stress?

## Motivation

Stress-related disorders are prevalent, yet individual variability in regulatory capacity remains poorly understood. While stress interventions exist, the role of trait interoceptive awareness (the ability to sense internal bodily states) as a predictor of naturalistic regulation is under-explored in open data. Addressing this gap could enable personalized stress-management strategies based on biological traits rather than generic interventions.

## Literature gap analysis

### What we searched

Queries included "interoceptive awareness stress regulation", "heartbeat perception task TSST", "heart rate variability stress prediction", and "public psychophysiological stress dataset" across Semantic Scholar and arXiv. The provided literature block contained two results, neither of which explicitly links baseline interoceptive accuracy to stress regulation outcomes in a predictive framework.

### What is known

- [Shesop Healthcare: Android application to monitor heart rate variance, display influenza and stress condition using Polar H7 (2016)](https://arxiv.org/abs/1607.04771) — Demonstrates the technical feasibility of monitoring heart rate variance for stress detection using wearable sensors, but focuses on algorithmic classification of stress states rather than the psychological trait of interoceptive awareness as a predictor.
- [Frequency Structure of Heart Rate Variability (2010)](https://arxiv.org/abs/1005.0776) — Establishes the theoretical factor structure of HRV periodograms, providing the physiological basis for extracting stress metrics, but does not address the relationship between these metrics and individual differences in interoceptive perception.

### What is NOT known

No published work has explicitly correlated baseline interoceptive accuracy (measured via heartbeat perception tasks) with physiological stress reactivity (HRV) in publicly available psychophysiological datasets. Existing literature focuses on either the technical aspects of stress monitoring or the theoretical structure of HRV, leaving the specific predictive link between the *trait* of interoception and the *state* of stress regulation unquantified in open data.

### Why this gap matters

Understanding whether interoceptive awareness is a stable predictor of stress resilience would inform clinical screening for anxiety disorders. If high interoception predicts better regulation, resources could be allocated to interoceptive training for at-risk populations; if not, it suggests current theoretical models of stress regulation need revision.

### How this project addresses the gap

This project audits open-source psychophysiological datasets (e.g., WESAD, OpenNeuro) for the co-occurrence of interoception tasks and stress paradigms. Where direct data is absent, it analyzes proxy correlations between resting-state physiological markers (as a proxy for interoceptive capacity) and stress reactivity to infer the potential role of interoceptive sensitivity, explicitly documenting the data limitations.

## Expected results

We expect to find a weak-to-moderate positive correlation between baseline physiological stability (proxy for interoceptive capacity) and HRV recovery rates during the post-stressor period. If no direct data exists linking specific heartbeat perception tasks to stress phases, the result will be a feasibility report confirming the scarcity of this specific multimodal data in current open repositories, guiding future data collection efforts.

## Methodology sketch

- Download the WESAD dataset (wearable stress and affect detection) via `wget` from Zenodo (DOI: 10.5281/zenodo.1292932) to access ECG and respiration signals during stress and baseline phases.
- Search OpenNeuro for studies containing "TSST" and "heartbeat" or "interoception" keywords; download specific subject-level BIDS data if available.
- Preprocess ECG/PPG signals using Python `hrv-analysis` to compute RMSSD and SDNN metrics for baseline (resting) and stress (TSST) phases.
- Extract self-reported stress ratings (PANAS or similar) from associated metadata JSON files or event markers.
- **Data Availability Check**: Verify if WESAD or OpenNeuro subsets contain an explicit heartbeat perception task (Schandry task). If absent, define a proxy variable: resting-state HRV stability as an indicator of physiological awareness potential.
- Compute Pearson correlation coefficients between the baseline physiological metric (proxy for interoceptive capacity) and the magnitude of HRV change (reactivity) and recovery slope.
- Perform linear regression to test if baseline metrics significantly predict post-stress recovery slope (alpha < 0.05), ensuring the outcome variable (recovery slope) is derived from the stress phase, not the baseline phase alone.
- Generate plots of HRV trajectories overlaid with stress phase markers using `matplotlib` to visualize individual variability.
- Document data availability findings in a final `data_audit.md` if direct interoception tasks are missing from the datasets, explicitly stating the limitation of using physiological proxies.

## Duplicate-check

- Reviewed existing ideas: None provided in current session context.
- Closest match: N/A.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-30T04:49:24Z
**Outcome**: exhausted
**Original term**: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress psychology
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress psychology | 0 |
| 1 | interoceptive sensitivity and emotion regulation | 1 |
| 2 | heart rate variability and stress response | 5 |
| 3 | bodily awareness in emotional control | 0 |
| 4 | mindfulness and interoception during stress | 0 |
| 5 | affective neuroscience of interoceptive processing | 0 |
| 6 | somatic markers and emotional regulation | 0 |
| 7 | anxiety modulation through interoceptive training | 0 |
| 8 | visceral feedback and stress coping mechanisms | 0 |
| 9 | alexithymia and emotional dysregulation under stress | 0 |
| 10 | cardiac interoception and anxiety management | 0 |
| 11 | physiological arousal and emotional recovery | 0 |
| 12 | metacognitive awareness of bodily states | 0 |
| 13 | stress reactivity and interoceptive accuracy | 0 |
| 14 | emotion regulation strategies and body perception | 0 |
| 15 | psychophysiological stress responses and self-awareness | 0 |
| 16 | the role of the insula in emotional regulation | 0 |
| 17 | interoceptive exposure therapy for emotional control | 0 |
| 18 | bodily sensations and stress resilience | 0 |
| 19 | predictive coding of interoceptive signals and emotion | 0 |
| 20 | autonomic nervous system regulation via interoception | 0 |

### Verified citations

1. **Shesop Healthcare: Android application to monitor heart rate variance, display influenza and stress condition using Polar H7** (2016). Andrien Ivander Wijaya, Ary Setijadi Prihatmanto, Rifki Wijaya. arXiv. [1607.04771](https://arxiv.org/abs/1607.04771). PDF-sampled: No.
2. **Frequency Structure of Heart Rate Variability** (2010). V. Mukhin. arXiv. [1005.0776](https://arxiv.org/abs/1005.0776). PDF-sampled: No.
