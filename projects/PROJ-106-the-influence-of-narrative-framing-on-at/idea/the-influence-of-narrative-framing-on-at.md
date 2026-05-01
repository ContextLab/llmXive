---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Narrative Framing on Attitudes Towards AI Assistance

**Field**: psychology

## Research question

Does framing large‑language‑model assistance as a “collaborative partner” versus an “automated tool” lead to more positive attitudes, higher perceived usefulness, and greater trust among lay users?

## Motivation

Understanding how narrative framing shapes public acceptance of AI is crucial for responsible deployment of LLM‑based assistants in education, health, and workplace settings. Existing work shows that subtle wording can sway risk perception and technology adoption, yet little is known about the specific impact of partnership versus tool framing for LLMs. Filling this gap will inform designers and policymakers on how to communicate AI capabilities without unintentionally eroding trust.

## Related work

- [OATH-Frames: Characterizing Online Attitudes Towards Homelessness with LLM Assistants (2024)](http://arxiv.org/abs/2406.14883v2) — Demonstrates that LLM‑generated narratives can be used to gauge public attitudes toward socially salient topics, illustrating the relevance of framing effects in LLM‑mediated communication.  
- [From Influencers to Lecturers: Understanding Public Attitudes Toward Digital vs. Traditional Jobs (2023)](http://arxiv.org/abs/2309.12885v2) — Examines how descriptive framing of digital occupations influences public sentiment, providing a methodological template for measuring attitude shifts caused by framing.

## Expected results

We anticipate that participants exposed to the “collaborative partner” framing will report significantly higher scores on attitude, perceived usefulness, and trust scales (Cohen’s d ≈ 0.4–0.6). A non‑significant difference would falsify the hypothesis, indicating that framing alone does not drive attitudinal change. Evidence will be based on between‑group t‑tests (α = 0.05) with a target sample size of N ≈ 300 (150 per condition) to achieve 80 % power.

## Methodology sketch

- **Stimulus creation**: Write two short vignettes (≈150 words each) describing the same AI‑assisted task (e.g., drafting an email). One vignette uses “collaborative partner” language; the other uses “automated tool” language. Pre‑test wording on a small pilot (n = 20) to ensure comparable readability (Flesch‑Kincaid) and length.  
- **Survey platform**: Deploy the experiment on Qualtrics (free tier) or Google Forms; embed a randomization script (JavaScript) that assigns participants to one of the two framing conditions.  
- **Participant recruitment**: Use Prolific Academic (or Amazon MTurk) to recruit a diverse adult sample (age 18‑65, English‑speaking). Set inclusion criteria: no prior professional AI experience.  
- **Data collection**: Collect responses to (a) the attitude scale (7‑item Likert), (b) perceived usefulness (3‑item), (c) trust in AI (4‑item), and (d) manipulation check (“The AI was described as a …”). Export data as CSV via the platform’s API.  
- **Language analysis (optional)**: Download the Sentiment140 dataset (https://github.com/kavgan/sentiment140) to compute baseline sentiment scores for the vignette texts, confirming that framing does not unintentionally alter overall valence.  
- **Statistical analysis**: In Python (pandas, scipy, statsmodels) perform: (i) manipulation‑check verification (χ²), (ii) independent‑samples t‑tests (or Welch’s correction) on each dependent variable, (iii) compute effect sizes (Cohen’s d) and 95 % confidence intervals.  
- **Robustness checks**: Run a non‑parametric Mann‑Whitney U test and a simple linear regression controlling for age, gender, and prior AI exposure.  
- **Reproducibility**: Store all scripts, raw CSVs, and analysis notebooks in a public GitHub repository; use a `requirements.txt` to pin package versions (≤ 7 GB RAM, ≤ 30 min per step).  

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: N/A (no similar fleshed‑out idea found).
- Verdict: NOT a duplicate.
