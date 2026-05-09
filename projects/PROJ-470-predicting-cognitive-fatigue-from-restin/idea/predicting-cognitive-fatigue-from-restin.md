---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Predicting Cognitive Fatigue from Resting-State EEG Complexity

**Field**: neuroscience

## Research question

Does resting-state EEG signal complexity, measured via Lempel-Ziv complexity or permutation entropy, correlate with subjective cognitive fatigue levels following a sustained attention task?

## Motivation

Cognitive fatigue is a debilitating symptom across neurological and psychiatric conditions (e.g., MS, depression, ADHD) but lacks objective biomarkers. If EEG complexity measures can serve as a fatigue proxy, this would enable real-time monitoring and intervention. The key gap is whether complexity changes are detectable in resting-state data (easier to collect) versus task-locked data (more demanding).

## Literature gap analysis

### What we searched

Queries attempted: (1) "EEG complexity Lempel-Ziv cognitive fatigue", (2) "resting-state EEG entropy fatigue biomarker", (3) "permutation entropy mental fatigue EEG". Sources: Semantic Scholar / arXiv / OpenAlex. Volume: ~15-25 results per query, many tangentially related to EEG complexity or fatigue separately but not both constructs together.

### What is known

- EEG complexity measures (Lempel-Ziv, sample entropy, permutation entropy) reliably capture state-dependent neural dynamics in healthy and clinical populations.
- Cognitive fatigue is associated with changes in EEG spectral power (increased theta, decreased alpha/beta) and functional connectivity patterns.
- Some work shows resting-state EEG features predict fatigue-prone driving performance, but complexity metrics specifically are underexplored.

### What is NOT known

No published work has systematically correlated resting-state EEG complexity (specifically LZ or permutation entropy) with post-task subjective fatigue ratings using standardized cognitive tasks. Most complexity studies focus on sleep, anesthesia, or consciousness disorders rather than cognitive fatigue. The temporal relationship (whether complexity changes precede, coincide with, or follow subjective fatigue reports) is also uncharacterized.

### Why this gap matters

Objective fatigue biomarkers would enable personalized interventions for fatigue-prone occupations (pilots, healthcare workers, drivers) and clinical populations. If resting-state complexity is predictive, it offers a low-burden assessment method compared to task-locked paradigms. The answer could constrain theoretical models of how neural information processing degrades under cognitive load.

### How this project addresses the gap

This project will (1) extract resting-state EEG complexity measures from publicly available datasets collected before/after sustained attention tasks, (2) correlate complexity metrics with subjective fatigue ratings, and (3) test whether baseline complexity predicts fatigue magnitude. The correlation analysis directly produces the previously-unavailable evidence linking these two constructs.

## Expected results

We expect decreased resting-state EEG complexity to correlate with increased subjective fatigue (r > 0.3, p < 0.05). A null result would be equally informative, suggesting complexity is not a viable fatigue biomarker. Evidence strength requires N ≥ 30 participants with paired pre/post measures to achieve 80% power for moderate effect sizes.

## Methodology sketch

- Download resting-state EEG datasets from PhysioNet (e.g., EEG Motor Movement/Imagery Dataset, Sleep-EDF) with pre/post cognitive task recordings
- Filter data to participants who completed sustained attention tasks (e.g., PVT, Stroop) with subjective fatigue ratings
- Preprocess EEG using MNE-Python: bandpass filter (1-40 Hz), remove line noise, reject bad channels/epochs, re-reference to average
- Extract resting-state segments (2-5 min eyes-closed or eyes-open) before and after the task
- Calculate Lempel-Ziv complexity and permutation entropy for each channel and electrode montage
- Compute fatigue delta scores (post-task rating minus baseline rating) from self-report questionnaires
- Perform Pearson/Spearman correlation between complexity changes and fatigue delta scores
- Control for confounds: age, time of day, baseline complexity, medication status
- Report effect sizes, confidence intervals, and power analysis; visualize with scatter plots and regression lines

## Duplicate-check

- Reviewed existing ideas: EEG biomarkers for sleep disorders, functional connectivity changes in depression, EEG entropy in anesthesia.
- Closest match: EEG biomarkers for sleep disorders (similarity: both use EEG complexity but different target construct).
- Verdict: NOT a duplicate
