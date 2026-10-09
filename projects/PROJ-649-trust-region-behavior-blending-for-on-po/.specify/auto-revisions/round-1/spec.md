# Revision Specification: Paper Science Revision — PROJ-649-trust-region-behavior-blending-for-on-po round 1

**Generated**: 2026-06-23T00:40:33.798665+00:00
**Kind**: paper_science
**Project**: PROJ-649-trust-region-behavior-blending-for-on-po
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[0f871ef5ee0e] (severity: science)** Statistical significance testing is absent for small performance differences (0.4-0.9 points in Table 1). Claims like "strongest average" and "outperforms" should include variance estimates or confidence intervals to support the conclusion.
- **[f777ef82d966] (severity: writing)** Several citations refer to 2025-2026 arXiv papers (Veto, Entropy-Aware OPD, TIP, Li 2026, Qwen3) that are difficult to verify. Please confirm these sources exist and accurately support the attributed claims, or replace with verified alternatives.
- **[47bee7950a45] (severity: writing)** The claim that "TRB prefixes yield higher success than vanilla-OPD prefixes across all tested lengths for both continuation models" (Section 4.3, line 183) is strong. Please verify this holds for every length tested in Figure 4, not just on average.
- **[757a16c92738] (severity: writing)** The specific numerical claim "only about a 0.0093 fraction of generated tokens are replaced by the teacher" (Section 4.3, line 166) requires implementation verification. Please confirm this value matches the actual SKD configuration used.
- **[08f17ee53ecf] (severity: writing)** No code artifacts provided for review. This arXiv-ingested paper lacks implementation files, test suites, or dependency specifications. Code quality review cannot be performed without access to the actual training/evaluation codebase.
- **[610411823c4e] (severity: writing)** Reproducibility from scratch cannot be assessed. The paper mentions verl, SGLang, FSDP2, math-verify but provides no repository link, Dockerfile, requirements.txt, or environment specification for reproducing experiments.
- **[e65515e5e049] (severity: writing)** No modularization or code structure review possible. Implementation details (trust-region solver, binary search, KL estimation) are described mathematically but no source code is available to evaluate readability, modularity, or test coverage.
- **[99b15effb1d2] (severity: writing)** Add a bibliography entry for the OpenThoughts3-1.2M corpus mentioned in Section 5.1 (Appendix Experimental Details).
- **[9564c772ed78] (severity: writing)** Specify license terms for Qwen3 models and evaluation datasets (MATH, GSM8K, AIME).
- **[19828833cc24] (severity: science)** Include a persistent link to the code and data artifacts for reproducibility.
- **[2a461ea95b27] (severity: writing)** Add explicit axis labels to all figure captions (e.g., x-axis = training steps, y-axis = metric name). Figures 2-4 currently imply axes but do not state them explicitly in captions per ACL/ML venue standards.
- **[ffe8460a6895] (severity: writing)** Ensure color choices are colorblind-safe and include non-color encodings (patterns, labels) for Figure 8's coral/teal coding. Grayscale print legibility should be verified.
- **[159ba1ad6c64] (severity: writing)** Add descriptive alt-text equivalents to complex figures (7, 8) to support accessibility. Current captions describe content but lack structured accessibility markup.
- **[1089c267cd05] (severity: writing)** Expand 'KL' to 'Kullback-Leibler' at first use in Abstract or Introduction to aid non-specialist readers.
- **[2a5e54d2cea0] (severity: writing)** Replace or define 'behavior policy', 'rollouts', and 'prefix' with plain-language equivalents (e.g., 'sampling strategy', 'generated sequences', 'text so far').
- **[d2b34d986df1] (severity: writing)** Define acronyms 'FSDP2', 'SGLang', and 'EOS' in Appendix A upon first mention to ensure reproducibility and clarity.
- **[c76b1430c3d7] (severity: writing)** Add brief parenthetical explanations for technical terms like 'exposure bias', 'top-k support', and 'exponential tilt' to reduce barrier to entry.
- **[e8433b58c407] (severity: science)** The paper claims TRB's success stems from the trust-region mechanism, but the comparison with Fixed-ε blending could better isolate whether annealing (vs. mechanism) drives the improvement. Consider adding a control where Fixed-ε uses the same annealing schedule without the trust-region constraint.
- **[0e2c0c0b51bc] (severity: writing)** Section 5.3 cites "0.0093 fraction of generated tokens replaced by teacher" for SKD without defining how this was measured. This affects reproducibility of the SKD baseline comparison.
- **[f6c1b25ab83b] (severity: science)** Table 1 shows performance differences between TRB and baselines, but no statistical significance tests are reported. Given checkpoint selection is based on mean scores across benchmarks, variance estimates would strengthen the causal claim that TRB genuinely outperforms alternatives.
- **[6742c4a8fa13] (severity: writing)** Main results table lacks variance/error bars. Claiming 'strongest average' without statistical significance testing or confidence intervals overstates the certainty of the reported differences.
- **[a25deb181ad9] (severity: writing)** Mechanistic claims in Discussion (e.g., 'TRB changes the early states on which OPD begins learning') are supported by continuation gain analysis which is a proxy probe, not direct evidence of training dynamics. Language should be more qualified.
- **[352dd651ff0b] (severity: writing)** Warmup horizon sensitivity is not fully addressed. Results shown for K∈{15,25,50} but no analysis of whether optimal K generalizes across problem difficulty or model scales.
- **[a7bdb6374df5] (severity: writing)** Add a brief 'Safety and Ethics' statement or expand the Limitations section to address potential dual-use implications of improved LLM reasoning and confirm data licensing compliance for OpenThoughts3.
- **[cff402a6241b] (severity: science)** Report variance across multiple random seeds for all main benchmark results. Table 1 shows single-point estimates without error bars or standard deviations, making it impossible to assess whether TRB's 0.4-0.9 point advantages are statistically significant.
- **[271e449b84f7] (severity: science)** Add statistical significance testing (e.g., t-tests, confidence intervals) for the claimed "strongest average" in Table 1. The marginal improvements (33.2 vs 32.3, 44.4 vs 44.0) lack uncertainty bounds necessary to substantiate superiority claims.
- **[c94f435d68a1] (severity: science)** Address checkpoint selection bias. Section 5.2 states methods are compared using "the checkpoint with the highest mean score over the setup-specific benchmark suite." This introduces selection bias when comparing methods—each method's best checkpoint is selected independently rather than comparing at matched training steps.
- **[ba9466558394] (severity: science)** Provide multiple seed training curves with error bands in Figures 2-4. Figure 2 shows single trajectories for SKD, TRB, and OPD without variance information, limiting interpretability of the "faster early rise" claim.
- **[2d8787e007a4] (severity: science)** Clarify the number of random seeds used for training runs. Appendix A does not specify if results are averaged over seeds, which is critical for statistical validity.
- **[72196be2a5b4] (severity: science)** Report variance (standard deviation) or confidence intervals for benchmark scores in Table 1. Point estimates alone do not support claims of statistical superiority.
- **[e6bd79f920e6] (severity: science)** Address checkpoint selection bias in Section 5.1. Selecting the best checkpoint per method inflates performance; compare at fixed steps or use a held-out validation set.
- **[8518dc497df1] (severity: science)** Justify evaluation sample sizes (e.g., n=32 for GSM8K). Smaller sample sizes increase variance in pass@1 estimates; ensure sufficient power for comparisons.
- **[609ed1b46ce5] (severity: writing)** The custom redefinition of \paragraph (line ~30) replaces the standard paragraph heading with a bold label and a period, which breaks the usual hierarchy and may interfere with hyperref anchors. Use the standard \paragraph formatting or replace these headings with \subsubsection for proper hierarchy.
- **[53071b6c7e08] (severity: writing)** Figure placement specifiers are overly restrictive (e.g., \begin{figure}[h] on lines ~71, ~210, ~260). Change them to [htbp] (or similar) to give LaTeX flexibility and avoid float placement warnings.
- **[a7b404b82e8f] (severity: writing)** The bibliography style is not explicitly set; ACL style typically requires \bibliographystyle{acl_natbib} before \bibliography{custom}. Add this command to ensure correct citation formatting.
- **[155b481c98af] (severity: writing)** Several lines exceed typical 80‑character width (e.g., long equations and table definitions). Consider line‑wrapping for readability and to conform to style guidelines.
- **[da8a1dc2b134] (severity: writing)** Standardize title capitalization for 'Trust-Region Behavior Blending' (capitalize 'Behavior') in Abstract, Section 4, and Figure 1 caption.
- **[5c6334e4868f] (severity: writing)** Align model naming convention: use 'Qwen3-1.7B-Base' consistently in Appendix E figures to match Section 5 and Table 1.
- **[ea696c8d6584] (severity: writing)** Improve sentence flow in Section 5 intro: change 'evaluate TRB along one main question, whether' to 'evaluate TRB by asking whether'.
- **[5f41e71265ce] (severity: writing)** Remove unnecessary comma in Appendix reference in Section 5 ('hyperparameters, and implementation details').


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 40 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
