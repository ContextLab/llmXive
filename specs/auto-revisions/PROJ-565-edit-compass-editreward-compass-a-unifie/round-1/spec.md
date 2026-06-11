# Revision Specification: Paper Science Revision — PROJ-565-edit-compass-editreward-compass-a-unifie round 1

**Generated**: 2026-06-11T02:09:46.512360+00:00
**Kind**: paper_science
**Project**: PROJ-565-edit-compass-editreward-compass-a-unifie
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[1bea5219d71b] (severity: science)** Resolve discrepancy between Introduction table (Qwen3.5-27B, 0.6998) and Experiments table (Qwen3.6-27B, 0.7183) for \rmbench results. Ensure consistent model reporting.
- **[77be4dbe5505] (severity: writing)** Correct arithmetic in Table \ref{tab:combined_results}: AVG gain shown as 0.1293, but values (0.4684 - 0.3415) yield 0.1269.
- **[95056158c17a] (severity: science)** Clarify model version confusion (Qwen3.5 vs Qwen3.6) in Experiments text vs tables. Citations must match the specific model evaluated.
- **[fa5d0d98ffbe] (severity: writing)** Code artifacts (repository, scripts, tests) are not included in the submission. Please provide a complete code package (requirements, tests, reproduction scripts) alongside the paper to enable reproducibility and code quality evaluation.
- **[3cf7c2e7c5ac] (severity: writing)** Specify the dataset license (e.g., CC-BY 4.0) for Edit-Compass and EditReward-Compass in the main text or appendix.
- **[f81eaf3c0697] (severity: writing)** Explicitly state compliance with source image licenses (Unsplash, Pexels, etc.) regarding redistribution.
- **[b5d3bbee9931] (severity: writing)** Include a dataset version number (e.g., v1.0) and release date in the repository and paper.
- **[9497d8b83225] (severity: writing)** Report data filtering statistics (e.g., number of generated vs. retained samples) to quantify selection bias.
- **[7b6abb4a6171] (severity: writing)** Standardize figure label naming conventions. The manuscript mixes prefixes ('fig:gallery', 'User_Study', 'Fig:ADD'). Adopt a consistent 'fig:' prefix for all figures to prevent referencing errors.
- **[2d99212d5f5e] (severity: writing)** Enhance qualitative figure captions. Current captions (e.g., Fig:ADD, Fig:Virtual Try-On) are generic ('Qualitative comparisons on...'). They should describe the specific visual evidence or finding (e.g., 'Model X preserves identity while Model Y fails...').
- **[5c3c119b3de8] (severity: writing)** Resolve duplicate figure label definitions. Labels like 'User_Study' and 'Fig:ADD' are defined in both chunk e001 and chunk e003, which will cause LaTeX compilation warnings and broken references.
- **[9949c9826aa5] (severity: writing)** Define acronyms RL (Reinforcement Learning) and LLM (Large Language Model) at first use in Abstract and Introduction.
- **[a4352b1a2a99] (severity: writing)** Define MLLM (Multimodal Large Language Model) before Section 3.1 Evaluation Pipeline; currently appears as 'MLLM-as-judge' without prior definition.
- **[5043f6a12c26] (severity: writing)** Spell out algorithmic terms DP (Dynamic Programming) and DFS (Depth-First Search) in Appendix Section 'Algorithmic Visual Reasoning tasks' for non-specialist clarity.
- **[36bffd03f09d] (severity: writing)** Define ROI (Region of Interest) in Appendix prompt boxes (e.g., URC_Complex_paint) where it appears without context.
- **[23d882333a86] (severity: writing)** Replace architecture-specific jargon 'DiT' (Diffusion Transformer) and 'UNet' with plain descriptions or ensure definitions exist in Appendix Section 'Image Editing Model Evaluation'.
- **[f1e2d3c4b5a6] (severity: writing)** Define FlowGRPO at first use in Section 3.1 Sampling Stage; currently appears without expansion.
- **[7b548a22ae8b] (severity: writing)** Weight rationale missing: Section supp:Evaluation Details defines task-type-specific weights (e.g., 0.6 IA for AVR tasks) without justification. Why should World Knowledge tasks weight IA higher?
- **[ffbaa7a0e2cb] (severity: writing)** System prompt gain ambiguity: Analysis section states '12.93%' gain but Table tab:combined_results(b) shows 0.1293 absolute improvement. Clarify whether this is percentage or absolute gain.
- **[51bd755094e0] (severity: writing)** Human correlation claim unsupported: Section 4.1 claims 'higher correlation with human preferences' but cites Fig. User_Study without providing actual correlation values in text.
- **[87bd87c6db5a] (severity: writing)** Score scale inconsistency: \bench reports 1-5 scores (e.g., Table 5), while \rmbench reports 0-1 scores (e.g., Table 3) despite claiming the same rubric framework. Explain normalization.
- **[0a148d84d9e4] (severity: writing)** Add explicit IRB approval statement for human annotators involved in benchmark construction and evaluation.
- **[9e74ad928364] (severity: writing)** Revise the Impact Statement to address dual-use risks of image editing (e.g., deepfakes, misinformation) rather than dismissing them.
- **[8d92fd7d988e] (severity: writing)** Clarify privacy consent for human subjects in 'Virtual Try-On' and stock photo datasets used in the benchmark.
- **[ba17f205f6f7] (severity: science)** Report standard deviation or confidence intervals for model scores across multiple seeds to establish statistical robustness.
- **[67288cad6289] (severity: science)** Specify the sample size (number of human ratings) for the User Study (Fig. User_Study) to validate the claimed human alignment.
- **[e0bc802a3eb4] (severity: science)** Report confidence intervals or standard errors for all model performance scores (e.g., Table tab:Image Editing Bench Main Results_EN). Point estimates alone cannot support claims of superiority between proprietary (3.99) and open-source (2.69) systems without uncertainty quantification.
- **[cd7b60c7136b] (severity: science)** Add statistical significance testing (e.g., paired t-tests, ANOVA with post-hoc corrections) for all model comparisons. With 29 models evaluated across 6 task categories, uncorrected comparisons inflate Type I error rates. Report p-values for key claims.
- **[616a059e9dee] (severity: science)** Report inter-rater reliability metrics (e.g., Cohen's kappa, ICC) for the MLLM-as-judge evaluation pipeline. The human study (Fig. User_Study) shows Pearson correlation but lacks correlation coefficients, p-values, and confidence intervals. Appendix should include these statistics.
- **[97d6bd978c78] (severity: writing)** Standardize table formatting: e005 uses vertical bars (|) in tabular definitions (e.g., \begin{tabular}{lc|ccc|...}), violating booktabs style used in e000. Ensure all tables use \toprule/\midrule/\bottomrule without vertical lines.
- **[dcbb3f68f396] (severity: writing)** Fix label hygiene: Multiple labels contain spaces (e.g., \label{supp: Evaluation Details} in e001, \label{tab:Image Editing Bench Main Results_EN} in e005). Replace spaces with underscores to prevent cross-reference errors.
- **[9e9b701daaba] (severity: writing)** Define missing environments: \begin{promptbox} and \begin{lstlisting} are used in e002/e003 but the preamble (e003) does not load 'listings' or define 'promptbox'. Add package declarations or remove unsupported environments.
- **[d135d246a5e2] (severity: writing)** Unify header punctuation: Section titles are inconsistent (e.g., \subsection{General and  Complex tasks.} in e003 ends with a period, while others do not). Remove trailing periods from section headers.
- **[e8762be525a8] (severity: writing)** Fix inconsistent figure label spacing: Labels use mixed conventions (e.g., \label{Fig:ADD} vs \label{Fig: Remove} with space). Standardize to no spaces in all figure labels.
- **[f6a06ad74980] (severity: writing)** Resolve document class inconsistency: e000 uses \documentclass{llmxive} while e003 uses \documentclass{article} with \usepackage{neurips_2026}. Ensure unified document class across all chunks.
- **[71370fe3b74e] (severity: writing)** Table captions (e.g., e005) contain incomplete hyphenation: 'open-' and 'closed-' models. Correct to 'open-source' and 'closed-source' for clarity.
- **[7748e6327500] (severity: writing)** Terminology inconsistency: 'closed-source' is used in e001, but 'proprietary' is used in e003. Standardize throughout the manuscript.
- **[1dcf2029e756] (severity: writing)** Potential duplicate sections: 'Conclusion' and 'Impact Statement' appear in both e000 and e003 chunks. Ensure the final manuscript does not contain redundant sections.
- **[a7a2011cd18e] (severity: writing)** Hyphenation consistency: 'instruction following' should be hyphenated as 'instruction-following' when used as an adjective (e.g., e000 Introduction).


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 39 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
