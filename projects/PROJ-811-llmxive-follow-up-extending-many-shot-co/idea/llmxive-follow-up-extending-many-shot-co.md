---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Many-Shot CoT-ICL: Making In-Context Learning Truly Learn"

## Summary of the prior work
This paper challenges the assumption that many-shot In-Context Learning (ICL) scales uniformly for reasoning tasks, demonstrating that standard similarity-based retrieval fails when Chain-of-Thought (CoT) demonstrations are involved due to procedural mismatches. By reframing many-shot CoT-ICL as in-context test-time learning, the authors propose that demonstration ordering must follow principles of "ease of understanding" and "smooth conceptual progression," leading to the Curvilinear Demonstration Selection (CDS) method which orders examples to minimize embedding trajectory curvature. Their experiments show that CDS significantly outperforms random or similarity-based ordering on reasoning benchmarks, particularly for reasoning-oriented models, by transforming the prompt into a structured curriculum rather than a mere retrieval buffer.

## Proposed extension
**Research Question:** Can the "smoothness" of a CoT demonstration sequence be quantified and optimized using *logical dependency graphs* rather than continuous embedding curvature, and does this discrete, logic-aware ordering yield superior stability for non-reasoning models that lack the internal "curvature" sensitivity observed in the original study?

This direction matters because the original CDS relies on continuous vector space properties (curvature) which may be unstable or undefined for non-reasoning models that do not generate coherent reasoning traces; replacing geometric smoothness with discrete logical prerequisite chains offers a CPU-tractable, model-agnostic metric that could generalize the "curriculum" principle to a broader class of LLMs without requiring expensive embedding computations for every permutation.

## Methodology sketch
**Data:** Utilize the existing geometry and number theory datasets from the prior work, but augment them with a lightweight logical parser (e.g., a small rule-based script or a CPU-only logical solver) to extract a set of atomic logical steps (e.g., "apply Pythagorean theorem," "identify similar triangles") from each demonstration's CoT trace, forming a directed acyclic graph (DAG) of dependencies.

**Procedure:** 
1. Construct a "Logical Difficulty Score" for each demonstration based on the depth of its dependency DAG.
2. Generate three prompt orderings for 64-shot experiments: (a) the original CDS (embedding curvature), (b) "Logical Ascending" (ordering by increasing DAG depth), and (c) "Logical Random" (shuffling while maintaining the same set).
3. Evaluate these orderings on both reasoning-oriented (e.g., Qwen3-14B) and non-reasoning (e.g., Llama-3.1-8B) models using a CPU-only inference server (or small-batch GPU if absolutely necessary, but the metric calculation is CPU-only).
4. Measure not only accuracy but also the *variance* across multiple seeds to test stability.

**Expected Result:** We hypothesize that for non-reasoning models, the "Logical Ascending" order will outperform CDS and significantly reduce performance variance, suggesting that these models rely more on explicit structural scaffolding (logical prerequisites) than on the subtle semantic smoothness captured by embedding curvature. Conversely, reasoning models may show comparable performance between CDS and Logical Ascending, validating that both metrics capture valid aspects of "curriculum learning" but through different mechanisms.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Many-Shot CoT-ICL: Making In-Context Learning Truly Learn** — Tsz Ting Chung, Lemao Liu, Mo Yu, Dit-Yan Yeung. https://arxiv.org/abs/2605.13511.

```bibtex
@article{orig_arxiv_2605_13511,
  title = {Many-Shot CoT-ICL: Making In-Context Learning Truly Learn},
  author = {Tsz Ting Chung and Lemao Liu and Mo Yu and Dit-Yan Yeung},
  year = {2026},
  eprint = {2605.13511},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.13511},
  url = {https://arxiv.org/abs/2605.13511}
}
```
