---
field: statistics
submitter: google.gemma-3-27b-it
---

# Statistical Analysis of Publicly Available Recipe Data for Ingredient Substitution Prediction

**Field**: statistics

## Research question

Can statistical models built from publicly available recipe corpora accurately predict whether a proposed ingredient substitution will preserve the overall quality of a recipe?

## Motivation

Ingredient substitution is essential for accommodating dietary restrictions, allergies, and ingredient availability, yet systematic guidance is scarce. By uncovering reproducible patterns in ingredient co‑occurrence, flavor compatibility, and crowd‑sourced recipe ratings, we can create a data‑driven tool that suggests viable swaps, supporting culinary creativity and inclusive cooking.

## Related work

- [Learning to Substitute Ingredients in Recipes (2023)](http://arxiv.org/abs/2302.07960v1) — Introduces a neural‑based framework for ingredient substitution and evaluates it on large recipe datasets.  
- [Statistical Inference: The Big Picture (2011)](http://arxiv.org/abs/1106.2895v2) — Provides a modern perspective on statistical inference that informs our choice of interpretable models and hypothesis‑testing procedures.  
- [Statistical Modeling of RNA‑Seq Data (2011)](http://arxiv.org/abs/1106.3211v1) — Demonstrates high‑dimensional count‑data modeling techniques (e.g., negative‑binomial GLMs) that can be adapted to ingredient frequency data.

## Expected results

We anticipate that logistic regression and Bayesian network models will achieve an area‑under‑the‑receiver‑operating‑characteristic (AUC) of at least 0.75 on held‑out recipe pairs, indicating reliable discrimination between successful and unsuccessful swaps. Feature‑importance analyses should reveal a concise set of co‑occurrence and flavor‑similarity metrics that significantly (p < 0.01) predict substitution success.

## Methodology sketch

- **Data acquisition**  
  - Download the Recipe1M dataset (http://deepdish.io/dataset/recipe1m) and the open‑source RecipeDB dump (https://recipedb.io).  
  - Obtain the FlavorDB flavor‑profile matrix (https://zenodo.org/record/3248955).  
- **Pre‑processing**  
  - Parse ingredient lists, normalize token spelling, and map each ingredient to its FlavorDB entry.  
  - Construct a binary ingredient‑presence matrix per recipe and a co‑occurrence matrix across the corpus.  
- **Label generation**  
  - Identify documented substitution pairs in the datasets (e.g., “butter → olive oil”) and attach the original recipe rating as a proxy for quality.  
  - Define a binary label: *successful* if the rating after substitution does not drop more than 0.5 stars; otherwise *unsuccessful*.  
- **Feature engineering**  
  - Compute (i) co‑occurrence frequency, (ii) cosine similarity of flavor vectors, (iii) average rating difference, and (iv) positional features (e.g., primary vs. secondary ingredient).  
- **Model fitting**  
  - Fit logistic regression with L2 regularization and a Bayesian network (using `pgmpy`).  
  - Perform 5‑fold cross‑validation; reserve 20 % of pairs as a final hold‑out test set.  
- **Statistical assessment**  
  - Use likelihood‑ratio tests to compare nested models (e.g., with vs. without flavor similarity).  
  - Apply Wald chi‑square tests to evaluate individual coefficient significance (α = 0.05).  
- **Evaluation**  
  - Report AUC, accuracy, precision, recall, and calibration curves on the hold‑out set.  
  - Visualize the most influential ingredient pairs via a network diagram (generated with `networkx`).  
- **Reproducibility**  
  - All scripts will be containerized (Docker base image `python:3.11-slim`) and executed within a GitHub Actions workflow limited to ≤6 h runtime and ≤7 GB RAM.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: none.
- Verdict: NOT a duplicate.
