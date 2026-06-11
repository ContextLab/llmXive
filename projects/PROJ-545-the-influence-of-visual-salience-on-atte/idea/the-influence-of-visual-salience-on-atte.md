---
field: psychology
submitter: agent:flesh_out
---

# The Influence of Visual Salience on Attentional Bias in Moral Decision-Making

**Field**: psychology

## Research question

Does visual salience systematically modulate attentional drift patterns in computational models of moral decision-making, and can these modulations predict choice outcomes in existing moral dilemma datasets?

## Motivation

Attentional drift diffusion models (aDDM) have successfully modeled perceptual and value-based decisions by linking fixation patterns to evidence accumulation. However, whether visual salience—distinct from moral relevance—biases evidence accumulation in moral contexts remains untested. This gap matters because if salience-driven attention operates similarly in moral and perceptual domains, it suggests a domain-general mechanism that could introduce systematic bias in high-stakes moral judgments independent of actual culpability.

## Related work

- [A multiattribute attentional drift diffusion model (2021)](https://linkinghub.elsevier.com/retrieve/pii/S0749597821000431) — Establishes that attentional weighting of choice attributes in aDDM predicts decision outcomes, providing a computational framework testable on moral dilemma data.
- [The Attentional Drift Diffusion Model of Simple Perceptual Decision-Making (2017)](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2017.00468/full) — Demonstrates that fixation duration directly modulates evidence accumulation rates in perceptual tasks, establishing the mechanistic link between attention and decision trajectories.

## Expected results

We expect that incorporating visual salience as an attentional weighting parameter in aDDM will improve prediction accuracy for moral dilemma choices compared to salience-naïve models. A null result would suggest moral decisions operate via distinct mechanisms from perceptual attention, which would be equally informative for theory.

## Methodology sketch

- **Dataset acquisition**: Download the Moral Machine dataset (https://www.moralmachine.net/download) or comparable public moral dilemma dataset with binary choice outcomes and scenario attributes.
- **Visual salience computation**: For any image-based dilemmas, compute saliency maps using lightweight algorithms (ITTI or GBVS implementations available on GitHub) via OpenCV; for text-only scenarios, proxy salience via word-frequency and position-based heuristics.
- **aDDM simulation**: Implement attentional drift diffusion model in Python (NumPy/SciPy only) with parameters for drift rate, threshold, and non-decision time; inject visual salience as attentional weighting on specific attributes.
- **Parameter fitting**: Use grid search over attentional salience weights (0.0–1.0) to find values that maximize likelihood of observed choices in held-out test set.
- **Model comparison**: Fit baseline aDDM (no salience) and salience-augmented aDDM; compare using AIC/BIC and held-out log-likelihood.
- **Cross-validation**: 5-fold cross-validation to ensure results generalize across scenario types; no single scenario family dominates the effect.
- **Statistical testing**: Likelihood ratio test between nested models; report effect size as improvement in predictive accuracy (percentage points).
- **Sensitivity analysis**: Vary threshold parameters and drift noise to confirm salience effect is robust across reasonable model configurations.
- **Validation independence**: Validate model predictions against held-out choices from the dataset—these are independent of the salience computations, which derive only from stimulus properties.

## Literature gap analysis

### What we searched

Searches were conducted via Semantic Scholar / arXiv / OpenAlex using two distinct queries: (1) "attentional drift diffusion model moral decision" and (2) "visual salience moral judgment computational". The verified literature search returned two results directly relevant to attentional drift diffusion modeling, though neither explicitly tested moral contexts.

### What is known

- [A multiattribute attentional drift diffusion model (2021)](https://linkinghub.elsevier.com/retrieve/pii/S0749597821000431) — Establishes that attentional weighting of choice attributes in aDDM predicts decision outcomes, providing a computational framework testable on moral dilemma data.
- [The Attentional Drift Diffusion Model of Simple Perceptual Decision-Making (2017)](https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2017.00468/full) — Demonstrates that fixation duration directly modulates evidence accumulation rates in perceptual tasks, establishing the mechanistic link between attention and decision trajectories.

### What is NOT known

No published work has applied attentional drift diffusion models to moral decision-making scenarios with explicit visual salience parameters. The existing aDDM literature focuses on value-based and perceptual decisions, leaving open whether moral judgments follow the same attentional-evidence accumulation dynamics.

### Why this gap matters

If moral decisions operate via the same attentional mechanisms as perceptual choices, it would unify decision-making theory across domains and suggest that visual design could bias moral judgments through attentional capture. This has implications for legal exhibits, media framing, and algorithmic decision systems that present moral information visually.

### How this project addresses the gap

This project implements a salience-augmented aDDM on public moral dilemma data, directly testing whether visual salience parameters improve predictive accuracy. The computational simulation approach fills the gap by applying established attentional models to an under-studied domain without requiring new human data collection.

## Duplicate-check

- Reviewed existing ideas: None found in current corpus.
- Closest match: N/A
- Verdict: NOT a duplicate
