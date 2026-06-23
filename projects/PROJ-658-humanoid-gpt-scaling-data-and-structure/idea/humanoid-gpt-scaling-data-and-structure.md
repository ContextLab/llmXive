---
field: computer science
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/273
paper_authors:
  - Zekun Qi
  - Xuchuan Chen
  - Dairu Liu
  - Chenghuai Lin
  - Yunrui Lian
  - Sikai Liang
  - Zhikai Zhang
  - Yu Guan
  - Jilong Wang
  - Wenyao Zhang
  - Xinqiang Yu
  - He Wang
  - Li Yi
---

# Humanoid-GPT: Scaling Data and Structure for Zero-Shot Motion Tracking

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.03985
Paper authors (from arXiv): Zekun Qi, Xuchuan Chen, Dairu Liu, Chenghuai Lin, Yunrui Lian, Sikai Liang, Zhikai Zhang, Yu Guan, Jilong Wang, Wenyao Zhang, Xinqiang Yu, He Wang, Li Yi

Submitted by: github-actions[bot]

(Intake from human-submission issue #273.)

## Rejection rationale (2026-06-23)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[9854b27eda8c]** Many in‑text citations (e.g., beyondmimic25, asap25, twist25, unitracker25, gmt25, sonic25, motionx++25, phuma25, motionmillion25, gmr25) are not present in the bibliography. Add proper bibliography entries or correct the citation keys.
- **[e453c0c6b3ab]** The claim that “video‑estimated motion can materially improve tracking when the model and the training set are scaled appropriately” is not supported by any ablation or quantitative analysis in the paper. Provide experimental evidence or remove the claim.
- **[3d276720b590]** The statement “We are the first motion tracker with zero‑shot ability trained on a 2B‑frame data set” and “over 200× larger than prior trackers” are presented as novelty claims without clear comparison to all existing works. Verify these claims against the literature and cite any relevant prior large‑scale trackers (e.g., SONIC, any other >100M‑frame works).
- **[79c0a2d5bfb8]** Table 1 lists several prior methods with check‑marks for “Agile” and “Zero‑shot” but provides no source or definition for these attributes. Clarify the criteria and ensure the table accurately reflects the cited papers.
- **[ebb34e39ad92]** The scaling‑law analysis (Fig. 5, Fig. 6) claims monotonic improvement up to 2 B tokens, yet the marginal gains between 200 M and 2 B are described as “slight” while still being presented as a strong scaling law. Re‑phrase to accurately reflect the observed diminishing returns.
- **[65ed57672518]** The latency claim (≤1.5 ms on RTX 4090) is shown in Fig. 7 but lacks details on batch size, precision (FP16 vs FP32), and whether TensorRT optimizations were applied uniformly across baselines. Add a brief description of the measurement setup.
- **[2c36cdd0402b]** Provide the full source code (training scripts, data processing pipelines, model definition, and evaluation utilities) in a well‑structured repository rather than only the LaTeX manuscript. Include a clear README, dependency list (e.g., requirements.txt or environment.yml), and reproducibility instructions (data download, preprocessing, training commands, hardware requirements).
- **[94e5d82cda27]** Modularize the codebase: separate data curation, expert PPO training, DAgger distillation, and inference into distinct Python packages or modules. Avoid monolithic scripts that exceed 200 lines; split them into logical sub‑modules (e.g., data/curation.py, train/expert.py, distill/da​gger.py, deploy/inference.py).
- **[d8e1ee2e6b56]** Add a comprehensive test suite. Unit tests should cover data loading/augmentation, reward computation, model forward passes, and checkpoint saving/loading. Integration tests should verify end‑to‑end training on a tiny synthetic dataset and inference latency on the target hardware.
- **[8988e002afbe]** Document the software environment and hardware dependencies explicitly (CUDA version, cuDNN, PyTorch/TensorFlow version, MuJoCo license). Provide a Dockerfile or Conda environment file to guarantee that reviewers can reproduce the experiments from scratch.
- **[5a6253cc6a9d]** Clean the LaTeX source: remove duplicate usepackage entries, consolidate macro definitions, and ensure all referenced figure files exist. This will prevent compilation failures and improve readability of the supplementary material.
- **[9b20aa8c039b]** Add a clear data availability and licensing statement for all external datasets (AMASS, LAFAN1, MotionMillion, PHUMA) and the internal 2 B‑frame corpus, including URLs, version identifiers, and the specific licenses under which each source can be redistributed.
- **[b8d5447735e1]** Provide a formal schema (e.g., JSON/YAML or protobuf definition) for the motion data format used after retargeting (joint ordering, units, timestamp resolution, missing‑value conventions).
- **[a88bd7be041f]** Describe the missing‑data handling pipeline in detail: how filtered or corrupted clips are detected, what criteria trigger removal, and whether any imputation or augmentation is applied.
- **[efcc412e220a]** Document the provenance of the in‑house recordings (date of capture, sensor setup, calibration procedures) and assign a persistent identifier (e.g., DOI or Zenodo record) to ensure reproducibility.
- **[af221487b533]** Ensure that all external resource links (e.g., dataset URLs, code repositories) are stable; consider using archived URLs (via archive.org) or providing a `requirements.txt`/`environment.yml` that pins exact versions of any preprocessing scripts.
- **[db12d000c6a5]** Include a version‑control snapshot (e.g., git commit hash) of the data processing scripts used for filtering, segmentation, and augmentation, and make these scripts publicly accessible.
- **[a85c1f28d27e]** Add clear axis labels (including units) and legends to all quantitative plots (e.g., Fig 2 (data_scaling.pdf), Fig 3 (model_training.pdf), Fig 4 (data.pdf)). This will make the figures interpretable without referring to the main text.
- **[16a50c38bfee]** Provide descriptive alt‑text for each figure in the LaTeX source (using \caption[...]{...} optional argument) to improve accessibility and aid reviewers reading the PDF in grayscale.
- **[be1bf1a0fbae]** Replace or recolor the current color schemes in multi‑color figures (e.g., Fig 1 (teaser.pdf), Fig 2 (pipeline.pdf), Fig 5 (ablation.pdf)) with a color‑blind‑friendly palette (e.g., using ColorBrewer’s ‘Set2’ or similar) and ensure sufficient contrast for print.
- **[6456cf4f72d5]** Increase the font size of axis tick labels and legend text in all plots so they remain legible when the figure is printed at typical journal column width (≈3.25 in).
- **[822b7b7c72ca]** For the bubble‑plot in Fig 2 (diversity.pdf), add a legend explaining the meaning of bubble size and axes (gstd, log‑volume) and include grid lines or reference markers to aid quantitative reading.
- **[fff2b97a2219]** In Fig 6 (accurate.pdf) showing inference latency, annotate the bars with exact latency values (ms) and indicate the hardware configuration directly in the caption.
- **[f8865c0991f3]** Ensure that all figures are embedded as vector graphics (PDF/EPS) rather than rasterized images where possible, to avoid loss of detail at high resolution.
- **[81370694c5ed]** Define every acronym on first use (e.g., AGI, MLP, PPO, DAgger, HME, G1, SR, MPJPE, MPJVE, MPKPE).
- **[02e3cd53d292]** Replace overloaded buzzwords such as “scaling”, “zero‑shot”, “foundation model”, “emergent”, and “science of scale” with concrete descriptions of what is actually being increased or achieved.
- **[f20f6be3b31f]** Remove or simplify decorative macros (e.g., \red{}, \blue{}, colored bold text) that add visual noise without adding meaning for readers.
- **[6f62eb3d7f24]** Provide plain‑language explanations for technical terms like “causal attention”, “GPT‑style Transformer”, and “Harmonic Motion Embedding (HME)” to make the paper accessible to readers outside the robotics/ML sub‑community.
- **[25cb6fe9892c]** Avoid excessive use of check‑mark symbols (\checkmark) in tables; replace with clear textual indicators (e.g., “yes”/“no”).
- **[caae0f5290c8]** Provide a controlled ablation that isolates the contribution of video‑estimated motion data versus purely mocap data (Section 3.1). Without this, the claim of “systematic evidence that video‑estimated motion materially improves tracking” is not logically supported.
- **[568b735c0e8e]** Clarify whether performance gains reported in Table 2 are primarily due to increased model capacity, data scale, or both. An experiment holding model size constant while varying data (or vice‑versa) would resolve the logical ambiguity.
- **[dd8d217c3665]** The manuscript repeatedly claims *unprecedented* zero‑shot generalisation (e.g., abstract line 1, Table 1, and Sec. 4) without providing statistically‑significant comparisons to strong baselines on a sufficiently diverse set of unseen tasks; add rigorous zero‑shot benchmarks (e.g., additional motion families, cross‑dataset tests) and report variance/ confidence intervals.
- **[6391d097cbdc]** The paper states that scaling to 2 B frames *materially improves* tracking and that a scaling law is derived (Sec. 5), yet no quantitative fit (exponent, R²) or ablation isolating data‑scale vs. model‑scale is presented; include a formal scaling‑law analysis with fitted curves and error bars.
- **[469f178cd1b7]** Claims such as “first systematic evidence that video‑estimated motion can materially improve tracking” (Sec. 1) are unsupported because no ablation comparing video‑estimated vs. purely mocap data is shown; provide a controlled experiment isolating this factor.
- **[b00b244ecf33]** The statement that the method “establishes a new performance frontier” (abstract and Sec. 4) is overstated given that the evaluation metrics (e.g., MPJPE, SR) are reported without statistical significance testing against baselines; add appropriate statistical tests (e.g., paired t‑test) and discuss practical significance.
- **[6ed30b55b536]** The paper asserts that the model “maintains real‑time performance” (Sec. 4.3) based on a single latency figure; however, latency is only measured on a high‑end RTX 4090 and does not reflect deployment on typical robot hardware; report latency on the target robot’s compute platform and discuss any trade‑offs.
- **[90c3dc4cfff3]** Provide explicit documentation of informed consent and anonymization procedures for all human motion capture data, especially any video‑estimated motions, and include IRB/IACUC approval numbers where applicable.
- **[0651566f0a38]** Add a dedicated safety analysis section that quantifies failure‑mode risks (e.g., falls, collisions) of the deployed humanoid, describes emergency‑stop mechanisms, and outlines testing protocols on safety‑critical scenarios.
- **[fad18d7f7a3e]** Discuss dual‑use concerns and propose mitigation strategies (e.g., usage licensing, access controls) to prevent the technology from being repurposed for harmful surveillance or malicious imitation of human behaviors.
- **[a89730ea4bc2]** Clarify data‑privacy handling for any external video sources used for motion estimation, ensuring that no personally identifiable information is retained and that data usage complies with relevant privacy regulations.
- **[9139f49bcb06]** Include a risk‑assessment matrix that maps identified hazards (physical injury, privacy breach, misuse) to mitigation measures and residual risk levels.
- **[5b23c20dc441]** Provide statistical uncertainty (e.g., confidence intervals or standard deviations) for all quantitative results in Tables 2 and 3 and for the scaling‑law curves (Figs 7‑9). This will allow assessment of effect size robustness and variance across random seeds.
- **[cd395eedbb70]** Report the number of random seeds and training runs used for each configuration (e.g., Humanoid‑GPT‑S/B/L) and ensure that baseline methods (GMT, TWIST, Any2Track) are re‑trained under identical seeds and data splits to serve as proper controls.
- **[1c45cbbc177b]** Include an ablation that isolates the contribution of the Harmonic Motion Embedding (HME) sampling strategy versus uniform sampling, with statistical tests to rule out over‑fitting to a particular cluster configuration.
- **[9c0a90029546]** Clarify the exact train/validation/test split for the 2 B‑frame corpus (e.g., how many clips are held out, whether any overlap exists with the real‑world dance sequences) to eliminate potential data leakage.
- **[36118986d75d]** Add significance testing (e.g., paired t‑tests or non‑parametric equivalents) when comparing Humanoid‑GPT against baselines on the AMASS‑test split to demonstrate that observed improvements are not due to chance.
- **[85d478ff0b39]** Report the distribution of motion types (e.g., percentages of locomotion, acrobatics, etc.) in the curated dataset and in the evaluation sets to verify that the claimed ‘diversity‑balanced’ sampling truly covers the motion manifold.
- **[78c76961f363]** Report variability (e.g., standard deviation, confidence intervals) for all quantitative metrics in Tables 2, 3, 4, and 5. This includes SR, MPJPE, MPJVE, RootVelErr, and MPKPE across multiple random seeds or runs.
- **[20dbd4969866]** Conduct appropriate statistical significance tests (e.g., paired t‑tests or non‑parametric tests) when comparing Humanoid‑GPT variants to baselines (GMT, TWIST, Any2Track). Clearly state the null hypothesis, test used, and p‑values.
- **[055030aaf588]** Provide details on random seed handling, number of repetitions per experiment, and any variance reduction techniques employed. This information should be added to the implementation and reproducibility section (Sec 6).
- **[c75661edd7f9]** When presenting scaling‑law curves (Fig. 7 and Fig. 8), fit explicit regression models, report the fitted parameters with confidence intervals, and discuss goodness‑of‑fit (e.g., R²).
- **[e372b66cd174]** Address multiple‑comparison concerns: if many model‑size and data‑size configurations are evaluated, apply a correction (e.g., Bonferroni or Holm) or justify why it is unnecessary.
- **[6c5c21be794d]** Remove duplicate and redundant package imports (e.g., multiple \usepackage{graphicx}, \usepackage{multirow}, \usepackage{tikz}, etc.) to clean up the preamble and avoid compilation warnings.
- **[95f75ac3a145]** Consolidate color definitions; the same colors (e.g., cmpblue) are defined twice. Keep a single definition per color to improve readability.
- **[ef6888157a83]** Avoid redefining \paragraph multiple times (appears in both the shim layer and later in the document). Choose a single definition and apply it consistently.
- **[19e460c72ba6]** Eliminate the unused \abstract macro defined in sec/0_abstract.tex, since the abstract is already provided via the standard \begin{abstract} environment in main-llmxive.tex.
- **[d32cf4941a6d]** Standardize table styling: use a single \tablestyle macro throughout instead of mixing custom \setlength{\tabcolsep}{...} and ad‑hoc \resizebox calls. This will make tables more uniform and easier to maintain.
- **[47f997055dd0]** Place all figure captions directly after the \includegraphics command and before the \label, as required by most style guides. Verify that each \caption is followed by a corresponding \label.
- **[e0601eab3036]** Remove redundant \makeatletter/\makeatother blocks that only provide no‑op shims for venue‑specific macros; they add noise to the source and can be omitted in the final version.
- **[94422daf3c48]** Check line wrapping and paragraph spacing around long equations and itemized lists to ensure they do not overflow the column width in the two‑column layout.
- **[42609fb40924]** Several sentences are overly long and contain multiple clauses, which reduces readability. Split complex sentences into shorter, clearer ones, especially in the Introduction and Method sections.
- **[a8d0015ff4c1]** There are typographical inconsistencies such as `R_{\text{panel}}` which should be `R_{\text{penal}}`, and missing spaces after citations (e.g., `~\cite{...}`) that disrupt flow.
- **[e3e99b00c197]** The preamble and macro definitions contain many duplicated or unused packages/macros (e.g., multiple `\usepackage{booktabs}` and redundant `\paragraph` redefinitions). Clean up the LaTeX preamble to improve document maintainability.
- **[39903512aecc]** Table captions and figure references sometimes lack proper punctuation or clear description (e.g., caption of Table 1). Revise captions to be self‑contained and grammatically correct.
- **[a412a4bf6a9e]** Paragraph cohesion can be improved; several paragraphs start abruptly without a clear topic sentence, making the logical flow harder to follow. Add introductory sentences that state the main point of each paragraph.
