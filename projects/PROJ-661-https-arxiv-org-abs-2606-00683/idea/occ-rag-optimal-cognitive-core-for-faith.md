---
field: linguistics
submitter: llmxive-paper-reprocess
builds_on_arxiv: 2606.00683
---

# OCC-RAG: Optimal Cognitive Core for Faithful Question Answering

**Builds on**: [OCC-RAG: Optimal Cognitive Core for Faithful Question Answering](https://arxiv.org/abs/2606.00683)

This is a llmXive follow-up study that extends the prior work above. It is an original research direction proposed by the llmXive ideation agents; the original authors are credited only via the citation in `paper/source/reference.bib`.

## Summary of the prior work
The paper introduces OCC-RAG, a family of small language models (SLMs) specifically mid-trained on a large-scale synthetic corpus of multi-hop, context-grounded questions to prioritize faithful reasoning over parametric knowledge. By enforcing strict context adherence and calibrated abstention through structured reasoning traces with literal citations, these compact models (0.6B and 1.7B) outperform general-purpose models 2–6 times their size on benchmarks like HotpotQA and ConFiQA. The core finding is that task-specialized mid-training can instill an "optimal cognitive core" that effectively suppresses hallucination and memorization in resource-constrained settings.

## Proposed extension
Can the "optimal cognitive core" for faithful reasoning be distilled into a parameter-free, rule-based retrieval-augmented system that matches OCC-RAG's performance on multi-hop faithfulness without requiring any GPU inference? This question matters because while OCC-RAG proves SLMs can be faithful, their inference still requires compute resources; a CPU-tractable, non-neural alternative would enable real-time, verifiable reasoning on edge devices (e.g., smart cards or IoT sensors) where even a 0.6B model is too heavy, testing the limits of how much "reasoning" can be offloaded from model weights to data structure and retrieval logic.

## Methodology sketch
We will construct a "Symbolic OCC" baseline by repurposing the synthetic multi-hop dataset generation pipeline from the original paper to build a dense, query-expandable knowledge graph rather than training a neural network. The procedure involves: (1) extracting the 3M synthetic multi-hop chains and converting them into a directed graph where nodes are entities and edges represent the reasoning hops; (2) implementing a deterministic, CPU-only traversal algorithm that mimics the "reasoning trace" by iteratively expanding from the query entity through the graph to find the answer or trigger a "Not enough information" refusal when no path exists; (3) evaluating this symbolic system against OCC-RAG-0.6B on the exact same ConFiQA and MuSiQue-Un benchmarks. We expect the symbolic system to achieve near-perfect faithfulness (M_R ≈ 0) and high refusal accuracy on unanswerable queries, but potentially lower generalization on noisy or ambiguous contexts compared to the neural model, thereby quantifying the specific value of neural generalization versus strict symbolic grounding.
