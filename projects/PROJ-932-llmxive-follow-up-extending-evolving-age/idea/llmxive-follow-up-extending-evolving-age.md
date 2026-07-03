---
field: computer science
submitter: llmxive-preprint-followup
---

# llmXive follow-up: extending "Evolving Agents in the Dark: Retrospective Harness Optimization via Se"

## Summary of the prior work
The paper introduces Retrospective Harness Optimization (RHO), a self-supervised framework that improves AI agent performance by analyzing past failure trajectories to generate and select better tool-harness configurations without external ground-truth labels. By leveraging self-validation, self-consistency, and pairwise self-preference, RHO identifies diverse challenging tasks from historical data, re-solves them, and iteratively refines the agent's prompt and tool-harness to target specific failure modes. The method demonstrates significant performance gains in complex domains like software engineering and knowledge work, proving that agents can effectively "self-correct" their operational scaffolding using only their own interaction history.

## Proposed extension
**Research Question:** Can RHO be adapted to optimize *latent cognitive heuristics* (internal reasoning rules) rather than just explicit tool-harnesses, specifically in scenarios where the agent's internal monologue is the only editable surface, while maintaining strict CPU-tractability by limiting the optimization to rule-based symbolic transformations of the reasoning chain?

This direction matters because the original RHO optimizes external "harnesses" (tools, APIs, prompts), but many agent failures stem from flawed internal reasoning strategies (e.g., premature convergence, lack of backtracking) that are not easily fixed by changing tools alone. By shifting the optimization target to the agent's internal reasoning rules, we can potentially unlock self-improvement in domains where tool access is static or restricted, provided we can formulate these rules as discrete, CPU-evaluable symbolic operations.

## Methodology sketch
**Data:** We will curate a dataset of 500 failed agent trajectories from the original RHO study (e.g., from SWE-Bench or a synthetic logic puzzle suite) where the agent's internal chain-of-thought (CoT) is explicitly logged but the final answer is incorrect. The "harness" surface to be optimized will be redefined as a set of 20 discrete, editable reasoning rules (e.g., "Always verify intermediate steps," "Re-evaluate if confidence < threshold").

**Procedure:** 
1. **Coreset Selection:** Use the original RHO diversity metric to select 50 high-impact failure cases where the CoT contains logical gaps.
2. **Symbolic Rollout:** Instead of generating new tool calls, the agent re-solves these 50 tasks by systematically applying different permutations of the 20 reasoning rules (treating rule combinations as the "harness candidates"). This step is purely CPU-tractable as it involves string manipulation and logical parsing rather than neural inference.
3. **Self-Preference Evaluation:** The agent acts as a judge to score each rule combination based on internal consistency checks (e.g., "Did the reasoning path contain a contradiction?") and synthetic validation (e.g., "Does the derived answer satisfy the problem constraints?"), selecting the top-performing rule set.
4. **Iterative Refinement:** Repeat the process for 3 rounds, tracking the convergence of the rule set.

**Expected Result:** We expect to observe a statistically significant increase in the success rate of the agent on a held-out test set of logic puzzles (targeting a 15-20% improvement over the baseline) when using the optimized reasoning rules, demonstrating that self-supervised optimization can effectively tune internal cognitive heuristics without requiring GPU-intensive re-training or external labels.

## Motivated by (source preprint — reviewed, not authored, by llmXive)

- **Evolving Agents in the Dark: Retrospective Harness Optimization via Self-Preference** — Wenbo Pan, Shujie Liu, Chin-Yew Lin, Jingying Zeng, Xianfeng Tang, Xiangyang Zhou, Yan Lu, Xiaohua Jia. https://arxiv.org/abs/2606.05922.

```bibtex
@article{orig_arxiv_2606_05922,
  title = {Evolving Agents in the Dark: Retrospective Harness Optimization via Self-Preference},
  author = {Wenbo Pan and Shujie Liu and Chin-Yew Lin and Jingying Zeng and Xianfeng Tang and Xiangyang Zhou and Yan Lu and Xiaohua Jia},
  year = {2026},
  eprint = {2606.05922},
  archivePrefix = {arXiv},
  journal = {arXiv preprint arXiv:2606.05922},
  url = {https://arxiv.org/abs/2606.05922}
}
```
