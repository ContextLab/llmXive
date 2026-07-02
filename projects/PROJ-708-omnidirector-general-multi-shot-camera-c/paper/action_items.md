# Automated-review action items — OmniDirector: General Multi-Shot Camera Cloning without Cross-Paired Data

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Claim that LTX-LoRA's transitions are 'artifacts of leakage' lacks evidence. High leakage does not prove the transition mechanism is an artifact; ablation or qualitative proof is needed to support this causal assertion.
- **[writing]** T-Pre definition uses degrees (°) for translation error, which is physically incorrect. Translation is a distance metric, not angular. This typo or error makes the reported 72.74% metric uninterpretable.
- **[writing]** The paper relies on 'Qwen3-VL' (citing a 2025 preprint) which may not exist yet. The methodology's validity depends on this model's actual capabilities. Clarify if this is a hypothetical citation or a real, available model.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption states 'Orthogonal lines represent the ceiling and floor (red and blue)', but the Top View plot shows a grid of red and blue lines on the X-Z plane (floor/ceiling) while the Front/Side views show yellow vertical lines (walls). However, the Front/Side view axes are labeled 'Y Axis' (vertical) and 'X/Z Axis' (horizontal), but the grid lines are yellow. The caption says vertical lines (yellow) denote walls, which matches the Front/Side views. But the Top View shows red and blu
- **[science]** Figure 2: The 'Dolly Zoom' row shows the subject (green cube) shrinking significantly across the three panels, contradicting the caption's claim that the subject 'remains fixed in size'.
- **[writing]** Figure 2: The text labels inside the bottom row panels (e.g., 'TRACKING', 'CUBE=3D subject') are illegible due to low resolution.
- **[writing]** Figure 3: The caption refers to a 'PE Agent' in the bottom panel, but the diagram labels this component as 'Camera Prompt Generator', creating a terminology mismatch.
- **[writing]** Figure 3: The 'Visual Encoding' section uses color-coded blocks (blue, pink, green) for latent variables, but lacks a legend explicitly mapping these colors to the specific inputs (Reference Image, Camera Grid, Noisy Latent).
- **[writing]** Figure 5: The caption contains a spelling error ('Qualitive' instead of 'Qualitative').
- **[writing]** Figure 5: The label 'LTX+LoRA' is likely a typo for 'LTXV+LoRA' or similar, given the context of video generation models, though this cannot be confirmed without external knowledge.
- **[science]** Figure 6: The row labels 'w/o Tran. PE' and 'w/o Sem. Fusion' are ambiguous; the caption does not define what 'Tran. PE' or 'Sem. Fusion' stand for, making the ablation study's specific contributions unclear.
- **[science]** Figure 6: The 'Ref. Video' rows are labeled but the corresponding generated results in the 'Full' rows are not explicitly linked to specific reference shots (e.g., 'first-person view', 'medium shot'), making it difficult to assess if the model correctly cloned the specific camera motion.
- **[writing]** Figure 7: The top section is labeled 'Reference Video Condition' but lacks a column header for the 'Ref' input, unlike the bottom section which explicitly labels 'Ref', 'Condition', and 'Synth'.
- **[writing]** Figure 7: The top section's 'Synth' column displays static images (e.g., Harry Potter, deer) rather than video frames or motion sequences, which contradicts the caption's claim of driving 'camera motion'.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'MMDiT' at first use in the Introduction. The acronym appears in the abstract and introduction without expansion, hindering non-specialist readers."
- **[writing]** Replace '6DoF' with 'six degrees of freedom' on first occurrence in Related Work to ensure accessibility for readers unfamiliar with robotics/graphics terminology."
- **[writing]** Define 'PE Agent' or 'Prompt Expansion Agent' fully before using the abbreviation. The term 'PE Agent' appears in the Method section without prior definition."
- **[writing]** Replace 'LoRA' with 'Low-Rank Adaptation' at first mention in the Experiments section. Acronyms for specific techniques should be defined for general audiences."
- **[writing]** Define 'GSB' (Good/Same/Bad) explicitly before using the abbreviation in the Experiments section. The metric name is introduced as an acronym without context."
- **[writing]** Replace 'T-Pre' and 'R-Pre' with 'Translation Precision' and 'Rotation Precision' (or similar plain terms) on first use, or define them immediately. These are non-standard abbreviations that obscure meaning."
- **[writing]** Define 'TransNet-V2' and 'DPA-V3' upon first mention in the Method section. While these are model names, their function (shot detection, pose estimation) should be briefly clarified for non-experts."

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 4.1.1 defines RTE and T-Pre using angular thresholds (20 degrees) for translation error. Translation is typically a distance metric, not an angle. Explicitly clarify if this measures the angular deviation of the translation vector to avoid confusion with standard Euclidean distance errors.
- **[science]** Section 4.1.1 claims pose estimators have inherent errors, yet Table 1 relies on DPA-V3 for both reference and generated poses to compute RRE/RTE. If ground truth is also estimated, metrics measure estimator consistency, not generation accuracy. Clarify if true ground truth exists or if the 'errors' refer to the evaluation noise floor.
- **[science]** Section 4.2.2 claims LTX-LoRA's transition success is an 'artifact of leakage' due to high leakage rates. High leakage does not logically preclude learning transitions. Provide evidence that transitions are side-effects of leakage rather than genuine learning, as the current causal link is unsupported.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim of 'director-level control' (Abstract, Intro) is overreaching. The paper demonstrates camera motion cloning but lacks evidence for controlling narrative depth or emotional atmosphere. Qualify this claim to 'camera motion control' or provide metrics for narrative alignment.
- **[science]** The 'Emergent Camera Understanding' section (Section 5.3) overstates generalization. Claiming the model executes dolly zooms 'without requiring explicitly curated training data' (lines 430-435) is unsupported, as Figure 2 shows these were rendered in training. Clarify that this is learned behavior, not zero-shot emergence.
- **[writing]** The assertion that the Prompt Expansion Agent 'completely decouples' camera signals (Section 4.2, lines 330-332) is absolute and unsupported. Table 1 shows a 3.38% leakage rate. Replace 'completely decouples' with 'significantly reduces leakage' to align with quantitative evidence.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript relies on Qwen3-VL and Gemini 3.1 Pro for prompt generation and evaluation (Sections 3.2.1, 4.1). Explicitly disclose the data privacy policies of these third-party APIs regarding the reference videos and generated prompts to ensure no sensitive content is inadvertently transmitted or stored.
- **[writing]** The training dataset comprises 1.8M internet videos (Section 4.1) without mentioning IRB approval, consent procedures, or copyright compliance. Add a statement clarifying the legal and ethical basis for using this data, specifically addressing potential copyright infringement and the exclusion of personally identifiable information (PII).
- **[writing]** The "emergent" capability to clone camera motion from raw RGB videos (Section 4.3) lowers the barrier for generating deepfakes or misleading content. Include a dedicated "Ethical Considerations" subsection discussing potential dual-use risks (e.g., misinformation, non-consensual content) and proposed mitigation strategies.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Ground truth for RRE/RTE relies on DPA-V3, a monocular estimator prone to scale drift. The paper lacks a sensitivity analysis or error bounds for these labels. Without quantifying the evaluator's noise floor, reported improvements may reflect estimator bias rather than true model superiority.
- **[science]** GSB and Sem-Pre metrics rely solely on Gemini 3.1 Pro without human validation or inter-rater reliability checks. Relying on an LLM judge for primary qualitative benchmarks introduces significant bias risk. Please provide human evaluation results or validate the judge's correlation with human preference.
- **[science]** Ablation study (Table 2) shows large metric drops (e.g., Sem-Pre 83% to 38%) but lacks statistical significance reporting. Please provide standard deviations, confidence intervals, or details on random seeds to rule out variance as a factor in these dramatic performance changes.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The evaluation metrics R-Pre and T-Pre are defined with inconsistent units: R-Pre uses a 4° angular threshold, while T-Pre uses a 20° threshold for translation error. Translation error (RTE) is typically measured in distance (meters) or normalized units, not degrees. Clarify the definition of T-Pre and ensure the threshold is appropriate for the metric's unit.
- **[science]** The GSB (Good/Same/Bad) pairwise comparison results in Table 3 lack statistical significance testing (e.g., binomial test or confidence intervals). With sample sizes implied by the percentages, the observed differences (e.g., 88.52% vs. baseline) should be validated to ensure they are not due to random chance.
- **[science]** The ablation study in Table 2 presents point estimates for metrics (e.g., RRE, RTE) without reporting variance (standard deviation) or confidence intervals. Given the stochastic nature of diffusion models and the evaluation set size (1,094 samples), uncertainty quantification is necessary to assess the robustness of the reported improvements.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.1.1, the sentence 'Only 3D grid lines are used to indicate the directions of spatial coordinate axes, thereby clearly presenting the geometric structure of the space and the camera motion trajectory' is slightly wordy. Consider simplifying to 'Only 3D grid lines indicate spatial axes, clearly presenting the geometric structure and camera trajectory.' to improve flow.
- **[writing]** In Section 3.2.1, the phrase 'harmoniously integrates different control signals by systematically describing camera motion and visual content through understanding signal relationships' is vague and repetitive. Clarify the specific mechanism of 'understanding signal relationships' or rephrase for conciseness.
- **[writing]** In Section 4.1, the definition of T-Pre states 'relative translation error below 20°'. Since translation is a vector, 'degrees' is likely a typo for 'meters' or a normalized unit. This ambiguity impairs understanding of the metric.
- **[writing]** In Section 4.2.2, the sentence 'While LTX-LoRA can generate occasional shot transitions, the results in Table 1 indicate that this capability is actually an artifact of information leakage rather than genuine camera control' is a strong claim. Ensure the phrasing is precise and supported by the preceding text to avoid sounding speculative.
