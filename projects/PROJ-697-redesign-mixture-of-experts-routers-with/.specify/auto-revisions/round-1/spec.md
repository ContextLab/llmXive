# Revision Specification: Paper Science Revision — PROJ-697-redesign-mixture-of-experts-routers-with round 1

**Generated**: 2026-06-18T04:40:21.484112+00:00
**Kind**: paper_science
**Project**: PROJ-697-redesign-mixture-of-experts-routers-with
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[4b60d74b1fcc] (severity: writing)** Clarify the exact experimental setup for the power‑iteration step (e.g., number of iterations, choice of expert weight matrix) and provide a brief algorithm box summarizing the MPI update.
- **[6061942822bc] (severity: writing)** Add a more detailed discussion of training stability, including quantitative analysis of gradient norms or loss spikes when router retraction is omitted.
- **[8987d23bb487] (severity: writing)** Compare the proposed MPI router against at least one recent alternative router design (e.g., Switch Transformer, auxiliary‑loss‑free load balancing) to contextualize the performance gains.
- **[af5dd2e2f1a1] (severity: writing)** Provide a reproducibility checklist (hyperparameter table, random seed, code repository link) and ensure all cited references in the bibliography are marked as verified.
- **[ba2ac3b39cf4] (severity: writing)** Include an error analysis showing cases where MPI improves or harms routing decisions, possibly with visualizations of router‑expert alignment.
- **[3543fa53122d] (severity: writing)** Refactor the LaTeX source into modular files (e.g., separate sections, macros, bibliography) and include a build script (e.g., Makefile or latexmk) to ensure reproducible compilation.
- **[46a4204299b2] (severity: writing)** Provide a public code repository containing the actual implementation of the Manifold Power‑Iteration router (Python/PyTorch), with a clear `requirements.txt` or `environment.yml` specifying all dependencies.
- **[63659f62d267] (severity: writing)** Add unit tests for the core router logic (power iteration step, L2 retraction, scaling constant C) and integration tests that verify the model can be trained end‑to‑end on a small synthetic MoE toy problem.
- **[04fed478bf80] (severity: writing)** Fix typographical errors in the provided pseudo‑code (e.g., rename `foward` to `forward`, ensure the variable `wg` is defined or passed, and close the parentheses on the `R_hat` line).
- **[34faa9734080] (severity: writing)** Include a reproducibility checklist in the appendix that details random seed settings, hardware configuration, and exact hyperparameter values used for each experiment, referencing the files in `apx:details`.
- **[cbb784f858ea] (severity: writing)** Document the version of the underlying libraries (e.g., PyTorch, MegaBlocks, TorchTitan, FSDP) used in the experiments to avoid hidden dependency drift.
- **[98a79c4da319] (severity: writing)** Add an explicit licensing statement for the manuscript (e.g., CC‑BY 4.0) and for any third‑party code or data used.
- **[5ce76953d2b0] (severity: writing)** Provide precise version identifiers (e.g., dataset DOI, commit hash, or release tag) for all external resources such as FineWeb‑Edu, Olmo 3, and the MegaBlocks library.
- **[1316d4b86fd2] (severity: writing)** Archive all cited URLs (arXiv, HuggingFace, project pages) using a service like Internet Archive or Zenodo and include the archive links in the bibliography.
- **[f90625e274fd] (severity: writing)** If code is released, include a public repository URL with a specific commit hash or release tag, and specify the software license.
- **[e8465109e424] (severity: writing)** Document how missing or corrupted data (e.g., unavailable token streams) are handled during preprocessing; add a brief description in the Appendix.
- **[a773eb7a5b79] (severity: writing)** Add explicit axis labels (including units where applicable) to all loss and performance plots (e.g., Fig. 1, Fig. 2, Fig. 3, Fig. 4, Fig. 5).
- **[dfaba5d4f03f] (severity: writing)** Replace the default color scheme in the plots with a color‑blind‑friendly palette (e.g., use colorblind‑safe blues/oranges or patterns) and ensure that line styles are distinguishable when printed in grayscale.
- **[c80e9566197b] (severity: writing)** Provide concise alt‑text descriptions for each figure (including sub‑figures a/b) in the LaTeX source using the \caption[...]{...} optional argument or the \includegraphics[alt=...]{...} package option.
- **[bb259d2a792b] (severity: writing)** Increase the font size of tick labels and legends in the PDF figures to guarantee legibility at typical conference print scales (e.g., ≥9 pt).
- **[4ac8b3e0f518] (severity: writing)** For the code‑listing figure (Fig. 1), avoid colored background highlights (blue/pink) that may not reproduce well in print; use a neutral gray or no background, and ensure the listing remains readable in monochrome.
- **[ee11c8225ac3] (severity: writing)** Clarify in the captions which curve corresponds to which optimizer or model variant (e.g., in Fig. 2 and Fig. 3) either by adding a legend within the figure or by explicitly naming the curves in the caption.
- **[e44a68be869e] (severity: writing)** Ensure that all figures are referenced in the text before they appear and that the figure numbers match the order of appearance.
- **[0768e8fbe108] (severity: writing)** Define every acronym (e.g., MoE, MPI, L2) at its first occurrence and provide a brief plain‑English explanation.
- **[91de4c9ccff3] (severity: writing)** Replace or accompany highly technical terms such as “principal singular direction”, “Rayleigh quotient”, “manifold”, “retraction”, and “spectral norm” with simpler language or short explanatory footnotes.
- **[1bc678a3d471] (severity: writing)** Avoid dense symbol‑heavy sentences (e.g., Eq. (1) and Eq. (2) in Section 3) without accompanying intuitive description; add a sentence that describes what the equation is doing in everyday terms.
- **[c03b65ca3c5c] (severity: writing)** Remove or clarify internal code‑style comments like “(*\\bluebg*)” and “(*\\pinkbg*)” in Figure 1’s listing; they add visual noise for non‑technical readers.
- **[b35c4b117fbe] (severity: writing)** Introduce a short glossary or inline parenthetical definitions for mathematical objects (e.g., \( \mathbf{R}_{[i]} \), \( \mathbf{W}_g^i \), \( \mathbf{M} \)) the first time they appear.
- **[5a8faefcc36c] (severity: writing)** Simplify the description of the “Power‑then‑Retract” paradigm by stating the intuition (e.g., “first we nudge the router toward the expert’s most important direction, then we scale it back to keep it stable”) before the formal equations.
- **[8b10079147f2] (severity: writing)** In the abstract and introduction, replace buzz‑word phrases like “cornerstone component”, “principal singular direction”, and “expressive mathematical description” with clearer phrasing (e.g., “key part”, “most important direction”, “compact summary”).
- **[3cc4a76ddb0f] (severity: science)** Clarify the underlying assumption that token vectors are well‑aligned with the subspace spanned by expert weight matrices; provide empirical or theoretical justification that maximizing the Rayleigh quotient of RᵢWᵢ indeed leads to higher token‑expert affinity.
- **[6d50f56dde3a] (severity: writing)** Explicitly discuss how the retraction step (norm normalization) may affect the load‑balancing loss, and separate its impact from genuine improvements in routing balance to avoid conflating two effects.
- **[5b70c609a9cc] (severity: writing)** Re‑examine the claim that a single power‑iteration step per training update is sufficient for convergence toward the principal singular direction; either provide a convergence bound or qualify the claim as an empirical observation.
- **[b462b134085a] (severity: science)** The manuscript presents an informal argument that the power‑then‑retract update drives router rows toward the principal singular direction (Section 3.2). However, no rigorous convergence proof or quantitative analysis of the rate of alignment is provided. Add a formal theorem (or clearly state the assumptions) and empirical metrics (e.g., alignment error over training steps) to substantiate this claim.
- **[ebff08ff754e] (severity: writing)** Claims that MPI “consistently facilitates faster convergence, superior downstream performance, and improved load balancing” are based on a limited set of experiments (up to 11 B parameters, specific token counts, and a single downstream benchmark suite). The paper should temper these statements or broaden the evaluation to include more model sizes, datasets, and alternative baselines.
- **[a7fdce13db9b] (severity: writing)** The statement that the method incurs “zero inference overhead” overlooks the need to run a power‑iteration pass on the router weights at model load time, which can be non‑trivial for very large expert counts. Clarify the actual cost and any potential latency impact.
- **[07b658293a28] (severity: science)** Section 5.2 claims compatibility with other router designs (e.g., auxiliary losses, sigmoid activation) based on a handful of small‑scale experiments. Provide systematic ablations across multiple activation functions, loss terms, and optimizer settings, or qualify the claim as preliminary.
- **[43c8232acc2d] (severity: writing)** The paper repeatedly describes MPI as a “principled” and “fundamental” redesign, yet the empirical gains are modest (≈0.01–0.02 % loss reduction, a few percentage points on downstream tasks). Discuss the practical significance of these improvements and potential trade‑offs (e.g., added complexity, stability issues noted in the ablations).
- **[666c7ff6babe] (severity: science)** The theoretical section (Eq. 10) derives an approximation for the update but does not quantify the approximation error or its impact on training stability. Include an error analysis or empirical verification of the approximation’s validity.
- **[dc7df79e603d] (severity: science)** Add an explicit discussion of potential dual‑use risks associated with more efficient Mixture‑of‑Experts models, including how the proposed router redesign could enable larger or more capable language models and the downstream societal implications.
- **[7a8ca99433e4] (severity: writing)** Include a brief ethical considerations section that addresses data privacy (if any data is used), the need for responsible deployment, and any foreseeable misuse of the technology.
- **[062e962b2a3e] (severity: writing)** Verify that the training data (FineWeb‑Edu, etc.) complies with appropriate usage licenses and contains no personally identifiable information; if necessary, provide a statement confirming compliance.
- **[ca36480658e5] (severity: science)** Run each experimental configuration (e.g., 1B, 3B, 11B scales with different optimizers) with at least three independent random seeds and report mean ± standard deviation for pre‑training loss, perplexity, and downstream accuracy. This will allow assessment of variance and statistical significance of the reported gains.
- **[b954add1d601] (severity: science)** Add statistical tests (e.g., paired t‑tests or bootstrap confidence intervals) when comparing MoE with and without MPI on downstream benchmarks. Include effect‑size metrics (Cohen’s d or relative improvement %) to quantify the practical relevance of the observed differences.
- **[d29d9ee45943] (severity: science)** Report variance (e.g., standard deviation or confidence intervals) for all aggregate metrics (pre‑training loss reductions, downstream accuracy averages, perplexity) and perform statistical significance testing (e.g., paired t‑tests or bootstrap) to substantiate the claimed improvements.
- **[a4e4881f974c] (severity: science)** Specify the number of random seeds / training runs used for each experimental configuration and provide the seed values or a reproducibility statement.
- **[342e7fc7ff8f] (severity: science)** Address multiple‑comparison issues when evaluating across 25 downstream benchmarks; consider correcting p‑values (e.g., Bonferroni or Holm) or reporting per‑task significance.
- **[6f69fa3ef8d0] (severity: science)** Include details on how the load‑balancing metrics (MaxVio) were computed (e.g., batch size, number of evaluation steps) and report their variability.
- **[3aa51b1845c5] (severity: science)** Provide the exact hyperparameter values for the constant C (including C′) used in the large‑scale experiments and any sensitivity analysis results, to enable independent replication.
- **[4e0e5c8c9934] (severity: writing)** Figure 2 (and similar) embed a table inside a figure environment and use \captionof{table}. Move the tabular to a proper \begin{table}…\end{table} environment and place the caption with \caption{}.
- **[e2b469b39bfa] (severity: writing)** The preamble loads tcolorbox twice (line 19 and line 84). Remove the duplicate \usepackage{tcolorbox} to avoid unnecessary package loading.
- **[84d71ac0fb2d] (severity: writing)** In the pseudo‑code listing, the method name is misspelled as `foward`. Correct it to `forward` to maintain professionalism and avoid confusion.
- **[6f3587771bb7] (severity: writing)** Citation commands are mixed (e.g., \citealp, \citep) while the bibliography style is plainnat. Standardise on a single citation macro (e.g., \citep) to keep citation style consistent throughout.
- **[ad77847d765d] (severity: writing)** Long lines in several paragraphs (e.g., the motivation paragraph in Section 3.1) exceed typical 80‑character width, which can cause overfull hboxes. Insert line breaks or re‑phrase to improve LaTeX line‑wrapping.
- **[a04e097c6312] (severity: writing)** Some figures use the optional position specifier `[t]` without accompanying \centering, leading to uneven vertical spacing. Add \centering inside the figure environment for consistent layout.
- **[a1d004a881dd] (severity: writing)** The macro definitions for \bluebg and \pinkbg include comments in Chinese and hard‑coded horizontal offsets (‑3.2em). Consider abstracting these values into a length macro for easier maintenance.
- **[5cad96b126f4] (severity: writing)** Duplicate definition of \eqref macro (both as a command and as a provided shim) can cause unexpected behaviour. Keep a single definition to ensure reliable cross‑references.
- **[52af49df9d2f] (severity: writing)** Clarify the motivation paragraph in Section 1 (lines 31‑45). The current prose mixes several ideas without clear transitions, making it hard for readers to follow why router‑expert alignment is a problem.
- **[9acea5359522] (severity: writing)** Standardize terminology for the proposed method. The paper alternates between “Manifold Power‑Iteration”, “Power‑then‑Retract”, and “MPI” (e.g., lines 61‑70, 124‑130). Choose one term and use it consistently.
- **[5a9fec2ceb45] (severity: writing)** Fix numerous grammatical errors and missing articles (e.g., “Router is the cornerstone component” → “The router is the cornerstone component” in the abstract, line 2).
- **[63b6b1044345] (severity: writing)** Improve figure and table captions for self‑containment. Captions such as Figure 1’s lack a description of what the plotted curves represent (lines 159‑165).
- **[5dfb2b4b12ba] (severity: writing)** Re‑write overly long sentences that hinder readability, especially in Section 3.1 (lines 203‑218) where a single sentence spans >80 words.
- **[5f0b309c9c94] (severity: writing)** Add explicit paragraph breaks to separate distinct ideas in the “Methodology” section. Currently, several paragraphs contain multiple unrelated points, reducing cohesion.
- **[be9b4e37d629] (severity: writing)** Correct inconsistent use of LaTeX commands for math notation (e.g., missing backslashes before “texttt” in equations on lines 88‑92).
- **[22ed862b0009] (severity: writing)** Provide a concise summary of contributions at the end of the Introduction (lines 101‑115). The current list is scattered and repeats earlier points.
- **[22fde68c37f8] (severity: writing)** Remove duplicated or placeholder comments (e.g., “% …” lines in the source) that appear in the compiled PDF, as they distract the reader.
- **[910c582873c9] (severity: writing)** Ensure all abbreviations are defined on first use (e.g., “LMO” appears without definition in the abstract).


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 67 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
