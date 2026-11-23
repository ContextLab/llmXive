# Revision Specification: Paper Science Revision — PROJ-636-locateanything-fast-and-high-quality-vis round 1

**Generated**: 2026-06-14T15:36:55.942437+00:00
**Kind**: paper_science
**Project**: PROJ-636-locateanything-fast-and-high-quality-vis
**Round**: 1

## Input

Address the following reviewer-raised action items:

- **[c22c05a96b42] (severity: writing)** Define 'high-quality' grounding in the Abstract and Introduction using specific metrics (e.g., IoU thresholds, F1-mIoU) rather than qualitative claims to align with the title's promise.
- **[4351b2492daf] (severity: writing)** Ensure the Supplementary Materials include the exact data mixing weights and hyperparameters for the Stage-3 and Stage-4 SFT to guarantee full reproducibility.
- **[2f236bdb3b01] (severity: writing)** Clarify Rex-Omni's coordinate representation in the Introduction (Lines 35-40) to align with Related Work (Lines 25-27), which describes it as 'point-based prediction' rather than box-coordinate token serialization.
- **[6d17cee8bbf4] (severity: writing)** Harmonize dataset size reporting between the Abstract (138M), Section 3.4 (138M), and Supplementary Table `query_stats` (~139.5M) for consistency.
- **[658aee1e038c] (severity: writing)** Ensure the linked GitHub repository includes a pinned requirements.txt or pyproject.toml to guarantee dependency reproducibility.
- **[a7761e2979b8] (severity: science)** Add a tests/ directory with unit tests for the attention mask logic and block-based output parsing described in Section 3.
- **[8f4b6d468d5c] (severity: writing)** Provide documentation on code modularity (e.g., separation of training loops, model definitions) to support the 'High-Quality' claim.
- **[f42df2cb017e] (severity: science)** Explicitly state the license for LocateAnything-Data in the main text or supplementary, given the aggregation of diverse source datasets (e.g., Unsplash, OpenImages) and synthetic generation via Qwen3-VL.
- **[15cff7cc08e6] (severity: writing)** Correct the GitHub link in main.tex (currently points to 'Eagle/Embodied') to accurately reflect the LocateAnything code/data repository, or provide a direct dataset download link.
- **[48c3f4514621] (severity: science)** Provide a version identifier or hash for the 138M-sample LocateAnything-Data to ensure reproducibility and data provenance tracking.
- **[1eea0a24403a] (severity: writing)** Document the raw dataset schema (e.g., JSON/Parquet structure) for LocateAnything-Data in the supplementary, distinct from the model token schema described in sec/3_0_method.tex.
- **[adc01ef00bc9] (severity: writing)** Correct filename typo in supplementary: `categroy-per-query.pdf` should be `category-per-query.pdf` (sec/X_0_suppl.tex).
- **[b23a771adbf6] (severity: writing)** Verify color definitions: `lightblue` is defined as RGB(0.46,0.73,0.00) which is green; rename or redefine to avoid confusion in tables/figures.
- **[17613fd0b1a9] (severity: writing)** Ensure Red/Green color scheme in Fig. 7 (vis_cases.pdf) is distinguishable for colorblind readers; consider adding patterns or shapes.
- **[356c9a57ad63] (severity: writing)** Confirm text legibility in Fig. 1 (teaser.pdf) bottom panel at print scale; small coordinate tokens may blur.
- **[fb1ae8e60848] (severity: writing)** Expand 'SFT' to 'supervised fine-tuning' at first use in the supplementary material (sec/X_0_suppl.tex).
- **[8a803a9e13b3] (severity: writing)** Define 'KV-caching' as 'Key-Value (KV) caching' upon first appearance in sec/3_0_method.tex.
- **[ba2b2d2f99d6] (severity: writing)** Replace 'SOTA' with 'state-of-the-art' throughout the manuscript for clarity.
- **[9116459ae4f6] (severity: writing)** Expand 'MLP' to 'multilayer perceptron' when first introduced in sec/3_0_method.tex.
- **[7a79732955e5] (severity: writing)** Define 'GUI' as 'graphical user interface' at first mention in sec/1_intro.tex.
- **[b7c72950d22b] (severity: writing)** Expand 'BF16' to 'bfloat16' in sec/X_0_suppl.tex.
- **[29185d1fd512] (severity: writing)** Abstract states 138M training samples, while Supplementary Sec:Data Statistics reports 139M queries. Align these figures for internal consistency.
- **[6178b7a7e090] (severity: writing)** Abstract claims PBD improves throughput, but Ablation Tab:combined_ablation (a) shows PBD (Slow) throughput equals Quantized (3.9 BPS). Clarify if the throughput claim applies specifically to Fast/Hybrid modes.
- **[bf099105ddcb] (severity: writing)** Main text (Sec 4.0) reports Hybrid throughput as 12.7 BPS, while Ablation Tab:combined_ablation (c) reports 13.2 BPS. Resolve this numerical inconsistency.
- **[f88c715a3932] (severity: writing)** Temper the claim that LocateAnything universally advances the speed‑accuracy frontier; provide per‑task analyses showing where it under‑performs (e.g., OCR on HierText, certain GUI categories) and adjust language accordingly.
- **[63c1af5f1262] (severity: science)** Add an ablation that isolates the impact of the 138 M LocateAnything‑Data from the Parallel Box Decoding (PBD) contribution to substantiate the claim that both jointly improve performance.
- **[d697d8da1619] (severity: writing)** Provide empirical evidence (e.g., latency measurements on an embedded device or robot) to support the statement that the method enables deployment in latency‑sensitive embodied systems, or revise the claim to be more modest.
- **[793091e74160] (severity: science)** Discuss the frequency and performance impact of Hybrid Mode fallbacks; if fallback occurs often, the claimed speedup may be overstated.
- **[81894465cdb6] (severity: science)** Include a broader evaluation of backbone generality beyond Qwen3‑VL‑4B (e.g., other encoder‑decoder architectures) to back the claim that PBD is backbone‑agnostic.
- **[39a5752c1768] (severity: writing)** Include a Data Privacy statement detailing how PII (e.g., faces, license plates) was handled in the 138M-sample LocateAnything-Data, particularly given the use of Unsplash and SA-1B (supp/data.tex).
- **[35645e73906c] (severity: writing)** Add a discussion on dual-use risks, specifically regarding GUI grounding capabilities enabling autonomous agents that could be misused for unauthorized access or surveillance (sec/1_intro.tex).
- **[569d5236ba04] (severity: writing)** Clarify license compliance for the aggregated dataset and provide usage policies for the released model on HuggingFace (sec/0_abstract.tex).
- **[6e06a1e2b1f5] (severity: science)** Report fallback frequency for Hybrid Mode. Throughput drops from 16.9 BPS (Fast) to 13.2 BPS (Hybrid) in ablations; without knowing how often fallback occurs in dense scenes, the speed advantage is unquantified.
- **[12aeb1ff6721] (severity: science)** Disclose dataset quality control metrics. The 138M samples are verified by teacher VLMs (Qwen3-VL, Rex-Omni) without human validation. Provide rejection rates or spot-check accuracy to support the "high-quality" claim.
- **[30d799ce7218] (severity: science)** Report standard deviation or confidence intervals for all reported F1 and BPS metrics to quantify variability.
- **[fb8acede9d0b] (severity: science)** Specify the number of random seeds used for training and evaluation in the main results and ablation studies.
- **[fc7e92a0ee22] (severity: writing)** Clarify the statistical significance tests supporting claims of 'significantly higher' throughput and accuracy.
- **[f4ef00ef3370] (severity: writing)** Fix LaTeX compilation errors: The tables use \rowcolor (e.g., tables/common_object_detection.tex), but packages.tex loads xcolor without the 'table' option. Add \usepackage[table]{xcolor} or load colortbl.
- **[713115b1dd25] (severity: writing)** Define undefined color 'nvidiagreen' in main.tex or update \hypersetup{urlcolor} to use a defined color like MyGreen to prevent warnings.
- **[ddc15668b077] (severity: writing)** Standardize citation commands: supp/data.tex uses \cite while the rest of the manuscript uses \citep. Align all to \citep for consistency with natbib configuration.
- **[7fd086c266fa] (severity: writing)** Correct typos in cross-reference labels: 'tab:gui_grounidng' (tables/gui_grounding.tex) and 'fig:categroy-per-query' (sec/X_0_suppl.tex) contain spelling errors.
- **[6b8486cf1e0b] (severity: writing)** Standardize section heading hierarchy: Section 2 (sec/2_related_works.tex) uses inline \textbf{} for subheadings, while Section 3 uses \subsection. Use \subsection throughout for structural consistency.
- **[4c0d959b659a] (severity: writing)** Correct the typo 'grounidng' to 'grounding' in Section 4.0 ('Main Results', paragraph 'Precise Open-World Localization Ability') and update the corresponding label in tables/gui_grounding.tex.
- **[e27dcfca2b92] (severity: writing)** Remove redundant phrasing in the Acknowledgements section (Section 5). The phrase 'would like to additionally acknowledge' is repetitive after 'We would also like to thank'. Simplify for conciseness.


## Success Criterion

After the implementer applies this revision, the project returns to
``paper_review`` and the per-specialist re-review protocol confirms
each of the 44 action item(s) above as ADEQUATELY ADDRESSED.

## Out of scope

- New experiments not directly required by a ``science``-severity item above.
- Refactors / cleanups not required by an action item.
