---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Style on LLM Code Understanding and Generation  

**Field**: computer science  

## Research question  

How do systematic variations in code style—formatting, naming conventions, and commenting—affect the performance of large language models on code‑understanding and code‑generation tasks such as completion, bug detection, and summarization?  

## Motivation  

LLMs are increasingly deployed as coding assistants (e.g., GitHub Copilot, ChatGPT) and developers rely on them for productivity gains. While many studies benchmark raw model capability, little is known about whether stylistic choices in source code influence those capabilities. Identifying any style‑sensitivity would (i) inform best‑practice guidelines for writing “LLM‑friendly” code, and (ii) reveal potential biases that could affect code quality, maintainability, and fairness in educational settings.  

## Related work  

- [SIMCOPILOT: Evaluating Large Language Models for Copilot-Style Code Generation (2025)](http://arxiv.org/abs/2505.21514v1) — introduces a benchmark for measuring LLM performance on interactive code‑completion tasks, providing a suitable evaluation framework for our completion experiments.  
- [Evaluating Code Generation of LLMs in Advanced Computer Science Problems (2025)](http://arxiv.org/abs/2504.14964v1) — studies LLM effectiveness on complex programming problems, highlighting the need to control for extraneous factors such as code presentation when interpreting results.  
- [A Style is Worth One Code: Unlocking Code-to-Style Image Generation with Discrete Style Space (2025)](http://arxiv.org/abs/2511.10555v5) — presents techniques for representing and manipulating code style, which we adapt to generate systematic style variants of a base code corpus.  
- [ChatGPT for Education and Research: Opportunities, Threats, and Strategies (2023)](https://doi.org/10.3390/app13095783) — discusses the impact of LLMs in learning environments, underscoring why understanding style effects matters for students and educators alike.  

## Expected results  

We anticipate measurable performance gaps across style dimensions: (1) code formatted according to PEP 8 and enriched with clear comments will yield higher exact‑match and CodeBLEU scores on completion, (2) descriptive identifiers will improve bug‑detection precision, and (3) the presence of docstrings will boost ROUGE/L‑BLEU for summarization. Effect sizes will be quantified with confidence intervals; non‑significant differences will suggest robustness of LLMs to certain stylistic variations.  

## Methodology sketch  

- **Data acquisition**  
  - Download the Python subset of the CodeSearchNet dataset via HuggingFace (`datasets.load_dataset("code_search_net", "python")`).  
  - Select ~5 k functions that compile and have existing docstrings.  

- **Style transformation pipeline** (all scripts run on the CI runner)  
  1. **Formatting**: apply `black` (PEP 8‑compliant) vs. a minified formatter that removes whitespace.  
  2. **Naming**: replace identifiers with either meaningful English words (using a word‑frequency list) or short generic tokens (`var1`, `func2`).  
  3. **Commenting**: retain original comments/docstrings vs. strip all comments.  

  - Combine factors orthogonally to produce a full factorial set (2 × 2 × 2 = 8 style variants per function).  

- **Task definitions**  
  - **Code completion**: mask the last line of each function; ask the LLM to generate it.  
  - **Bug detection**: inject a single syntactic or logical bug (e.g., off‑by‑one) into a copy of each variant; ask the LLM to label “buggy” vs. “clean”.  
  - **Summarization**: prompt the LLM to produce a one‑sentence description of the function’s purpose.  

- **Model evaluation**  
  - Use the open‑source `codegen-2b` model via the HuggingFace `transformers` pipeline (CPU‑only).  
  - For each task, compute:  
    - Exact match & CodeBLEU for completion.  
    - Precision/recall/F1 for bug detection.  
    - ROUGE‑L and BLEU for summarization.  

- **Statistical analysis**  
  - Fit a mixed‑effects ANOVA with fixed effects for the three style factors and random intercepts for the original function ID.  
  - Report p‑values, η² effect sizes, and post‑hoc pairwise comparisons (Bonferroni‑corrected).  

- **Reproducibility**  
  - All code and configuration will be version‑controlled.  
  - Results (metrics CSV, plots) will be saved under `results/` and uploaded as GitHub Action artifacts.  

## Duplicate-check  

- Reviewed existing ideas: none.  
- Closest match: N/A (no similar fleshed‑out idea found).  
- Verdict: **NOT a duplicate**.
