# Automated-review action items — UI-MOPD: Multi-Platform On-Policy Distillation for Continual GUI Agent Learning

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a novel method for cross-platform GUI agents, but several factual claims rely on non-existent or unverified external entities, and there are minor numerical inconsistencies between sections. First, the data collection pipeline relies on specific teacher models that appear to be hallucinated. The Appendix (Section "Query Generation") and Section 3.1 explicitly state that "Kimi-K2.6" and "Gemini-3.1-Pro" were used to generate queries and trajectories. As of the current public re

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The text 'Bbox Anotation' contains a spelling error and should be corrected to 'Bbox Annotation'.
- **[writing]** Figure 1: The 'Desktop' and 'Mobile' screenshots are low-resolution and illegible, making it impossible to verify the specific UI elements or text shown.
- **[writing]** Figure 2: The caption 'Desktop task execution example of .' is grammatically incomplete and missing the specific task name or description.
- **[writing]** Figure 2: The top-left speech bubble contains a specific user prompt ('Can you assist me...'), but the figure lacks a corresponding label or title identifying this as the 'User Task' or 'Goal'.
- **[fatal]** Figure 3: The caption 'Mobile task execution example of .' is incomplete and grammatically broken, failing to describe the specific task shown (replying to a gourmet user about Moussaka).
- **[science]** Figure 3: The 'Structured Chain-of-Thought' box contains a factual hallucination; it states the file 'waiver.jpg' is listed 'Jun 2 2026', but the screenshot clearly shows the date as 'Jun 2, 2025'.
- **[writing]** Figure 3: The top-level instruction bubble is cluttered with a cartoon avatar and excessive whitespace, which distracts from the scientific content of the figure.
- **[writing]** Figure 4: The 'Reverse KL Computation' panel contains mathematical notation (e.g., log π(y_t|h_t)) that is illegible due to low resolution, making the specific formula unreadable.
- **[writing]** Figure 4: The 'Router' component is depicted with a speaker icon and dotted lines, but the visual metaphor for 'platform-conditioned routing' is ambiguous without explicit labels on the input/output paths.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 2.1 (Method): The symbol `μ` is introduced in Eq. 3 as an 'adaptive KL mask' but is never defined in the surrounding text. A reader cannot determine if it is a scalar, a vector, or a function of the rollout. Define `μ` explicitly where it first appears (e.g., 'where μ is a binary mask...').
- **[writing]** Section 2.1 (Method): The term 'K3 estimator' is used in the paragraph header and Eq. 5 without a definition or citation. While 'KL' is standard, 'K3' appears to be specific to this work or a very niche subfield. Add a brief clause explaining what the K3 estimator is (e.g., 'a variance-reduced token-level KL estimator') or cite the source.
- **[writing]** Section 2.3 (Reward Design): The variable `f_a` is introduced as 'the fraction of matched dimensions' but the specific dimensions for each action type (e.g., coordinate inclusion, key set equality) are listed as examples rather than a formal definition. An adjacent-field reader cannot verify the calculation without guessing the exact set of dimensions. Explicitly list the dimension set or reference a table/appendix where the full schema is defined.
- **[writing]** Appendix A (Dataset Construction): The term 'AndroidControl*' is used repeatedly with a star superscript. While the text mentions it is an 'evaluated subset', the specific criteria for inclusion/exclusion (beyond '781 trajectories') are not defined in the main text or this section. Define the selection criteria for the star subset at first use to ensure reproducibility.
- **[writing]** Section 3.1 (Experimental Setup): The acronym 'DAPO' appears in the hyperparameter table ('GRPO-based DAPO objective') without being expanded in the text. While 'GRPO' is a known method, 'DAPO' is not standard across the broader ML field. Expand 'DAPO' at first use (e.g., 'Direct Advantage Policy Optimization') or clarify its relationship to GRPO.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Appendix A, the 'Query Generation' paragraph is duplicated verbatim with slightly different phrasing. The first instance mentions Kimi-K2.6 and Gemini-3.1-Pro generically, while the second adds specific environment names (OSWorld, MobileWorld). This redundancy creates a logical break in the narrative flow. Merge these into a single, coherent paragraph.
- **[writing]** Section 1 (Introduction) states the dataset contains 'nearly 10K' trajectories, while Appendix A (Dataset Construction) and Table 1 state '~11.5K' trajectories. While both are approximations, the discrepancy (10K vs 11.5K) is significant enough to cause confusion regarding the dataset scale. Align the numbers in the Introduction to match the specific value in the Appendix/Tables (e.g., 'approximately 11.5K').
- **[writing]** In Appendix A, Figure 1 is labeled `fig:intro` and captioned 'Overview of Unified Cross-Platform Data Collection Harness.' However, `fig:intro` is already used in the main body (Section 1) for the 'Motivation of UI-MOPD' figure. This label collision will cause LaTeX to generate incorrect cross-references (e.g., Section 1's figure will point to the harness diagram). Rename the appendix figure label to `fig:harness_overview`.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract/Intro claim UI-MOPD is 'the first method' to use MOPD for GUI agents. Related Work cites DeepSeek-V4/Nemotron using MOPD. Qualify to 'first to apply MOPD to cross-platform GUI continual learning' to avoid implying the technique itself is novel.
- **[writing]** Abstract/Conclusion claim the method 'mitigates catastrophic forgetting' and enables 'continual adaptation.' Experiments only show static benchmark scores (OSWorld/MobileWorld) without a sequential training/forgetting metric. Hedge to 'preserves performance on tested benchmarks' rather than claiming to solve forgetting.
- **[writing]** Conclusion claims applicability to 'diverse digital environments.' Experiments are limited to desktop and mobile. Narrow the claim to 'desktop and mobile environments' in the abstract and conclusion to match the tested scope.

## paper_reviewer_safety_ethics — verdict: accept

This paper presents a method for training cross-platform GUI agents using multi-teacher on-policy distillation. The research involves collecting interaction trajectories from desktop and mobile environments, training teacher models, and distilling knowledge into a student model.

From a safety and ethics perspective, the work is low-risk. The data collection harness described in the Appendix (Section `app:data_collection_harness`) utilizes synthetic query generation and automated trajectory collection within controlled benchmark environments (OSWorld, MobileWorld, AndroidWorld). The paper explicitly states that trajectories are filtered for quality and success, and no human-subjects data, personal information, or sensitive user interactions are involved in the training or evaluation process. The datasets constructed (Uni-GUI, AndroidControl*) are derived from these synthetic or public benchmark sources, and the paper does not release any raw data containing PII.

The method itself (GUI automation) is a standard area of research in the field. While GUI agents have potential dual-use applications (e.g., automating malicious tasks), the paper focuses on improving task success rates and cross-platform generalization for benign automation. It does not describe capabilities that lower the barrier to specific high-harm activities (such as generating exploits, biological synthesis, or targeted disinformation) beyond the general capabilities of the underlying foundation models (Qwen3-VL). The paper does not claim to bypass security controls or operate covertly.

There are no missing disclosures regarding human subjects, consent, or data licensing that would constitute a safety violation. The use of public benchmarks and synthetic data generation avoids the ethical pitfalls associated with scraping private user data. Consequently, no specific safety or ethics action items are required.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a compelling method for cross-platform GUI agents, but the experimental design currently leaves open several alternative explanations for the reported gains. First, the stability of the results is unverified. Table 2 reports a 5.6 percentage point improvement on MobileWorld (12.0% vs 6.4% for Mixed-SFT) and a 3.2 point gain on OSWorld. However, the paper reports these as single-point estimates without any indication of variance, standard deviation, or the number of random seed

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 and Section 4.3 report single-point success rates (e.g., 38.2%, 12.0%) without any measure of uncertainty (SD, SE, or CI) or number of seeds. In RL-based agent training, performance is highly stochastic. Report mean ± SD over at least 3 independent training seeds for all main results to distinguish stable improvements from random variance.
- **[writing]** The abstract and Section 4.3 claim UI-MOPD is 'significantly better' or shows 'substantial improvements' over baselines (e.g., 12.7% and 55.8% relative gains) but provide no statistical hypothesis tests (e.g., paired t-test, bootstrap) or p-values. Without variance estimates or formal tests, these 'significant' claims are unsupported. Either run statistical tests on seed-level results or rephrase to 'observed improvement' without statistical inference.
- **[writing]** Table 1 compares UI-MOPD against 4 baselines across 2 benchmarks (8 pairwise comparisons) and highlights the best results. No correction for multiple comparisons (e.g., Bonferroni, Holm, or FDR) is mentioned. With multiple tests, the risk of false positives increases. Apply a correction method or explicitly acknowledge the uncorrected multiplicity when interpreting 'best' results.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-structured and readable, with clear logical flow between sections. The abstract effectively summarizes the problem, method, and results. However, there are specific areas where the prose creates friction for the reader. The most significant issue is in the Appendix, Section 2 ("Unified Cross-Platform Data Collection Harness"). There are two consecutive paragraphs both titled "Query Generation." The first paragraph describes generating queries using Kimi-K2.6 for deskt
