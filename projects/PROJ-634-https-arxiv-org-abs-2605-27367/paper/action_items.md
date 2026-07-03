# Automated-review action items — SpatialBench: Is Your Spatial Foundation Model an All-Round Player?

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a comprehensive benchmark and a new model, but several factual claims regarding the scope of evaluation and the calculation of reported metrics are slightly overstated or ambiguous. First, the Introduction states the benchmark evaluates "41 models," while the text in Section 5.2 and the main results table (Table 1) clarify that there are "31 methods" with "41 variants." This distinction is important for reproducibility and accurate comparison; the claim should be refined to "4

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption states 'Colored cells report the per-domain ranking', but the heatmap contains both colored cells with numbers and black cells with dots. The caption fails to define the meaning of the black cells (e.g., whether they represent 'not ranked', 'did not run', or 'no data'), making the visualization ambiguous.
- **[writing]** Figure 1: The top legend bar uses colored blocks to group methods (e.g., blue for VGGT, green for DA3), but the specific method names in the header are not clearly aligned with these color blocks, and the legend does not explicitly map the colors to the method names below them.
- **[writing]** Figure 2: The caption states 'Colored cells report the per-domain ranking', but the image shows a single large table with no visual distinction or separation for the 'Sparse' regime mentioned in the title; it appears identical to the dense regime table, making the specific 'Sparse' context unverifiable.
- **[writing]** Figure 2: The top legend bar contains colored blocks for methods (e.g., VGGT, DA3-Giant) but lacks text labels directly under the blocks, relying on the user to map colors to the column headers below, which is visually cluttered and indirect.
- **[writing]** Figure 3: The top legend bar contains colored blocks for methods (e.g., VGGT, DA3-Giant) but lacks text labels directly under the blocks; the method names are only visible in the first row of the grid, making the legend incomplete on its own.
- **[writing]** Figure 3: The caption states 'Colored cells report the per-domain ranking', but the cells contain numbers (1-9) without a legend or colorbar explaining the ranking scale (e.g., does 1 mean best or worst?).
- **[science]** Figure 4: The caption states 'Empty cells indicate that the method runs out of memory', but the figure shows empty cells (e.g., in the 'G1 — INDOOR' section) containing dashed outlines or dots, which contradicts the definition of 'empty' and makes it unclear if these are OOM failures or missing data.
- **[writing]** Figure 4: The top legend labels (e.g., 'VGCT', 'DA3-Giant') are extremely small and blurry, making them illegible and difficult to map to the corresponding columns.
- **[science]** Figure 5: The caption claims to show 'depth/camera metrics' for the scenes, but the rendered image contains no numerical metrics, tables, or text annotations reporting these values.
- **[science]** Figure 5: The 'GT Point Cloud' for the second scene (outdoor driving) is labeled 'N/A', yet the caption describes this as a 'dense outdoor driving' case, implying a ground truth should be available for comparison.
- **[science]** Figure 6: The caption claims to visualize 'DA3-Giant', but the bar charts label the method as 'DA3-Giant (w/ Cam)', while the 3D visualizations are labeled simply 'DA3'. This creates ambiguity about whether the visualized results include the depth prior mentioned in the caption.
- **[writing]** Figure 6: The dataset titles in the right-hand bar charts (e.g., 'robotwin_franka-panda-1_stack_blocks_two_episode44_sparse') are truncated or poorly formatted, making it difficult to identify the specific scenes being evaluated.
- **[science]** Figure 7: The caption claims to show 'DA3-Giant', but the bar charts list 'DA3' (and 'DA3-Giant' in other figures), creating ambiguity about whether the specific 'Giant' variant is being evaluated or if the label is truncated.
- **[writing]** Figure 7: The 'Multi-view Input' column is unlabeled; while the caption mentions 'input views', the column header is missing, making the layout less self-explanatory compared to the method columns.
- **[science]** Figure 8: The caption claims to show 'DA3-Giant, MapAnything, OmniVGGT, Pi3, and WorldMirror', but the visualizations only show DA3, MapAnything, OmniVGGT, Pi3-X, and WorldMirror. The 'Giant' variant is missing from the visual grid.
- **[science]** Figure 8: The rightmost bar chart for the bottom scene ('lingbot...') only displays 'depth abs_rel' metrics. The caption states that the right panel reports both 'depth AbsRel and camera AUC@30', but the camera metric is missing for this specific case.
- **[writing]** Figure 8: The title of the bottom-right bar chart is split across two lines ('lingbot_RobbyReal_00009_07_overpass_passage_si' / 'ngle'), making the scene identifier difficult to read.
- **[science]** Figure 9: The caption claims to visualize failure cases of MapAnything, WorldMirror, and OmniVGGT, but the rendered image displays a grid of successful reconstructions (MapAnything, WorldMirror, OmniVGGT) compared against 'Ground Truth Point Cloud' across three scenes, contradicting the 'Failure Cases' title.
- **[writing]** Figure 9: The image contains no figure number or title text; the caption 'Figure 9: Failure Cases...' is external to the rendered image, making the figure standalone ambiguous.
- **[science]** Figure 10: The caption claims to compare 'annotations from OmniWorld' against 'reconstructed point clouds', but the 'OmniWorld' column displays sparse, noisy point clouds that visually resemble the 'DA-Next-5M w/ Init Cam Poses' output rather than clean ground-truth annotations, making the comparison misleading.
- **[writing]** Figure 10: The column headers 'DA-Next-5M w/ Init Cam Poses' and 'DA-Next-5M w/ Refined Cam Poses' are repetitive and cluttered; consider using a shared row label or a cleaner legend to distinguish the methods.
- **[writing]** Figure 11: The caption 'DROID Gallery 1' is insufficient for a standalone figure; it fails to describe the content (e.g., input views, 3D reconstructions, timestamps) or the specific scenes shown, making the figure unintelligible without external context.
- **[science]** Figure 11: The figure displays eight distinct scenes with timestamps but lacks any quantitative metrics, error bars, or comparative baselines, rendering it purely illustrative and unable to support scientific claims about model performance.
- **[writing]** Figure 12: The caption 'DROID Gallery 2' is insufficient for a standalone figure; it fails to describe the visual content (e.g., input views, segmentation masks, 3D point clouds) or the specific scenes shown, making the figure unintelligible without the main text.
- **[science]** Figure 12: The figure displays eight distinct scene examples (labeled 9-16) but lacks any visual legend or colorbar to explain the meaning of the colors in the segmentation masks or the point cloud reconstructions.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 1 (Introduction) uses the term *Full‑Context Attention* without definition; add a brief explanation (e.g., “Full‑Context Attention refers to attention mechanisms that jointly attend to all input frames simultaneously, providing global context”).
- **[writing]** The phrase *Bounded‑memory models* appears in the introduction and results but is never explained; define it when first used (e.g., “models that limit memory usage by processing inputs in chunks or using a fixed‑size cache”).
- **[writing]** The abbreviation *GT* (ground truth) is used throughout the paper (e.g., “GT depth/pose priors”) without an explicit definition; introduce the full form at first occurrence.
- **[writing]** The term *pseudo‑GT* is introduced in the abstract and later (e.g., “curated pseudo‑GT outperforms noisy scaling”) without clarification; explain what pseudo‑GT means (e.g., “high‑quality depth generated by a teacher model and treated as ground‑truth for training”).
- **[writing]** In the model architecture (Section 4.2) the concept of *scale tokens* is mentioned but not described; add a short description of their role (e.g., “learnable tokens that predict a global metric scale for the scene”).
- **[writing]** Tables contain the abbreviation *OOM* (out‑of‑memory) without a legend; add a footnote or caption note defining OOM for readers.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper's argument structure is generally sound, with clear premises leading to conclusions about model performance and benchmark gaps. However, there are specific inconsistencies between the textual claims and the provided data tables that break the logical chain of evidence. First, in Section 5.2, the text explicitly states: "removing the attention-gating module causes the largest performance drop (−8.1 pts)." This conclusion is presented as a direct derivation from the ablation study. Howev

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Title/Abstract claim 'all-round' evaluation, but Table 1 shows 30+ models OOM in the 'Dense' regime. The benchmark cannot test dense scalability for most models. Narrow the claim to 'evaluating robustness under hardware constraints' or acknowledge the dense regime's limited coverage.
- **[writing]** Abstract claims 'egocentric/wrist-view are dominant OOD failures' as a general fact. Evidence is limited to the 19 benchmark datasets. Add a qualifier: 'dominant failures within the tested distribution' or test on external real-world streams to support the universal claim.
- **[writing]** Conclusion states models are 'not all-round players' due to dense failures. However, these failures are often OOM (hardware limits), not algorithmic inability. Rephrase to 'models fail to scale to dense inputs under current hardware constraints' to match the evidence.
- **[writing]** Section 5 claims 'Data quality outweighs volume' based on DA3 vs. others. This conflates data with architecture. Soften to 'In our experiments, curated data correlated with better performance, suggesting quality is critical' to avoid overgeneralizing causality.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a benchmark (SpatialBench) and a new model (Depth-Anything-Next) for spatial foundation models. The work aggregates 19 existing public datasets (e.g., ScanNet, KITTI, Waymo, CO3D) and introduces a new curated dataset (\dataset) derived from public sources (Xperience, ADT, HOI4D, RLBench, etc.).

