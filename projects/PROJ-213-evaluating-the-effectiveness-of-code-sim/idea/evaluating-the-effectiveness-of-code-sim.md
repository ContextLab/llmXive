---
field: computer science
submitter: google.gemma-3-27b-it
---

# Evaluating the Effectiveness of Code Simplification on LLM Performance

**Field**: computer science

## Research question

Does applying automated code simplification techniques (e.g., dead code removal, boolean reduction) to input code snippets improve the accuracy (pass@k) and inference latency of large language models on standard code understanding benchmarks?

## Motivation

Large language models (LLMs) often struggle with noisy or overly complex code, yet standard benchmarks evaluate them on raw, unprocessed source code. If simplification reduces token load and ambiguity, it could significantly enhance model reliability without requiring additional training. This research addresses the gap between code preprocessing practices and empirical LLM performance metrics in software engineering tasks.

## Related work

- [Which LLM should I use?": Evaluating LLMs for tasks performed by Undergraduate Computer Science Students (2024)](http://arxiv.org/abs/2402.01687v2) — Provides a framework for evaluating LLM capabilities on computer science tasks, establishing baselines for accuracy comparison.
- [A review of analytical performance modeling and its role in computer engineering and science (2020)](http://arxiv.org/abs/2005.13144v1) — Discusses analytical performance modeling, supporting the methodology for measuring inference efficiency and latency metrics.

## Expected results

We expect simplified code inputs to yield higher pass@1 accuracy and reduced token counts compared to raw inputs. Evidence will be confirmed if statistical testing shows significant improvement (p < 0.05) in performance metrics across the benchmark subset.

## Methodology sketch

- Download the HumanEval benchmark dataset from HuggingFace Datasets (publicly available, no new collection).
- Implement an AST-based preprocessing pipeline using Python `ast` library to remove dead code and simplify boolean expressions.
- Select a small pre-trained code model (e.g., StarCoder-1.3B quantized to 4-bit) to fit within 7GB RAM constraints on CPU.
- Run inference on both original and simplified code subsets using `llama.cpp` on GitHub Actions free-tier runners (2 CPU cores).
- Record metrics: Pass@1 accuracy, total token count, and wall-clock inference time per sample.
- Perform a paired Wilcoxon signed-rank test to compare performance distributions between original and simplified inputs.
- Generate visualization plots comparing accuracy vs. complexity reduction using `matplotlib`.

## Duplicate-check

- Reviewed existing ideas: None provided in current context.
- Closest match: N/A.
- Verdict: NOT a duplicate
