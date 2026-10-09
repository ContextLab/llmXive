# Revision Specification: Paper Science Revision — PROJ-626-skillopt-executive-strategy-for-self-evo round 1

**Generated**: 2026-06-13T12:37:38.973417+00:00
**Kind**: paper_science
**Project**: PROJ-626-skillopt-executive-strategy-for-self-evo
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[256d18bda9a4] (severity: writing)** Clarify the distinction between 'Executive Strategy' and 'Skill Optimization' in the introduction to address prior reviewer concerns on terminology consistency.
- **[c31e454de098] (severity: writing)** Confirm that all 2026-dated references in references.bib have verification_status: verified in the project citation state to meet acceptance criteria.
- **[69d3a62e4e28] (severity: writing)** Expand the related work section to include the historical comparison suggested by prior reviewer david-krakauer-simulated regarding skill evolution lineage.
- **[1034d23c488f] (severity: science)** Recalculate the 'Cost / pt' column in Table 2 (lines 320-335) to ensure consistency with 'Train tokens' and Table 1 score gains (e.g., LiveMath reported 3.6M vs calculated 0.79M).
- **[468a8bd38a5e] (severity: science)** Code repository at https://aka.ms/SkillOpt is not accessible for independent verification. Include a public GitHub/GitLab link with commit hash in the paper for reproducibility.
- **[cafbcbba7997] (severity: science)** Add a reproducibility checklist section detailing dependencies, environment setup, and hardware requirements needed to reproduce the 52 benchmark cells.
- **[19c6ee1fd0e4] (severity: writing)** Include test coverage metrics and CI/CD status badges in the paper appendix to demonstrate code quality and reliability of the implementation.
- **[f9ebd8597420] (severity: writing)** Add specific dataset version numbers or commit hashes for all benchmarks (e.g., SearchQA, SpreadsheetBench) in references.bib or Section 4 to ensure data provenance reproducibility.
- **[605fa7eafd2c] (severity: writing)** Specify an open-source license (e.g., MIT, Apache 2.0) for the released code and skill artifacts in sections/0_abstract.tex or the repository README.
- **[3a6a6e384017] (severity: writing)** Provide a pinned Git commit hash or tag for the code at https://aka.ms/SkillOpt to prevent link rot and version drift between paper submission and code access.
- **[da7617c42b32] (severity: writing)** Complete bibliography entries for cited works (e.g., memp, autorefine, procmem, evolver) with URLs, DOIs, or journal metadata to ensure citation data provenance.
- **[b2675fadc8b4] (severity: writing)** Add accessible alt text descriptions to all \includegraphics figures (Fig 1, 2, 3) for screen reader compliance.
- **[3a0a976ccc5c] (severity: writing)** Ensure subplot labels (a), (b), (c) appear directly on Figure 3 images, not solely in the caption.
- **[af5ad84dce7e] (severity: writing)** Increase font size in Figure 4 (skill_excerpts) from \footnotesize to \scriptsize minimum for print legibility.
- **[830b3263e68a] (severity: writing)** Verify color palettes in Figures 1 and 2 are colorblind-safe and distinguishable in grayscale print.
- **[bdab7335a1a7] (severity: writing)** Refactor Figure 3 (epoch_ablation) to use the subcaption package for machine-readable subplot labels rather than relying on a single PDF image.
- **[ad7b7787b558] (severity: writing)** Replace "text-space optimizer" with "text-based optimizer" for clarity.
- **[45a67ff7022d] (severity: writing)** Replace "harness" with "execution environment" in Abstract and Methods.
- **[11e43d163e64] (severity: writing)** Define acronyms QA, SoK, and MCQ at first use.
- **[85e45e713b42] (severity: writing)** Replace "rollouts" with "executions" or "test runs".
- **[e82f78c25103] (severity: writing)** Standardize "selection split" to "validation set".
- **[f9a2b3c4d5e6] (severity: writing)** Replace "frontier models" with "leading-edge models" in Introduction.
- **[1ca8b86b564b] (severity: writing)** Replace "trajectory" with "execution trace" in Methods (Section 3.1).
- **[230007bee554] (severity: writing)** Replace "slow/meta update" with "long-term guidance update" in Methods (Section 3.5).
- **[69dcf8f7f4ea] (severity: science)** The claim that 'without the gate, a stronger optimizer could push harmful rewrites' (Section 4.2, 'Effect of optimizer strength') is a causal assertion not directly tested. No ablation compares performance with and without the validation gate itself.
- **[0a08b9b24041] (severity: science)** The validation gate ablation only tests 'rejected-edit buffer' removal, not the gate's strictness (strictly greater vs. greater-or-equal). Section 4.2 states 'ties are rejected' but this threshold is not ablated.
- **[66b70e297876] (severity: writing)** The abstract still claims 'first systematic controllable text-space optimizer' without qualifying that TextGrad, GEPA, and EvoSkill also implement validation gates. Qualify as 'among the first' or specify unique contribution.
- **[f25dcdefdcd8] (severity: science)** The '52 of 52 cells best or tied-best' claim lacks statistical significance testing or confidence intervals. Many inter-method differences are <2 points. Re-run analysis with proper statistical validation.
- **[c94509b2b3a4] (severity: writing)** Cross-harness transfer claims (+59.7 SpreadsheetBench Codex→Claude Code) still frame single benchmark case study as generalizable deployment signal. Acknowledge limited evidence base more prominently.
- **[1bed5bd4924b] (severity: writing)** The paper still describes deep-learning analogy as 'operational rather than decorative' (Introduction, paragraph 4) without evidence of functional equivalence to weight-space optimization. Qualify as 'conceptual analogy'.
- **[f6c3883b3af6] (severity: writing)** Add a paragraph in the Discussion or Conclusion explicitly addressing potential misuse scenarios (dual-use) and recommending safety constraints for the optimizer in high-risk domains.
- **[c3d5558fc272] (severity: science)** Report variance (standard deviation) across multiple random seeds for the 52 cells in Table 1. Single point estimates without variance prevent statistical significance claims.
- **[ee480dd615be] (severity: science)** Justify the small training set sizes for LiveMathematicianBench (35 items) and ALFWorld (39 tasks). Demonstrate sensitivity to training set size to rule out overfitting.
- **[c1da1cdc4e65] (severity: science)** Report confidence intervals or standard deviations for all benchmark scores. The paper claims 52/52 wins but provides no uncertainty estimates. With 52 cells and 6+ baselines per cell, multiple-comparisons inflation is a serious concern. Add SE/SD across seeds or bootstrap CIs.
- **[810005739e59] (severity: science)** Perform statistical significance testing between method and baselines. Point differences like 87.1 vs 87.0 in Table 2 (ablation_sweeps) lack statistical justification. Use paired t-tests or non-parametric equivalents with proper multiple-comparison correction (e.g., Bonferroni, Holm-Bonferroni).
- **[024f691a17fa] (severity: science)** Specify the number of independent runs per configuration and random seeds. The paper mentions 'deterministic train/selection/test splits' but does not report variance across seeds or runs, making reproducibility and effect-size uncertainty impossible to assess.
- **[d2b68b27d19c] (severity: science)** Address overfitting to the selection split in the validation gate. With strict inequality gating (> current score), small noise-driven improvements could accumulate. Report selection-vs-test gap analysis (e.g., Figure 1 shows trends but no statistical test of generalization gap).
- **[3ce13e9a9c16] (severity: science)** Provide power analysis or sample-size justification for benchmarks with small training pools (e.g., LiveMath: 35 training items). Small samples may not support the claimed effect sizes, and Type II error rates are unknown.
- **[e6e9f34c6838] (severity: writing)** Add \usepackage{xcolor} explicitly in main.tex preamble. Current use of \textcolor, \definecolor (e.g., sections/3_methods.tex delta-gain annotation) relies on implicit loading which risks compilation failure.
- **[3623fcad37ac] (severity: writing)** Replace \resizebox in tab:ablation_sweeps (sections/3_methods.tex, line ~320) and tab:transfer_all (sections/3_methods.tex, line ~480) with \small or \footnotesize. Resizing scales font size inconsistently with the rest of the document.
- **[80d999c1cac2] (severity: writing)** Remove unused packages \usepackage{pifont}, \usepackage{wrapfig}, and \usepackage{cleveref} from main.tex preamble to reduce dependency overhead.
- **[2e66dc7a58ed] (severity: writing)** Move Table 1 (main_results_by_harness) from sections/3_methods.tex to sections/4_experiments.tex to align with standard narrative flow (results after methods).
- **[4714e192726b] (severity: writing)** Break down long sentences in the Abstract (lines 2-4) and Introduction (lines 60-70) to improve readability and reduce cognitive load.
- **[d198c6f3acd3] (severity: writing)** Consolidate duplicate macro definitions (e.g., \providecommand{\ourmethod}) found in sections/3_methods.tex and sections/4_experiments.tex into main.tex preamble.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 44 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
