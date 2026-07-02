---
field: linguistics
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration"

## Summary of the prior work
The paper introduces TIDE, a framework that enables AI agents to proactively discover multiple hidden problems within user contexts (like workspaces or codebases) rather than just reacting to explicit requests. It achieves this through two key mechanisms: iterative discovery, which conditions subsequent rounds on previously found issues to expand coverage, and thought templates, which are reusable schemas that ground predictions in recognizable problem classes. The authors demonstrate that this approach significantly outperforms single-shot and parallel multi-agent baselines in identifying and resolving coexisting, non-salient issues.

## Proposed extension
**Research Question:** Can lightweight, rule-based "micro-templates" derived from static analysis heuristics replace or augment the LLM-generated thought templates in TIDE to maintain high discovery coverage while reducing inference latency and computational cost by an order of magnitude?

This matters because the original TIDE framework relies on iterative LLM calls to generate and refine thought templates, which may be computationally prohibitive for real-time, continuous monitoring of large-scale user environments on CPU-only edge devices or low-cost servers. If static heuristics can encode the necessary "problem class" logic, TIDE could become a practical, always-on discovery tool for resource-constrained settings without sacrificing the ability to find hidden issues.

## Methodology sketch
**Data:** We will curate a subset of the original TIDE evaluation datasets (personal workspaces and software repositories) containing 500 instances with known ground-truth hidden problems, alongside a new set of 200 synthetic "edge-case" instances designed to test the limits of rule-based detection.

**Procedure:** We will implement a "TIDE-Lite" variant where the "Thought Template" generation step is replaced by a deterministic pipeline of static analysis rules (e.g., regex patterns for common config errors, dependency graph traversal for unused imports, and simple metric thresholds for code complexity) rather than LLM prompting. We will run this CPU-optimized version against the original TIDE and a standard single-shot baseline, measuring three metrics: (1) problem discovery recall (F1 score against ground truth), (2) average time-to-discovery per problem, and (3) CPU utilization. We will also conduct a human evaluation on a random sample of 50 discovered issues to assess the "actionability" of the findings compared to the LLM-based approach.

**Expected Result:** We anticipate that TIDE-Lite will achieve 85-90% of the original TIDE's discovery recall for high-frequency, structural problems while reducing inference latency by 95% and operating entirely within CPU constraints. We expect the method to struggle slightly more with semantic, context-dependent issues (e.g., logical inconsistencies in documentation), but the trade-off in efficiency will demonstrate that a hybrid approach (rules for common classes, LLM for rare classes) is optimal for scalable, proactive discovery.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration** — Soyeong Jeong, Jinheon Baek, Minki Kang, Sung Ju Hwang. https://arxiv.org/abs/2606.04743.

```bibtex
@article{orig_arxiv_2606_04743,
  title = {TIDE: Proactive Multi-Problem Discovery via Template-Guided Iteration},
  author = {Soyeong Jeong and Jinheon Baek and Minki Kang and Sung Ju Hwang},
  year = {2026},
  eprint = {2606.04743},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.04743},
  url = {https://arxiv.org/abs/2606.04743}
}
```
