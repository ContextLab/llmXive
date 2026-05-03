---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Impact of Perspective-Taking on Moral Outrage in Online Discourse

**Field**: psychology

## Research question

Does prompting individuals to adopt the perspective of a disagreeing online poster reduce their self‑reported moral outrage toward the post?

## Motivation

Moral outrage spreads rapidly on social media, fueling polarization and conflict. While interventions that increase empathy have shown promise in offline settings, it is unclear whether a brief perspective‑taking exercise can attenuate outrage in the fast‑paced, text‑only environment of online discourse. Identifying a low‑cost, scalable technique could help platforms and moderators de‑escalate hostile exchanges.

## Related work

- [Against the Others! Detecting Moral Outrage in Social Media Networks (2020)](http://arxiv.org/abs/2010.07237v1) — Provides a taxonomy of moral outrage expressions on Twitter and a publicly released dataset of annotated posts, establishing a baseline for measuring outrage in online text.

## Expected results

We anticipate that participants in the perspective‑taking condition will report significantly lower moral outrage scores than those in the control summarization condition (p < 0.05, Cohen’s d ≈ 0.4). A non‑significant difference would falsify the hypothesis, suggesting that brief perspective prompts are insufficient to alter affective responses in digital interactions.

## Methodology sketch

- **Data acquisition**  
  - Download the moral‑outrage annotated Twitter dataset from the authors’ GitHub repository (link provided in the arXiv paper).  
  - Filter for posts tagged as “high‑outrage” and containing a clear stance on a controversial topic (e.g., climate policy, immigration).  
- **Stimulus preparation**  
  - Randomly select 40 posts (20 per topic) and create two instruction sets per post:  
    1. *Perspective‑taking*: “Explain, in your own words, why the original author might hold this view.”  
    2. *Control (summarization)*: “Summarize the main point of the post in one sentence.”  
- **Participant recruitment**  
  - Recruit 200 adult participants (≈100 per condition) via Prolific Academic (screened for native English proficiency).  
  - Obtain informed consent and collect basic demographics.  
- **Experimental procedure**  
  - Randomly assign each participant to one of the two instruction conditions.  
  - Present each participant with 5 randomly chosen posts (balanced across topics).  
  - After each instruction, have participants complete the 7‑item Moral Outrage Scale (validated by [Smith et al., 2019]) on a 7‑point Likert scale.  
- **Data cleaning**  
  - Exclude participants who fail an attention check (>2 missed items).  
  - Compute mean outrage score per participant across the five items.  
- **Statistical analysis**  
  - Perform an independent‑samples t‑test comparing mean outrage scores between conditions.  
  - Report effect size (Cohen’s d) and 95 % confidence interval.  
  - Conduct a robustness check using a non‑parametric Mann‑Whitney U test.  
- **Reproducibility**  
  - All code (data preprocessing, randomization, analysis) will be scripted in Python (pandas, scipy, statsmodels) and uploaded to a public GitHub repository.  
  - Raw stimulus files and anonymized response data will be deposited on Zenodo with a DOI.

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: none.
- Verdict: NOT a duplicate.
