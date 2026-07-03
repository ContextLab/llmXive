# Automated-review action items — Lens: Rethinking Training Efficiency for Foundational Text-to-Image Models

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** The 19.3% compute cost claim compares 192K A100 hours to 314K H800 hours using peak TFLOPS (312 vs 989.5) without explicitly stating this calculation or accounting for utilization differences. Clarify the metric used to derive this percentage.
- **[writing]** The paper cites "GPT-4.1" and "GPT-5.5" for captioning and reasoning but provides no bibliography entries for these specific model versions. Add citations or clarify if these are internal/unreleased models to ensure verifiability.
- **[science]** The "Lens-800M" dataset claim (800M pairs) lacks a specific data card or repository link in the text. Provide a citation or link detailing the dataset construction and captioning source to validate the scale claim.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a grammatical error and missing reference: 'Section provides more visualizations' lacks a specific section number or name.
- **[writing]** Figure 1: The caption claims '1440 resolution' but does not specify the dimension (e.g., 1440x1440 or 1440x2560), which is ambiguous for image generation tasks.
- **[science]** Figure 2: The caption states 'marker area is proportional to model size', but the plot contains no legend or scale to define this relationship, making the model size data unreadable.
- **[science]** Figure 2: The x-axis uses a logarithmic scale (1, 2, 5, 10...) but lacks explicit tick labels or grid lines to allow precise reading of inference times.
- **[writing]** Figure 2: The y-axis label 'Score' is ambiguous; the caption mentions two benchmarks (OneIG and GenEval) but does not specify which score is plotted or if they are combined.
- **[fatal]** Figure 3: The rendered image is a single pie chart that does not match the caption's description of three distinct sub-figures (a, b, c) covering pre-training data, RL data, and caption length distribution.
- **[science]** Figure 3: The chart contains a logical contradiction where the central 'Public'/'Private' circles are visually nested inside the 'Real Data' slice, yet the 'Real Data' slice is also labeled with a value (455.8M) that implies it is a separate category from the center.
- **[science]** Figure 3: The 'Synthetic' slice is labeled '1.844M' but visually occupies a negligible sliver compared to the 'Real Data' (455.8M) and 'Text-Synthetic' (110M) slices, suggesting a potential unit error or mislabeling of the data.
- **[science]** Figure 4: The x-axis label 'Training step (k)' contradicts the caption's claim of a 'Caption-length ablation study'; the axis should represent caption length (e.g., word count) rather than training steps to validate the study's premise.
- **[writing]** Figure 4: The caption is insufficient as it fails to define the specific caption lengths or word counts corresponding to the 'Detailed', 'Mixed', and 'Brief' categories shown in the legend.
- **[science]** Figure 6: The x-axis label 'Training step (k)' and the legend entry 'GPT-OSS-20BA3B' contradict the caption's claim that this is a 'Study of different language encoders'; the figure appears to show a training efficiency ablation (steps vs. score) rather than a comparison of encoder architectures.
- **[writing]** Figure 6: The x-axis tick labels are crowded and overlap (e.g., '104112120'), reducing legibility.
- **[science]** Figure 9: The image is a 4x3 grid of 12 distinct portraits, but the caption fails to label or number the sub-panels (e.g., a, b, c...), making it impossible to reference specific examples in the text.
- **[science]** Figure 9: The caption claims 'diverse human subjects,' yet the grid includes a dog (row 2, col 1) and a fantasy character with a neon mask (row 4, col 2), which contradicts the stated scope of the figure.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and jargon that are not defined at their first occurrence, creating barriers for non-specialist readers. In the Abstract, terms like 'T2I', 'VAE', and 'RL' are used immediately without expansion. Section 2.1 introduces 'MMDiT', 'RoPE', and 'MoE' without defining them. Section 2.5 uses 'CFG' without explanation. The Appendix introduces 'LoRA', 'TTUR', 'IDA', and 'R1' without definitions. Furthermore, benchmark acronyms like 'NED', 'CVTG',

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The 19.3% compute cost claim compares raw A100 vs H800 hours without normalizing for hardware throughput differences. The text asserts algorithmic efficiency but the premise (raw hours) does not logically support the conclusion (efficiency gain) without explicit TFLOPS-adjusted calculation.
- **[writing]** The claim of generalization to 1440^2 from 1024^2 training lacks a stated mechanism. The text asserts RoPE enables this but does not explain the causal link between the specific training distribution and the observed high-resolution extrapolation capability.
- **[writing]** Table 1 ablates text prompt presence, not rubric design. The conclusion that the specific '10+1 rubric' design drives diversity is not logically supported by the provided evidence, which only shows text prompts are necessary.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that Lens achieves '19.3% of the training compute' of Z-Image (Abstract, Intro) conflates GPU-hours with FLOPs without providing the specific FLOP counts or hardware efficiency factors for both models. The comparison of 192K A100 hours vs. 314K H800 hours is not directly additive without a normalized TFLOP-hour calculation, which is currently missing.
- **[writing]** The statement that the model 'generalizes to aspect ratios 1:2 to 2:1 and resolutions up to 1440^2' (Abstract, Intro) implies a hard boundary or guaranteed performance at these limits. The text should clarify if 1440^2 is the tested maximum or a theoretical extrapolation, and whether performance degrades significantly at the edges of this range compared to the training distribution.
- **[writing]** The claim that 'Strong language encoders... enable multilingual generalization from English-only training' (Intro) is a strong causal assertion. The paper admits in limitations that multilingual performance is 'lower than English' and struggles with non-English text rendering. The text should be tempered to reflect that the encoder aids *comprehension* of multilingual prompts but does not fully solve the *generation* of non-English text without specific training data.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper claims to use a 'reasoner' to reject inappropriate requests (Section 6, Section 7) but provides no details on the safety taxonomy, rejection rates, or failure modes. Explicitly describe the safety guardrails and their limitations to prevent misuse for generating harmful content.
- **[writing]** The training dataset (Lens-800M) includes 'private' sources and synthetic data generated by GPT-4.1. The manuscript lacks a clear statement on data provenance, consent for private data usage, and potential copyright or privacy violations inherent in the dataset composition.
- **[writing]** The paper relies on GPT-4.1 and GPT-5.5 for captioning, rubric generation, and reward modeling. There is no discussion of the safety alignment of these underlying models or the risk of propagating their biases into the Lens model's generation capabilities.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim that Lens achieves 19.3% of Z-Image's compute cost (Abstract, Intro) compares 192K A100 hours to 314K H800 hours. This conflates hardware generations (A100 vs H800) and does not normalize for FLOPS or memory bandwidth. The paper cites raw TFLOPS (312 vs 989.5) but fails to provide a unified compute metric (e.g., total FLOPs or normalized GPU-hours) to substantiate the '19.3%' figure. Re-calculate efficiency using a hardware-agnostic metric.
- **[science]** The GenEval score of 0.930 (Table 1) is exceptionally high compared to prior SOTA (e.g., LongCat-Image 0.870). The paper does not report standard deviation, confidence intervals, or the number of seeds used for evaluation. Given the sensitivity of GenEval to prompt rewriting (Section 4, 'Prompt for GenEval Benchmark'), the lack of statistical variance reporting makes it impossible to assess if the improvement is robust or an artifact of specific prompt engineering.
- **[science]** The ablation study on RL dataset diversity (Table 2) shows GenEval scores of 0.916 (1/4 set) vs 0.930 (Full set). The absolute gain is small (1.4%), yet the text claims 'full diversity is critical.' The paper lacks a statistical significance test (e.g., t-test) to determine if this difference is meaningful or within the noise of the evaluation metric, especially given the small sample size of the RL set (8K prompts).

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The paper claims Lens achieves '19.3% of the training compute' of Z-Image (Abstract, Intro) based on 192K A100 hours vs. 314K H800 hours. This comparison conflates hardware generations (A100 vs. H800) and lacks a normalized FLOPs calculation. Please provide a normalized compute estimate (e.g., total FLOPs or H100-equivalent hours) to substantiate the efficiency claim.
- **[science]** Benchmark results in Table 1 and Appendix tables report single-point scores (e.g., GenEval 0.930) without confidence intervals, standard deviations, or p-values. Given the stochastic nature of diffusion sampling and the finite size of benchmarks (e.g., 553 prompts for GenEval), statistical significance testing or variance reporting is required to validate performance differences against baselines.
- **[science]** The RL ablation in Table 2 (RL Training Set diversity) shows performance gains with full data but lacks statistical validation. With only three data points (1/4, 1/2, Full), the trend is suggestive but not statistically robust. Please report variance across multiple seeds or apply a significance test to confirm the improvement is not due to random fluctuation.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the phrase '314K H800 GPU hours' is ambiguous. Clarify if this refers to total compute hours or a specific cluster size over time to ensure the efficiency comparison with Lens is mathematically precise.
- **[writing]** Section 2.1 (Pre-training Data) lists 'NSFW (EVA...)' and 'aesthetic (Aesthetic Predictor...)' without defining the acronyms or model versions upon first mention. Define 'EVA' and ensure the citation for the aesthetic predictor is clear.
- **[writing]** The caption for Figure 1 (teaser) states '1440 resolution' but the text and other sections specify '1440^2' (pixels). Standardize this to '1440^2' or '1440x1440' to avoid confusion between linear dimension and area.
- **[writing]** In Section 2.3 (Pre-training), the phrase '3 base areas... x 9 aspect ratios (27 buckets)' is slightly dense. Consider rephrasing to '3 base resolutions combined with 9 aspect ratios, forming 27 buckets' for better flow.
- **[writing]** Section 4 (Comparison) introduces 'CVTG' without a full expansion or definition in the main text, relying on the caption or external knowledge. Define 'Complex Visual Text Generation (CVTG)' upon first use in the main body.
