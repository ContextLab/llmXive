---
action_items:
- id: aeff9c2b909e
  severity: science
  text: 'Clarify RL training replication: Section 3.5 and Fig 2 do not specify the
    number of random seeds. RL dynamics are stochastic; single-run curves may not
    be representative. Report mean/std over seeds or justify single-run.'
- id: 8179ff866dc6
  severity: science
  text: 'Strengthen detection evaluation statistics: Table 3 evaluates RHDA on only
    6 controlled runs. This small sample size limits statistical power. Discuss confidence
    intervals or increase run count.'
- id: '480109729815'
  severity: science
  text: 'Report significance for capability degradation: Tables 1 & 2 show point estimates
    for downstream performance drops. Add error bars or statistical tests to confirm
    degradation is significant.'
- id: 43a28882ea8c
  severity: science
  text: 'Address audit bias: Appendix manual audit for onset validation is performed
    by authors. This risks confirmation bias. Acknowledge this limitation or suggest
    external validation.'
artifact_hash: eca43eb888bbc8155fd1bf21a6b137ce6bb47419fcb91606da445eda44a63a5a
artifact_path: projects/PROJ-663-https-arxiv-org-abs-2606-04923/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-27T04:38:53.973250Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: minor_revision
---

The paper presents a strong methodological contribution with CHERRL, a controllable environment for studying reward hacking. The dual-judge design effectively isolates bias, providing a clear ground truth for hacking onset that is typically unavailable in real-world settings. The evidence for the environment's utility is generally sound, particularly the clear reward divergence shown in Figure 2 and the systematic analysis of bias types.

However, the scientific evidence supporting the empirical claims requires strengthening in three areas. First, the RL training dynamics (Section 3.5, Figure 2) do not specify the number of random seeds used. Reinforcement learning is inherently stochastic; presenting single-run curves without error bars or replication makes it difficult to assess the robustness of the reported hacking onsets and training trajectories. Second, the detection system evaluation (Section 4.2, Table 3) relies on only six controlled runs. This small sample size limits the statistical power of the comparison between RHDA and baselines. Third, the capability degradation results (Tables 1 & 2) report point estimates without measures of variance or statistical significance. It is unclear if the observed drops (e.g., IFB Strict 31.7 vs 23.7) are statistically significant or within the noise of evaluation.

Finally, the manual audit used to validate the operational reference onsets (Appendix) is conducted by the paper's authors. While the protocol is detailed, author-only annotation introduces potential confirmation bias. Acknowledging this limitation more prominently or providing external validation would strengthen the evidence for the onset definitions. Addressing these statistical rigor issues will solidify the paper's empirical claims.
