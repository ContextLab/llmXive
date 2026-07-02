# Automated-review action items — Training Long-Context Vision-Language Models Effectively with Generalization Beyond 128K Context

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: full_revision

- **[fatal]** The abstract and introduction cite 'Qwen2.5-VL-7B' with a token budget of '5B (2605.13831, https://arxiv.org/abs/2605.13831)'. The arXiv ID 2605.13831 is invalid (future-dated) and the URL is unreachable. The citation does not support the claim of the model's origin or the budget source. This must be corrected with a valid reference or removed.
- **[fatal]** Section 1 claims 'LVLMs' context windows have been rapidly scaled to 128K tokens and beyond' citing 'Gemini 3.1' and 'GPT-5.4'. These model versions do not exist in public records or the provided bibliography. The claim is factually unsupported and relies on hallucinated model names.
- **[fatal]** Section 2 claims 'Concurrent work finds that 1B-token LongPT outperforms its 10B-token counterpart' and 'LongSFT outperforms LongPT' citing 'veselka2026longvl'. The provided bibliography does not contain this entry, and the arXiv ID '2605.13831' (reused in the paper) is invalid. The specific comparative claims cannot be verified against the provided sources.
- **[writing]** Section 6 states 'MMProLong improves long-document VQA scores by 7.1%... exceeding baselines by over 20%'. The 7.1% figure (57.70 vs 50.59) is correct, but the 'over 20%' claim is ambiguous. If referring to the gap against Qwen2.5-VL-7B (50.59), the improvement is ~14%. If referring to other baselines, specific comparisons must be cited. The current phrasing is misleading without a specific baseline definition.
- **[writing]** Section 4 claims the document pool contains 'over 1.5 million PDF-formatted documents'. Appendix Table 'tab:doc_pool_statistics' lists '1,537,504' documents. While the number matches, the claim 'over 1.5 million' is supported, but the source of this pool (e.g., specific dataset name or collection method) is not cited, making the provenance of the data unverifiable.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 2: The caption describes 'Long-document VQA data in the pool-native Distribution', but the plot shows three identical histograms labeled 'Extract-single', 'Extract-multi', and 'Reasoning'. It is unclear if these are distinct data subsets or if the same data was plotted three times, and the caption fails to explain the relationship between the panel titles and the 'pool-native' description.
- **[writing]** Figure 2: The y-axis label 'Count (K)' is ambiguous; it is unclear if the values represent raw counts divided by 1000 or if the unit is strictly thousands, and the tick marks (0, 2, 4) lack gridlines for precise reading.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript relies heavily on domain-specific acronyms and custom shorthand that hinder accessibility for a broader audience. In the Abstract and Introduction, the term "LVLM" is used repeatedly without being spelled out as "large vision-language model" at the very first instance. Similarly, "LongPT" is introduced as a concept but the acronym is not explicitly defined until later or assumed, which breaks the flow for non-specialist readers. In Section 3, technical terms like "mRoPE," "FSDP,"

## paper_reviewer_logical_consistency — verdict: full_revision

- **[science]** "The logical consistency of the paper is compromised by several gaps between premises and conclusions, particularly regarding the extrapolation claims and citation errors.\n\nFirst, the central claim of generalizing to 256K and 512K contexts \"without additional training or adaptation\" (Abstract, Introduction) lacks a supporting mechanism. Section 3 and Appendix A explicitly state that the mRoPE base frequency was scaled to $4\\times10^6$ to accommodate the 128K context window. In standard Rota

## paper_reviewer_overreach — verdict: full_revision

- **[science]** Claims of generalization to video/web tasks (Abstract) are unsupported; training is PDF-only. Improvements on MM-NIAH/Video-MME do not prove true modality transfer beyond static document retrieval skills.
- **[science]** The claim of 512K generalization (Abstract) is overreaching. Evaluation uses random negative document padding (App A.4.2), testing distractor robustness, not genuine 512K multimodal sequence processing.
- **[writing]** The conclusion that short-context data is unnecessary (Sec 5.3) overstates a minor performance drop. The claim of recipe transfer to stronger backbones relies on a single, already long-context trained model (Qwen3-VL).

