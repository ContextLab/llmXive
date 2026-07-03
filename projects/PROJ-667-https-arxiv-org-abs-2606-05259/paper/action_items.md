# Automated-review action items — VideoKR: Towards Knowledge- and Reasoning-Intensive Video Understanding

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** The Introduction claims the benchmark is filtered so that 'single-frame probing fails for all three frontier models (Claude-4.5-Sonnet, Qwen3-VL-235B-A22B, GPT-5.2).' These model names (e.g., 'GPT-5.2', 'Claude-4.5') appear to be hallucinated or future-dated, as no such public models exist as of the paper's context. This undermines the factual accuracy of the benchmark's difficulty claim.
- **[writing]** Table 1 and the Abstract state the corpus contains '145K newly collected CC-licensed videos' and '315K examples.' However, the 'Domain Knowledge Bank' subsection claims 'numknow = 63,745 knowledge points.' The relationship between 63k knowledge points and 145k videos (avg ~2.3 videos per point) is not explained, nor is the derivation of 315k QA pairs from these points clear. The claim of 'expert-validated selection' needs specific citation or methodology to support the scale.
- **[fatal]** The paper cites 'GPT-5.2' and 'Claude-4.5-Sonnet' in the Introduction and Table 2 as baselines. These models do not exist in the public domain or the provided bibliography. Citing non-existent models as state-of-the-art baselines is a critical factual error that invalidates the comparative performance claims.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 6: The caption states the reasoning process is 'concise and abbreviated,' but the image displays full, detailed reasoning blocks with no visible abbreviation or truncation, creating a mismatch between the figure's content and its description.
- **[writing]** Figure 6: The caption contains a grammatical error ('A example' should be 'An example').
- **[writing]** Figure 9: The 'Core Skills' section lists 'Basic Video Perception' but the diagram below it labels the skills as 'Knowledge' and 'Reasoning', creating a mismatch between the list and the visual representation.
- **[writing]** Figure 9: The 'Example of Collected CC-licensed Video' section displays video thumbnails with timestamps (00:35, 00:38, etc.) but lacks a clear legend or label explaining what specific frames or events these timestamps represent in the context of the QA examples.
- **[writing]** Figure 10: The caption states '(Right) Statistics of and training corpus', but the right side of the figure contains a 'Data Quality Control' pipeline diagram, not statistical charts or tables.
- **[writing]** Figure 10: The caption contains a grammatical error ('Statistics of and training corpus') and appears to mismatch the visual content on the right.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on undefined acronyms and LaTeX-specific macros that significantly hinder readability for non-specialists or readers viewing the compiled PDF without access to the source code definitions. In the Abstract, the term "CoT" (Chain-of-Thought) is used without definition. While common in the field, the paper's stated goal of "Knowledge- and Reasoning-Intensive Video Understanding" suggests a broader audience where this acronym should be spelled out. More critically, the

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** The claim that single-frame probing fails for all cited frontier models contradicts Table 2 (e002), where GPT-5.4 scores 63.2% on VideoKR-Eval. If single-frame access truly failed, scores should be near random chance.
- **[writing]** The paper states a 315K corpus but uses a 201K SFT subset without explicitly defining the logical derivation or partitioning criteria between the 201K SFT and 114K RL sets.
- **[writing]** The video collection section mentions "49% (saturated)" without defining the metric or explaining the logical step from scenario generation to the final 145K video count.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** "The paper makes several strong claims regarding the novelty and difficulty of its proposed benchmark and the resulting model performance that appear to overreach the provided evidence.\n\nFirst, the Introduction asserts that the VideoKR-Eval benchmark is \"filtered to require genuine video reasoning\" specifically because \"single-frame probing fails for all three frontier models.\" This is a definitive claim about the nature of the data that is not substantiated by the results presented. Table

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The Impact Statement (Section 6) claims annotators were paid $13/h and gave informed consent, but lacks specific IRB approval numbers or the name of the ethics review board. For a dataset involving human labor and potential sensitive content, explicit IRB/ethics committee approval details are required to verify compliance with institutional standards.
- **[writing]** The paper mentions using YouTube API to collect CC-licensed videos (Section 3.2) but does not detail the content safety filtering process. Given the scale (145K videos), there is a risk of inadvertently including harmful, hateful, or non-consensual content. A description of the safety filters (e.g., Microsoft Azure Content Safety API usage details) and the protocol for handling flagged content is needed.
- **[writing]** The dataset includes 145K videos across professional domains (Healthcare, Engineering). The authors must explicitly state whether any personally identifiable information (PII) or private patient data was scrubbed from the video sources, especially for the Healthcare subset, to ensure compliance with privacy regulations (e.g., HIPAA, GDPR) before public release.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The ablation study in Table 2 (e001) lacks statistical significance testing (e.g., p-values or confidence intervals) for the reported gains (e.g., +1.1% on VideoKR-Eval). Given the small margins in some comparisons, the robustness of these improvements against random seed variance is unproven.
- **[science]** The claim that the VideoKR-Eval benchmark is 'challenging' because single-frame probing fails (Introduction, e000) is not empirically supported by a dedicated ablation or control experiment in the provided text. A specific experiment demonstrating the failure of single-frame baselines on this specific benchmark is required to validate this central premise.
- **[science]** The data construction pipeline relies on 'Expert-validated selection from 7 frontier models' (Table 1, e000) but does not report inter-annotator agreement (IAA) or expert consistency metrics. Without IAA scores, the reliability of the 'high-quality' CoT rationales and the potential for model bias in the synthetic data generation cannot be assessed.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance (e.g., p-values, confidence intervals, or standard deviations over multiple seeds) for the performance gains in Table 2 and Table 3. Single-run point estimates are insufficient to claim 'state-of-the-art' or 'significant' improvements over baselines like VideoAuto-R1.
- **[science]** Clarify the statistical methodology for the benchmark difficulty claim in Section 1. The assertion that 'single-frame probing fails for all three frontier models' requires a formal hypothesis test or a clear definition of the failure threshold (e.g., accuracy < 30%) and the sample size used to derive this conclusion.
- **[science]** In Table 1 (Ablation Studies), the use of single-point accuracy scores without error bars or variance metrics makes it impossible to assess the stability of the 'Skill-Oriented Data Composition' findings. Please provide results averaged over at least 3 random seeds with standard deviations.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2 (Video Collection), the sentence 'Scenario generation (LLM‑produced 1–3 realistic situations per knowledge point) → YouTube API search (top‑10 CC‑licensed videos, $$49 % (saturated), while \ours remains challenging ($pprox$42 %).' is grammatically broken and contains LaTeX syntax errors ($$49 %). It needs to be rewritten as a complete sentence to clarify the saturation comparison.
- **[writing]** The caption for Figure 2 in the LaTeX source is malformed. It begins with 'Knowledge-intensive Reasoning' and 'Inference-time frame scaling results...' but lacks a proper introductory clause or context, appearing as a fragment rather than a descriptive caption. Please rewrite to clearly describe the figure's content.
- **[writing]** In the Introduction, the phrase 'single‑frame probing fails for all three frontier models (Claude‑4.5‑Sonnet, Qwen3‑VL‑235B‑A22B, GPT‑5.2)' lists model names that appear to be future-dated or hypothetical (e.g., GPT-5.2, Qwen3). While this may be a placeholder, the writing should either use current, verifiable model names or explicitly state these are hypothetical baselines to avoid confusing the reader.
