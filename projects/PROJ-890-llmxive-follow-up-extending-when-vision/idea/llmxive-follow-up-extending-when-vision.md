---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "When Vision Speaks for Sound"

**Field**: computer science

## Research question

Does the persistence of audio-visual decoupling in models trained on causally isolated synthetic data indicate that current MLLM architectures fundamentally lack a mechanism for verifying physical sound existence, independent of alignment data scale?

## Motivation

Current multimodal large language models exhibit an "audio-visual Clever Hans effect": they infer expected sounds from visual content rather than processing the audio stream itself. It remains unclear whether the failure to verify physical sound existence (Mute/Swap conditions) is a limitation of large-scale alignment recipes or a deeper architectural deficiency. Testing whether the decoupling persists in a constrained, causally-controlled training regime separates these hypotheses and informs whether future fixes require data-scale growth or new architectural objectives.

## Literature gap analysis

### What we searched

The librarian queried Semantic Scholar/arXiv with the idea title and ~20 variants covering vision-to-audio synthesis, cross-modal generation, multimodal vision-audio learning, cross-modal attention, and joint vision-audio representations. The verified literature block returned five results, of which only one (a survey of audio-visual learning) is directly on-topic for audio-visual integration in multimodal models; the remainder concern dereverberation, embodied navigation, vision-language pretraining, and speech enhancement — related application areas but not probing causal sound-existence verification.

### What is known