## paper_reviewer_safety_ethics — verdict: full_revision

- **[science]** The paper presents a systematic study on long-context Vision-Language Models (LVLMs), but significant safety and ethical concerns regarding data provenance, privacy, and potential for harm remain unaddressed. Data Provenance and Copyright (Sec 4.1): The authors construct a "large-scale document pool" of over 1.5 million PDFs from unspecified sources, including "academic papers, books, and technical manuals." The manuscript lacks a critical data statement detailing the licensing status of these d

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The scientific evidence supporting the central claims of this paper is currently insufficient due to missing statistical controls and potential confounding variables in the experimental design. First, the most significant claim—that the model generalizes to 256K and 512K contexts without adaptation (Section 6, Table 2)—is supported only by point estimates. Long-context performance is notoriously unstable and sensitive to positional encoding interpolation and sampling noise. The absence of multip

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The paper reports performance gains (e.g., +7.1% in Abstract, Table 1) without any measure of statistical significance (e.g., standard deviation, confidence intervals, or p-values). Given the use of LLM-based judges which can be stochastic, single-run results are insufficient to claim superiority. Re-run experiments with multiple seeds or report variance.
- **[science]** In Section 5.2 (Table 2), the selection of the 8:2 extraction-to-reasoning ratio is based on a single point estimate. The difference between 8:2 (57.70) and 6:4 (57.27) is marginal (0.43 points). Without statistical testing or error bars, it is unclear if this difference is meaningful or due to noise. Justify the choice statistically or acknowledge the uncertainty.
- **[science]** The ablation on mRoPE base frequency (Appendix C.3, Table 12) shows conflicting trends across tasks (e.g., 8e6 improves MMLB-D but degrades reasoning). The paper lacks a statistical aggregation method (e.g., ANOVA or paired t-tests) to determine if the observed differences are significant across the three tasks. A more rigorous analysis of the trade-offs is required.
- **[science]** The claim that 'pure long-document VQA largely preserves short-context capabilities' (Section 5.3) relies on a drop from 66.47 to 65.48 (0.99 points). Without reporting the standard error of the mean across the six benchmarks or a significance test, this claim of 'preservation' is statistically weak. Provide variance metrics for the short-context benchmarks.

## paper_reviewer_writing_quality — verdict: full_revision

- **[writing]** Remove all unresolved claim markers (e.g., [UNRESOLVED-CLAIM: c_...]) and placeholder text (e.g., {{claim:...}}) from the manuscript. These artifacts appear in the Abstract, Introduction, Related Work, Setup, Curation, and Results sections, severely disrupting readability and indicating an incomplete draft.
- **[writing]** Correct the double period punctuation error in Section 4.1 (lines 10-11) where '...from multiple sources [UNRESOLVED-CLAIM: c_92a39337 — status=not_enough_info]..' appears. Also fix the similar error in Section 4.2 regarding page selection.
- **[writing]** Fix the broken footnote syntax in Section 4.1. The command '\footnote{.' is incomplete and missing the footnote text and closing brace. This must be completed or removed to ensure compilation and readability.
- **[writing]** Resolve the repetitive and grammatically broken sentence in Section 2 (Related Work): 'For example, they find that Concurrent work finds that 1B-token LongPT outperforms its 10B-token counterpart...'. The phrase 'Concurrent work finds that' is repeated and the sentence structure is incoherent.
- **[writing]** Fix the sentence fragment and capitalization error in Section 4.1: 'From these documents, We construct five training tasks...'. The pronoun 'We' should not be capitalized after a comma.
- **[writing]** Correct the awkward phrasing and double period in Section 5.2: 'As shown in \cref{tab:extract_reason_ratio}, Moderately extraction-heavy mixtures perform best...'. The sentence starts with a lowercase verb after a comma and ends with a double period.
