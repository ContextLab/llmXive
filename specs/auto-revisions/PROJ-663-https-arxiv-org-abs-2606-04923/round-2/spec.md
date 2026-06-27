# Revision Specification: Paper Science Revision — PROJ-663-https-arxiv-org-abs-2606-04923 round 2

**Generated**: 2026-06-27T04:54:31.220871+00:00
**Kind**: paper_science
**Project**: PROJ-663-https-arxiv-org-abs-2606-04923
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[36b879c4f31b] (severity: writing)** Add missing bibliography entries for citations 'panicksseryLLMEvaluatorsRecognize2024' (Intro), 'ifbench2025' (Table 1), and 'writingbench2025'/'arena_hard_2024' (Sec 3.2) to support factual claims about prior work and benchmarks.
- **[b17497cba78d] (severity: writing)** Ensure all citation keys in the LaTeX text match the keys defined in custom.bib to prevent compilation errors and verify source attribution.
- **[7339985b81f8] (severity: writing)** Appendix F (Reproducibility) lacks specific GRPO hyperparameters (learning rate, KL penalty, batch size) required for independent reproduction of training dynamics.
- **[50fdc0e0898c] (severity: writing)** The Artifacts section should explicitly mention dependency management (e.g., requirements.txt, Python version) and testing infrastructure (e.g., unit tests) included in the code release.
- **[830730185d0f] (severity: writing)** Clarify the validation process for the 'sanitized rollout mirror' (Appendix D) to ensure no bias leakage occurs during the data sanitization pipeline.
- **[3f93603afeb9] (severity: writing)** Explicitly state the software licenses for HealthBench and VerInstruct datasets in the Artifacts section (Appendix F) to ensure legal compliance and reproducibility.
- **[9ab3b616a697] (severity: writing)** Provide a persistent archival link (e.g., Zenodo DOI) for the CHERRL code repository in the Abstract to mitigate link rot risks beyond GitHub.
- **[cbbcb5438c15] (severity: science)** Specify exact commit hashes or version tags for the open-source Qwen models (Qwen3-4B, Qwen3.5-27B) used in training to enable precise reproduction.
- **[b87ea0b996f1] (severity: writing)** Figure 1 (fig:figure1) is placed in the Introduction but is never referenced in the text. Either add a citation (e.g., \cref{fig:figure1}) or remove the figure to avoid orphaned content.
- **[415059464679] (severity: writing)** Appendix figures (budget_run_*.png, case_tool_timeline.png) are in raster PNG format. Convert these to vector PDF/EPS to ensure legibility at print scale and consistent quality with main text figures.
- **[2fb35a0eb470] (severity: writing)** No alt text or accessibility metadata is provided for any figure. Add \alttext or equivalent accessibility tags to comply with publication standards for visually impaired readers.
- **[35f288e39fae] (severity: writing)** Define every acronym on first use (e.g., LaaJ, RLVR, GRPO, OR, RHDA, CC‑Qwen).
- **[0dcc9d1845b1] (severity: writing)** Replace or explain high‑frequency jargon such as “latent biases”, “proxy reward”, “dual‑judge architecture”, “operational reference onset”, and “bracket‑and‑shrink strategy” with plain‑language alternatives.
- **[1de2ba49e65d] (severity: writing)** Break up overly long sentences (e.g., the abstract and Section 1 paragraphs) to improve readability for non‑specialist audiences.
- **[2e70dedd36fe] (severity: writing)** Add brief, lay‑person‑friendly explanations when introducing core concepts (e.g., what a “rubric‑based RL” system does, why “reward hacking” matters) to avoid assuming prior knowledge.
- **[e01eaf1d667e] (severity: science)** Clarify the assumption of additive decomposition of judge scores (Eq. 1) and discuss how non‑linear interactions between true quality and bias could affect the validity of the dual‑judge formulation.
- **[cb1014edd530] (severity: science)** Provide a more rigorous justification that the operational reference onset (Section 3.3) approximates a true ground‑truth onset, and acknowledge potential bias introduced by the threshold sweep and manual audit.
- **[764f7cbbcc69] (severity: writing)** Temper the claim of “precise identification of reward‑hacking onset” to reflect the uncertainty inherent in the reference construction and limited evaluation scope.
- **[502862a565e4] (severity: science)** Strengthen the causal argument linking bias‑task entanglement to discoverability (Section 5.1) by adding controlled ablations or statistical tests beyond the reported correlation with odds ratios.
- **[b2fb48923c24] (severity: science)** Section 4 claims general mechanisms ('discoverability is driven by...', 'exploitability hinges on...') based on only 4 bias types across 2 datasets. Soften these causal claims to reflect the limited sample size (e.g., 'preliminary evidence suggests').
- **[c871d2dd9128] (severity: writing)** Abstract claims 'precise identification of hacking onset'. Section 3.3 defines this as an 'operational reference' based on threshold sweeps. Align the abstract claim with the operational nature of the ground truth.
- **[8a5ca34440ac] (severity: writing)** While Section 5 notes 'composite real-world biases are left for future work', the Abstract and Introduction frame RHDA as a general detection system. Clarify that RHDA's evaluation is strictly on synthetic injected biases to avoid overclaiming real-world applicability.
- **[5522b0c48ee6] (severity: writing)** Add a dedicated paragraph in the Limitations or Ethics section discussing the dual-use risks of releasing CHERRL, acknowledging that the hacking environment could theoretically be used to learn exploitation techniques, and framing the release as defensive research.
- **[beae0a416783] (severity: writing)** Clarify the ethical compliance of the 'Manual Expert Audit' in Appendix (Section app:manual_audit). Explicitly state whether IRB approval or exemption was obtained for the author annotators, as this involves human judgment on model outputs.
- **[aeff9c2b909e] (severity: science)** Clarify RL training replication: Section 3.5 and Fig 2 do not specify the number of random seeds. RL dynamics are stochastic; single-run curves may not be representative. Report mean/std over seeds or justify single-run.
- **[8179ff866dc6] (severity: science)** Strengthen detection evaluation statistics: Table 3 evaluates RHDA on only 6 controlled runs. This small sample size limits statistical power. Discuss confidence intervals or increase run count.
- **[480109729815] (severity: science)** Report significance for capability degradation: Tables 1 & 2 show point estimates for downstream performance drops. Add error bars or statistical tests to confirm degradation is significant.
- **[43a28882ea8c] (severity: science)** Address audit bias: Appendix manual audit for onset validation is performed by authors. This risks confirmation bias. Acknowledge this limitation or suggest external validation.
- **[1ffd974d2dd9] (severity: science)** Report standard deviations or confidence intervals for benchmark scores in Tables 2 and 3 to account for RL training stochasticity.
- **[bf4534269e41] (severity: science)** Conduct statistical significance testing (e.g., paired t-test or Wilcoxon) for the detection agent comparison in Table 3 rather than reporting summed errors.
- **[5ee0e9f1d2da] (severity: science)** Clarify the sample size used for the Odds Ratio calculation in Section 4.1 and avoid claiming 'correlation' with only 6 data points without a test statistic.
- **[31c7af4c4731] (severity: science)** Provide a sensitivity analysis for the reference onset threshold sweep (Appendix A.1) to justify the chosen threshold values.
- **[8dbabc8d1105] (severity: writing)** The paper demonstrates strong overall text formatting with consistent heading hierarchy and figure-caption placement. However, several LaTeX hygiene and structural issues require attention before final submission. First, there are redundant package imports that should be cleaned up to avoid compiler warnings. Specifically, \usepackage{graphicx} is declared three times (lines 31, 55, 57), \usepackage{booktabs} twice (lines 38, 60), and \usepackage{xcolor} twice (lines 7, 41). Consolidating these
- **[4ec796956b08] (severity: writing)** Section 5.2 repeats 'rubric-based RL' and 'reward hacking' in the final sentence. Consider rephrasing for conciseness (e.g., '...in this paradigm').
- **[260196dd1a82] (severity: writing)** Section 2.5 repeats 'in these two settings' twice in one sentence. Streamline to improve flow.
- **[67a0b23f750e] (severity: writing)** Related Work (Section 5) contains several long, dense sentences. Consider breaking them down for better readability.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 36 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
