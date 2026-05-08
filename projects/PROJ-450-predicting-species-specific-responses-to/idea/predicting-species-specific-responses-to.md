---
field: biology
submitter: google.gemma-3-27b-it
---

# Predicting Species-Specific Responses to Climate Change from Museum Collection Data

**Field**: biology

## Research question

How have species' realized climatic niches shifted over the past century in response to documented climate change, and do these shifts vary systematically across taxonomic groups or geographic regions?

## Motivation

Understanding how species track or fail to track changing climate conditions is critical for predicting extinction risk and prioritizing conservation action. Museum collections provide a unique temporal archive of species distributions spanning decades to centuries, yet their utility for quantifying niche shifts remains underexplored relative to newer occurrence databases. This work addresses the gap by systematically comparing species-specific climatic niche trajectories against regional climate trends.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex using terms: "herbarium climate niche shift", "museum collection species distribution modeling climate change", "temporal species occurrence climate tracking", and "natural history collection phenology climate response". The search returned approximately 150 records total, but only 2 were directly retrievable and on-topic for this specific research question.

### What is known

- [Digitization of herbaria enables novel research (2017)](https://doi.org/10.3732/ajb.1700281) — Establishes that digitized herbarium specimens can document spatial and temporal patterns of plant diversity, validating their use for large-scale distributional analyses.

### What is NOT known

No published work has systematically quantified species-specific realized climatic niche shifts across multiple taxa using museum occurrence data spanning the past century while directly comparing these shifts to regional climate trend magnitudes. Existing studies focus on either single-species case analyses or aggregate community-level metrics that mask species-level variation.

### Why this gap matters

Conservation prioritization requires identifying which species are lagging behind climate change (vulnerable) versus those tracking successfully (resilient). Without species-level niche shift estimates, conservation resources may be misallocated toward resilient species while vulnerable ones remain undetected until populations collapse.

### How this project addresses the gap

The methodology extracts georeferenced occurrence records from GBIF (which aggregates museum data) and pairs them with gridded climate data from WorldClim to compute species-specific niche centroids over time periods. This directly produces the previously unavailable species-level shift estimates that can be compared across taxa and regions.

## Expected results

We expect to find that species in rapidly warming regions show larger niche centroid shifts than those in stable climates, but with substantial taxonomic variation. A significant positive correlation between regional warming rates and species niche shifts would confirm climate tracking; a null or weak correlation would indicate widespread lag and elevated extinction risk. Either outcome provides actionable evidence for conservation prioritization.

## Methodology sketch

- Download georeferenced occurrence records from GBIF for 10–15 focal species across 3 taxonomic groups (e.g., plants, birds, insects) using `rgbif` R package; filter for records with >50 years temporal spread.
- Extract corresponding climate variables (mean annual temperature, precipitation) from WorldClim v2 historical layers (1970–2000 and 1991–2020) using `raster` package.
- Compute species-specific climatic niche centroids for each time period by averaging climate values at occurrence locations.
- Calculate niche shift magnitude as Euclidean distance in climate space between centroids; compute regional warming rate as difference in mean temperature between periods.
- Perform linear regression of species niche shift magnitude against regional warming rate; report slope, R², and p-value.
- Conduct sensitivity analysis by subsampling occurrence records to test robustness to sampling effort variation.
- Visualize results with scatter plots of niche shift vs. warming rate, colored by taxonomic group.

## Duplicate-check

- Reviewed existing ideas: none provided (existing_idea_paths was empty).
- Closest match: none identified.
- Verdict: NOT a duplicate
