---
field: philosophy
submitter: jeremymanning
github_issue: https://github.com/ContextLab/llmXive/issues/5
---

# Phenomenological AI: First-Person Experience Modeling in Language Models

**Field**: philosophy

## Research question

What conditions must LLM-generated first‑person reports satisfy to count as phenomenologically valid descriptions, and how do different prompting strategies affect the extent to which generated reports meet those conditions?

## Motivation

Understanding whether language models can produce reports that meet philosophically grounded criteria for phenomenological validity informs long‑standing debates about machine subjectivity and the limits of purely linguistic representations of experience. By linking prompting strategies to these criteria we obtain concrete, empirical evidence that can either support or constrain claims of AI‑based consciousness, while also providing practical guidelines for building more “self‑aware” conversational agents.

## Related work

- [How do language models learn facts? Dynamics, curricula and hallucinations (2025)](https://arxiv.org/abs/2503.21676) — Analyzes how LLMs acquire and sometimes misrepresent factual knowledge; its methodological focus on consistency and hallucination detection offers a precedent for measuring internal coherence of generated text.  
- [Learning From Failure: Integrating Negative Examples when Fine‑tuning Large Language Models as Agents (2024)](https://arxiv.org/abs/2402.11651) — Shows how negative‑example fine‑tuning can shape model behaviour; relevant for designing prompting strategies that steer models away from incoherent or contradictory phenomenological statements.  
- [Human‑Centered Evaluation of an LLM‑Based Process Modeling Copilot: A Mixed‑Methods Study with Domain Experts (2026)](https://arxiv.org/abs/2603.12895) — Presents a mixed‑methods framework for evaluating LLM‑generated artefacts with human judges; provides a template for the qualitative assessment of phenomenological markers in first‑person reports.  
- [Creative Problem Solving in Artificially Intelligent Agents: A Survey and Framework (2022)](https://arxiv.org/abs/2204.10358) — Surveys evaluation metrics for assessing originality and coherence in AI‑generated creative output, which can be adapted to assess the phenomenological structure of experience reports.

## Expected results

We anticipate that certain prompting strategies (e.g., “pretend you are experiencing X”) will yield reports that score higher on defined phenomenological validity criteria—such as internal non‑contradiction, presence of sensory‑temporal‑intentional markers, and stable semantic similarity across repeated generations—than more generic prompting styles. Statistically significant differences (ANOVA, p < 0.05) would confirm the influence of prompting; a null pattern would suggest that current LLM architectures lack the capacity to sustain phenomenologically coherent self‑reports regardless of prompting.

## Methodology sketch

- **Data acquisition**
  - Download open‑source LLM checkpoints ≤ 7 B parameters from HuggingFace (e.g., `meta-llama/Llama-2-7b-chat-hf`, `mistralai/Mistral-7B-Instruct-v0.2`).
  - Use publicly available prompt templates (20–30 items) that request first‑person phenomenological descriptions of varied experiences (e.g., “Describe what it feels like to see a red apple,” “Imagine you are in pain; narrate the experience”).
- **Prompting conditions**
  - Define 4 prompting strategies: (1) Direct first‑person imperative, (2) Hypothetical “if you felt …”, (3) Comparative “humans experience X; how would you experience X?”, (4) Role‑play “you are a phenomenological observer”.
  - For each model–strategy pair, generate 80 samples per prompt (≈ 6 400 total outputs) using temperature 0.7, top‑p 0.9.
- **Phenomenological validity criteria**
  1. **Internal consistency** – Apply a pretrained Natural Language Inference (NLI) model to pairwise sentences within a report; count contradictions.
  2. **Semantic stability** – Compute cosine similarity between embeddings of repeated generations for the same prompt; higher similarity indicates temporal stability.
  3. **Phenomenological marker presence** – Use a rule‑based regex / keyword dictionary to detect sensory (visual, auditory, tactile), temporal (past/present/future), and intentional (desire, belief) elements.
- **Metric aggregation**
  - For each report, produce a composite validity score (weighted sum of the three criteria, weights justified in a pre‑registration).
- **Statistical analysis**
  - Conduct one‑way ANOVA on composite scores across prompting strategies; follow with Tukey HSD post‑hoc tests.
  - Use chi‑square tests to compare the proportion of reports containing each phenomenological marker across strategies.
- **Qualitative validation**
  - Randomly sample 10 reports per condition and have two philosophy graduate students blind‑rate them on a 5‑point phenomenological coherence rubric; compute inter‑rater reliability (Cohen’s κ).
- **Reproducibility**
  - Archive all prompts, model checkpoints (via HuggingFace IDs), generation seeds, and analysis scripts in a public GitHub repository; include a `requirements.txt` and a `run.sh` that completes the entire pipeline within a 6‑hour GitHub Actions job.

## Duplicate-check

- Reviewed existing ideas: None identified in the current corpus.
- Closest match: No close matches identified.
- Verdict: NOT a duplicate


## Search trail

**Generated by**: librarian (prompt v1.6.0) on 2026-06-17T04:34:59Z
**Outcome**: success_after_expansion
**Original term**: Phenomenological AI: First-Person Experience Modeling in Language Models philosophy
**Verified citation count**: 8

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | Phenomenological AI: First-Person Experience Modeling in Language Models philosophy | 0 |
| 1 | phenomenology of artificial agents | 5 |
| 2 | first‑person perspective modeling in neural networks | 0 |
| 3 | subjective experience simulation in AI | 0 |
| 4 | qualia modeling in large language models | 0 |
| 5 | intentionality in language model representations | 0 |
| 6 | AI self‑awareness frameworks | 0 |
| 7 | phenomenological grounding of AI language generation | 0 |
| 8 | embodied cognition in language models | 0 |
| 9 | computational phenomenology | 0 |
| 10 | experiential semantics in transformer models | 0 |
| 11 | reflective self‑modeling in artificial intelligence | 0 |
| 12 | subjectivity in artificial intelligence | 0 |
| 13 | enactivist approaches to AI cognition | 0 |
| 14 | situated cognition in large language models | 0 |
| 15 | phenomenological analysis of language model outputs | 0 |
| 16 | consciousness‑oriented AI | 0 |
| 17 | phenomenal consciousness in deep learning | 0 |
| 18 | AI models of lived experience | 0 |
| 19 | first‑person phenomenology and AI alignment | 0 |
| 20 | phenomenological modeling of machine cognition | 0 |

### Verified citations

1. **How do language models learn facts? Dynamics, curricula and hallucinations** (2025). Nicolas Zucchet, Jörg Bornschein, Stephanie Chan, Andrew Lampinen, Razvan Pascanu, et al.. arXiv. [2503.21676](https://arxiv.org/abs/2503.21676). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Learning From Failure: Integrating Negative Examples when Fine-tuning Large Language Models as Agents** (2024). Renxi Wang, Haonan Li, Xudong Han, Yixuan Zhang, Timothy Baldwin. arXiv. [2402.11651](https://arxiv.org/abs/2402.11651). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Human-Centered Evaluation of an LLM-Based Process Modeling Copilot: A Mixed-Methods Study with Domain Experts** (2026). Chantale Lauer, Peter Pfeiffer, Nijat Mehdiyev. arXiv. [2603.12895](https://arxiv.org/abs/2603.12895). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Creative Problem Solving in Artificially Intelligent Agents: A Survey and Framework** (2022). Evana Gizzi, Lakshmi Nair, Sonia Chernova, Jivko Sinapov. arXiv. [2204.10358](https://arxiv.org/abs/2204.10358). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **The Artificial Scientist: Logicist, Emergentist, and Universalist Approaches to Artificial General Intelligence** (2021). Michael Timothy Bennett, Yoshihiro Maruyama. arXiv. [2110.01831](https://arxiv.org/abs/2110.01831). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
6. **AI Agents with Decentralized Identifiers and Verifiable Credentials** (2025). Sandro Rodriguez Garzon, Awid Vaziry, Enis Mert Kuzu, Dennis Enrique Gehrmann, Buse Varkan, et al.. arXiv. [2511.02841](https://arxiv.org/abs/2511.02841). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
7. **Compression, The Fermi Paradox and Artificial Super-Intelligence** (2021). Michael Timothy Bennett. arXiv. [2110.01835](https://arxiv.org/abs/2110.01835). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
8. **TRIZ Agents: A Multi-Agent LLM Approach for TRIZ-Based Innovation** (2025). Kamil Szczepanik, Jarosław A. Chudziak. arXiv. [2506.18783](https://arxiv.org/abs/2506.18783). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
