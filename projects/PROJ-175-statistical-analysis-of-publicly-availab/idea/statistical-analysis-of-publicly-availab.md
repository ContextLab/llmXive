---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Field**: statistics

## Research question

To what extent do flavor-profile similarity and ingredient functional role predict the culinary compatibility of ingredient pairs, as measured by independent sensory evaluation scores, after statistically controlling for their historical co-occurrence frequency in the Recipe1M corpus?

## Motivation

Ingredient substitution is critical for dietary adaptation and allergy management, yet current data-driven tools often rely on opaque neural models or simple co-occurrence heuristics that conflate frequency with genuine compatibility. By statistically isolating the contributions of flavor chemistry and functional role from raw frequency, this project addresses a gap in interpretable culinary science, providing evidence-based guidelines for when a substitution will succeed regardless of historical recipe popularity.

## Related work

- [Learning to Substitute Ingredients in Recipes](https://arxiv.org/abs/2302.07960) — Establishes a neural baseline for substitution tasks, highlighting the need for interpretable statistical factors beyond deep learning black boxes.
- [The networks of ingredient combinations as culinary fingerprints of world cuisines](https://arxiv.org/abs/2408.15162) — Demonstrates that ingredient co-occurrence networks capture cultural culinary patterns, providing the statistical foundation for controlling frequency in our model.
- [Counterfactual Recipe Generation: Exploring Compositional Generalization in a Realistic Scenario](https://arxiv.org/abs/2210.11431) — Investigates how models handle novel ingredient combinations, supporting our focus on predicting compatibility for pairs with lower historical co-occurrence.

## Expected results

We expect flavor-profile similarity and functional role to remain significant predictors of culinary compatibility (p < 0.05) even after controlling for co-occurrence frequency, likely increasing the model's AUC by at least 0.05 over a frequency-only baseline. The analysis will reveal that high-frequency co-occurrence is a necessary but insufficient condition for successful substitution, with flavor chemistry acting as the primary differentiator for novel pairings.

## Methodology sketch

- **Data acquisition**
  - Download the Recipe1M dataset from HuggingFace (`deepdish/recipe1m`) or a verified mirror to ensure reproducibility within the GitHub Actions environment.
  - Download the FlavorDB flavor-profile matrix from Zenodo (`10.5281/zenodo.3248955`) to map ingredients to chemical compound vectors.
- **Pre-processing**
  - Parse ingredient lists from Recipe1M, normalize entity names (e.g., mapping "butter" and "unsalted butter" to a canonical ID), and map to FlavorDB chemical profiles.
  - Construct a global co-occurrence matrix $C$ where $C_{ij}$ is the log-transformed count of recipes containing both ingredients $i$ and $j$.
- **Label generation (Independent Validation)**
  - Identify candidate substitution pairs from the "Counterfactual Recipe Generation" dataset where a specific ingredient was swapped.
  - Define *culinary compatibility* as a binary label derived from **independent sensory evaluation scores** or **crowd-sourced preference ratings** provided in the evaluation split of the counterfactual dataset, ensuring this label source is distinct from the co-occurrence counts used as predictors.
  - *Constraint Check*: The label (sensory score) is measured independently of the predictor (co-occurrence frequency) to avoid circular validation.
- **Feature engineering**
  - **Co-occurrence frequency**: Log-transformed $C_{ij}$ to reduce skew.
  - **Flavor similarity**: Cosine similarity between the chemical vector profiles of ingredients $i$ and $j$ from FlavorDB.
  - **Functional role**: Categorical encoding (primary, secondary, garnish) derived from ingredient position and frequency in the recipe corpus.
- **Model fitting**
  - Fit a regularized logistic regression model where the dependent variable is the binary compatibility label and independent variables are flavor similarity, functional role, and co-occurrence frequency.
  - Fit a hierarchical Bayesian model to estimate the posterior distribution of the effect sizes for each predictor.
- **Statistical assessment**
  - Perform likelihood-ratio tests comparing a full model (all predictors) against a null model (co-occurrence only) to quantify the independent explanatory power of flavor and role.
  - Calculate Variance Inflation Factors (VIF) to ensure predictors are not collinear.
  - Conduct 5-fold cross-validation to estimate generalization error.
- **Evaluation**
  - Report AUC, precision, recall, and calibration plots on a held-out test set.
  - Generate a coefficient plot to visualize the magnitude and direction of each factor's influence.
- **Reproducibility & runtime**
  - Execute all steps in a single GitHub Actions job using Python 3.11.
  - Ensure memory usage stays under 7GB by streaming data processing and downsampling the Recipe1M corpus if necessary.
  - Total runtime target: < 4 hours.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: none.
- Verdict: NOT a duplicate.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-05T01:14:52Z
**Outcome**: exhausted
**Original term**: Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction statistics
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction statistics | 3 |

### Verified citations

1. **Learning to Substitute Ingredients in Recipes** (2023). Bahare Fatemi, Quentin Duval, Rohit Girdhar, Michal Drozdzal, Adriana Romero-Soriano. arXiv. [2302.07960](https://arxiv.org/abs/2302.07960). PDF-sampled: No.
2. **The networks of ingredient combinations as culinary fingerprints of world cuisines** (2024). Claudio Caprioli, Saumitra Kulkarni, Federico Battiston, Iacopo Iacopini, Andrea Santoro, et al.. arXiv. [2408.15162](https://arxiv.org/abs/2408.15162). PDF-sampled: No.
3. **Counterfactual Recipe Generation: Exploring Compositional Generalization in a Realistic Scenario** (2022). Xiao Liu, Yansong Feng, Jizhi Tang, Chengang Hu, Dongyan Zhao. arXiv. [2210.11431](https://arxiv.org/abs/2210.11431). PDF-sampled: No.
