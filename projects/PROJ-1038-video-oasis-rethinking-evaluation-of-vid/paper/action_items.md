# Automated-review action items — Video-Oasis: Rethinking Evaluation of Video Understanding

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper makes several strong claims regarding the prevalence of "shortcuts" in video benchmarks and the resulting performance of state-of-the-art models. While the methodology for auditing benchmarks is sound, there are specific instances where the textual claims are not fully supported by the provided evidence or rely on unverifiable external resources. First, the claim in Section 4.2 that models perform "marginally above random guessing" is an overstatement given the data. The text cites a r

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1b: The caption claims 'Benchmarks with higher shortcut ratios tend to report higher accuracy,' but the chart shows a negative correlation where accuracy (blue bars) generally decreases as the shortcut ratio (red line) decreases. The trend contradicts the caption's claim.
- **[writing]** Figure 1b: The x-axis labels for the benchmarks are rotated at a steep angle, making them difficult to read and cluttered.
- **[science]** Figure 3: The caption claims panel (b) shows 'Questions incorrectly filtered by the frame shuffling test,' but the visual examples (baseball, basketball) explicitly highlight 'Temporal Context' and sequential events ('after the second ball'), which are the exact type of temporal dependencies the frame shuffling test is designed to detect. This contradicts the caption's assertion that these were 'incorrectly filtered' and should have been removed.
- **[writing]** Figure 3: Panel (a) bottom example uses the label 'Ambiguous Subject' to describe a scene with multiple bounding boxes, but the visual evidence (red vs. green boxes) suggests the issue is 'Object Tracking' or 'Identity Consistency' rather than subject ambiguity, as the question asks for a relation between two specific entities.
- **[writing]** Figure 5: The caption states this figure shows 'Fine-Grained Perception Challenges,' but the internal text labels explicitly categorize the examples as 'Living Room Recognition' and 'Background Tracking' (Spatial Temporal Grounding), creating a mismatch between the figure's title and its content.
- **[writing]** Figure 5: The text 'Why Video Native Challenges?' is repeated as a header for both examples, which is redundant and disrupts the visual flow of the qualitative examples.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 5.1 uses 'AKS' without expansion. Define as 'Adaptive Keyframe Sampling (AKS)' at first use.
- **[writing]** Section 3.3 refers to 'sensitivity check' and 'redundancy checks' without linking to the capitalized definitions in 3.1. Clarify as 'the Sensitivity test' and 'the Redundancy test' to distinguish from generic terms.
- **[writing]** Section 5.2 introduces 'Qwen3-VL_voting' as an 'oracle ensemble baseline' without defining the aggregation rule. Specify 'logical OR' or 'majority vote' explicitly in the definition clause.
- **[writing]** Section 3.1 introduces 'Bag-of-Frames (BoF)' but the acronym 'BoF' is used immediately. Ensure the full expansion 'Bag-of-Frames (BoF)' is clearly presented before the acronym is used in subsequent sentences.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 5.3 text is truncated mid-sentence ('Video-R1 (26.3%) } \ \texttt{< Definition...'), cutting off the RLVR analysis. The conclusion about RLVR effectiveness does not follow from the missing premise. Complete the sentence and state the finding derived from Table 11.
- **[writing]** Abstract claims '55% of samples are solvable without visual/temporal input,' but Section 3.2 Table 3 shows a range (44.6%-63.0%) for strict consensus (c=3). The body does not define how the specific '55%' aggregate was calculated. Explicitly state the calculation method or qualify the Abstract claim to match the data.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract: The '55%' shortcut claim relies on a strict consensus threshold (c=3) in Table 5, while Table 3 shows 92.7% under relaxed conditions (c>=1). Scope the claim to 'under strict consensus' or acknowledge the higher prevalence to avoid understating the issue.
- **[writing]** Abstract & Sec 4.2: Claiming SOTA models perform 'marginally above random' is inaccurate for Gemini-2.5-Pro (46.7% vs 25.6% baseline). Scope this to 'open-source Video-LLMs' to avoid misrepresenting frontier proprietary model capabilities.
- **[writing]** Sec 5.2: The claim that reasoning strategy is 'as impactful as raw scale' lacks a scaling study. The oracle ensemble only compares modes within one model. Narrow to 'can close the gap between current open-source and frontier models'.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a diagnostic framework (Video-Oasis) for auditing existing video understanding benchmarks to identify "shortcut" samples that can be solved without visual or temporal evidence. The work involves re-evaluating public benchmarks (e.g., EgoSchema, VideoMME, MLVU) and running automated tests (e.g., blind tests, frame shuffling) on them.

From a safety and ethics perspective, the research is low-risk. The methodology does not involve:
1.  **Human Subjects:** The "human-in-the-loop" verification mentioned (Section 3.1, Criteria 3) refers to inspecting annotation quality of existing public datasets, not collecting new data from human participants. No IRB/ethics statement is required for this type of secondary analysis of public data.
2.  **Dual-Use Harm:** The paper does not generate new capabilities for deception, surveillance, or cyber-attacks. Instead, it aims to *reduce* the overestimation of model capabilities, which is a safety-positive outcome for the field.
3.  **Data Privacy:** The work relies on existing public benchmarks. There is no indication of scraping private data, releasing PII, or violating data licenses in the context of the *new* artifacts produced (the filtered set and the diagnostic code). The authors explicitly state code availability and the nature of the distilled dataset.
4.  **Bias/Fairness:** While the paper discusses benchmark flaws, it does not introduce new biases or fail to address a specific, identifiable harm to a demographic group that the paper's own results expose.

The paper appropriately focuses on methodological rigor in evaluation rather than deploying systems with direct societal impact. No specific safety disclosures or mitigations are missing given the nature of the work. The verdict is **accept** with no action items required for this lens.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling diagnostic framework, Video-Oasis, to audit video benchmarks. However, the evidentiary strength of the core quantitative claims is weakened by a lack of reported variance and insufficient controls in the ablation studies. First, the headline finding that "55% of existing benchmark samples are solvable without visual input" (Abstract) and the detailed breakdowns in Table 2 and Table 3 are presented as aggregate point estimates. The paper does not report standard de

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The statistical treatment in this paper is generally descriptive, which is common for benchmark auditing papers, but it lacks necessary rigor in quantifying uncertainty and validating baselines. First, the paper relies heavily on aggregate accuracy percentages (e.g., "55% of samples," "92.7% shortcut ratio," "35.6% accuracy") presented as precise point estimates in Tables 2, 3, 4, 5, 6, 7, 8, 9, and 10. There is no reporting of standard deviation (SD), standard error (SE), or confidence interval

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** Section 5.3, paragraph 2: The sentence listing RLVR insights ends abruptly with 'Video-R1 (26.3%) }' and is followed by a LaTeX fragment, cutting off the conclusion. Complete the sentence to state the finding regarding reward design effectiveness before the list ends.
- **[writing]** Section 3.1, paragraph 3: The sentence 'Since video data are long and information-dense, video-QA annotations can be ambiguous...' uses 'are' with the singular subject 'data' (often treated as singular in modern usage, but 'data' is plural in strict academic style). For consistency with the rest of the paper's formal tone, consider 'Since video data is long...' or 'Since video data are long...' (ensure consistency with other instances of 'data' in the text).
- **[writing]** Section 4.1, paragraph 2: The phrase 'We then consolidate these initial clusters into five unified categories that capture the dominant capabilities required by the Video-Oasis-filtered samples' is slightly wordy. Consider tightening to 'We consolidate these into five categories capturing the dominant capabilities required by Video-Oasis-filtered samples.' to improve flow.
