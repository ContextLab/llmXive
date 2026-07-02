# Automated-review action items — DanceOPD: On-Policy Generative Field Distillation

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 4.1, the claim of a 1.6% GenEval improvement over DiffusionOPD (0.833) is inconsistent with the table data (0.849 vs 0.833 yields ~1.92%). Correct the percentage or verify the baseline used.
- **[writing]** In Section 4.1, clarify the specific alpha/beta pairs defining 'train-only' and 'eval-only' CFG baselines to ensure the 7.6% and 1.4% improvement claims are unambiguously supported by Table 3.
- **[writing]** In Section 4.1, the 8.5% GEditBench improvement over the Edit source (4.930 vs 5.347) is accurate (8.46%), but ensure all percentage claims in the text are rounded consistently to avoid minor discrepancies.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption contains a rendering artifact 'Editing$$T2I' which likely indicates a missing LaTeX symbol (e.g., \leftrightarrow) between 'Editing' and 'T2I'.
- **[writing]** Figure 1: The inset legend in the right panel (top-left) is illegible; the x-axis label 's/step' is visible, but the y-axis label and tick values are too blurry to read.
- **[writing]** Figure 2: The caption contains a grammatical error and missing reference: 'Qualitative Examples from .' ends abruptly with a period and no noun phrase.
- **[science]** Figure 2: The collage contains 28 diverse images but lacks any labels, text overlays, or a legend to indicate which specific 'text-to-image' or 'editing' behaviors are being demonstrated in each panel.
- **[writing]** Figure 2: The caption claims the figure shows 'diverse text-to-image and editing behaviors' but does not specify what the 'original generative capabilities' are that are being retained, making the claim unverifiable from the visual alone.
- **[writing]** Figure 3: The caption contains a grammatical omission ('Conceptual Illustration of .') and the title 'DanceOPD' is missing from the sentence structure, making the description incomplete.
- **[writing]** Figure 4: The caption refers to 'Additional Edit Cases' but does not explicitly name the three specific editing tasks shown (Apple material, Piano environment, Armchair lighting), making it harder to map the visual examples to the text description.
- **[writing]** Figure 4: The 'Raw' column in the Grand Piano and Leather Armchair rows displays images that do not match the 'Source' images in the left column (e.g., the piano is in a different room, the chair is in a different setting), which obscures the baseline for evaluating the editing quality.
- **[science]** Figure 5: The caption claims to show 'T2I and Edit Composition' and compares DanceOPD to baselines, but the figure contains no text labels, legends, or row headers to identify which method generated which image. It is impossible to verify the claim that 'several baselines introduce color shift' without knowing which rows correspond to the baselines.
- **[writing]** Figure 5: The column headers (e.g., 'T2I: Buckskin Dusk...') are cropped at the top edge of the image, making the specific prompts used for generation partially illegible.
- **[science]** Figure 6: The caption describes three panels (a, b, c), but the rendered image contains four distinct subplots. The leftmost subplot (T2I Score vs Step) is not referenced in the caption, and the rightmost subplot (GEditBench vs Step) is not described, creating a disconnect between the text and the visual evidence.
- **[writing]** Figure 6: The caption mentions 'where $$ denotes the effective CFG', but the mathematical symbol for the effective CFG is missing from the text, making the sentence incomplete and confusing.
- **[science]** Figure 6: The rightmost subplot (GEditBench-EN Avg) lacks a legend defining the specific line styles (solid vs dashed) and colors for the 'Gen-8', 'Gen-16', etc. series, rendering the data uninterpretable without guessing.
- **[science]** Figure 7: The caption claims to show 'Realism-Field Absorption' and compares DanceOPD to off-policy distillation, but the image is a grid of qualitative samples labeled 'Base', 'Teacher', 'Off-Policy', and 'Ours' without any quantitative metrics, statistical significance indicators, or explicit visual markers demonstrating the claimed 'shift toward more photorealistic texture'.
- **[writing]** Figure 7: The caption states 'DanceOPD absorbs the teacher's realism-oriented field more effectively than off-policy distillation', but the figure lacks a clear legend or annotation explaining what specific visual features constitute 'realism' or how the comparison is quantified beyond subjective visual inspection.
- **[fatal]** Figure 8: The rendered image contains three bar charts with x-axis labels (e.g., 'K1G1', 'Hard MSE', 'MSE') that do not correspond to the caption's description of 'Routing, Objective, and Dense-Query Diagnostics' (e.g., 'same-step accumulation', 'soft teacher mixing'). The figure appears to be a mismatch or placeholder.
- **[fatal]** Figure 8: The legend at the bottom left is cropped and illegible, making it impossible to map the bar colors to the specific experimental conditions or baselines mentioned in the caption.
- **[science]** Figure 8: The y-axis label 'GEditBench-EN Avg' is present, but the specific metric or task (e.g., 'Global Edit', 'Local Edit') is not defined in the caption or axis, making the performance claims ambiguous.
- **[science]** Figure 9: The caption describes 'Training Progression' and 'distillation proceeds', but the image contains no text labels, axis markers, or legends to indicate which column corresponds to which training step or iteration.
- **[science]** Figure 9: The caption claims the figure shows 'Local and Global Edit Composition', yet the displayed rows (cars, landscapes, bikes, flowers, headphones, drinks) appear to be independent single-image generations rather than explicit composition tasks or edits of a base image.
- **[science]** Figure 10: The rightmost panel shows 'Weighted' performance increasing with Trajectory Queries K, contradicting the caption's claim that 'increasing the number of trajectory queries does not improve performance'.
- **[writing]** Figure 10: The left and middle panels lack legends defining the 'Low-t', 'Median-t', 'High-t', 'Local', 'T2I', 'Merged', and 'Global' series, making the ablation trends uninterpretable without guessing.
- **[science]** Figure 11: The caption claims to compare DanceOPD with 'off-policy distillation, joint training, DiffusionOPD, and Flow-OPD', but the figure grid only displays 'Raw', 'Off-Policy', 'FlowOPD', 'Teacher', 'Joint Training', and 'DiffusionOPD'. The 'DanceOPD (Ours)' result is shown as a large standalone image on the left, but the specific 'Off-Policy' baseline shown in the grid is not explicitly labeled as 'Off-Policy Distillation' in the caption context, and the 'Teacher' baseline is included in th
- **[writing]** Figure 11: The 'Raw' and 'Off-Policy' labels in the top row are partially obscured by the image content or have low contrast against the background, reducing legibility.
- **[writing]** Figure 12: The caption refers to 'Local and Global Edits' but the image labels are 'Evening Gown' and 'Rental Room', which do not explicitly indicate the edit type (local vs global) for the reader.
- **[writing]** Figure 12: The caption claims DanceOPD produces 'stronger global transformations' than baselines, but the 'Rental Room' example shows DanceOPD (Ours) as a clean render while baselines like 'Raw' and 'Off-Policy' show messy or cluttered scenes, making the comparison ambiguous without a clear 'before' state or explicit transformation description.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology that is not consistently defined for a broader audience, creating barriers for non-specialist readers. The term "semantic-side" (Section 3.3, Eq. 4) is used frequently to describe the query distribution but is never explicitly defined; readers must infer it means "low-noise" or "high-fidelity" regions of the trajectory. Similarly, "anchor capability" (Introduction, Section 4.1) is used to denote the preserved base capability (e.g., T2I) wi

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical consistency of the proposed method relies heavily on the equivalence between the proposed MSE objective and a KL-divergence minimization, as well as the linearity of the guidance field composition. First, in Section 3.4 and Appendix A.1, the authors derive that minimizing the KL divergence between the student and teacher transition kernels reduces to a velocity MSE objective. This derivation explicitly assumes that the student and teacher share the same local covariance ($\sigma_t^2

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** Claiming the student outperforms the 'edit source' teacher by 8.5% (Sec 1) is an over-claim. Distillation should not exceed the teacher without extra data or different eval protocols. Clarify if the teacher was re-evaluated under identical conditions or if this implies a super-teacher capability, which contradicts standard distillation.
- **[writing]** The claim that the method 'absorbs' CFG (Abstract, Sec 3) overstates the results. Sec 4.1.D shows absorbed and external CFG compose multiplicatively, causing severe degradation if not carefully managed. Temper the claim to reflect that it internalizes the field but requires strict inference-time scaling to avoid over-guidance.
- **[writing]** The conclusion that the method is a 'practical route toward scalable multi-capability visual generation' (Sec 5) is too broad. Experiments are limited to two composition settings and specific models. There is no evidence for scalability to larger models or complex tasks. Restrict the conclusion to the demonstrated capabilities.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper relies on a proprietary realism reward model for evaluation (Sec 4.1.C, App. Settings) without describing its training data, potential biases, or safety guardrails. A description of the reward model's provenance and a discussion of potential failure modes (e.g., bias towards specific demographics or unsafe content) is required to assess the safety of the generated outputs.
- **[writing]** The method involves training on image editing datasets (e.g., GEditBench, OmniEdit) and generating edited images. The manuscript does not explicitly state whether the training data or the generated outputs were screened for sensitive content (e.g., deepfakes, non-consensual imagery, hate symbols). A statement on data curation and content safety filters is necessary.
- **[writing]** The paper discusses "CFG Absorption" (Sec 4.1.D), which internalizes guidance scales. While primarily a performance optimization, this could theoretically be used to bypass safety filters embedded in the inference-time guidance of the base model. The authors should address whether their method preserves or inadvertently bypasses safety constraints of the underlying foundation model.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims significant improvements (e.g., 8.1% on GEditBench) but does not report standard deviation, confidence intervals, or the number of independent training runs. Without variance estimates or a statistical significance test (e.g., t-test), it is impossible to determine if these gains are robust or due to random seed variance.
- **[science]** The 'DiffusionOPD' baseline is described as a 'paper-faithful reproduction' in the appendix. The review requires explicit confirmation that the reproduction code was validated against the original paper's reported numbers on a shared subset before being used as a baseline for comparison, to ensure the 8.1% gain is not an artifact of a weak baseline implementation.
- **[science]** The 'Realism Absorption' experiment relies on a 'proprietary' reward model for evaluation. The paper must provide a detailed description of this model's architecture, training data, and validation metrics, or release a proxy version, to allow independent verification of the claimed 9.9% improvement and the 85.3% gap closure.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report standard deviations or confidence intervals for all quantitative results in Tables 2, 4, 5, and 6. The current tables present single-point averages (e.g., GEditBench Avg) without indicating variance across seeds or runs, making it impossible to assess statistical significance of the reported improvements (e.g., the 8.1% gain over DiffusionOPD).
- **[science]** Clarify the number of random seeds used for all experiments. The text mentions 'reproduced baselines' and 'diagnostic studies' but does not specify if the reported metrics are means over multiple independent runs or single runs. Without this, the robustness of the 'single-query' vs 'dense-query' conclusions cannot be statistically verified.
- **[science]** In Section 4.2 (Multi-Teacher Extension), the claim that 'same-step accumulation... loses 4.6% on average' lacks a statistical test. Please provide p-values or effect sizes to confirm that the observed degradation is statistically significant and not due to random variance in the evaluation metrics.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 4.1 (Main Results), the sentence listing Figure references ('Fig. 5, Fig. 6...') is repetitive and disrupts the flow. Consolidate this list or refer to a single composite figure if the content is identical across them.
- **[writing]** The phrase 'semantic-side' is used frequently (e.g., Sec 3.3, 4.3) without a clear, concise definition in the introduction. While defined technically in the appendix, a brief intuitive explanation in the main text would improve accessibility for readers unfamiliar with the specific rollout coordinate terminology.
- **[writing]** In Section 4.2, the transition between the 'Hard Routing' and 'Same Step Multi-Teacher Accumulation' subsections is abrupt. A brief bridging sentence explaining how these two diagnostics relate to the broader 'Multi-Teacher Extension' goal would improve cohesion.
