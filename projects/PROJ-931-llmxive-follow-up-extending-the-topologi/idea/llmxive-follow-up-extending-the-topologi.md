---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "The Topological Trouble With Transformers"

## Summary of the prior work
The paper argues that standard feedforward Transformers fundamentally struggle with "state tracking" (iteratively updating latent variables over time) because each update pushes the state representation deeper into the network stack, eventually exhausting the model's fixed depth. The authors propose that true temporally extended cognition requires shifting from explicit external "thought traces" to implicit internal dynamics via recurrent architectures, introducing a taxonomy to categorize these by their recurrence axis (depth vs. step).

## Proposed extension
**Research Question:** Can a "Coarse-Grained Recurrent Attention" mechanism, which aggregates state updates over $k$ input tokens before applying a single recurrent transformation to the hidden state, achieve perfect state tracking on finite-state automata tasks using only CPU-tractable, shallow (depth < 10) models, whereas standard Transformers and fine-grained RNNs fail?

This matters because it tests the paper's hypothesis that "coarse-grained recurrence" can bypass the depth bottleneck without the computational overhead of explicit chain-of-thought or deep recurrent stacks, offering a potential architectural fix for state tracking that is compatible with existing, resource-constrained hardware.

## Methodology sketch
*   **Data:** Generate a synthetic dataset of 10,000 sequences based on a specific 4-state Deterministic Finite Automaton (DFA) (e.g., parity checking or modulo counting) with sequence lengths ranging from 50 to 200 tokens, ensuring the task requires strict memory of the current state to predict the next output.
*   **Procedure:** Train three models on CPU-only hardware: (1) a standard Transformer (depth 6), (2) a standard RNN (depth 6, unrolled), and (3) the proposed "Coarse-Grained Recurrent Attention" model where the hidden state is updated only every $k=10$ tokens using a learned aggregation of the intervening context. Measure the accuracy of state prediction at the final token and analyze the "state depth" via probing classifiers at each layer.
*   **Expected Result:** The standard Transformer and fine-grained RNN will show a sharp drop in accuracy as sequence length increases due to depth exhaustion or gradient issues, while the Coarse-Grained model will maintain near-perfect accuracy and demonstrate that the latent state remains accessible in shallow layers, validating the efficacy of coarse-grained recurrence for state tracking.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **The Topological Trouble With Transformers** — Michael C. Mozer, Shoaib Ahmed Siddiqui, Rosanne Liu. https://arxiv.org/abs/2604.17121.

```bibtex
@article{orig_arxiv_2604_17121,
  title = {The Topological Trouble With Transformers},
  author = {Michael C. Mozer and Shoaib Ahmed Siddiqui and Rosanne Liu},
  year = {2026},
  eprint = {2604.17121},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2604.17121},
  url = {https://arxiv.org/abs/2604.17121}
}
```
