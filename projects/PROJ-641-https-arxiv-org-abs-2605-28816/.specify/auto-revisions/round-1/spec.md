# Revision Specification: Paper Science Revision — PROJ-641-https-arxiv-org-abs-2605-28816 round 1

**Generated**: 2026-06-14T07:52:48.092659+00:00
**Kind**: paper_science
**Project**: PROJ-641-https-arxiv-org-abs-2605-28816
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[5a4eab7f8201] (severity: science)** Provide quantitative inference benchmarks (latency/FPS) on specified hardware to support the '24 FPS' claim asserted in Abstract and Intro.
- **[0e0026040b9a] (severity: writing)** Verify that citation 'ali2025world-simulation' explicitly supports the specific model name 'Cosmos-Predict2.5-2B' or adjust text to clarify derivation.
- **[76fba0ee109b] (severity: science)** Ensure the architectural description of Solaris (dense joint attention, learned ID embedding) matches the cited source to validate baseline comparison.
- **[7f843ed28f9c] (severity: science)** No code repository or artifact included with the submission. Reviewers cannot evaluate modularity, test coverage, or dependency hygiene without access to the implementation codebase.
- **[4748ef0b9b2e] (severity: science)** Appendix contains implementation details but no version control information (commit hashes, release tags) or Docker/conda environment specifications for reproducibility.
- **[d3a0b9d123b7] (severity: science)** Training stages mention specific hardware (GB200s) but no inference code or checkpoint availability is documented beyond the project page link.
- **[ca45d2b15687] (severity: writing)** Specify data licenses for the RealOmin-Open Dataset and the generated Minecraft trajectories to ensure legal compliance and reproducibility.
- **[b3fb1da91c71] (severity: writing)** Add URLs to dataset citations in main.bib (e.g., genrobot2025opendata) to prevent link rot and enable verification.
- **[e3db51e9732c] (severity: science)** Document data preprocessing steps, specifically synchronization verification and missing-data handling, in the experiments section.
- **[409421f71899] (severity: writing)** Add explicit alt text to all \includegraphics commands for accessibility compliance.
- **[621926d8d305] (severity: writing)** Ensure axis labels in fig:sparse-hub-efficiency explicitly state units (ms, GFLOPs).
- **[c79dd5cee012] (severity: writing)** Improve captions for qualitative figures (fig:qualitative-two-agent, fig:qualitative-scaling) to describe specific visual evidence of agent interaction rather than generic task lists.
- **[efcd305c67bd] (severity: writing)** Define acronyms like RoPE, KV, and DiT at first use in Abstract/Intro.
- **[b7e9cfcd48dc] (severity: writing)** Expand AdaLN, LoRA, and TI2V definitions in Appendix.
- **[0f514ec8ddae] (severity: writing)** Replace 'isometry' with 'distance-preserving mapping' for accessibility.
- **[705e2f7bafb8] (severity: writing)** Clarify hardware specifications for the '24 FPS' inference claim in Abstract and Intro to avoid misleading 'real-time' assertions.
- **[b6450253ae98] (severity: science)** Provide quantitative metrics (FVD/FID) for the 4-player zero-shot generalization to support the core scalability claim.
- **[f61560a8c00a] (severity: science)** Qualify the robotics application claim as qualitative demonstration, as no quantitative metrics are provided for the real-world task.
- **[4fae8e1e1b5c] (severity: writing)** Add a dedicated 'Safety and Ethics' or 'Broader Impact' section discussing dual-use risks of generative world models, including potential misuse for misinformation or autonomous agent training.
- **[a2ec39072130] (severity: writing)** Clarify data provenance and compliance for the RealOmin-Open Dataset, including confirmation of appropriate licensing and consent for any human-recorded robotic data used.
- **[3fd8aff3ed02] (severity: science)** Quantitative results lack statistical rigor: report standard deviations or confidence intervals across multiple random seeds for all FVD/FID metrics in Tables 1-2 and ablation tables.
- **[d9cd661e1dc5] (severity: science)** Sample size for evaluation not specified: state number of test episodes, unique trajectories, and total frames used for quantitative metrics. Training dataset size (unique trajectories) also missing.
- **[64cae3cd72e1] (severity: science)** 4-player generalization claim lacks quantitative validation: Table 1 only shows 2-player results; provide FVD/FID metrics for 4-player zero-shot transfer to support scaling claims.
- **[b16f16b9379a] (severity: writing)** Multiple hypothesis testing not addressed: 5 metrics reported in Tables 1-2 with selective bolding; justify whether corrections for multiple comparisons were applied.
- **[3f80588e70bf] (severity: writing)** 24 FPS real-time claim needs verification: specify hardware used, whether this is per-agent or aggregate throughput, and whether it includes action encoding overhead.
- **[9d0b2f9ad046] (severity: science)** Report standard deviations across multiple random seeds for all FVD, FID, and LPIPS metrics in Tables 1, 2, and 4. Perform significance testing for comparative claims.
- **[75e66f4e01a4] (severity: writing)** Standardize table definitions to a single directory (e.g., tables/) or inline style to ensure consistency between appendix and main text.
- **[89570e95d764] (severity: writing)** Remove all commented-out spacing commands (e.g., % \\vspace) from the source code to reduce clutter before submission.
- **[69a858d38234] (severity: writing)** Unify cross-reference commands to use \\cref from cleveref consistently instead of manual \\S\\ref where configured.
- **[6a6d6b61c359] (severity: writing)** Verify that the nvidiatechreport class loads fancyhdr, or explicitly load \\usepackage{fancyhdr} in main.tex to prevent compilation errors.
- **[75ab7bf0ec05] (severity: writing)** Remove commented-out code blocks throughout the manuscript (e.g., lines with % space{-3mm} in intro.tex, appendix.tex, and the commented project page URL in main.tex) to improve code cleanliness and reduce visual clutter.
- **[9bee546cf360] (severity: writing)** Standardize figure and table reference capitalization - use 'Figure' consistently instead of mixing 'figure' and 'Figure' throughout the document (e.g., 'figure~ef{fig:method}' in method.tex should be 'Figure~ef{fig:method}').
- **[c639df3dcedb] (severity: writing)** Break up several overly long sentences in the introduction (lines 15-25) and method sections to improve readability and reduce cognitive load for readers.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 33 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
