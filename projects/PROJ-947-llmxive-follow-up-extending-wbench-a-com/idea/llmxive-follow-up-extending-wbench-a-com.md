---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "WBench: A Comprehensive Multi-turn Benchmark for Interactive Video Wor"

## Summary of the prior work
The paper introduces WBench, a comprehensive multi-turn benchmark designed to evaluate interactive video world models across five key dimensions: video quality, setting adherence, interaction adherence, consistency, and physics compliance. It features 289 test cases with over 1,000 interaction turns, utilizing a unified control interface for navigation and a suite of 22 automatic metrics validated against human judgments to reveal that no current model excels in all areas.

## Proposed extension
How does the "cognitive load" of a user's interaction sequence (measured by the entropy of command diversity and the depth of causal dependency between turns) correlate with the degradation of a world model's physics compliance and consistency? This question matters because WBench identifies that consistency and physics are major failure points, but it does not yet isolate whether these failures are caused by the intrinsic complexity of the world state or the cumulative burden of multi-turn instruction following, which is critical for designing more robust, long-horizon agents without requiring expensive GPU-intensive retraining.

## Methodology sketch
We will construct a "Low-Compute Interaction Stress Test" dataset by sampling 100 cases from WBench and generating three variants for each: (1) Low-entropy sequences (repetitive, single-type actions), (2) Medium-entropy sequences (mixed navigation and action), and (3) High-entropy sequences (rapid perspective switching, event editing, and complex causal chains). The procedure involves running the existing 20 state-of-the-art models (using their publicly available inference endpoints or CPU-optimized quantized versions where available) to generate video responses for these sequences, then calculating the existing WBench metrics (physics compliance and consistency) while simultaneously computing a "Sequence Complexity Score" based on the command log. The expected result is a statistically significant negative correlation between the Sequence Complexity Score and physics/consistency scores, quantifying exactly how much interaction complexity a model can handle before its internal world representation collapses, thereby providing a CPU-tractable diagnostic tool for model selection.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation** — Kaining Ying, Hengrui Hu, Siyu Ren, Jiamu Li, Fengjiao Chen, Ziwen Wang, Xuezhi Cao, Xunliang Cai, Henghui Ding. https://arxiv.org/abs/2605.25874.

```bibtex
@article{orig_arxiv_2605_25874,
  title = {WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation},
  author = {Kaining Ying and Hengrui Hu and Siyu Ren and Jiamu Li and Fengjiao Chen and Ziwen Wang and Xuezhi Cao and Xunliang Cai and Henghui Ding},
  year = {2026},
  eprint = {2605.25874},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.25874},
  url = {https://arxiv.org/abs/2605.25874}
}
```
