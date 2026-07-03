# Automated-review action items — Cosmos 3: Omnimodal World Models for Physical AI

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 3.1 claims pre-training is dominated by image-text (18.8M) and text-only (2.2M), but Table 1 shows video-text adds ~1M, making the sum 21M, not 22M. Reconcile the text summary with the table totals.
- **[writing]** Section 4.1 claims Cosmos 3 outperforms Cosmos-Reason2 due to '20% more pre-training data,' but the paper does not state Cosmos-Reason2's data volume. Cite the baseline count or remove the specific percentage.
- **[writing]** Section 5.2 claims 'state-of-the-art' in I2V (48.9) while Table 3 lists Sora2 (closed) at 46.4. Clarify if 'SOTA' refers strictly to open-source models to avoid ambiguity regarding closed baselines.
- **[writing]** Section 5.3 claims Cosmos3-Super achieves 'new state-of-the-art' in action generation, but Table 5 shows Cosmos3-Nano wins on RRE and ties on RTE. Specify which metric (ATE) drives this claim for precision.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The figure has no caption (labeled '(no caption)'), making it impossible to verify if the chart supports the claims it is cited for or to understand the context of the 'Action Data Distribution'.
- **[science]** Figure 1: The donut chart displays a total of 61.3K hours, but the sum of the visible percentages (67.4% + 16.3% + 8.7% + 7.5%) equals 99.9%, leaving a small unexplained gap or rounding error without a legend entry for 'Other' or 'Uncategorized'.
- **[writing]** Figure 2: The caption describes 'view-layout metadata' and 'structured JSON prompt' to associate pixel regions with camera streams, but the image contains no visible JSON, text overlays, or layout markers to demonstrate this formatting.
- **[writing]** Figure 2: The image displays three distinct camera views (one close-up, two wide-angle) but lacks labels or arrows to identify which specific viewpoint corresponds to which part of the 'concatenated canvas' described in the caption.
- **[writing]** Figure 3: The caption states that gray cells (---) indicate a mode is not active, but the rendered figure uses empty white cells for these entries, creating a visual mismatch between the description and the image.
- **[writing]** Figure 3: The caption mentions 'The video row' covers multiple modalities, but the figure labels this row 'Text-to-(Video+Audio)' and 'Image-to-(Video+Audio)', which is a confusing and inconsistent naming convention compared to the caption's description.
- **[science]** Figure 4: The caption states the figure summarizes data across 'pre-training and supervised fine-tuning stages' with 'each ring showing the relative contribution,' but the rendered image displays only a single ring labeled '22.0M samples' (pre-training). The 2.2M supervised fine-tuning samples and the second ring described in the caption are missing.
- **[science]** Figure 5: The caption claims 'Eight representative driving scenarios are provided,' but the image displays only a single static frame of one collision scenario. This discrepancy misleads the reader regarding the figure's content.
- **[writing]** Figure 5: The caption states the dataset covers 'long-tail, rare scenarios,' but the image shows a generic intersection collision without specific context or labels explaining why this specific instance is considered a rare or long-tail event.
- **[fatal]** Figure 6: The rendered image displays a single RGB frame of a wrecking ball scene, but the caption claims it shows five panels (RGB, center-of-mass displacement, cumulative rotation, linear velocity, and angular velocity) arranged from left to right. The visual content does not match the description.
- **[writing]** Figure 7: The figure has no caption (labeled '(no caption)'), making it impossible to verify what the UMAP plot represents, what the colored clusters correspond to, or the context of the 'Pretrain data' baseline.
- **[science]** Figure 7: The legend lists specific datasets (SDG-DriveSim, SDG-PhyxSim, etc.) but the plot shows a massive, undefined gray cloud labeled 'Pretrain data' without explaining its source or relationship to the colored clusters, limiting interpretability.
- **[writing]** Figure 8: The row label 'Collison' is misspelled and should be 'Collision' to match the caption and standard English.
- **[science]** Figure 8: The percentages listed above the robot images (e.g., 'Unitree G1 (44.47%)') are undefined; the caption does not explain if these represent the proportion of clips within that category or the total dataset.
- **[science]** Figure 9: The caption claims to show 'RGB, depth; exterior and interior views' from left to right, but the image displays a single RGB scene with no visible depth map or interior view, making the figure content inconsistent with the description.
- **[science]** Figure 10: The caption claims to show 'four scenarios' and lists five annotation types (RGB, metric depth, instance segmentation, shaded segmentation, Canny edge), but the image displays only a single scenario view with no visible annotations or multi-panel layout to support these claims.
- **[writing]** Figure 11: The caption contains LaTeX formatting artifacts (e.g., '$\3 resolutions\ \5 aspect ratios\ \3 tokenizer call modes$') that should be rendered as plain text or proper math notation for readability.
- **[writing]** Figure 11: The mathematical expression in the caption uses inconsistent spacing and backslashes (e.g., '$\!15\,min$') which may not render correctly in all viewers; consider simplifying to '15 min' and '<1 min'.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits significant jargon density that impedes accessibility for non-specialist readers. The term "Physical AI" is used repeatedly as a proper noun in the Abstract and Introduction without a definition, effectively gatekeeping the paper's scope to those familiar with this specific industry branding. Similarly, critical architectural acronyms are introduced without expansion: "AR" and "DM" appear in Section 2.2 without being defined as "autoregressive" and "diffusion" (or "denois

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 5.2 claims 'Human score drops in all variants (-0.38 to -0.69)', but Table 16 shows SDG-Warehouse increases Human score from 85.46 to 94.79 (+9.33). This contradicts the text's assertion that all variants drop, invalidating the 'sim-to-real gap' conclusion for that dataset.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that Cosmos 3 'effectively subsumes' VLMs, video generators, and world-action models (Abstract) is an overreach. The results show competitive or superior performance on specific benchmarks but do not demonstrate that the unified architecture is strictly superior to or capable of replacing specialized SOTA models in all their specific niches. The text should be tempered to reflect 'unifying capabilities' rather than 'subsuming' the field.
- **[writing]** The statement that the model 'establishes a new state-of-the-art across a diverse suite' (Abstract) is too broad. While the paper shows SOTA on specific open-source leaderboards (e.g., RoboArena, Artificial Analysis), it trails closed models like Gemini 3.1 Pro and Veo-3.1 on several key metrics (e.g., General Reasoning, T2V HUE). The claim should be qualified to specify 'among open-source models' or list the specific domains where SOTA is achieved.
- **[science]** The claim that 'Unclear is treated as No' in the Cosmos-HUE benchmark (Section 7) is a methodological choice that artificially inflates the gap between models and ground truth. While stated, the paper overstates the reliability of the 'Real video GT' score (93.6%) without acknowledging that this score is likely a lower bound due to the strict binary penalty for ambiguity, potentially skewing the perceived 'gap' to reality.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes training on healthcare robotic surgery data (398K conversations, 2.2M images) and dense pedestrian localization (208K images, 5.6M boxes) without explicit mention of IRB approval, patient consent, or PII redaction protocols. Add a dedicated subsection in Section 4 (Data) detailing the ethical review process, consent mechanisms, and specific anonymization techniques used for these sensitive datasets.
- **[writing]** The 'Healthcare robotic surgery' dataset (Section 4.1) and 'SDG-Warehouse' safety scenarios (Appendix E.5) involve high-stakes physical interactions. The paper lacks a discussion on the potential for these models to be misused to generate deceptive safety-critical training data or to simulate hazardous scenarios for malicious physical AI development. Include a 'Dual-Use and Safety' discussion in the Conclusion or Introduction addressing these risks.
- **[writing]** The 'Cosmos-HUE' benchmark (Section 7) relies on VLM-generated questions and human annotation. The paper does not specify the safety guidelines provided to human annotators or the VLMs when evaluating potentially harmful or physically dangerous generated content (e.g., collisions, falls). Clarify the safety protocols and exclusion criteria used during the annotation and evaluation phases.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims state-of-the-art performance on 48 benchmarks (Table 1, e002) but lacks statistical significance testing (e.g., p-values, confidence intervals) for the marginal improvements over baselines like Gemini 3.1 Pro or Wan2.2. Given the high variance in generative model evaluation, report standard deviations across seeds or bootstrap confidence intervals to validate that observed gains are not due to random fluctuation.
- **[science]** The 'Real video GT' baseline in the Cosmos-HUE benchmark (Table 7, e007) scores 93.6% and 94.4%, yet the text states the GT score remains below 100% due to 'low variance' design. This implies the benchmark itself has a ceiling effect or annotation noise. The authors must quantify the inter-annotator agreement (e.g., Cohen's kappa) and the intrinsic noise floor of the human evaluation protocol to ensure the 0.1-2.3 point gaps between models are meaningful.
- **[science]** The ablation study on SDG datasets (Table 5, e005) shows a consistent drop in the 'Human' domain score (-0.38 to -0.69) across all synthetic data variants, attributed to a 'sim-to-real gap.' However, the paper does not provide a control experiment or quantitative analysis isolating whether this drop is caused by domain shift, annotation bias in the synthetic captions, or overfitting to synthetic physics. A more rigorous ablation isolating the specific failure mode is required.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** In Section 7, the 95% CI calculation assumes 10,000 independent observations, ignoring the hierarchical structure (questions nested in videos/prompts). This likely underestimates variance. Please use cluster-robust SEs or mixed-effects models.
- **[science]** Tables 1, 2, and 4 report only point estimates without uncertainty measures (SD, SE, or CI). Given stochastic generation and LLM-as-judge variance, these are insufficient to claim significance. Please report mean ± SD over multiple seeds.
- **[science]** Claims of 'state-of-the-art' in Table 4 (e.g., 48.9 vs 46.4) lack statistical significance testing (e.g., paired t-test, p-values). With high benchmark variance, these differences may not be significant. Please include p-values or effect sizes.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1 (Action), the notation for relative transforms uses \Delta \mathbf{T}_t = \mathbf{T}_{t-1}^{-1}\mathbf{T}_t. Ensure the inverse operation is clearly defined for the specific Lie algebra representation used (e.g., SE(3) vs. dual quaternions) to avoid ambiguity for readers implementing the encoder.
- **[writing]** Section 4.1 (Reasoner Data) states 'Pre-training (22.0M): Dominated by image-text (18.8M) and text-only (2.2M).' The sum of these components (21.0M) does not match the stated total (22.0M). Please clarify the missing 1.0M samples or correct the totals.
- **[writing]** Table 1 (Results Overview) uses the symbol '$^\ast$' to denote post-trained variants but does not explicitly define it in the table caption or a footnote within the table body, relying on the reader to infer from the text. Add a clear legend or footnote.
- **[writing]** In Section 5.2 (Generator Training), the text mentions 'Tokens: Cosmos3-Nano 31.05 T... Cosmos3-Super 17.86 T'. The unit 'T' is used without definition (likely Trillion). Define 'T' at first use or use the full word to ensure clarity for a general audience.
