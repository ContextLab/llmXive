---
field: psychology
submitter: google.gemma-3-27b-it
---

# The Influence of Visual Salience on Moral Judgments of Simulated Scenarios

**Field**: psychology

## Research question

Does increasing the visual salience of non-causal elements in morally ambiguous simulated scenarios systematically shift participants' blame and responsibility judgments toward the visually highlighted party?

## Motivation

Visual salience is a well-documented driver of attention, but its downstream effects on moral reasoning remain underexplored. If salient non-causal details (e.g., a brightly colored object, a salient speed indicator) bias blame assignments, this could explain inconsistencies in eyewitness testimony and inform ethical design in virtual reality training environments.

## Literature gap analysis

### What we searched

Searches were conducted for queries including "visual salience moral judgment," "attention bias blame responsibility," and "visual prominence moral cognition" across Semantic Scholar and arXiv. Only one paper was returned in the verified results block, and it concerns lexical anthropomorphization in AI moral judgments rather than visual salience in human scenarios.

### What is known

- [Lexical Anthropomorphization Influences on Moral Judgments of AI Bad Behavior (2026)](http://arxiv.org/abs/2604.25814v1) — This work establishes that linguistic framing (anthropomorphic language) can shift moral judgments of AI behavior, demonstrating that non-causal contextual cues affect moral reasoning in general.

### What is NOT known

No published work has measured whether visual salience cues (independent of semantic content) systematically shift blame assignments in human moral judgment scenarios. The existing literature focuses on linguistic/anthropomorphic framing, not visual attention mechanisms. There is no established benchmark for visual salience manipulation in moral judgment tasks.

### Why this gap matters

Understanding whether visual prominence alone can bias moral reasoning has implications for legal settings (eyewitness testimony reliability), virtual reality training design (ensuring ethical scenarios don't inadvertently bias participants), and theoretical models of moral cognition (attention vs. reasoning pathways).

### How this project addresses the gap

This project will systematically manipulate visual salience in public scenario datasets (e.g., images from open visual commons datasets) while keeping semantic content constant, then measure blame ratings. The methodology directly produces evidence on whether visual salience cues independently influence moral judgments.

## Expected results

We expect to find a measurable effect of visual salience on blame ratings, with visually highlighted elements associated with negligence receiving higher blame scores even when causally irrelevant. A null result would suggest visual salience does not systematically bias moral reasoning, which would be equally informative for constraining attention-based theories of moral judgment.

## Methodology sketch

- Download open visual scenario datasets (e.g., Visual Genome subset, COCO images with moral scenario annotations) using `wget` from public URLs.
- Identify 20-30 morally ambiguous scenarios from existing annotations (e.g., traffic accidents, interpersonal conflicts).
- Create visual salience manipulations using Python PIL/OpenCV: enhance contrast/brightness of target objects without changing semantic content.
- Generate 2-3 salience levels per scenario (low, medium, high) to create within-subject design.
- Deploy survey via public platform (e.g., Qualtrics free tier, Google Forms) with participant recruitment through Prolific or university subject pool (existing datasets preferred).
- Collect blame ratings (1-7 Likert scale) for each manipulated image from 100-150 participants.
- Compute within-subject effect size using repeated-measures ANOVA on salience level vs. blame rating.
- Perform post-hoc pairwise comparisons with Bonferroni correction to identify which salience contrasts drive effects.
- Run mediation analysis to test whether attention allocation (measured via self-report or eye-tracking proxy) mediates salience-blame relationship.
- Calculate statistical power post-hoc and report confidence intervals for all effect sizes.

## Duplicate-check

- Reviewed existing ideas: None in current corpus (first iteration).
- Closest match: None identified.
- Verdict: NOT a duplicate
