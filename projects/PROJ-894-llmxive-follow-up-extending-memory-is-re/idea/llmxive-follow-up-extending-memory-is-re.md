---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents"

## Summary of the prior work
The paper introduces MRAgent, a framework that replaces static retrieval with an "active reconstruction" mechanism using a Cue-Tag-Content graph to dynamically prune memory paths during LLM agent inference. By integrating reasoning directly into the memory access loop, the system avoids combinatorial explosion while significantly improving performance on long-horizon benchmarks like LoCoMo and LongMemEval. The core innovation lies in treating memory not as a fixed database to be queried, but as a reconstructible structure that evolves based on intermediate evidence.

## Proposed extension
**Research Question:** How does the "reconstruction cost" (measured in cognitive steps or graph traversal depth) of active memory access correlate with the stability of long-term reasoning in low-resource LLM agents, and can a "lazy reconstruction" heuristic reduce this overhead without degrading performance?

This question matters because MRAgent's active reconstruction, while effective, may introduce significant latency or token overhead for agents operating under strict computational constraints (e.g., edge devices or CPU-only environments); determining if a simplified, "lazy" version of the graph traversal maintains efficacy would make the approach scalable for real-world, resource-constrained deployment.

## Methodology sketch
**Data:** Utilize the LoCoMo benchmark subset containing multi-hop reasoning tasks with varying context lengths, paired with a synthetic dataset of "noisy" memory graphs where irrelevant edges are artificially inflated to test pruning robustness.

**Procedure:** Implement a CPU-tractable simulation of the MRAgent graph traversal using a small, quantized language model (e.g., a 1B parameter model running in 4-bit precision) or a rule-based agent that mimics LLM token costs. Compare three conditions: (1) the original active reconstruction (full path exploration), (2) a "greedy" reconstruction that only explores the top-k highest-confidence edges, and (3) a "lazy" reconstruction that defers graph expansion until a specific evidence threshold is met. Measure success rates, average graph nodes visited per step, and total inference latency.

**Expected Result:** We hypothesize that the "lazy" reconstruction strategy will achieve comparable accuracy to the full active method on tasks with clear intermediate cues while reducing the average number of graph nodes visited by 40-50%, thereby proving that aggressive real-time reconstruction is not strictly necessary for all reasoning horizons.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents** — Shuo Ji, Yibo Li, Bryan Hooi. https://arxiv.org/abs/2606.06036.

```bibtex
@article{orig_arxiv_2606_06036,
  title = {Memory is Reconstructed, Not Retrieved: Graph Memory for LLM Agents},
  author = {Shuo Ji and Yibo Li and Bryan Hooi},
  year = {2026},
  eprint = {2606.06036},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.06036},
  url = {https://arxiv.org/abs/2606.06036}
}
```
