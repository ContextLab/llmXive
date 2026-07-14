# Research: The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

## Research Question

Does enhancing the visual salience (luminance contrast/brightness) of target objects in morally ambiguous scenarios significantly increase blame ratings assigned by participants?

## Dataset Strategy

### Verified Datasets

The project will **NOT** use `lmms-lab/POPE` or `lmms-lab/RefCOCO` for identifying moral ambiguity, as these datasets lack the necessary semantic context (moral conflict, duty, outcome uncertainty) and pose a fatal construct validity threat.

Instead, the project will use a **Manual Curation & Text-to-Image Synthesis** strategy:
1. **Manual Curation**: A set of text descriptions of morally ambiguous scenarios (e.g., "A person stealing medicine to feed a starving child") will be manually curated by the researchers. These narratives provide the necessary moral context.
2. **Image Generation/Selection**:
   - **Option A (Preferred)**: Generate images for these narratives using a CPU-tractable diffusion model (e.g., `stable-diffusion-v1-5` via `diffusers` on CPU). This ensures the image matches the narrative.
   - **Option B (Fallback)**: Select public domain images that visually match the curated narratives.
3. **Verification**: The generated/selected images will be verified for visual quality and semantic match to the narrative.

**Note**: The "Verified datasets" block in the prompt does not contain a suitable dataset for morally ambiguous visual scenarios. Therefore, the project relies on **Manual Curation** (which does not require a URL) and **Synthetic Generation** (using open-source models) to ensure construct validity.

| Dataset/Source | URL | Usage | Notes |
|----------------|-----|-------|-------|
| Manual Curation | N/A | Source of morally ambiguous text narratives | Researchers curate a curated set of scenarios. No URL required. |
| Stable Diffusion v1.5 (via diffusers) | https://huggingface.co/runwayml/stable-diffusion-v1-5 | Image generation (if Option A) | CPU-tractable; used to visualize curated narratives. |
| Public Domain Image Repos | N/A | Image selection (if Option B) | Used only if generation is too slow; must match narrative. |

**Limitation**: The lack of a dedicated morally ambiguous visual dataset in the "Verified datasets" block is a significant constraint. The project addresses this by **manually creating** the stimuli from text narratives, ensuring the moral context is present by design.

### Data Processing Pipeline

1. **Ingestion**: Load curated text narratives from `data/raw/scenarios.csv`.
2. **Image Generation/Selection**: Generate or select images for each narrative.
3. **Human Coding**: Recruit ≥3 independent annotators to rate ambiguity (1-5 Likert). Scenarios with mean ≥ 3.5 AND Cohen's κ ≥ 0.6 are selected.
4. **Manipulation**: Generate low, medium, and high salience variants for each selected scenario.
5. **Pilot Manipulation Check**: Recruit a **separate** panel of coders to confirm "moral narrative preservation" (≥80% agreement).
6. **Validation**: Verify manipulation success using CLIP similarity (≥ 0.95) **AND** human narrative check.

## Statistical Analysis Plan

### Model Specification

The primary analysis will use a Linear Mixed-Effects Model (LMM) to test the effect of visual salience on blame ratings.

**Fixed Effects**:
- Salience Level (categorical: Low, Medium, High)
- Scenario ID (as a random effect)
- Participant ID (as a random effect)

**Random Effects**:
- Random intercepts for Participant and Scenario

**Model Formula**:
`blame_rating ~ salience_level + (1 | participant_id) + (1 | scenario_id)`

### Assumptions and Corrections

- **Normality**: Residuals will be checked for normality using the Shapiro-Wilk test. If violated, a robust alternative (e.g., LMM with ordinal link function or non-parametric bootstrap) will be used.
- **Multiple Comparisons**: Bonferroni correction will be applied to the three pairwise comparisons (Low vs. Medium, Medium vs. High, Low vs. High) to control for family-wise error rate.
- **Effect Size**: **Marginal R²** (variance explained by fixed effects) and **Conditional R²** (variance explained by fixed + random effects) will be calculated using the `r2glmm` method. **Partial eta-squared is NOT used as it is inappropriate for LMMs.**
- **Power Analysis**:
  - **A Priori**: A simulation-based power analysis (using `simr` or `statsmodels.stats.power`) will be conducted **before** data collection to determine the required N for a within-subject design with 3 levels. This is a mandatory gate.
  - **Post-hoc**: A post-hoc power analysis will be conducted using the observed effect size. If power < 0.80, it will be flagged as a limitation.

### Data Cleaning

- **Straight-lining**: Participants with variance < 0.1 or >90% identical ratings will be excluded.
- **Missing Data**: Missing responses will be handled by listwise deletion or multiple imputation, depending on the extent of missingness.
- **Precision Threshold**: The 95% confidence interval width for the effect size will be explicitly checked against a **pre-registered** threshold of ≤ 0.3. If the width exceeds this, the result will be flagged as low precision.

## Decision/Rationale

### Dataset Choice

The decision to use **Manual Curation** and **Synthetic Generation** is driven by the need for construct validity. Existing datasets (POPE, RefCOCO) lack the moral narrative required for the study. Manual curation ensures the semantic content is appropriate.

### Statistical Method

The LMM is chosen for its ability to handle nested data structures (participants and scenarios). **Marginal/Conditional R²** are used as effect size metrics because they are the standard for LMMs, unlike partial eta-squared.

### Computational Feasibility

All methods are designed to run on CPU-only infrastructure. Image manipulation will use `Pillow` and `OpenCV`. Statistical analysis will use `statsmodels`. Power analysis will use `simr` or `statsmodels.stats.power`.

## References

- Visual Salience and Moral Judgment: [Citation to be added based on literature review]
- Linear Mixed-Effects Models: [Citation to be added based on literature review]
- Bonferroni Correction: [Citation to be added based on literature review]
- Marginal/Conditional R² for LMMs: Nakagawa & Schielzeth (2013)