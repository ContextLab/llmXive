---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Efficacy of Code Summarization Techniques for Bug Localization

**Field**: computer science

## Research question

Do automatically generated code summaries improve the speed and accuracy with which developers can locate bugs compared to using raw source code alone?

## Motivation

Bug localization remains a bottleneck in large codebases, especially when functions lack clear documentation. Recent advances in code summarization—particularly large‑language‑model (LLM) based approaches—offer a potential shortcut to understanding code intent. Quantifying their impact on developer performance can guide tool‑building decisions and prioritize research on summarization quality.

## Related work

- [WELL: Applying Bug Detectors to Bug Localization via Weakly Supervised Learning (2023)](http://arxiv.org/abs/2305.17384v2) — Introduces weakly supervised learning to boost bug‑localization performance, highlighting the importance of auxiliary signals such as code semantics.  
- [BoostNSift: A Query Boosting and Code Sifting Technique for Method Level Bug Localization (2021)](http://arxiv.org/abs/2108.12901v1) — Proposes query‑boosting and code‑sifting to improve IR‑based bug localization, providing a baseline for measuring added value of summaries.  
- [Software testing and analysis: process, principles, and techniques (2008)](https://doi.org/10.5860/choice.46-0935) — Offers a broad overview of software testing methods, including manual bug‑localization workflows that serve as a reference point for human‑performance measurements.

## Expected results

We anticipate that participants using high‑quality LLM‑generated summaries will locate buggy lines faster (≥15 % reduction in median search time) while maintaining or improving precision (≥5 % increase in correct‑first‑line identification). A statistically significant difference (paired Wilcoxon signed‑rank test, *p* < 0.05) between summary‑assisted and baseline conditions would confirm the hypothesis; a non‑significant result would falsify it.

## Methodology sketch

1. **Select benchmark bugs**  
   - Download the Defects4J v2.0 dataset (https://github.com/rjust/defects4j) and extract a stratified sample of 60 buggy methods across Java projects (e.g., *Chart*, *Time*, *Math*).  
2. **Generate code summaries**  
   - For each buggy method, produce three variants: (a) no summary (baseline), (b) summary from an open‑source LLM (e.g., CodeLlama‑7B via HuggingFace `codellama/CodeLlama-7b-hf`), (c) summary from a rule‑based tool (e.g., *srcML* comment extractor).  
   - Store summaries as plain text files; keep the original method source unchanged.  
3. **Prepare bug reports**  
   - Use the official Defects4J bug reports (text files) that describe the observed failure.  
4. **Human subject study**  
   - Recruit 12 graduate‑level software engineering students (remote via a secure web form).  
   - Randomly assign each participant a balanced set of 30 tasks (10 per summary condition) using a Latin‑square design to control order effects.  
   - For each task, present the bug report plus either the raw method or the method with its generated summary; participants click the line they believe contains the bug. Record time from display to click.  
5. **Data collection**  
   - Store timestamps, selected line numbers, and participant IDs in a CSV file.  
6. **Evaluation metrics**  
   - *Accuracy*: proportion of tasks where the selected line matches the ground‑truth buggy line (from Defects4J).  
   - *Speed*: median time‑to‑decision per condition.  
7. **Statistical analysis**  
   - Perform paired Wilcoxon signed‑rank tests comparing (a) baseline vs. LLM summary and (b) baseline vs. rule‑based summary for both accuracy and speed.  
   - Compute effect sizes (r) and 95 % confidence intervals via bootstrapping (1 000 resamples).  
8. **Reproducibility package**  
   - Publish all scripts (Python 3.11, `pandas`, `scikit-learn`, `requests`) and the anonymized interaction logs on an OSF repository, with a `README` detailing how to rerun the analysis within a GitHub Actions job (<6 h runtime, ≤4 GB RAM).

## Duplicate-check

- Reviewed existing ideas: none.
- Closest match: none.
- Verdict: NOT a duplicate.
