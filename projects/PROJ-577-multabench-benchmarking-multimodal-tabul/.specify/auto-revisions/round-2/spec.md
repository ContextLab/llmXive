# Revision Specification: Paper Science Revision — PROJ-577-multabench-benchmarking-multimodal-tabul round 2

**Generated**: 2026-06-14T12:40:16.203122+00:00
**Kind**: paper_science
**Project**: PROJ-577-multabench-benchmarking-multimodal-tabul
**Round**: 2

## Input

Address the following reviewer-raised action items:

- **[4a38088769e8] (severity: science)** Verify DINO-v3 citation: Cite simeoni_dinov3_2025 for DINO-v3-small. DINOv2 is the public standard; confirm DINOv3 exists and the citation accurately reflects the model used.
- **[fac48c5c759c] (severity: writing)** Refine GBDT comparison citation: The claim 'surpassing GBDTs' cites GBDT invention papers (e.g., breiman_random_2001). Cite the benchmark paper (erickson_tabarena_2025) for the performance comparison claim.
- **[5e22dacfb005] (severity: writing)** Explicitly list software dependencies (e.g., requirements.txt) in the repository and reference in the paper.
- **[b86986421547] (severity: writing)** Describe testing strategy (unit/integration tests) and coverage metrics in Appendix C or main text.
- **[cce87ef997dd] (severity: writing)** Include specific code commit hash or tag to ensure exact reproducibility of experimental results.
- **[5ccfcda4f405] (severity: science)** Clarify the licensing terms for the MulTaBench bundle. Explicitly confirm redistribution rights for source datasets (e.g., CheXpert, CBIS-DDSM) which often have restricted licenses.
- **[c5c264416b61] (severity: writing)** Replace the generic Kaggle profile link (https://www.kaggle.com/chico89/datasets) with a persistent archive link (e.g., Zenodo DOI or specific dataset collection URL) to prevent link rot.
- **[9b06806e6bfc] (severity: science)** Report the percentage of rows dropped due to missing/corrupt images or files during curation to ensure transparency on data loss.
- **[f6b95d3bc51e] (severity: writing)** Reconcile the contradiction between Section 5 ("Uploaded to Kaggle") and the Checklist ("upon acceptance"). Specify current availability status for reviewers.
- **[d4f903451d08] (severity: writing)** Consolidate redundant leaderboard figures (fig:leaderboard, fig:leaderboard_cls, fig:leaderboard_reg) to reduce visual clutter.
- **[cf015fbe8f18] (severity: writing)** Verify axis labels and units are legible at print scale in fig:compute_costs and fig:leaderboard.
- **[c3f366d4439c] (severity: writing)** Define all acronyms (LoRA, MMTL, HPO, CI, VLMs, GBDTs) at first use in the main text. Currently, LoRA (Sec 1), MMTL (Sec 1), HPO (Sec 5), VLMs (Sec 1), and GBDTs (Sec 1) are used without expansion. CI appears in Fig 5 caption without definition.
- **[fe7900086952] (severity: writing)** Replace field-specific jargon with plain English. 'SOTA' is used in Abstract and Sec 1 (should be 'state-of-the-art'). 'Learners' is used frequently (Sec 3, 5) where 'models' is preferred.
- **[174feec7f7ce] (severity: writing)** Standardize terminology spelling. 'finetune'/'finetuned'/'finetuning' is used throughout (Sec 1, 3, 5, App) instead of hyphenated 'fine-tune'.
- **[10ca4dc24329] (severity: writing)** Define 'ICL' (In-Context Learning) at first use. Used in Sec 2 ('non-ICL transformer') and Sec 5 ('violating ICL') without definition.
- **[bc558ee67307] (severity: writing)** Claim 'largest image-tabular benchmarking effort to date' needs verification. Cite specific prior benchmarks with dataset counts (e.g., MuG, TIME, MultimodalTabPFN) to justify superlative. Abstract and Introduction, lines 1-15.
- **[2a93acc9f453] (severity: writing)** Generalization claim 'gains generalize across learners, encoder scales, and dimensions' overstates scope. Only 5 learners, 2 encoder sizes (small/large), and 3 PCA dimensions tested. Qualify with 'across tested configurations' or expand evaluation. Section 5, lines 1-10.
- **[0a49bd34f892] (severity: science)** Curation pipeline circularity understated. Datasets selected where TAR already outperforms frozen, then TAR gains reported. 'Entangles problem with solution' in Discussion (line 385) insufficient. Need explicit statement that benchmark validates TAR on datasets pre-selected for TAR-sensitivity. Section 7, lines 380-390.
- **[4aac4e5a6849] (severity: writing)** Attention map analysis presented as mechanistic evidence for TAR gains, but correlation != causation. Qualitative figures (Fig 6) show attention shifts but don't quantify relationship to performance. Remove causal language or add quantitative analysis. Section 5.4, lines 1-15.
- **[590f07f2e3e3] (severity: writing)** Claims about healthcare/e-commerce 'high-impact domains' (Introduction) lack domain-specific evidence. No medical or e-commerce benchmarks show particular advantage over other domains. Either remove or provide domain-stratified analysis. Introduction, lines 30-35.
- **[252aa7cf3eb3] (severity: science)** Computational cost analysis shows TAR is 10x slower for text encoders (Appendix E2.3) but doesn't discuss cost-benefit tradeoff. For regression tasks with small gains (+0.018 mean), is TAR justified? Add cost-efficiency discussion. Section 6, lines 1-20.
- **[c959054b2f39] (severity: writing)** Expand the 'Broader impacts' section to explicitly discuss potential negative societal impacts, such as algorithmic bias in healthcare or financial decision-making, rather than only citing positive use cases.
- **[f48828bc226c] (severity: writing)** Clarify data provenance and consent status for datasets containing human faces (e.g., CelebA, Instagram-based datasets) to ensure compliance with privacy regulations and original licenses.
- **[0bd80b23ee55] (severity: writing)** Revise the 'Safeguards' checklist answer from 'NA' to discuss potential misuse risks of the benchmark, such as enabling discriminatory automated decision-making systems.
- **[3a475d49cb44] (severity: science)** The curation pipeline filters datasets based on TAR performance, creating circular bias. No analysis of datasets that passed Joint Signal but failed Task-awareness is provided to demonstrate the phenomenon is not algorithmically circular.
- **[86cc77d2ad4d] (severity: science)** Table in Appendix e001 reports mean gain (+0.022) without p-values or formal statistical significance tests (paired t-test or Wilcoxon). Confidence intervals are present but significance testing on aggregate improvement is still missing.
- **[b4f5365a5132] (severity: science)** For the image-tabular split, 15 of 20 datasets were manually curated from Kaggle. The specific selection criteria for these 15 additions are not documented, leaving reproducibility concerns about potential cherry-picking to favor TAR.
- **[d72f51263896] (severity: writing)** Specify CI calculation method (t-distribution for N=5 seeds) in Section 3.2 and Figure captions.
- **[0ffe63639f1d] (severity: science)** Add paired statistical tests (e.g., Wilcoxon) for TAR vs Frozen gains across datasets in Section 5.
- **[97f3a6b65dac] (severity: writing)** Clarify if regression R^2 is on binned labels or original values in Appendix A.1.
- **[b55a3ff889a4] (severity: science)** Quantify selection bias impact in Discussion (Section 7) regarding curation pipeline.
- **[ebed5604e2de] (severity: writing)** Inconsistent citation command usage persists: mix of \cite{}, \citet{}, \citep{} without clear style guide (e.g., \citet{van_breugel_position_2024} in e003, \citep{kim_carte_2024} in e000). Standardize to one format throughout.
- **[daf5b3ad272b] (severity: writing)** Table formatting inconsistency remains: some tables use \setlength{\tabcolsep}{4pt} and \small (tab:petfinder, tab:amazon_packages), others don't (tab:conditions, tab:win_rate). Apply uniform spacing/caption styling across all tables.
- **[e22a1ce69824] (severity: writing)** Cross-reference style inconsistency persists: use \S\ref{} in some places (e.g., \S\ref{app:curation_formal} in e000) but \ref{} in others (\ref{app:multabench}). Standardize section reference formatting.
- **[2a65486e2d3c] (severity: writing)** Figure placement specifiers still vary: [!t] (fig:curation_flow), [ht] (fig:curation_example, fig:text_pool_joint_tar), [htb] not used. Review and standardize for consistent document flow.
- **[9a1a1b28571e] (severity: writing)** \paragraph{} command usage remains inconsistent: some have trailing text on same line (\paragraph{Tabular Foundation Models.}), others start new paragraphs. Consider using \subsubsection{} for formal subsections or standardize \paragraph{} usage.
- **[d8a1d3b29990] (severity: writing)** Convert telegraphic fragments to full sentences in Sections 4, 5, 6, and 7 for better flow. Example: 'Rows: 400 to 114,000' should be 'The datasets contain between 400 and 114,000 rows.'
- **[2f8baeb803ac] (severity: writing)** Correct hyphenation of 'state of the art' to 'state-of-the-art' when used as an adjective (Introduction, Section 1).
- **[0291104400b0] (severity: writing)** Fix subject omission in Section 5: 'In PetFinder, suppresses background' lacks a clear subject (e.g., 'the model suppresses').


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 39 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
