---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Beyond the Current Observation: Evaluating Multimodal Large Language M"

## Summary of the prior work
The paper introduces RNG-Bench, a benchmark suite evaluating Multimodal Large Language Models (MLLMs) in controllable non-Markov games where agents must reconstruct hidden states from brief past observations to make future decisions. It isolates "forgetting" from "suboptimal planning" using a Memory Gap metric across two environments (Matching Pairs and 3D Maze) and demonstrates that fine-tuning on optimal rollouts significantly improves long-context retention without degrading general capabilities. The core finding is that current frontier MLLMs fail primarily due to the inability to retain visual information over long horizons rather than a lack of strategic reasoning.

## Proposed extension
**Research Question:** Can a CPU-tractable, discrete symbolic abstraction layer (acting as a "working memory" buffer) mitigate the visual forgetting observed in RNG-Bench when the agent is restricted to text-only reasoning steps between visual observations?
This matters because it tests whether the bottleneck is purely a visual encoding/decoding failure in the transformer architecture or a lack of explicit intermediate state representation, offering a path to robust long-horizon planning without requiring massive GPU-accelerated fine-tuning or context window expansion.

## Methodology sketch
**Data:** Generate a subset of the RNG-Bench "3D Maze" environment where the visual grid is rendered into a compact, deterministic ASCII grid representation (e.g., `#` for walls, `.` for path, `M` for monster) and a JSON log of "key events" (e.g., `{"t": 5, "event": "saw_key", "loc": "(2,4)"}`) is appended to the prompt at every step.
**Procedure:** Run a lightweight, CPU-only text-only LLM (e.g., a quantized 3B parameter model or a small transformer) on a modified game loop where the model receives only the ASCII state and event log, explicitly instructed to update a "mental map" string in its output before selecting the next move; compare this against the baseline MLLM receiving raw images in the original RNG-Bench protocol.
**Expected Result:** The text-only agent with explicit symbolic state updates should achieve a significantly lower "Memory Gap" on the CPU, demonstrating that the failure in the multimodal setting stems from the difficulty of maintaining latent visual states rather than an inability to perform the logical deduction required for the game.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Beyond the Current Observation: Evaluating Multimodal Large Language Models in Controllable Non-Markov Games** — Shengyuan Ding, Xilin Wei, Xinyu Fang, Haodong Duan, Dahua Lin, Jiaqi Wang, Yuhang Zang. https://arxiv.org/abs/2606.19338.

```bibtex
@article{orig_arxiv_2606_19338,
  title = {Beyond the Current Observation: Evaluating Multimodal Large Language Models in Controllable Non-Markov Games},
  author = {Shengyuan Ding and Xilin Wei and Xinyu Fang and Haodong Duan and Dahua Lin and Jiaqi Wang and Yuhang Zang},
  year = {2026},
  eprint = {2606.19338},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.19338},
  url = {https://arxiv.org/abs/2606.19338}
}
```
