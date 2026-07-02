# Automated-review action items — ViQ: Text-Aligned Visual Quantized Representations at Any Resolution

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Claim in 'Image Reconstruction' that ViQ 'ranks first among mainstream discrete visual autoencoders' is false. Table 2 shows UniTok has higher PSNR (25.32 vs 22.73) and lower rFID (0.37 vs 0.62). Correct the ranking claim.
- **[writing]** Claim that JPEG requires Q≈0.08 to match ViQ's compression ratio is unsupported. No citation or data validates this specific quality factor. Remove the specific number or provide evidence.
- **[writing]** Ablation text claims Case B has 'unsatisfactory performance on OCR/Chart' but Table 5 only shows aggregate scores. Clarify that this observation comes from full benchmark results (Table 1), not the ablation table alone.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The text labels inside the 'Position-Aware FSQ' matrix (e.g., '9', '863', '25', '358') are extremely small and illegible, making the specific quantization values unreadable.
- **[science]** Figure 1: The bar charts on the right lack explicit axis titles (e.g., 'Score' or 'FID') and the y-axis tick labels are too small to read, hindering verification of the 'state-of-the-art' claim.
- **[writing]** Figure 2: The legend in Stage 2-2 uses the term 'LoRA' (Low-Rank Adaptation), but the diagram does not explicitly show where LoRA modules are applied to the frozen components, making the legend's relevance to the visual flow unclear.
- **[writing]** Figure 2: The bottom row of diagrams appears to be a duplicate or slightly modified version of the top row without a clear distinction in the caption explaining the difference between the two rows.
- **[science]** Figure 3: The legend defines '4K Speed-up ratio' and '16K Speed-up ratio' as lines, but the bars are labeled with specific values (e.g., 12.94, 15.67) that do not match the right y-axis scale (0-100%) or the line trends, creating ambiguity about what the bar values represent.
- **[writing]** Figure 3: The caption states the figure compares 'Training Efficiency', but the y-axis is labeled 'Time (s)' and 'Speed-up Ratio (%)', which are metrics of inference or forward pass efficiency, not training efficiency, creating a contradiction between the caption and the data shown.
- **[writing]** Figure 3: The legend includes 'ViQ Offline Code Extraction' and 'MLLM w/ ViQ' as separate entries, but the bars appear stacked or grouped in a way that makes it unclear which specific bar segment corresponds to which legend item without explicit visual distinction (e.g., hatching vs solid) matching the legend keys.
- **[writing]** Figure 4: The x-axis label 'JPEG(Q=0.08)' is visually identical to the 'ViQ-Codes' label, yet the bar chart shows 'JPEG(Q=0.08)' at 0.08 MB and 'ViQ-Codes' at 0.07 MB. The visual reconstruction images above the 'ViQ-Codes' label appear to correspond to the 'JPEG(Q=0.08)' quality level (highly compressed artifacts), while the 'JPEG(Q=0.85)' label is missing its corresponding image column, creating a mismatch between the visual examples and the quantitative data.
- **[science]** Figure 4: The bar chart compares 'Raw' (7.37 MB) against 'ViQ-Codes' (0.07 MB) to claim a 96x compression ratio. However, the 'Raw' image is likely uncompressed (e.g., PNG or raw sensor data), whereas 'ViQ-Codes' represents a compressed representation. A fair comparison for 'image compression' should typically be against a standard baseline like JPEG at a similar quality level or a standard raw format specification, as comparing against a potentially inflated 'Raw' size exaggerates the compressi
- **[science]** Figure 5: The caption states 'Left or above is the original image,' but the visual layout (2x4 grid) and image content suggest these are side-by-side comparisons of original vs. reconstructed images. The 'above' descriptor is confusing for a grid layout, and the lack of explicit 'Original' vs. 'Reconstructed' labels makes it difficult to verify the reconstruction quality claim.
- **[writing]** Figure 5: The caption is ambiguous regarding the spatial arrangement of the comparison pairs. It should explicitly state 'Left column is original, right column is reconstructed' (or similar) to match the visual evidence, rather than using 'Left or above' which implies a different layout structure.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'proximal representation' at first use in Section 3.2. The term is introduced as a 'regularization function' but lacks a plain-English explanation of what 'proximal' implies in this specific context for non-specialists.
- **[writing]** Replace the acronym 'VQ' with 'vector quantization' on its first occurrence in Section 3.2 ('Since our vector quantization (VQ) implementation...'). While common in the field, the paper targets a broader audience and should define it explicitly upon first use.
- **[writing]** Clarify the term 'native resolution' in Section 3.1. The phrase is used repeatedly to describe input handling, but the text does not explicitly define what constitutes 'native' versus 'fixed' or 'resized' resolution for a general reader.
- **[writing]** Define 'RoPE' (Rotary Position Embedding) at first use in Section 3.2. The text introduces '2D rotary position embedding (RoPE)' but assumes the reader knows the acronym; spell it out fully before using the abbreviation.
- **[writing]** Replace the jargon-heavy phrase 'optimization-free' in Section 3.2 with a clearer description, such as 'does not require learning a codebook,' to ensure non-specialist readers understand the distinction from other quantization methods.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** In Section 3.2 (Eq. 3), the formula conflates dimensionality reduction with L_infty projection. Clarify if BN is the bottleneck layer and L_infty is a separate projection step to ensure the mathematical definition matches the text description.
- **[science]** The efficiency claim in Section 4.2.1 conflates online feature extraction with offline code generation. Explicitly state if the reported speedup includes the cost of generating ViQ codes, or clarify that the comparison is strictly for the LLM forward pass to avoid misleading conclusions about training speed.
- **[writing]** In Section 4.3, the claim that ViQ 'ranks first' among discrete autoencoders contradicts Table 2, where UniTok achieves a better rFID (0.37 vs 0.62). Revise the claim to reflect that ViQ is competitive or second-best, or restrict the comparison to models with identical objectives.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that ViQ 'ranks first among mainstream discrete visual autoencoders' (Abstract, Intro) is contradicted by Table 1 (sec/4-Experiments.tex), where UniTok achieves superior PSNR (25.32 vs 22.73), SSIM (0.77 vs 0.66), and rFID (0.37 vs 0.62). The text must be revised to accurately reflect that ViQ is competitive or second-best, not first, to avoid over-claiming.
- **[science]** The efficiency claim of '20%-70% acceleration' (Abstract) relies on a comparison where ViQ uses pre-computed offline codes while the baseline (SigLIP2-g) extracts features online. The paper does not explicitly state that the baseline's feature extraction time is excluded from the 'forward time' metric in a way that makes the comparison fair for end-to-end training latency. Clarify if the baseline comparison includes feature extraction or if the speedup is only for the LLM forward pass.
- **[writing]** The statement that ViQ 'surpasses the previous state-of-the-art scores... under 6B number of visual encoder parameters' (Intro) is misleading. Table 1 shows ViQ (1.3B) beats InternViT-2.5-6B (6.0B) on average, but the 6B model is a specific large variant. The claim implies a general superiority over all 6B models, whereas the comparison is against a specific baseline. Rephrase to specify the exact baseline being surpassed.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript presents ViQ, a method for text-aligned visual quantized representations. From a safety and ethics perspective, the primary concerns revolve around data provenance and the potential for dual-use applications of the proposed efficiency gains. Data Provenance and Consent: The Appendix (sec/A-Appendix.tex) states that Stage 2 training utilizes "approximately 30B vision-language tokens." The paper mentions using data from "LLaVA-OneVision" (sec/4-Experiments.tex) but lacks a dedicated

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The efficiency claims (20%-70% speedup) compare online feature extraction against offline pre-computed codes. Clarify if the reported speedup includes the amortized cost of encoding or if the baseline was also pre-processed to ensure a fair comparison.
- **[science]** Table 1 shows ViQ trailing SOTA on specific benchmarks like OCRBench. Provide statistical significance tests (e.g., p-values or confidence intervals) to confirm the aggregated average improvement is robust against variance across the nine benchmarks.
- **[science]** The claim of a unique trade-off between reconstruction and understanding relies on comparing different models. Include an ablation varying reconstruction loss weight to causally demonstrate the trade-off within a single architecture.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 (sec/4-Experiments.tex) reports average scores across nine benchmarks without providing standard deviations, confidence intervals, or the number of random seeds used. Given the small margins of victory (e.g., 57.2 vs 57.0), statistical significance testing (e.g., paired t-tests or bootstrap CIs) is required to validate that these improvements are not due to random variance.
- **[science]** The efficiency claims in Section 4.2 (sec/4-Experiments.tex) cite specific speedup percentages (e.g., '70% acceleration') but lack statistical context. The authors must report the variance across multiple runs or provide a statistical test to confirm that the observed speedups are consistent and not artifacts of a single favorable run.
- **[science]** In the ablation study (Table 3, sec/4-Experiments.tex), the performance differences between configurations (e.g., 68.7 vs 68.3) are marginal. The authors should clarify if these results are statistically significant or if the reported 'best' settings are merely the result of overfitting to a single validation split.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In sec/4-Experiments.tex, the 'Loss Combination' paragraph contains grammatical errors: 'When keep only the text loss' should be 'When keeping only the text loss', and 'add self distillation loss with significant enhance the performace' should be 'adding the self-distillation loss significantly enhances the performance'. Additionally, 'performace' is misspelled.
- **[writing]** In sec/4-Experiments.tex, the 'Visual Encoder Baselines' paragraph contains a typo: 'specialized optimized for mutli-modal' should be 'specialized for optimizing multi-modal' or 'optimized for multi-modal', and 'mutli-modal' is misspelled.
- **[writing]** In sec/A-Appendix.tex, the 'From Fix Resolution to Native Resolution' section contains a typo: 'wit a Multi-head Attention Pooling Layer' should be 'with a Multi-head Attention Pooling Layer'. Also, 'Fix Resolution' in the heading should likely be 'Fixed Resolution'.
