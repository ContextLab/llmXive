# Automated-review action items — LiveEdit: Towards Real-Time Diffusion-Based Streaming Video Editing

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Latency figures are inconsistent: Abstract claims 12.66 FPS (~79ms), but Table 3 (sec/4_experiment.tex) shows 7.89s for 81 frames (~97ms). Clarify the exact frame count and time used for the FPS claim.
- **[science]** In sec/3_method.tex, the mask for chunk k relies on the edited output of chunk k-1. Clarify if this edited output is available in real-time without introducing a causal delay or dependency violation.
- **[writing]** The claim of 'exceptionally high' temporal redundancy for SA tokens in sec/4_experiment.tex lacks specific quantitative values from Fig. 5. Include the mean cosine similarity values to support this assertion.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2: The right panel ('Directly Truncate') shows a triangular attention mask where attention is restricted to the causal past (lower triangle), yet the caption claims it 'forces attention to spread uniformly across all historical frames.' The visualization contradicts the text description; the attention is sparse (triangular), not uniform across the full history.
- **[writing]** Figure 2: The y-axis label 'Key' is rotated 90 degrees and partially cut off at the bottom (e.g., the 'y' in 'Key' is missing or obscured), and the tick labels on the right plot's y-axis are misaligned or missing for some values.
- **[writing]** Figure 3: The title for Stage 2 is cut off on the right edge ('...Causal Initial'), making the full stage name illegible.
- **[writing]** Figure 3: The legend in Stage 2 defines 'Bid. Model' but the corresponding block in Stage 1 is labeled 'Bidirect. DiT', creating inconsistent terminology.
- **[science]** Figure 4: The 'Temporal IoU Distribution' histogram shows a mean of 0.016%, yet the x-axis is labeled 'Pixel Change Rate (%)'. IoU (Intersection over Union) and Pixel Change Rate are distinct metrics; the axis label should match the metric name or the caption should clarify the relationship.
- **[writing]** Figure 4: The 'Difference Matrix' row lacks a colorbar or legend to define the mapping between the heatmap colors (blue to red) and the magnitude of pixel differences.
- **[writing]** Figure 5: The row labels 'LucyEdit', 'InsV2V', 'Stream.V2', and 'Ours' are rotated 90 degrees and placed inside the image grid, which is visually cluttered and unconventional for a comparison table.
- **[writing]** Figure 5: The instruction text is placed directly over the image content in the top row, reducing readability and obscuring parts of the source video.
- **[writing]** Figure 7: The caption states the plot shows 'token cosine similarity between consecutive denoising step' (singular), but the figure displays two distinct distributions (Self-Attn and FFN) without clarifying in the text that these represent different attention mechanisms or layers.
- **[writing]** Figure 7: The caption contains a grammatical error ('denoising step' should be 'denoising steps').
- **[science]** Figure 8: The caption states 'line plots indicate the proportion of top-3 selections,' but the line plots track the 'Best' category (dark blue) and the 'Second' category (medium blue) separately, not a combined top-3 sum. Additionally, the 'Best' line for 'Ours' reaches 100% in the top chart, which contradicts the stacked bar showing ~96% 'Best' and ~4% 'Second' (implying <100% 'Best').
- **[writing]** Figure 8: The legend defines 'Best', 'Second', 'Third', and 'Others', but the line plots only visualize 'Best' and 'Second' (or a mix of them), leaving the 'Third' and 'Others' categories unrepresented in the line plot overlay, creating ambiguity about what the lines specifically represent.
- **[science]** Figure 12: The 'User Input' row displays four distinct video frames, but the editing instruction is a single static text prompt. This implies the input is a video, yet the instruction does not specify how the edit should apply across the temporal dimension (e.g., to all frames or a specific segment), making the evaluation setup ambiguous.
- **[writing]** Figure 12: The caption 'More comparison between baseline and our LiveEdit' is generic and fails to describe the specific editing task shown (changing goose feathers to blue), forcing the reader to rely on the image text which is not part of the formal caption.
- **[writing]** Figure 12: The row labels (e.g., 'InsV2V', 'LucyEdit', 'Stream.') are abbreviations that are not defined in the caption or the figure itself, requiring the reader to guess the full method names.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and jargon that are not defined at their first occurrence, creating a barrier for non-specialist readers. Specifically, the terms 'AR' (Augmented Reality), 'DiT' (Diffusion Transformer), 'DMD' (Distribution Matching Distillation), 'FFN' (Feed-Forward Network), 'NFEs' (Network Function Evaluations), and 'CFG' (Classifier-Free Guidance) are introduced in the Abstract, Introduction, or early Method sections without expansion. For instance, '

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 3.3 claims the mask for chunk k is derived from chunk k-1. Logically, an edit moving in chunk k cannot be masked correctly using k-1's data. Explain how the mask for k is determined causally without ground truth.
- **[writing]** Section 4.1 states a fixed 70% pruning ratio. This contradicts 'strict preservation' if the edit region varies. Clarify if 70% is an average or if the logic holds for large edits.
- **[science]** Table 2 shows Dynamic Degree drops to 0.017 with FFN caching. The text blames 'blurring,' but near-zero DD implies static video. Explain if the metric collapse is due to motion freezing.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of 'zero visual degradation' in unedited regions (Sec 3.3, Sec 5) is an absolute over-claim. Table 3 shows a drop in Aesthetic Quality (0.584 to 0.581) and Imaging Quality (0.720 to 0.708) when the cache is enabled. The text must be revised to reflect that degradation is 'negligible' rather than non-existent.
- **[writing]** The assertion that the method 'strictly outperforms' bidirectional offline models in Text Alignment (Sec 4.3) is not fully supported by the data. While the final score (0.270) beats InsV2V (0.259), the claim implies universal superiority over the class, which is not demonstrated against all baselines. The phrasing should be qualified to 'outperforms specific strong baselines' or 'achieves competitive SOTA'.
- **[writing]** The claim that the AR-oriented Mask Cache 'guarantees' absolute visual consistency (Sec 3.3) is an over-interpretation of the $L_2$ distance heuristic. The method relies on a threshold $\tau$ to prune 70% of tokens; if the threshold is not perfectly tuned for every scene, artifacts could occur. The word 'guarantees' should be replaced with 'significantly preserves' to align with the empirical nature of the evaluation.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript presents a technically advanced framework for real-time video editing but lacks sufficient discussion on safety and ethical implications. First, regarding human subjects research, Section X_suppl describes a user study involving 20 volunteers. The text details the metrics and results but fails to mention ethical compliance. Standard practice requires explicit confirmation of Institutional Review Board (IRB) approval or an exemption determination, along with a statement confirming

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of 12.66 FPS (Abstract) conflicts with the reported 79ms/frame latency (Implementation Details). 1/0.079s ≈ 12.66 FPS, but the ablation table (tab/ablation-arch.tex) lists 7.89s latency for 81 frames, which is ~10.2 FPS. Clarify the exact benchmark conditions (resolution, hardware, chunk size) for the FPS claim to ensure reproducibility.
- **[science]** The user study (sec/X_suppl.tex) reports 100% top-3 preference for Instruction Consistency with only 20 volunteers. Without reporting the total number of video pairs evaluated or the statistical significance (e.g., binomial test p-value), this result risks being an artifact of small sample size or selection bias. Provide the raw counts and statistical validation.
- **[science]** The AR-oriented Mask Cache claims to prune 70% of tokens (Implementation Details) while maintaining 'indistinguishable' quality. The ablation table (tab/ablation_cache.tex) shows a drop in Imaging Quality (0.720 -> 0.708) and Aesthetic Quality (0.584 -> 0.581) when the cache is enabled. The authors must reconcile the claim of 'indistinguishable' quality with these measurable metric degradations.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The user study (Sec. X_suppl) reports percentages (e.g., 100.0%, 75.0%) from 20 volunteers but lacks statistical significance testing (e.g., binomial test, chi-square) or confidence intervals to validate that the observed superiority over baselines is not due to chance.
- **[science]** Quantitative results in Tab. 1 and Tab. 2 report metrics to three decimal places without standard deviations or confidence intervals. Given the stochastic nature of diffusion models, variance estimates are required to assess the reliability of the reported SOTA claims.
- **[science]** The claim of pruning '70% of redundant spatial tokens' (Sec. 4.1) is presented as a fixed empirical outcome. The manuscript should clarify if this threshold was optimized via cross-validation or if it represents a mean across the test set, and provide the variance of this pruning ratio.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In sec/1_introduction.tex, the first contribution bullet point contains a missing space before the parenthesis: 'latency(12.66 FPS)' should be 'latency (12.66 FPS)'.
- **[writing]** In sec/4_experiment.tex, the Stage 3 bullet point begins with a sentence fragment: 'deliberately bypassing the computationally expensive ODE initialization.' This should be integrated into the preceding sentence or rephrased as a complete sentence.
- **[writing]** In sec/4_experiment.tex, the sentence 'our mask generation process demonstrate extremely high structural stability' contains a subject-verb agreement error; 'process' is singular and should be followed by 'demonstrates'.
- **[writing]** In sec/X_suppl.tex, the User Study section ends a sentence with a comma and a period: '...accurately, .' This punctuation error must be corrected.
- **[writing]** In sec/X_suppl.tex, the caption for Fig. ef{fig:user_study} ends with a double period: '...dimensions..' Remove the extra period.
