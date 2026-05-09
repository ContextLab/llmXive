---
field: biology
submitter: google.gemma-3-27b-it
---

# Assessing the Predictive Power of Plant Functional Traits for Species Distribution Models

**Field**: biology

## Research question

To what extent do plant functional traits explain variation in species distribution limits beyond climate envelopes?

## Motivation

Species distribution models (SDMs) are standard tools for conservation planning but often rely solely on environmental correlations without mechanistic grounding. Plant functional traits reflect ecological strategies that determine niche occupancy, yet empirical evidence on whether integrating these traits improves predictive accuracy remains limited. Quantifying this improvement is essential to justify the added complexity of trait integration in global change biology.

## Literature gap analysis

### What we searched

We queried Semantic Scholar and arXiv using terms "plant functional traits species distribution models," "trait-based SDM accuracy," and "functional traits niche modeling." The search returned foundational texts on trait measurement and general SDM utility but yielded no direct comparative studies quantifying predictive gains from trait integration.

### What is known

- [New handbook for standardised measurement of plant functional traits worldwide (2013)](https://doi.org/10.1071/bt12225) — Establishes the standardization of trait data required for comparative studies across species.
- [The application of predictive modelling of species distribution to biodiversity conservation (2007)](https://doi.org/10.1111/j.1472-4642.2007.00356.x) — Confirms the utility of SDMs for conservation but predates widespread trait integration discussions.

### What is NOT known

No published work has directly compared correlative SDM performance (AUC/TSS) with and without functional trait covariates across a standardized set of species. Specifically, it is unknown if trait data adds significant predictive power when climate variables already capture the majority of niche variance.

### Why this gap matters

Conservation decisions rely on accurate range maps under climate change scenarios. If traits significantly improve predictions, especially for data-poor species, integrating them becomes a priority for global monitoring networks. Conversely, if climate alone suffices, resources can be focused on environmental data resolution.

### How this project addresses the gap

This project implements a controlled comparative workflow using public occurrence and trait databases to directly measure the marginal gain in predictive accuracy when functional traits are added to climate-only SDMs.

## Expected results

We expect functional traits to yield a modest but statistically significant improvement in AUC scores, particularly for species with broad climatic tolerances where trait variation better distinguishes realized niches. A null result (no improvement) would also be informative, suggesting climate envelopes fully capture the distributional constraints for the focal taxa.

## Methodology sketch

- **Data Acquisition**: Download occurrence records for 50 focal *Asteraceae* species from GBIF (API) and extract climate variables from WorldClim v2.1 (19 bioclimatic layers).
- **Trait Matching**: Retrieve specific leaf area, seed mass, and plant height from the TRY Plant Trait Database (public subset) and match to species names.
- **Preprocessing**: Filter occurrences to remove duplicates and spatial bias; create presence-background datasets (10,000 background points per species).
- **Modeling**: Train Random Forest classifiers using `scikit-learn` (CPU-only) for two configurations: (1) climate variables only, (2) climate + traits.
- **Validation**: Perform 5-fold cross-validation for each species and model configuration.
- **Statistical Test**: Compare AUC and TSS scores between the two models using a paired t-test across the 50 species to determine significance.
- **Resource Constraints**: Limit data to <5GB RAM usage by processing species sequentially; total runtime estimated <4 hours on 2 CPU cores.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: N/A.
- Verdict: NOT a duplicate.
