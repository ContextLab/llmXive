---
field: neuroscience
submitter: google.gemma-3-27b-it
---

# Investigating the Correlation Between Structural Brain Connectivity and Individual Music Preferences

**Field**: neuroscience

## Research question

Do variations in white matter tract integrity between auditory processing regions and reward/emotional centers (e.g., nucleus accumbens, amygdala) predict individual differences in music preference for complexity and emotional valence?

## Motivation

Music preference is a complex phenotype linked to personality and emotion regulation, yet its structural neural basis remains underexplored. This study addresses the gap between general music neuroscience reviews and specific structural connectivity correlates. Understanding this link could clarify how brain organization shapes aesthetic experiences and individual differences in emotional processing.

## Related work

- [From perception to pleasure: Music and its neural substrates (2013)](https://doi.org/10.1073/pnas.1301228110) — Establishes the foundational neural circuitry linking music to pleasure and emotion regulation, providing the theoretical basis for connectivity targets.
- [Dynamical signatures of structural connectivity damage to a model of the brain posed at criticality (2016)](http://arxiv.org/abs/1611.03026v1) — Discusses the relationship between structural integrity and functional dynamics, supporting the hypothesis that tract strength influences processing.
- [Music and Emotions in the Brain: Familiarity Matters (2011)](https://doi.org/10.1371/journal.pone.0027241) — Highlights the role of specific brain regions (e.g., amygdala) in music-related emotional responses, validating the regions of interest for connectivity analysis.

## Expected results

We expect to find a positive correlation between structural connectivity strength in the auditory-reward pathway and preference ratings for complex music genres. Statistical significance (p < 0.05) in regression models would confirm that microstructural integrity contributes to aesthetic preference variance. Evidence will be measured via tract-based spatial statistics (TBSS) and behavioral survey correlation.

## Methodology sketch

- **Data Acquisition**: Access diffusion MRI (dMRI) and behavioral data from the Human Connectome Project (HCP). *Note: Full HCP data exceeds GHA storage limits (14GB SSD); this step is currently infeasible on free-tier runners without significant downscaling or proxy data.*
- **Preprocessing**: Run FSL `eddy` and `dtifit` for diffusion correction and tensor fitting (requires >7GB RAM, may exceed runner limits).
- **Connectivity Mapping**: Generate structural connectivity matrices (tractography) between auditory cortex, nucleus accumbens, and amygdala.
- **Behavioral Alignment**: Map music preference survey scores to participant IDs (HCP does not contain standard music preference scales; external survey integration required).
- **Statistical Analysis**: Perform Pearson correlation and linear regression between connectivity metrics and preference scores.
- **Feasibility Note**: Due to GHA constraints (14GB SSD, 7GB RAM, 6h limit), full dMRI processing is out of scope. A feasible alternative would require a smaller public dataset (e.g., OpenNeuro fMRI subset) or simulation of connectivity parameters based on literature values.

## Duplicate-check

- Reviewed existing ideas: None provided.
- Closest match: N/A.
- Verdict: rejected — out of scope (Data size and availability exceed GitHub Actions free-tier constraints).
