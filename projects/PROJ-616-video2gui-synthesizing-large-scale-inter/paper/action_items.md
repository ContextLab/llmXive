# Automated-review action items — Video2GUI: Synthesizing Large-Scale Interaction Trajectories for Generalized GUI Agent Pretraining

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 3.2 (Trajectory Extraction), the paper claims to use 'Gemini-3-Pro' for annotation. The bibliography lists 'Gemini 2.5' (comanici2025gemini). Verify if 'Gemini-3-Pro' is a typo or a distinct model not cited, as this affects the reproducibility of the annotation quality claims.
- **[writing]** The abstract and Section 1 claim pre-training yields 'consistent and substantial improvements of 5–20%'. Table 1 (grounding benchmark) shows a 15.1% gain for Qwen2.5-VL on ScreenSpot-Pro Avg, but Table 2 (offline benchmark) shows a 0.8% gain for Qwen2.5-VL on AndroidControl-Low Type Acc. The '5-20%' range is not supported by the full dataset of results presented.
- **[science]** Section 3.3 claims 'Manual verification of 200 randomly sampled actions confirms that over 95% are accurately parameterized'. The text does not define the criteria for 'accurately parameterized' (e.g., IoU threshold, exact coordinate match) or the inter-annotator agreement for this manual check, making the 95% figure unverifiable.
- **[writing]** Section 5.1 (Scaling Effects) states the model reaches '56.9% at 200 billion tokens' on ScreenSpot-Pro. However, Table 1 lists the final score for Mimo-VL-7B + WildGUI as 56.9, while the text implies this is the Qwen2.5-VL result (which is 41.9 in the table). The text conflates the results of the two different base models.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 1: The caption 'example. [ZvNgczioehg_task_0.png]' is a placeholder that fails to describe the figure's content (a 5-step GUI interaction workflow), making it impossible to understand the figure's purpose or claims without reading the internal text.
- **[science]** Figure 1: The figure is a raw composite of screenshots and JSON data logs rather than a synthesized scientific visualization; it lacks a cohesive layout, clear visual hierarchy, or annotations that explain the significance of the steps to the reader.
- **[writing]** Figure 2: The caption 'example. [EF-Qh1ydNgk_task_4.png]' is a placeholder that fails to describe the figure's content (a 5-step GUI interaction workflow), making it impossible to understand the figure's purpose without reading the internal text.
- **[writing]** Figure 2: The internal text 'Instruction: Set the computer's power plan to High Performance' is not referenced in the caption, creating a disconnect between the figure label and the visual data.
- **[writing]** Figure 3: The caption 'example. [55BzMmeagwU_task_0.png]' is generic and fails to describe the figure's actual content (a step-by-step iPhone Dark Mode tutorial), making it impossible to understand the figure's purpose without reading the internal text.
- **[science]** Figure 3: The figure is a composite of screenshots and raw JSON-like logs without a unifying visual layout or explanatory annotations, making it difficult to distinguish between the system's 'thought' process and the actual GUI state changes.
- **[writing]** Figure 4: The caption 'example. [oXoXz11H4Q4_task_0.png]' is a placeholder and does not describe the figure's content (a step-by-step guide to factory resetting a Tecno smartphone), making it impossible to understand the figure's purpose or context.
- **[science]** Figure 4: The figure displays a sequence of 7 steps for a smartphone task, but lacks a clear title or introductory text explaining the overall objective, which is only partially inferred from the text within the figure itself.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'VLM' at first use. The acronym appears in Section 3 ('VLM-driven approach') and Section 5 ('VLM-based GUI agents') without prior expansion. Use 'vision-language model (VLM)' on first occurrence.
- **[writing]** Replace 'grounding' with 'locating' or 'identifying' in non-technical contexts. The term 'spatial grounding' is used repeatedly (e.g., Section 3.3, 4.2) without a plain-English definition for non-specialists. Consider 'mapping actions to screen coordinates' for clarity.
- **[writing]** Define 'POMDP' at first use. Section 2 introduces 'Partially Observable Markov Decision Process (POMDP)' but the acronym is then used exclusively. Ensure the full term is clear to readers outside reinforcement learning.
- **[writing]** Clarify 'Stage 1' and 'Stage 2' terminology. These terms are used frequently (e.g., Section 4, 5) without a clear, consistent definition of what they refer to (pre-training vs. post-training) in the main text before the appendix.
- **[writing]** Replace 'coarse-to-fine' with 'broad-to-specific' or 'initial screening followed by detailed evaluation' in Section 3.1. While common in CS, the phrase is jargon-heavy for a general audience.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Section 5.1 (Main Results), the text claims Qwen2.5-VL-7B + WildGUI improves from 26.8 to 41.2 on ScreenSpot-Pro. However, Table 2 explicitly lists the result as 41.9. This numerical inconsistency undermines the precision of the reported gains.
- **[writing]** In Section 5.2 (Scaling Effects), the text states the model reaches a peak of 56.9% on ScreenSpot-Pro at 200B tokens. Table 2 reports the final score for Mimo-VL-7B + WildGUI as 56.9, but the text implies this is the Qwen2.5 result or conflates the two models. The scaling curve description needs to explicitly map the specific model architecture to the reported peak value to avoid ambiguity.
- **[writing]** In Section 3.2 (Trajectory Extraction), the authors claim to use Gemini-3-Pro for annotation. However, the bibliography (example_paper.bib) contains a citation for 'Gemini 2.5' (comanici2025gemini) but no entry for 'Gemini-3-Pro'. The reference list must be updated to include the specific source for the model version cited in the methodology.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that the dataset spans 'over 1,500 applications and websites' (Abstract, Table 1) lacks a specific methodology for counting unique entities. Without a definition of how 'application' is distinguished from 'website' or how duplicates are handled, this specific number appears to be an over-estimate or an unverified extrapolation from the raw video count.
- **[science]** The statement that 'Human evaluation shows that the overall annotation accuracy exceeds 80%' (Introduction, paragraph 4) is unsupported by the provided text. The 'Data Quality Check' section (Section 5.4) only reports a Likert-scale user study (score 4.62/5) and inter-rater agreement, not a binary accuracy metric against a ground truth. This specific percentage is an over-claim not backed by the reported evidence.
- **[writing]** The claim that the model 'surpasses state-of-the-art performance' (Abstract) is potentially misleading. Table 2 shows the proposed model (Mimo-VL-7B + WildGUI) scoring 67.6 on OSWorld-G, while Seed1.5-VL scores 62.9. However, Seed1.5-VL is a proprietary model, and the paper does not clarify if the comparison is fair regarding model size, training compute, or access to private data. The phrasing implies a universal SOTA without qualifying the proprietary nature of the competitor.
- **[writing]** The paper claims to process '500 million video metadata entries' (Abstract) but does not explicitly state the source or the time window of this data. Given the rapid evolution of YouTube content, the lack of temporal context for this massive dataset makes the claim of 'generalization' slightly over-reaching without specifying the data freshness.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Impact Statement (Section Impact Statement) is generic and fails to address specific dual-use risks of autonomous GUI agents, such as unauthorized automation, credential theft, or bypassing security controls. A detailed discussion of potential misuse and mitigation strategies is required.
- **[writing]** The data collection pipeline relies on scraping 500 million YouTube videos. The manuscript lacks explicit confirmation of compliance with YouTube's Terms of Service, copyright laws, and the specific licenses of the source videos. Clarification on legal basis for data usage and redistribution is needed.
- **[writing]** The human evaluation study (Section Data Quality Check) involves five expert participants but does not mention IRB approval, informed consent procedures, or how participant anonymity and data privacy were protected during the study.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The human evaluation study (Section 5.4) relies on a sample size of only 300 data points rated by 5 experts. For a dataset of 12M trajectories, this sample is statistically underpowered to support the claim of 'superior quality' across the entire corpus. Please report confidence intervals or conduct a power analysis to justify the sample size, or increase the sample size significantly.
- **[science]** The ablation study (Table 4) reports performance drops (e.g., AndroidWorld 31.9 -> 24.1) without providing standard deviations or results from multiple random seeds. Given the stochastic nature of LLM training and evaluation, single-run results are insufficient to claim the 'necessity' of specific loss components. Please provide variance metrics or re-run experiments with multiple seeds.
- **[science]** The scaling law analysis (Figure 4) claims a 'strong positive correlation' and 'no saturation' based on a single curve. Without error bars or confidence intervals on the performance metrics at each data scale point (0, 50B, 200B tokens), it is impossible to determine if the observed gains are statistically significant or within the noise of the evaluation protocol.
- **[science]** The paper claims 95% accuracy for the spatial grounding stage based on 'manual verification of 200 randomly sampled actions' (Section 3.3). This sample size is too small to robustly estimate a 95% accuracy rate with a narrow confidence interval. Please provide the 95% confidence interval for this accuracy estimate or increase the validation sample size.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Section 5.3 (Data Quality Check): The reported Krippendorff's alpha of 0.84 is strong, but the sample size (300 points rated by 5 experts) is small relative to the 12M dataset. Please report the 95% confidence interval for the alpha coefficient and clarify if the 300 samples were stratified by platform/application to ensure representativeness.
- **[science]** Section 5.1 (Scaling Effects): The scaling law analysis (Figure 4) presents point estimates without error bars or confidence intervals. Given the stochastic nature of training, please report the standard deviation or 95% CI across multiple seeds (or at least clarify if results are from a single run) to validate the statistical significance of the observed gains.
- **[science]** Section 5.2 (Ablation Studies): The ablation results in Table 4 show performance drops (e.g., AndroidWorld 31.9 -> 24.1). Without reported variance or statistical significance tests (e.g., paired t-tests or bootstrap CIs), it is unclear if these drops are statistically significant or within the noise margin of the evaluation protocol.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 5.2 (Scaling Effects), the phrase 'accuracy improves improves' contains a repeated verb. Please correct to 'accuracy improves'.
- **[writing]** In Section 5.1 (Main Results), the sentence 'surpassing both Qwen3-VL-32B at 60.6 and Seed1.5-VL at 62.9' contains a Chinese character '的' (de) instead of 'at' or 'with'. Please replace with English prepositions.
- **[writing]** In Section 3.1 (Meta Info Filtering), the phrase 'DeepSeek-V3 demonstrates high alignment with human judgment' is vague. Consider specifying the metric (e.g., 'achieves 92% agreement') or citing the specific validation result mentioned in the same paragraph.
- **[writing]** In Section 4.1 (Implementation Details), the phrase '160 CPU cores, 512 GB system memory, and 256 NVIDIA GPUs' lacks specific GPU model names (e.g., A100, H100). While not strictly a writing error, adding the model name improves clarity and reproducibility of the hardware description.