- [Learning in Audio-visual Context: A Review, Analysis, and New Perspective (2022)](https://arxiv.org/abs/2208.09579) — A survey of audio-visual learning paradigms establishing that joint audio-visual modeling is a mature research area and organizing its tasks, but it does not address whether MLLMs verify physical sound existence versus hallucinating it from visual cues.

### What is NOT known

No published work, to our knowledge, has measured whether audio-visual decoupling — specifically failure on Mute (silent audio with visible sound sources) and Swap (mismatched audio) probes — persists after fine-tuning on causally isolated synthetic data with explicit negative examples of sound existence. It is also unknown whether improvements on temporal-shift detection transfer to physical-existence verification within the same model, which would indicate whether these are dissociable competencies.

### Why this gap matters

If decoupling persists under causally-targeted training, practitioners building audio-capable MLLMs should stop expecting alignment-scale fixes to work and instead invest in architectural mechanisms (e.g., explicit audio-grounding verification heads). If it does not persist, a cheap synthetic-data recipe becomes a practical mitigation. Either outcome constrains the design space for the next generation of audio-visual models.

### How this project addresses the gap

The methodology below constructs exactly the missing evidence: a synthetic dataset with controlled Mute/Swap/Shift conditions, a lightweight fine-tuning protocol with preference pairs contrasting correct vs. hallucinated audio-visual alignment, and a probing evaluation that dissociates temporal detection from existence verification, all within a single free-tier CPU job.

## Expected results

We anticipate that synthetic training will substantially improve Shift (temporal misalignment) detection but yield small or statistically non-significant gains on Mute and Swap tasks. This pattern — dissociable improvement — would support the architectural-deficiency hypothesis. The alternative outcome (uniform improvement across all three probes) would indicate the gap is data-driven and closable with targeted synthetic data. Either result is informative; a paired statistical comparison across probe types with confidence intervals provides the confirmatory/falsifying measurement, and we would require improvement differences beyond bootstrap 95% CIs to claim an effect.

## Methodology sketch

- **Data generation**: Use `numpy` and `pydub` on CPU to synthesize ~500 short (≤5s) samples across three conditions: (1) **Silence-Only** (visible speech-like visual motion, silent audio), (2) **Sound-Only/Swap** (visual content paired with unrelated audio), (3) **Sync-Shift** (audio delayed by 500ms), plus matched positive controls.
- **Model selection**: Use a small open-source audio-capable MLLM (e.g., Qwen2-Audio-0.5B or comparable ≤1B-parameter model) with a frozen vision encoder, quantized to fit the 7 GB RAM envelope.
- **Training protocol**: Apply parameter-efficient fine-tuning (LoRA) with Direct Preference Optimization on preference pairs contrasting correct vs. hallucinated audio-visual alignment answers; run in ≤30-minute checkpointed chunks to stay within the 6-hour GHA job limit.
- **Evaluation framework**: Run the Thud-style probing suite (Shift, Mute, Swap binary questions) on the fine-tuned model and on the unmodified base model.
- **Baseline comparison**: The unmodified base model serves as the control; optionally include a model fine-tuned on generic audio-visual QA pairs to isolate the causal-data effect.
- **Statistical analysis**: McNemar's test per probe type (paired, binary outcomes) plus bootstrap 95% CIs on accuracy deltas; report the Shift-vs-Mute/Swap improvement difference as the key statistic.
- **Compute plan**: Entire pipeline (synthesis, LoRA fine-tuning, inference, statistics) executes end-to-end on a GitHub Actions free-tier runner (2 CPU, 7 GB RAM, ≤6h); no GPU, no external datasets beyond the model weights from HuggingFace.
- **Validation independence**: Evaluation uses held-out synthetic samples whose ground-truth condition labels are fixed by the generation script's random seed, disjoint from the fine-tuning split; the predicted variable (probe accuracy) is measured from model text outputs, not from any internal representation or feature used in training.

## Duplicate-check

- Reviewed existing ideas: None (fresh extension of prior work).
- Closest match: N/A (no existing fleshed-out ideas in corpus).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-10-10T21:22:33Z
**Outcome**: success_after_expansion
**Original term**: llmXive follow-up: extending "When Vision Speaks for Sound" computer science
**Verified citation count**: 5

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "When Vision Speaks for Sound" computer science | 0 |
| 1 | audio-visual cross-modal learning | 5 |
| 2 | visual sound source localization | 0 |
| 3 | audio-visual correspondence | 0 |
| 4 | audio-driven video generation | 0 |
| 5 | cross-modal retrieval between audio and video | 0 |
| 6 | multimodal representation learning | 0 |
| 7 | vision-guided audio generation | 0 |
| 8 | audio-visual scene understanding | 0 |
| 9 | self-supervised audio-visual pretraining | 0 |
| 10 | sound source separation guided by visual cues | 0 |
| 11 | audio-visual event detection | 0 |
| 12 | audio-visual question answering | 0 |
| 13 | lip reading and speech recognition from video | 0 |
| 14 | cross-modal knowledge transfer | 0 |
| 15 | audio-visual synchronization | 0 |
| 16 | embodied audio-visual navigation | 0 |
| 17 | multimodal foundation models | 0 |
| 18 | audio-visual saliency prediction | 0 |
| 19 | visual-to-audio sensory translation | 0 |
| 20 | contrastive audio-visual learning | 0 |

### Verified citations

1. **Learning in Audio-visual Context: A Review, Analysis, and New Perspective** (2022). Yake Wei, Di Hu, Yapeng Tian, Xuelong Li. arXiv. [2208.09579](https://arxiv.org/abs/2208.09579). PDF-sampled: No.
2. **Learning Audio-Visual Dereverberation** (2021). Changan Chen, Wei Sun, David Harwath, Kristen Grauman. arXiv. [2106.07732](https://arxiv.org/abs/2106.07732). PDF-sampled: No.
3. **Semantic Audio-Visual Navigation** (2020). Changan Chen, Ziad Al-Halah, Kristen Grauman. arXiv. [2012.11583](https://arxiv.org/abs/2012.11583). PDF-sampled: No.
4. **CMAL: A Novel Cross-Modal Associative Learning Framework for Vision-Language Pre-Training** (2024). Zhiyuan Ma, Jianjun Li, Guohui Li, Kaiyan Huang. arXiv. [2410.12595](https://arxiv.org/abs/2410.12595). PDF-sampled: No.
5. **Audio-visual Speech Enhancement Using Conditional Variational Auto-Encoders** (2019). Mostafa Sadeghi, Simon Leglaive, Xavier Alameda-PIneda, Laurent Girin, Radu Horaud. arXiv. [1908.02590](https://arxiv.org/abs/1908.02590). PDF-sampled: No.
