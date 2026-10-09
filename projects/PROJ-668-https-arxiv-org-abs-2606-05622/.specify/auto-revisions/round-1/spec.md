# Revision Specification: Paper Science Revision — PROJ-668-https-arxiv-org-abs-2606-05622 round 1

**Generated**: 2026-06-29T08:45:17.654347+00:00
**Kind**: paper_science
**Project**: PROJ-668-https-arxiv-org-abs-2606-05622
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[9cc818aebad4] (severity: science)** Resolve GPT-5 vs GPT-5-Nano accuracy inconsistency: Abstract/text claim 67.75% for GPT-5, but Table 1 shows GPT-5-Nano at 42.35%. Table 2 shows GPT-5 at 67.75%. Clarify model naming and ensure consistency across tables.
- **[e09483b7907d] (severity: writing)** Verify citation completeness: Many cited works (e.g., PlanBench, PrefEval, costbench, ReflAct) are missing from the provided bibliography snippet. Ensure all in-text citations have corresponding bib entries.
- **[c22fbccc42b5] (severity: writing)** Clarify variation vs confidence interval: Text states 'variation ≤ 3%' but Table 2 shows 95% CI ±5.23% for GPT-5. Explain if these measure different quantities (run-to-run vs statistical CI).
- **[6460a32e66e0] (severity: science)** Provide correlation data: Claims of accuracy correlation with ATWC (0.898) and ATUC (0.919) are stated but not shown in tables. Include correlation coefficients in results table or appendix.
- **[15cd18142381] (severity: science)** Report early termination rate: Claim '17.91% of queries terminate early' is specific but not shown in tables. Include this metric in main results or appendix.
- **[a17efd5daddb] (severity: science)** Code repository (https://github.com/JiayuJeff/AdaPlanBench) not accessible for review. Cannot verify modularity, test coverage, dependency management, or reproducibility scripts. Authors should provide direct repository access or include code quality documentation in submission.
- **[6858b08d6d48] (severity: science)** Paper mentions vLLM dependency (Section 2, Ethics) but no requirements.txt or environment specification visible in provided materials. Reproducibility from scratch cannot be verified.
- **[3159f0f79d4d] (severity: writing)** Specify the exact Creative Commons license identifier (e.g., CC-BY-4.0) in the Ethics statement instead of the generic 'CC'.
- **[58fa2c32c009] (severity: science)** Include a specific commit hash or version tag for the dataset release to ensure reproducibility of the 307-task benchmark.
- **[1c5bf7bc1b63] (severity: writing)** Clarify IRB approval or informed consent procedures for the 8 PhD-level human annotators mentioned in Section 'Human Annotation Details'.
- **[4ee9d690ee7e] (severity: writing)** Remove unused figure files (pipeline_1.pdf, github-logo.png, hf-logo.png) not referenced in the LaTeX source to reduce clutter.
- **[c5cb47bf3772] (severity: writing)** Add alt text descriptions to all figure environments for accessibility compliance.
- **[0a966556c62f] (severity: writing)** Ensure tcolorbox prompt figures (e.g., fig:user-llm-prompt) are legible at print scale; consider reducing font size or splitting content.
- **[cead5b2849d5] (severity: writing)** Consolidate the four human-vs-LLM alignment histogram figures into a single multi-panel figure to save space and improve comparison.
- **[2535dcc654ed] (severity: writing)** Define 'PDDL' at first use in Related Works (Section 3) for non-specialist readers.
- **[a49a7e28a62e] (severity: writing)** Replace 'canonicalized' with 'standardized' in Formalization (Section 4.1) to reduce technical density.
- **[25d9d88845a7] (severity: writing)** Define 'CI' (Confidence Interval) in Table 3 caption or Metric Definitions section.
- **[313019442346] (severity: writing)** Replace 'a priori' with 'in advance' in Related Works (Section 3) for clarity.
- **[aa82b2528772] (severity: writing)** Replace 'serializes' with 'records sequentially' in Constraint-Tracking Analysis (Section 4.1).
- **[7b917613be94] (severity: writing)** Ensure \BENCH{} macro expands to 'AdaPlanBench' in Abstract text for immediate clarity.
- **[bfcc57fa1737] (severity: science)** Temperature settings are inconsistent across models in main results (GPT-5 at T=1.0, others at T=0.0). This confounds model comparison. Clarify or control for temperature in Section 3.1.
- **[4febad715de5] (severity: science)** Correlation claims (ATWC/ATUC vs accuracy, r=0.898/0.919) are based on n=10 models. Provide p-values or confidence intervals to support statistical significance.
- **[833ddb10df6b] (severity: writing)** Main accuracy (67.75%) corresponds to rubric threshold γ=4.00 (Table 5), but this is not explicitly stated in the main text. Add this specification to Section 3.1.
- **[e6961cf50a00] (severity: science)** Temper the claim 'Scaling insufficient for adaptiveness' (Section 2, Results) to reflect the specific model range tested (8B-32B) rather than general scaling laws.
- **[8e0c801b6ba7] (severity: writing)** Clarify in the main text that primary metrics (Accuracy, VPR) are LLM-judged estimates validated on a subset (240 trajectories), avoiding overclaiming precision on the full benchmark results.
- **[d00efd00b402] (severity: science)** Discuss potential bias in LLM-generated constraints in the main analysis (Section 2/3) rather than solely in the Limitations section, as this affects the validity of the 'dual-constraint' claim.
- **[35a748981683] (severity: writing)** The 'Human Annotation Details' section (e001) describes recruiting 8 PhD-level annotators but does not mention IRB approval or ethics committee oversight. Explicitly state whether IRB approval was obtained or if the study was deemed exempt, and confirm informed consent procedures were followed.
- **[24e7c9fb735c] (severity: writing)** The 'Ethics statement' section mentions data annotations were performed by researchers but omits details on compensation and data privacy protections for the annotators. Add a sentence confirming fair compensation and that no personally identifiable information (PII) was collected from annotators.
- **[0702a42271e9] (severity: writing)** Clarify the origin of 'User Constraints' in the benchmark. While the 'User Simulator prompt' suggests synthetic generation, ensure there is no risk of inadvertently encoding real user preferences or PII into the dataset that could compromise privacy.
- **[a4827bcc37cd] (severity: writing)** Scientific Evidence Review Sample Size & Power: The benchmark uses 307 household tasks, which is reasonable for a planning benchmark. However, human annotation validation covers only 240 trajectories (3 queries × 10 models), representing ~8% of total evaluations (3070). This limited human validation may not adequately capture judge reliability across the full task distribution. Controls & Ablations: The paper includes multiple ablation studies (temperature, constraint type, rubric threshold, mem
- **[f91ed4ab6d08] (severity: science)** Report p-values and confidence intervals for all correlation coefficients (e.g., accuracy vs ATWC/ATUC correlations of 0.898/0.919). Current presentation lacks statistical significance testing.
- **[b8366e74971c] (severity: science)** Apply multiple-comparison correction (e.g., Bonferroni, Holm, or FDR) when comparing 10 models across 7 metrics. Current bold/underline highlighting of best performers ignores family-wise error rate.
- **[de246b8a22ac] (severity: science)** Replace Wald confidence intervals with Wilson or Agresti-Coull intervals for proportion metrics, especially for models with accuracy near boundaries (e.g., Qwen3-8B at 14.38%).
- **[e233cb140e3b] (severity: science)** Report inter-rater reliability using Cohen's/Fleiss' Kappa for human annotation study (8 annotators, 240 trajectories) instead of only agreement percentages.
- **[28f362d58432] (severity: writing)** Define the variation metric (≤3% across 3 runs) precisely—specify whether this is standard deviation, range, or coefficient of variation.
- **[d38056294797] (severity: writing)** Fix section hierarchy: 'Human Annotation Details' (e001) should be a subsection of 'Human Annotation' (e000), not a top-level section.
- **[d1594c96aa15] (severity: writing)** Reorder sections: Move 'Limitations' and 'Ethics statement' from the beginning (e000) to the end of the paper, following standard academic structure.
- **[5a72a9d6f215] (severity: writing)** Correct cross-reference typo: 'app:model_choise' in e002 should likely be 'app:model-setup' or 'app:model-choice' to match defined labels.
- **[c2ca0e5f9a45] (severity: writing)** Review table formatting: Avoid 'esizebox' in table* (e002) to prevent font size inconsistencies; use explicit font sizing instead.
- **[495f4a6acc19] (severity: writing)** Clarify figure semantics: Several 'figure*' environments contain text boxes (tcolorbox) rather than images; ensure captions and labels reflect content type.
- **[bb6c69c47523] (severity: writing)** Fix sentence fragments in Limitations and Ethics sections (e.g., 'Uses multiple LLM judges' lacks a subject).
- **[95aaacc6de35] (severity: writing)** Correct the typo in the appendix reference label 'app:model_choise' to 'app:model_choice'.
- **[8cccc692d0ff] (severity: writing)** Complete the section heading 'Intuition Behind' to specify the subject (e.g., 'Intuition Behind the Construction').
- **[93884661e7c7] (severity: writing)** Ensure consistent tense in Human Annotation Details (e.g., change 'recruit' to 'recruited').


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 44 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
