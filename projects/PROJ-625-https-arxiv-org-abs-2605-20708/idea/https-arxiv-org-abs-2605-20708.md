---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/230
---

# https://arxiv.org/abs/2605.20708

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.20708

Submitted by: github-actions[bot]

(Intake from human-submission issue #230.)

## Rejection rationale (2026-06-24)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[aa7cbdb51714]** The submission does not include any source code, training scripts, or a reproducibility package; provide a public repository with the full implementation (model definition, data pipeline, training loop, evaluation scripts).
- **[275b0f6c9633]** Add a clear `README` that lists all required dependencies (exact package versions, CUDA/cuDNN requirements) and step‑by‑step instructions to reproduce the ImageNet experiments.
- **[031dbafca540]** Modularize the implementation: separate model architecture, routing module (DAR), and utility functions into distinct Python modules or packages rather than a single monolithic script.
- **[2650e7629bb0]** Include unit and integration tests for the core components (e.g., DAR attention routing, chunked aggregation, RMSNorm) to ensure correctness and guard against regressions.
- **[a3fce83c8679]** Provide a `setup.py`/`pyproject.toml` or `requirements.txt` with pinned versions to guarantee dependency hygiene across environments.
- **[2b6803ef031a]** Document the custom Triton kernels (fusion implementation) with comments, type hints, and a small benchmark script to verify performance claims.
- **[a634e6a669e8]** If the code relies on external data (ImageNet), include scripts to download, preprocess, and verify the dataset checksum.
- **[7dbeaaa11bd1]** Add a clear data availability and licensing statement for ImageNet, including the exact version (e.g., ImageNet‑1K 2023 release) and the permissive or restrictive license under which the data is used.
- **[ce98912f6bf6]** Provide persistent, archived URLs (e.g., Zenodo or Internet Archive) for any external resources referenced in the paper (e.g., code repositories, pretrained checkpoints, or third‑party datasets) to mitigate link rot.
- **[9b8597adfae6]** Document the full preprocessing pipeline (e.g., resizing, normalization, augmentation) and the schema of the input tensors (shape, datatype, range) so that future reproductions can verify data handling.
- **[ed03f820c7e4]** Include checksums (e.g., SHA‑256) for the exact dataset files used during training to enable verification of data integrity.
- **[08b15557cff3]** If any custom data splits or subsets are employed (e.g., validation split for early‑stop experiments), describe how they were generated and provide the split files or a deterministic script.
- **[1465eb7dbe4a]** Add descriptive alt‑text for every figure (e.g., “Figure 3 shows three diagnostic plots of forward magnitude, gradient magnitude, and cosine similarity versus transformer block index”) to improve accessibility and comply with publication standards.
- **[8754addcf9f5]** Ensure all plots include clear axis labels with units where appropriate (e.g., training‑iteration count (K) on the x‑axis and FID (lower‑better) on the y‑axis in Figure 2; timesteps on the x‑axis and source‑mixing importance on the y‑axis in Figure 4).
- **[f2f4905bef53]** Add colorbars or legends to heat‑map style figures (Figures 4 and 7) that explain the meaning of the color scale (e.g., importance weight, speedup factor, memory‑saving percentage).
- **[f5aa7c9571db]** Check that line styles, markers, and text remain legible when the figures are printed at typical conference column width (≈3.25 in). Increase line thickness or marker size if necessary.
- **[769469df3689]** For multi‑panel figures (e.g., Figure 1 and Figure 2), provide sub‑figure labels (a), (b), … in the caption and ensure each sub‑figure is referenced correctly in the main text.
- **[c732393cfd9e]** Verify that any quantitative axes (e.g., latency speedup in Figure 7 left) include the scale (e.g., “× speedup”) and that the range of values is appropriate for the plotted data.
- **[7315566455b8]** Define every acronym (e.g., DiT, DAR, REPA, SiT, U‑ViT, CFG, ODE, SDE) at its first occurrence; add a concise glossary for readers unfamiliar with diffusion‑model terminology.
- **[88b9b5e4600e]** Replace overloaded technical jargon such as “PreNorm dilution”, “timestep‑adaptive”, “non‑incremental aggregation”, and “vertical attention” with clearer, plain‑English explanations or brief parenthetical definitions.
- **[9c8f31603191]** Simplify long, dense sentences (e.g., the abstract and Section 1) by breaking them into shorter statements and avoiding excessive nominalizations.
- **[9e235f23cd9e]** Introduce a brief, non‑technical overview of diffusion models and Transformers for readers outside the sub‑field, possibly as a “Background” paragraph before the related‑work section.
- **[637bd466a832]** Ensure that symbols like $t$, $L$, $S$, and $N$ are explicitly described in the surrounding text when first used, rather than assuming the reader knows their meaning.
- **[b292a44b4295]** Provide a direct causal analysis linking the reduction of each diagnosed symptom (forward magnitude inflation, backward gradient decay, block-wise redundancy) to the observed performance gains (FID/IS). For example, include ablations where only one symptom is mitigated to isolate its impact.
- **[aa9c051ccfd4]** Clarify the apparent contradiction between the claim that standard residuals cannot adaptively weight earlier layers and the counterfactual gate experiment (Fig. 5) which shows timestep‑dependent source importance even without an explicit router.
- **[45711407249a]** Re‑evaluate the claim that the dynamic query variant is superior to the static variant with explicit timestep injection; the current ablation (Table 4) shows comparable or better performance for the static‑with‑t‑injection model.
- **[2fefb69eadcb]** Report quantitative measurements of how DAR affects the forward hidden‑state magnitude and gradient magnitude across depth, to substantiate the argument that DAR alleviates PreNorm dilution.
- **[427300163bee]** In the chunk‑size analysis, explicitly state the assumed values of the hyper‑parameter α used in Eq. (9) and verify that the predicted S* aligns with the empirical optimum for the exact α chosen.
- **[d1a727e458f8]** The manuscript claims to be the first systematic study of cross‑layer information flow in Diffusion Transformers. Provide a more precise literature context and acknowledge closely related works (e.g., U‑Net‑like skip routing studies) to avoid overstating novelty.
- **[7607f1ad00e4]** The statement that DAR is a “drop‑in residual replacement” is not fully supported, as it introduces additional parameters, chunking logic, and a new attention mechanism. Clarify the exact changes required to integrate DAR into existing DiT codebases.
- **[00b35f4e17a9]** The claim of orthogonality between DAR and REPA is based on limited experiments. Include a more thorough analysis (e.g., ablation of combined loss terms, statistical significance testing) to substantiate that the improvements truly compound rather than overlap.
- **[053751ad429c]** Performance gains are reported without detailed hyper‑parameter tuning for the baselines. Ensure that baseline SiT/DiT models are optimally tuned (learning rate schedules, regularization) to rule out that DAR’s advantage stems from unequal training settings.
- **[1f333e499b77]** The paper asserts that DAR “preserves the isotropic and homogeneous Transformer stack,” yet the depth‑wise attention fundamentally alters the routing topology. Discuss any potential impact on model scaling properties and compatibility with future architectural extensions.
- **[f48bf3b7e199]** Provide quantitative evidence that the timestep‑aware routing variants (static + t‑injection, dynamic) are indeed necessary; the current ablation (Table 5) shows modest differences. Include statistical variance or confidence intervals to demonstrate significance.
- **[2ed218d350ae]** The theoretical Proposition 1 about chunk size optimality is based on a simplified cost model. Validate the model empirically across a broader range of depths (e.g., deeper DiTs) to confirm that the predicted S* aligns with observed performance.
- **[c94de2f9fc55]** Add a brief discussion of the dual‑use risks of diffusion transformers (e.g., generation of disinformation, deepfakes) and outline recommended mitigation strategies or responsible‑use guidelines.
- **[6b60face5dce]** Disclose any potential conflicts of interest, such as affiliations with commercial entities that may benefit from the proposed architecture.
- **[91310bbb0b6b]** Report variance or confidence intervals (e.g., standard deviation over multiple random seeds) for all quantitative metrics such as FID, sFID, IS, precision, and recall. This will allow assessment of statistical significance of the reported improvements.
- **[46c8f2d7d748]** Provide explicit details on random seed handling, number of independent training runs, and any hyper‑parameter search performed for both the baseline and DAR variants. This is essential for reproducibility.
- **[589f3bfc685d]** Extend the experimental evaluation beyond ImageNet‑1K (e.g., CIFAR‑10/100, LSUN, or a downstream text‑to‑image benchmark) to demonstrate that the observed benefits of DAR generalize across datasets and modalities.
- **[f646996aff40]** Report statistical variability (e.g., standard deviations or confidence intervals) for all quantitative metrics (FID, IS, sFID, precision, recall) across multiple random seeds or repeated runs.
- **[0cfd9e29190f]** Provide details on random seed initialization and any stochastic components of training/evaluation to enable exact reproducibility.
- **[aac8f60f2353]** When performing multiple ablations (e.g., static vs. dynamic query, chunk sizes, timestep‑injection variants), apply appropriate multiple‑comparison corrections or clearly state that each comparison is independent.
- **[05eb77903984]** Include a brief statistical justification for the number of samples (50 k) used for evaluation and discuss whether this sample size yields stable estimates of the reported metrics.
- **[b5d41d143c18]** Duplicate macro definitions (`\best` and `\second`) appear twice in the preamble (lines ~140 and ~380). Use `\renewcommand` or remove the second definitions to avoid LaTeX warnings.
- **[892f0fb56857]** Figures are created with a `center` environment and `\captionsetup{type=figure}` instead of a proper `figure` environment (e.g., the abstract‑overview figure around lines 70‑95). Replace with a standard `\begin{figure}[t] ... \end{figure}` to ensure correct float handling and caption placement.
- **[c48de3d9ea85]** Negative vertical spacing (`\vspace{-...}`) is used extensively before sections and inside figures (e.g., lines 55, 115, 210). Review these adjustments; excessive negative spacing can cause overfull boxes and layout instability.
- **[6768e130c8b1]** The `wrapfigure` and `wraptable` environments are used without accompanying `\clearpage` or `\FloatBarrier` to control float placement, which may lead to unexpected layout shifts in the final PDF. Consider adding `\FloatBarrier` (from `placeins`) after each wrapped element.
- **[75b198efd165]** Citation style mixes `\citep` (natbib) with `\citet` in some places, but the bibliography style is `plainnat`. Ensure consistent citation commands throughout for uniform formatting.
- **[bc0d63b13b96]** Several sentences are overly long and contain multiple clauses, which hampers readability. Break them into shorter, clearer sentences (e.g., the first sentence of the Introduction spans three ideas).
- **[57302e9683c1]** Inconsistent use of punctuation in figure captions (e.g., missing periods, mixed use of commas and semicolons). Standardize caption style for uniformity.
- **[55b5a9919cdc]** The abstract repeats the same claim twice (“improves SiT‑XL/2 by 2.11 FID … and matches the baseline’s converged quality …”), which is redundant. Remove the duplication for conciseness.
- **[e629a316ce14]** There are occasional grammatical slips, such as missing articles (“the denoising timestep — the very dimension that distinguishes DiTs from a standard Transformer — should play a vital role”) and mismatched verb tenses. Proofread for article usage and tense consistency.
- **[4ddb43376dbf]** The transition between sections sometimes lacks a clear connective phrase (e.g., moving from the diagnostic results to the proposed method). Add brief bridging sentences to improve flow.
- **[346ca799f467]** The notation for equations is sometimes inconsistent (e.g., mixing inline math with displayed equations without proper punctuation). Ensure each displayed equation is introduced and referenced in the surrounding text.
- **[a839f98d92b5]** Some abbreviations are introduced without prior definition (e.g., “DMD” in the figure caption). Define all acronyms at first use.
- **[377280c21b4d]** The bibliography includes several entries with missing fields (e.g., missing year for some arXiv preprints). Complete the citation details for a professional reference list.
