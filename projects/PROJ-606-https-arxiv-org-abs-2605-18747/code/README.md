# Code as Agent Harness - Adaptation Summary

## Original Paper Context
The original paper "Code as Agent Harness" is a **survey paper**. It proposes a conceptual framework (Interface, Mechanisms, Scaling) for agent systems but does not provide a specific algorithm, training code, or experimental dataset with a quantitative result to reproduce.

## Adaptation Strategy
Since there is no "core algorithmic result" to reproduce, this adaptation **quantifies the survey's own structure**.
- **Real Data Source**: The paper's abstract (provided in the prompt) is treated as the real data.
- **Methodology**: A keyword frequency analysis is performed to measure the relative emphasis (coverage) placed on the three layers defined in the abstract.
- **Approximation**: Instead of running a complex LLM or agent simulation (which is impossible on the CPU-only, 2-core runner without external heavy dependencies), we use simple regex-based keyword matching. This faithfully represents the *conceptual* result of the paper (i.e., "The paper discusses these three areas") in a quantifiable format.

## Simplifications vs. Original
- **Original**: Qualitative survey of literature.
- **Adaptation**: Quantitative text analysis of the abstract.
- **Data**: Used the abstract text directly (no external download required, ensuring speed and reliability).
- **Dependencies**: Pure Python + `pandas`, `matplotlib`, `numpy` (CPU-safe).

## Output Artifacts
- `data/layer_coverage.csv`: Table of keyword counts and coverage scores per layer.
- `data/layer_coverage.json`: JSON version of the results.
- `figures/layer_distribution.png`: Bar chart visualizing the coverage.
