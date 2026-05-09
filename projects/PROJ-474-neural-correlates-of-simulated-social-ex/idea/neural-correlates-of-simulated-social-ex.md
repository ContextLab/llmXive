---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Neural Correlates of Simulated Social Exclusion on Default Mode Network Dynamics

**Field**: neuroscience

## Research question

How does acute simulated social exclusion modulate functional connectivity dynamics within the default mode network (DMN)?

## Motivation

Social exclusion is a robust predictor of adverse mental health outcomes, yet the specific neural mechanisms linking rejection to DMN dysfunction remain under-specified. While the DMN is implicated in self-referential processing, its dynamic response to acute social threat in healthy populations requires clearer characterization. Clarifying this relationship could inform targeted interventions for conditions involving rejection sensitivity, such as social anxiety disorder.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and OpenAlex using terms including "default mode network social exclusion," "fMRI Cyberball task connectivity," and "DMN dynamics social rejection." The literature block returned 8 results, of which only 1 is directly on-topic regarding DMN and social cognition, and 1 is tangentially related to neural flexibility and mood. The majority of results concern social *network* theory (graph dynamics, information diffusion) or machine learning, rather than neuroimaging of social exclusion.

### What is known

- [The default mode network and social understanding of others: what do brain connectivity studies tell us](https://doi.org/10.3389/fnhum.2014.00074) — Establishes that the DMN is fundamentally involved in domains of cognitive and social processing, providing a theoretical basis for linking DMN activity to social experiences.
- [Psilocybin therapy increases cognitive and neural flexibility in patients with major depressive disorder](https://doi.org/10.1038/s41398-021-01706-y) — Demonstrates that neural flexibility in mood disorders is modifiable, suggesting that state-dependent neural changes (like those during exclusion) are measurable, though not specific to social exclusion.

### What is NOT known

There is no published work in the provided results that quantifies specific functional connectivity changes within the DMN *during* a simulated social exclusion paradigm (e.g., Cyberball) using public resting-state or task-based fMRI data. Existing literature focuses on broad social understanding or clinical interventions rather than the acute neural dynamics of exclusion in healthy cohorts.

### Why this gap matters

Filling this gap would provide empirical evidence for how transient social stressors alter core brain networks involved in self-referential thought. This is critical for distinguishing between trait-level DMN abnormalities (e.g., in depression) and state-level responses to social threat, potentially refining diagnostic biomarkers for social anxiety.

### How this project addresses the gap

This project directly measures DMN functional connectivity strength before and after a standardized exclusion task using public fMRI data. By computing connectivity metrics and comparing conditions, this study generates the missing quantitative evidence linking acute social exclusion to specific DMN dynamic alterations.

## Expected results

We expect to observe a significant reduction in functional connectivity strength between DMN nodes (e.g., PCC and mPFC) following the exclusion condition compared to the inclusion condition. Confirmation will rely on a paired statistical test showing a consistent directional shift across subjects, with effect sizes sufficient to distinguish state from noise.

## Methodology sketch

- Download preprocessed resting-state and task-based fMRI data from OpenNeuro (e.g., dataset ds000030 or similar Cyberball task datasets) ensuring total size fits within 14GB SSD limits.
- Extract BOLD time-series signals from canonical DMN regions of interest (PCC, mPFC, angular gyrus) using standard atlases (e.g., AAL or Harvard-Oxford).
- Compute Pearson correlation matrices for DMN nodes separately for pre-task (baseline) and post-exclusion blocks.
- Calculate functional connectivity strength as the mean absolute correlation coefficient across DMN edges for each condition.
- Apply a non-parametric paired permutation test (10,000 iterations) to compare connectivity strength between inclusion and exclusion conditions.
- Visualize connectivity changes using heatmaps and bar plots with error bars indicating 95% confidence intervals.
- Validate data integrity by checking for motion artifacts (>3mm displacement) and excluding affected subjects from analysis.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A (No existing ideas provided for comparison).
- Verdict: NOT a duplicate
