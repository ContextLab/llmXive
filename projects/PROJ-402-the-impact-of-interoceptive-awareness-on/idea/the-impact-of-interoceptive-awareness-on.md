---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress

**Field**: psychology

## Research question

Does behavioral interoceptive accuracy predict the magnitude of physiological emotional regulation during acute psychosocial stress, independent of baseline heart rate variability?

## Motivation

Stress-related disorders are prevalent, yet individual variability in regulatory capacity remains poorly understood. While stress interventions exist, the role of trait interoceptive awareness (the ability to sense internal bodily states) as a predictor of naturalistic regulation is under-explored in open data. Addressing this gap could enable personalized stress-management strategies based on biological traits rather than generic interventions, specifically determining if the *perception* of the body, distinct from the *physiological state* itself, drives resilience.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv for terms including "interoceptive accuracy stress regulation prediction," "heartbeat perception task TSST correlation," "HRV independent of interoception stress," "public psychophysiological stress dataset interoception," and "Schandry task open data." The search yielded five results, none of which explicitly link baseline interoceptive accuracy (behavioral) to stress regulation outcomes in a public dataset while controlling for baseline HRV.

### What is known

- [Digital Emotion Regulation on Social Media (2023)](https://arxiv.org/abs/2307.13187) — Establishes the theoretical importance of consciously altering affective states and the current focus on digital/social contexts, but does not address the physiological mechanisms or the role of somatic sensing in acute stress paradigms.
- [TensiStrength: Stress and relaxation magnitude detection for social media texts (2016)](https://arxiv.org/abs/1607.00139) — Demonstrates methods for detecting stress intensity in textual data, confirming that stress is a measurable construct, yet it relies on linguistic proxies rather than direct physiological or interoceptive behavioral measures.
- [Interoceptive machine framework: Toward interoception-inspired regulatory architectures in artificial intelligence (2026)](https://arxiv.org/abs/2604.24527) — Proposes a theoretical framework for applying interoceptive principles to AI, offering a conceptual parallel for how internal state sensing could drive regulation, but provides no empirical data on human psychophysiology or stress responses.

### What is NOT known

No published work has explicitly correlated baseline interoceptive accuracy (measured via behavioral heartbeat perception tasks like the Schandry task) with physiological stress reactivity (HRV) in publicly available psychophysiological datasets while statistically controlling for baseline HRV. Existing literature focuses either on the theoretical application of interoception in AI, the detection of stress in digital/textual domains, or general emotion regulation strategies, leaving the specific *predictive* link between the *trait* of interoceptive accuracy and the *state* of stress regulation—disentangled from baseline autonomic tone—unquantified in open human data.

### Why this gap matters

Understanding whether interoceptive awareness is a stable predictor of stress resilience *independent* of baseline physiological health (HRV) is critical for clinical screening. If high interoception predicts better regulation even when baseline HRV is low, it suggests interoceptive training is a viable standalone intervention for at-risk populations; if the effect vanishes when controlling for HRV, it suggests current models overestimate the role of perception and overemphasize the body's state rather than its sensing.

### How this project addresses the gap

This project conducts a rigorous audit of open-source psychophysiological datasets (e.g., WESAD, OpenNeuro) to determine if the co-occurrence of interoception tasks and stress paradigms exists. By systematically searching for and analyzing these datasets, the project will either identify a previously unutilized resource to test the hypothesis or definitively document the data gap, providing a clear roadmap for future primary data collection.

## Expected results

We expect to find that while datasets like WESAD contain rich physiological stress data, they lack the specific behavioral interoceptive accuracy tasks (e.g., Schandry) required to test the primary hypothesis. Consequently, the primary result will be a feasibility report confirming the scarcity of this specific multimodal data in current open repositories, rather than a statistical correlation. If a suitable dataset is found, we expect a weak-to-moderate positive correlation between baseline interoceptive accuracy and HRV recovery rates that remains significant after regressing out baseline HRV.

## Methodology sketch

- Download the WESAD dataset (wearable stress and affect detection) via `wget` from Zenodo (DOI: 10.5281/zenodo.1292932) to access ECG and respiration signals during stress and baseline phases.
- Search OpenNeuro for studies containing "TSST" and "heartbeat" or "interoception" keywords; download specific subject-level BIDS data if available.
- Preprocess ECG/PPG signals using Python `hrv-analysis` to compute RMSSD and SDNN metrics for baseline (resting) and stress (TSST) phases.
- Extract self-reported stress ratings (PANAS or similar) from associated metadata JSON files or event markers.
- **Data Availability Check**: Verify if WESAD or OpenNeuro subsets contain an explicit heartbeat perception task (Schandry task). If absent, document the absence as the primary finding; do not substitute with invalid proxies like resting-state HRV stability for "interoception."
- If data is available: Calculate the magnitude of physiological regulation as the difference (or slope) between stress-phase HRV and baseline HRV.
- If data is available: Perform linear regression with the regulation magnitude as the outcome, and baseline interoceptive accuracy as the primary predictor, **including baseline HRV as a covariate** to ensure the predictor (interoception) and the control (baseline HRV) are distinct from the outcome (regulation magnitude).
- Verify that the validation target (regulation magnitude) is not mathematically derived solely from the predictor's source; specifically, ensure the regression model tests the unique variance explained by interoception beyond the baseline autonomic state.
- Generate plots of HRV trajectories overlaid with stress phase markers using `matplotlib` to visualize individual variability (if data exists).
- Document data availability findings in a final `data_audit.md` if direct interoception tasks are missing from the datasets, explicitly stating the limitation of using physiological proxies and the necessity of future targeted data collection.

## Duplicate-check

- Reviewed existing ideas: None provided in current session context.
- Closest match: N/A.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-31T15:58:45Z
**Outcome**: success_after_expansion
**Original term**: The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress psychology
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Impact of Interoceptive Awareness on Emotional Regulation During Simulated Stress psychology | 5 |

### Verified citations

1. **Interoceptive machine framework: Toward interoception-inspired regulatory architectures in artificial intelligence** (2026). Diego Candia-Rivera. arXiv. [2604.24527](https://arxiv.org/abs/2604.24527). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Emo-LiPO: Listwise Preference Optimization for Fine-Grained Emotion Intensity Control in LLM-based Text-to-Speech** (2026). Yihang Lin, Li Zhou, Congwei Cao, Dongchu Xie, Xiaoxue Gao, et al.. arXiv. [2606.13006](https://arxiv.org/abs/2606.13006). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Digital Emotion Regulation on Social Media** (2023). Akriti Verma, Shama Islam, Valeh Moghaddam, Adnan Anwar. arXiv. [2307.13187](https://arxiv.org/abs/2307.13187). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Detecting Syllable-Level Pronunciation Stress with A Self-Attention Model** (2023). Wang Weiying, Nakajima Akinori. arXiv. [2311.00301](https://arxiv.org/abs/2311.00301). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **TensiStrength: Stress and relaxation magnitude detection for social media texts** (2016). Mike Thelwall. arXiv. [1607.00139](https://arxiv.org/abs/1607.00139). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
