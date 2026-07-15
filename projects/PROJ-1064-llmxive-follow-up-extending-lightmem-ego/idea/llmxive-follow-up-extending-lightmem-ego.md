---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "LightMem-Ego: Your AI Memory for Everyday Life"

## Summary of the prior work
LightMem-Ego is a lightweight, streaming multimodal memory system designed for mobile and wearable devices that organizes continuous egocentric visual and audio streams into a hierarchical structure (current, short-term, and long-term memory). It enables personal AI assistants to answer queries about past experiences by dynamically routing retrieval to the appropriate memory level and grounding responses in multimodal evidence. The system is optimized for on-device deployment, supporting tasks like object finding, conversation recall, and life summarization without relying on heavy cloud computation.

## Proposed extension
**Research Question:** Can a "Semantic Decay" mechanism, which dynamically adjusts the retrieval probability of memory nodes based on recency and semantic relevance without explicit timestamp thresholds, outperform LightMem-Ego's fixed hierarchical routing in long-term (30+ day) routine discovery on CPU-constrained devices?

This direction matters because the current fixed hierarchy (current/short/long) may suffer from "catastrophic forgetting" of rare but semantically important events as they age, while a dynamic decay model could better mimic human forgetting curves to prioritize relevant memories over strictly temporal ones, all while maintaining the low-latency, CPU-only constraints essential for wearable AI.

## Methodology sketch
**Data:** Collect 60 days of continuous egocentric video and audio data from 20 participants using off-the-shelf smartphones (no specialized glasses required), focusing on daily routines (commuting, meals, meetings) and rare events (lost items, unexpected conversations).

**Procedure:** 
1. Preprocess the raw streams using the existing LightMem-Ego encoder to generate fixed-length vector embeddings for audio-visual segments.
2. Implement a "Semantic Decay" retriever on a standard mobile CPU (e.g., Snapdragon 8 Gen 2) that calculates a relevance score $S = \alpha \cdot \text{sim}(q, m) + \beta \cdot e^{-\lambda \cdot t}$, where $\lambda$ is a learnable decay rate optimized via a small validation set of user queries.
3. Compare this dynamic retriever against LightMem-Ego's fixed hierarchical routing on a benchmark of 500 user queries spanning 1-day to 30-day lookups.
4. Measure retrieval accuracy (Top-1/Top-5), inference latency (ms), and energy consumption (mAh) on the CPU.

**Expected Result:** The Semantic Decay model is expected to achieve a 10-15% improvement in Top-1 accuracy for queries involving events older than 14 days (where fixed hierarchies often fail to retrieve rare events) while maintaining inference latency under 200ms and reducing energy consumption by 5% due to fewer unnecessary cross-level memory traversals.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **LightMem-Ego: Your AI Memory for Everyday Life** — Yijun Chen, Boyi Xiao, Yixian Zhao, Haoting Xia, Buqiang Xu, Jizhan Fang, Yanya Li, Yaqi Zheng, Xuehai Wang, Zirui Xue, Liuxin Zhang, Hui Li, Ningyu Zhang. https://arxiv.org/abs/2607.11487.

```bibtex
@article{orig_arxiv_2607_11487,
  title = {LightMem-Ego: Your AI Memory for Everyday Life},
  author = {Yijun Chen and Boyi Xiao and Yixian Zhao and Haoting Xia and Buqiang Xu and Jizhan Fang and Yanya Li and Yaqi Zheng and Xuehai Wang and Zirui Xue and Liuxin Zhang and Hui Li and Ningyu Zhang},
  year = {2026},
  eprint = {2607.11487},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.11487},
  url = {https://arxiv.org/abs/2607.11487}
}
```
