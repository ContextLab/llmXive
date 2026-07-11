---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Video-Oasis: Rethinking Evaluation of Video Understanding"

## Summary of the prior work
The paper introduces "Video-Oasis," a diagnostic suite that audits existing video understanding benchmarks to identify "shortcuts" where samples can be solved without visual perception or temporal reasoning. By applying visual-dependency, temporal-dependency, and ambiguity tests across 14 benchmarks, the authors reveal that 55% of samples are solvable via linguistic priors or static cues, and that state-of-the-art models perform near-random on the remaining "video-native" challenges. The work concludes that current benchmarks overestimate model capabilities and provides a framework for distilling rigorous, video-specific evaluation data.

## Proposed extension
**Research Question:** Can we construct a "Zero-GPU Video Reasoning Benchmark" where all video-native challenges are solvable *only* by models that possess explicit, structured temporal logic (e.g., causal graphs or event sequences) rather than implicit attention mechanisms, and does this capability correlate with performance on CPU-only logical reasoning tasks?

**Why it matters:** While Video-Oasis identifies *that* models fail on video-native tasks, it does not determine *why* (e.g., lack of temporal architecture vs. insufficient training data). By shifting the evaluation to a text-based, logic-centric format derived from video events, we can isolate the specific reasoning deficit without requiring expensive video encoding or GPU inference, enabling rapid iteration on algorithmic designs for temporal reasoning.

## Methodology sketch
**Data:** We will use the "video-native" subset distilled by Video-Oasis and manually convert each video question into a structured "Event-Logic" textual representation (e.g., a JSON list of timestamped events with causal links like "Event A causes Event B"), removing all raw pixel data.
**Procedure:** 
1. Filter the Video-Oasis video-native set for samples where the answer depends strictly on the order and causality of events (verified by human annotators).
2. Generate a parallel text-only dataset where the video content is replaced by these structured event logs and the original question.
3. Evaluate a suite of diverse, CPU-tractable small language models (SLMs) and logical solvers on this text-only dataset, comparing their accuracy against the original Video-LLM performance on the video version.
4. Introduce "temporal noise" (randomly reordering event logs) to verify that only models with explicit temporal attention mechanisms maintain high accuracy.

**Expected Result:** We expect to find a strong positive correlation between performance on the "Event-Logic" text benchmark and the original video benchmark, but only for models with explicit temporal reasoning modules (e.g., chain-of-thought or graph-based reasoning), while standard SLMs and Video-LLMs relying on implicit attention will fail the text-based logic test, confirming that the bottleneck is logical structure rather than visual encoding.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Video-Oasis: Rethinking Evaluation of Video Understanding** — Geuntaek Lim, Sungjune Park, Jaeyun Lee, Inwoong Lee, Taeoh Kim, Dongyoon Wee, Minho Shim, Yukyung Choi. https://arxiv.org/abs/2603.29616.

```bibtex
@article{orig_arxiv_2603_29616,
  title = {Video-Oasis: Rethinking Evaluation of Video Understanding},
  author = {Geuntaek Lim and Sungjune Park and Jaeyun Lee and Inwoong Lee and Taeoh Kim and Dongyoon Wee and Minho Shim and Yukyung Choi},
  year = {2026},
  eprint = {2603.29616},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2603.29616},
  url = {https://arxiv.org/abs/2603.29616}
}
```
