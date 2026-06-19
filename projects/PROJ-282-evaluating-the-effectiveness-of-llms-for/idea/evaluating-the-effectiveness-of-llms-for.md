---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code

**Field**: computer science

## Research question

What structural and semantic features in open-source code are most predictive of security vulnerabilities when detected via zero‑shot LLM inference, and how does detection accuracy vary across vulnerability categories without fine‑tuning?

## Motivation

Automated detection of security bugs remains a bottleneck: static analysers miss many semantic issues, while manual review is costly. Large language models (LLMs) can reason about code semantics without bespoke training, but it is unclear which code characteristics drive their success and whether performance differs across vulnerability types. Clarifying these relationships would guide realistic deployment of zero‑shot LLMs as a lightweight supplement to existing tools.

## Related work

- **[Vulnerable Source Code Detection using SonarCloud Code Analysis (2023)](https://arxiv.org/abs/2307.02446)** — Demonstrates how conventional static analysis (e.g., SonarCloud) identifies vulnerabilities in the software development lifecycle, providing a baseline for comparison with LLM‑based approaches.  
- **[Towards Vulnerability Discovery Using Staged Program Analysis (2015)](https://arxiv.org/abs/1508.04627)** — Introduces staged static analysis techniques that extract structural code features (control‑flow, data‑flow) for vulnerability discovery, informing the set of predictors we will evaluate against LLM performance.  
- **[Can Open-Source LLM Agents Replace Static Application Security Testing Tools? An Empirical Assessment (2026)](https://arxiv.org/abs/2606.11672)** — Directly assesses zero‑shot LLM agents on security tasks, reporting overall detection metrics but without dissecting which code features drive success; our work extends this by linking feature‑level properties to accuracy across categories.

## Expected results

- Zero‑shot LLMs will achieve moderate precision (≈ 65 %) and lower recall (≈ 45 %) overall, with higher precision on syntactic bugs (e.g., buffer overflows) and lower on semantic issues (e.g., logic flaws).  
- Specific structural features (e.g., depth of AST, cyclomatic complexity) and semantic cues (e.g., presence of taint‑propagating APIs) will show statistically significant positive correlations (p < 0.05) with per‑category detection accuracy.  
- A multiple‑linear regression model using these features will explain a meaningful portion of variance in LLM performance (adjusted R² ≈ 0.30), indicating that feature‑level analysis can predict when LLMs are likely to succeed.

## Methodology sketch

- **Data acquisition**  
  - Download the *VulDeePecker* dataset (≈ 5 k vulnerable and non‑vulnerable C code snippets) from its public GitHub release.  
  - Retrieve additional open‑source snippets (Python, JavaScript) from the *Juliet* test suite via Zenodo (DOI 10.5281/zenodo.XXXX).  

- **Feature extraction (predictors)**  
  - Parse each snippet into an abstract syntax tree (AST) using `tree-sitter`.  
  - Compute structural metrics: AST depth, node count, cyclomatic complexity, number of function calls.  
  - Compute semantic token metrics: frequency of known taint‑source APIs, presence of sanitization functions, embedding‑based similarity to known vulnerable patterns (using a small pre‑trained code encoder).  

- **Zero‑shot LLM inference (outcome)**  
  - Load three open‑source LLMs that fit ≤ 7 GB RAM (CodeLlama‑7B, StarCoder‑Base, and a distilled Llama‑2‑Chat).  
  - For each snippet, construct a uniform prompt: “Identify any security vulnerability present in the following code and specify its type (e.g., SQLi, XSS, buffer overflow).”  
  - Run inference in batches of 50 samples to stay within memory limits; record the model’s predicted vulnerability type (or “none”).  

- **Ground‑truth alignment**  
  - Use the dataset’s provided labels to create binary outcomes per vulnerability category (vulnerable = 1, safe = 0).  

- **Performance evaluation**  
  - Compute precision, recall, F1‑score, and ROC‑AUC for each model and each vulnerability category.  
  - Apply **McNemar’s test** (α = 0.05) to compare LLM predictions against a baseline static analyzer (Bandit for Python, cppcheck for C).  

- **Feature‑performance analysis**  
  - Correlate each extracted feature with per‑category detection accuracy using Pearson’s r.  
  - Fit a multiple linear regression (or LASSO) model predicting accuracy from the full feature set; assess significance of coefficients (t‑test, p < 0.05).  

- **Scalability check**  
  - Log inference time per sample; verify total runtime ≤ 6 h on a GitHub Actions runner (2 CPU cores, 7 GB RAM).  

- **Reproducibility**  
  - All scripts will be version‑controlled; data URLs and model identifiers are explicitly listed for automated `wget`/`git clone` in the final pipeline.

## Duplicate-check

- Reviewed existing ideas: N/A (first idea in this project).  
- Closest match: None found in corpus.  
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-19T18:39:45Z
**Outcome**: exhausted
**Original term**: Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code computer science
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating the Effectiveness of LLMs for Identifying Security Vulnerabilities in Open-Source Code computer science | 0 |
| 1 | large language model based static code analysis for security | 5 |
| 2 | AI-driven vulnerability detection in open‑source software | 0 |
| 3 | transformer models for automated security bug finding | 0 |
| 4 | machine learning methods for software security flaw identification | 0 |
| 5 | deep learning code auditing for security vulnerabilities | 0 |
| 6 | GPT‑style code review for exploit detection | 0 |
| 7 | neural code models applied to security vulnerability classification | 0 |
| 8 | language model assisted security code scanning | 0 |
| 9 | benchmark of LLMs for software security testing | 0 |
| 10 | prompt engineering for automated vulnerability discovery | 0 |
| 11 | AI‑powered static analysis tools for open‑source repositories | 0 |
| 12 | semantic code analysis with transformers for security assessment | 0 |
| 13 | large language model accuracy in identifying security bugs | 0 |
| 14 | automated security triage using generative AI on codebases | 0 |
| 15 | neural representation learning for software security analysis | 0 |
| 16 | AI‑enhanced code review pipelines for vulnerability mitigation | 0 |
| 17 | large‑scale evaluation of LLMs in security code inspection | 0 |
| 18 | deep neural networks for detection of insecure coding patterns | 0 |
| 19 | generative models for security flaw prioritization in open‑source projects | 0 |
| 20 | comparative study of machine‑learning vs. traditional static analysis for vulnerability detection | 0 |

### Verified citations

1. **Vulnerable Source Code Detection using SonarCloud Code Analysis** (2023). Alifia Puspaningrum, Muhammad Anis Al Hilmi,  Darsih, Muhamad Mustamiin, Maulana Ilham Ginanjar. arXiv. [2307.02446](https://arxiv.org/abs/2307.02446). PDF-sampled: No.
2. **Towards Vulnerability Discovery Using Staged Program Analysis** (2015). Bhargava Shastry, Fabian Yamaguchi, Konrad Rieck, Jean-Pierre Seifert. arXiv. [1508.04627](https://arxiv.org/abs/1508.04627). PDF-sampled: No.
3. **Can Open-Source LLM Agents Replace Static Application Security Testing Tools? An Empirical Assessment** (2026). Derek Yohn, Luke Flancher, Mirajul Islam, Khaled Slhoub. arXiv. [2606.11672](https://arxiv.org/abs/2606.11672). PDF-sampled: No.
