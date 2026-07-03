# Automated-review action items — MCompassRAG: Topic Metadata as a Semantic Compass for Paragraph-Level Retrieval

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The abstract and introduction claim an average Information Efficiency (IE) improvement of 8.24% over the 'strongest non-LLM baseline'. However, Table 1 shows MCompassRAG (IE 38.97) underperforming the 'LLM + 10 Topics' oracle (IE 40.83) on Dragonball. The claim requires clarification: does 'strongest non-LLM baseline' refer to SAKI-RAG (IE 32.90) or a different aggregate? The specific baseline for the 8.24% figure must be explicitly named to avoid misrepresentation.
- **[science]** Section 3.3 states training uses 'Qwen3-Embedding-4B' and 'Qwen3-32B'. These model versions (Qwen3) are not yet publicly released as of the current date (2024/2025 context). Unless these are internal unreleased models, the citation or model name is likely hallucinated or premature. If these refer to Qwen2.5 or similar, the text must be corrected to match available public artifacts to ensure reproducibility.
- **[writing]** Table 1 lists 'LLM + 10 Topics' as a baseline with IE 40.83 on Dragonball, yet the text describes MCompassRAG as 'closely approaching' this oracle. However, the table also lists 'LLM' (without topics) at 34.73. The distinction between the 'LLM' baseline and the 'LLM + 10 Topics' oracle is critical; the paper must clarify if the 'LLM' baseline includes topic metadata or if the 'LLM + 10 Topics' row represents a theoretical upper bound not achieved by any standard LLM baseline.

## paper_reviewer_figure_critic — verdict: minor_revision

- **[writing]** Figure 1: The caption is explicitly marked as '(no caption)', leaving the diagram's components and flow unexplained.
- **[writing]** Figure 1: The diagram contains a placeholder text 'Overview of .' where the model name or system description should be.
- **[writing]** Figure 2: The caption contains multiple grammatical gaps where the model name 'MCompassRAG' is missing (e.g., 'Overview of .', 'At inference time, selects...'). Additionally, the caption states that icons indicate trainability (fire for trained, snowflake for frozen), but the rendered figure lacks a legend or key to define these symbols.
- **[writing]** Figure 3: The x-axis label 'Topics' is ambiguous; the caption specifies 'number of topics', but the axis ticks (2, 4, ..., 20) are not explicitly labeled as counts, which could be confused with topic IDs.
- **[writing]** Figure 3: The y-axis label 'IE' is undefined in the figure and caption; the metric (e.g., Inverse Entropy, Information Efficiency) should be spelled out for clarity.
- **[writing]** Figure 5 caption: The sentence ends abruptly with 'query--gold alig', indicating a truncation error.
- **[writing]** Figure 5 caption: 'shareholde structure' contains a typo (missing 'r').

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific jargon and undefined acronyms that hinder accessibility for non-specialist readers. The most critical issue is the introduction of "Information Efficiency (IE)" in the Abstract and Introduction without a definition. Readers cannot evaluate the claim of an "8.24% improvement" without knowing if this metric measures precision, recall, token cost, or a composite score. This term must be explicitly defined in plain English upon first use. Additionally

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a coherent argument for using topic metadata to guide retrieval, but several logical gaps exist between the stated claims and the presented evidence. First, the central claim of an "8.24% average improvement in Information Efficiency (IE)" over the "strongest non-LLM baseline" (Abstract, Introduction) requires precise definition. In Table 1, MCompassRAG (IE 38.97) is compared against SAKI-RAG (IE 32.90) and the "LLM + 10 Topics" oracle (IE 40.83). If the 8.24% figure is an ave

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The paper makes several quantitative claims that slightly overreach the presented evidence, primarily regarding the magnitude of improvement over "strongest" baselines and the proximity to the oracle. First, the abstract and introduction claim an average Information Efficiency (IE) improvement of 8.24% over the "strongest efficient RAG baselines." However, Table 1 (e000) and the detailed tables in the appendix (e001) reveal that the "LLM + 10 Topics" configuration consistently outperforms MCompa

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The training pipeline relies on GPT-4o (openai2024gpt4o) to generate synthetic queries and relevance labels (Section 3.3, Appendix A). The manuscript must explicitly state the data privacy policy regarding any proprietary or sensitive data potentially present in the target corpora (e.g., LegalBench-RAG, DRBench) when sent to the external LLM API, and confirm that no Personally Identifiable Information (PII) was included in the prompts.
- **[writing]** The 'Limitations' section (Section 6) acknowledges sensitivity to topic count and domain shifts but omits discussion of potential bias amplification. The authors should add a brief statement addressing whether the topic modeling or distillation process could inadvertently reinforce biases present in the training data (e.g., in LegalBench-RAG or HotpotQA) and how this was mitigated.
- **[writing]** The paper claims 'over 5x lower latency' than LLM-based baselines (Abstract, Section 1). While this is an efficiency claim, it has safety implications for deployment in high-stakes domains (e.g., legal/medical RAG) where speed might encourage over-reliance on potentially hallucinated outputs. The authors should briefly discuss the trade-off between the efficiency gains and the risk of reduced interpretability compared to full LLM reasoning.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The claim of '8.24% average IE improvement' (Abstract, Intro) lacks a defined baseline. Table 1 shows MCompassRAG trailing the 'LLM + 10 Topics' oracle on all metrics. Clarify if the 8.24% is against the strongest non-LLM baseline (SAKI-RAG) or a different aggregate, and report the specific baseline used for this calculation to avoid ambiguity.
- **[science]** The latency claim of '5x lower latency' (Abstract) is not supported by the provided data. Table 2 shows MCompassRAG at 174ms vs. SAKI-RAG at 925ms (~5.3x), but PageIndex is 4408ms (~25x). The text implies a comparison to 'strongest efficient RAG baselines' but does not explicitly state which baseline yields the 5x figure, risking cherry-picking.
- **[science]** The training data synthesis relies on GPT-4o (Section 3.3) without reporting the inter-annotator agreement or consistency of the teacher labels. Given the reliance on distillation, the potential for teacher bias or hallucination in the relevance labels is a significant threat to validity that requires a brief discussion or error analysis.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report statistical significance (e.g., paired t-tests or bootstrap CIs) for the claimed 8.24% average IE improvement and latency reductions across the six benchmarks. Point estimates alone are insufficient to support the claim of consistent outperformance.
- **[science]** Clarify the experimental design for the 'LLM + 10 Topics' oracle baseline. Is this a single run or an average? If single, the comparison against the student model (which likely has variance) is statistically invalid without error bars or significance testing.
- **[science]** The ablation study (Table 3) shows small absolute differences (e.g., IE 38.97 vs 38.03). Without reported standard deviations or p-values, it is unclear if the 'Abstraction' and 'Selection' components provide statistically significant gains over the noise floor.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The title and abstract use the placeholder '\name{}' instead of the actual model name 'MCompassRAG'. This must be replaced with the full name or a defined macro before submission to ensure the paper is self-contained and readable.
- **[writing]** In Section 2 (Related Work), the second paragraph heading 'Semantic Guidance and Efficient Retrieval. ' contains a trailing space before the closing brace. While minor, this is a typographical error that should be cleaned up for professional presentation.
- **[writing]** The phrase 'Topic Metadata as a Semantic Compass' is used as a metaphor, but the text occasionally shifts between 'topic-level signals' and 'topic metadata' without clear distinction. Ensure consistent terminology throughout the introduction and method sections to avoid reader confusion.
