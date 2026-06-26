---
action_items:
- id: eecdd483931e
  severity: science
  text: Report 95% confidence intervals (e.g., via bootstrapping) for all primary
    metrics (T1 Acc, T3 Acc, HR) in Table 1 to quantify estimation uncertainty.
- id: dc39e97bf514
  severity: science
  text: Perform statistical significance testing (e.g., paired t-test or McNemar's)
    for top-model comparisons rather than relying solely on point-estimate rankings.
- id: 549731ad4227
  severity: science
  text: Address multiple-comparisons correction when claiming specific performance
    gaps (e.g., the -26.6% open-vs-closed T3 gap) are statistically significant.
artifact_hash: 37d4da743146174451c6b81c250d33af63eaf988a8502062dfca5a6325ae068a
artifact_path: projects/PROJ-620-perception-or-prejudice-can-mllms-go-bey/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-26T01:04:29.896474Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_statistical_analysis
score: 0.0
verdict: minor_revision
---

The statistical framework for the MM-OCEAN benchmark is largely well-structured, particularly in the definition of failure-mode metrics (PR, CR, IR, HR) and the robustness checks performed. The threshold sensitivity analysis in Appendix A.9 (lines 1050-1080) is a strong point, demonstrating that the Holistic-Grounding Rate (HR) ranking is stable ($\rho \geq 0.92$) across threshold variations. Similarly, the cross-judge robustness for Task 2 (Appendix A.10) provides necessary validation for the AI-as-Judge protocol.

However, the statistical reporting of model performance lacks necessary rigor for a benchmark paper. Table 1 (lines 330-360) presents point estimates for accuracy and error rates without confidence intervals (CIs). Given the sample size (1,104 videos), differences between models (e.g., Gemini 3 Flash at 64.1% vs. GPT-5.5 at 56.0% on T1) should be accompanied by 95% CIs to determine if these gaps are statistically significant or within sampling noise. Currently, the leaderboard implies precision that is not statistically quantified.

Furthermore, the paper makes strong claims about ecosystem-level gaps (e.g., $\Delta_{T3} = -26.6\%$ in Section 5.2, line 380) without reporting p-values or correcting for multiple comparisons. With 27 models evaluated across three tasks and four failure modes, the risk of Type I errors is non-negligible. The authors should apply corrections (e.g., Bonferroni or FDR) when asserting the significance of these gaps.

Finally, the thresholds for binarizing continuous scores into failure modes (Eq. 4, line 240) are heuristic ($\theta_1=\theta_3=0.5, \theta_2=0.7$). While sensitivity is tested, a statistical justification (e.g., maximizing F1 against a gold standard or optimizing for stability) would strengthen the validity of the PR/CR/IR/HR definitions. The variance of the AI-as-Judge scores (Task 2) is also not reported; only means are shown, obscuring the reliability of the T2 metric. Addressing these statistical gaps is essential for the benchmark's credibility.
