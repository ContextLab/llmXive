# Idea rejected as infeasible — propose a CONSTRAINED replacement

Regeneration attempt 1 of 3. The previous idea (below) was judged infeasible for the execution environment. You MUST propose a SUBSTANTIALLY DIFFERENT idea in the same field that satisfies the feasibility constraint — do NOT re-state or lightly rephrase the rejected idea.

**Why it was rejected**: reason: flesh-out judged idea out of GHA-feasible scope
detected_at: 2026-06-27T00:12:20.909444+00:00

**Feasibility constraint**: the entire study must be executable by automated agents inside GitHub-Actions-class compute — public datasets or generated data only, no human subjects, no wet lab, no GPU training runs, no paid services.

## The rejected idea (for reference — do not reuse)

### investigating-neural-signatures-of-predi.md

---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating Neural Signatures of Predictive Processing in Visual Illusions

**Field**: neuroscience

## Research question

Does prediction error signaling in early visual cortex (V1/V2) correlate with the subjective magnitude of the Müller-Lyer illusion across individual subjects?

## Motivation

Predictive processing theories propose that perception results from the brain's minimization of prediction errors. Visual illusions like the Müller-Lyer provide a natural testbed for this framework, as the illusory percept persists despite veridical sensory input. However, empirical evidence linking early visual cortex prediction error signals to subjective illusion strength remains limited. Understanding this relationship would constrain predictive coding models and clarify the neural locus of perceptual inference.

## Literature gap analysis

### What we searched

We queried Semantic Scholar/arXiv/OpenAlex with three search strategies: (1) "predictive coding visual illusions fMRI neural activity" (8 results), (2) "Müller-Lyer illusion BOLD signal visual cortex" (8 results), and (3) "precision weighting prediction error perception fMRI" (8 results). The literature block contains 2 on-topic results from these searches.

### What is known

- [Visual illusions via neural dynamics: Wilson-Cowan-type models and the efficient representation principle (2019)](https://arxiv.org/abs/1907.13004) — This computational modeling work demonstrates that Wilson-Cowan neural dynamics can reproduce supra-threshold visual illusion phenomena, establishing a theoretical link between neural population dynamics and illusory perception.
- [Decoding Predictive Inference in Visual Language Processing via Spatiotemporal Neural Coherence (2025)](https://arxiv.org/abs/2512.20929) — This EEG-based study decodes neural responses to predictive inference in visual language processing, providing methodological precedent for measuring prediction-related neural signals, though in a different domain.

### What is NOT known

No published work has directly measured prediction error signaling in early visual cortex (V1/V2) and correlated it with subjective illusion magnitude across individual subjects in human neuroimaging data. Existing work is either computational modeling without empirical validation or uses different domains (language) and different neural measures (EEG coherence rather than fMRI BOLD).

### Why this gap matters

Filling this gap would provide the first direct empirical test of whether prediction error signals in early sensory cortex track subjective perceptual experience as predicted by hierarchical predictive coding theories. This would help distinguish between competing accounts of where in the visual hierarchy perceptual inference occurs and whether individual differences in illusion susceptibility reflect differences in early cortical prediction error processing.

### How this project addresses the gap

This project will analyze existing public fMRI datasets containing visual illusion stimuli, extract V1/V2 activation patterns during illusion presentation, compute prediction error proxies using computational models fitted to behavioral responses, and test for cross-subject correlations between neural signals and subjective magnitude ratings.

## Expected results

We expect to observe a positive correlation between V1/V2 prediction error signal strength and subjective Müller-Lyer illusion magnitude across subjects (r > 0.3, p < 0.05), supporting the hypothesis that early sensory prediction errors contribute to perceptual inference. A null result would suggest that illusion magnitude is determined by higher-level areas or that prediction error signals do not vary systematically across individuals in a way that affects subjective experience.

## Methodology sketch

- Download publicly available fMRI dataset containing visual illusion stimuli (e.g., OpenNeuro ds001234 or similar with Müller-Lyer task; verify data availability before implementation)
- Preprocess fMRI data using fMRIPrep (Docker container) with standard pipeline (motion correction, normalization, smoothing)
- Extract time-series from V1/V2 ROIs using HCP-style parcellation or functional localizers if available
- Fit a predictive coding computational model to behavioral illusion magnitude ratings to estimate individual-level prediction error parameters
- Compute prediction error signal proxy by contrasting BOLD response during illusion vs. veridical control stimuli in V1/V2
- Perform Pearson correlation between individual V1/V2 prediction error signal strength and subjective illusion magnitude ratings
- Apply bootstrap resampling (1000 iterations) to estimate confidence intervals on correlation coefficient
- Conduct sensitivity analysis excluding subjects with motion artifacts (>3mm translation)

## Duplicate-check

- Reviewed existing ideas: (none in corpus).
- Closest match: None identified.
- Verdict: NOT a duplicate

## Scope note

This methodology assumes a public fMRI dataset with visual illusion stimuli and subjective ratings is available. If no such dataset exists within download constraints (<2GB for 6h job), this project will be marked as rejected — out of scope, requiring data collection beyond GHA capabilities.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-27T00:11:57Z
**Outcome**: exhausted
**Original term**: Investigating Neural Signatures of Predictive Processing in Visual Illusions neuroscience
**Verified citation count**: 2

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Investigating Neural Signatures of Predictive Processing in Visual Illusions neuroscience | 0 |
| 1 | Predictive coding mechanisms in visual perception | 3 |
| 2 | Neural correlates of visual illusions | 4 |
| 3 | Top-down modulation in visual cortex | 0 |
| 4 | Bayesian inference in human vision | 0 |
| 5 | Expectation effects on visual processing | 0 |
| 6 | Prediction error signaling in visual areas | 0 |
| 7 | Electrophysiological markers of predictive coding | 0 |
| 8 | fMRI studies of perceptual illusions | 0 |
| 9 | Hierarchical predictive processing vision | 0 |
| 10 | Neural basis of ambiguous visual stimuli | 0 |
| 11 | Cortical oscillations during visual illusions | 0 |
| 12 | Mismatch negativity visual perception | 0 |
| 13 | Prior expectations visual system | 0 |
| 14 | Free energy principle visual perception | 0 |
| 15 | Contextual modulation visual illusions | 0 |
| 16 | Neural encoding of prediction errors vision | 0 |
| 17 | ERP components visual illusions | 0 |
| 18 | Bottom-up top-down visual integration | 0 |
| 19 | Perceptual bias neural mechanisms | 0 |
| 20 | Sensory prediction visual cortex activity | 0 |

### Verified citations

1. **Decoding Predictive Inference in Visual Language Processing via Spatiotemporal Neural Coherence** (2025). Sean C. Borneman, Julia Krebs, Ronnie B. Wilbur, Evie A. Malaia. arXiv. [2512.20929](https://arxiv.org/abs/2512.20929). PDF-sampled: No.
2. **Visual illusions via neural dynamics: Wilson-Cowan-type models and the efficient representation principle** (2019). Marcelo Bertalmío, Luca Calatroni, Valentina Franceschi, Benedetta Franceschiello, Alexander Gomez-Villa, et al.. arXiv. [1907.13004](https://arxiv.org/abs/1907.13004). PDF-sampled: No.

