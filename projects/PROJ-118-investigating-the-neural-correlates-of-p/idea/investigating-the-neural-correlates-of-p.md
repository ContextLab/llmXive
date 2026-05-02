---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Neural Correlates of Predictive Coding Errors in Auditory Perception

**Field**: neuroscience

## Research question

How do event‑related potential components, especially the Mismatch Negativity (MMN), reflect prediction‑error signals during auditory perception in humans?

## Motivation

Predictive coding explains perception as continuous model updating driven by prediction errors, yet most empirical support comes from vision. Auditory perception, particularly the neural signature of deviance detection (MMN), remains under‑explored in this framework. Clarifying the relationship between stimulus predictability and MMN amplitude/latency will bridge this gap and inform theories of auditory learning.

## Related work

- [Relating Human Perception of Musicality to Prediction in a Predictive Coding Model (2022)](http://arxiv.org/abs/2210.16587v1) — Demonstrates a computational predictive‑coding model applied to music perception, highlighting the relevance of prediction error to auditory processing.  
- [Predictive coding and stochastic resonance as fundamental principles of auditory perception (2022)](http://arxiv.org/abs/2204.03354v2) — Discusses how predictive coding and stochastic resonance could underlie auditory perception, providing a theoretical basis for linking MMN to prediction errors.  
- [A General Close‑loop Predictive Coding Framework for Auditory Working Memory (2025)](http://arxiv.org/abs/2503.12506v1) — Introduces a predictive‑coding architecture for auditory working memory, suggesting neural signatures that may overlap with MMN.  
- [Neuromorphic Auditory Perception by Neural Spiketrum (2023)](http://arxiv.org/abs/2309.05430v1) — Explores biologically plausible spiking models for auditory perception, offering insights into how prediction errors could be encoded in neural dynamics.  
- [Neural Population Geometry Reveals the Role of Stochasticity in Robust Perception (2021)](http://arxiv.org/abs/2111.06979v1) — Shows how stochastic population activity relates to perceptual robustness, relevant for interpreting variability in MMN responses.  
- [Information thermodynamics: from physics to neuroscience (2024)](http://arxiv.org/abs/2409.17599v1) — Provides a thermodynamic perspective on information processing in the brain, useful for framing MMN as a measurable prediction‑error signal.

## Expected results

We expect larger MMN amplitudes and earlier latencies for low‑probability (unexpected) tones compared with high‑probability tones, indicating stronger and faster prediction‑error signaling. Confirmation will come from statistically significant differences (p < 0.05, corrected) between conditions across participants; a null result would falsify the hypothesis that MMN directly indexes predictive‑coding errors.

## Methodology sketch

- **Dataset acquisition**: Download the publicly available auditory oddball EEG dataset from OpenNeuro (e.g., ds003645, DOI 10.18112/openneuro.ds003645.v1.0.2) via `wget` or `curl`.  
- **Preprocessing**: Use MNE‑Python to filter (1–30 Hz), re‑reference, and epoch data time‑locked to stimulus onset (−200 ms to 600 ms). Perform artifact rejection (e.g., ICA for eye blinks).  
- **Condition labeling**: Assign each epoch to “standard” (high‑probability) or “deviant” (low‑probability) based on stimulus metadata. Compute trial‑wise predictability scores if the dataset includes graded probabilities.  
- **ERP extraction**: Average epochs per condition to obtain ERPs; isolate the MMN window (≈150–250 ms post‑stimulus) at fronto‑central electrodes (Fz, FCz).  
- **Amplitude & latency measurement**: For each participant, compute peak MMN amplitude (minimum voltage) and latency (time of peak) within the window.  
- **Statistical analysis**: Conduct paired‑sample t‑tests (or non‑parametric Wilcoxon signed‑rank tests if normality fails) comparing deviant vs. standard amplitudes and latencies across participants. Apply Bonferroni correction for multiple electrodes if needed.  
- **Effect‑size estimation**: Report Cohen’s d for amplitude and latency differences.  
- **Robustness checks**: Perform a mixed‑effects model with subject as random effect and predictability as a continuous predictor to verify linearity of prediction‑error scaling.  
- **Visualization**: Generate grand‑average ERP plots with shaded confidence intervals, and topographic maps of MMN differences using matplotlib/seaborn.  
- **Reproducibility**: Package the analysis in a Jupyter notebook, pin all Python dependencies (e.g., `mne==1.6`, `numpy`, `pandas`, `statsmodels`), and provide a `requirements.txt` for the GitHub Actions runner.

## Duplicate-check

- Reviewed existing ideas: (none provided).
- Closest match: (no close match identified).
- Verdict: NOT a duplicate.
