---
action_items:
- id: 16c3d18ee5d9
  severity: science
  text: Report results over multiple random seeds with error bars for main performance
    claims (Fig. 5, Table 1) to establish statistical significance.
- id: 09c98bccd60a
  severity: science
  text: Justify the 50-sample validation set size for EffOPD selection; provide sensitivity
    analysis to ensure robustness against overfitting.
- id: 51318bbeb955
  severity: science
  text: Clarify causal vs. correlational nature of 'foresight' mechanism; consider
    ablation disrupting low-rank structure to test necessity.
artifact_hash: 86f3dbb1aa547b2619e2d0068122fd6e86cb21c5f6980bdd3810b1ffe64d94e9
artifact_path: projects/PROJ-597-https-arxiv-org-abs-2605-11739/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T03:31:22.479220Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents compelling empirical evidence that On-Policy Distillation (OPD) is more parameter-efficient than RL, supported by geometric analysis of weight updates (Table 1, Section 3). However, the scientific evidence lacks statistical rigor. The NeurIPS Checklist explicitly notes the absence of error bars or significance tests (Item 7). Main results in Figure 5 and Table 1 should be averaged over multiple seeds to rule out variance-driven effects. Given the high variance often seen in LLM training, single-run results are insufficient to support the claim of consistent 3x speedup.

The EffOPD method relies on a 50-sample validation set for extrapolation selection (Section 4, "Method"). This small sample size risks overfitting to the validation distribution, potentially inflating the reported speedup. The claim that "any lightweight set suffices" (Fig. 6b) needs stronger evidence, such as varying the validation set size (e.g., 10, 50, 100 samples) and showing performance stability. If the selection is sensitive to the specific 50 samples, the method's robustness is questionable.

Finally, the "foresight" mechanism (Functional Redundancy Avoidance, Early Low-Rank Lock-in) is presented as an explanation for efficiency. The evidence is largely correlational (Section 2 & 3). The paper observes that OPD updates are low-rank and efficient, but does not prove that low-rankness *causes* the efficiency. To strengthen the causal claim, the authors should perform ablation studies that explicitly disrupt the low-rank structure (e.g., via noise injection or rank constraints) and measure the impact on efficiency. Without this, the mechanism remains a hypothesis rather than a proven explanation. Additionally, the theoretical analysis in the Appendix is local (linearized); extending this to non-linear dynamics would strengthen the evidence for the "lock-in" phenomenon.
