# Revision Specification: Paper Science Revision — PROJ-618-bench-evaluating-proactive-personal-assi round 2

**Generated**: 2026-06-26T22:59:33.812446+00:00
**Kind**: paper_science
**Project**: PROJ-618-bench-evaluating-proactive-personal-assi
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[d16b7ad65b07] (severity: science)** Section 4.3 claims Task Type H has the largest gap (84.1% Comp vs 38.1% Proc). Calculations from Table task_type_scores show Task Type C has a larger gap (82.2% vs 35.0%). Correct the claim or verify calculation.
- **[11631378eb4f] (severity: writing)** Section 4.3 references Fig. 4.3 subfigure (d), but the caption only lists (a, b, c). Align text reference with figure labels.
- **[0479cc0290ba] (severity: science)** Provide full project repository including src/, tests/, and dependency files (requirements.txt/pyproject.toml).
- **[d5c76019467a] (severity: science)** Include Dockerfile and environment setup scripts to enable reproducibility from scratch.
- **[5ea8c304477c] (severity: science)** Add unit/integration tests for the user agent and grader logic described in Section 3.
- **[1883eacb8f39] (severity: writing)** Specify the open-source license for the pi-Bench dataset and task definitions. Currently, only dependency licenses (Nanobot: MIT, AppWorld: Apache-2.0) are mentioned in 2-appendix/experiments.tex.
- **[12195384b0a8] (severity: writing)** Add a specific commit hash or release tag to the GitHub repository link in the Abstract to ensure reproducibility and prevent link rot over time.
- **[42a933b85e8a] (severity: science)** Clarify the provenance of the realistic workflows in 2-appendix/benchmark-construction.tex. State whether tasks were synthesized, crowdsourced, or derived from public logs to support data quality claims.
- **[7613abae3f93] (severity: science)** Specify the version of AppWorld used for tool simulation in 2-appendix/experiments.tex. The URL alone does not guarantee environment stability for future replication.
- **[9ff751537a50] (severity: writing)** Figure 3 caption is truncated with placeholder text '{a, b, c}' instead of describing actual axes and data. Update caption to specify x-axis (task type), y-axis (Proc/Comp scores), and color coding scheme."
- **[6864290629e3] (severity: writing)** Main figures (overview.pdf, interaction.pdf, task_type.pdf, turn_proactivity.pdf, ablation_study.pdf) lack alt text. Add \includegraphics[alt=...] or corresponding \caption with descriptive text for accessibility compliance."
- **[9a33cb0ef444] (severity: writing)** Figure 4 (turn_proactivity.pdf) and Figure 5 (ablation_study.pdf) do not specify axis labels or units in their LaTeX code. Ensure x/y axes are labeled with variable names and measurement units before submission."
- **[e3c2ff5d8499] (severity: writing)** tcolorbox case study figures (e.g., Fig. case_zhangshunkai_1_deepseek_trajectory) use small font size without clear visual hierarchy. Consider increasing font or adding section dividers for better print legibility."
- **[32df4cdbaede] (severity: writing)** Define 'ReAct' as Reason-Act on first use in Introduction; expand 'GUI' to graphical user interface in Related Work.
- **[f4d41332991e] (severity: writing)** Replace 'long-horizon trajectories' with 'extended interaction sequences' in Abstract and Section 1.
- **[43620608b04f] (severity: writing)** Define 'SOPs' in Table 1 and 'LC-MS'/'RMB' in Case Studies for international accessibility.
- **[b5a1ddf91a19] (severity: writing)** Change 'terminal status' to 'final state' in Section 3 and 'agentic scaffold' to 'agent framework' in Section 4.
- **[2344fb50d995] (severity: science)** Table 1 intent status percentages do not mathematically align with Table 2 Proc scores. For Qwen3.6 Plus, Table 1 shows Completed=63.18%, Inferred=10.45%, which should give Proc=73.63%, but Table 2 reports Proc=64.0%. Explain this discrepancy or correct the numbers.
- **[d049be04717a] (severity: science)** The user agent uses GPT-5.4 as base model (Sec. 4.1), and GPT-5.4 is also an evaluated model. This creates potential circularity in intent status assignment. Justify this design or use a different model for the user agent.
- **[4fa46fb36e8c] (severity: writing)** Claims of "clear distinction" between Proactivity and Completeness (Sec. 4.2) lack statistical significance testing. Report p-values or confidence intervals for the observed gaps (e.g., Kimi K2.5 Comp=61.6 vs Proc=43.1).
- **[292e968891c1] (severity: writing)** The negative correlation between turn count and Proc (Fig. 3) lacks mechanistic explanation. Why should fewer turns imply higher proactivity? Clarify the causal reasoning.
- **[aff12b650550] (severity: writing)** Abstract claims benchmark better reflects real-world use (line 30) despite simulated users. Soften to approximate or add simulated qualifier.
- **[1ff576b5c9c3] (severity: writing)** Section 4.2 claims practical decoupling between proactivity and completeness (line 352) based on 9 models. Add in our evaluation qualifier.
- **[1ea27a1ce179] (severity: writing)** Cross-session continuity claims (line 168) suggest continuity evaluation but ablation only tests final task. Clarify scope to final-task dependency.
- **[f6851103bbe7] (severity: science)** Evaluation reliability claim strong agreement (line 408) for 2.66% human disagreement lacks statistical rigor. Add confidence intervals or kappa.
- **[8e7e72cadf62] (severity: writing)** Limitations section (line 425) admits simulated users but abstract/conclusion do not reflect this constraint. Ensure claims consistently qualified.
- **[2fc5876de22c] (severity: writing)** Explicitly state IRB approval or ethics exemption for the three human expert annotators used in the reliability audit (Appendix Experiments).
- **[6dfbd6a70de7] (severity: science)** Detail data sanitization procedures for the released benchmark to ensure synthetic PII in sensitive domains (legal, medical) cannot be reverse-engineered.
- **[bb17fe1a1479] (severity: science)** Address potential bias from using GPT-5.4 as both user agent and grader, especially since it is also the top-performing evaluated model.
- **[e2a2d3f37450] (severity: science)** Include statistical significance testing (e.g., t-tests) for model comparisons in Table 2 to validate claims of superiority.
- **[b17902e401eb] (severity: science)** Provide error bars or significance markers on the ablation study results (Fig. 6) to confirm robustness of the 9.5 point drop.
- **[3b4ebab61696] (severity: science)** Add statistical significance tests (e.g., paired t-tests) for model comparisons in Table 1 to validate bolded scores.
- **[55322ded1953] (severity: science)** Report 95% confidence intervals instead of standard deviations of the mean, given only 3 runs per task.
- **[e7d8a496f229] (severity: science)** Apply multiple comparisons correction (e.g., Bonferroni) for the 9 models x 18 task types analysis.
- **[589b3ef177bd] (severity: writing)** Inconsistent vertical spacing around figures: use -13 pt (e000, fig:process), -15 pt (e000, fig:process), -12 pt (e000, fig:interaction), -16 pt (e000, fig:ablation_study), -8 pt (e000, fig:turn_count). Standardize to a single value or remove manual spacing.
- **[9cf922b8b741] (severity: writing)** Table column spacing inconsistent: setlength{tabcolsep} 8pt (e000, tab:hidden_intent_status), 5.5 pt (e000, tab:task_type_scores), default elsewhere. Use consistent spacing across all tables.
- **[cd351efc36a8] (severity: writing)** hyperref package loaded early (line 6 in e000) but should typically be loaded last in LaTeX documents for best compatibility with other packages and link styling.
- **[eadc77d9f2b7] (severity: writing)** Custom tcolorbox commands (tcolorboxCase, tcolorboxPrompt) defined at end of document (e002) but used earlier in case studies (e000). Move definitions before first usage.
- **[def3071aa816] (severity: writing)** Unify model naming conventions across text and tables to ensure consistency
- **[0739932e1c58] (severity: writing)** Resolve duplicate Experiments section in main and appendix to prevent numbering conflicts
- **[f8aec1dbf913] (severity: writing)** Correct subject-verb agreement in Failure Analysis section for grammatical accuracy


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 41 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
