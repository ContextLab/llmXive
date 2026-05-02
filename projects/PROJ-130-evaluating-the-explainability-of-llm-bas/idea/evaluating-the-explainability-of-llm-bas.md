---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Explainability of LLM-Based Bug Fixes

**Field**: computer science

## Research question

How well do different explainability techniques (attention visualization, code‑diff saliency maps, and generated natural‑language rationales) reflect the actual correctness and safety of bug fixes suggested by large language models for source‑code defects?

## Motivation

LLMs such as CodeLlama can automatically propose patches for buggy code, but developers often lack insight into *why* a particular edit was suggested, limiting trust and adoption. By systematically evaluating explainability methods against a ground‑truth bug‑fix corpus, we can identify which techniques provide reliable, actionable signals about a model’s reasoning and potential failure modes.

## Related work

- Related work: TODO — lit-search returned no results.

## Expected results

We anticipate that (1) attention‑based visualizations will correlate only weakly with fix correctness, (2) gradient‑based saliency maps over the code diff will show a moderate positive correlation (Spearman ρ ≈ 0.4) with whether the patch passes the test suite, and (3) generated natural‑language rationales that achieve a BLEU score > 30 against human‑written explanations will be the strongest predictor of safe patches (logistic‑regression odds ratio > 2). These findings will be validated using statistical significance testing (p < 0.05) on the Defects4J benchmark.

## Methodology sketch

- **Data acquisition**
  - Download the Defects4J v2.0 dataset (https://github.com/rjust/defects4j) and extract the buggy versions and corresponding test suites.
  - Retrieve the CodeLlama‑7B‑Instruct model weights from HuggingFace (`codellama/CodeLlama-7b-Instruct-hf`).
- **Patch generation**
  - For each bug, prompt the model with the buggy file(s) and the failing test description; collect the generated patch (diff format) using the `transformers` pipeline.
- **Explainability techniques**
  1. **Attention visualization** – extract per‑token attention weights from the model’s last decoder layer for the generated patch; aggregate to file‑level heatmaps.
  2. **Saliency maps** – apply Captum’s Integrated Gradients to the tokenized diff to obtain gradient‑based importance scores for each edited line.
  3. **Natural‑language rationales** – prompt the model to produce a short textual justification for each edit; compute BLEU/ROUGE against the human‑written patch notes provided by Defects4J (if available) or against a manually curated subset.
- **Correctness assessment**
  - Apply each generated patch to the buggy source, run the Defects4J test suite, and record binary pass/fail outcome and any new test failures (unsafe changes).
- **Metric computation**
  - Derive quantitative explainability scores: average attention weight on edited tokens, summed saliency magnitude on edited lines, and rationale similarity (BLEU).
- **Statistical analysis**
  - Compute Spearman correlation between each explainability score and binary correctness.
  - Fit logistic regression models to predict patch correctness from the explainability scores; evaluate via AUC‑ROC.
  - Perform paired t‑tests to compare the predictive power of the three techniques (α = 0.05, Bonferroni‑corrected).
- **Reproducibility**
  - All scripts will be written in Python 3.11, using `transformers`, `datasets`, `captum`, `scikit‑learn`, and `pytest`. The workflow will be orchestrated with a Makefile so that a single GitHub Actions job (≤6 h, ≤7 GB RAM) can run the full pipeline on a representative subset (e.g., 50 bugs) and produce the final analysis notebook.

## Duplicate-check

- Reviewed existing ideas: (none).
- Closest match: none.
- Verdict: NOT a duplicate.
