# Automated-review action items — DomainShuttle: Freeform Open Domain Subject-driven Text-to-video Generation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The '18.7% improvement' claim (Intro/Abstract) compares against Kling 1.6 (0.725) but implies comparison against all SOTA baselines. The best open-source baseline (VACE) is 0.538, yielding a 60% gain. Explicitly state the baseline used for this percentage to avoid misleading readers.
- **[writing]** Citations for 'GPT-5.2' and 'Qwen3-VL-8B' (Sec 4) refer to unreleased or non-existent models. Evaluation metrics relying on these models are unverifiable. Replace with publicly available model versions or clarify their status to ensure reproducibility.
- **[writing]** The claim that edited videos are '3.3% of total data' (Sec 3.4) is mathematically correct (25k/750k) but ambiguous. Clarify that this refers to the total 750k dataset, not the Ditto-1M subset, to prevent misinterpretation of the training data composition.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The 'Cross-Domain' section header includes a row labeled 'Existing Methods' with a sad face, but the visual grid below it displays 'Our Method' results (indicated by the happy face row). The figure fails to visually present the 'Existing Methods' baseline results in the cross-domain section, making the comparison claim unsupported by the image.
- **[writing]** Figure 1: The 'In-Domain' section displays three rows of results, but the header only provides two smiley face icons, creating a mismatch between the number of visual examples and the provided legend indicators.
- **[writing]** Figure 2: The caption explicitly labels three distinct components (a, b, c), but the rendered image lacks these corresponding labels (e.g., '(a)', '(b)', '(c)') to guide the reader.
- **[writing]** Figure 2: The legend in the top-right panel defines 'Random Choice' with a die icon, but the 'Ref Image Pool' and 'Video Pool' inputs use a different, undefined dice icon (showing a '1'), creating ambiguity.
- **[science]** Figure 3: The 'Open-Domain Subject Consistency' subplot lists baselines in a different order (Ours, Kling-1.6, VACE-14B, SkyReels-V3, Phantom) compared to the 'Overall Video Quality' and 'Text Controllability' subplots (Ours, Kling-1.6, SkyReels-V3, Phantom, VACE-14B), which disrupts visual comparison across metrics.
- **[science]** Figure 3: The y-axis is labeled 'Average Score' with a range of 0-5, but the caption describes this as 'Human preference evaluation' without specifying the scale (e.g., 1-5 Likert scale), making the absolute values ambiguous.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and architectural shorthand that are not defined at their first point of use, creating a barrier for non-specialist readers. In the Abstract, terms like "AdaLN," "RoPE," "S2V," "Domain-MoT," and "CCL" are introduced without their full expansions. For instance, "AdaLN" appears in the phrase "domain-aware AdaLN" without stating it stands for Adaptive Layer Normalization. Similarly, "RoPE" is used as a standalone noun in "Video-Reference Dua

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that Cross-Pair Consistent Loss (CCL) improves controllability but not fidelity contradicts the ablation data. Table 2 shows CCL (ID 3 to 4) increases DINO-I from 0.394 to 0.400 and CLIP-I from 0.688 to 0.690. The text claims these are negligible while highlighting a 5.9% CD-Score jump, yet the logic that CCL *only* aids controllability is not supported by the simultaneous fidelity gains shown in the same table.
- **[fatal]** The definition of the Cross-Domain Score (CD-Score) relies on GPT-5.2, a model that does not currently exist. The logical consistency of the evaluation metric is broken because the primary evidence for the paper's main claim (18.7% improvement) depends on a non-existent or hallucinated evaluator.
- **[science]** The paper claims to decouple video and reference features via Domain-MoT to prevent domain attribute entanglement. However, the training data section states that domain attributes are annotated by an MLLM and injected as a condition 'a'. If the model is explicitly trained to associate specific domain attributes with specific subjects via this injection, the logical mechanism for 'free' cross-domain shuttling is undermined by the training objective which binds them.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The '18.7% improvement' claim (Sec 1, 4.2) lacks a clear baseline. Table 1 shows a rise from 0.725 to 0.861 (18.8% relative to 0.725), but the text implies a comparison to 'SOTA' which is ambiguous. Explicitly state the baseline value used for this percentage to avoid over-claiming magnitude.
- **[writing]** The claim of 'comprehensive outperformance' (Sec 1, 4.2) is contradicted by Table 1, where the method underperforms in In-Domain DINO-I (0.400 vs 0.407) and CLIP-I (0.690 vs 0.701). Qualify the text to reflect that improvements are specific to cross-domain scenarios, not universal.
- **[writing]** The ablation study (Sec 4.3) claims CCL 'significantly' improves fidelity by 0.3% and 1.5% while stating it mainly improves controllability. These negligible gains contradict the 'significant' framing. Temper the language regarding fidelity improvements attributed to CCL.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes a human preference study involving 40 volunteers (Sec 4.2, Human Preference Evaluation) but lacks any mention of IRB approval, informed consent procedures, or ethical oversight. Given the collection of human ratings, an ethics statement or IRB exemption confirmation is required.
- **[writing]** The training pipeline utilizes datasets containing human subjects (e.g., Phantom-Data, OpenS2V) and employs MLLMs for annotation. The manuscript does not address data privacy, consent for the use of these images in training, or potential biases in the dataset regarding demographic representation. A data ethics statement is needed.
- **[writing]** The method enables high-fidelity subject-driven generation and cross-domain transformation (e.g., real-to-fantasy). The paper does not discuss potential dual-use risks, such as the generation of deepfakes, non-consensual imagery, or the impersonation of specific individuals. A discussion on safety mitigations or responsible use guidelines is necessary.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The Cross-Domain (CD) Score relies on GPT-5.2, a model not publicly available or verifiable. To ensure scientific reproducibility, replace this with a fully open-source MLLM (e.g., Qwen-VL) for the primary metric or provide the exact model weights and inference code.
- **[science]** The ablation study (Tab. 2) shows CCL improves CD-Score by 5.9% but only marginally affects in-domain fidelity. The paper claims CCL 'precisely extracts intrinsic features,' but the data suggests it primarily prevents overfitting to style. Clarify this distinction to avoid over-interpreting the loss function's mechanism.
- **[science]** The human preference study (Sec 4.3) uses 40 volunteers ranking 20 videos each without reporting inter-rater reliability (e.g., Krippendorff's alpha) or statistical significance tests (e.g., t-tests) between methods. Add these statistical validations to support the claim of 'significant advantages'.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report variability metrics (standard deviation or confidence intervals) for all quantitative results in Table 1 and Table 2. Currently, only point estimates are provided, making it impossible to assess statistical significance or the robustness of the reported 18.7% improvement.
- **[science]** Clarify the statistical methodology for the Human Preference Evaluation (Section 4.2). With 40 volunteers ranking 20 videos, specify the aggregation method (e.g., mean rank, Borda count) and the statistical test used to claim 'significant advantages' (e.g., Friedman test, Wilcoxon signed-rank).
- **[science]** Define the sampling strategy for the 110 in-domain and 110 cross-domain test samples. Explicitly state if stratified sampling was used to ensure balanced representation of subjects/domains, and report the standard error of the mean for the reported metrics.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1 (Preliminaries), the text states 'video latents and reference image features... are separately patchified to extract their patch embeddings f_v and f_r'. However, the preceding sentence defines f_v and f_r as 'patch embeddings' without explicitly stating they are extracted via patchification in that specific sentence, creating a slight logical gap. Clarify the flow: '...are separately patchified to extract patch embeddings, denoted as f_v and f_r'.
- **[writing]** In Section 3.2.1, the sentence 'Notably, the reference AdaLN is modulated by both the reference domain attributes and time features, while the noise AdaLN is modulated only by time features' uses 'noise AdaLN' which is non-standard terminology for the video branch modulation. Consider replacing 'noise AdaLN' with 'video latent AdaLN' or 'temporal AdaLN' for consistency with the rest of the paper's terminology (e.g., 'video latents').
- **[writing]** In Section 4 (Experiments), the phrase 'well-performed methods' in the Human Preference Evaluation subsection is awkward. Replace with 'strong baselines' or 'state-of-the-art methods' to match the academic tone used elsewhere in the paper.
- **[writing]** In Section 3.2.2, the description of the RoPE offset for reference images states 'the temporal index is set to 0 while the temporal index for video starts from 1'. This is slightly ambiguous regarding the specific indices used for the video branch in the formula. Clarify if the video indices are strictly 1 to f-1 or if 0 is reserved for reference images to avoid confusion.
