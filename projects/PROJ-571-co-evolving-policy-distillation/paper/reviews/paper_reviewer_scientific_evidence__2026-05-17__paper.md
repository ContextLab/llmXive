---
artifact_hash: de55394b12e45f35d14619842228dd7f355c964a3689a145deba5b04573843f5
artifact_path: projects/PROJ-571-co-evolving-policy-distillation/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.0.0
reviewed_at: '2026-05-17T14:45:38.911319Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The empirical evidence supporting CoPD's efficacy relies primarily on single-run benchmark scores without reported standard deviations or statistical significance tests. RLVR training is inherently stochastic due to sampling variance; consequently, small gains (e.g., Table 1, Text Avg: 58.76 vs. 57.89) require validation across multiple seeds to rule out random fluctuation. The claim of "significantly outperforming" in the Abstract is unsupported without p-values or confidence intervals.

Figure 2 presents a pilot study demonstrating a strong correlation ($r=0.89$) between top-$k$ overlap and OPD gain. However, this relies on temperature variation to induce overlap, which may not generalize to the co-evolution dynamics in Section 3. The causal link between maintaining overlap (Fig 3a) and final performance needs stronger evidence, as other factors (e.g., training dynamics) could drive the result.

Table 3 ablations confirm component necessity but do not fully control for compute budget variations during the $S_{RL}/S_{OPD}$ sweep (Fig 3c). While the paper states step budgets are matched (Section 4.1), the optimal ratio (1.5:1) is derived from a single curve without error bars. Additionally, the merging strategy (Algorithm 1) is claimed to consolidate strengths, but the ablation shows individual branches already outperform static baselines (Table 3). Evidence distinguishing the contribution of merging versus parallel training is weak.

To strengthen the evidence, report results over at least 3 seeds with error bars on all tables. Validate the behavioral overlap hypothesis (Eq. 5) directly during CoPD training with multiple seeds. Provide statistical tests for the benchmark improvements. Finally, include an ablation isolating the merging operation to prove its necessity beyond the co-evolution process.
