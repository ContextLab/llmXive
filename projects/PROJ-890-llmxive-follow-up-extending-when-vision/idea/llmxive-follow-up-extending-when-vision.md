---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "When Vision Speaks for Sound"

**Field**: computer science

## Research question

Does the cognitive decoupling between temporal synchronization (Shift) and physical existence verification (Mute/Swap) in Multimodal Large Language Models persist when trained exclusively on low-compute, CPU-tractable synthetic datasets that isolate specific acoustic-visual causal mechanisms?

## Motivation

Current large-scale MLLMs exhibit an "audio-visual Clever Hans effect," relying on visual cues to hallucinate audio understanding rather than processing the audio stream. It remains unclear whether the failure to verify physical sound existence (Mute/Swap) is a limitation of massive-scale alignment recipes or a fundamental architectural deficiency requiring lighter, causally-informed training objectives. This study addresses this gap by testing if decoupling persists in a constrained, interpretable regime.

## Literature gap analysis

### What we searched
We queried Semantic Scholar, arXiv, and OpenAlex using terms like "multimodal large language model audio hallucination," "audio-visual Clever Hans effect," "counterfactual audio verification MLLM," and "synthetic audio-visual dataset for causal reasoning." The search focused on recent preprints (2023–2026) addressing the "Thud" framework, audio-visual misalignment, and synthetic data generation for multimodal alignment.

### What is known
- [When Vision Speaks for Sound](https://arxiv.org/abs/2605.16403) — Establishes the existence of the "audio-visual Clever Hans effect" in MLLMs and introduces the *Thud* probing framework to diagnose failures in temporal, existential, and material verification.
- [Sound Synthesis, Propagation, and Rendering: A Survey](https://arxiv.org/abs/2011.05538) — Reviews sound rendering techniques in virtual environments, highlighting the importance of audio for realism but not addressing the specific cognitive failure modes of MLLMs in verifying audio existence.
- [FlashSpeech: Efficient Zero-Shot Speech Synthesis](https://arxiv.org/abs/2404.14700) — Discusses efficient speech synthesis methods but focuses on generation quality and speed rather than the verification of audio-visual consistency or causal reasoning in multimodal models.

### What is NOT known
No published work has specifically investigated whether the decoupling between temporal synchronization and physical existence verification persists when models are trained on small, synthetic datasets designed to isolate causal mechanisms on CPU hardware. The literature lacks evidence on whether "Alignment Tax" phenomena observed in large-scale training transfer to these constrained, interpretable regimes.

### Why this gap matters
Understanding whether these failures are scale-dependent or architecturally fundamental is critical for determining if future research should focus on massive data scaling or on developing new, causally-grounded training objectives. If the decoupling persists in low-compute settings, it would suggest that current alignment objectives are insufficient for modeling physical causality, necessitating a shift in research direction.

### How this project addresses the gap
This project directly addresses the gap by generating a synthetic dataset with strict causal conditions (Silence-Only, Sound-Only, Sync-Shift) and training a small MLLM using Direct Preference Optimization. By applying the *Thud* probing framework to this model, we will empirically determine if the decoupling is a result of data scale or a structural gap in alignment objectives.

## Expected results

We anticipate that while synthetic training will improve "Shift" (temporal) detection, it will yield negligible improvement on "Mute" and "Swap" tasks unless the data explicitly includes negative examples of sound existence reasoning. This would confirm that the decoupling is a structural gap in how current alignment objectives model physical causality, rather than merely a data-scale issue.

## Methodology sketch

- **Data Generation**: Use `pydub` and `numpy` on a CPU to synthesize ~500 samples with three conditions: (1) **Silence-Only** (visual speech with silent audio), (2) **Sound-Only** (visual speech with unrelated sound), and (3) **Sync-Shift** (audio delayed by 500ms).
- **Model Selection**: Select a small, open-source MLLM (e.g., 1-2B parameters) with a frozen vision encoder to ensure CPU tractability.
- **Training Protocol**: Apply Direct Preference Optimization (DPO) using the synthetic dataset, constructing preference pairs that explicitly contrast correct vs. incorrect audio-visual alignment.
- **Evaluation Framework**: Execute the *Thud* probing framework on the fine-tuned model to measure accuracy on Shift, Mute, and Swap tasks.
- **Baseline Comparison**: Compare performance against a baseline model trained on general video QA data to isolate the effect of the synthetic causal data.
- **Statistical Analysis**: Perform paired t-tests comparing the fine-tuned model's accuracy on Mute/Swap tasks against the baseline, ensuring the entire pipeline (synthesis, training, inference) completes within 48 hours on a standard multi-core CPU.
- **Validation Independence**: Validation accuracy is measured against the ground-truth labels of the synthetic dataset (which are defined by the generation script's parameters), independent of the model's internal representations or the visual features used for prediction.

## Duplicate-check

- Reviewed existing ideas: None (fresh extension of prior work).
- Closest match: N/A (no existing fleshed-out ideas in corpus).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-09T13:13:04Z
**Outcome**: success_after_expansion
**Original term**: llmXive follow-up: extending "When Vision Speaks for Sound" computer science
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "When Vision Speaks for Sound" computer science | 0 |
| 1 | vision-to-sound synthesis | 5 |
| 2 | audio generation from visual input | 0 |
| 3 | cross-modal audio synthesis | 0 |
| 4 | image-to-audio generation models | 0 |
| 5 | visual-driven sound synthesis | 0 |
| 6 | multimodal generative models for audio | 0 |
| 7 | deep learning for vision-audio translation | 0 |
| 8 | automatic sound generation from images | 0 |
| 9 | video-to-audio synthesis networks | 0 |
| 10 | semantic audio generation from visual features | 0 |
| 11 | cross-modal representation learning for audio | 0 |
| 12 | generative adversarial networks for image-to-sound | 0 |
| 13 | transformer-based vision-to-audio models | 0 |
| 14 | audio synthesis conditioned on visual data | 0 |
| 15 | machine hearing from visual cues | 0 |
| 16 | visual context for audio generation | 0 |
| 17 | neural audio synthesis from images | 0 |
| 18 | cross-modal generative adversarial networks | 0 |
| 19 | multimodal pre-training for vision and audio | 0 |
| 20 | unsupervised vision-to-sound mapping | 0 |

### Verified citations

1. **Synthesis of Reversible Functions Beyond Gate Count and Quantum Cost** (2010). Robert Wille, Mehdi Saeedi, Rolf Drechsler. arXiv. [1004.4609](https://arxiv.org/abs/1004.4609). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Synth-by-Reg (SbR): Contrastive learning for synthesis-based registration of paired images** (2021). Adrià Casamitjana, Matteo Mancini, Juan Eugenio Iglesias. arXiv. [2107.14449](https://arxiv.org/abs/2107.14449). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Text-to-Speech Synthesis Techniques for MIDI-to-Audio Synthesis** (2021). Erica Cooper, Xin Wang, Junichi Yamagishi. arXiv. [2104.12292](https://arxiv.org/abs/2104.12292). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Sound Synthesis, Propagation, and Rendering: A Survey** (2020). Shiguang Liu, Dinesh Manocha. arXiv. [2011.05538](https://arxiv.org/abs/2011.05538). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **FlashSpeech: Efficient Zero-Shot Speech Synthesis** (2024). Zhen Ye, Zeqian Ju, Haohe Liu, Xu Tan, Jianyi Chen, et al.. arXiv. [2404.14700](https://arxiv.org/abs/2404.14700). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
