# Revision Specification: Paper Science Revision — PROJ-619-delta-discriminative-token-credit-assign round 1

**Generated**: 2026-06-19T00:49:24.079922+00:00
**Kind**: paper_science
**Project**: PROJ-619-delta-discriminative-token-credit-assign
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[323b14e45b63] (severity: writing)** Verify all arXiv citations and replace future-dated references (2025-2026) with stable, verifiable versions or add notes explaining their status
- **[cd607ba0ba8f] (severity: writing)** Clarify model version references (Qwen3 does not exist as of current date); use existing Qwen2.5 or add disclaimer about hypothetical models
- **[edb06be1dbfe] (severity: writing)** Improve statistical reporting transparency by reporting variance/std across evaluation runs beyond the Mann-Whitney U test p-values
- **[6fb04f41e0e8] (severity: writing)** Add a proper citation for the Brumo25 benchmark used in the experimental evaluation (Section 5.1).
- **[e7a624564a22] (severity: writing)** Provide citations for the GPQA-Diamond and MMLU-Pro benchmarks used in out-of-domain evaluation (Appendix app:ood).
- **[ef12f7555888] (severity: writing)** Code repository not accessible for direct review; paper mentions GitHub URL but no code artifacts provided in this submission. For proper code quality review, access to the implementation is required.
- **[fd804ccf358f] (severity: writing)** No test files, CI configuration, or dependency specifications (requirements.txt, pyproject.toml) included in the submission. These are essential for reproducibility from scratch.
- **[d54bf44c2a3d] (severity: writing)** Appendix D (DelTA Implementation Details) describes algorithm steps but lacks pseudocode or reference implementation snippets that would aid independent verification.
- **[23495fee1560] (severity: writing)** Training hyperparameters are documented (Table~\ref{tab:RL-hyper-parameters}), but seed values, random state handling, and exact library versions are not specified, limiting reproducibility.
- **[fd9982d827c1] (severity: writing)** Add specific download URLs or version tags for DeepMath-103K to enable exact training data reproduction.
- **[712c3c229585] (severity: writing)** Include persistent URLs or DOIs for all benchmark citations (e.g., AIME24, AIME25).
- **[3218ff3e9c6a] (severity: writing)** Explicitly state the license types for all datasets used, rather than a generic statement in Appendix app:hyp.
- **[2de9e059d2f9] (severity: writing)** Replace \captionof usage in multi-panel figures (e.g., Section 6.2, Figures 3-4 around lines 645-660) with standard \subcaption environments for consistent numbering and accessibility.
- **[954b69fe88f1] (severity: writing)** Add explicit units to axis labels or captions for all plots (e.g., 'Entropy (bits)', 'Reward (0-1)') to ensure scientific precision.
- **[2cdd41995376] (severity: writing)** Optimize 'figs/token_c/*.pdf' file sizes; current sizes (~1.1-1.2MB) suggest rasterization. Re-export as vector graphics for print legibility.
- **[3ab388688df5] (severity: writing)** Consider adding explicit alt text or descriptive captions for complex diagrams (e.g., Figure 1, Line 260) to improve accessibility compliance.
- **[cb33a4c71d42] (severity: writing)** Replace 'token-gradient vectors' with 'token gradients' throughout (e.g., Abstract, Line 13) to reduce compound noun density.
- **[d1cb23ff58a4] (severity: writing)** Define 'LM-head' explicitly as 'language model head' on first use in Appendix (Line 1050) for non-specialist clarity.
- **[ff14e4de9a14] (severity: writing)** Simplify 'entropy-regularized assignment problem' (Line 230) to 'score calculation using entropy' to improve accessibility.
- **[f7185d3c219b] (severity: writing)** Replace 'stop-gradient token coefficients' (Line 260) with 'fixed token weights' to avoid implementation-specific jargon in main text.
- **[9123da0516d7] (severity: writing)** Define 'GAE' (Generalized Advantage Estimation) when first used in SAPO hyperparameter table (Appendix) or text, as 'Gae Gamma' and 'Gae Lam' appear without context.
- **[537a57eda482] (severity: writing)** Define 'CoT' (Chain of Thought) before using the abbreviation in Appendix (Line 1650, 'long-CoT RL training').
- **[aa0093a979ad] (severity: writing)** Define 'SGLang' in Table 1 (Line 1200) as it is an external inference engine not defined elsewhere.
- **[a46ad0aa6970] (severity: writing)** Replace 'side-wise centroids' with 'group averages' throughout (e.g., Section 3.1, Line 310) to reduce jargon density.
- **[81438054e410] (severity: writing)** Add plain-language explanation for 'self-normalized RLVR surrogate' when first introduced (Section 3.2, Line 420).
- **[62b8a84f03ab] (severity: writing)** Replace 'positive-advantage responses' / 'negative-advantage responses' with 'high-reward / low-reward responses' for accessibility.
- **[d14be9888ea2] (severity: writing)** Clarify in the Limitations section that safety alignment or adversarial testing was not evaluated, to prevent inference that the improved models are safe for deployment.
- **[88b23d5f48db] (severity: science)** Clarify whether method-specific hyperparameters for SAPO/FIPO are intrinsic or tuned, as Section sec:exp_s claims 'same hyperparameters' but app:baseline-details lists unique settings.
- **[fc735678231d] (severity: science)** Explicitly acknowledge the limitation of single-training-seed results in the Limitations section, noting that RL training variance is not captured by evaluation-run-level significance tests.
- **[96965ef4434c] (severity: science)** Provide statistical significance tests for code generation and OOD results (Tables tab:code_tab, tab:ood_tab) or explicitly state they are not evaluated to avoid overclaiming robustness.
- **[5ab5bf356cf7] (severity: writing)** Report exact p-values and effect sizes (e.g., rank-biserial correlation) for the Mann-Whitney U tests in Appendix app:sig to ensure reproducibility.
- **[36adfe34e8b0] (severity: writing)** Include standard deviations or 95% confidence intervals in Table tab:results_main to visualize evaluation variance across the 16 runs.
- **[674db1646b05] (severity: science)** Explicitly state in the Limitations section that significance tests reflect evaluation sampling variance, not training seed variance, given the single-seed training protocol.
- **[822db6604490] (severity: writing)** Remove duplicate package declarations for hyperref, url, amsmath, amsfonts, and bm. Load each package only once in the preamble (Lines 6, 7, 9, 13, 23, 24, and math_commands.tex Line 21).
- **[024736dc258f] (severity: writing)** Add \label commands to main sections missing them (Analysis, Related Work, Conclusion, Limitations, Broader impacts) to ensure consistent cross-referencing (Lines 577, 658, 673, 681, 701).
- **[ac682beb7abb] (severity: writing)** Standardize table environments. Replace wraptable with table or table* for ICLR submission consistency, or ensure wrapfig package is explicitly loaded in the main preamble if wraptable is retained (tabs/abl_tab.tex, tabs/ana_own.tex, tabs/code_tab.tex, tabs/ood_tab.tex).
- **[aaa3a26b5f85] (severity: writing)** Refine wrapfigure hygiene in Appendix. Use subcaption package for sub-figures instead of manual \par and \vspace commands inside the figure environment (Line 1405).
- **[f3f555a43589] (severity: writing)** Inconsistent benchmark naming: 'Brumo 25' in Section 5.1 (Experimental Setup) vs 'Brumo25' in Table 1 (tabs/main_tab.tex). Maintain consistent naming throughout.
- **[24246eff60eb] (severity: writing)** Remove unprofessional comments from LaTeX source, e.g., '% good luck!!!!!!' (line 67, iclr2026_conference.tex author section). Such comments are inappropriate for submission.
- **[55d976d9d431] (severity: writing)** Replace 'To better reveal' with 'To better assess' in Section 5.1 (Experimental Setup) for precision. The current phrasing is imprecise.
- **[6cbec90ed647] (severity: writing)** Remove unprofessional Chinese comments from LaTeX source and included files (e.g., % 提供了丰富的数学符号 in iclr2026_conference.tex preamble, % 下标版本 in tab_com.tex). All non-English comments should be removed for a professional submission.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 41 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
