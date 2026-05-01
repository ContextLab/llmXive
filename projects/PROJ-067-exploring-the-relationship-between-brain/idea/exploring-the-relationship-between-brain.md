---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Exploring the Relationship Between Brain Network Dynamics and Individual Differences in Dream Recall Frequency

**Field**: neuroscience

## Research question

Do individual differences in resting-state dynamic functional connectivity (specifically network flexibility and stability) predict self-reported dream recall frequency?

## Motivation

Dream recall frequency varies widely across individuals, yet the neural mechanisms driving this variability are poorly understood. This project addresses the gap between static connectivity models and dynamic brain states, hypothesizing that high recallers exhibit more flexible network reconfiguration in memory and self-referential circuits.

## Related work

- [Toward an Integration of Deep Learning and Neuroscience (2016)](https://doi.org/10.3389/fncom.2016.00094) — Provides foundational context for using computational models to bridge neural dynamics and cognitive phenomena, though specific dream-recall links remain unexplored.

## Expected results

We expect to find a positive correlation between dynamic network flexibility in the Default Mode Network and dream recall frequency. A statistically significant correlation (p < 0.05, FDR-corrected) would support the hypothesis that dynamic brain states facilitate memory consolidation during wakefulness.

## Methodology sketch

- **Data Acquisition**: Download resting-state fMRI data from OpenNeuro (e.g., `https://openneuro.org/`) filtering for studies with sleep questionnaire metadata. Target N=50 subjects to fit GitHub Actions memory limits.
- **Preprocessing**: Use `Nilearn` (Python) to run standard denoising (ICA-AROMA) and normalization; ensure intermediate files are cleaned to stay under 7 GB RAM.
- **Dynamic Connectivity**: Implement sliding window correlation (window size 30s, step 10s) to generate time-varying connectivity matrices for each subject.
- **Metric Extraction**: Calculate network flexibility and stability metrics using `NetworkX` for key networks (DMN, Salience, Hippocampal).
- **Statistical Analysis**: Perform Spearman correlation between network metrics and dream recall scores (extracted from study metadata).
- **Validation**: Run permutation testing (1000 iterations) to establish null distributions within the 6-hour job limit.

## Duplicate-check

- Reviewed existing ideas: None provided for comparison.
- Closest match: N/A.
- Verdict: NOT a duplicate
