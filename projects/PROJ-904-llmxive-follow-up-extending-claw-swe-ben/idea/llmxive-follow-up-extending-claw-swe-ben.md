---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnes"

**Field**: computer science

## Research question

How does the fidelity of context compression strategies modulate the reasoning capacity of language models on long-horizon coding tasks, and does this interaction reveal a fundamental trade-off where context optimization can substitute for model scaling in specific reasoning regimes?

## Motivation

Current evaluations of agent harnesses often conflate the benefits of larger model backbones with the efficiency of context management, making it unclear whether resource-constrained deployments should prioritize model scaling or retrieval optimization. By isolating context compression fidelity as a primary variable, this work addresses the gap in understanding how to maximize Pass@1 scores under strict CPU-only and token-budget constraints, which is critical for sustainable, local deployment of coding agents.

## Related work

- [SWE-bench Goes Live! (2025)](https://arxiv.org/abs/2505.23419) — Establishes the foundational dataset structure for issue-resolving tasks, which this project extends by filtering for instances where context length is the primary bottleneck.
- [SWE-ABS: Adversarial Benchmark Strengthening Exposes Inflated Success Rates on Test-based Benchmark (2026)](https://arxiv.org/abs/2603.00520) — Highlights that standard benchmarks are approaching saturation and that metrics can be inflated, underscoring the need for robust evaluation dimensions like cost-efficiency and context handling fidelity.
- [Understanding Code Agent Behaviour: An Empirical Study of Success and Failure Trajectories (2025)](https://arxiv.org/abs/2511.00197) — Provides a methodological precedent for analyzing agent failure modes beyond simple pass/fail metrics, supporting the proposed analysis of how context loss leads to specific reasoning breakdowns.
- [SWEnergy: An Empirical Study on Energy Efficiency in Agentic Issue Resolution Frameworks with SLMs (2025)](https://arxiv.org/abs/2512.09543) — Demonstrates the viability of Small Language Models (SLMs) in agentic frameworks, providing a baseline for comparing the cost-efficiency of context optimization against model scaling.

## Expected results

We expect that high-fidelity context strategies (e.g., diff-aware retrieval) will enable smaller models to match the performance of larger models on long-horizon tasks, effectively shifting the performance curve such that context optimization yields a higher marginal return than parameter scaling beyond a certain threshold. This would be confirmed by a crossover point in the performance-vs-cost curves where the retrieval-enhanced SLM surpasses the baseline larger model, and falsified if model scaling continues to dominate regardless of context strategy.

## Methodology sketch

- **Data Acquisition**: Download the Claw-SWE-Bench Lite and full benchmark datasets from the official repository; programmatically filter for issues where the relevant file history exceeds 500 lines to ensure the task is context-bound.
- **Baseline Configuration**: Implement a control harness using a CPU-runnable 1B-parameter LLM (e.g., a quantized variant of Llama-3-8B or Mistral-7B) with a naive "first-N-lines" truncation strategy to establish a low-fidelity context baseline.
- **Experimental Configurations**: Develop and integrate three distinct context compression modules: (a) TF-IDF/BM25 relevance retrieval of code snippets relative to the issue description, (b) Sliding window with diff-awareness prioritizing lines adjacent to predicted changes, and (c) Rule-based semantic summarization of file changes.
- **Scaling Comparison**: Run the same experimental modules with a larger (e.g., 7B-parameter) model to quantify the performance gain from model scaling versus context optimization.
- **Execution Protocol**: Execute all configurations on the filtered dataset with identical API call limits and runtime budgets (e.g., 60 minutes per instance) on a standard CPU-only environment (2 cores, 7GB RAM), utilizing quantization (e.g., GGUF/llama.cpp) to fit models in memory.
- **Measurement**: Record Pass@1 success rates, total tokens consumed (proxy for cost), and the specific failure modes (e.g., missing context vs. reasoning error) for each configuration.
- **Statistical Analysis**: Apply a two-way ANOVA to test for interaction effects between "context strategy" and "model size" on Pass@1 scores, followed by post-hoc pairwise comparisons to identify the crossover point where context optimization outperforms scaling.
- **Validation Independence**: Validate all performance metrics against the ground-truth test cases provided in the benchmark (unit tests), ensuring the evaluation target (test pass/fail) is independent of the context compression logic used to generate the patches.

## Duplicate-check

- Reviewed existing ideas: Claw-SWE-Bench extension, SWE-bench saturation analysis, OpenClaw execution surfaces, SWEnergy efficiency study.
- Closest match: Claw-SWE-Bench extension (similarity sketch: shares the benchmark and harness focus, but this project uniquely isolates context compression strategies as the primary variable against model scaling, whereas the original benchmark focuses on harness architecture generally).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-08-05T22:29:17Z
**Outcome**: success_after_expansion
**Original term**: llmXive follow-up: extending "Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnes" computer science
**Verified citation count**: 8

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "Claw-SWE-Bench: A Benchmark for Evaluating OpenClaw-style Agent Harnes" computer science | 8 |

### Verified citations

1. **SWE-bench Goes Live!** (2025). Linghao Zhang, Shilin He, Chaoyun Zhang, Yu Kang, Bowen Li, et al.. arXiv. [2505.23419](https://arxiv.org/abs/2505.23419). PDF-sampled: No.
2. **SWE-ABS: Adversarial Benchmark Strengthening Exposes Inflated Success Rates on Test-based Benchmark** (2026). Boxi Yu, Yang Cao, Yuzhong Zhang, Liting Lin, Junjielong Xu, et al.. arXiv. [2603.00520](https://arxiv.org/abs/2603.00520). PDF-sampled: No.
3. **Understanding Code Agent Behaviour: An Empirical Study of Success and Failure Trajectories** (2025). Oorja Majgaonkar, Zhiwei Fei, Xiang Li, Federica Sarro, He Ye. arXiv. [2511.00197](https://arxiv.org/abs/2511.00197). PDF-sampled: No.
4. **SWEnergy: An Empirical Study on Energy Efficiency in Agentic Issue Resolution Frameworks with SLMs** (2025). Arihant Tripathy, Ch Pavan Harshit, Karthik Vaidhyanathan. arXiv. [2512.09543](https://arxiv.org/abs/2512.09543). PDF-sampled: No.
5. **Foundations for Agentic AI Investigations from the Forensic Analysis of OpenClaw** (2026). Jan Gruber, Jan-Niclas Hilgert. arXiv. [2604.05589](https://arxiv.org/abs/2604.05589). PDF-sampled: No.
6. **OpenClaw-RL: Train Any Agent Simply by Talking** (2026). Yinjie Wang, Xuyang Chen, Xiaolong Jin, Mengdi Wang, Ling Yang. arXiv. [2603.10165](https://arxiv.org/abs/2603.10165). PDF-sampled: No.
7. **Security of OpenClaw Agents: Fundamentals, Attacks, and Countermeasures** (2026). Yuntao Wang, Jianle Ba, Han Liu, Yanghe Pan, Jintao Wei, et al.. arXiv. [2605.25435](https://arxiv.org/abs/2605.25435). PDF-sampled: No.
8. **From Assistant to Double Agent: Formalizing and Benchmarking Attacks on OpenClaw for Personalized Local AI Agent** (2026). Yuhang Wang, Feiming Xu, Zheng Lin, Guangyu He, Yuzhe Huang, et al.. arXiv. [2602.08412](https://arxiv.org/abs/2602.08412). PDF-sampled: No.
