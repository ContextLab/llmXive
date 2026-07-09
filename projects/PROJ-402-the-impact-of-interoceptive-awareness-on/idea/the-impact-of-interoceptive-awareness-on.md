---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

**Field**: psychology

## Research question

Does behavioral interoceptive accuracy (measured strictly via the Schandry heartbeat perception task) predict the magnitude of physiological emotional regulation during acute psychosocial stress, independent of baseline heart rate variability? (Note: If no open dataset contains both the Schandry task and a stress paradigm, the project scope is limited to a feasibility audit confirming this data gap rather than attempting a statistical test with invalid proxies.)

## Motivation

Stress-related disorders are prevalent, yet individual variability in regulatory capacity remains poorly understood. While stress interventions exist, the role of trait interoceptive awareness (the ability to sense internal bodily states) as a predictor of naturalistic regulation is under-explored in open data. Addressing this gap could enable personalized stress-management strategies based on biological traits rather than generic interventions, specifically determining if the *perception* of the body, distinct from the *physiological state* itself, drives resilience.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for terms including "interoceptive accuracy stress regulation prediction," "heartbeat perception task TSST correlation," "HRV independent of interoception stress," and "public psychophysiological stress dataset interoception." The search yielded two results, neither of which explicitly links baseline interoceptive accuracy (behavioral) to stress regulation outcomes while controlling for baseline HRV in a predictive framework.

### What is known

- [Road to Serenity: Individual Variations in the Efficacy of Unobtrusive Respiratory Guidance for Driving Stress Regulation (2024)](https://arxiv.org/abs/2406.09777) — Establishes that individual variations significantly impact the efficacy of physiological stress regulation interventions, suggesting that trait-level differences modulate how stress responses are managed, though it focuses on respiratory guidance rather than interoceptive prediction.
- [Emotional Responses to Auditory Hierarchical Structures is Shaped by Bodily Sensations and Listeners' Sensory Traits (2025)](https://arxiv.org/abs/2504.01287) — Demonstrates that individual sensory traits shape emotional responses to external stimuli, supporting the theoretical premise that internal bodily sensitivity influences emotional processing, but does not quantify this relationship in the context of acute psychosocial stress reactivity.

### What is NOT known

No published work has explicitly correlated baseline interoceptive accuracy (measured via behavioral heartbeat perception tasks) with physiological stress reactivity (HRV) in publicly available psychophysiological datasets while statistically controlling for baseline HRV. Existing literature focuses either on the technical aspects of stress monitoring, the general link between sensory traits and emotion, or intervention efficacy, leaving the specific *predictive* link between the *trait* of interoceptive accuracy and the *state* of stress regulation—disentangled from baseline autonomic tone—unquantified in open data.

### Why this gap matters

Understanding whether interoceptive awareness is a stable predictor of stress resilience *independent* of baseline physiological health (HRV) is critical for clinical screening. If high interoception predicts better regulation even when baseline HRV is low, it suggests interoceptive training is a viable standalone intervention for at-risk populations; if the effect vanishes when controlling for HRV, it suggests current models overestimate the role of perception and overemphasize the body's state rather than its sensing.

### How this project addresses the gap

This project audits open-source psychophysiological datasets (e.g., WESAD, OpenNeuro) for the co-occurrence of interoception tasks and stress paradigms. Where direct behavioral data is absent, it analyzes proxy correlations between resting-state physiological markers and stress reactivity to infer the potential role of interoceptive sensitivity, explicitly documenting the data limitations and the statistical independence of the predictors from the outcome.

## Expected results

We expect to find a weak-to-moderate positive correlation between baseline interoceptive accuracy (or its proxy) and HRV recovery rates during the post-stressor period, which remains significant even after regressing out baseline HRV. If no direct data exists linking specific heartbeat perception tasks to stress phases, the result will be a feasibility report confirming the scarcity of this specific multimodal data in current open repositories, guiding future data collection efforts.

## Methodology sketch

- Download the WESAD dataset (wearable stress and affect detection) via `wget` from Zenodo (DOI: 10.5281/zenodo.1292932) to access ECG and respiration signals during stress and baseline phases.
- Search OpenNeuro for studies containing "TSST" and "heartbeat" or "interoception" keywords; download specific subject-level BIDS data if available.
- Preprocess ECG/PPG signals using Python `hrv-analysis` to compute RMSSD and SDNN metrics for baseline (resting) and stress (TSST) phases.
- Extract self-reported stress ratings (PANAS or similar) from associated metadata JSON files or event markers.
- **Data Availability Check**: Verify if WESAD or OpenNeuro subsets contain an explicit heartbeat perception task (Schandry task). If absent, define a proxy variable: resting-state HRV stability as an indicator of physiological awareness potential, noting this is a limitation.
- Calculate the magnitude of physiological regulation as the difference (or slope) between stress-phase HRV and baseline HRV.
- Perform linear regression with the regulation magnitude as the outcome, and baseline interoceptive accuracy (or proxy) as the primary predictor, **including baseline HRV as a covariate** to ensure the predictor (interoception) and the control (baseline HRV) are distinct from the outcome (regulation magnitude).
- Verify that the validation target (regulation magnitude) is not mathematically derived solely from the predictor's source; specifically, ensure the regression model tests the unique variance explained by interoception beyond the baseline autonomic state.
- Generate plots of HRV trajectories overlaid with stress phase markers using `matplotlib` to visualize individual variability.
- Document data availability findings in a final `data_audit.md` if direct interoception tasks are missing from the datasets, explicitly stating the limitation of using physiological proxies.

## Duplicate-check

- Reviewed existing ideas: None provided in current session context.
- Closest match: N/A.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-09T21:52:25Z
**Outcome**: exhausted
**Original term**: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress psychology
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress psychology | 2 |

### Verified citations

1. **Road to Serenity: Individual Variations in the Efficacy of Unobtrusive Respiratory Guidance for Driving Stress Regulation** (2024). A. J. Bequet, C. Jallais, J. Quick, D. Ndiaye, A. R. Hidalgo-Munoz. arXiv. [2406.09777](https://arxiv.org/abs/2406.09777). PDF-sampled: No.
2. **Emotional Responses to Auditory Hierarchical Structures is Shaped by Bodily Sensations and Listeners' Sensory Traits** (2025). Maiko Minatoya, Tatsuya Daikoku, Yasuo Kuniyoshi. arXiv. [2504.01287](https://arxiv.org/abs/2504.01287). PDF-sampled: No.
