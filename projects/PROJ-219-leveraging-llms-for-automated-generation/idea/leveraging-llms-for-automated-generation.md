---
field: computer science
submitter: google.gemma-3-27b-it
---

# Leveraging LLMs for Automated Generation of Code Complexity Metrics

**Field**: computer science

## Research question

Can zero-shot large language models accurately estimate standard code complexity metrics (e.g., cyclomatic complexity, Halstead volume) compared to traditional static analysis tools, and under what computational constraints?

## Motivation

Traditional static analysis tools can be computationally expensive or brittle on novel code structures, whereas LLMs offer semantic understanding that might bypass syntactic parsing limitations. This research addresses the gap in evaluating LLM reliability for quantitative software engineering tasks within resource-constrained environments like continuous integration pipelines.

## Related work

- [A Review on Large Language Models: Architectures, Applications, Taxonomies, Open Issues and Challenges (2024)](https://doi.org/10.1109/access.2024.3365742) — Establishes the baseline extraordinary capability of LLMs in natural language processing tasks relevant to code understanding.
- [Can Large Language Models Transform Computational Social Science? (2023)](https://doi.org/10.1162/coli_a_00502) — Demonstrates that LLMs can successfully perform classification and explanation tasks zero-shot, supporting the hypothesis of metric estimation without fine-tuning.
- [The Power of Generative AI: A Review of Requirements, Models, Input–Output Formats, Evaluation Metrics, and Challenges (2023)](https://doi.org/10.3390/fi15080260) — Highlights the critical need to identify specific evaluation metrics when deploying generative AI for technical outputs.
- [The Future of Scientific Publishing: Automated Article Generation (2024)](http://arxiv.org/abs/2404.17586v1) — Shows proof-of-concept for LLMs processing Python code to generate structured text outputs.

## Expected results

We expect LLM estimates to correlate highly (>0.8 Pearson) with traditional tools on simple functions but diverge on complex control flow structures. Success will be confirmed if inference time per snippet remains under 5 seconds on CPU hardware while maintaining acceptable error margins.

## Methodology sketch

- Download a subset (500 snippets) of the `codeparrot/github-code-clean` dataset from HuggingFace Datasets (`hf://datasets/codeparrot/github-code-clean`).
- Install `radon` library locally to compute ground-truth cyclomatic complexity and Halstead volume for all snippets.
- Load a quantized 1B parameter model (e.g., TinyLlama-1.1B INT4) using `transformers` on CPU, ensuring memory usage stays under 4GB.
- Construct prompts asking the model to output specific metric values for each code snippet in JSON format.
- Run inference on the 500 snippets, logging latency and output tokens per request.
- Parse model outputs and compare against `radon` ground truth using Pearson correlation and Mean Absolute Error (MAE).
- Visualize results with scatter plots of estimated vs. actual values to identify systematic biases.

## Duplicate-check

- Reviewed existing ideas: None provided in input context.
- Closest match: N/A.
- Verdict: NOT a duplicate
