# Automated-review action items — FashionChameleon: Towards Real-Time and Interactive Human-Garment Video Customization

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper repeatedly cites 'Gemini-3.0' and 'Gemini-3.1' (e.g., lines 145, 230, 305) for evaluation and data curation. These model versions do not exist publicly. Please verify the actual models used (e.g., Gemini 1.5) and correct the text and bibliography to ensure factual accuracy.
- **[writing]** In the Appendix, the paper cites 'UniMatch' (li2025unimatch) for optical flow estimation. However, the provided bibliography entry describes it as a 'few-shot drug discovery' method. This is a factual mismatch. Please correct the citation to a valid optical flow method or fix the bibliography entry.
- **[writing]** The claim of being '30-180x faster' compares the method to baselines that may not support the specific 'interactive garment switching' task. If baselines cannot perform the task, the speedup claim is misleading. Clarify if the comparison is against models capable of the same interactive task.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a grammatical error ('Overall pipeline of :') where the model name is missing, likely due to a formatting placeholder.
- **[writing]** Figure 1: The 'Legends' box uses icons (flame, snowflake) that are not explicitly defined in the legend text itself, relying on the viewer to infer 'Trainable' and 'Frozen' from the icons alone.
- **[writing]** Figure 2: The right panel's x-axis labels ('Reference', 'Garment', 'History') are ambiguous and do not match the caption's description of 'historical and conditional KV'; clarify what each block represents.
- **[science]** Figure 2: The right panel's colorbar scale (0.000–0.0003) is extremely low and lacks context; without normalization or comparison to baseline attention values, the claim that 'the model attends more to historical KV' is not visually substantiated.
- **[writing]** Figure 3: The column headers use inconsistent naming conventions, mixing method names with parameter counts (e.g., 'Ours(5B)', 'Edit(20B)+I2V(5B)', 'Phantom(1.3B)') without defining what the numbers in parentheses represent in the caption or figure.
- **[writing]** Figure 3: The caption states 'Qualitative comparison of our with other baselines' but contains a grammatical error ('of our') and fails to explicitly name the proposed method ('FashionChameleon') in the text.
- **[science]** Figure 5: The top row (Native DMD vs. Gradient-Reweighted DMD) shows a static scene with no motion, contradicting the caption's claim that Gradient-Reweighted DMD 'alleviates motion collapse during extrapolation'; the visual evidence does not support the stated ablation claim.
- **[writing]** Figure 5: The bottom row labels ('Random Reference', 'Reference KV w/o Disentangle', 'Reference KV Disentangle') are not clearly aligned with the image columns, making it difficult to distinguish which method corresponds to which result.
- **[writing]** Figure 6: The caption contains a placeholder 'of .' instead of the paper title 'FashionChameleon'.
- **[writing]** Figure 6: The top-left section lists filtering criteria (e.g., 'Transition Abruptly', 'No Human') but lacks a legend or label explicitly identifying this block as Stage 1, unlike the other three stages which have clear titles.
- **[writing]** Figure 7: The caption for (c) states that each sample comprises a reference image, a garment image, and an input prompt, but the rendered image only shows the images; the input prompt text is missing from the visual layout.
- **[writing]** Figure 7: The bar chart in (b) displays percentage values (e.g., '29.6%') on top of the bars, but the y-axis is labeled 'Count', creating a contradiction between the axis label and the data labels.
- **[science]** Figure 8: The stacked bars sum to 100% but the caption claims they show 'human preference rates' without clarifying if this is a 'win rate' in pairwise comparisons or a normalized distribution; the lack of a y-axis scale or total count makes the statistical significance of the 'superior' rates (e.g., 44%) ambiguous.
- **[writing]** Figure 8: The legend at the top is cluttered and uses inconsistent formatting for model names (e.g., 'Edit(20B)+I2V(5B)' vs 'Phantom-1.3b'), and the color mapping for 'Phantom-1.3b' (light blue) is visually indistinguishable from 'Edit(20B)+I2V(5B)' (darker blue) in the bars, risking misinterpretation.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'KV' (Key-Value) at first use in the Abstract and Section 3.3. The term 'KV Cache' is used repeatedly without explanation, which excludes readers unfamiliar with transformer inference internals.
- **[writing]** Replace 'I2V' with 'image-to-video (I2V)' at first occurrence in Section 1 and Section 3.1. Acronyms should be defined before use to ensure accessibility for non-specialists.
- **[writing]** Clarify 'DMD' (Distribution Matching Distillation) in Section 2 and 3.2. While the full name appears later, the acronym is used in equations and text before the definition is explicitly provided in the flow of the argument.
- **[writing]** Replace 'FT' with 'fine-tuning (FT)' in Section 4 (Table 1 caption and text). The abbreviation is used in table headers and text without prior definition in the main body.
- **[writing]** Define 'VAE' (Variational Autoencoder) at first use in Section 2 (Preliminary) or Section 3.1. While common in the field, the paper aims for broad applicability and should define standard acronyms.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical consistency of the proposed methodology contains several gaps where the stated mechanisms do not fully support the claimed outcomes. First, in Section 3.3 (Training-Free KV Cache Rescheduling), the logic regarding Reference KV Disentangle is circular and potentially contradictory. The authors state that to maintain coherence during garment switching, they replace the static reference KV ($KV^{\text{src}}$) with a KV derived from the last generated frame ($KV^{\text{k}}$). They claim

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of 'real-time' at 23.8 FPS (Abstract, Intro) is misleading without explicit context. 23.8 FPS is below standard 30 FPS video. Clarify if 'real-time' refers to streaming latency or throughput, and qualify the claim to avoid over-extrapolation.
- **[science]** The '30-180x faster' claim (Abstract) compares streaming FPS to batch FPS, which is asymmetric. Clarify if this speedup refers to time-to-first-frame or total generation time to ensure the magnitude is scientifically accurate.
- **[science]** The claim of 'consistent long-video extrapolation' (Abstract) lacks quantitative metrics for drift over extended sequences. Provide quantitative evidence for long-form consistency or temper the claim to reflect only tested lengths.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The 'Potential Negative Societal Impact' section (Appendix) acknowledges risks like deepfakes and bias but lacks concrete mitigation strategies. Explicitly detail technical safeguards (e.g., watermarking, NSFW filters) or usage policies intended to prevent malicious deployment.
- **[writing]** The data curation pipeline (Appendix, Sec. 1) involves scraping 'raw videos from the Internet' and using VLMs for captioning. The manuscript must clarify the legal basis for this data collection, confirm adherence to copyright/privacy laws, and state whether IRB approval or informed consent was obtained for any human subjects in the training data.
- **[writing]** The HGC-Bench construction (Appendix, Sec. HGC-Bench Details) mentions 'anonymize identifiable facial information via face swapping.' This process requires rigorous verification to ensure re-identification is impossible. The authors should provide evidence of the anonymization efficacy or a statement on residual privacy risks.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The garment consistency metrics (HGC, LGC, NTP) rely entirely on Gemini-3.0 scoring without human validation or inter-annotator agreement. Given the subjective nature of garment fidelity, the authors must report a human evaluation study (e.g., user preference or Likert scale) for these specific metrics to validate the automated scores.
- **[science]** The claim of 23.8 FPS is evaluated on an H200 GPU (Table 1), while the training and most ablation studies use A100s (Sec 4.1). The authors must clarify if the FPS metric is consistent across hardware generations or provide a normalized efficiency metric to ensure fair comparison with baselines that may have been benchmarked on different hardware.
- **[science]** The ablation study for Gradient-Reweighted DMD (Table 2) shows performance gains, but the statistical significance of these improvements (e.g., p-values or confidence intervals) is not reported. With only a single run implied, the authors should provide evidence that the observed gains are not due to random variance.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The garment consistency metrics (HGC, LGC, NTP) rely entirely on Gemini-3.0 scoring without reporting inter-rater reliability, confidence intervals, or statistical significance tests against baselines. Given the subjective nature of VLM scoring, a statistical validation (e.g., bootstrapped CIs or permutation tests) is required to support the claim of superiority.
- **[science]** The ablation study in Table 2 (GR-DMD) reports mean scores for different temperature coefficients ($	au$) but omits variance measures (standard deviation or standard error). Without variance estimates, it is impossible to determine if the observed differences between $	au=0.2$ and other values are statistically significant or due to random noise.
- **[science]** The user study (Appendix) reports aggregate preference rates from 672 responses but lacks a statistical test (e.g., binomial test or chi-square) to confirm that the observed preference for the proposed method is significantly different from chance or baselines. Reporting p-values or confidence intervals is necessary.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Abstract and Introduction, the phrase 'switch garment' should be corrected to 'switch garments' (plural) to match the context of multiple items and standard grammar. This appears in the Abstract ('interactively switch garment') and Section 1 ('switch garments during generation' is correct, but 'switch garment' appears in the conclusion).
- **[writing]** In Section 3.3, the sentence 'Specifically, I^gar_2 is encoded... and the corresponding KV^gar_2 are obtained' contains a subject-verb agreement error. 'KV^gar_2' is singular, so it should be 'is obtained'. Additionally, the phrase 'new new KV' contains a typo (repetition of 'new').
- **[writing]** In Section 3.3, the phrase 'Recall that we deliberately I2V property' is grammatically incomplete and missing a verb. It should likely read 'Recall that we deliberately retained the I2V property' or 'preserved the I2V property' to make sense of the sentence structure.
- **[writing]** In Section 3.3, the term 'streaming eneration' contains a typo (missing 'g' in 'generation'). This appears in the paragraph discussing Figure 3 (analysis.pdf).
- **[writing]** In Section 4, the caption for Table 1 states 'The best results are highlighted in bold and the second best are underlined.' However, the table uses 'underline' for the second best, but the text description in the caption uses 'underlined' (adjective) while the table content uses the command. Ensure consistency in the description of formatting styles throughout the paper, specifically checking if 'underlined' is the intended term for the second-best results in the text body as well.
