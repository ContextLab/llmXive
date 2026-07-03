---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level "

## Summary of the prior work
MCompassRAG addresses the trade-off between retrieval precision and latency in RAG systems by augmenting chunk embeddings with topic-level metadata signals, effectively using topics as a "semantic compass" to guide retrieval. By training a lightweight retriever via LLM-teacher distillation, it achieves higher information efficiency and significantly lower latency compared to standard dense retrieval baselines across six complex benchmarks. The core innovation lies in representing chunks and queries as weighted sums of topic centroid embeddings to filter semantic noise before the final similarity search.

## Proposed extension
Can we replace the computationally expensive topic modeling pre-processing step of MCompassRAG with a lightweight, deterministic keyword-graph traversal to achieve similar "topic-aware" retrieval precision on CPU-only hardware? This question matters because the current reliance on neural topic models (e.g., BERTopic) creates a significant inference bottleneck and dependency on GPU resources for the metadata generation phase, limiting the deployment of MCompassRAG in edge or low-resource environments where the original paper's latency gains are most needed.

## Methodology sketch
We will construct a dataset of 5,000 academic abstracts and full-text paragraphs from the arXiv CS domain, removing all GPU-accelerated components. The procedure involves replacing the neural topic model in MCompassRAG with a TF-IDF based keyword co-occurrence graph where nodes are terms and edges represent semantic proximity within a sliding window; "topics" will be defined as the connected components or high-degree clusters in this graph. We will then generate chunk representations by mapping text to these graph clusters using simple set intersection and frequency weighting, training the same lightweight distillation head from the original paper using only CPU-based vector operations (e.g., via NumPy or scikit-learn). The expected result is a "GraphCompass" variant that retains at least 80% of the original MCompassRAG's information efficiency improvement over dense baselines while reducing the total end-to-end latency (including metadata generation) by 40% on a standard multi-core CPU.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval** — Amirhossein Abaskohi, Raymond Li, Gaetano Cimino, Peter West, Giuseppe Carenini, Issam H. Laradji. https://arxiv.org/abs/2606.18508.

```bibtex
@article{orig_arxiv_2606_18508,
  title = {MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval},
  author = {Amirhossein Abaskohi and Raymond Li and Gaetano Cimino and Peter West and Giuseppe Carenini and Issam H. Laradji},
  year = {2026},
  eprint = {2606.18508},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.18508},
  url = {https://arxiv.org/abs/2606.18508}
}
```
