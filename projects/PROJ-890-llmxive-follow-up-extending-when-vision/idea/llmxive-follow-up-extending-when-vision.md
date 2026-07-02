---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "When Vision Speaks for Sound"

## Summary of the prior work
The paper identifies an "audio-visual Clever Hans effect" in Multimodal Large Language Models (MLLMs), where models hallucinate audio understanding by relying solely on visual cues rather than verifying the actual audio stream. To diagnose this, the authors introduce *Thud*, a probing framework using counterfactual edits (Shift, Mute, Swap) to break audio-visual alignment, and propose a two-stage alignment recipe using intervention-derived preference pairs to improve verification accuracy. While their method significantly boosts temporal synchronization detection, it reveals that models still struggle with existential (Mute) and material (Swap) verification, suggesting these are orthogonal cognitive dimensions.

## Proposed extension
**Research Question:** Does the cognitive decoupling between temporal synchronization (Shift) and physical existence verification (Mute/Swap) persist when models are trained exclusively on low-compute, CPU-tractable synthetic datasets that isolate specific acoustic-visual causal mechanisms, or does the "Alignment Tax" observed in large-scale training also manifest in these constrained, interpretable regimes?

This question matters because it determines whether the failure to verify physical sound existence is a limitation of current massive-scale alignment recipes or a fundamental architectural deficiency that requires a different, potentially lighter-weight, training objective. By focusing on CPU-tractable synthetic data, we can rapidly iterate on causal hypotheses about *why* models fail to detect silence or swapped sounds without the resource overhead of training on terabytes of video.

## Methodology sketch
*   **Data:** Generate a small, synthetic dataset (approx. 500 samples) using a CPU-only audio synthesis library (e.g., `pydub` or `numpy`) and a static image renderer. Create three strict conditions: (1) **Silence-Only**: A video of a person speaking with the audio track replaced by pure silence; (2) **Sound-Only**: A video of a person speaking with the audio replaced by a distinct, unrelated sound (e.g., a dog barking); (3) **Sync-Shift**: A video where the audio is delayed by exactly 500ms. No external video/audio datasets are used.
*   **Procedure:** Train a small, open-source MLLM (e.g., a 1-2B parameter model with frozen vision encoder) using Direct Preference Optimization (DPO) on these synthetic pairs. Run the *Thud* probing framework on the fine-tuned model to measure accuracy on Shift, Mute, and Swap tasks. Crucially, compare the performance gain on "Mute/Swap" tasks against a baseline model trained on general video QA data, ensuring the entire pipeline (synthesis, training, inference) runs on a standard multi-core CPU within 48 hours.
*   **Expected Result:** We anticipate that while the synthetic training will drastically improve "Shift" detection (temporal), it will yield negligible improvement on "Mute" and "Swap" tasks unless the training data explicitly includes negative examples of "sound existence" reasoning. This would confirm that the decoupling is not just a data-scale issue but a structural gap in how current alignment objectives model physical causality, suggesting future work must explicitly inject causal counterfactuals rather than just preference pairs.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **When Vision Speaks for Sound** — Xiaofei Wen, Wenjie Jacky Mo, Xingyu Fu, Rui Cai, Tinghui Zhu, Wendi Li, Yanan Xie, Muhao Chen, Peng Qi. https://arxiv.org/abs/2605.16403.

```bibtex
@article{orig_arxiv_2605_16403,
  title = {When Vision Speaks for Sound},
  author = {Xiaofei Wen and Wenjie Jacky Mo and Xingyu Fu and Rui Cai and Tinghui Zhu and Wendi Li and Yanan Xie and Muhao Chen and Peng Qi},
  year = {2026},
  eprint = {2605.16403},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2605.16403},
  url = {https://arxiv.org/abs/2605.16403}
}
```
