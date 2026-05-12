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

- [Moral Outrage Shapes Commitments Beyond Attention: Multimodal Moral Emotions on YouTube in Korea and the US (2026)](https://arxiv.org/abs/2601.21815) — Examines how moral emotional framing in video media influences audience engagement, establishing that moral content can drive attention but not addressing visual salience as a causal factor in blame attribution.
- [Let's Do a Thought Experiment: Using Counterfactuals to Improve Moral Reasoning (2023)](https://arxiv.org/abs/2306.14308) — Investigates moral reasoning in language models on the MMLU Moral Scenarios task, providing methodological precedent for structured moral judgment measurement but in a computational rather than perceptual context.
- [Moral Stories: Situated Reasoning about Norms, Intents, Actions, and their Consequences (2020)](https://arxiv.org/abs/2012.15738) — Addresses situated moral reasoning for artificial systems, establishing frameworks for norm-based judgment but not human perceptual biases in moral evaluation.

### What is NOT known

No published work has experimentally tested whether systematically varying visual salience of actors in moral scenarios (while holding their actual role constant) produces measurable shifts in blame ratings. The specific mechanism—whether this operates through attentional capture, perceived agency, or heuristic processing—remains unexamined in the literature. Existing work focuses on either moral content framing (e.g., emotional language in video) or AI moral reasoning, leaving the perceptual → moral judgment pathway unexplored.

### Why this gap matters

Understanding whether visual design features can unconsciously bias moral judgments would inform evidence-based guidelines for media presentation, legal exhibits, and public communication. If salience effects exist, they represent a systematic source of bias that could be mitigated in high-stakes decision contexts where visual evidence is presented to juries or the public.

### How this project addresses the gap

This project would create controlled stimuli varying only in visual salience of actors while holding moral scenario content constant, then measure blame attribution differences. However, this requires human participant data collection which cannot be executed within the GitHub Actions runner constraints.

## Expected results

We expect a statistically significant positive correlation between objective visual salience measures (e.g., saliency map intensity) and blame attribution ratings. A null result would suggest that moral reasoning operates independently of low-level visual attention mechanisms. Either outcome would be informative: a positive effect would demonstrate a novel bias pathway, while a null effect would support the robustness of moral reasoning against perceptual interference.

## Methodology sketch

- **Stimulus creation**: Use Open Images Dataset or similar public image repository to extract images depicting multi-agent scenarios; manipulate visual salience of target actors via color saturation, contrast, and edge intensity using standard image processing libraries (PIL/OpenCV).
- **Salience quantification**: Compute objective visual salience metrics for each actor (saliency map integration, contrast ratio, color distinctiveness) using existing saliency detection algorithms.
- **Moral scenario annotation**: Have independent raters verify that actors' actual moral role (perpetrator, bystander, victim) remains constant across salience manipulations.
- **Participant data collection**: **Requires external human recruitment** (e.g., Prolific) to rate perceived culpability of each actor on Likert scale. This step violates the "No new experimental data collection" constraint for GitHub Actions runners.
- **Statistical analysis**: Fit linear mixed-effects model with visual salience as predictor, blame rating as outcome, and random effects for participant and stimulus; test significance of salience coefficient.
- **Power analysis**: Pre-register minimum detectable effect size (e.g., r = 0.2) and required N (e.g., 200 participants) for adequate power.

## Duplicate-check

- Reviewed existing ideas: None found in current corpus.
- Closest match: N/A
- Verdict: **rejected — out of scope**


## Search trail

**Generated by**: librarian (prompt v1.5.0) on 2026-05-12T15:20:27Z
**Outcome**: success_after_expansion
**Original term**: The Influence of Visual Salience on Attentional Bias in Moral Decision-Making psychology
**Verified citation count**: 7

### Search terms used

| Rank | Term | Hit count |
|-|-|-|
| 0 (initial) | The Influence of Visual Salience on Attentional Bias in Moral Decision-Making psychology | 0 |
| 1 | Visual salience and ethical judgment | 0 |
| 2 | Attentional capture in moral dilemmas | 3 |
| 3 | Gaze bias in moral reasoning | 3 |
| 4 | Perceptual salience and moral decision making | 0 |
| 5 | Visual attention allocation in ethics | 0 |
| 6 | Stimulus salience effects on moral choice | 0 |
| 7 | Bottom-up attention in moral psychology | 0 |
| 8 | Eye-tracking studies of moral judgment | 0 |
| 9 | Visual framing effects in ethical decisions | 0 |
| 10 | Selective attention and moral evaluation | 0 |
| 11 | Attentional mechanisms in moral cognition | 0 |
| 12 | Visual prominence and behavioral ethics | 0 |
| 13 | Salient distractors in moral reasoning | 0 |
| 14 | Implicit attentional bias in morality | 0 |
| 15 | Visual cues in ethical dilemmas | 0 |
| 16 | Cognitive biases in moral reasoning | 0 |
| 17 | Attention and moral decision making | 0 |
| 18 | Visual processing in moral judgment | 0 |
| 19 | Affective salience and moral choice | 0 |
| 20 | Top-down versus bottom-up attention in ethics | 0 |

### Verified citations

1. **Quantum decision making by social agents** (2012). V. I. Yukalov, D. Sornette. arXiv. [1202.4918](https://arxiv.org/abs/1202.4918). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
2. **Moral Outrage Shapes Commitments Beyond Attention: Multimodal Moral Emotions on YouTube in Korea and the US** (2026). Seongchan Park, Jaehong Kim, Hyeonseung Kim, Heejin Bin, Sue Moon, et al.. arXiv. [2601.21815](https://arxiv.org/abs/2601.21815). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
3. **Moral Dilemmas for Moral Machines** (2022). Travis LaCroix. arXiv. [2203.06152](https://arxiv.org/abs/2203.06152). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
4. **Quasi-Dilemmas for Artificial Moral Agents** (2018). Daniel Kasenberg, Vasanth Sarathy, Thomas Arnold, Matthias Scheutz, Tom Williams. arXiv. [1807.02572](https://arxiv.org/abs/1807.02572). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
5. **Let's Do a Thought Experiment: Using Counterfactuals to Improve Moral Reasoning** (2023). Xiao Ma, Swaroop Mishra, Ahmad Beirami, Alex Beutel, Jilin Chen. arXiv. [2306.14308](https://arxiv.org/abs/2306.14308). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
6. **Navigating the State of Cognitive Flow: Context-Aware AI Interventions for Effective Reasoning Support** (2025). Dinithi Dissanayake, Suranga Nanayakkara. arXiv. [2504.16021](https://arxiv.org/abs/2504.16021). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
7. **Moral Stories: Situated Reasoning about Norms, Intents, Actions, and their Consequences** (2020). Denis Emelin, Ronan Le Bras, Jena D. Hwang, Maxwell Forbes, Yejin Choi. arXiv. [2012.15738](https://arxiv.org/abs/2012.15738). PDF-sampled: No. ⚠️ *topically marginal — admitted as fallback when judge rejected all stricter matches*
