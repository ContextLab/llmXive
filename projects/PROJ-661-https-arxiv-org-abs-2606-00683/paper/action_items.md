# Automated-review action items — OCC-RAG: Optimal Cognitive Core for Faithful Question Answering

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** In Section 5.1, the text claims OCC-RAG-0.6B exceeds Qwen3-1.7B by 9.5 points on ConFiQA. Table 1 shows a difference of 15.1 points (79.9 vs 64.8). Verify the correct baseline or delta.
- **[writing]** In Section 5.1, the text cites Qwen3-0.6B memorization as 8.2, but Table 1 lists 9.0 as the standard value (8.2 is for thinking mode). Clarify which baseline is used for the comparison.
- **[writing]** In Section 5.1, the claim that OCC-RAG-1.7B (87.2 R-Acc) is 'on par with models of 8B parameters or higher' is inaccurate as Qwen3-8B scores 90.7. Refine the claim to reflect the actual performance gap.

## paper_reviewer_figure_critic — verdict: accept

### Figure 1

Figure 1 is a clear and well-structured flowchart that accurately visualizes the OCC-RAG reasoning process described in the caption. All components, including the input, the three internal reasoning steps, and the final output status, are legible and logically connected.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on field-specific jargon that creates barriers for non-specialist readers, despite the authors' stated goal of demonstrating practical utility for compact models. First, the term "mid-training" is used extensively (Abstract, Section 4, Section 5) without a clear, plain-language definition. While it implies a stage between pre-training and fine-tuning, the specific mechanics or distinction from standard fine-tuning are not explained in accessible terms. This should b

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The logical consistency of the paper is generally sound in its high-level narrative: the authors posit that specialized mid-training on synthetic data can improve faithfulness and reasoning in small models, and the results generally support this. However, there are specific instances where the textual claims do not align with the provided data tables, creating logical gaps in the argumentation. First, in the Introduction, the authors state: "OCC-RAG-0.6B exceeds Qwen3-1.7B ($2.8\times$ larger) b

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The claim that OCC-RAG models 'match or exceed general-purpose models 2–6× their size' (Abstract, Intro) is an over-extrapolation. While OCC-RAG-1.7B outperforms Qwen3-4B on faithfulness, it trails Qwen3-4B on multi-hop reasoning (60.9 vs 60.6 In-Acc is a marginal lead, but Qwen3-8B and larger models significantly outperform OCC-RAG on reasoning). The '2-6x' claim implies a blanket superiority across all metrics and scales that the data in Table 1 does not support.
- **[writing]** The statement that OCC-RAG 'achieves the highest results on faithfulness and refusal' (Results) is slightly overreaching regarding refusal. While OCC-RAG-1.7B (87.2) is competitive, Qwen3-8B achieves 90.7 R-Acc (Table 1). The paper should qualify this claim to specify that OCC-RAG matches or exceeds larger models *up to a certain scale* (e.g., 4B) or on specific subsets, rather than implying it beats all larger models on refusal.
- **[writing]** The attribution of Pleias-RAG's lower performance to a lack of multi-hop training data ('as can be inferred from their technical report') is speculative. The paper does not provide evidence that Pleias-RAG's generation process specifically lacks multi-hop data, nor does it control for other architectural or training differences. This causal claim should be softened to a hypothesis or supported by a direct citation/analysis of the Pleias-RAG paper.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes a data generation pipeline using 'gpt-oss-120B' and 'Qwen3.5-27B' to create a 3.25M example synthetic corpus. While source data is Wikipedia, the paper does not explicitly state if the generation process included filters for PII, sensitive data, or copyrighted text. A statement on PII scrubbing and copyright compliance in the 'Training Data' section is required.
- **[writing]** The 'Unanswerable Question Construction' method relies on a DeBERTa model fine-tuned on SQuAD. The paper does not disclose the specific SQuAD version used or confirm adherence to its consent/privacy protocols. Clarification on the ethical handling of SQuAD-derived refusal cases is needed to ensure data provenance.
- **[writing]** The paper claims the model learns 'safe abstention' but only evaluates refusal via a specific phrase on MuSiQue-Un. There is no discussion of risks like false refusal on benign queries or failure to refuse harmful instructions in context. A brief discussion on the safety boundaries of the refusal capability is necessary.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims OCC-RAG-0.6B exceeds Qwen3-1.7B by 9.5 points on ConFiQA (Intro), but Table 1 shows 79.9 vs 64.8 (15.1 points). This discrepancy in the central claim's magnitude must be corrected to ensure statistical accuracy.
- **[science]** The evaluation of Qwen3 and SmolLM3 baselines uses 'thinking mode' (Section 5.1), while OCC-RAG uses a fixed structured trace format. This introduces a confounding variable where the baselines may benefit from additional compute/latency not available to the proposed model, potentially inflating the relative performance gap. Clarify if a non-thinking baseline comparison exists or justify the asymmetry.
- **[science]** The synthetic data generation pipeline relies on 'gpt-oss-120B' and 'Qwen3.5-27B' as teachers (Section 4). The paper lacks a quantitative analysis of teacher-student alignment or error propagation. Without reporting the failure rate of the LLM-as-a-judge or the distribution of errors in the 3.25M synthetic examples, the robustness of the training signal is unverifiable.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The evaluation section reports single-point accuracy metrics (In-Acc, F1, R-Acc) without confidence intervals or standard deviations. Given the stochastic nature of LLM inference and the finite size of test sets (e.g., 2,417 samples for MuSiQue), statistical significance testing (e.g., bootstrap CIs or paired t-tests) is required to substantiate claims of superiority over baselines.
- **[science]** The Memorization Ratio (M_R) is defined as P_o / (P_o + P_c) but lacks an associated uncertainty estimate. With ConFiQA subsets varying in difficulty, the variance in M_R across the QA, MR, and MC subsets should be reported to assess the stability of the faithfulness claim.
- **[science]** The paper claims OCC-RAG-0.6B 'exceeds' baselines on every benchmark. Without reported p-values or confidence intervals for the differences in accuracy (e.g., the 9.5 point gap on ConFiQA), it is statistically premature to assert these improvements are not due to random variance in the evaluation samples.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3 (Training Data), the sentence 'To ensure that questions remain strictly grounded in the provided evidence, we condition its generation on a knowledge graph...' contains a pronoun agreement error. 'Questions' is plural, but 'its' is singular. Change 'its' to 'their'.
- **[writing]** In Section 5 (Evaluation), the phrase 'OCC-RAG-0.6B, at just 0.6B parameters, exceeds Gemma-3-4B and SmolLM-3-3B on each dimension' is slightly ambiguous. It is unclear if 'each dimension' refers to the three specific metrics (reasoning, faithfulness, refusal) or the specific benchmarks listed earlier. Consider clarifying to 'on all three evaluation dimensions'.
- **[writing]** In the Introduction, the sentence 'We evaluate OCC-RAG on context QA benchmarks spanning multi-hop reasoning... and abstention on unanswerable questions (MuSiQue-Un~\cite{musique})' uses a raw citation command `\cite` instead of the consistent `\citep` used throughout the rest of the paper. Standardize to `\citep`.
