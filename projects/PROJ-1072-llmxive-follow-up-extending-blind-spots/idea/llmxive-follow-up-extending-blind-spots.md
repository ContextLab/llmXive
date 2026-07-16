---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Blind-Spots-Bench: Evaluating Blind Spots in Multimodal Models"

## Summary of the prior work
The paper introduces *Blind-Spots-Bench*, a curated dataset of 235 human-designed tasks that expose persistent reasoning failures in modern multimodal AI systems, such as character-level manipulation and spatial counting, which standard benchmarks often miss. It establishes a task taxonomy and an automated grading pipeline to evaluate 38 models, revealing that while closed-source models generally outperform open-weight ones, no single model excels across all "simple-for-humans" blind spot categories, and scaling does not guarantee improvement on these specific failures.

## Proposed extension
**Research Question:** Does the *order of reasoning steps* in a model's Chain-of-Thought (CoT) generation causally influence its success on *Blind-Spots-Bench* tasks, or do failures stem primarily from the initial perception of constraints regardless of subsequent reasoning?
This matters because the original paper identifies *that* models fail on these tasks but does not distinguish whether the error originates from a "perceptual blind spot" (misreading the input) or a "procedural blind spot" (losing track of constraints during generation). A CPU-tractable investigation into this distinction could guide the design of more efficient, non-GPU-intensive diagnostic tools that target specific failure modes rather than relying on brute-force model scaling.

## Methodology sketch
**Data:** Re-use the 235 *Blind-Spots-Bench* samples, specifically filtering for the "Abstract Reasoning" and "Object-Centric" sub-tasks where the original paper reported the highest failure rates.
**Procedure:** 
1. Run a set of mid-sized, open-weight LLMs (e.g., Llama-3-8B, Mistral-7B) on these tasks using a fixed temperature and standard CoT prompting.
2. Parse the generated CoT traces to extract the *first* constraint mentioned and the *final* constraint acknowledged before the answer.
3. Apply a lightweight, rule-based or small-model classifier (running on CPU) to label each trace as "Perceptual Error" (constraint missed immediately), "Procedural Error" (constraint acknowledged but dropped later), or "Correct."
4. Correlate these labels with the final grading from the original paper's pipeline to determine the dominant failure mode distribution.
**Expected Result:** We hypothesize that for "character-level manipulation" tasks, errors are predominantly *Perceptual* (tokenization issues cause immediate misinterpretation), whereas for "abstract reasoning" tasks, errors are predominantly *Procedural* (attention mechanisms fail to maintain long-term constraint consistency), suggesting that different architectural or training interventions are needed for each blind spot category.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Blind-Spots-Bench: Evaluating Blind Spots in Multimodal Models** — Matteo Santelmo, Xiuying Wei, Israa Fakih, Felix Bauer, Juan Garcia Giraldo, Chengkun Li, Etienne Bamas, Emmanuel Abbé. https://arxiv.org/abs/2607.08317.

```bibtex
@article{orig_arxiv_2607_08317,
  title = {Blind-Spots-Bench: Evaluating Blind Spots in Multimodal Models},
  author = {Matteo Santelmo and Xiuying Wei and Israa Fakih and Felix Bauer and Juan Garcia Giraldo and Chengkun Li and Etienne Bamas and Emmanuel Abbé},
  year = {2026},
  eprint = {2607.08317},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2607.08317},
  url = {https://arxiv.org/abs/2607.08317}
}
```
