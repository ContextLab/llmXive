---
action_items:
- id: f789aa6438c7
  severity: science
  text: Report standard deviations or 95% confidence intervals for all success rate
    metrics in Tables 1, 2, and 3. Single-point estimates without variance prevent
    statistical significance assessment.
- id: f9b3763d0ab4
  severity: science
  text: Specify the number of random seeds used for model training and report mean/std
    performance across seeds. Single-seed results are insufficient to rule out initialization
    variance.
- id: 1d1a6b09bd1e
  severity: science
  text: Clarify the total episode count discrepancy in Section 4.1 (500x15x4) versus
    Appendix A.1 (14 angles). Inconsistent sample size reporting undermines reproducibility.
artifact_hash: 1607b7a56c94fa04d6447f07acdf09cff37e83d8d846355c78db174b7f1d3ac9
artifact_path: projects/PROJ-796-in-context-world-modeling-for-robotic-co/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-28T05:47:28.573809Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_scientific_evidence
score: 0.0
verdict: full_revision
---

The scientific evidence supporting the central claims of In-Context World Modeling (ICWM) is currently insufficient due to a lack of statistical rigor and reproducibility details. While the experimental design includes appropriate baselines (Multi-View BC, Explicit Configuration) and ablation studies (Section 5.1), the reporting of results lacks the necessary statistical depth to validate the claimed improvements.

First, all success rate metrics in Tables 1 and 2 (Appendix) and Table 3 (Main) are reported as single point estimates (e.g., "25.0%"). Without standard deviations, confidence intervals, or p-values, it is impossible to determine if the observed gains (e.g., 5.2% over MV in OOD simulation) are statistically significant or due to random variance. Given the binary nature of success/failure, binomial confidence intervals should be calculated and reported.

Second, the training protocol does not specify the number of random seeds used. Deep learning models, particularly those with 3B parameters (Qwen2.5-VL-3B), exhibit significant performance variance across different initializations. Reporting results from a single seed (implied by the lack of variance reporting) is a critical weakness in scientific evidence. The authors must re-run experiments across multiple seeds (e.g., 3-5) and report mean ± std.

Third, there is an inconsistency in sample size reporting. Section 4.1 states "500 x 15 x 4 total episodes," but Appendix A.1 specifies 14 angles (8 ID + 6 OOD). This discrepancy (15 vs 14) casts doubt on the exact experimental setup and total data volume.

Finally, while the "False Context" ablation (Table 3) provides strong evidence that the model utilizes context content, the lack of variance on this metric also limits the strength of this conclusion. The real-robot experiments (600 trials) are well-powered, but the simulation results require the statistical corrections noted above to support the claim of "significant improvements." Addressing these issues is essential to establish the robustness of the evidence.
