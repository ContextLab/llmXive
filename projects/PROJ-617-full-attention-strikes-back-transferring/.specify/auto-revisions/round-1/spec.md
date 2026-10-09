# Revision Specification: Paper Science Revision — PROJ-617-full-attention-strikes-back-transferring round 1

**Generated**: 2026-06-13T07:32:10.718932+00:00
**Kind**: paper_science
**Project**: PROJ-617-full-attention-strikes-back-transferring
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[1bd59129dd76] (severity: writing)** Remove all visible author comments (e.g., \\yy{}, \\zyk{}, \\hs{}) and commented-out text blocks from the LaTeX source files to ensure a clean final manuscript.
- **[31b47deb324b] (severity: writing)** Verify and remove any active \\TBD or \\PLH macros; ensure all figure captions and references are finalized and consistent with the bibliography.
- **[9247af8c56d9] (severity: writing)** Confirm that the proofreader pipeline has been run and all proofreader flags are cleared before final compilation.
- **[ad3a420becd3] (severity: writing)** Add missing citation entry 'zucchet2026the' to references.bib; it is cited in src/intro.tex (Line 13) but absent from the bibliography.
- **[63205323b0c4] (severity: science)** Verify experimental software versions (Python 3.14, CUDA 12.8, PyTorch 2.8) in src/exp.tex (Line 3) as they appear inconsistent with the arXiv submission date (May 2026) and release schedules.
- **[29565ca2126a] (severity: writing)** Confirm 'DeepSeek Sparse Attention' (src/intro.tex, Line 10) is accurately described in the 'DeepSeek-V3.2' bib entry (dsa); if not, replace with a specific technical report on sparse attention.
- **[aa92c84041dd] (severity: writing)** Code artifacts (implementation, tests, kernels) are not accessible for this arXiv-ingested paper. A code quality review requires access to the actual implementation repository with source code, test suites, and reproducibility scripts.
- **[f2256132d5dd] (severity: writing)** The paper describes custom GPU kernels (Section 4.4) but no kernel source code is provided. For reproducibility, include CUDA kernel implementations in a public repository with build instructions.
- **[5d43e78862e4] (severity: writing)** Training pipeline code (two-stage training in Section 4.3) is referenced but not accessible. Provide training scripts with hyperparameters to enable independent verification.
- **[a2679d630e4d] (severity: writing)** Add license information for FineWeb and Dolma 3 Longmimo Mix training datasets (Section 5.1, Appendix D.3)
- **[d671ac362bc4] (severity: writing)** Include version numbers for benchmark datasets (LongBench, RULER, MMLU-PRO) to ensure reproducibility
- **[18f569aca9a0] (severity: writing)** Provide data card or datasheet link for the 8K-sample calibration sequence construction
- **[0d35c8f706b5] (severity: writing)** Verify all external arXiv links (e.g., qwen3, fineweb) and add DOIs where available to mitigate link rot
- **[7ecd24cecaa3] (severity: writing)** Figure captions are too minimal. fig:overall caption 'A teaser view...' lacks quantitative context. Add specific speedup values, context lengths, and accuracy metrics to captions for standalone interpretability.
- **[3aa283414867] (severity: writing)** Figure fig:query_dependent_patterns (lines 251-264) has author comment 'the font is too small; the figure not easy to interpret'. This must be resolved before submission. Verify legibility at print scale (10pt minimum for axis labels).
- **[d48f1fb3e794] (severity: writing)** No axis labels visible in figure source code review. Figures like fig:multi_benchmark, fig:sparse_decode_speedup, and training loss curves (fig:stage1_indexer_loss, fig:stage2_end2end_loss) must explicitly label axes with units (e.g., 'Context Length (tokens)', 'Sparsity (%)', 'Training Steps').
- **[8fd27984c9c3] (severity: writing)** Color choices in multi-figure comparisons (Table~\ref{tab:longbench}, Table~\ref{tab:ruler} with SOTA markers) use \SOTA macro but figure color palettes (L0-L17) are not consistently documented. Ensure colorblind-safe palettes and provide legend for all color-coded elements.
- **[89287d56d378] (severity: writing)** Figure fig:architecture (line 334) caption 'Overall architecture of RTPurbo' is non-descriptive. Caption should explain key components shown (retrieval heads, local heads, low-dim projector, top-p selector) for readers who skim figures without reading method section.
- **[d04f8a5b2a75] (severity: writing)** Define 'KV cache' as 'Key-Value cache' at first use in Abstract and Introduction.
- **[3db07526d5ad] (severity: writing)** Expand 'RoPE' to 'Rotary Positional Embeddings' before first use in Section 2.2.
- **[3adceb5ab7e6] (severity: writing)** Define 'MQA' and 'GQA' (Multi-Query/Grouped-Query Attention) in Section 4.2.
- **[6103099f4cf2] (severity: writing)** Define 'NIAH' as 'Needle-In-A-Haystack' before use in Figure captions and Tables.
- **[78b7aecae631] (severity: writing)** Replace 'SOTA' macro with 'state-of-the-art' text in tables for clarity.
- **[f31328d76bb2] (severity: writing)** Clarify 'attention sinks' in Section 4.1 or cite the specific mechanism briefly.
- **[1aab17862e86] (severity: writing)** Clarify in the Abstract that the 9.36x prefill speedup refers to a single attention layer, not end-to-end inference, to avoid overgeneralizing micro-benchmark results.
- **[38e85be18947] (severity: writing)** Softening the 'first method' novelty claim in the Introduction to 'to our knowledge' or similar phrasing to align with the evidentiary scope of the baseline comparison.
- **[995effdaed33] (severity: writing)** Adjust the Abstract's claim that 'full-attention LLMs are already intrinsically sparse' to specify that this is observed in the Qwen3 family tested, acknowledging the limitation in the main text.
- **[d452711b3100] (severity: writing)** Add a dedicated discussion of dual‑use risks and mitigation strategies, especially how the reduced computational cost may lower barriers for malicious deployment of long‑context LLMs.
- **[b6c6aab2b2a9] (severity: writing)** Include an explicit ethical statement covering data provenance, licensing, and consent for the FineWeb and Dolma 3 Longmimo Mix corpora used in training (see Section 5, lines 115‑130).
- **[157658ef6c64] (severity: science)** Provide a brief safety evaluation (e.g., alignment checks, content filtering) of the sparsified model to demonstrate that efficiency gains do not compromise established safety mitigations.
- **[68b127989ab8] (severity: writing)** Disclose any potential conflicts of interest beyond the author affiliations, such as commercial interests in Alibaba’s deployment of the method.
- **[cc6deb623347] (severity: writing)** Clarify that no human subjects were involved, confirming that IRB/IACUC approval is not required, and reference the relevant institutional review statement.
- **[4bdb92f3bdf9] (severity: science)** Evaluate on additional model architectures (e.g., LLaMA, Mistral) beyond Qwen3 variants to validate the claim that 'full-attention LLMs are intrinsically sparse' is generalizable.
- **[70a8d7929a1a] (severity: science)** Include trainable sparse attention baselines (DSA, NSA) for fair comparison; current baselines are mostly training-free, making it unclear if gains come from sparsification or additional training.
- **[52a47142aa4a] (severity: science)** Report multiple evaluation runs with confidence intervals on benchmark results (LongBench, RULER, AIME) to assess statistical significance of reported improvements.
- **[c4f0d741ce71] (severity: writing)** Clarify speedup measurement methodology: specify hardware configuration, batch size, and whether 9.36× prefill speedup is layer-level or end-to-end inference.
- **[03dc34245075] (severity: science)** Provide statistical analysis on head calibration stability across multiple documents; appendix shows one heatmap but claims calibration on 'one single sequence' is sufficient.
- **[4e9fd141cbb4] (severity: science)** No statistical significance tests reported for benchmark comparisons. Tables show point estimates only (e.g., LongBench Avg 54.24% vs 53.80% Full Attn) without p-values or confidence intervals. Add paired t-tests or bootstrap CIs across benchmark samples.
- **[d94c53874492] (severity: science)** Multiple comparisons problem unaddressed. Paper reports results across 16 LongBench sub-benchmarks, 9 RULER tasks, and 9 reasoning benchmarks without correction (Bonferroni/FDR). Claim of 'near-lossless accuracy' is statistically unsupported.
- **[9d1e72b5ee65] (severity: science)** Speedup measurements (9.36x, 2.01x) reported as single point estimates with no variance, standard deviation, or confidence intervals. Hardware benchmarking requires repeated measurements for statistical validity.
- **[97c39903cdc3] (severity: science)** Head calibration stability claim ('one single long text sequence is sufficient', Section 3.1) lacks statistical evidence. No variance analysis across documents or power analysis justifying single-sequence sufficiency.
- **[a0ac75071d29] (severity: science)** Training reproducibility incomplete. No random seeds reported, no variance across multiple training runs, and no justification for 600 steps/1.2M label tokens via power analysis. Appendix D provides hyperparameters but not reproducibility guarantees.
- **[7577380d1c90] (severity: writing)** The preamble of main-llmxive.tex is missing the booktabs package, but the included table files use \toprule, \midrule, \bottomrule which require it. Add \usepackage{booktabs} to the preamble.
- **[8f76a8a201c0] (severity: writing)** The command \rtpblue is defined as a color but used as a macro in \beginappendix. Change to \textcolor{rtpblue}{Appendix} to avoid LaTeX errors.
- **[8665d044ec7a] (severity: writing)** Remove the commented-out duplicate table block for tab:topk_topp_inline found around line 370 in main-llmxive.tex, as the active version exists around line 400.
- **[29dfa303b6cd] (severity: writing)** The custom command \titlefont used in \beginappendix is not defined in the provided preamble. Ensure it is defined in llmxive.cls or replace with a standard font command.
- **[a07c596ff751] (severity: writing)** Correct the title grammar from 'within Hundred Training Steps' to 'within a Few Hundred Training Steps'.
- **[60701a7b5705] (severity: writing)** Remove all commented-out author notes and TODOs (e.g., % \yy{...}, % \zyk{...}) from the LaTeX source.
- **[34b149a3161a] (severity: writing)** Fix the LaTeX typo in src/exp.tex: replace '($$0.93)' with a valid textual description or value.
- **[32f8dee258be] (severity: writing)** Verify the accuracy of software versions listed in Section 4 (e.g., Python 3.14, PyTorch 2.8) as they appear to be placeholders.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 50 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
