---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Program-as-Weights: A Programming Paradigm for Fuzzy Functions"

## Summary of the prior work
The paper introduces "Program-as-Weights" (PAW), a paradigm where a neural compiler translates natural-language specifications of "fuzzy functions" into compact, parameter-efficient adapters (LoRA or prefix-tuning) for a frozen, lightweight interpreter. This shifts the heavy lifting of Large Language Models to a one-time compilation step, enabling the resulting neural programs to run locally, offline, and efficiently on consumer hardware while matching the performance of much larger models. The authors validate this with a 10M-example dataset called FuzzyBench and demonstrate that a 0.6B interpreter executing PAW programs outperforms direct prompting of a 32B model.

## Proposed extension
**Research Question:** Can the PAW paradigm be extended to support *dynamic, multi-step fuzzy workflows* where a single natural-language specification is compiled into a *composition* of multiple small, specialized neural adapters that are stitched together at runtime, rather than a single monolithic adapter?

**Why it matters:** The current PAW approach compiles a single adapter per function, which limits its ability to handle complex, multi-stage tasks (e.g., "Extract entities, then summarize them, then format as JSON") without overloading a single small interpreter or requiring a massive, monolithic adapter that defeats the efficiency goal. A compositional approach would enable complex agentic behaviors to be run entirely offline on CPU with the same memory footprint, bridging the gap between simple fuzzy functions and full agentic planning.

## Methodology sketch
**Data:** We will augment FuzzyBench by synthetically generating "chain-of-thought" style multi-step tasks. For each base fuzzy task (e.g., log parsing), we will create 500,000 variations requiring sequential execution of 2-3 sub-functions (e.g., "parse log" -> "classify severity" -> "generate alert"), annotated with intermediate ground-truth states.

**Procedure:** 
1. **Compiler Design:** Modify the PAW compiler to output a *directed acyclic graph (DAG)* of adapter specifications instead of a single LoRA. The compiler will first decompose the natural language spec into sub-tasks, then generate a small LoRA adapter for each sub-task using the existing Text-to-LoRA mechanism.
2. **Interpreter Modification:** Create a "Chained Interpreter" that accepts a DAG of adapters. It will execute the workflow by: (a) running the first adapter on input, (b) passing the hidden state or output to the next adapter in the chain, and (c) hot-swapping adapters in RAM without re-loading the base model.
3. **Evaluation:** Run the system on a standard laptop CPU (M3 or Intel i7) without GPU acceleration. Compare the end-to-end accuracy and latency against: (a) a single monolithic PAW adapter for the whole chain, (b) direct API calls to a 32B model, and (c) a sequential pipeline of separate PAW programs.

**Expected Result:** We hypothesize that the compositional approach will achieve 95%+ of the accuracy of the monolithic adapter (which likely suffers from capacity limits in a small model) while maintaining sub-100ms latency per step on CPU. Crucially, the memory footprint should remain constant (base model + largest single adapter) regardless of chain length, whereas the monolithic adapter's size and inference cost would grow linearly with task complexity, eventually exceeding CPU RAM limits.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Program-as-Weights: A Programming Paradigm for Fuzzy Functions** — Wentao Zhang, Liliana Hotsko, Woojeong Kim, Pengyu Nie, Stuart Shieber, Yuntian Deng. https://arxiv.org/abs/2607.02512.

```bibtex
@article{orig_arxiv_2607_02512,
  title = {Program-as-Weights: A Programming Paradigm for Fuzzy Functions},
  author = {Wentao Zhang and Liliana Hotsko and Woojeong Kim and Pengyu Nie and Stuart Shieber and Yuntian Deng},
  year = {2026},
  eprint = {2607.02512},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.02512},
  url = {https://arxiv.org/abs/2607.02512}
}
```
