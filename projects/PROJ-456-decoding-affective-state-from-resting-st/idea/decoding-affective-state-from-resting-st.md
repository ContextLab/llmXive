---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Decoding Affective State from Resting-State EEG Microstates

**Field**: neuroscience

## Research question

Do resting-state EEG microstate temporal dynamics systematically vary with individual affective state dimensions (valence and arousal)?

## Motivation

Resting-state EEG offers a non-invasive window into neural dynamics without task demands, yet its relationship to trait-level affective dimensions remains unclear. Establishing this link could enable affective biomarkers that don't require active emotional elicitation paradigms, improving ecological validity for clinical monitoring and research applications.

## Literature gap analysis

### What we searched

Literature search queried Semantic Scholar and arXiv for combinations of "EEG microstates," "affective state," "resting-state emotion," and "valence arousal EEG." One result returned on resting-state EEG applications, focused on motor-imagery decoding rather than affective dimensions.

### What is known

- [Can EEG resting state data benefit data-driven approaches for motor-imagery decoding? (2024)](http://arxiv.org/abs/2411.09789v1) — Establishes that resting-state EEG reveals individual-specific neural patterns, though applied to motor tasks rather than affective states.

### What is NOT known

No published work has systematically examined whether microstate temporal dynamics (duration, occurrence, coverage) correlate with self-reported affective dimensions in resting-state conditions. The relationship between microstate sequences and valence/arousal remains unexplored.

### Why this gap matters

Filling this gap would enable passive affective monitoring without emotional task paradigms, supporting clinical screening for mood disorders and real-time affective state estimation in naturalistic settings where task-based assessment is impractical.

### How this project addresses the gap

This project will extract microstate features from resting-state EEG in OpenNeuro datasets with affective self-reports, then test correlations between microstate dynamics and valence/arousal scores, producing the first published evidence on this relationship.

## Expected results

We expect to detect at least one microstate metric (e.g., duration or occurrence rate) that shows significant correlation (|r| > 0.3, p < 0.05) with valence or arousal scores. Null results would constrain theoretical models of resting-state affective processing. Evidence level requires replication across multiple datasets or cross-validation splits.

## Methodology sketch

- Download resting-state EEG data from OpenNeuro (e.g., ds003501, ds004137) with available affective questionnaires
- Preprocess EEG: bandpass filter (1-40 Hz), remove artifacts via ICA, re-reference to average
- Segment EEG into 4 canonical microstate classes using K-means clustering on topographic maps
- Extract temporal features: mean duration, occurrence rate, coverage, transition probability for each microstate class
- Collect self-reported valence/arousal scores from associated questionnaires (e.g., PANAS, SAM)
- Compute Pearson/Spearman correlations between microstate features and affective scores
- Apply Bonferroni correction for multiple comparisons across microstate classes and affective dimensions
- Validate findings using leave-one-subject-out cross-validation where sample size permits
- Generate effect size estimates (Cohen's d) and confidence intervals for significant correlations

## Duplicate-check

- Reviewed existing ideas: None provided in input.
- Closest match: No existing ideas to compare.
- Verdict: NOT a duplicate
