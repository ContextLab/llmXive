# Automated-review action items — Geometry-Aware Representation Denoising for Robust Multi-view 3D Reconstruction

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Citations like 'wang2025vggt', 'tong2026scaling', and 'jang2026gld' refer to future years (2025-2026) or non-existent papers. Claims relying on these sources (e.g., RAEs, specific baselines) are unverifiable.
- **[writing]** The 'Depth Anything 3 (DA3)' benchmark is cited as 'depthanything3', but no such published benchmark exists (v2 is latest). All experimental results on this 'benchmark' are unsupported by verifiable evidence.
- **[writing]** Placeholder citations like '9506550', 'SNAVELY-IJCV08', 'sturmrichard', and 'panvisual' are used to support claims about robotics and multi-view reconstruction. These sources do not exist.
- **[writing]** Citations 'hidiff', 'instructir', and 'lingbot-depth2026' are non-standard and likely non-existent. Claims about these specific restoration models cannot be verified.
- **[writing]** References 'Youk_2024_CVPR', 'Edstedt_2024_CVPR', and 'Sun_2021_CVPR' use non-standard keys. The claims attributing specific video restoration capabilities to these works are unverified.
- **[writing]** The paper cites 'DBLP:journals/corr/abs-1905-03561' and 'DeTone_2018_CVPR_Workshops' as standard sources. These keys are malformed or refer to non-existent entries, undermining the literature review.
- **[writing]** Claims about 'SIR-Diff' operating in VAE spaces cite 'mao2025sir' (future year). Without a valid source, the comparison of latent spaces is factually unsupported.
- **[writing]** The paper claims 'RobustVGGT' handles distractors citing 'han2025emergent' (future year). This specific methodological claim cannot be verified against a published source.
- **[writing]** Citations 'an2024cross' and 'Jiang_2025' are used for multi-view reconstruction claims. These keys do not correspond to known, accessible publications, making the claims unverifiable.
- **[writing]** The paper relies on 'kingma2013auto' for VAE bottlenecks, which is valid, but pairs it with 'yao2025reconstruction' (future year) for RAE claims. The contrast is partially unsupported.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption ends abruptly with 'through [fig_architecture_copy_8.pdf]', indicating a broken sentence and a likely copy-paste error where the figure filename was pasted instead of the intended text.
- **[writing]** Figure 1: The mathematical notation in the caption contains a typo, writing the denoiser as '$S_()$' instead of '$S_{\theta}(\cdot)$' or similar, which does not match the label '$S_{\theta}(\cdot)$' shown in the diagram.
- **[writing]** Figure 2: The caption text is truncated at the end ('...restored images and consi'), cutting off the sentence and likely the figure filename.
- **[science]** Figure 2: The diagram labels the input as 'Degraded Images' and output as 'Restored Images & 3D Geometry', but the caption describes the method as operating on 'geometry-aware latent representations' and restoring 'intermediate representations', creating a disconnect between the visual pipeline and the textual description.
- **[writing]** Figure 3 caption: The phrase 'provided in Fig. of the supplementary material' is incomplete and missing the specific figure number.
- **[science]** Figure 3: The y-axis for the VAE method in panel (b) is broken and scaled differently (0.4–1.2) than the main plot (17–27), which obscures the true magnitude of performance differences and makes direct visual comparison difficult.
- **[science]** Figure 4: The caption claims to visualize 'top-down camera trajectories' for degraded inputs, but the plots show abstract 2D line graphs with no spatial context, axes, or units to verify they represent camera poses or trajectories.
- **[writing]** Figure 4: The legends inside the subplots are illegible due to low resolution, making it impossible to distinguish between the 'GARD' method and the baselines mentioned in the caption.
- **[science]** Figure 5: The caption claims to visualize 'reconstructed 3D point clouds', but the images display 2D RGB renderings of the scene (e.g., a bedroom and a fruit bowl) rather than explicit 3D geometry or point cloud data.
- **[writing]** Figure 5: The labels for the baseline methods (HI-Diff, InstructIR, MoCE-IR, Restormer, VRT, FMA-Net, VAE_MVD) are positioned above the image rows, but the layout is ambiguous regarding which specific images correspond to which method without explicit column headers or grid lines.
- **[writing]** Figure 7: The rendered image is a visual collage of results (labeled 'Degraded Views & Depths', 'Degraded 3D Point Cloud', etc.) rather than a schematic diagram of the 'GARD framework' described in the caption. The caption claims to describe the framework's mechanism (denoising on geometry-aware representations), but the figure only shows qualitative before/after examples without illustrating the architecture or data flow.
- **[science]** Figure 7: The figure lacks a legend or colorbar for the depth maps shown in the 'Degraded Views & Depths' and 'Restored Views & Depths' columns, making it impossible to interpret the quantitative depth values or verify the 'accurate 3D scene geometry' claim visually.
- **[science]** Figure 8: The caption claims to visualize the effect of attention alignment training, but the figure lacks a 'Before' vs. 'After' comparison or a baseline to demonstrate the specific effect of the training.
- **[writing]** Figure 8: The figure contains no internal labels, legends, or axis definitions to explain what the visual patterns (e.g., heatmaps or point clouds) represent, making the visualization unintelligible without external context.
- **[writing]** Figure 9: The caption text ('Visualization of target correspondence maps') is identical to the caption for Figure 8, suggesting a copy-paste error or missing specific description for the target maps shown.
- **[science]** Figure 9: The heatmap visualizations lack a colorbar or scale legend, making it impossible to interpret the magnitude of the correspondence values.
- **[writing]** Figure 10: The caption lists 'VAE', 'DINOv2', and 'DA3' as the methods being visualized, but the rendered image lacks row labels or a legend to identify which row corresponds to which method.
- **[writing]** Figure 10: The caption mentions 'Cross-view correspondence visualization' but does not define the column headers (e.g., 'Reference (query)', 'View 1', etc.) which are visible in the image but not described in the text.
- **[science]** Figure 11: The caption claims to show 'depth estimation results,' but the visualizations use a 'jet' colormap (blue-to-yellow) that is characteristic of normal maps or surface orientation rather than standard depth maps (which typically use a linear or log scale from near to far). Without a colorbar or explicit legend, the data representation is ambiguous and potentially misleading.
- **[writing]** Figure 11: The caption states 'three selected views out of ten input views,' but the figure displays a grid of 11 columns (Input Views, LQ, HI-Diff, InstructIR, MoCE-IR, Restormer, VRT, FMA-Net, VAEMVD, GARD (Ours), HQ). The caption fails to identify the methods shown in the intermediate columns, making it impossible to interpret the comparison.
- **[writing]** Figure 12: The caption text is truncated at the end ('...clean HQ repres'), cutting off the final word and citation.
- **[writing]** Figure 12: The y-axis label 'Cosine Similarity' is illegible due to low resolution.
- **[science]** Figure 12: The x-axis label 'Layer Index' is illegible; the specific layer numbers (14-40) are too small to read.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized acronyms and domain-specific metrics without providing definitions for a general computer vision audience. In Section 3.2, the term "PCK" is used to evaluate feature representations (Fig. 2) but is never defined. Similarly, in Section 4.1, the metrics "AUC5" and "AUC30" are presented in Table 1 without explaining that they refer to the Area Under the Curve for pose estimation at 5 and 30-degree thresholds. Section 5.3 introduces "AbsRel" and "$\delta_

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical consistency of the paper is generally strong, with a clear narrative arc from problem identification (degradation in feed-forward models) to solution (feature-space denoising). However, there are specific areas where the causal claims and experimental interpretations require tighter alignment. First, the interpretation of the ablation study in Section 5.1 regarding the "Attention Alignment Loss" contains a slight logical gap. The text states that alignment "does not consistently impr

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The paper exhibits significant overreach in its claims regarding the capabilities of the GARD framework and the limitations of existing baselines, which are not fully supported by the presented data. First, the central claim of "simultaneous recovery" of 3D geometry and high-quality RGB imagery is not substantiated. While the method proposes an RGB decoder, the experimental results (Tables 1, 2, and 3) focus exclusively on pose estimation, 3D reconstruction metrics (Overall, F-score), and depth

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper lacks a formal statement regarding Institutional Review Board (IRB) or ethics committee approval. While the datasets (Hypersim, TartanAir) appear synthetic, the authors must explicitly confirm that no human subjects were involved in data collection or annotation to satisfy standard safety and ethics review protocols.
- **[writing]** The 'Implementation Details' section (e002) mentions training on Hypersim and TartanAir but does not explicitly address data privacy or consent for any real-world data that might be included in these benchmarks. A statement confirming the datasets are publicly available and used in compliance with their respective licenses is required.
- **[writing]** The paper proposes a robust 3D reconstruction framework for autonomous navigation and robotics. While the primary application is beneficial, the authors should include a brief 'Dual-Use' or 'Broader Impact' discussion acknowledging potential risks, such as the technology being used for surveillance or unauthorized mapping of private spaces, and how the research mitigates these concerns.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The scientific evidence supporting the claim that GARD robustly handles multi-view degradation is currently insufficient due to gaps in the experimental design and ablation analysis. First, the ablation study in Table 1 (e001) presents a contradiction between the text and the data. The authors state that attention alignment yields "consistent performance gains" when combined with interpolated flow matching. However, the data shows that Model B (Alignment only) performs *worse* than the baseline

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** Table 2 (e001) claims attention alignment yields gains only with flow matching, yet Model B (Alignment only) underperforms Model A on ETH3D/DTU. The text lacks statistical justification (e.g., p-values) for ignoring this negative interaction or claiming consistency.
- **[science]** Tables 1-3 (e000, e001) report only point estimates (means) without standard deviations or confidence intervals. Given the stochastic nature of diffusion models and random view sampling, multiple runs are required to establish statistical significance of improvements.
- **[science]** Table 3 (e001) lists 30/50 views for HiRoom with dashes despite the text stating a 20-view limit. The sampling protocol for these entries is undefined, raising concerns about data comparability and statistical validity across view counts.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the sentence 'their attention mechanism encode cross-view information' contains a subject-verb agreement error. 'Mechanism' is singular and should be followed by 'encodes'. This appears in the first paragraph of the Introduction.
- **[writing]** In Section 3.1 (Task Formulation), the phrase 'consequently, applying S(·) independently' creates a comma splice. The word 'consequently' acts as a conjunctive adverb here and should be preceded by a semicolon or start a new sentence to fix the run-on structure.
- **[writing]** In Section 3.2 (GARD), the sentence 'From these restored features, four feature levels... are selected' is slightly ambiguous regarding whether the levels are selected from the restored features or if the features at those levels are selected. Rephrasing to 'Features at four specific levels... are selected from these restored representations' would improve clarity.
- **[writing]** In the Appendix (Section 'Implementation Details'), the caption for Figure 'fig_suppl_attn_target' repeats the phrase 'We visualize the effect of attention alignment training' which is identical to the caption for 'fig_suppl_attn'. While the content differs, the captions lack distinctiveness and should be rewritten to specifically describe the target maps versus the learned attention maps.
