---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "OCC-RAG: Optimal Cognitive Core for Faithful Question Answering"

## Summary of the prior work
The paper introduces OCC-RAG, a family of task-specialized small language models (SLMs) designed to prioritize robust multi-hop reasoning and strict context faithfulness over parametric knowledge. By mid-training on a novel, large-scale synthetic corpus of 3 million multi-hop QA examples, the authors demonstrate that compact models (0.6B and 1.7B parameters) can outperform general-purpose models 2–6 times their size in answering questions grounded in provided text while successfully abstaining when evidence is missing. The core innovation lies in a training curriculum that enforces structured reasoning traces with literal source citations, proving that an "optimal cognitive core" for faithful QA can be achieved through data quality and architectural specialization rather than sheer scale.

## Proposed extension
**Research Question:** Can a CPU-tractable "Cognitive Pruning" protocol, which dynamically removes attention heads and feed-forward neurons based on their contribution to context-grounded reasoning (measured via gradient-free sensitivity analysis), reduce the parameter count of OCC-RAG by 50% while maintaining >90% of its faithfulness and refusal capabilities? This matters because it tests whether the "Optimal Cognitive Core" identified by OCC-RAG is a dense, redundant capability or a sparse, essential sub-network that can be extracted without expensive GPU-based fine-tuning, enabling deployment on edge devices.

## Methodology sketch
**Data:** Utilize the existing OCC-RAG-1.7B checkpoints and the held-out subset of the synthetic multi-hop QA corpus (approx. 50k examples) plus standard benchmarks (HotpotQA, ConFiQA, MuSiQue-Un).
**Procedure:** 
1. Implement a CPU-tractable sensitivity analysis using activation patching or zero-out probing on the frozen OCC-RAG model; for each layer, systematically mask 10% of attention heads and FFN neurons and measure the drop in "Context Faithfulness Score" (a weighted metric of ConFiQA accuracy and citation precision).
2. Identify the "critical sub-network" consisting of the top 50% of parameters that show the highest sensitivity to faithfulness metrics.
3. Prune the model to retain only these critical parameters (creating OCC-RAG-Pruned-0.85B) and perform a lightweight, CPU-only "re-mid-training" phase using only 10k synthetic examples to recover any minor accuracy loss, avoiding full backpropagation.
**Expected Result:** The pruned model (0.85B) will retain >90% of the original 1.7B model's performance on faithfulness and refusal benchmarks, demonstrating that the "cognitive core" is highly sparse and that high-fidelity RAG capabilities can be distilled into sub-billion parameter models via structural pruning rather than just data scaling.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **OCC-RAG: Optimal Cognitive Core for Faithful Question Answering** — Maksim Savkin, Mikhail Goncharov, Alexander Gambashidze, Alla Chepurova, Dmitrii Tarasov, Nikita Andriianov, Daria Pugacheva, Vasily Konovalov, Andrey Galichin, Ivan Oseledets. https://arxiv.org/abs/2606.00683.

```bibtex
@article{orig_arxiv_2606_00683,
  title = {OCC-RAG: Optimal Cognitive Core for Faithful Question Answering},
  author = {Maksim Savkin and Mikhail Goncharov and Alexander Gambashidze and Alla Chepurova and Dmitrii Tarasov and Nikita Andriianov and Daria Pugacheva and Vasily Konovalov and Andrey Galichin and Ivan Oseledets},
  year = {2026},
  eprint = {2606.00683},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.00683},
  url = {https://arxiv.org/abs/2606.00683}
}
```
