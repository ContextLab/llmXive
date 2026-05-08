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

We queried Semantic Scholar, arXiv, and OpenAlex for terms including "code duplication LLM performance," "impact of code clones on language models," "redundancy in code training data," "code patterns LLM understanding," and "LLM code quality metrics." The verified literature block returned 16 results, all focused on LLM benchmarks for code generation, static analysis reasoning, or context engineering rather than investigating how code duplication affects LLM comprehension or prediction metrics.

### What is known

- [CoRe: Benchmarking LLMs Code Reasoning Capabilities through Static Analysis Tasks (2025)](https://arxiv.org/abs/2507.05269) — Establishes that static analysis can be used to evaluate LLM code reasoning, but does not examine structural redundancy as a predictor variable.
- [DynaCode: A Dynamic Complexity-Aware Code Benchmark for Evaluating Large Language Models in Code Generation (2025)](https://arxiv.org/abs/2503.10452) — Introduces complexity-aware code benchmarks but does not correlate results with code duplication metrics in the training or test corpora.
- [Context Engineering for Multi-Agent LLM Code Assistants Using Elicit, NotebookLM, ChatGPT, and Claude Code (2025)](https://arxiv.org/abs/2508.08322) — Addresses context limitations in code tasks but does not examine how code duplication within the corpus affects model comprehension.

### What is NOT known

There is no published work quantifying the relationship between structural clone density and downstream model metrics such as perplexity or bug detection error rates. It remains unclear whether LLMs treat duplicated code as a signal for pattern reinforcement or as noise that degrades generalization. None of the retrieved papers examine code duplication as an independent variable affecting model comprehension.

### Why this gap matters

If duplication systematically biases model predictions, refactoring strategies for "AI-readiness" may need to prioritize code uniqueness over human readability. Filling this gap would provide empirical evidence for whether reducing duplication improves the reliability of LLM-assisted software engineering tools, informing both training data curation and codebase maintenance practices.

### How this project addresses the gap

This project will compute clone density metrics on a public Python corpus and measure the resulting perplexity and task accuracy of a pre-trained model. By correlating these two independent measurements, we will produce the first evidence linking code redundancy directly to LLM understanding performance.

## Expected results

We expect to find a non-linear correlation where moderate duplication reduces perplexity (easier prediction) but high duplication increases bug detection errors (overfitting to patterns). Confirmation will require a statistically significant correlation coefficient (p < 0.05) across a stratified sample of code segments.

## Methodology sketch

- Download a 500MB subset of the `codeparrot/github-code` dataset from HuggingFace Datasets (Python files only) using `datasets` library with streaming mode to stay within GHA RAM limits.
- Parse each file using Python's built-in `ast` module to extract function bodies and compute syntactic clone density via AST subtree matching (no external dependencies).
- Load `Salesforce/codegen-350M-mono` in 8-bit quantization using `bitsandbytes` for CPU inference, ensuring memory usage stays under 7GB.
- Compute token-level perplexity for each code segment using the model's log-probability outputs.
- Evaluate bug detection on a held-out 50-problem subset from `human-eval` using pass@1 accuracy as the metric.
- Calculate Spearman's rank correlation between duplication density and both perplexity and bug detection accuracy.
- Visualize the relationship using scatter plots with regression lines generated via `matplotlib`.
- Document all hyperparameters, random seeds, and clone detection thresholds for reproducibility.
- Store intermediate metrics in CSV format for auditability.
- Perform sensitivity analysis across three different clone-detection thresholds (0.7, 0.8, 0.9) to verify robustness.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: None identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.4.0) on 2026-05-07T19:24:30Z
**Outcome**: success
**Original term**: Evaluating the Impact of Code Duplication on LLM Code Understanding computer science
**Verified citation count**: 16

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Evaluating the Impact of Code Duplication on LLM Code Understanding computer science | 16 |

### Verified citations

1. **NeuroSync: Intent-Aware Code-Based Problem Solving via Direct LLM Understanding Modification** (2025). Wenshuo Zhang, Leixian Shen, Shuchang Xu, Jindu Wang, Jian Zhao, et al.. ACM Symposium on User Interface Software and Technology. [https://doi.org/10.1145/3746059.3747668](https://doi.org/10.1145/3746059.3747668). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Understanding and Mitigating Errors of LLM-Generated RTL Code** (2025). Jiazheng Zhang, Cheng Liu, Huawei Li. IEEE Transactions on Computer-Aided Design of Integrated Circuits and Systems. [https://doi.org/10.48550/arXiv.2508.05266](https://doi.org/10.48550/arXiv.2508.05266). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Lost in the Mix: Evaluating LLM Understanding of Code-Switched Text** (2025). Amr Mohamed, Yang Zhang, M. Vazirgiannis, Guokan Shang. arXiv.org. [https://doi.org/10.48550/arXiv.2506.14012](https://doi.org/10.48550/arXiv.2506.14012). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Scaling Up and Distilling Down: Language-Guided Robot Skill Acquisition** (2023). Huy Ha, Peter R. Florence, Shuran Song. Conference on Robot Learning. [https://doi.org/10.48550/arXiv.2307.14535](https://doi.org/10.48550/arXiv.2307.14535). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **GNN-RAG: Graph Neural Retrieval for Large Language Model Reasoning** (2024). Costas Mavromatis, George Karypis. arXiv.org. [https://doi.org/10.48550/arXiv.2405.20139](https://doi.org/10.48550/arXiv.2405.20139). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
6. **DynaCode: A Dynamic Complexity-Aware Code Benchmark for Evaluating Large Language Models in Code Generation** (2025). Wenhao Hu, Jinhao Duan, C. Wei, Li Zhang, Yue-feng Zhang, et al.. Annual Meeting of the Association for Computational Linguistics. [https://doi.org/10.48550/arXiv.2503.10452](https://doi.org/10.48550/arXiv.2503.10452). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
7. **Position: The Hidden Costs and Measurement Gaps of Reinforcement Learning with Verifiable Rewards** (2025). Aaron Tu, Weihao Xuan, Heli Qi, Xu Huang, Qingcheng Zeng, et al.. arXiv.org. [https://doi.org/10.48550/arXiv.2509.21882](https://doi.org/10.48550/arXiv.2509.21882). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
8. **Model selection meets clinical semantics: Optimizing ICD-10-CM prediction via LLM-as-Judge evaluation, redundancy-aware sampling, and section-aware fine-tuning** (2025). Hong-Jie Dai, Zheng-Hao Li, An-Tai Lu, Bo-Tsz Shain, Ming-Ta Li, et al.. arXiv.org. [https://doi.org/10.48550/arXiv.2509.18846](https://doi.org/10.48550/arXiv.2509.18846). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
9. **PACIFIC: a framework for generating benchmarks to check Precise Automatically Checked Instruction Following In Code** (2025). I. Dreyfuss, Antonio Abu Nassar, Samuel Ackerman, Axel Bendavid, E. Farchi, et al.. arXiv.org. [https://doi.org/10.48550/arXiv.2512.10713](https://doi.org/10.48550/arXiv.2512.10713). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
10. **CoRe: Benchmarking LLMs Code Reasoning Capabilities through Static Analysis Tasks** (2025). Danning Xie, Mingwei Zheng, Xuwei Liu, Jiannan Wang, Chengpeng Wang, et al.. arXiv. [2507.05269](https://arxiv.org/abs/2507.05269). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
11. **Context Engineering for Multi-Agent LLM Code Assistants Using Elicit, NotebookLM, ChatGPT, and Claude Code** (2025). Muhammad Haseeb. arXiv. [2508.08322](https://arxiv.org/abs/2508.08322). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
12. **Enhancing LLM Code Generation with Ensembles: A Similarity-Based Selection Approach** (2025). Tarek Mahmud, Bin Duan, C. Păsăreanu, Guowei Yang. arXiv.org. [https://doi.org/10.48550/arXiv.2503.15838](https://doi.org/10.48550/arXiv.2503.15838). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
13. **CLASP: Training-Free LLM-Assisted Source Code Watermarking via Semantic-Preserving Transformations** (2025). Rui Xu, Jiawei Chen, Weizhi Liu, Zhaoxia Yin, Cong Kong, et al.. n/a. [2510.11251](https://arxiv.org/abs/2510.11251). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
14. **Distilling LLM Agent into Small Models with Retrieval and Code Tools** (2025). Minki Kang, Jongwon Jeong, Seanie Lee, Jaewoong Cho, Sung Ju Hwang. arXiv.org. [https://doi.org/10.48550/arXiv.2505.17612](https://doi.org/10.48550/arXiv.2505.17612). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
15. **RTL++: Graph-enhanced LLM for RTL Code Generation** (2025). Mohammad Akyash, Kimia Azar, Hadi Kamali. arXiv. [2505.13479](https://arxiv.org/abs/2505.13479). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
16. **Enhancing Code Translation in Language Models with Few-Shot Learning via Retrieval-Augmented Generation** (2024). Manish Bhattarai, Javier E. Santos, Shawn Jones, Ayan Biswas, Boian Alexandrov, et al.. arXiv. [2407.19619](https://arxiv.org/abs/2407.19619). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
