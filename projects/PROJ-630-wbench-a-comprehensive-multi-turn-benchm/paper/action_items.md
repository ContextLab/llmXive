# Automated-review action items — WBench: A Comprehensive Multi-turn Benchmark for Interactive Video World Model Evaluation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 5.2 claims navigation correlation is '≈0'. Verify exact value (e.g., 0.05) in Fig 3a. If non-zero, change to 'weakly correlated' to avoid overstatement.
- **[science]** Section 5.2 states 'four ρ=1.00' for human alignment. Perfect correlation is statistically improbable with 400 annotators. Verify if this is rounding (e.g., 0.996) and adjust text to 'ρ ≥ 0.99'.
- **[writing]** Abstract claims 'no single model excels on all dimensions'. Clarify this means no model leads in all five simultaneously, as Table 4 shows leaders in individual dimensions.
- **[writing]** Section 4.1 states '62% FPP, 38% TPP'. Verify if these are exact or rounded. If rounded, add 'approximately' to ensure factual precision.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains multiple instances of missing text where the benchmark name should appear (e.g., 'Overview of .', 'cases in .', 'covered by :'). The figure itself also uses the abbreviation 'PS' without defining it in the caption.
- **[science]** Figure 1: The radar chart in panel (d) lacks a visible scale or grid values, making it impossible to determine the magnitude of the scores for the plotted models.
- **[science]** Figure 2(c): The heatmap contains values exceeding the theoretical range of a Z-score (e.g., +1.9, -1.9), yet the colorbar scale is fixed to [-1.0, 1.0]. This causes the most extreme values to be clipped to the maximum/minimum colors, obscuring the true magnitude of the deviations.
- **[writing]** Figure 2(c): The y-axis labels are rotated 90 degrees and overlap significantly, making them difficult to read; horizontal alignment or increased spacing is needed.
- **[science]** Figure 3: The 'Perspective Switching' panel shows a red 'X' and a dashed line for the '9 text-driven models' baseline, but the legend entry for this group is a solid black square. This visual mismatch makes the baseline data illegible and confusing.
- **[writing]** Figure 3: The caption 'Per-turn performance degradation' is too brief; it should explicitly state that the y-axis represents the evaluation score (e.g., 0-100) to clarify the metric being degraded.
- **[writing]** Figure 4: The caption contains LaTeX formatting artifacts ('Spearman $$', '$ 0.94', '$ = 1.00') instead of the symbol '$\rho$' or the word 'correlation', making the metric and values unreadable.
- **[writing]** Figure 4: The legend at the top is not explicitly labeled as 'Models' or 'Methods', though the context implies it; adding a label would improve clarity.
- **[writing]** Figure 5 caption contains a missing reference: 'all cases in .' lacks the benchmark name (likely 'WBench').
- **[writing]** Figure 5 caption is incomplete: 'all cases in .' should specify the dataset or benchmark name.
- **[writing]** Figure 6: The caption claims 'Two categories per row are presented,' but the layout displays four distinct categories per row (Nature, Urban, Indoor, Workspace in the top half; Fantasy, Sports in the bottom half), creating a direct contradiction between the text and the visual structure.
- **[writing]** Figure 6: The caption states each category is shown as a 'photorealistic/stylized pair,' yet the 'Nature' and 'Urban' rows contain multiple disparate images (e.g., penguin, bamboo, city street, neon city) rather than a single paired comparison, making the description inaccurate for the majority of the content.
- **[science]** Figure 10: The caption claims to showcase 'same-subject switches, multi-subject switches, and scope-mode transitions,' but the image only displays two examples (scope-to-FPP and FPP-to-FPP) and lacks the promised variety of sub-types.
- **[writing]** Figure 10: The text labels 'TPP -> FPP', 'FPP -> FPP', etc., are rendered at a resolution that is difficult to read and may be illegible in smaller formats.
- **[writing]** Figure 12: The caption claims the figure shows distributions across 'direction, scene type, and control interface', but the figure only displays distributions for 'direction' (Atomic Distribution) and 'trajectory type' (Trajectory/Mix Distribution). The 'scene type' and 'control interface' distributions mentioned in the caption are missing from the visual.
- **[writing]** Figure 12: The third subplot is labeled '(b) Mix Distribution', but it should be labeled '(c)' to follow the sequential ordering of (a) and (b) in the preceding subplots.
- **[science]** Figure 12: The 'Atomic Distribution' chart (a) labels segments with single letters (W, S, A, D) and directions (up, down, left, right) but does not explicitly state that these represent navigation key presses or actions, which is critical context for a 'navigation test case' distribution.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript is dense with domain-specific acronyms and abbreviations that hinder accessibility for readers outside the immediate niche of generative video and robotics. While the technical precision is high, the text frequently assumes prior knowledge of terms that should be explicitly defined or replaced with plain English. Specifically, the term "6-DoF" appears in the Abstract and Introduction without definition. While standard in robotics, a general computer science reader may not immediat

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a comprehensive benchmark, but several logical gaps exist in the interpretation of experimental results. First, in Section 5.2 ("Results Summary"), the authors state that "navigation is largely independent (correlation ≈0) from quality, consistency, and physics." However, the same section explicitly reports that "Physical scores correlate with video quality (r=0.84)." Logically, if Variable A (Navigation) is uncorrelated with B (Quality) and C (Physics), and B and C are highly

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim 'no single model excels on all dimensions' (Abstract) is an over-generalization. Table 1 shows leaders vary, but the paper lacks statistical proof that no model is second-best in all others. Clarify if this is a qualitative summary or a robust statistical finding.
- **[science]** The assertion 'Physical scores correlate with video quality' (r=0.84) does not specify the model subset. If driven only by text-driven models, generalizing this to all world models is an overreach. Specify the exact subset used for this correlation.
- **[science]** The claim 'navigation is decoupled' relies on correlations from different evaluation subsets (158 vs 289 cases). Comparing across non-overlapping data risks over-interpreting independence. Clarify the data overlap used for the correlation analysis.
- **[writing]** The statement 'Open-source models achieve competitive scores' is misleading as top performers (Wan 2.7, Kling 3.0) are API-only. Qualify this to 'some open-source models' to avoid implying general parity with closed models.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript presents a comprehensive benchmark for interactive video world models. From a safety and ethics perspective, the paper is generally sound in its intent to evaluate model capabilities rather than generate harmful media. However, three specific areas require clarification to ensure full compliance with ethical research standards. First, regarding Dual-Use and Content Safety: The dataset includes interaction types such as "combat" and "subject action" (Section 5, Appendix e002). Whil

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of strong human-auto alignment (Spearman ρ ≥ 0.94, Fig. 5) relies on 400 annotators but lacks statistical power analysis or confidence intervals. With 13.5K tasks, the sample size is large, but the variance in human judgments (inter-annotator agreement) is not reported, making the robustness of the correlation claim uncertain.
- **[science]** Navigation accuracy (NavScore) depends on MegaSaM for pose estimation against synthetic GT. The paper does not report the error rate of MegaSaM on the specific synthetic data distribution or validate the GT construction logic. If the pose estimator fails on the generated video styles, the 'ground truth' comparison is invalid.
- **[science]** The 'Physical' dimension relies heavily on VLMs (Doubao-Seed-2.0-lite) for Causal Fidelity. The prompt engineering and rubric (Appendix) are provided, but no inter-rater reliability (Cohen's kappa) between VLMs or between VLMs and human experts is reported to validate the metric's stability against prompt variations.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report confidence intervals or standard errors for all mean scores in Tables 1 and 2. With 289 cases, point estimates alone are insufficient to assess statistical significance of model differences (e.g., Wan 2.7 vs. Kling 3.0).
- **[science]** Clarify the multiple-comparisons correction method used for the 22 sub-metrics. Without adjustment (e.g., Bonferroni or FDR), the risk of Type I errors in identifying 'leading' models is high.
- **[writing]** Specify the sample size (N) and degrees of freedom for the Pearson/Spearman correlations reported in Figure 3. Correlation strength depends heavily on N, which is currently ambiguous for the '20 models' subset.
- **[science]** Provide the distribution (e.g., boxplots or histograms) of the human-annotation scores used to validate the automated metrics. A single Spearman rho value does not reveal if the alignment holds across the full score range or only at extremes.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (Experiments), the phrase 'flickering >92' and 'smoothness >96' lacks units or context. Explicitly state these are scores on the 0-100 scale to avoid ambiguity for readers unfamiliar with the specific metric ranges.
- **[writing]** The abstract and introduction use the macro \numvideo and \numturn. While standard in LaTeX, ensure the final compiled PDF renders these as the specific numbers (289 and 1,058) clearly. If the macro expansion is missing in the final output, replace with explicit numerals for immediate readability.
- **[writing]** In the Appendix, several figure captions (e.g., Fig. qual_ee, qual_sa, qual_ps) are empty or contain only the label text. Ensure these captions describe the visual content (e.g., 'High vs. low scoring cases for event editing') to make the appendix self-contained.
