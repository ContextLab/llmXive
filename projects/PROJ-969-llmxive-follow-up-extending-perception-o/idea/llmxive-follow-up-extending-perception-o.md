---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers"

**Field**: computer science

## Research question

Does augmenting Multimodal Large Language Models (MLLMs) with explicit, text-based social priors (e.g., cultural norms, situational context) via retrieval-augmented prompting significantly reduce the "Prejudice Gap"—where correct trait ratings lack behavioral grounding—or is this failure mode strictly inherent to the models' visual feature extraction capabilities?

## Motivation

The original "Perception or Prejudice" work established that over 50% of correct personality ratings by MLLMs rely on superficial visual heuristics rather than valid behavioral evidence. This gap suggests models may lack the contextual understanding necessary to interpret behaviors correctly (e.g., distinguishing a nervous smile from a polite one). Determining whether this is a solvable reasoning deficit via lightweight context injection or a fundamental visual limitation is critical for deciding whether future improvements require expensive visual encoder retraining or can be achieved through efficient, CPU-tractable prompting strategies.

## Related work

- [A Survey on Multimodal Large Language Models](https://arxiv.org/abs/2306.13549) — Provides the foundational landscape of MLLM architectures, establishing the standard separation between visual encoders and LLM "brains" that this project seeks to intervene upon via prompting.
- [Benchmarking Adversarial Robustness to Bias Elicitation in Large Language Models](https://arxiv.org/abs/2504.07887) — Demonstrates methodologies for assessing bias in LLMs using automated judgment, offering a precedent for the three-tier evaluation framework (rating, reasoning, grounding) adapted from the prior work.
- [Revealing Hidden Bias in AI: Lessons from Large Language Models](https://arxiv.org/abs/2410.16927) — Highlights how LLMs perpetuate stereotypes in interview contexts, reinforcing the necessity of investigating whether external social context can mitigate such biases in multimodal settings.
- [Intersectional Bias in Japanese Large Language Models from a Contextualized Perspective](https://arxiv.org/abs/2506.12327) — Illustrates the impact of contextualized perspectives on bias reduction, supporting the hypothesis that injecting situational norms may override superficial pattern matching.

## Expected results

We expect that models with sufficient reasoning capacity will show a statistically significant reduction in the Prejudice Rate (e.g., from >50% to <30%) when provided with relevant social priors, confirming that the "Prejudice Gap" is partially a reasoning deficit. Conversely, models relying purely on visual heuristics will show no improvement, indicating a hard limit of the visual feature extraction layer. A null result across all models would suggest the gap is entirely architectural and immune to prompt-based context injection.

## Methodology sketch

- **Data Acquisition**: Download the MM-OCEAN validation subset (~200 video samples) from the original repository (arXiv:2605.22109) and the associated metadata (transcripts, video IDs).
- **Context Construction**: Build a static, CPU-accessible JSON knowledge base mapping video metadata (e.g., "job interview," "East Asian setting") to curated cultural norms and situational scripts; ensure no new data collection is required.
- **Baseline Execution**: Run the original 27 MLLMs on the GPR task using the standard prompt to establish the baseline Prejudice Rate (PR) and Holistic-Grounding Rate (HR).
- **Intervention Prompting**: Implement a "Context-Grounded Chain-of-Thought" prompt that injects the retrieved Context Profile before the reasoning step, directing the model to analyze situational norms before deriving trait ratings.
- **Control Condition**: Execute a parallel ablation where the context profile is replaced with random noise to isolate the effect of relevant social priors from mere prompt length or distraction.
- **Evaluation**: Re-evaluate model outputs using the three-tier metrics (Rating, Reasoning, Grounding) to calculate the shift in PR and the Integration-failure Rate (IR).
- **Statistical Analysis**: Apply a paired t-test (or Wilcoxon signed-rank test if normality assumptions fail) to compare baseline and intervention PRs across the model ensemble, ensuring the validation metric (grounding score) is derived from the model's explicit textual justification, which is independent of the input visual features.
- **Resource Check**: Ensure all inference runs and evaluations fit within the 6-hour GHA limit by processing the 200-sample subset in batches and using quantized or smaller open-source MLLMs where necessary.

## Duplicate-check

- Reviewed existing ideas: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers".
- Closest match: None (This is a specific follow-up proposal extending the prior work with a distinct intervention).
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-07-19T09:53:53Z
**Outcome**: exhausted
**Original term**: llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers" computer science
**Verified citation count**: 4

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | llmXive follow-up: extending "Perception or Prejudice: Can MLLMs Go Beyond First Impressions of Pers" computer science | 0 |
| 1 | multimodal large language model bias assessment | 5 |
| 2 | first impression bias in vision-language models | 0 |
| 3 | MLLM stereotyping and prejudice detection | 0 |
| 4 | multimodal model fairness beyond initial context | 0 |
| 5 | visual bias in large language models | 0 |
| 6 | perception versus prejudice in AI agents | 0 |
| 7 | multimodal reasoning and social bias mitigation | 0 |
| 8 | evaluating MLLM judgment accuracy on social cues | 0 |
| 9 | first impression errors in multimodal understanding | 0 |
| 10 | bias amplification in vision-language pretraining | 0 |
| 11 | social perception biases in generative multimodal AI | 0 |
| 12 | multimodal model hallucination of social stereotypes | 0 |
| 13 | extending MLLM evaluation for social bias | 0 |
| 14 | vision-language model prejudice quantification | 0 |
| 15 | cognitive bias in multimodal large language models | 0 |
| 16 | initial impression reliability in AI perception systems | 0 |
| 17 | multimodal fairness benchmarks for first impressions | 0 |
| 18 | social bias in image-text foundation models | 0 |
| 19 | MLLM overconfidence in social judgment tasks | 0 |
| 20 | mitigating first-impression bias in multimodal agents | 0 |

### Verified citations

1. **A Survey on Multimodal Large Language Models** (2023). Shukang Yin, Chaoyou Fu, Sirui Zhao, Ke Li, Xing Sun, et al.. arXiv. [2306.13549](https://arxiv.org/abs/2306.13549). PDF-sampled: No.
2. **Benchmarking Adversarial Robustness to Bias Elicitation in Large Language Models: Scalable Automated Assessment with LLM-as-a-Judge** (2025). Riccardo Cantini, Alessio Orsino, Massimo Ruggiero, Domenico Talia. arXiv. [2504.07887](https://arxiv.org/abs/2504.07887). PDF-sampled: No.
3. **Revealing Hidden Bias in AI: Lessons from Large Language Models** (2024). Django Beatty, Kritsada Masanthia, Teepakorn Kaphol, Niphan Sethi. arXiv. [2410.16927](https://arxiv.org/abs/2410.16927). PDF-sampled: No.
4. **Intersectional Bias in Japanese Large Language Models from a Contextualized Perspective** (2025). Hitomi Yanaka, Xinqi He, Jie Lu, Namgi Han, Sunjin Oh, et al.. arXiv. [2506.12327](https://arxiv.org/abs/2506.12327). PDF-sampled: No.
