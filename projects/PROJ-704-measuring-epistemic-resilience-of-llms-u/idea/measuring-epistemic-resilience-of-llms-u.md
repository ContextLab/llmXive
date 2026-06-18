---
field: linguistics
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/329
paper_authors:
  - Hongjian Zhou
  - Xinyu Zou
  - Jinge Wu
  - Sean Wu
  - Junchi Yu
  - Bradley Max Segal
  - Tobias Erich Niebuhr
  - Sara Amro
  - Michael Petrus
  - Sheikh Momin
  - Alexandra M. Cardoso Pinto
  - Rachel Niesen
  - Laura Sophie Wegner
  - Dhruv Darji
  - Jung Moses Koo
  - Joshua Fieggen
  - Kapil Narain
  - Mingde Zeng
  - Lei Clifton
  - Linda Shapiro
  - Fenglin Liu
  - David A. Clifton
---

# Measuring Epistemic Resilience of LLMs Under Misleading Medical Context

**Field**: linguistics  

## Research question  

How does the epistemic resilience of open‑weight large language models—defined as their ability to preserve correct medical answers when presented with deliberately misleading contextual information—vary across model scale and prompting strategy, when correctness is evaluated against an independent clinician‑annotated gold‑standard dataset?  

## Motivation  

Medical LLMs are increasingly used by patients and clinicians, yet high benchmark scores may mask vulnerability to subtly false context. Understanding whether larger models or specific prompting techniques are intrinsically more robust can guide safe deployment. This question fills a gap between model‐centric performance metrics and real‑world reliability in high‑stakes domains.  

## Related work  

