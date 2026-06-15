---
field: other
submitter: github-actions[bot]
github_issue: https://github.com/ContextLab/llmXive/issues/277
---

# https://arxiv.org/abs/2606.02800

A paper was submitted via the website for consideration / review.

Source URL: https://arxiv.org/abs/2606.02800

Submitted by: github-actions[bot]

(Intake from human-submission issue #277.)

## Rejection rationale (2026-06-15)

Paper-stage review found one or more `fatal`-severity action items. The underlying research question is returned to the backlog so a fresh approach can be considered:

- **[ce59fcdeb776]** Clarify model parameter counts. Abstract claims 16B (Nano) and 64B (Super), but Table 1 suggests ~8B and ~23B for dense architectures. Specify if MoE is used and list expert counts to support the claimed parameter sizes.
- **[c1b5293bdcff]** Qualify state-of-the-art claim. Abstract states SOTA on understanding and generation tasks, but Table 2 shows Gemini 3.1 Pro outperforms Cosmos 3 on General Reasoning (77.5 vs 73.7). Restrict SOTA claim to open-source or Physical AI domains.
- **[a36ab3373b22]** Verify Wan citation specificity. Text cites Wan2.2-TI2V-5B but bibliography entry wan2025 lacks version details. Update bib title or text to ensure alignment.
- **[bff077e62400]** Code artifacts (training scripts, inference code, test suites, dependency files) are external to the paper submission at github.com/nvidia/cosmos. Cannot evaluate code quality, modularity, tests, or reproducibility without access to actual implementation.
- **[f98e7d5e1227]** Data provenance lacks version identifiers for external datasets (e.g., DROID, BEHAVIOR-1K, CARLA). Add dataset version numbers or commit hashes to enable reproducibility.
- **[75d2dd59466b]** OpenMDW-1.1 license restricts redistribution; clarify whether raw training data is available under this license or only processed/filtered versions.
- **[54d312be6560]** External URLs (HuggingFace, GitHub) lack archival snapshots; add DOI or archive.org references to prevent link rot.
- **[d8262269f5c2]** Data filtering statistics (4.23% deduplication, 78%/46% retention at thresholds) lack breakdown by modality; add per-modality filtering metrics.
- **[274a349b7324]** Synthetic dataset schemas (SDG-PhyxSim, SDG-RobotSim, etc.) lack formal schema versioning; add JSON Schema references or version tags.
- **[3733594b1080]** Add accessibility alt-text attributes to all \\includegraphics commands to support screen readers and print fallback.
- **[fa85fa27c130]** Verify axis label font sizes in figure\\ref{fig:cosmos3_serving_latency_combined} and figure\\ref{fig:sdg_pretrain_umap} for legibility at 100% print scale.
- **[6049d5a83b8e]** Convert leaderboard screenshot figures (e.g., figure\\ref{fig:sft_t2i_aa_leaderboard}) to vectorized tables or high-DPI PDFs to ensure text clarity.
- **[36717943992e]** Define 'Physical AI' and 'Omnimodal' more explicitly in Section 1 for non-specialist readers.
- **[4af59a60d17f]** Expand acronyms like 'AR', 'DM', 'FD', 'ID' at first use in Section 2 and avoid reusing them without context.
- **[9452dfda511e]** Replace 'SFT' with 'Supervised Fine-Tuning' throughout Section 3 and 4 to reduce acronym density.
- **[eb5b16f8b607]** Simplify infrastructure jargon (e.g., 'SILA', 'HSDP', 'IVF_PQ') in Section 5 with brief parenthetical explanations.
- **[d09ad0b9cfd1]** Clarify the relationship between Reasoner sample counts (24.2M, Sec 4.1) and Generator sample counts (1.1B+, Sec 4.2) given identical token counts (31T/17T, Sec 5.1/5.2). Explain mixing ratio or token density assumptions.
- **[e5b9950b94cf]** Reconcile Action Token definition (DM tower, Sec 2.2) with Reasoner Action CoT data (Sec 4). Clarify if Reasoner outputs language plans or raw action tokens to avoid architectural contradiction.
- **[7d70eba0d69c]** Align Abstract claim ("ranking best... on robot policy") with Table 1 (Cosmos3-Super Policy = "-"). Specify that the policy benchmark result applies to the Nano variant to prevent misinterpretation of the flagship model's capabilities.
- **[fd061c9c2fd9]** Clarify SOTA claims to distinguish between base model and post-trained variants; many results marked with * are from specialized fine-tuned models, not the base Cosmos 3.
- **[f388693f1bf4]** Resolve contradiction between Introduction claim of 'training-environment creation' capability and Figure 2 caption stating this is 'future work'.
- **[121f7b051304]** Add limitations section discussing action tokenization generalization, long-horizon video consistency, and generalization to unseen domains beyond synthetic datasets.
- **[0e2c6dcb2785]** Clarify benchmark comparison protocols when comparing against closed models (Gemini 3.1 Pro, Veo-3.1) to ensure fair evaluation.
- **[39c659cb8312]** Provide quantitative evidence for claims that 'Post-training improves synthetic data quality' rather than relying on qualitative descriptions of SDG datasets.
- **[d1a319a08136]** Clarify IRB/ethics approval status for the healthcare robotic surgery dataset (2.2M images, 398K conversations) described in Section e001. Patient consent and HIPAA compliance are not mentioned.
- **[e50f6def40c2]** Detail consent procedures and compensation for human annotators who provided dense temporal captions for egocentric videos (Section e001).
- **[36a84edfa0b6]** Specify restrictions in the OpenMDW-1.1 License regarding dual-use risks (e.g., autonomous weapons, surveillance) given the release of open weights for robotics and AV (Abstract, Section e000).
- **[bc6c837e9b0d]** Provide technical verification of PII blurring effectiveness for the 5.6M pedestrian bounding boxes in the Smart Infrastructure dataset (Section e001).
- **[3ada297f99ec]** Report standard deviations or confidence intervals for all benchmark scores where multiple seeds were used (e.g., PAIBench-G, Cosmos-HUE) to establish statistical significance.
- **[f8e3083c5ec3]** Explicitly confirm the independence of internal benchmarks (Cosmos-HUE, PAIBench-G) from training data to rule out data leakage or overfitting.
- **[be12676200e3]** Provide a breakdown of real-world vs. synthetic data performance on robotics benchmarks (e.g., RoboLab) to validate generalization claims for Physical AI tasks.
- **[51a56c876107]** Report standard deviations or confidence intervals for all benchmark scores (e.g., Tables 5, 6, 7) to validate statistical significance of SOTA claims.
- **[aaf743c0852b]** Specify the number of random seeds used for generation tasks and clarify Best-of-N selection parameters in Table 10.
- **[2868a309d936]** Address multiple-comparisons correction for the 48 reasoning benchmarks to control Type I error inflation.
- **[c450e9ab9ec7]** In Appendix (e006), the \caption command appears outside a float environment. Wrap the \input{figures/...} and subsequent \caption/\label in a \begin{figure}...\end{figure} block.
- **[5a9a9bba96fb]** Inconsistent label naming convention: use sec::intro (e000) vs tab:results_overview (e000). Standardize to one style (e.g., underscores) across all sections/tables/figures.
- **[0a1a11e022a6]** Section hierarchy skip in e001: \section{Temporal and Motion Data} is immediately followed by \paragraph{Action CoT.}. Insert a \subsection or \subsubsection level for proper hierarchy.
- **[0fb9633e3a02]** Ensure all non-standard packages (tcolorbox, tasks, cleveref, placeins, subcaption) are explicitly declared in the preamble to guarantee compilation hygiene.
- **[45aadb2290e5]** Standardize cross-referencing style. Some sections use \cref (e.g., Section 2, e000) while others use 'Figure~\ref' (e.g., Section 5, e002). Choose one consistent method.
- **[3555ead90107]** Unify spelling conventions. The text predominantly uses American English ('modeling'), but 'summarises' appears in Section 5.1 (e002). Align all to one dialect.
- **[2710f7662639]** Ensure consistent capitalization in figure captions. Example: 'Joint Data-Loader' (Fig 4, e002) vs 'Joint data loader' (text). Apply title case or sentence case uniformly.
- **[a0b9dd72382a]** Document or replace custom LaTeX commands. The contributors section (e006) uses undefined commands like \task and \begin{tasks}. Ensure these are defined in the preamble.
- **[1b9c017781d6]** Verify hyphenation consistency for compound adjectives (e.g., 'open-source' vs 'open source', 'state-of-the-art'). Ensure uniform usage throughout the manuscript.
