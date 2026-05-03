---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Decoding Emotional Valence from Facial EMG Patterns with Machine Learning

**Field**: Neuroscience

## Research question

Can machine learning algorithms accurately classify emotional valence (positive vs. negative) using feature sets extracted from facial electromyography (EMG) signals without requiring visual facial expression analysis?

## Motivation

Facial EMG provides a direct physiological measure of muscle tension associated with emotion, offering higher temporal resolution than video-based systems. While current literature focuses heavily on EEG or visual cues, there is a gap in leveraging specific facial muscle activity for robust valence decoding in affective computing.

## Related work

- [Human emotion recognition from EEG-based brain–computer interface using machine learning: a comprehensive review (2022)](https://doi.org/10.1007/s00521-022-07292-4) — Establishes the broader landscape of ML-based emotion recognition, though focused on EEG rather than peripheral EMG signals.
- [Review and Classification of Emotion Recognition Based on EEG Brain-Computer Interface System Research: A Systematic Review (2017)](https://doi.org/10.3390/app7121239) — Provides systematic methodology for classifying emotional states using biosignals, serving as a template for feature engineering in this project.
- [Why bodies? Twelve reasons for including bodily expressions in affective neuroscience (2009)](https://doi.org/10.1098/rstb.2009.0190) — Justifies the inclusion of bodily/physiological signals (like EMG) over purely facial visual analysis in affective neuroscience research.

## Expected results

We expect to achieve classification accuracy significantly above chance (>65%) for valence using standard classifiers like SVM or Random Forest on time-domain EMG features. Validation will rely on 5-fold cross-validation scores and permutation testing to confirm the signal is not driven by noise artifacts.

## Methodology sketch

- Download the DEAP dataset (https://www.eecs.qmul.ac.uk/mmv/datasets/deap/) which includes synchronized facial EMG recordings from 32 subjects.
- Preprocess raw EMG signals using a 10–500 Hz bandpass filter and 50/60 Hz notch filter to remove powerline interference.
- Extract time-domain features including Root Mean Square (RMS), Zero Crossings (ZC), and Willison Amplitude (WAMP) per 1-second window.
- Train Support Vector Machine (SVM) and Random Forest classifiers using scikit-learn on the feature vectors.
- Evaluate performance using 5-fold cross-validation to ensure generalization across subjects.
- Apply a paired t-test to compare model accuracies against a shuffled baseline to determine statistical significance (p < 0.05).
- Ensure all computation runs within 7GB RAM limits by processing subjects individually rather than loading all data at once.

## Duplicate-check

- Reviewed existing ideas: None found in current project corpus.
- Closest match: N/A.
- Verdict: NOT a duplicate
