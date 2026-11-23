# Revision Specification: Paper Science Revision — PROJ-639-https-arxiv-org-abs-2605-28774 round 2

**Generated**: 2026-06-29T11:15:59.634571+00:00
**Kind**: paper_science
**Project**: PROJ-639-https-arxiv-org-abs-2605-28774
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[c9e4772c4dd3] (severity: writing)** Resolve numerical discrepancy in 4B Pass@4 delta: Table shows 74.1 vs 71.7 (diff 2.4), but reported delta is 2.3. Ensure consistency between average columns and delta rows.
- **[2f6ef42459a8] (severity: science)** Verify citation support for claims (e.g., GRPO definition, SFT limitations). The provided bibliography is truncated, preventing full verification of whether cited sources support the attributed claims.
- **[a43e3b2dd312] (severity: science)** Missing implementation code (training/eval scripts) required for reproducibility.
- **[451112fe8ab8] (severity: science)** Missing dependency specifications (e.g., requirements.txt, environment.yml).
- **[cb8dcb83b742] (severity: science)** Missing configuration files for RL framework (verl/rllm) referenced in appendix.
- **[ab05a2c34adb] (severity: writing)** Add explicit provenance for all external datasets (MathVision, DynaMath, V*, VisualProbe, HR-Bench, MMSearch, etc.) including URLs, version numbers, and license information. This will clarify reuse permissions and prevent future legal issues.
- **[4065cd8c9b96] (severity: writing)** Provide a data schema description for the SFT and RL trajectory files (e.g., JSON format, required fields, tokenization conventions) and document how missing or malformed entries are detected and handled during training.
- **[33d7d2d08091] (severity: writing)** Include a version control reference (e.g., Git commit hash or tag) for the code used to generate the figures, tables, and training pipelines. Currently the repository is not mentioned, which hampers reproducibility.
- **[73963fc2d267] (severity: writing)** Document the licensing and usage terms of the external tools (Python interpreter, Tavily web search, image zoom‑in) and specify how API endpoints are accessed (including any API keys). This mitigates link‑rot risk and clarifies compliance.
- **[8fe5cebff0fd] (severity: writing)** Describe the handling of potential missing data in the benchmark evaluations (e.g., images that fail to load, tool call timeouts) and the fallback strategies employed. This is essential for understanding robustness.
- **[c5c88fc58aa1] (severity: writing)** Archive the exact versions of the benchmark datasets (e.g., via Zenodo or a similar DOI service) and provide permanent links. This prevents future link rot and ensures long‑term accessibility.
- **[7a626768ee36] (severity: writing)** Add `alt` text to all `\includegraphics` commands to ensure accessibility compliance for screen readers.
- **[cff714a180b5] (severity: writing)** Describe color mappings in figure captions (e.g., 'AXPO in blue, GRPO in red') to ensure legibility for colorblind readers and print.
- **[dc5da3629bbf] (severity: writing)** Verify font sizes in `fig:analysis` subfigures (0.32\linewidth) are legible at standard print scale; consider increasing width or reducing caption text.
- **[77e76cbf143d] (severity: writing)** Define every acronym (e.g., AXPO, GRPO, SFT, RL, PPO) at its first occurrence; otherwise readers unfamiliar with the field must guess their meaning.
- **[36e29f53d91d] (severity: writing)** Replace or explain highly technical terms such as “Thinking-Acting Gap”, “tool‑using subgroup”, “all‑wrong”, and “tool‑call tokens” with clearer, plain‑English descriptions or add brief parenthetical definitions.
- **[726e36f40c1d] (severity: writing)** Reduce the density of bold/italic markup in sentences (e.g., multiple bolded phrases in the same paragraph) to improve readability for non‑specialist audiences.
- **[2180d3590315] (severity: writing)** Simplify overly long, compound sentences (e.g., the abstract and introduction contain multiple clauses separated by commas) to make the narrative easier to follow.
- **[52ac4c4471e5] (severity: writing)** Provide a concise, non‑technical summary of the core idea (resampling at the tool‑call boundary) early in the paper, avoiding jargon‑heavy phrasing.
- **[7e154ecbe9aa] (severity: writing)** When referring to specific metrics (Pass@1, Pass@4, tool‑utilization rate), include a brief reminder of what they measure for readers not familiar with the evaluation protocol.
- **[a49748ca609e] (severity: writing)** Avoid using domain‑specific shorthand like “AXPO w/o prefix fix” in table captions without an accompanying plain‑language explanation.
- **[7378adb66db6] (severity: writing)** Standardize the naming of components (e.g., sometimes “tool‑call resampling” is written as “tool‑call resampling”, other times as “	oolresample”) to prevent confusion.
- **[9c417d32bfaf] (severity: writing)** Consider adding a glossary of key terms and abbreviations to aid readers from adjacent fields.
- **[88baebf8814f] (severity: science)** Clarify the theoretical link between uncertainty-based prefix selection and the success probability condition in Proposition 1 (Sec 3.1).
- **[deb5faf4ffe2] (severity: science)** Explicitly address the assumption that the GPT-5.4 proxy for image search preserves the tool-output distribution in Appendix A.4.
- **[9cb248c39142] (severity: writing)** Temper the claim that 8B AXPO 'surpasses' the 32B Base baseline (75.8% vs 75.1%) to 'matches or slightly exceeds' or provide statistical significance testing, as the margin is within the reported variance of the 8B model (std ~1.2%).
- **[0e0132b24f43] (severity: writing)** Clarify in Table `tab_image_search.tex` and the main text that the 'unseen tool' experiment used a GPT-5.4 text proxy rather than a real API tool, to avoid overstating the generalization to actual external tool interfaces.
- **[fb0d560dda06] (severity: writing)** Expand the Broader Impacts section to explicitly discuss dual-use risks of enhanced agentic tool capabilities, beyond sandboxing.
- **[0fc924220ade] (severity: writing)** Address privacy implications of the web search tool usage (e.g., query logging, data retention by third-party APIs).
- **[3ea62cbedb67] (severity: writing)** Discuss mitigation strategies for potential misuse (e.g., adversarial prompts, automated harmful actions) rather than stating safety is out of scope.
- **[82bcfa74dfe1] (severity: science)** Report statistical significance (p-values or confidence intervals) for the main performance gains, particularly the 8B vs 32B comparison, as the reported standard deviations (tab_main_p1_std.tex) suggest the margins are within noise.
- **[bc84f4131e61] (severity: science)** Clarify the total sample size (number of questions/steps) used to generate the diagnostic curves in Figure 3 (fig3.tex) to ensure the trend analysis is robust.
- **[ef3beb77b7fe] (severity: science)** Provide a more detailed compute budget comparison (FLOPs or wall-clock time) between AXPO's 25% resampling budget and the 2x rollout baseline in Table 2 to validate the efficiency claim.
- **[21d045e15d9f] (severity: science)** Report variance across multiple training seeds to validate statistical significance of AXPO vs GRPO improvements, as evaluation std alone is insufficient.
- **[85b5467c0d4d] (severity: science)** Address multiple-comparison issues across 9 benchmarks x 4 sizes x 2 metrics (72 tests) via correction or explicit discussion of false positive risk.
- **[9c5879259d6c] (severity: writing)** Report 95% confidence intervals for main Pass@1/4 results derived from training seeds, not just evaluation rollouts.
- **[09dfb905ecd8] (severity: writing)** Move the abstract inclusion (input{text/0_abstract}) inside the document environment, i.e., after begin{document} and before maketitle. This violates LaTeX structure and can cause compilation warnings.
- **[adfedecbd334] (severity: writing)** Remove duplicate package imports: amsmath, amssymb, amsthm and booktabs are each loaded twice. Consolidate them to a single usepackage line to avoid redundancy.
- **[10dd7442f438] (severity: writing)** Consolidate the two natbib loading commands (PassOptionsToPackage{numbers, compress}{natbib} and usepackage[numbers]{natbib}) into a single, correctly ordered usepackage statement.
- **[bc59ef89f254] (severity: writing)** Correct malformed vspace commands in figures (e.g., vspace{-0.in} should be vspace{-0in} or a valid length). Such syntax errors can lead to compilation errors or unexpected spacing.
- **[1bc16c325e7a] (severity: writing)** Ensure that all caption commands appear after the centering and before the label for consistency with common LaTeX practice, and verify that the label references match the figure/table numbers used in the text.
- **[8a4044fa7752] (severity: writing)** Standardize the placement of label commands: they should immediately follow the caption within each figure or table environment to guarantee correct cross-referencing.
- **[ec2a09bba9b2] (severity: writing)** Review the use of begin{table*}[t] versus begin{table}[t] for consistency; table* spans two columns in a two-column layout, but the document class appears to be single-column. Use table unless a full-width table is intended.
- **[b67d8a920a78] (severity: writing)** Check that all custom commands (e.g., toolresample, gap) are defined before first use; some appear in the text before their definitions in the preamble, which can cause undefined-command warnings.
- **[85b4a7aa5265] (severity: writing)** Verify that all autoref and custom reference macros (figref, secref, etc.) are used consistently and that the referenced labels exist. Inconsistent naming (e.g., Figref vs. figref) may lead to broken links.
- **[9f998e31a0b8] (severity: writing)** Consider adding a clearpage before the bibliography to ensure that floats (figures/tables) do not appear after the references, improving document flow.
- **[cbcdf417d1ec] (severity: writing)** Correct the grammatical error 'underperforms than' in Section 3.4 to 'underperforms' or 'performs worse than'.
- **[3cf8b11fa63c] (severity: writing)** Refine the Abstract sentence '8B with SFT+AXPO surpasses...' for smoother flow and clarity.
- **[1fbb14787e86] (severity: writing)** Break down complex sentences in Section 2 (Method) to improve readability of the advantage calculation logic.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 49 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
