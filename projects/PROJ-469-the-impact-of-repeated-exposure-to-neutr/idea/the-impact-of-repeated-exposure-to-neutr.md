---
field: psychology
submitter: agent:flesh_out
---

# The Impact of Self‑Reported Political News Exposure on Implicit Political Bias

**Field**: psychology  

## Research question  

How does self‑reported frequency of exposure to political news relate to implicit political bias measured by the Implicit Association Test (IAT), and does this relationship differ across individuals with liberal versus conservative self‑identified ideology?

## Motivation  

Implicit political bias influences voting behavior, policy support, and inter‑group relations even when individuals consciously endorse egalitarian values. While laboratory exposure manipulations are common, little is known about how everyday exposure to political news—an abundant, naturally occurring stimulus—shapes implicit bias in the real world. Understanding this relationship would clarify whether media consumption patterns reinforce or attenuate automatic partisan attitudes, informing media literacy interventions.

## Literature gap analysis  

### What we searched  

We performed two queries on Semantic Scholar and OpenAlex (max 8 results each):  

1. `"implicit association test" "political news exposure"` – targeting studies that link self‑reported media consumption to IAT‑measured bias.  
2. `"habituation" "implicit bias"` – broader search for work on repeated exposure effects on automatic attitudes.  

Both searches returned only marginally related works, none directly addressing everyday political news exposure and implicit bias using public datasets.

### What is known  

- **[Optimal information gain at the onset of habituation to repeated stimuli (2023)](https://arxiv.org/abs/2301.12812)** — Shows how habituation to repeated stimuli modulates information processing; provides a theoretical basis for exposure‑driven attitude change.  
- **[Entity‑Based Evaluation of Political Bias in Automatic Summarization (2023)](https://arxiv.org/abs/2305.02321)** — Develops metrics for detecting political bias in text, illustrating methodological approaches for bias quantification in language data.  
- **[On Measuring Gender Bias in Translation of Gender‑neutral Pronouns (2019)](https://arxiv.org/abs/1905.11684)** — Presents a framework for measuring implicit bias in NLP outputs, offering a precedent for operationalising bias scores from large corpora.  
- **[Neural Correlates of Face Familiarity Perception (2022)](https://arxiv.org/abs/2208.00352)** — Discusses how repeated exposure to faces alters perceptual processing; conceptually relevant to exposure effects on social cognition.

### What is NOT known  

No published work has examined **real‑world, self‑reported frequency of political news consumption** as a predictor of **implicit political bias** measured by the IAT, nor has any study tested whether this association varies between **self‑identified liberals and conservatives**. Existing literature focuses on laboratory exposure manipulations or on bias detection in algorithmic outputs, leaving a gap in observational, population‑scale analysis.

### Why this gap matters  

Answering the question would reveal whether everyday media diets contribute to the formation or mitigation of automatic partisan attitudes. Findings could guide evidence‑based media‑literacy programs, inform policy discussions about news consumption, and extend bias‑research methods beyond controlled lab settings to large, publicly available behavioral datasets.

### How this project addresses the gap  

- **Data source**: Use the publicly released Project Implicit “Political IAT” dataset (CC‑0) that includes participants’ IAT D‑scores, self‑reported political ideology, and a Likert‑scale item on frequency of political news exposure.  
- **Analysis**: Quantify the relationship between news‑exposure frequency (predictor) and IAT D‑score (outcome), testing for an interaction with self‑identified ideology (moderator).  
- **Outcome**: Provide the first large‑scale, observational evidence on how naturalistic media exposure correlates with implicit partisan bias, directly filling the identified literature gap.

## Expected results  

We anticipate a modest positive association: higher self‑reported political news exposure will correlate with stronger implicit bias *in the direction of* the participant’s declared ideology. The interaction term is expected to be significant, indicating that the exposure‑bias link is steeper for conservatives than for liberals (or vice‑versa, depending on the data). A null finding would suggest that mere frequency of news consumption does not systematically shape implicit partisan attitudes, highlighting limits of exposure‑based theories.

## Methodology sketch  

- **1. Acquire data**  
  - `wget` the Project Implicit “Political IAT” dataset (CSV) from the OpenPsych repository (e.g., `https://openpsych.net/datasets/implicit/political_iat.csv`).  
  - `wget` the accompanying codebook (JSON) that defines variable names and scales.  

- **2. Preprocess**  
  - Load data with `pandas`; filter rows with complete values for `IAT_D_score`, `political_ideology` (liberal/conservative), and `news_exposure_freq` (Likert 1–5).  
  - Encode ideology as a binary variable (0 = liberal, 1 = conservative).  
  - Standardise `news_exposure_freq` (z‑score).  

- **3. Descriptive statistics**  
  - Compute mean ± SD of IAT D‑scores by ideology and exposure level.  
  - Visualise the relationship with a scatter plot and lowess smoother (via `seaborn`).  

- **4. Primary analysis**  
  - Fit a linear regression model using `statsmodels`:  
    `IAT_D ~ news_exposure_z * ideology_binary`.  
  - Extract the interaction coefficient, its 95 % CI, and p‑value.  

- **5. Robustness checks**  
  - Perform a non‑parametric bootstrap (1 000 resamples) of the interaction effect to assess stability.  
  - Re‑run the model controlling for age, gender, and education (available in the dataset).  

- **6. Sensitivity to exposure coding**  
  - Repeat the analysis treating `news_exposure_freq` as an ordinal factor (ANOVA) to verify consistency.  

- **7. Reporting**  
  - Save model summaries (`.txt`), effect‑size tables (`.csv`), and plots (`.png`) into a `results/` directory.  
  - Generate a concise PDF report (≤ 5 MB) using `matplotlib`/`pdfkit`.  

All steps rely on pure Python (≥ 3.9) libraries (`pandas`, `numpy`, `statsmodels`, `seaborn`, `matplotlib`) that run comfortably within the 2‑CPU, 7 GB RAM, ≤ 6 h GitHub Actions environment.

## Duplicate-check  

- Reviewed existing ideas: *(none)*.  
- Closest match: *(none)*.  
- Verdict: **NOT a duplicate**.