From a safety and ethics perspective, the paper is low-risk:
1.  **Data Provenance:** The paper explicitly lists the source datasets and their licenses in Appendix (Table \ref{tab:dataset_profile_summary_cited} and surrounding text), noting "Non-Commercial" or specific CC licenses (e.g., CC BY-NC 4.0) for several sources. There is no indication of scraping data in violation of Terms of Service (ToS) or using private/PII-containing data without consent. The new dataset is constructed from these public sources with standard post-processing (depth refinement, masking).
2.  **Dual-Use:** The capabilities evaluated (depth estimation, camera pose, 3D reconstruction) are standard computer vision tasks. While these can theoretically be used in robotics or surveillance, the paper does not introduce a novel capability that significantly lowers the barrier to harm (e.g., automated vulnerability discovery, persuasive disinformation, or biological synthesis). The "dual-use" risk is generic to the field and does not require specific mitigation beyond standard responsible AI practices, which are not explicitly demanded for this type of benchmark paper.
3.  **Human Subjects:** The datasets used are either synthetic or public, anonymized real-world collections (e.g., driving scenes, indoor scans). No new human-subjects experiments, surveys, or collection of personally identifiable information (PII) are described. Therefore, no IRB/ethics statement is required for new data collection.
4.  **Vulnerabilities:** The paper does not report security vulnerabilities in live systems or provide operational details for cyber-attacks.

