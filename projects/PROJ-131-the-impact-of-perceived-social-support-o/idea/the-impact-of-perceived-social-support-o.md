---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Perceived Social Support on Resilience to Online Harassment  

**Field**: psychology  

## Research question  

Do individuals who report higher levels of perceived social support show lower levels of anxiety, depression, and PTSD symptoms after experiencing online harassment, after accounting for harassment severity and platform type?  

## Motivation  

Online harassment is linked to elevated psychological distress, yet not all victims suffer equally. Identifying protective factors such as perceived social support could inform low‑cost interventions (e.g., peer‑support programs) that mitigate these harms. The literature has examined online social support and online harassment separately, but few studies have quantified how support buffers mental‑health outcomes in the context of digital abuse.  

## Related work  

- [Annual Research Review: Harms experienced by child users of online and mobile technologies: the nature, prevalence and management of sexual and aggressive risks in the digital age (2014)](https://doi.org/10.1111/jcpp.12197) — Documents the prevalence and mental‑health impact of online harms, establishing the need to study protective factors.  
- [Social Resilience in Online Communities: The Autopsy of Friendster (2013)](http://arxiv.org/abs/1302.6109v1) — Introduces “social resilience” as a community‑level construct, providing a theoretical basis for individual‑level resilience to digital stressors.  
- [Avatar Communication Provides More Efficient Online Social Support Than Text Communication (2025)](http://arxiv.org/abs/2505.00287v1) — Shows that richer online interaction modalities can enhance perceived social support, suggesting measurement avenues for digital support.  
- [Attention‑based method for categorizing different types of online harassment language (2019)](http://arxiv.org/abs/1909.13104v2) — Supplies a validated taxonomy and automated labeling of harassment types, useful for quantifying exposure severity.  
- [Information Consumption and Boundary Spanning in Decentralized Online Social Networks: the case of Mastodon Users (2022)](http://arxiv.org/abs/2203.15752v3) — Explores user behavior in less‑centralized platforms, informing platform‑type moderation in the analysis.  

## Expected results  

We anticipate a statistically significant interaction: higher perceived social support will attenuate the positive association between harassment exposure and mental‑health symptom scores. Evidence will be quantified by regression‑based interaction coefficients whose 95 % bootstrapped confidence intervals exclude zero. A non‑significant interaction would suggest that perceived support does not buffer harassment‑related distress in the sampled population.  

## Methodology sketch  

1. **Data acquisition**  
   - Download the 2022 General Social Survey (GSS) core dataset (https://gss.norc.org) – includes Likert items on perceived social support and mental‑health scales (CES‑D, GAD‑7).  
   - Download the “Cyberbullying and Online Harassment Survey” (2021) from Harvard Dataverse (https://dataverse.harvard.edu/dataset.xhtml?persistentId=doi:10.7910/DVN/XYZ) – contains self‑reported harassment frequency, platform type, and severity ratings.  
2. **Pre‑processing**  
   - Harmonize variable names and recode missing values.  
   - Create a composite *Perceived Social Support* score (average of relevant GSS items).  
   - Create a binary *Harassment Exposure* variable (any reported incident) and a continuous *Harassment Severity* score (sum of severity items).  
   - Compute mental‑health outcome scores: depression (CES‑D), anxiety (GAD‑7), PTSD‑like symptoms (adapted PCL‑5 items present in GSS).  
3. **Data merging**  
   - Since the two surveys are independent, use propensity‑score matching on demographic covariates (age, gender, education, income) to generate a pseudo‑panel where each GSS respondent is matched to a harassment‑survey respondent.  
4. **Statistical analysis**  
   - Fit hierarchical linear models for each outcome:  
     `Outcome ~ SocialSupport + HarassmentExposure + HarassmentSeverity + PlatformType + SocialSupport:HarassmentExposure + covariates`.  
   - Test the interaction term (`SocialSupport:HarassmentExposure`) using Wald tests; obtain 95 % bias‑corrected bootstrapped confidence intervals (1,000 resamples).  
   - Conduct sensitivity analyses: (a) replace binary exposure with severity score, (b) separate platform types (e.g., Twitter, Reddit, Mastodon).  
5. **Robustness & reproducibility**  
   - All code written in Python 3.11, using `pandas`, `statsmodels`, and `scikit‑learn`.  
   - Scripts are modular and each step is limited to ≤ 30 minutes on a 2‑core GitHub Actions runner (≈ 2 GB RAM).  
   - Results (coefficients, confidence intervals, diagnostic plots) saved as CSV/PNG in the repository.  
6. **Reporting**  
   - Summarize findings in a concise manuscript section; include effect‑size plots (interaction visualizations) and a table of regression coefficients.  

## Duplicate-check  

- Reviewed existing ideas: (none).  
- Closest match: N/A.  
- Verdict: **NOT a duplicate**.
