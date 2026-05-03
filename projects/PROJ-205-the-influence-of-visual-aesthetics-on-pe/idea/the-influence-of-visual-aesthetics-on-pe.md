---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Visual Aesthetics on Perceived Credibility of Online Information

**Field**: psychology

## Research question

Do visual‑aesthetic qualities of a webpage (color scheme, typography, image quality, layout simplicity) systematically affect users’ perceived credibility of the information presented, when the textual content is held constant?

## Motivation

Misinformation spreads rapidly online, yet credibility judgments are often driven by superficial cues rather than content quality. Identifying how design elements bias trust can inform guidelines for responsible information design and help mitigate the persuasive power of deceptive sites.

## Related work

- [Parasocial interactions with real and virtual influencers: The role of perceived similarity and human‑likeness (2022)](https://doi.org/10.1177/14614448221102900) — Shows that visual and perceived similarity cues shape trust toward digitally created agents, suggesting that aesthetic presentation can influence credibility judgments.

## Expected results

We anticipate that webpages adhering to professional design principles (high‑resolution images, harmonious colour palettes, clean layout, consistent typography) will receive higher credibility ratings than minimalist or deliberately “low‑quality” designs, despite identical article text. A statistically significant difference (p < 0.05) between design conditions on average Likert scores would support the hypothesis; a null finding would falsify it.

## Methodology sketch

1. **Select source article** – Choose a neutral news article (≈300 words) from a public domain source (e.g., Wikipedia or the Common Crawl).  
2. **Create visual templates** – Build 4 HTML/CSS templates representing distinct aesthetic levels:  
   - *Professional*: balanced colour scheme, serif heading + sans‑serif body, high‑resolution stock images (Unsplash, CC‑BY).  
   - *Modern minimalist*: monochrome palette, large whitespace, minimal imagery.  
   - *Low‑quality*: clashing colours, inconsistent fonts, pixelated images (down‑sampled).  
   - *Neutral baseline*: default browser styling.  
   Store templates in a public GitHub repo for reproducible download (`wget`).
3. **Generate stimuli** – Render each template with the same article text, producing 4 stimulus webpages. Host them temporarily on GitHub Pages or a static file server.
4. **Recruit participants** – Use Prolific (or MTurk) to obtain N = 250 adult participants (balanced gender, age 18‑65). Provide a link to a Qualtrics/Google Forms survey that randomizes presentation order of the 4 designs per participant (Latin square).
5. **Collect responses** – For each page, ask participants to rate perceived credibility on a 7‑point Likert scale and to indicate perceived professionalism (1‑7). Record timestamps and device/browser info.
6. **Data preprocessing** – Export CSV, remove incomplete entries (<80 % completion), check for duplicate IPs, and standardize Likert scores.
7. **Statistical analysis** –  
   - Perform a repeated‑measures ANOVA with *design condition* as within‑subject factor on credibility ratings.  
   - Follow up with pairwise Bonferroni‑corrected t‑tests to locate specific differences.  
   - Compute effect sizes (η²) and Bayesian Information Criterion (BIC) for model comparison.  
8. **Robustness checks** – Include participant‑level covariates (age, education) in a mixed‑effects model to verify that effects persist after controlling for demographics.
9. **Reporting** – Generate summary figures (boxplots, raincloud plots) using `matplotlib`/`seaborn`; all code and analysis scripts will be placed in a reproducible `R`/`Python` notebook that can run on a GitHub Actions runner within 6 hours (data < 5 MB, model‑free analysis).

## Duplicate-check

- Reviewed existing ideas: *(none provided)*.  
- Closest match: None.  
- Verdict: NOT a duplicate.