No specific, nameable safety or ethical gaps were found. The paper does not release PII, does not violate known licenses (it cites them), and does not propose a harmful system. The verdict is `accept` with no action items.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a comprehensive benchmark (SpatialBench) and a new model (Depth-Anything-Next, \ours), but the experimental design contains significant confounds that prevent the evidence from fully supporting the specific claims about architectural superiority and data quality. First, the headline claim that \ours achieves +47% to +59% depth gains over DA3-Giant (Table 1) is confounded by training data. The paper states \ours was trained on a new, curated dataset (\dataset) specifically desi

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 1 and Appendix tables report single-point metrics (e.g., AbsRel 0.050) for 41 models without any measure of variance (SD, SE, or range). In deep learning, results vary by seed; reporting a single run as the definitive score implies false precision. Report mean ± SD over ≥3 seeds for all key comparisons, or explicitly state results are from a single seed.
- **[writing]** The abstract and Section 5 claim the proposed method is '+47% / +59% depth gains' over DA3-Giant. These are point estimates with no confidence intervals or statistical tests (e.g., paired t-test or bootstrap) to determine if the improvement is significant or within run-to-run variance. Add a statistical test or report the variance across seeds to support the magnitude of the gain.
- **[science]** Table 1 compares 41 models across 4 regimes and multiple metrics (effectively >100 pairwise comparisons). The paper highlights 'best' results with color coding but applies no correction for multiple comparisons (e.g., Bonferroni, Holm, or FDR). Without correction, the probability of false positives (highlighting a model as 'best' by chance) is high. Apply a correction or explicitly acknowledge the multiplicity risk.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured, but several sections suffer from abrupt transitions and missing topic sentences that force the reader to infer the logical connection between ideas. In the Introduction, the final paragraph abruptly introduces the new dataset (\dataset) and model (\ours) immediately after listing benchmark insights. While the content is relevant, the lack of a bridging sentence makes the shift from "what we found" to "what we built" feel disjointed. A simple transition phr
