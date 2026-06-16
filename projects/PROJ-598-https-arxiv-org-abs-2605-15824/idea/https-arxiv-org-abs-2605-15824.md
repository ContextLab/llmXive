---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/202
---

# https://arxiv.org/abs/2605.15824

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2605.15824

Submitted by: github-actions[bot]

(Intake from human-submission issue #202.)

## Rejection rationale (2026-06-16)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[f422e9b5d9ea]** Replace or verify all citations that reference works from future years (e.g., 2025, 2026). Ensure every bibliography entry corresponds to an existing, peer‑reviewed source with a verifiable verification_status.
- **[786395e8218d]** Provide a complete, reproducible description of the dataset curation pipeline, including exact numbers of videos per class, annotation formats, and any filtering thresholds used. Release the curated dataset or a detailed script to reconstruct it.
- **[4e172dce12b8]** Clarify the definitions and computation procedures for the evaluation metrics HGC, LGC, and NTP (currently only listed in tables). Include equations or references so readers can reproduce the scores.
- **[cbec5ce7442d]** Add explicit hardware and software environment details for the reported 23.8 FPS figure (GPU model, driver version, batch size, precision, any optimizations). Provide a reproducibility checklist.
- **[e11122073050]** Expand the description of the Training‑Free KV Cache Rescheduling algorithm: provide pseudo‑code or a clear algorithmic flow, and discuss computational overhead and memory usage.
- **[c4eb1743f46a]** The abstract (Section 1) claims “30–180× faster than baselines” but the manuscript never provides baseline FPS numbers to substantiate this range. Add a table or explicit numbers for each baseline’s inference speed to support the speed‑up claim.
- **[22ec6abd63f2]** The statement in the introduction (Section 2) that diffusion‑based text‑to‑video models “lack fine‑grained, low‑latency garment control” is not directly supported by the cited works \cite{ho2020denoising,lipman2022flow,yang2024cogvideox,wan2025wan}. Those papers discuss general video diffusion and do not evaluate garment‑level control. Either replace the citation with works that explicitly study garment control or qualify the claim.
- **[649e7bcd1a0f]** In the related‑works paragraph on Subject‑to‑Video customization, the paper asserts that existing methods “suffer high latency” and that FashionChameleon “achieves real‑time interactivity”. No latency figures are provided for the cited baselines \cite{wang2026customvideo,chen2024disenstudio,he2024id,yuan2025identity,liu2025phantom,vace,xue2025stand}. Provide latency measurements (FPS or ms/frame) for these baselines to substantiate the claim.
- **[5c4b1dcfd73f]** The claim that the proposed Gradient‑Reweighted DMD “improves long‑video (165‑frame) metrics” relies on Table 5, which compares only two variants (Naive DMD vs. GR‑DMD). However, statistical significance is not reported. Include variance/error bars or statistical tests to confirm that the improvements are not due to random variation.
- **[d0ab59acbb3d]** The conclusion states that the method “outperforms baselines on ID consistency, motion quality, and garment consistency”. While Table 1 shows the best values for many metrics, the baselines’ numbers are omitted (shown as “… rows omitted…”). Provide the full baseline results so readers can verify the superiority claim.
- **[05ca85adaeca]** The submission does not include any source code, build scripts, or dependency specifications required to reproduce the reported results. Provide a publicly accessible repository (e.g., GitHub) containing the full training and inference code, with a clear README.
- **[19cacd6ca863]** Current LaTeX source references many figures (e.g., figures/overall_pipeline.pdf, figures/analysis.pdf) but the repository lacks the corresponding source files (e.g., Python scripts that generate these figures). Include the data processing and visualization scripts.
- **[0b2067a090e1]** No unit or integration tests are provided for critical components such as the KV‑Cache rescheduling module, the gradient‑reweighted DMD implementation, or the in‑context teacher forcing logic. Add a test suite (e.g., pytest) covering at least 80 % of the code base.
- **[7ea0043fcc01]** Dependency hygiene is unclear: the paper mentions libraries like FSDP, AdamW, and specific VAE/Transformer implementations, but there is no requirements.txt or environment.yml. Specify exact package versions (including CUDA/cuDNN) to ensure reproducibility.
- **[5b900e4e2ee0]** The training hyper‑parameters are described in prose (e.g., learning‑rate schedule, batch size) but not exposed in a machine‑readable config file. Provide a YAML/JSON configuration that can be consumed by the training script.
- **[c321496d6d97]** Large‑scale experiments (e.g., 62 K samples, 23.8 FPS on H200 GPU) require hardware specifications and runtime logs. Include scripts to benchmark FPS and scripts to log GPU memory/throughput.
- **[eaff53f6876b]** Provide a public, version‑controlled release of the curated 62 K video‑garment triplet dataset (e.g., via Zenodo or a Git‑LFS repository) and include a persistent DOI.
- **[9c2af188b0cf]** Specify the data license (e.g., CC‑BY‑4.0) for the released dataset and for any third‑party assets used (YOLOv8‑Seg, VLM prompts, etc.).
- **[69bab2f7e128]** Add a detailed schema for the dataset (fields, formats, units, missing‑value conventions) in the appendix or a separate data‑card.
- **[719deb5d51f9]** Describe how missing or corrupt video frames, incomplete garment annotations, or failed OCR/VLM steps are detected and handled during curation.
- **[540f138de284]** Ensure all external URLs (e.g., the project page https://quanjiansong.github.io/projects/FashionChameleon/) are archived (e.g., via Internet Archive) and referenced with a stable identifier.
- **[35e5c43fc35b]** Include a version‑control statement for the codebase (e.g., Git commit hash) and for the model checkpoints used in experiments.
- **[c7e4ad168d08]** Figure \ref{fig:intro} (average performance chart) lacks axis labels and units; add a clear X‑axis label (e.g., “Method”) and Y‑axis label (e.g., “Score / FPS”) with numeric ranges.
- **[f4b6a11eaf92]** Figures \ref{fig:overall_pipeline}, \ref{fig:analysis}, and \ref{fig:qualitative_comparison} use color palettes that are not color‑blind friendly (red/green contrasts). Replace with a palette that is distinguishable for deuteranopia/protanopia.
- **[144966c0e8ea]** Several PDF figures (e.g., \ref{fig:teaser}, \ref{fig:overall_pipeline}, \ref{fig:analysis}) are rendered at 0.98 × textwidth but may be too small for print; increase their width to at least 0.9 \linewidth or provide higher‑resolution raster versions.
- **[77c4223c7b08]** Alt‑text descriptions are missing for all figures; add concise alt‑text in the caption or a separate \caption[]{...} command to improve accessibility.
- **[32b139312989]** Figure \ref{fig:user_preference} (human evaluation bar plot) does not indicate error bars or statistical significance; include standard deviation or confidence intervals to support the claim of superiority.
- **[5749293581b7]** The analysis figure (\ref{fig:analysis}) shows attention visualisation but the color scale is not explained; add a legend indicating what the color intensity represents.
- **[a1a20908d09f]** In the ablation figure(s) (e.g., \ref{fig:ablation2}), the sub‑figures are not labelled (a), (b), etc., making it hard to reference them in the text; add panel labels.
- **[5f3949f8d537]** Define every acronym on first use (e.g., KV, DMD, GR‑DMD, HGC, LGC, NTP, Cur., GME, Amp., Smoo., VQ) or replace with plain terms.
- **[a067888bc025]** Replace “In‑Context Learning” with a brief explanation (e.g., learning from examples provided at inference time) or a simpler phrase.
- **[50c6fdcdb17d]** Explain technical jargon such as “teacher forcing”, “gradient‑reweighted distribution‑matching distillation”, and “multimodal attention” in plain language or add footnotes.
- **[c13adfc03103]** Substitute dense metric abbreviations (Cur., GME, Amp., Smoo., VQ, HGC, LGC, NTP) with full names in the text and tables, or provide a clear legend near the first occurrence.
- **[bc7c5299dd80]** Avoid overuse of buzz‑words like “autoregressive”, “bidirectional teacher”, “streaming distillation”, and “training‑free KV cache rescheduling” without concise definitions; consider rephrasing for readability.
- **[8f140626b910]** Simplify the description of “KV cache” operations (Refresh, Withdraw, Disentangle) by describing the purpose (e.g., updating stored information) rather than using the abbreviation‑heavy terminology.
- **[2db2bc52e53c]** Clarify the meaning of “23.8 FPS (30–180× faster than baselines)” by stating the absolute speed of baselines or giving a concrete comparison.
- **[a8cd8a9f3d5b]** Reduce the density of numeric symbols in tables (e.g., use “higher is better” notes) and provide a brief caption explaining each column.
- **[2163fc547d3c]** The claim of ‘30–180× faster than baselines’ in the abstract is not substantiated by the quantitative results; baseline FPS values are omitted from Table 1, making the speed‑up factor unverifiable.
- **[80cc69872752]** The methodology states that the teacher model is trained on a single reference–garment pair yet the paper asserts ‘single‑to‑multiple generalization’; provide experimental evidence or a clearer theoretical justification for how a model trained on one pair can handle arbitrary garment sequences.
- **[ee0d2b0578ef]** Clarify whether the reported 23.8 FPS is measured on 720p (1280×704) resolution consistently across all experiments; any deviation should be explicitly noted to avoid implicit contradictions in performance reporting.
- **[7dc99bd95052]** Provide explicit baseline inference‑time or FPS numbers for each competing method to substantiate the claim of “30–180× faster than baselines” (Abstract, line 1). Without these numbers the speed‑up statement is not verifiable.
- **[9e65e3fce69a]** Re‑phrase the “training‑free KV Cache Rescheduling” description (Section 4.3) to clarify that only the cache‑rescheduling component is training‑free, while the overall pipeline still requires teacher pre‑training and streaming distillation.
- **[97a96d629428]** In Table 1 (Main Results) include the FPS values of the baseline methods, or at least a footnote specifying their speeds, so readers can confirm the reported 23.8 FPS advantage and the claimed 30–180× speedup.
- **[5b5b9edccd7b]** The manuscript does not describe how subjects in the training data gave informed consent; add a detailed discussion of data collection ethics and consent procedures.
- **[b2e88b3203a3]** Potential for generating non‑consensual or harmful deepfake videos is not mitigated; propose concrete safeguards such as watermarking, usage restrictions, and detection tools.
- **[c2f978895085]** Bias and fairness analyses of garment representation across demographics are missing; include evaluation of demographic bias and steps to mitigate.
- **[f03cf3639f57]** The paper lacks a clear policy for responsible deployment and user access control; add a section outlining responsible release practices.
- **[1e24b2aa8e44]** The manuscript reports quantitative metrics (e.g., Cur., GME, FPS) without any measure of variability (standard deviation, confidence intervals) or statistical significance testing, making it impossible to assess whether observed differences are robust or could arise by chance.
- **[604adaf7e3d5]** FPS comparisons claim a 30–180× speedup over baselines, yet the paper does not disclose hardware‐specific configurations (e.g., batch size, precision mode) for the baselines, nor does it provide raw timing logs. Without a controlled benchmarking protocol, the speedup claim remains unverified.
- **[868cd89e564e]** Ablation tables (e.g., Table 2, Table 3) present single scalar values per variant, but there is no indication of how many runs were performed or whether the results are averaged. Replication details (random seeds, variance) are missing, raising concerns about result stability.
- **[d60622129e32]** The user study reports 672 valid responses, yet the demographic breakdown, randomization of video presentation order, and statistical analysis (e.g., ANOVA or post‑hoc tests) are absent. This hampers evaluation of the external validity of the subjective findings.
- **[5e1fac481ba8]** The training dataset size (≈ 62 K triplets) is mentioned, but the paper does not provide a power analysis or justification that this sample size is sufficient to support the claimed generalization to diverse garment categories. A discussion of potential sampling bias is needed.
- **[164d20e3f7e3]** Provide statistical significance testing (e.g., paired t‑tests, Wilcoxon signed‑rank) for the quantitative comparisons in Table ef{tab:main_results} and all ablation tables. Report p‑values or confidence intervals to substantiate claims of superiority.
- **[7952d28cb2ca]** Include measures of variance (standard deviation, standard error, or confidence intervals) for each reported metric (Cur., GME, Amp., etc.) across multiple random seeds or data splits. Currently only point estimates are shown.
- **[46d903864ec3]** Address multiple‑comparison issues when evaluating many metrics and baselines simultaneously. Apply corrections (e.g., Bonferroni, Holm) or clearly justify why they are unnecessary.
- **[9746b55e3491]** Detail the experimental protocol for reproducibility: number of runs, random seed handling, hardware variability, and any stochastic components in training/distillation.
- **[2d61e52c690a]** Clarify how evaluation metrics (e.g., ID Consistency, Motion Magnitude, Visual Quality) are computed and whether they are directly comparable across baselines that may have different output resolutions or preprocessing.
- **[19d74de01566]** Inconsistent use of figure environments – the teaser figure uses a \begin{center} … \captionof{figure} construct while all other figures use the standard \begin{figure} environment. Standardize all figures to the \begin{figure} … \caption{…} \label{…} \end{figure} pattern.
- **[2a59211abd7f]** Duplicate top‑level sections: the manuscript contains two separate \section{Introduction} blocks (one after the abstract and another after the custom abstract) and two \section{Methodology} blocks. Remove the redundancies or rename the later sections to appropriate subsection levels.
- **[5240fb1bf01e]** Table formatting relies on \toprule, \midrule, and \bottomrule but the preamble does not show an explicit \usepackage{booktabs}. Ensure the booktabs package is loaded, otherwise compilation will fail.
- **[6610404484ca]** Citation style is mixed: some citations use a non‑breaking space before the \cite (e.g., ~\cite{...}) while others use a plain \cite{...}. Adopt a consistent style (preferably ~\cite{...}) throughout the paper.
- **[54dcc78d0b90]** Line length exceeds typical 80‑character limits in many LaTeX source lines (e.g., the long equations and paragraph blocks). Re‑wrap these lines for better version‑control readability.
- **[0ec4540cef36]** The \captionof{figure} command is used without loading the \usepackage{caption} package. Add \usepackage{caption} or replace the construct with a proper figure environment.
- **[254cb5549008]** Cross‑references are correct, but some \label commands appear after \captionof (in the teaser) rather than after \caption, which can affect reference ordering. Move \label immediately after \caption.
- **[d3afc512121a]** The bibliography uses \bibliographystyle{IEEEtran} but the document class is not shown; ensure that the chosen class is compatible with IEEEtran bibliography style or switch to a more generic style.
- **[6ed1258502ea]** Abstract contains a run‑on sentence and inconsistent punctuation; split enumerated items into separate clauses and add commas for clarity.
- **[37a3be7cd950]** Introduction mixes questions and statements without smooth transitions; rewrite to separate context setting from challenge enumeration.
- **[5f37f6b4da11]** Acronym density is high (KV, DMD, GR‑DMD, HGC, LGC); ensure each acronym is defined at first use in the main text and consider a glossary.
- **[5aa637ab2f33]** Table 1 lacks a self‑contained caption; add a concise caption directly beneath the table summarising its key result.
- **[5150dd23ae75]** Figure references are sometimes syntactically awkward; adopt a uniform style such as “Figure \ref{...} illustrates …”.
- **[e763b6928743]** Inconsistent spelling and hyphenation (e.g., “optimise” vs. “optimize”, “real‑time” vs. “real‑time”); choose one style guide and apply it throughout.
- **[afb25d5e3432]** Long equations (e.g., Eq. 3) are broken across lines without proper alignment; reformat using multiline environments with clear spacing.
- **[9dab43679944]** Conclusion repeats the abstract verbatim; rewrite to provide a synthesized discussion of findings and future work.
- **[fa66a7def5ae]** Sentences with dangling modifiers (e.g., “Garment KV Refresh: replace $KV^{\text{gar}}$ with $KV^{\text{gar}_{2}}$ derived from new garment.”) need clarification of the actor.
- **[df78432085a1]** Bibliography contains placeholder citations (e.g., \cite{#1}) that will not resolve; ensure all citation keys match entries in the .bib file.
