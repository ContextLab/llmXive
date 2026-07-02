---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Formalizing Latent Thoughts: Four Axioms of Thought Representation in "

## Summary of the prior work
This paper establishes an axiomatic framework (Causality, Minimality, Separability, Stability) to evaluate the quality of latent thought representations in LLMs independently of downstream task accuracy. Through audits of 23 reasoning tasks across diverse model families, the authors demonstrate that current representations fail to satisfy all four axioms simultaneously, primarily because they distinguish task types but fail to differentiate between specific questions within the same task, encoding little new information beyond the input. The study concludes that this representational gap is a structural limitation inherent to current architectures rather than a result of model size or training procedures.

## Proposed extension
**Research Question:** Can the "Separability" axiom be satisfied by explicitly injecting synthetic, task-agnostic noise into the input embeddings of a frozen LLM, thereby forcing the model to generate distinct latent thought vectors for different questions within the same task type? This matters because if noise injection can structurally disentangle representations without retraining, it suggests that the failure of current models is due to a lack of forced differentiation in the input manifold rather than an inability of the transformer architecture to support such representations. This approach is CPU-tractable as it only requires forward passes through a frozen model and simple vector arithmetic, avoiding the computational cost of gradient-based optimization or large-scale RL.

## Methodology sketch
**Data:** We will use the 23 reasoning tasks from the original paper, specifically selecting pairs of questions that belong to the same task type but have different ground-truth answers (the "within-task" pairs that previously failed the Separability test).
**Procedure:** 
1. Load a small, open-weight model (e.g., Llama-3-8B or a distilled variant) in CPU-only mode.
2. For each input pair, generate a baseline latent thought representation (the hidden state at the "thought" token).
3. Create a "noise-augmented" input by adding Gaussian noise ($\epsilon \sim \mathcal{N}(0, \sigma^2)$) to the input embeddings, where $\sigma$ is tuned to be significant enough to perturb the input manifold but small enough to preserve semantic coherence (verified via a simple perplexity check).
4. Pass the noise-augmented inputs through the frozen model to generate new latent thought representations.
5. Compute the pairwise cosine similarity between the thought vectors for the two questions in each pair; a successful extension would show a statistically significant increase in dissimilarity (lower cosine similarity) for the noise-augmented condition compared to the baseline, while maintaining the semantic validity of the output via a lightweight heuristic check.
**Expected Result:** We expect to observe that adding structured noise to the input embeddings significantly improves the Separability metric for within-task question pairs, indicating that the model's representational failure is partly due to the smoothness of the input manifold rather than a hard architectural constraint, and that this "forcing" mechanism can be applied without retraining.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Formalizing Latent Thoughts: Four Axioms of Thought Representation in LLMs** — Fahd Seddik, Fatemeh Fard. https://arxiv.org/abs/2606.27378.

```bibtex
@article{orig_arxiv_2606_27378,
  title = {Formalizing Latent Thoughts: Four Axioms of Thought Representation in LLMs},
  author = {Fahd Seddik and Fatemeh Fard},
  year = {2026},
  eprint = {2606.27378},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.27378},
  url = {https://arxiv.org/abs/2606.27378}
}
```
