# Automated-review action items — Enhancing Train-Free Infinite-Frame Generation for Consistent Long Videos

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Clarify that the '4.7% and 2.0%' consistency gains in Sec 3.3 apply specifically to the VideoCrafter2 baseline, as Wan2.1 gains differ (3.8% and 2.1%).
- **[writing]** Replace 'moderately' with 'negligible' in the memory analysis (App. Comp. Eff.) to accurately reflect the <1% overhead shown in Table 4.
- **[writing]** Qualify the 'consistent outperformance' claim in NarrLV results to acknowledge varying improvement magnitudes across TNA settings and models.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption is explicitly marked as '(no caption)', yet the figure contains complex visual elements (film strips, text blocks, axes) that require a descriptive caption to explain the content and context.
- **[writing]** Figure 1: The x-axis label 'Frame Num' is present, but the axis tick labels are illegible due to low resolution, making it difficult to verify the scale or specific frame counts.
- **[writing]** Figure 1: The text blocks on the left side describing the video prompts are blurry and difficult to read, hindering the viewer's ability to understand the specific inputs used for generation.
- **[writing]** Figure 2: The x-axis label 'Frame Num' is present, but the axis contains a non-standard infinity symbol (∞) next to '1000' without explanation in the caption or axis labels.
- **[writing]** Figure 2: The text blocks describing the video content (Iron Man, sea turtle, Corgi) are extremely small and difficult to read, reducing the figure's clarity.
- **[science]** Figure 4: The caption states the video case contains a 'consistency anomaly,' but the visual sequence in panel (a) shows a car that is white in the first three frames and black in the fourth, yet the text in Figure 9 describes the anomaly as a car changing from black to white. This contradiction creates confusion regarding the specific anomaly being analyzed.
- **[writing]** Figure 4: The 3D plot in panel (c) has a legend with very small text ('Noise level=10', etc.) that is difficult to read and distinguish from the grid lines, reducing the clarity of the data series mapping.
- **[writing]** Figure 5 caption contains LaTeX-style comment markers ('%') and appears to be a duplicate of Figure 4's description; the text should be cleaned and verified for uniqueness.
- **[writing]** Figure 5 caption is identical to Figure 4's caption, suggesting a copy-paste error in the manuscript that needs correction.
- **[writing]** Figure 6 caption contains raw formatting artifacts ('yellowYellow', 'redRed') that should be cleaned up for professional presentation.
- **[writing]** Figure 6 caption is grammatically incomplete; it defines what the bboxes indicate but does not explicitly state that rows (a)-(d) correspond to the Baseline, Stage 1, Stage 2, and DCE methods respectively, relying on the reader to infer this from the labels.
- **[writing]** Figure 7 caption: The LaTeX syntax for the variable is malformed as `$_adju` (missing backslash and braces); it should be formatted as `$\delta_{adju}$` to match the rendered axis labels.
- **[writing]** Figure 7 caption: The text 'O.S.' is undefined; the caption should explicitly state that 'O.S.' stands for 'Overall score' to match the y-axis label in panel (a).
- **[science]** Figure 8: The x-axis label 'Stage 2 steps' is misleading because the data points (0, 5, 10, 15, 20, 25, 30, 64) are not evenly spaced, yet the visual bar spacing implies a linear progression; the gap between 30 and 64 is visually compressed compared to the actual numerical difference, distorting the trend interpretation.
- **[writing]** Figure 8: The annotation 'Without Stage 1 !!!' with an arrow pointing to the bar at x=64 is informal and lacks precise definition — it’s unclear whether this condition applies only to that point or represents a separate experimental setup; the caption does not clarify this critical distinction.
- **[writing]** Figure 9: The caption text is truncated at the end ('achieve h'), likely cutting off the final word (e.g., 'higher consistency').
- **[writing]** Figure 9: The caption contains a syntax error in the parenthetical example ('When anomalies are detected (, the car's...'), missing the condition or symbol before the comma.
- **[writing]** Figure 10: The caption describes a 'multi-prompt controlled generation case' but fails to list the specific text prompts used for each row, making it impossible to verify the model's adherence to the instructions.
- **[writing]** Figure 10: The image contains frame indices (e.g., #0, #50) but lacks explicit row labels or headers to distinguish the different generation conditions or prompts.
- **[science]** Figure 11: The caption claims to illustrate a 'bad case' resulting from migrating to CogVideoX, but the image contains no visual indicators (e.g., red boxes, arrows, or text annotations) to identify the specific artifacts or inconsistencies, making it impossible to verify the claim.
- **[writing]** Figure 11: The image consists of a sequence of frames with frame numbers (#0, #20, etc.) but lacks a descriptive title or axis labels to explain the context of the scene (e.g., 'SUV on mountain road'), relying entirely on the caption for basic context.
- **[writing]** Figure 12: The caption contains a typo 'blueblue' instead of 'blue' when describing the highlighting of superior results.
- **[writing]** Figure 12: The text description at the top of the figure describes a cymbal changing colors, but the visual content shows Iron Man; the text does not match the image.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits a moderate overuse of domain-specific acronyms and undefined abbreviations that hinder accessibility for non-specialist readers. While the core concepts are sound, the writing frequently assumes the reader possesses prior knowledge of specific method names and metric abbreviations. First, the primary method name, MIGA, is introduced in the caption of Figure 1 and the text of Section 3 without being explicitly defined in the Introduction. The acronym appears before the ful

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a logical framework for train-free long video generation, but several claims require tighter alignment with the presented data to ensure full logical consistency. First, the Conclusion states that MIGA "preserves constant memory usage." This claim is logically inconsistent with the data in Table 3 (memory_analysis), which explicitly reports peak memory consumption increasing from 9929 MiB (500 frames) to 9985 MiB (2000 frames). While the authors note this is a "moderate" incre

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that MIGA achieves 'state-of-the-art' performance (Conclusion) is overreaching. Table 1 in the Appendix shows Infinity-RoPE (a train-based method) scoring 98.08 O.S. vs. MIGA's 97.82. The paper must explicitly qualify 'SOTA' to 'train-free SOTA' or acknowledge the gap with trained methods.
- **[writing]** The assertion that MIGA 'naturally supports infinite frame generation' with 'constant memory' (Abstract/Conclusion) is technically imprecise. Table 'memory_analysis' shows memory increasing from 9929 MiB to 9985 MiB as frames grow from 500 to 2000. While the growth is small, it is not constant. The text should reflect 'bounded' or 'sub-linear' growth rather than 'constant'.
- **[writing]** The paper claims DCE improves consistency by '4.7% and 2.0%' (Methods) based on VBench scores. However, the ablation table (Tab:ab_1) shows the jump from FIFO (95.02) to MIGA (97.82) is 2.8 points, not 4.7. The 4.7% figure likely refers to a specific metric (S.C.) or a different baseline comparison not clearly defined in the text, creating ambiguity about the magnitude of the claimed improvement.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Impact Statement (Section 6) dismisses societal impacts as 'non-exceptional' despite the method enabling infinite, consistent video generation. This capability significantly lowers the barrier for creating deepfakes and disinformation. The statement must be expanded to explicitly address dual-use risks, including identity fraud and misinformation, and propose mitigation strategies.
- **[writing]** The Human Evaluation section (Appendix E001) describes a user study with 8 annotators but lacks details on IRB approval, informed consent procedures, and data privacy protections for the participants. As this involves human subjects, the manuscript must include a statement confirming ethical oversight and compliance with relevant institutional guidelines.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation studies (Tab. 1, Tab. 2) report single-point performance metrics without standard deviations or confidence intervals. Given the stochastic nature of diffusion sampling, statistical significance testing (e.g., paired t-tests) is required to confirm that the observed gains (e.g., +2.03% O.S.) are not due to random variance.
- **[science]** The user study (Tab. 3) relies on a small sample size (48 prompts, 8 annotators) without reporting statistical power analysis or inter-annotator agreement (e.g., Krippendorff's alpha). The claim of 'large-scale' validation is unsupported by these numbers; a more rigorous statistical treatment or larger sample is needed.
- **[science]** The comparison with training-based methods (Tab. 4) lacks a clear definition of the evaluation subset. If the same prompts were used for both train-free and train-based methods, potential data leakage or prompt bias could inflate the train-free scores. The experimental protocol must explicitly state how the test set was constructed to ensure fair comparison.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The user study (Tab. 1, App. D) reports percentages (e.g., 62.23%) from 48 prompts and 8 annotators but lacks confidence intervals or significance tests (e.g., binomial test) to confirm the improvements over FIFO-Diffusion are statistically significant rather than random variation.
- **[science]** Ablation tables (Tab. 2, Tab. 3) present single-point performance metrics without standard deviations or error bars, making it impossible to assess the stability of the reported gains (e.g., the 0.01% memory increase) or the robustness of hyperparameter choices.
- **[science]** The claim of 'state-of-the-art' performance relies on point estimates from VBench and NarrLV; the manuscript should clarify if these benchmarks provide variance estimates or if the authors performed multiple runs to ensure the observed differences are not due to stochasticity in the generation process.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the 'Implementation on Different Foundation Models' section, the sentence 'However, We observe that...' contains a capitalization error. The pronoun 'We' should be lowercase ('we') as it follows a comma and is not the start of a new sentence.
- **[writing]** The 'Acknowledgements' section lists 'Grant No.2022ZD0116403'. Standard English convention requires a space between the abbreviation 'No.' and the number (i.e., 'No. 2022ZD0116403').
- **[writing]** In the 'Limitations and Future Work' section, the phrase 'cat's head and tail suddenly switch places' is slightly ambiguous. Consider clarifying if this refers to a spatial swap or a morphological transformation to ensure precise reader understanding.
