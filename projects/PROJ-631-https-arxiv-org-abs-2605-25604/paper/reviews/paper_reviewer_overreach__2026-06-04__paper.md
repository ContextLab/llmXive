---
action_items:
- id: 58aadcae5aeb
  severity: writing
  text: The claim 'hyperparameter-free weighting scheme' (Abstract, Introduction)
    is slightly misleading. The method requires initial weights {w_k} (Eq. 17), even
    if set equally. Clarify that it removes the need for *tuning* trade-off weights
    rather than being entirely free of hyperparameters.
- id: 6165207aa4d0
  severity: writing
  text: The title 'Multi-reward Reinforcement Learning' suggests generality beyond
    the GRPO framework tested. Consider narrowing to 'Multi-reward GRPO' or explicitly
    stating the GRPO scope in the abstract to avoid overreach regarding other RL algorithms.
artifact_hash: 07982a7d39aea2d81ed519d381a91780afe8b9e5e46fa8b3a223fc43d78599b4
artifact_path: projects/PROJ-631-https-arxiv-org-abs-2605-25604/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-04T07:45:07.047154Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper presents a theoretically grounded method for multi-objective optimization within the GRPO framework. The theoretical contributions (Propositions 1-3 in the Method section and Appendix) are mathematically consistent and well-proven within the scope of the defined assumptions. However, there are minor instances of overreach regarding the generalization of claims beyond the empirical evidence provided.

First, the Abstract and Introduction describe DVAO as a "hyperparameter-free weighting scheme." While the method dynamically adapts weights based on variance, it still requires the specification of initial weights $\{w_k\}$ (Equation 17), which are typically set equally in the experiments. This is a distinction from being truly hyperparameter-free. This phrasing overstates the autonomy of the method and should be tempered to reflect that it eliminates the need for manual *tuning* of trade-off weights rather than removing the parameters entirely.

Second, the title "Dynamic Variance-adaptive Advantage Optimization for Multi-reward Reinforcement Learning" implies a broad applicability to general Reinforcement Learning. The methodology and experiments are strictly confined to Group Relative Policy Optimization (GRPO) and its variants. While the title is not incorrect, it risks overgeneralization for readers expecting PPO or other algorithm compatibility. The Abstract does clarify the GRPO context, but the Title should align more closely with the specific algorithmic contribution to avoid scope creep.

Third, the claim of a "self-adaptive cross-objective regularization mechanism" (Introduction) is derived from the sensitivity analysis in Proposition 3. While the mathematical derivation holds, the functional characterization as a "regularization mechanism" implies specific generalization benefits that are only indirectly supported by the Pareto frontier results. The current evidence shows improved trade-offs, but the "regularization" terminology suggests a broader theoretical guarantee on generalization error which is not explicitly proven.

The Limitations section (Appendix) is commendably honest, acknowledging the focus on dual-objective scenarios and the reliance on reward quality. This mitigates the risk of severe overreach, but the main text should be adjusted to match this level of precision. Minor revisions to the Abstract, Introduction, and Title will ensure claims strictly align with the GRPO-specific scope and the dual-objective empirical evidence.
