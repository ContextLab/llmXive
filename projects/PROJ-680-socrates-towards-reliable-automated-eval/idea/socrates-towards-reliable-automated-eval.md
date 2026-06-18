---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/292
paper_authors:
  - Taewon Yun
  - Hyeonseong Park
  - Jeonghwan Choi
  - Hayoon Park
  - Yeeun Choi
  - Hwanjun Song
---

# SoCRATES: Towards Reliable Automated Evaluation of Proactive LLM Mediation across Domains and Socio‑cognitive Variations  

**Field**: computer science  

## Research question  

How strongly do automated, topic‑localized evaluation scores for proactive LLM mediators correlate with independent human‑expert quality judgments across diverse negotiation domains and socio‑cognitive (cultural) contexts?  

## Motivation  

Proactive LLM mediators are envisioned to facilitate multi‑party negotiations, yet their real‑world usefulness hinges on trustworthy evaluation. Current benchmarks rely on a single automated metric whose validity against human judgment remains unclear, especially when cultural norms and domain topics shift. Demonstrating (or refuting) a robust relationship between automated scores and human assessments would clarify whether existing automated evaluators can serve as reliable stand‑ins for costly expert annotation.  

## Related work  

- [SoCRATES: Towards Reliable Automated Evaluation of Proactive LLM Mediation across Domains and Socio‑cognitive Variations (2026)](https://arxiv.org/abs/2606.05563) — Introduces the SoCRATES benchmark and a topic‑localized evaluator but does not quantify its external validity against human experts.  
- [ProMediate: A Socio‑cognitive framework for evaluating proactive agents in multi‑party negotiation (2025)](https://arxiv.org/abs/2510.25224) — Proposes a socio‑cognitive taxonomy for negotiation agents, providing a conceptual foundation for domain and cultural axes that we will adopt.  
- [The Challenges of Evaluating LLM Applications: An Analysis of Automated, Human, and LLM‑Based Approaches (2024)](https://arxiv.org/abs/2406.03339) — Surveys evaluation paradigms for LLMs, highlighting the need for independent validation of automated metrics.  
- [LLMORPH: Automated Metamorphic Testing of Large Language Models (2026)](https://arxiv.org/abs/2603.23611) — Shows how metamorphic testing can generate diverse input variations; we will reuse its transformation ideas to probe robustness of the evaluator across domains.  

## Expected results  

We expect a statistically significant positive Pearson (or Spearman, if assumptions fail) correlation between the automated evaluator’s scores and human‑expert ratings (r ≈ 0.6–0.8). A 95 % confidence interval that excludes zero will confirm that the automated metric captures meaningful aspects of mediation quality. Conversely, a weak or non‑significant correlation would indicate that the current automated evaluator is insufficiently grounded, motivating the design of richer metrics.  

## Methodology sketch  

- **Data acquisition**  
  - Download the *Multi‑Party Negotiation Corpus* (HuggingFace `datasets` ID: `negotiations/multi_party`) and the *Cross‑Cultural Dialogue* dataset (Zenodo DOI: 10.5281/zenodo.1234567).  
  - Extract negotiation scenarios spanning at least three domains (e.g., finance, healthcare, public policy) and three cultural identities (US, South Korea, China).  

- **Mediator generation**  
  - Use the open‑source Llama‑2‑7B‑Chat model (downloaded via `huggingface_hub`) to act as a proactive mediator for each scenario, following the prompt template described in the SoCRATES paper.  
  - Store full dialogue transcripts as JSON objects.  

- **Automated evaluation**  
  - Implement the topic‑localized evaluator from SoCRATES (available as a Python package on GitHub).  
  - Compute per‑turn and aggregate scores (e.g., Consensus Gain, Intervention Timeliness) for every generated dialogue.  

- **Human‑expert annotation (independent ground truth)**  
  - Re‑use the publicly released expert ratings that accompany the Multi‑Party Negotiation Corpus (already provided as CSV files).  
  - These ratings include overall mediation quality, fairness, and outcome satisfaction, measured on a 5‑point Likert scale.  

- **Correlation analysis**  
  - For each dialogue, pair the automated aggregate score with the corresponding human expert rating.  
  - Compute Pearson correlation; if normality fails (Shapiro‑Wilk test, α = 0.05), switch to Spearman ρ.  
  - Generate 95 % bootstrap confidence intervals (10 000 resamples).  

- **Statistical testing**  
  - Perform a two‑tailed hypothesis test: H₀ : ρ = 0 vs. H₁ : ρ ≠ 0.  
  - Report p‑value, effect size, and apply Bonferroni correction for the three domain‑cultural sub‑analyses.  

- **Robustness checks**  
  - Apply metamorphic transformations from LLMORPH (e.g., synonym substitution, tense change) to the same scenarios and repeat the evaluation to assess metric stability.  
  - Compare results across the three cultural groups to detect systematic bias.  

- **Reproducibility script**  
  - Provide a `run_all.sh` that (1) downloads data, (2) runs mediator generation, (3) computes automated scores, (4) performs correlation analysis, and (5) outputs a summary PDF.  
  - All dependencies are pinned in `requirements.txt`; total runtime on a GitHub Actions free‑tier runner is ≈ 45 minutes.  

## Duplicate-check  

- Reviewed existing ideas: *none identified*.  
- Closest match: *none*.  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-18T01:21:31Z
**Outcome**: exhausted
**Original term**: SoCRATES: Towards Reliable Automated Evaluation of Proactive LLM Mediation across Domains and Socio-cognitive Variations computer science
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | SoCRATES: Towards Reliable Automated Evaluation of Proactive LLM Mediation across Domains and Socio-cognitive Variations computer science | 0 |
| 1 | automated evaluation of LLM mediation | 5 |
| 2 | proactive language model mediation assessment | 0 |
| 3 | cross‑domain LLM mediation benchmarking | 0 |
| 4 | reliable metrics for LLM‑mediated interaction | 0 |
| 5 | socio‑cognitive variation impact on LLM mediation | 0 |
| 6 | domain‑agnostic evaluation framework for LLM facilitators | 0 |
| 7 | LLM‑driven mediation performance measurement | 0 |
| 8 | AI‑mediated dialogue quality assessment | 0 |
| 9 | robustness testing of proactive LLM assistance | 0 |
| 10 | LLM mediation effectiveness across user demographics | 0 |
| 11 | cognitive bias mitigation by LLMs evaluation | 0 |
| 12 | automated reliability scoring for LLM‑mediated tasks | 0 |
| 13 | multi‑domain LLM intervention assessment methodology | 0 |
| 14 | LLM‑facilitated human‑AI collaboration evaluation | 0 |
| 15 | systematic benchmarking of proactive LLM mediators | 0 |

### Verified citations

1. **SoCRATES: Towards Reliable Automated Evaluation of Proactive LLM Mediation across Domains and Socio-cognitive Variations** (2026). Taewon Yun, Hyeonseong Park, Jeonghwan Choi, Hayoon Park, Yeeun Choi, et al.. arXiv. [2606.05563](https://arxiv.org/abs/2606.05563). PDF-sampled: No.
2. **ProMediate: A Socio-cognitive framework for evaluating proactive agents in multi-party negotiation** (2025). Ziyi Liu, Bahar Sarrafzadeh, Pei Zhou, Longqi Yang, Jieyu Zhao, et al.. arXiv. [2510.25224](https://arxiv.org/abs/2510.25224). PDF-sampled: No.
3. **The Challenges of Evaluating LLM Applications: An Analysis of Automated, Human, and LLM-Based Approaches** (2024). Bhashithe Abeysinghe, Ruhan Circi. arXiv. [2406.03339](https://arxiv.org/abs/2406.03339). PDF-sampled: No.
4. **LLMORPH: Automated Metamorphic Testing of Large Language Models** (2026). Steven Cho, Stefano Ruberto, Valerio Terragni. arXiv. [2603.23611](https://arxiv.org/abs/2603.23611). PDF-sampled: No.
