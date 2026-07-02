# Automated-review action items — ShutterMuse: Capture-Time Photography Guidance with MLLMs

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: reject

- **[fatal]** Citations for baselines like 'GPT-5.5', 'Gemini-3.5', and 'Nano-Banana-Pro' refer to non-existent or future-dated models. Claims of superiority over these baselines are factually unsupported and unverifiable.
- **[science]** The dataset construction relies on 'Nano-Banana-Pro' for person removal. As this tool appears fictional, the reproducibility of the 130K dataset and the validity of the subject-side guidance claims are compromised.
- **[fatal]** The paper cites 'du2026venus' and 'moonshotai2025kimik26'. These future-dated references invalidate the experimental comparison, as the models do not exist in the current scientific record.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2: The 'Three-way decision scheme' bar charts show 'Refine' at 76.2% (left) and 80.0% (right), but the corresponding inner donut slices for 'Photographer-side Guidance' are 77.5% and 43.2% respectively. The 'Refine' category in the bar chart does not match the 'Photographer-side Guidance' category in the donut chart, creating a disconnect between the visualizations.
- **[writing]** Figure 2: The legend text 'Still life:27K' and 'Still life:56' is likely a typo for 'Still life' (singular) or 'Still lifes', and the counts (27K vs 56) suggest a massive discrepancy in scale between the Dataset and Bench that is not explained in the caption.
- **[science]** Figure 4: The pipeline shows 'Human Experts' performing 'Rectification' on pose keypoints, but the caption states the keypoints are 'verified' without specifying the verification method or agent, creating ambiguity about the data quality assurance process.
- **[writing]** Figure 4: The 'Assistant' output box in panel (a) displays raw JSON data (visibility, keypoints_xyn) and a visualization, but the caption does not explicitly mention that the pipeline outputs structured pose data alongside the scene, which is a key component of the 'subject-side guidance'.
- **[writing]** Figure 5: The caption states 'Qualitative comparisons of different models,' but the image contains two distinct sections: (a) a comparison of three models and (b) a demonstration of ShutterMuse's interactive features. The caption should explicitly describe both parts to match the visual content.
- **[writing]** Figure 5: The sub-captions '(a)' and '(b)' are present in the image but are not referenced or described in the main figure caption, making the structure ambiguous.
- **[science]** Figure 6: The 'Original Photo' column displays images containing people (e.g., the person on the bicycle), which contradicts the caption's description of 'subject-side guidance' where portrait images are converted into 'person-free scenes' to serve as the background for pose recommendations.
- **[writing]** Figure 6: The column headers ('Original Photo', 'Nano-Banana-Pro', etc.) are repeated for the top and bottom rows of images, creating visual clutter and redundancy.
- **[science]** Figure 7: The legend defines 'Refine' (yellow circle) and 'Reject' (green x) markers, but these series are not plotted in subplots (b) or (c), which only show 'Keep' and 'Overall'. This creates ambiguity about whether 'Refine'/'Reject' data is missing or intentionally omitted.
- **[writing]** Figure 7: Subplot (d) y-axis label is truncated to 'num' instead of 'Number' or 'Count', reducing clarity.
- **[science]** Figure 8: The caption states the second row shows 'reject cases,' but the image labels the second row as 'Defects' and the top row as 'Refine', 'Reject', 'Keep'. The visual layout (3 columns) contradicts the caption's description of rows (Refine, Reject, Keep). Specifically, the top row contains a 'Reject' example (middle column) and a 'Keep' example (right column), which conflicts with the caption claiming the first row is 'refine cases'.
- **[writing]** Figure 8: The legend at the top ('Refine', 'Reject', 'Keep') uses colored squares that do not match the background shading of the rows below. The top row has a pinkish background (matching 'Refine'), the middle row has a blueish background (matching 'Reject'), and the bottom row has a greenish background (matching 'Keep'), but the text labels inside the rows ('Defects', 'Strength') do not align with the row's assigned category in the caption.
- **[science]** Figure 9: The caption claims poses 'float slightly,' but the visualization shows severe structural failures where the skeleton is misaligned with the scene geometry (e.g., legs passing through the chair in the top row, torso floating in mid-air in the bottom row). The caption understates the magnitude of the failure shown.
- **[writing]** Figure 9: The figure lacks panel labels (e.g., a, b, c) to distinguish the different failure examples, making it difficult to reference specific cases in the text.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript exhibits a high density of acronyms and specialized terminology that, while standard within the specific sub-field of multimodal AI and computer vision, may hinder accessibility for a broader audience or readers from adjacent disciplines. The primary issue is the introduction of acronyms without explicit definition at their first occurrence. Specifically, the term MLLM (Multimodal Large Language Model) is used repeatedly in the Abstract and Introduction without being spelled out f

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Clarify the logical link between the 'reject' class definition (non-croppable defects) and the RSR/MLLM-Score metrics. The current scoring for 'reject' samples appears circular (score=1 iff predict 'reject'), failing to measure the model's ability to identify specific defects versus simply classifying.
- **[science]** Justify why optimizing for salient object coverage (R_mask) logically leads to expert-defined 'refine' outcomes. Experts may exclude salient but distracting objects, creating a misalignment between the RFT reward signal and the IoU/MLLM-Score evaluation targets.
- **[science]** Resolve the contradiction between training for exact visibility matching (R_sub) and evaluating for 'multiple plausible poses'. Training on a single ground-truth visibility state conflicts with the evaluation premise that multiple valid solutions exist.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several strong claims regarding the performance and capabilities of ShutterMuse that slightly exceed the evidence provided in the results tables. First, the Abstract and Introduction repeatedly claim that ShutterMuse achieves the "best overall photographer-side performance among evaluated baselines." While ShutterMuse leads in IoU, BDE, and Refinement Success Rate (R), Table 1 clearly demonstrates that it does not outperform all baselines on every metric. Specifically, Qwen3-VL-3

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The dataset construction pipeline (Sec 4.1) relies on 'Nano-Banana-Pro' to remove subjects from portrait images to create 'person-free scenes.' This raises significant privacy and consent concerns regarding the source of the original portrait images. The paper must explicitly state the provenance of these images (e.g., public datasets, user-uploaded content) and confirm that appropriate consent was obtained for the original subjects before their likenesses were processed and used for training.
- **[writing]** The subject-side guidance task involves generating pose recommendations for humans in specific scenes. There is a risk of generating poses that could be unsafe, physically impossible, or culturally inappropriate for the specific context. The paper should include a discussion on safety filters or constraints implemented to prevent the model from suggesting harmful or dangerous poses, and clarify if any safety guidelines were provided to the human annotators during the verification process.
- **[writing]** The evaluation of subject-side guidance uses an MLLM judge to score 'physical plausibility' and 'scene interaction' (Sec 4.2, App B). While this avoids direct human testing, the training data generation involved human annotators reviewing poses. The paper should clarify if the annotators were provided with safety guidelines to reject poses that might lead to injury or if the dataset includes any exclusion criteria for hazardous scenarios.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The subject-side evaluation relies entirely on MLLM judges (Gemini-3.0-Pro) for physical plausibility and aesthetics without reporting inter-annotator agreement or a robust human baseline beyond a small ranking study. Given the subjective nature of 'aesthetics' and 'plausibility,' the paper must clarify the reliability of the MLLM judge or provide a larger, statistically powered human evaluation to validate the 0.34 vs 0.35 mean score difference.
- **[science]** The photographer-side 'Reject' and 'Keep' success rates (RSR/KSR) show extreme variance across baselines (e.g., 0.00% for specialized models vs 82.76% for ShutterMuse). The benchmark size for these specific classes is not explicitly stated in the text (only 421 total samples). Please report the exact class distribution (n_keep, n_reject, n_refine) to assess if the high RSR/KSR is driven by a small sample size or class imbalance.
- **[science]** The reinforcement learning reward $R_{mask}$ uses BiRefNet to define 'salient object' coverage. BiRefNet is a general-purpose model, not a photography-specific ground truth. The paper should discuss the potential noise introduced by using an off-the-shelf saliency detector as a proxy for 'correct composition' and how this might bias the model toward specific types of subjects (e.g., people) over others.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The user study (Sec. 6) reports a Spearman rank correlation of 0.90 between MLLM and human rankings but provides no confidence interval or p-value. With only 100 samples and 6 raters, the statistical significance of this correlation is unknown. Please report the 95% CI and p-value for the SRCC.
- **[science]** The MLLM-Score metric relies on a single judge (Gemini-3.0-Pro) without reporting inter-rater reliability or variance estimates. For the subject-side task, where multiple poses are plausible, a single deterministic score may be unstable. Please report the standard deviation of scores across multiple judge runs or multiple judges.
- **[science]** In the ablation study (Table 4), performance differences between variants (e.g., IoU 74.30 vs 74.10) are small. The paper does not state whether these differences are statistically significant or if they fall within the margin of error of the benchmark evaluation. Please add significance testing (e.g., paired t-test or bootstrap) for ablation comparisons.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5 (ShutterMuse), the JSON schema description for photographer-side guidance states that an empty value indicates 'reject', but the text later says '[0,0,1,1] indicates keep'. This creates ambiguity: is 'reject' an empty string, null, or a specific token? Clarify the exact JSON structure for all three decision types to ensure reproducibility.
- **[writing]** Section 4.2 (CaptureGuide-Bench) introduces the 'ratio following rate (RFR)' metric with Equation 1, but the entire paragraph and equation are commented out in the LaTeX source. If RFR is not used in the final evaluation, remove the commented code to avoid confusion. If it is used, uncomment and ensure the text explains its inclusion in the results.
- **[writing]** The abstract and Introduction mention '130K samples' for the dataset, but Section 4.1 specifies '100K photographer-side' and '30K subject-side'. While the sum is correct, the phrasing 'approximately 130K' in the abstract followed by exact numbers later is slightly inconsistent. Consider using '130,000' or '130K' consistently to match the precision of the body text.
- **[writing]** In the 'Reinforcement Fine-Tuning' section, the text defines $R_{	ext{mask}}$ and $R_{	ext{photo}}$ but references a coverage threshold $	au_m$ without defining its value in the text (it is defined in Section 6.1). For better flow, define $	au_m$ when first introduced in the method section or explicitly cross-reference the value.
