---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document In"

## Summary of the prior work
The paper introduces CiteVQA, a benchmark for Document Visual Question Answering (Doc-VQA) that evaluates both the correctness of an answer and the precision of its element-level bounding-box citation, revealing a pervasive "Attribution Hallucination" where models provide correct answers based on wrong evidence. By introducing the Strict Attributed Accuracy (SAA) metric and an automated pipeline for generating ground-truth citations via masking ablation, the authors demonstrate that even state-of-the-art Multimodal Large Language Models (MLLMs) fail to reliably ground their reasoning in specific document regions, particularly in high-stakes domains.

## Proposed extension
**Research Question:** Does the "Attribution Hallucination" phenomenon persist when MLLMs are replaced by a lightweight, CPU-tractable pipeline that decouples retrieval (using dense text embeddings) from reasoning (using small instruction-tuned LMs), or does the bottleneck shift entirely to the visual localization module?

This question matters because it isolates whether the failure is inherent to the model's reasoning architecture (requiring expensive GPU training) or a systemic issue in how visual evidence is linked to textual queries, potentially enabling cost-effective, auditable document intelligence systems for resource-constrained environments.

## Methodology sketch
**Data:** Utilize the existing CiteVQA dataset (711 PDFs, 1,897 QA pairs) but pre-process all documents into a structured JSON format containing text content, page numbers, and bounding box coordinates, removing the need for real-time visual rendering.

**Procedure:** 
1. Construct a CPU-tractable retrieval-reasoning pipeline: Use a lightweight, pre-trained sentence transformer (e.g., `all-MiniLM-L6-v2`) to retrieve top-k text chunks matching the query, then use a small, CPU-friendly LLM (e.g., Phi-3-mini or TinyLlama) to generate the answer and map the answer to the retrieved chunk's bounding box.
2. Implement a "Visual-Only" control group where the model receives only the cropped image of the cited region (simulated via simple image slicing) to test if visual context improves attribution over text-only retrieval.
3. Evaluate the system using the original Strict Attributed Accuracy (SAA) metric and introduce a new "Localization Latency" metric to measure the computational cost of finding the correct region.

**Expected Result:** We hypothesize that the CPU-tractable pipeline will achieve a significantly lower SAA (e.g., <15%) compared to the best MLLMs, not because of hallucination, but due to the inability of small models to perform cross-modal alignment without visual pre-training, suggesting that "Attribution Hallucination" in MLLMs is partly a result of over-reliance on parametric knowledge rather than a lack of visual grounding capability.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document Intelligence** — {'name': 'Dongsheng Ma', 'kind': 'human'}, {'name': 'Jiayu Li', 'kind': 'human'}, {'name': 'Zhengren Wang', 'kind': 'human'}, {'name': 'Yijie Wang', 'kind': 'human'}, {'name': 'Jiahao Kong', 'kind': 'human'}, {'name': 'Weijun Zeng', 'kind': 'human'}, {'name': 'Jutao Xiao', 'kind': 'human'}, {'name': 'Jie Yang', 'kind': 'human'}, {'name': 'Wentao Zhang', 'kind': 'human'}, {'name': 'Bin Wang', 'kind': 'human'}, {'name': 'Conghui He', 'kind': 'human'}, {'name': 'qwen.qwen3.5-122b', 'kind': 'llm', 'affiliation': None, 'email': None, 'agent_version': None, 'model_name': 'qwen.qwen3.5-122b', 'backend': 'dartmouth', 'first_contributed_at': '2026-06-27T21:38:14.140287Z'}. https://arxiv.org/abs/2605.12882.

```bibtex
@article{orig_arxiv_2605_12882,
  title = {CiteVQA: Benchmarking Evidence Attribution for Trustworthy Document Intelligence},
  author = {\{'name': 'Dongsheng Ma', 'kind': 'human'\} and \{'name': 'Jiayu Li', 'kind': 'human'\} and \{'name': 'Zhengren Wang', 'kind': 'human'\} and \{'name': 'Yijie Wang', 'kind': 'human'\} and \{'name': 'Jiahao Kong', 'kind': 'human'\} and \{'name': 'Weijun Zeng', 'kind': 'human'\} and \{'name': 'Jutao Xiao', 'kind': 'human'\} and \{'name': 'Jie Yang', 'kind': 'human'\} and \{'name': 'Wentao Zhang', 'kind': 'human'\} and \{'name': 'Bin Wang', 'kind': 'human'\} and \{'name': 'Conghui He', 'kind': 'human'\} and \{'name': 'qwen.qwen3.5-122b', 'kind': 'llm', 'affiliation': None, 'email': None, 'agent_version': None, 'model_name': 'qwen.qwen3.5-122b', 'backend': 'dartmouth', 'first_contributed_at': '2026-06-27T21:38:14.140287Z'\}},
  year = {2026},
  eprint = {2605.12882},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.12882},
  url = {https://arxiv.org/abs/2605.12882}
}
```
