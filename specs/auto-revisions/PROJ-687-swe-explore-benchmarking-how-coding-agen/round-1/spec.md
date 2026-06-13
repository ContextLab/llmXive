# Revision Specification: Paper Science Revision — PROJ-687-swe-explore-benchmarking-how-coding-agen round 1

**Generated**: 2026-06-13T21:59:46.738482+00:00
**Kind**: paper_science
**Project**: PROJ-687-swe-explore-benchmarking-how-coding-agen
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[6fff07aad923] (severity: writing)** Verify all 2026-dated citations exist on arXiv or correct publication dates. Several model names (GPT-5.4, Gemini-3-Pro, Sonnet-4.6) appear future-dated and need validation against actual model releases.
- **[876cbd09116f] (severity: writing)** Complete truncated tables in LaTeX source (e.g., tab:compare, tab:main-results show '... N rows omitted'). Ensure all data rows are present in final submission.
- **[f6d7258c88cd] (severity: writing)** Add verification_status verified to bibliography entries in state/citations/PROJ-687.yaml for all 2026-dated references before resubmission.
- **[b186fea8eea7] (severity: writing)** Correct citation in Section 3.2: 'SWE-bench Multilingual' currently cites `yang2025swesmith` (SWE-smith) but should cite `zan2025multiswebenchmultilingualbenchmarkissue` (Multi-SWE-bench) or clarify the data source relationship.
- **[d631fabafb4a] (severity: writing)** Resolve naming inconsistency in Table 1: 'Loc-Bench' cites `chen2025locagent` (LocAgent). Ensure benchmark name matches source paper title or clarify if distinct.
- **[2b1d4d97326d] (severity: writing)** Add citations or clarification for proprietary model versions (e.g., GPT-5.4, Gemini-3-Pro) listed in Section 3.3 to match the citation style used for Claude Code.
- **[7c25a143e076] (severity: science)** Code artifacts not provided for review. Paper references external GitHub (github.com/Qiushao-E/SWE-Explore-Bench) and HuggingFace but reviewer cannot access or evaluate actual implementation code, test suites, or evaluation scripts.
- **[52e5870ddcd9] (severity: science)** Reproducibility claims in Appendix Section 'Reproducibility, Compute, and Limitations' cannot be verified without access to benchmark scripts, data processing pipelines, and evaluation harness code.
- **[a8da3280137f] (severity: writing)** Add an explicit license declaration (e.g., MIT, CC-BY) for the SWE-Explore dataset in Appendix E to ensure legal clarity for downstream users.
- **[3ed9901c45df] (severity: writing)** Include a dataset version tag (e.g., v1.0) in Section 5.2 or Appendix A to prevent reproducibility issues if the GitHub/HF repository is updated.
- **[8d09e27507a4] (severity: writing)** Cite the specific schema file (e.g., `schema.json`) in the artifact description rather than just claiming a schema exists.
- **[2626a51e6f6c] (severity: writing)** Add alt text descriptions to all figures for accessibility compliance. Current LaTeX source lacks lt or equivalent accessibility metadata for motivation.pdf, instance.pdf, degradation_grid.pdf, framework.pdf, and lang_distribution.pdf.
- **[cd81bb6a7c10] (severity: writing)** Verify all figures meet 300 DPI print resolution requirements. The degradation_grid.pdf (19KB) and lang_distribution.pdf (19KB) are unusually small file sizes for publication-quality figures; ensure vector formats (PDF/SVG) are used rather than raster.
- **[ce55a370c28f] (severity: writing)** Ensure axis labels in degradation_grid.pdf include units and clear tick mark descriptions. Caption mentions α∈{0,25,50,75,100}% but figure axes should explicitly label this percentage scale.
- **[4a3e9af9a3d8] (severity: writing)** Replace "trajectory-grounded supervision" with "supervision from agent execution paths" in Abstract and Section 3.3 to improve accessibility for non-specialists.
- **[3e88591bfeff] (severity: writing)** Define "Oracle" as "Ideal Baseline" on first use in Section 5.3 to clarify it represents perfect context rather than a specific tool.
- **[eebd53b23a86] (severity: writing)** Simplify "context-efficiency" to "context usage efficiency" in Section 4.2 and Abstract to reduce compound jargon density.
- **[cedf38875817] (severity: science)** Resolve the contradiction between Section 5.2 (n=150 instances) and Table 3 caption (explorer-level correlation). Clarify if correlation is per-instance or per-explorer.
- **[ec98963ad195] (severity: science)** Justify the logical step from 'intersection of successful trajectories' to 'necessary ground truth' in Section 3.3. Intersection implies consensus, not necessity.
- **[954be2ecc7d7] (severity: science)** Ground truth filtering with >=2 successful trajectories biases benchmark toward solvable instances. Claim of generalizability to unsolved problems is unsupported. Add discussion of selection bias in Section 3.3.
- **[28a2b8f6f7d5] (severity: science)** Correlation r=0.950 in Table 2 is computed on n=150 subset without cross-validation across model families or difficulty strata. This risks overfitting. Add uncertainty bounds or holdout analysis.
- **[1ca4305c902b] (severity: writing)** Multilingual coverage claim of 10 languages is misleading because 64.5% are Python per Appendix D. Temper generalization claims about cross-language exploration capabilities.
- **[5dd4e54dad5c] (severity: science)** Downstream validation uses restricted-context environment with fixed agent. This creates circular validation where exploration quality is validated against a repair task dependent on same exploration output. Acknowledge this limitation in Section 4.2.
- **[27c13708fad6] (severity: writing)** Oracle degradation experiment in Section 4.4 concludes missing context is dominant failure mode without acknowledging this may be specific to repair agent capabilities. Qualify the conclusion.
- **[1aa24bbb60fa] (severity: writing)** Add a dedicated Ethics Statement or Broader Impact section per NeurIPS 2026 guidelines (referenced in document class).
- **[43da97271898] (severity: writing)** Explicitly detail data sanitization procedures for GitHub issues to ensure no PII or secrets remain in the benchmark.
- **[64b10853369d] (severity: writing)** Include a brief discussion on dual-use risks, specifically regarding automated vulnerability discovery and codebase navigation.
- **[fa559498eb05] (severity: science)** Address selection bias in ground-truth construction (Section 3.2). Only instances solvable by >=2 agents are included, limiting generalizability to hard/unresolved issues.
- **[43c517a4c46c] (severity: science)** Explain the high correlation (r=0.950) in Table 3 (Section 5.2). Verify no data leakage exists between exploration metrics and downstream repair validation.
- **[dd6a944b74c5] (severity: science)** Clarify the 'LLM-based promotion' step in GT refinement (Appendix B). Provide audit logs or inter-annotator agreement to ensure reproducibility.
- **[801928f87371] (severity: science)** Correlation analysis (Table 3, Sec 5.2) lacks p-values and confidence intervals. With n=150 instances but correlations computed across explorers (likely <20), report 95% CIs for r and rho values to assess statistical significance of the claimed 'highest' correlations.
- **[22165ae27ef7] (severity: science)** Multiple comparisons not addressed. Testing 10+ metrics (Table 4) without correction inflates Type I error. Apply Bonferroni or FDR correction when claiming any metric 'outperforms' others.
- **[b27954455057] (severity: science)** Degradation analysis (Fig 3, Sec 5.4) claims rate 'jumps' between alpha=50 and alpha=75 but provides no statistical test. Report confidence intervals on resolve rates at each alpha level and p-values for pairwise comparisons.
- **[b286769628e9] (severity: science)** Aggregation method (Appendix A) states 'per-instance then averaged' but does not specify weighted vs. unweighted averaging or report variance across instances. Add instance-level variance metrics to support generalization claims.
- **[a354f96f13ed] (severity: writing)** LaTeX source provided in review input is truncated (ends with 'summary truncated to 60% of input' comment). Verify complete file integrity.
- **[0f57f753f969] (severity: writing)** Inconsistent table input files for downstream validation: e001 uses '3-co', e002 uses '2-resolve-rate'. Ensure single source of truth.
- **[47df5241f4fb] (severity: writing)** Use standard \caption{} inside table environments instead of \captionof{} in e002 for consistency.
- **[388d3e9a4a4d] (severity: writing)** Verify figure inputs: e000 uses PDF, e001 uses .tex input for motivation. Standardize to one format.
- **[138f10eb841b] (severity: writing)** Appendix A contains grammatical fragments (e.g., 'SWE-Explore constructed from' lacks a verb; 'Keep instance only when' should be plural 'instances').
- **[b979dcb3de57] (severity: writing)** Section 5.1 states 'Sparse retrievers remain close to Random.' Replace 'remain' with 'perform' for grammatical precision.
- **[60f6a7c8673b] (severity: writing)** Section 5.3 uses the abbreviation 'pp' for percentage points without prior definition. Spell out or define on first use.
- **[e513a2287d2d] (severity: writing)** Section 3.3 notation is inconsistent: uses $T$ in one paragraph and $T_m$ in the next for trajectory sets. Unify notation.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 42 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
