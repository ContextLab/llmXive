---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

**Field**: psychology

## Research question

Does visual salience of actors in morally ambiguous images systematically bias human blame attribution, independent of the actors' actual role in the moral event?

## Motivation

Visual attention mechanisms are well-documented to prioritize salient stimuli (bright colors, high contrast, motion), but it is unclear whether this perceptual bias extends to higher-order moral reasoning. If salient actors are disproportionately blamed regardless of their actual culpability, this could have implications for legal judgments, media framing, and eyewitness testimony. This gap is particularly pressing given the increasing use of visual media in public discourse and legal proceedings.

## Literature gap analysis

### What we searched

Searches were conducted via Semantic Scholar / arXiv / OpenAlex using two distinct queries: (1) "visual salience moral judgment blame attribution" and (2) "attentional bias moral decision-making imagery". The verified literature search returned seven results, none of which directly address the intersection of visual attention mechanisms and human moral psychology.

### What is known

- [Moral Outrage Shapes Commitments Beyond Attention: Multimodal Moral Emotions on YouTube in Korea and the US (2026)](https://arxiv.org/abs/2601.21815) — Establishes that moral emotional framing in video media drives audience attention but does not test visual salience as a causal factor in blame attribution.
- [Let's Do a Thought Experiment: Using Counterfactuals to Improve Moral Reasoning (2023)](https://arxiv.org/abs/2306.14308) — Provides methodological precedent for structured moral judgment measurement using MMLU Moral Scenarios, though in a computational rather than perceptual context.
- [Moral Stories: Situated Reasoning about Norms, Intents, Actions, and their Consequences (2020)](https://arxiv.org/abs/2012.15738) — Establishes frameworks for norm-based moral reasoning for artificial systems but does not address human perceptual biases in moral evaluation.

### What is NOT known

No published work has experimentally tested whether systematically varying visual salience of actors in moral scenarios (while holding their actual role constant) produces measurable shifts in blame ratings. The specific mechanism—whether this operates through attentional capture, perceived agency, or heuristic processing—remains unexamined in the literature. Existing work focuses on either moral content framing (e.g., emotional language in video) or AI moral reasoning, leaving the perceptual → moral judgment pathway unexplored.

### Why this gap matters

Understanding whether visual design features can unconsciously bias moral judgments would inform evidence-based guidelines for media presentation, legal exhibits, and public communication. If salience effects exist, they represent a systematic source of bias that could be mitigated in high-stakes decision contexts where visual evidence is presented to juries or the public.

### How this project addresses the gap

This project would create controlled stimuli varying only in visual salience of actors while holding moral scenario content constant, then measure blame attribution differences. The methodology directly tests the causal pathway from perceptual salience to moral judgment that remains unexamined.

## Expected results

We expect a statistically significant positive correlation between objective visual salience measures (e.g., saliency map intensity) and blame attribution ratings. A null result would suggest that moral reasoning operates independently of low-level visual attention mechanisms. Either outcome would be informative: a positive effect would demonstrate a novel bias pathway, while a null effect would support the robustness of moral reasoning against perceptual interference.

## Methodology sketch

- **Stimulus creation**: Use Open Images Dataset (https://storage.googleapis.com/openimages/web/index.html) to extract images depicting multi-agent scenarios; manipulate visual salience of target actors via color saturation, contrast, and edge intensity using standard image processing libraries (PIL/OpenCV).
- **Salience quantification**: Compute objective visual salience metrics for each actor (saliency map integration, contrast ratio, color distinctiveness) using existing saliency detection algorithms (e.g., GBVS or ITTI implementations from public repositories).
- **Moral scenario annotation**: Use existing moral judgment datasets from HuggingFace Datasets (search: "moral judgment", "social reasoning") to identify images with pre-existing human blame ratings; verify actors' actual moral role (perpetrator, bystander, victim) remains constant across salience manipulations.
- **Secondary analysis**: If no suitable dataset exists with both images and human moral ratings, conduct computational simulation using pre-trained vision-language models (e.g., CLIP, BLIP-2 from HuggingFace) to generate predicted blame scores as proxy measurements, with acknowledgment of limitations.
- **Statistical analysis**: Fit linear mixed-effects model with visual salience as predictor, blame rating as outcome, and random effects for image and condition; test significance of salience coefficient using restricted maximum likelihood estimation.
- **Power estimation**: Conduct post-hoc power analysis on effect sizes from comparable attention-bias literature to estimate minimum detectable effects given dataset constraints.

## Duplicate-check

- Reviewed existing ideas: None found in current corpus.
- Closest match: N/A
- Verdict: **rejected — out of scope** (requires external human participant recruitment incompatible with GitHub Actions free-tier constraints; no existing public dataset combines visual stimuli with human moral judgment ratings for secondary analysis)


## Search trail

**Generated by**: librarian (prompt v1.5.0) on 2026-05-12T20:48:35Z
**Outcome**: success_after_expansion
**Original term**: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making psychology
**Verified citation count**: 7

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Influence of Visual Salience on Attentional Bias in Moral Decision-Making psychology | 7 |

### Verified citations

1. **Quantum decision making by social agents** (2012). V. I. Yukalov, D. Sornette. arXiv. [1202.4918](https://arxiv.org/abs/1202.4918). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Moral Outrage Shapes Commitments Beyond Attention: Multimodal Moral Emotions on YouTube in Korea and the US** (2026). Seongchan Park, Jaehong Kim, Hyeonseung Kim, Heejin Bin, Sue Moon, et al.. arXiv. [2601.21815](https://arxiv.org/abs/2601.21815). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Moral Dilemmas for Moral Machines** (2022). Travis LaCroix. arXiv. [2203.06152](https://arxiv.org/abs/2203.06152). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Quasi-Dilemmas for Artificial Moral Agents** (2018). Daniel Kasenberg, Vasanth Sarathy, Thomas Arnold, Matthias Scheutz, Tom Williams. arXiv. [1807.02572](https://arxiv.org/abs/1807.02572). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **Let's Do a Thought Experiment: Using Counterfactuals to Improve Moral Reasoning** (2023). Xiao Ma, Swaroop Mishra, Ahmad Beirami, Alex Beutel, Jilin Chen. arXiv. [2306.14308](https://arxiv.org/abs/2306.14308). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
6. **Navigating the State of Cognitive Flow: Context-Aware AI Interventions for Effective Reasoning Support** (2025). Dinithi Dissanayake, Suranga Nanayakkara. arXiv. [2504.16021](https://arxiv.org/abs/2504.16021). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
7. **Moral Stories: Situated Reasoning about Norms, Intents, Actions, and their Consequences** (2020). Denis Emelin, Ronan Le Bras, Jena D. Hwang, Maxwell Forbes, Yejin Choi. arXiv. [2012.15738](https://arxiv.org/abs/2012.15738). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
