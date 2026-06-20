---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/255
paper_authors:
  - Min Zhao
  - Hongzhou Zhu
  - Bokai Yan
  - Zihan Zhou
  - Yimin Chen
  - Wenqiang Sun
  - Kaiwen Zheng
  - Guande He
  - Xiao Yang
  - Chongxuan Li
  - Fan Bao
  - Jun Zhu
---

# minWM: A Full-Stack Open-Source Framework for Real-Time Interactive Video World Models

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.30263
Paper authors (from arXiv): Min Zhao, Hongzhou Zhu, Bokai Yan, Zihan Zhou, Yimin Chen, Wenqiang Sun, Kaiwen Zheng, Guande He, Xiao Yang, Chongxuan Li, Fan Bao, Jun Zhu

Submitted by: github-actions[bot]

(Intake from human-submission issue #255.)

## Rejection rationale (2026-06-20)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[3e452b88f664]** Numerous in‑text citations (e.g., \cite{zhu2026causal}, \cite{zhao2026causal}, \cite{li2026cameras}, \cite{wang2025spatialvid}, \cite{ling2024dl3dv}, \cite{nan2024openvid}, \cite{bao2024vidu}, \cite{feng2025vidarc}, \cite{ye2025yan}, \cite{xiang2025pan}, \cite{he2025matrix}) have no corresponding entries in the bibliography. Add the missing bibliography items or remove/replace the citations.
- **[c84e5a85b6b3]** Broad statements about the progress of video diffusion models (e.g., “Recent video diffusion foundation models have achieved remarkable progress in high‑quality video generation”) are made without any supporting references. Cite recent benchmark papers or surveys that substantiate these claims.
- **[de827dca8dc7]** The claim that minWM “substantially reduces the first‑frame latency” is supported only by a single table (Table 1) with single‑run numbers. Provide statistical evidence (e.g., mean ± std over multiple runs, hardware/software configuration details) to justify the magnitude of the speedup and avoid overstating the result.
- **[39663027f92d]** The manuscript asserts that the framework is “architecture‑general” but demonstrates it on only two backbones (Wan2.1 and HY1.5). Either temper the claim or add experiments on a third, qualitatively different architecture to substantiate generality.
- **[1dba10677b44]** The description of PRoPE camera‑conditioning cites \cite{li2026cameras}, which is absent from the bibliography. Verify that the cited work exists and that the equations accurately reflect it; otherwise, provide a correct reference or adjust the description.
- **[9e6550f6ae56]** Provide a top‑level README that documents the repository layout, required Python/R environment (e.g., conda env.yml or requirements.txt), and step‑by‑step instructions to reproduce the full minWM pipeline from data preparation to inference.
- **[4f6c155b9d5f]** Add the actual training and inference scripts (e.g., data preprocessing, camera‑control fine‑tuning, AR diffusion training, distillation, and inference) to the repository; currently only LaTeX sources are present, making reproducibility impossible.
- **[6c70ef7ffb8f]** Refactor the LaTeX preamble: the custom \textbf redefinition interferes with standard bold formatting and may break packages; replace it with a dedicated macro (e.g., \mybf) or remove it entirely.
- **[c912f2419651]** Trim the massive macro block in math_commands.tex – many symbols (e.g., \rva…\rvz, \rmA…\rmZ) are never used in the paper, inflating the source and risking name collisions. Keep only the symbols actually referenced.
- **[683dfe7599ce]** Introduce a build script (e.g., a Makefile or a simple bash script) that runs pdflatex/biber with the correct flags, ensuring the PDF can be regenerated automatically from the source.
- **[b89a2cfd7ca9]** Add unit‑style tests for any Python utilities (e.g., data loaders, camera‑parameter injection functions) using pytest, and include them in CI to catch regressions.
- **[42e3645e00fa]** Provide explicit version pins for all external dependencies (e.g., PyTorch, transformers, diffusion libraries) in a requirements.txt or conda environment file to avoid hidden incompatibilities.
- **[2477575f6ac0]** Remove unused bibliography entries (e.g., classic ML textbooks) that are not cited in the manuscript; this reduces clutter and improves citation relevance.
- **[d2f87edcbe59]** Add an explicit data‑license statement for all external datasets used (SpatialVid, DL3DV, OpenVid, WorldPlay) and for the released code/checkpoints, specifying the exact license (e.g., CC‑BY‑4.0, MIT).
- **[0d265f6ff3ef]** Provide a concise data schema (e.g., JSON/YAML description) for the camera‑annotated video files, including required fields (intrinsics, extrinsics, timestamps) and how missing values are handled.
- **[5b434e0eda15]** Document the version‑control provenance of the released repository (e.g., git commit hash, tag) and include a reproducible build script that pins all dependencies.
- **[ef49349deba6]** Add persistent, archived URLs (e.g., via Zenodo or Internet Archive) for all external resources cited (datasets, prior papers) to mitigate link rot, or include DOI links where available.
- **[4244ed5cf647]** Add concise alt‑text descriptions for every figure (including sub‑figures) to improve accessibility for screen‑reader users.
- **[706214804911]** Ensure that any quantitative plots (e.g., latency table, if rendered as a figure) include clearly readable axis labels, units, and tick marks that remain legible when printed at 1 column width.
- **[0897b179a620]** Verify that the colour palettes used in the PDF figures are colour‑blind safe (e.g., avoid red‑green combos) and provide a colour legend where multiple curves or categories are shown.
- **[04dc124e59ed]** Provide a brief caption note indicating the resolution or scaling factor of the visualisations (e.g., “Frames are down‑sampled to 480×832 for display”) so readers understand the visual fidelity.
- **[3b453ab06017]** If any figure contains dense visual information (e.g., the main generation example), consider adding a higher‑resolution version in the supplementary material and reference it from the caption.
- **[2f85c0bb97c3]** Define every acronym (e.g., T2V, TI2V, AR, ODE, DMD, SE(3), PF‑ODE, EMA, etc.) at its first appearance in the manuscript.
- **[3711e53e9c4e]** Replace overly technical phrases such as “bidirectional diffusion backbone”, “camera‑controllable multi‑step bidirectional diffusion model”, and “asymmetric DMD” with clearer, more accessible language (e.g., “video diffusion model”, “camera‑aware model”, “final refinement step”).
- **[6e615cd575da]** Simplify the dense mathematical notation in Section 3; many symbols (e.g., \( \widetilde P_i \), \( D_t^{\mathrm{PRoPE}} \), \( \mathrm{Attn}_{\mathrm{PRoPE}} \)) are introduced without intuitive explanation, making the text inaccessible to non‑specialists.
- **[d393ac1f8278]** Add brief, plain‑English summaries after each technical paragraph to explain the purpose of the described operation (e.g., what “teacher‑forcing” achieves, why “causal consistency distillation” matters).
- **[5d0eefa22a0d]** Avoid excessive use of the word “controllability” as a noun; instead use “ability to follow camera commands” or similar phrasing.
- **[5e4288f65c8a]** Standardize reference macros (e.g., replace custom \figref, \secref, etc.) with the journal’s preferred citation style to reduce visual clutter.
- **[4c4d6dcc327c]** The latency comparison (Table 1) pits first‑frame latency of a multi‑step bidirectional model against that of a few‑step AR model, which is not an apples‑to‑apples measure of interactive latency. The claim that minWM “substantially reduces first‑frame latency for real‑time interaction” is therefore insufficiently supported.
- **[1784f3877e89]** The assertion that the distillation pipeline “effectively preserves camera controllability” relies solely on visual inspection of Fig 1. No quantitative metric (e.g., controllability error, pose tracking accuracy) is provided, making the causal claim weak.
- **[acaad80b6617]** The paper states that minWM is “architecture‑general” and can convert “multiple types of video foundation models,” yet only two backbones (Wan2.1 and HY1.5) are evaluated. This overgeneralization is not logically justified by the presented evidence.
- **[66abe07a71c6]** Ablation studies (batch size, training steps, data quality) are presented only as qualitative figure captions without statistical analysis or confidence intervals, leaving the causal relationship between these factors and controllability ambiguous.
- **[5a9abdce11b2]** The method description mixes terminology (e.g., “causal ODE initialization” vs. “causal CD initialization”) without a clear logical mapping to the experimental settings, making it difficult to trace which variant was actually used for each reported result.
- **[18a236a7c05d]** The paper claims “real‑time interactive video world models” but only reports first‑frame latency on a single GPU; it does not provide end‑to‑end interaction latency, frame‑rate during rollout, or user‑perceived latency. This overstates the real‑time capability.
- **[bdd3ac748ae9]** The claim that the framework is “architecture‑general” is supported only by two backbones (Wan2.1 and HY1.5). No experiments on other architectures (e.g., MMDiT, latent diffusion) are shown, making the generality claim unsupported.
- **[027e94a5fb95]** The statement that “few‑step AR models preserve camera‑controllable generation” is based solely on visual inspection of a single figure (Fig. 1). No quantitative metric (e.g., pose error, controllability score) or user study is provided, so the preservation claim is not substantiated.
- **[982bf6612142]** Batch‑size and training‑step ablations (Figs. 2‑4) are presented without statistical variance or repeated runs, yet the paper draws definitive conclusions about minimal batch size and step thresholds. This extrapolates beyond the limited evidence.
- **[d5bd3d785fd7]** The limitations section is absent. The manuscript does not discuss failure modes (e.g., degradation of visual quality after distillation, sensitivity to camera‑trajectory noise, or scalability to longer videos), which is required given the strong performance claims.
- **[f31b9de12732]** Latency numbers in Table 1 exclude VAE encoding/decoding time and only measure the first frame. Claiming “low‑latency inference” without reporting total inference time per frame or memory footprint is misleading.
- **[0f27b604e2ad]** The paper suggests that the framework can adapt existing world models (e.g., HY‑WorldPlay) to new data distributions, yet no experiments or benchmarks are provided to support this claim.
- **[02e5f4f9e75a]** The abstract and introduction repeatedly assert that a “full‑stack, reproducible, extensible recipe” is provided, but the repository link is not evaluated for completeness (e.g., missing scripts for data preprocessing, missing checkpoints for intermediate stages). This overstates reproducibility.
- **[6ef416cde126]** Add a dedicated “Ethical Considerations” or “Responsible Use” section that discusses the dual‑use nature of camera‑controllable video generation, potential for disinformation, privacy violations, and outlines concrete mitigation strategies (e.g., watermarking, usage licenses, model access controls).
- **[6def0747d8f8]** Provide clear documentation of the provenance and licensing of all training datasets (SpatialVid, DL3DV, OpenVid, WorldPlay). Verify that no personally identifiable information (PII) or copyrighted content is inadvertently included, and state any filtering steps taken to remove such data.
- **[9b34cfca9ed2]** Consider implementing a technical safeguard such as a detectable watermark or a model‑level classifier that can flag generated content, and describe this in the code repository.
- **[c1b9da4eed05]** If the released checkpoints are made publicly available, include a usage policy that restricts malicious applications (e.g., deep‑fake creation, surveillance) and outlines a process for revoking access if abuse is detected.
- **[45361c17c92c]** Provide quantitative evaluation of video quality (e.g., FVD, IS, user preference studies) for both the bidirectional and few‑step AR models, including confidence intervals or statistical significance testing.
- **[bcf4a32d3035]** Report the size of the training and validation datasets (number of videos, total frames) used for each ablation (batch size, training steps, data source) and include variance measures (e.g., standard error) across multiple runs.
- **[e5bc17cf5999]** Include a clear description of random seeds, hardware configuration, and any nondeterministic components to enable exact replication of the reported latency and controllability results.
- **[2ec88c41ac7a]** Add an objective metric for camera controllability (e.g., pose error, trajectory alignment score) rather than relying solely on visual inspection of a few examples.
- **[2a6dd5e15be5]** Present ablation results in tabular form with numeric values (e.g., latency, quality scores) instead of only qualitative figure captions, and discuss statistical robustness of observed trends.
- **[ca476e2c7206]** Clarify the number of training steps and batch‑size experiments that were repeated; if only a single run was performed, run multiple seeds to assess variability and report the results.
- **[e05e54b58e36]** Provide details on the distribution of camera trajectories in the constructed datasets (e.g., range of rotations, translations) to justify the claim that ground‑truth trajectories are essential.
- **[f1c53d4af76f]** Provide quantitative evaluation of camera‑controllable generation quality (e.g., FVD, CLIP‑Score, or task‑specific metrics) across multiple random seeds, and report mean ± standard deviation or confidence intervals.
- **[4d7e7f158801]** Include statistical significance testing (e.g., paired t‑test or Wilcoxon signed‑rank) when comparing latency reductions or quality metrics between the multi‑step bidirectional, multi‑step AR, and few‑step AR models.
- **[34eeb2741554]** Document the number of independent training runs performed for each ablation (batch size, training steps, data source) and present variance measures to support claims of stability or instability.
- **[dc49774cdfaf]** Address multiple‑comparison concerns by applying appropriate corrections (e.g., Bonferroni or Holm) when reporting several ablation results in the same table/figure.
- **[9df6f3e42e66]** Add error bars to all plotted quantitative results (e.g., latency, any future quality metrics) and describe the method used to compute them (bootstrapping, standard error, etc.).
- **[f769a245c082]** Move the abstract environment to after \maketitle (i.e., place \begin{abstract}…\end{abstract} after \maketitle inside the document body).
- **[993d796309a2]** Remove the space in the label \label{sec: method} (change to \label{sec:method}) to avoid illegal label names.
- **[1e8bc16c481e]** Resolve the citation style conflict: you load natbib with numeric style but later redefine \cite to \citep (author‑year). Choose one style and keep the corresponding \bibliographystyle (e.g., use natbib’s numeric style with \citep or switch to author‑year and adjust the bibliography style).
- **[12e41b8b28fe]** Ensure the booktabs package is explicitly loaded (or confirm that shengshu.cls provides it) before using \toprule, \midrule, and \bottomrule in tables.
- **[7829ca2d19db]** Avoid redefining the core \textbf command in the preamble (the current \DeclareTextFontCommand overrides the standard bold font and may break other packages). Use a new macro for the custom font size instead.
- **[ab9360daa581]** In subfigure environments, replace the width argument \linewidth with a relative width (e.g., 0.48\textwidth) to avoid subfigure stretching to the full line width, which can cause layout warnings.
- **[815f38b5c99d]** Place \label after \caption in all figure and table environments (most of your figures already do this, but double‑check consistency).
- **[7c18dbd7d2d9]** Check that all \usepackage commands are not duplicated by the class; remove any redundant package loads to prevent conflicts (e.g., natbib is already loaded by the class).
- **[56a7e71431d4]** Standardize line wrapping in long paragraphs (e.g., the abstract and method description) to avoid overfull hbox warnings; consider using \sloppy or manual line breaks where appropriate.
- **[27d41e7ac622]** Split overly long sentences (e.g., the abstract sentence describing the Causal Forcing pipeline) into shorter, clearer statements.
- **[05899fa69995]** Add missing spaces after periods (e.g., in Method section: "generator.The pipeline" → "generator. The pipeline").
- **[76f8efc89f90]** Correct inconsistent section label syntax (e.g., "\label{sec: method}" should be "\label{sec:method}").
- **[db335cc6a622]** Standardize phrasing of figure references (use "Fig.~\ref{...}" consistently) and ensure captions are concise.
- **[78ae4b4c3ee8]** Revise repetitive phrasing such as "real-time interactive video world models" which appears multiple times in the abstract and introduction; replace with synonyms or restructure.
- **[af3333ebcbf0]** Fix minor grammatical errors (e.g., missing commas in lists: "causal rollout, respond to user actions" → "causal rollout, respond to user actions,").
- **[0f2417ba7bc4]** Adjust table caption wording for clarity (e.g., "First-frame latency of different HY1.5 and Wan2.1 models" → "First-frame latency for HY1.5 and Wan2.1 models").
- **[101d96c13a3e]** Rename the conclusion heading from "Conclusion and the Future Work" to the more conventional "Conclusion and Future Work".
- **[8b4443b76bb5]** Ensure consistent use of hyphenation and spacing in technical terms (e.g., "few‑step" vs "few-step").
- **[1b71ee91023c]** Proofread for typographical consistency in mathematical notation (e.g., add spaces around operators in equations).
