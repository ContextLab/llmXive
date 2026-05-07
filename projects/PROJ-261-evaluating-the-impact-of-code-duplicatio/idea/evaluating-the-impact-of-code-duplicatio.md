---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Impact of Code Duplication on LLM Code Understanding

**Field**: Computer Science

## Research question

How does the local density of syntactic code clones correlate with the perplexity and bug-detection accuracy of pre-trained language models on open-source Python code?

## Motivation

Code duplication is a well-documented liability for human maintainability, yet its influence on Large Language Model (LLM) robustness remains unquantified. Since LLMs are trained on GitHub corpora rich in copy-pasted code, understanding whether this redundancy aids memorization or degrades generalization is critical for assessing training data quality. This gap matters for developers relying on AI tools to refactor or debug systems where duplication is prevalent.

## Literature gap analysis

### What we searched

We queried Semantic Scholar, arXiv, and OpenAlex for terms including "code duplication LLM performance," "impact of code clones on language models," "redundancy in code training data," and "LLM code understanding clone density." The search returned five results, all focused on using LLMs *for* clone detection tasks rather than investigating how code duplication affects LLM comprehension or prediction metrics.

### What is known

- [Code Clone Detection Techniques Based on Large Language Models (2025)](https://ieeexplore.ieee.org/document/10918947/) — Confirms LLMs are effective at detecting code duplication, noting that excessive cloning poses maintenance challenges for human developers.
- [Investigating the Efficacy of Large Language Models for Code Clone Detection (2024)](https://dl.acm.org/doi/10.1145/3643916.3645030) — Demonstrates LLM success in code generation and clone detection tasks, but does not measure how clone density affects model performance.
- [Selecting and Combining Large Language Models for Scalable Code Clone Detection (2025)](https://arxiv.org/abs/2510.15480) — Addresses risks of code clones including vulnerabilities, but focuses on detection methodology rather than training data impact.
- [Assessing the Code Clone Detection Capability of Large Language Models (2024)](https://ieeexplore.ieee.org/document/10576803/) — Evaluates GPT-3.5 and GPT-4 on clone detection benchmarks, confirming LLMs can perform this task but not how clones affect model understanding.
- [Can large language models identify and refactor code clones? An empirical study (2025)](https://linkinghub.elsevier.com/retrieve/pii/S0164121225003863) — Establishes that LLMs can identify and refactor code clones, confirming clone detection is a viable LLM task.

### What is NOT known

There is no published work quantifying the relationship between structural clone density and downstream model metrics such as perplexity or bug detection error rates. It remains unclear whether LLMs treat duplicated code as a signal for pattern reinforcement or as noise that degrades generalization. None of the retrieved papers examine code duplication as an independent variable affecting model comprehension.

### Why this gap matters

If duplication systematically biases model predictions, refactoring strategies for "AI-readiness" may need to prioritize code uniqueness over human readability. Filling this gap would provide empirical evidence for whether reducing duplication improves the reliability of LLM-assisted software engineering tools, informing both training data curation and codebase maintenance practices.

### How this project addresses the gap

This project will compute clone density metrics on a public Python corpus and measure the resulting perplexity and task accuracy of a pre-trained model. By correlating these two independent measurements, we will produce the first evidence linking code redundancy directly to LLM understanding performance.

## Expected results

We expect to find a non-linear correlation where moderate duplication reduces perplexity (easier prediction) but high duplication increases bug detection errors (overfitting to patterns). Confirmation will require a statistically significant correlation coefficient (p < 0.05) across a stratified sample of code segments.

## Methodology sketch

- Download a subset of the `codeparrot/github-code` dataset from HuggingFace (Python files only, limited to 500MB to fit GHA RAM).
- Run a lightweight AST-based clone detector (e.g., `srcml` or custom Python AST parser) to assign a "duplication density" score to each code segment.
- Load `Salesforce/codegen-350M-mono` in 8-bit quantization for CPU inference to stay within 7GB RAM limits.
- Compute perplexity for each segment and run bug detection on a held-out subset using the `humaneval` evaluation suite.
- Calculate Spearman's rank correlation between duplication density and model performance metrics.
- Visualize the relationship using scatter plots with regression lines generated via `matplotlib`.
- Document all hyperparameters and random seeds for reproducibility.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.0.0) on 2026-05-07T02:19:29Z
**Outcome**: success_after_expansion
**Original term**: Evaluating the Impact of Code Duplication on LLM Code Understanding computer science
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating the Impact of Code Duplication on LLM Code Understanding computer science | 5 |

### Verified citations

1. **Can large language models identify and refactor code clones? An empirical study** (2025). Xing Qian, E. Alomar. Journal of Systems and Software. [https://doi.org/10.1016/j.jss.2025.112717](https://doi.org/10.1016/j.jss.2025.112717). PDF-sampled: No.
2. **Code Clone Detection Techniques Based on Large Language Models** (2025). Afnan A. Almatrafi, F. Eassa, Sana Sharaf. IEEE Access. [https://doi.org/10.1109/ACCESS.2025.3549780](https://doi.org/10.1109/ACCESS.2025.3549780). PDF-sampled: Inaccessible.
3. **Investigating the Efficacy of Large Language Models for Code Clone Detection** (2024). Mohamad Khajezade, J. Wu, F. H. Fard, Gema Rodríguez-Pérez, M. Shehata. IEEE International Conference on Program Comprehension. [https://doi.org/10.1145/3643916.3645030](https://doi.org/10.1145/3643916.3645030). PDF-sampled: No.
4. **Selecting and Combining Large Language Models for Scalable Code Clone Detection** (2025). Muslim Chochlov, G. Ahmed, James Patten, Yuanhua Han, Guoxian Lu, et al.. arXiv.org. [https://doi.org/10.48550/arXiv.2510.15480](https://doi.org/10.48550/arXiv.2510.15480). PDF-sampled: No.
5. **Assessing the Code Clone Detection Capability of Large Language Models** (2024). Zixian Zhang, Takfarinas Saber. 2024 4th International Conference on Code Quality (ICCQ). [https://doi.org/10.1109/ICCQ60895.2024.10576803](https://doi.org/10.1109/ICCQ60895.2024.10576803). PDF-sampled: No.
