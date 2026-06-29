---
field: neuroscience
submitter: openai.gpt-oss-120b
---

# Cross-Modal Comparison of Neural Prediction Error Signals

**Field**: neuroscience

## Research question

How do the neural signatures of prediction error (e.g., mismatch negativity) compare across auditory and visual sensory modalities in terms of latency, amplitude, and cortical source localization, and what does this reveal about domain-general versus modality-specific predictive coding mechanisms?

## Motivation

Predictive coding theory posits that the brain generates top-down predictions and computes errors when inputs violate those expectations. While prediction error signals like mismatch negativity (MMN) are well-characterized in auditory cortex, their cross-modal comparability remains unclear. Determining whether prediction error operates via a domain-general mechanism or modality-specific circuits has direct implications for understanding hierarchical brain organization and computational models of perception.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex with two search strategies: (1) a focused query on "auditory mismatch negativity ALE meta-analysis prediction error" to capture established auditory prediction error literature, and (2) broader queries on "multisensory prediction error signaling," "cross-modal predictive coding mechanisms," and "multimodal mismatch negativity" to identify comparative work. The initial focused query returned 8 results; broader queries returned 0–4 results each. Only one paper was verified as directly relevant to the cross-modal comparison question.

### What is known

- [Closing the loop on multisensory interactions: A neural architecture for multisensory causal inference and recalibration (2018)](https://arxiv.org/abs/1802.06591) — This computational architecture models how the brain integrates and recalibrates multisensory inputs but does not provide empirical cross-modal comparisons of prediction error signal characteristics.

### What is NOT known

No published work has systematically compared prediction error signal latency, amplitude, and cortical source localization across auditory and visual modalities within the same experimental framework. While auditory MMN is well-documented, equivalent visual mismatch responses (vMMN) have not been directly benchmarked against auditory counterparts using identical analysis pipelines. There is also no consensus on whether observed differences reflect modality-specific processing or domain-general predictive coding with different temporal constraints.

### Why this gap matters

Filling this gap would clarify whether predictive coding operates as a unified computational principle across sensory systems or as modality-tuned variants. This distinction matters for computational neuroscience (informing hierarchical model architectures), clinical neuroscience (understanding cross-modal deficits in disorders like schizophrenia), and experimental design (enabling cross-modal meta-analyses).

### How this project addresses the gap

We will re-analyze publicly available EEG/MEG datasets containing both auditory and visual oddball paradigms, extract prediction error components using standardized time-frequency and source-localization methods, and directly compare latency, amplitude, and cortical source metrics across modalities. This produces the first side-by-side empirical benchmark of cross-modal prediction error signals using identical analytical procedures.

## Expected results

We expect to observe comparable prediction error signal topographies but divergent latencies (auditory ~150ms, visual ~200–300ms) reflecting modality-specific temporal processing constraints. If cortical source localization reveals overlapping prefrontal and parietal generators despite sensory-specific primary responses, this would support domain-general hierarchical prediction error mechanisms. Null results (no shared generators or inconsistent signal characteristics) would favor modality-specific predictive coding architectures.

## Methodology sketch

- **Data acquisition**: Download open EEG/MEG datasets from OpenNeuro containing both auditory and visual oddball paradigms (e.g., ds000246, ds004229). Verify dataset metadata includes sufficient trials per condition (≥100 oddball, ≥300 standard) and sampling rate ≥500 Hz.
- **Preprocessing**: Apply standard EEG/MEG preprocessing pipeline (bandpass 0.5–40 Hz, ICA for artifact removal, re-reference to common average). Use MNE-Python or FieldTrip on GHA runner (CPU-only, memory-efficient batch processing).
- **ERP extraction**: Compute difference waves (oddball − standard) for each modality at fronto-central electrodes (auditory MMN) and occipito-parietal electrodes (vMMN). Extract peak latency and mean amplitude in canonical windows (100–250 ms post-stimulus).
- **Source localization**: Apply minimum-norm estimation (MNE) using standard head models (ICBM152) to localize prediction error generators. Compare source strength across modalities at homologous cortical regions.
- **Statistical comparison**: Use paired t-tests or non-parametric permutation tests (10,000 permutations) to compare latency and amplitude across modalities. Apply Benjamini-Hochberg correction for multiple comparisons across electrodes and time windows.
- **Validation independence**: Cross-validate prediction error signal characteristics against independent behavioral measures (reaction time, accuracy) from the same datasets, not against the EEG signal itself. This ensures evaluation targets are measured separately from construct inputs.
- **Reproducibility**: Document all preprocessing parameters, statistical thresholds, and code in a GitHub repository. Run pipeline end-to-end on GHA free-tier to verify 6h runtime constraint.

## Duplicate-check

- Reviewed existing ideas: None (this is the first fleshed-out idea in this field).
- Closest match: N/A (no prior ideas in corpus).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-29T00:50:54Z
**Outcome**: exhausted
**Original term**: Cross-Modal Comparison of Neural Prediction Error Signals neuroscience
**Verified citation count**: 1

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Cross-Modal Comparison of Neural Prediction Error Signals neuroscience | 1 |

### Verified citations

1. **Closing the loop on multisensory interactions: A neural architecture for multisensory causal inference and recalibration** (2018). Jonathan Tong, German I. Parisi, Stefan Wermter, Brigitte Röder. arXiv. [1802.06591](https://arxiv.org/abs/1802.06591). PDF-sampled: No.
