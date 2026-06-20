---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/274
---

# https://arxiv.org/abs/2606.03458

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.03458

Submitted by: github-actions[bot]

(Intake from human-submission issue #274.)

## Rejection rationale (2026-06-20)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[55b4a855dc84]** Add a complete bibliography with entries for every citation used (e.g., openai2024learning, snell2025scaling, KIVI, TurboQuant, etc.). Currently the bibliography is empty, so none of the cited sources can be verified.
- **[0752e9c5e99e]** Provide a concrete URL or repository link for the released code mentioned in the abstract and conclusion. The paper states that code is available in the supplementary, but no such link or supplementary material is present.
- **[80c96e616eef]** Clarify the scope of the “state‑of‑the‑art” claim. The tables show KVarN outperforms other quantization baselines, but it is still below full‑precision FP16 performance. Explicitly state that the claim refers to quantized KV‑Cache methods, not to full‑precision models.
- **[537b58201855]** Remove duplicate package imports (e.g., `booktabs` is loaded twice) and consolidate the preamble to improve readability and maintainability.
- **[9c1f110905ca]** Provide the full implementation of the variance-normalization algorithm (Alg. 1) in a separate `.py` or `.cpp` file rather than embedding it in LaTeX; keep the LaTeX file focused on exposition.
- **[5a58e0bf83a6]** Add a minimal, self‑contained test suite (e.g., using `pytest` for Python) that verifies the correctness of the dual‑scale normalization and the pseudo‑decode proxy. Include these tests in the repository.
- **[2e1af3325b25]** Document all external dependencies (e.g., vLLM version, Triton kernel version) in a `requirements.txt` or `environment.yml` file to ensure reproducibility from scratch.
- **[aa8b5307382f]** Split the large LaTeX sections that contain extensive code listings (e.g., the full algorithm and the extensive tables) into separate files and `\\input{}` them, keeping each file under ~200 lines to avoid potential 32 K token truncation limits.
- **[b215ef009aad]** Include the actual KV‑Cache quantization code (both the quantization and dequantization kernels) in the supplementary material or a public repository, and reference the exact commit hash used for the experiments.
- **[ef10505e1e06]** Add a dedicated Data Availability section that lists the exact versions (including commit hashes or release tags) of all external benchmarks used (MATH500, AIME24, HumanEval, IF‑Eval, Line‑Retrieval, NIAH) and provides persistent URLs or DOIs; include the license terms under which each dataset is distributed.
- **[c19efba41bfd]** Provide a public, version‑controlled code repository (e.g., GitHub) that contains the full implementation of KVarN, the preprocessing scripts for the KV‑Cache, and the evaluation pipelines; include a clear README with instructions for reproducing the experiments and a citation to the repository in the paper.
- **[8171babb7409]** Verify that all external URLs (e.g., the GitHub link to https://github.com/huawei-csl/KVarN and any dataset download links) are stable and consider archiving them via a service like Zenodo to prevent link rot.
- **[90c0ae7bfb9c]** Several figures (e.g., Fig. 1, Fig. 5, Fig. 6, Fig. 9) lack explicit axis labels and units, making it hard to interpret the plotted quantities without referring to the main text.
- **[defa81b612de]** The color schemes (custom blue, gray, and multiple hues) are not verified for color‑blind accessibility; consider using a palette that is distinguishable for deuteranopia/protanopia.
- **[307c24226ec4]** Some sub‑figures are very small (e.g., the wrap‑figure in Fig. 3 and the three‑panel Fig. 5) and may become illegible at the final print size; increase font sizes and line widths to ensure readability.
- **[fd8ff389eb0c]** Alt‑text or descriptive captions for the PDF are missing; include concise descriptions for each figure to aid accessibility and for reviewers using screen readers.
- **[147d764ab902]** Figure 2 (pipeline schematic) does not label the individual processing steps (Hadamard rotation, variance‑normalization, RTN) directly on the diagram, which would help readers quickly grasp the workflow.
- **[6cb06c9733ab]** Figures that compare multiple methods (e.g., Fig. 1b, Fig. 5, Fig. 9) should include a legend within the figure area rather than relying on caption text alone, to avoid confusion when printed in grayscale.
- **[cf91b80bb7d9]** The bar charts (Fig. 6, Fig. 8) lack y‑axis tick marks and numeric scales; add these to convey the magnitude of the reported overheads or errors.
- **[1792404d2ced]** Ensure that all figures are referenced in the text with their correct numbers; some captions refer to sub‑figures using \ref{fig:scale:a} etc., but the surrounding text does not always call them out, which can reduce clarity.
- **[20912ffb3d2b]** Define the acronym KV (key‑value) and LLM (large language model) at first use; they appear throughout the manuscript without explanation, which hinders readers outside the sub‑field.
- **[cbed2df70cf4]** Introduce and briefly explain technical terms such as ‘Hadamard rotation’, ‘Sinkhorn‑inspired dual‑scaling’, ‘incoherence processing’, and ‘pseudo‑decode’ when they first appear; currently they are presented as jargon without context.
- **[89dfe62f42c7]** Replace or clarify overloaded abbreviations like RTN (round‑to‑nearest), MSE (mean‑squared error), KL (Kullback‑Leibler), FP16/FP8, and bits/elem; these are not defined before use and assume specialist knowledge.
- **[c36afabde345]** Provide plain‑language descriptions for dataset names (MATH500, AIME24, HumanEval, IFEval, Needle‑in‑a‑Haystack) the first time they are mentioned, e.g., “MATH500, a benchmark of 500 math reasoning problems”.
- **[7411a8d11a9b]** Explain the meaning of UP (uniform precision) and the significance of “bits per element” in the tables; readers unfamiliar with compression metrics may not grasp their impact.
- **[3423c7878cf3]** Avoid excessive use of the term ‘outlier errors’ without a simple definition; a brief explanation of why a few large errors dominate end‑to‑end performance would improve accessibility.
- **[7c007ed7bd1b]** Standardize terminology: the paper alternates between ‘token scaling’, ‘token magnitude errors’, and ‘per‑token scaling’. Choose one phrase and define it early to reduce confusion.
- **[8026bff43828]** When citing prior work (e.g., KIVI, TurboQuant, KVQuant, Kitty, PolarQuant, SnapKV, PyramidKV, KVZip), add a short parenthetical description of each method’s core idea for non‑expert readers.
- **[89c16decb89c]** The phrase ‘dual‑scaling variance normalization’ is repeated many times; consider a concise synonym (e.g., “bidirectional variance scaling”) after the first definition to improve readability.
- **[9a09a87e92df]** Remove back‑ticks around terms like `pseudo‑decode` in the main text; they add visual clutter and do not aid comprehension.
- **[674c3b2ad5e5]** Validate the `pseudo-decode` proxy (Fig. 4) against a true autoregressive decoding run and report quantitative agreement; otherwise temper the claim that it “accurately simulates” error accumulation.
- **[9366909b071a]** Add missing baselines (e.g., recent 2‑bit KV‑Cache methods, mixed‑precision variants) and report statistical significance of the reported gains; the current tables (e.g., Tab. 1, Tab. 2) do not demonstrate that the improvements are robust.
- **[806f8299d738]** Rephrase blanket statements of “state‑of‑the‑art” performance (Abstract, Sec. 1, Sec. 5) to reflect that results are limited to the evaluated models and settings.
- **[0516d8e715f6]** The manuscript does not discuss the dual‑use implications of enabling more memory‑efficient, long‑context reasoning in large language models. Add a brief section (≈1 page) outlining potential misuse scenarios (e.g., generation of disinformation, automated hacking assistance) and propose mitigation strategies such as responsible release policies or usage monitoring.
- **[7bf95e856c9d]** There is no mention of privacy considerations for KV‑Cache contents, which may store user‑provided prompts or sensitive data. Include a statement on how quantization interacts with data confidentiality and whether any leakage risk is introduced.
- **[6a99a9f3255e]** The code release is announced but lacks a licensing or ethical use clause. Provide an explicit license that restricts malicious applications and reference a responsible AI framework.
- **[9d6308e6a9ca]** Provide statistical significance testing (e.g., paired t‑tests or Wilcoxon signed‑rank tests) for the reported improvements in Tables 1‑4 and Figures 2‑5, including p‑values and effect sizes.
- **[1a686c33cdbb]** Report confidence intervals (95 % CI) or standard errors for all aggregate metrics (accuracy, KL‑divergence, token counts) rather than only means or occasional std deviations.
- **[19ce99690d22]** Address multiple‑comparison issues arising from evaluating many models, tasks, and quantization settings; apply a correction method (e.g., Bonferroni, Holm‑Šidák) or clearly justify why it is unnecessary.
- **[4271f5bb1be2]** Validate the ‘pseudo‑decode’ proxy (Section 3.2, Fig. 3) by correlating its results with full autoregressive decoding on a held‑out subset, and report the correlation coefficient with confidence bounds.
- **[be0686437177]** Include a power analysis or sample‑size justification for the number of runs (three) used in the experiments; explain whether this provides sufficient statistical power to detect the observed effect sizes.
- **[9bfa4a50bb6c]** Remove the duplicated `\usepackage{booktabs}` line in the preamble to avoid unnecessary package loading.
- **[76f1af0714fb]** Replace the non‑standard `wrapfig2` package with the standard `wrapfig` (or ensure `wrapfig2` is available) to guarantee compilation on all LaTeX installations.
- **[c1053d1497d4]** Add a period at the end of each figure caption (e.g., after the closing parenthesis) to follow NeurIPS style guidelines for caption punctuation.
- **[425c6b773c63]** Ensure all `\begin{algorithm}` environments include a `\caption{...}` and a corresponding `\label{...}` for proper referencing.
- **[de9329e1b21b]** Standardise the presentation of method names in tables: use `\textbf{KVarN}` (or the defined `\methodname`) consistently instead of mixing `\textit`, `\others`, and `\ours` without a clear legend.
- **[212d7bd91878]** Check column alignment in tables: some `tabular` specifications contain extra spaces (e.g., `l l c c c c c c c c c`). Remove redundant spaces to improve readability of the source.
- **[620aa2c9cf7c]** Add a short explanatory note for the custom commands `\ours` and `\others` in the caption of each table, or move their definitions to a separate style file, to keep the main document cleaner.
- **[e9fd10e8d66b]** Verify that all `\label{...}` commands are placed *after* the corresponding `\caption{...}` (as required for proper cross‑referencing) – e.g., the main `figure` environments currently place `\label` after the caption, which is correct, but double‑check any that deviate.
- **[aa293f97af28]** The abstract contains three overlapping versions of the same paragraph (lines 71‑108). Remove the duplicated text and keep a single concise abstract.
- **[a9cf59ae20b8]** In the Introduction, the first sentence is overly long and mixes several ideas (lines 115‑122). Split it into two sentences for better readability.
- **[1271eca111f5]** Several acronyms (e.g., KV‑Cache, RTN, SINQ) are introduced without prior definition or consistent formatting (e.g., lines 138‑144, 210‑215). Define each acronym on first use and use a uniform style.
- **[c7b099e1ff7f]** Figure captions are overly verbose and contain LaTeX commands that break flow (e.g., Fig. 1 caption lines 176‑186). Rewrite captions to be self‑contained, clear, and free of internal references like ‘Eq.~\ref{eq:decompose}’ unless the equation is actually present.
- **[8e340f9dff15]** The paper mixes British and American spelling (e.g., “optimise” vs. “optimize”) and inconsistent capitalization of section headings (e.g., ‘Preliminaries’ vs. ‘Key Ideas’). Standardize spelling and heading style.
- **[ba75aa16ed0f]** The pseudo‑decode description (Section 4.2, lines 260‑274) repeats the same idea twice and uses informal phrasing such as ‘we will show’. Rephrase to a more formal tone and eliminate redundancy.
- **[a8975de37612]** The ‘Key Ideas’ paragraph (lines 300‑312) uses a wrap‑figure that interrupts the text flow and leaves a dangling reference to Fig. 2 without proper introduction. Relocate the figure or adjust the layout.
- **[994f7d4689ee]** In the Methods section, the equation derivation (lines 340‑355) is dense and lacks explanatory prose; add a brief narrative explaining each step.
- **[cb3473e8352a]** The conclusion (lines 560‑572) repeats results already presented in tables; condense to a summary of contributions and future work.
- **[a2e95c8714a8]** The bibliography style is set to ‘plain’ but the .bbl file is empty, leading to missing citations throughout the text. Ensure all references are properly included.
