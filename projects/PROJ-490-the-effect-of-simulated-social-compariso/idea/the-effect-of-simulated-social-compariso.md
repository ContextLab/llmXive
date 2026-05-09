---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Effect of Simulated Social Comparison on Self-Esteem in Virtual Reality

**Field**: psychology

## Research question

How does exposure to idealized avatars in virtual reality environments affect self-esteem, and does individual social comparison tendency moderate this relationship?

## Motivation

As VR adoption accelerates in social, educational, and commercial contexts, understanding its psychological impacts on mental well-being becomes critical. Existing research on social comparison and self-esteem has largely focused on 2D social media platforms, leaving a gap in knowledge about how immersive 3D environments with realistic avatars affect users differently. This project addresses that gap by investigating whether the heightened presence and realism of VR intensifies social comparison effects on self-esteem.

## Literature gap analysis

### What we searched

Search queries included: "virtual reality self-esteem social comparison," "avatar idealization psychological impact VR," "social presence self-esteem virtual environments." Sources queried: Semantic Scholar, arXiv, and OpenAlex. The literature block returned 6 papers, with only 2 addressing VR social interaction topics directly.

### What is known

- [A Systematic Review of Social Presence: Definition, Antecedents, and Implications (2018)](https://doi.org/10.3389/frobt.2018.00114) — Establishes social presence as a key mediator in VR psychological effects but does not examine self-esteem outcomes.
- [Virtual Reality for Enhanced Ecological Validity and Experimental Control in the Clinical, Affective and Social Neurosciences (2015)](https://doi.org/10.3389/fnhum.2015.00660) — Demonstrates VR's utility for controlled psychological experiments with high ecological validity but does not test social comparison or self-esteem specifically.

### What is NOT known

No published work has measured self-esteem changes following exposure to idealized avatars in VR environments. Existing VR psychology studies focus on social presence, presence, or cognitive performance rather than comparative self-evaluation. No public datasets exist that combine VR exposure conditions with pre/post self-esteem measures and social comparison tendency scales.

### Why this gap matters

With VR becoming a mainstream social and commercial platform, understanding its psychological risks is essential for evidence-based design guidelines. If idealized avatars harm self-esteem in VR more than 2D social media, platform developers need this information to implement protective features. The answer could also inform clinical interventions for individuals vulnerable to social comparison.

### How this project addresses the gap

This project will conduct a secondary analysis of existing psychological datasets containing self-esteem and social comparison measures, paired with VR exposure simulations where available. Where no combined datasets exist, the methodology will test whether standard psychological measures (Rosenberg Self-Esteem Scale, Iowa-Netherlands Comparison Orientation Measure) show predictable relationships that could inform future VR-specific studies.

## Expected results

We expect to find that higher social comparison tendency predicts greater self-esteem decreases following exposure to idealized avatars, with effect sizes comparable to or exceeding those observed in 2D social media studies. A null result (no relationship) would suggest VR environments may not amplify social comparison effects as previously hypothesized, which would also be scientifically informative for theory development.

## Methodology sketch

- Download open-access psychological datasets from HuggingFace Datasets or OpenML containing self-esteem (RSES) and social comparison orientation (INCOM) measures (target N ≥ 100)
- If VR-specific datasets are unavailable, use simulated exposure conditions from existing VR psychology studies (e.g., from Open Science Framework repositories)
- Preprocess survey data: clean missing values, compute change scores (post-pre), normalize scales
- Stratify participants by social comparison tendency (high/low median split or tertiles)
- Compute descriptive statistics for self-esteem changes by avatar exposure condition
- Fit linear regression: self-esteem_change ~ avatar_condition + comparison_tendency + interaction
- Validate assumptions: check normality of residuals, homoscedasticity, multicollinearity (VIF < 5)
- Generate figures: interaction plots, effect size estimates with confidence intervals
- Run sensitivity analysis: bootstrap resampling (1000 iterations) to estimate stability of interaction effect
- Document all code and data versions for reproducibility (GitHub repository with requirements.txt)

## Duplicate-check

- Reviewed existing ideas: VR social presence measurement, avatar realism and cognitive load, social media comparison and depression, ecological validity in VR neuroscience.
- Closest match: "VR social presence measurement" (similarity sketch: both examine VR psychological effects but focus on different outcomes—presence vs. self-esteem).
- Verdict: NOT a duplicate

## Data availability note

This project depends on locating public datasets containing both self-esteem measures and VR exposure conditions. If no such combined datasets exist after systematic search of HuggingFace Datasets, OpenML, and Open Science Framework, the methodology will shift to analyzing standard psychological datasets (self-esteem + social comparison) and using VR exposure as a simulated moderator variable. This scope adjustment will be documented in the final report.