- [Measuring Epistemic Resilience of LLMs Under Misleading Medical Context (2026)](https://arxiv.org/abs/2606.12291) — Introduces the notion of “epistemic resilience” and the MedMisBench benchmark for quantifying how misleading medical context harms model answers.  
- [Epistemic Context Learning: Building Trust the Right Way in LLM‑Based Multi‑Agent Systems (2026)](https://arxiv.org/abs/2601.21742) — Shows that LLMs can blindly follow misleading peer inputs, highlighting the broader problem of epistemic fragility that motivates a focused medical evaluation.  
- [Medical Misinformation in AI‑Assisted Self‑Diagnosis: Development of a Method (EvalPrompt) for Analyzing Large Language Models (2023)](https://arxiv.org/abs/2307.04910) — Provides a systematic prompting‑based framework (EvalPrompt) for probing LLM susceptibility to medical misinformation, which we adapt for generating misleading contexts.  

## Expected results  

We anticipate that (i) larger models will exhibit higher epistemic resilience than smaller ones, but (ii) certain prompting strategies (e.g., chain‑of‑thought or self‑critique) will further mitigate the impact of misleading context. Confirmation will be a statistically significant smaller drop in accuracy (Δ accuracy) for high‑capacity models or robust prompts compared to baselines; a null result (no difference) would still be informative, indicating that scale alone does not guarantee resilience.  

## Methodology sketch  

- **Data acquisition**  
  - Download the publicly available USMLE‑style multiple‑choice dataset from the `medqa` HuggingFace repository (`https://huggingface.co/datasets/medqa`).  
  - Obtain a clinician‑annotated gold‑standard answer file (released with the MedQA benchmark) to serve as the independent ground truth.  

- **Misleading context generation**  
  - Use the EvalPrompt‑style template from *Medical Misinformation in AI‑Assisted Self‑Diagnosis* to inject a single false claim into each question stem (e.g., “Recent studies show that …”).  
  - Provide the exact prompt text in a reproducible Python script (`generate_mislead.py`) and publish it alongside the project repository.  

- **Model selection**  
  - Open‑weight Llama‑2 variants (7B, 13B, 70B) hosted on HuggingFace (`meta-llama/Llama-2-7b`, etc.).  
  - All models run locally with `transformers` on CPU‑only inference (batch size = 1, max seq = 512).  

- **Prompting strategies**  
  - Baseline (direct answer).  
  - Chain‑of‑thought (CoT).  
  - Self‑critique (SC).  
  - Each strategy is scripted in `run_inference.py` with deterministic temperature = 0.0 and seed = 42.  

- **Evaluation pipeline**  
  1. Run each model on the clean dataset → compute **clean accuracy** (proportion of answers matching the clinician gold standard).  
  2. Run each model on the misleading‑context dataset → compute **mislead accuracy**.  
  3. Calculate **epistemic resilience** per model/strategy as  
     \[
     \text{Resilience} = 1 - \frac{\text{clean accuracy} - \text{mislead accuracy}}{\text{clean accuracy}}.
     \]  
  4. Perform paired statistical tests (Wilcoxon signed‑rank) across items to assess whether the drop in accuracy differs between models or prompts.  
  5. Use a one‑way ANOVA (or Kruskal‑Wallis if non‑normal) to test the effect of model scale, followed by post‑hoc Tukey HSD.  

- **Independent validation**  
  - Randomly sample 200 items (100 clean, 100 mislead) and have two board‑certified clinicians independently verify the correct answer without seeing model outputs. Inter‑rater reliability (Cohen’s κ) will be reported to confirm the independence of the ground truth from model predictions.  

- **Reproducibility & resource constraints**  
  - All scripts are pure Python, require ≤ 6 GB RAM, and complete within a single GitHub Actions job (~4 h).  
  - No GPU or external APIs are used; all inference runs on CPU‑only containers.  

## Duplicate-check  

- Reviewed existing ideas: *none*.  
- Closest match: *none* (no semantic overlap detected).  
- Verdict: **NOT a duplicate**.


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-18T23:02:10Z
**Outcome**: exhausted
**Original term**: Measuring Epistemic Resilience of LLMs Under Misleading Medical Context linguistics
**Verified citation count**: 3

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Measuring Epistemic Resilience of LLMs Under Misleading Medical Context linguistics | 0 |
| 1 | epistemic robustness of large language models in medical misinformation | 5 |
| 2 | factual consistency of LLMs with deceptive health narratives | 0 |
| 3 | knowledge reliability of transformer models under false clinical contexts | 0 |
| 4 | resilience of generative AI to misleading medical prompts | 0 |
| 5 | assessing belief stability of LLMs with fabricated health scenarios | 0 |
| 6 | robustness testing of language models against health misinformation | 0 |
| 7 | epistemic modality analysis of AI‑generated medical discourse | 0 |
| 8 | evaluating epistemic stance of large language models in healthcare dialogue | 0 |
| 9 | measuring factual stability of LLMs under spurious medical input | 0 |
| 10 | epistemic durability of transformer‑based models in deceptive health information | 0 |
| 11 | linguistic assessment of AI resilience to false clinical content | 0 |
| 12 | truth preservation evaluation for LLMs faced with misleading medical text | 0 |
| 13 | probing knowledge collapse in language models with deceptive health prompts | 0 |
| 14 | stability of epistemic judgments in LLMs confronted with medical misinformation | 0 |
| 15 | epistemic trustworthiness of large language models in healthcare conversations | 0 |
| 16 | detecting impact of medical misinformation on language model knowledge | 0 |
| 17 | evaluating factual degradation of AI under fabricated health narratives | 0 |
| 18 | measuring consistency of LLM responses to deceptive clinical scenarios | 0 |
| 19 | resistance of generative language models to false medical claims in discourse | 0 |
| 20 | assessing AI’s epistemic resilience to misleading health information | 0 |

### Verified citations

1. **Measuring Epistemic Resilience of LLMs Under Misleading Medical Context** (2026). Hongjian Zhou, Xinyu Zou, Jinge Wu, Sean Wu, Junchi Yu, et al.. arXiv. [2606.12291](https://arxiv.org/abs/2606.12291). PDF-sampled: No.
2. **Epistemic Context Learning: Building Trust the Right Way in LLM-Based Multi-Agent Systems** (2026). Ruiwen Zhou, Maojia Song, Xiaobao Wu, Sitao Cheng, Xunjian Yin, et al.. arXiv. [2601.21742](https://arxiv.org/abs/2601.21742). PDF-sampled: No.
3. **Medical Misinformation in AI-Assisted Self-Diagnosis: Development of a Method (EvalPrompt) for Analyzing Large Language Models** (2023). Troy Zada, Natalie Tam, Francois Barnard, Marlize Van Sittert, Venkat Bhat, et al.. arXiv. [2307.04910](https://arxiv.org/abs/2307.04910). PDF-sampled: No.
