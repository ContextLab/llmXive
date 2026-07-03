---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "ArcANE: Do Role-Playing Language Agents Stay in Character at the Right"

## Summary of the prior work
The paper introduces ArcANE, a benchmark and evaluation framework for Role-Playing Language Agents (RPLAs) that assesses whether a character's responses evolve correctly across their psychological "Character Arc" rather than maintaining a static persona. It segments narratives into phases along specific psychological axes and generates probes (scenarios) that test if the model adapts its behavior to the current phase, finding that explicitly conditioning on the arc significantly outperforms standard retrieval, especially for scenarios outside the source text.

## Proposed extension
**Research Question:** Does the *granularity* of the psychological axis (e.g., coarse "Good vs. Evil" vs. fine-grained "Trust vs. Cynicism") determine the *transferability* of character evolution to novel, out-of-domain scenarios, and can a "coarse-to-fine" prompting strategy improve arc-awareness in CPU-tractable, small-context models?

This matters because ArcANE demonstrates the value of arcs, but it remains unclear if all psychological abstractions are equally effective for generalizing behavior to unseen situations, and current arc-grounding methods often require large context windows or fine-tuning that may be prohibitive for edge deployment.

## Methodology sketch
**Data:** Select 3 novels from the existing ArcANE corpus (e.g., Harry Potter, Pride and Prejudice) and manually define two sets of Character Arcs per character: (1) **Coarse Axes** (broad, high-level traits like "Innocence to Experience") and (2) **Fine Axes** (specific, nuanced shifts like "Naive Trust to Calculated Skepticism"). Generate a new set of 50 "Out-of-World" probes per character that are semantically distant from the source text (e.g., modern ethical dilemmas).

**Procedure:** 
1. Run a CPU-tractable, open-weight model (e.g., Phi-3-mini or TinyLlama) in a "zero-shot" mode.
2. Prompt the model with the same probe under three conditions: (a) **Coarse Context** (only the broad axis description), (b) **Fine Context** (only the specific axis description), and (c) **Hybrid Context** (brief coarse summary followed by the specific phase details).
3. Use a lightweight, rule-based scoring metric (e.g., keyword alignment with phase-specific behavioral constraints) and a single, small LLM-as-a-Judge (running locally via CPU quantization) to rate response consistency with the target phase.

**Expected Result:** We hypothesize that while Coarse Context fails to distinguish between adjacent phases in complex arcs, Fine Context may be too noisy for small models to track without fine-tuning; the Hybrid Context strategy will yield the highest consistency scores, demonstrating that a structured "coarse-to-fine" narrative abstraction is necessary for robust, low-resource character evolution.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **ArcANE: Do Role-Playing Language Agents Stay in Character at the Right Time?** — Woojung Song, Nalim Kim, Sangjun Song, Chaewon Heo, Jongwon Lim, Yohan Jo. https://arxiv.org/abs/2606.05553.

```bibtex
@article{orig_arxiv_2606_05553,
  title = {ArcANE: Do Role-Playing Language Agents Stay in Character at the Right Time?},
  author = {Woojung Song and Nalim Kim and Sangjun Song and Chaewon Heo and Jongwon Lim and Yohan Jo},
  year = {2026},
  eprint = {2606.05553},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.05553},
  url = {https://arxiv.org/abs/2606.05553}
}
```
