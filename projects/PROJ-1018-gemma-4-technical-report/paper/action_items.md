# Automated-review action items — Gemma 4 Technical Report

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** The paper presents a generally coherent technical report for the Gemma 4 family, but several specific claims regarding performance metrics and architectural ratios require clarification to ensure they are fully supported by the provided tables and text. First, there is a minor inconsistency in the description of the attention mechanism ratios. The Introduction states a "5:1 ratio of local sliding window to global self-attention" for the model suite, while Section 2.1 clarifies that this 5:1 rati

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The caption states the drafter is fed 'activations and KV cache', but the diagram only explicitly labels 'Last Prefilled Global Layer' and 'Last Prefilled Local Layer' as inputs; the specific 'KV cache' input is not visually labeled.
- **[writing]** Figure 1: The input labels at the bottom ('t1 / p1', 't2 / p1', 't3 / p1') are undefined in the caption, making it unclear what 'p1' represents in the context of the autoregressive process.
- **[science]** Figure 2: The caption claims the image is resized to '2 x 4 pooled patches', but the visual grid clearly displays 3 rows and 3 columns (9 patches). This contradicts the text description of the pooling layout.
- **[science]** Figure 2: The caption states the image is resized to '2 x 4 pooled patches (each of size 48px^2)', but the visual grid shows 9 patches, and the math for a 96x192 image with pooling kernel 3 and patch size 16 does not yield 48px^2 pooled patches in a 2x4 arrangement.
- **[writing]** Figure 2: The caption contains a typo 'pooled $33$' which appears to be a formatting error or missing text, making the sentence 'the vision encoder representations are pooled $33$' illegible.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 1 (Introduction) uses 'p-RoPE' and 'KV cache' without definition. While 'KV cache' is common in LLM literature, 'p-RoPE' is a specific variant introduced in a cited paper; define it at first use (e.g., 'p-RoPE (a variant of Rotary Positional Embeddings)') to ensure adjacent-field readers understand the specific modification.
- **[writing]** Section 1 (Introduction) and Section 2 use 'MTP' (Multi-Token Prediction) and 'QAT' (Quantization-Aware Training) as acronyms before they are explicitly defined in the text. Expand these at their first occurrence in the Introduction or early in Section 2 (e.g., 'autoregressive multi-token prediction (MTP) drafter head').
- **[writing]** Table 1 caption and Section 2 use 'E2B' and 'E4B' as model identifiers without defining the 'E' prefix or the numbers in the main text. While the table caption mentions 'effective', the specific naming convention (Effective 2B/4B) should be explicitly defined in the prose when first introduced to avoid confusion with total parameter counts.
- **[writing]** Section 2.1 (Vision modality) introduces '2D-RoPE' and '2D absolute positional embeddings' without a brief gloss. While 'RoPE' is standard, the '2D' adaptation for vision is a specific architectural choice; a short clause explaining that this extends rotary embeddings to 2D spatial coordinates would aid adjacent-field readers.
- **[writing]** Section 2.3 (Encoder-free architecture) mentions '48x48x3 RGB patches' and '640-dimensional vectors' without defining the source of the 640 dimension (e.g., '640-dimensional vectors (derived from 16kHz audio sampled at 40ms chunks)'). The dimensionality is critical for understanding the projection but is currently implicit.
- **[writing]** Section 2.4 (Pre-training) and Section 3 (Instruction Tuning) use 'PT' and 'IT' as acronyms for 'Pre-training' and 'Instruction Tuning' without defining them. These are common in the field but should be expanded at first use (e.g., 'Pre-training (PT) versus Instruction Tuning (IT) formatting') for clarity.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The paper presents a generally coherent argument for the Gemma 4 model family, with a clear progression from architecture to evaluation. However, there are minor inconsistencies in terminology and numerical reporting that require clarification to ensure the logical flow is unambiguous. First, the description of the "encoder-free" architecture in the Abstract and Introduction (Section 1) states the model "ingests raw audio and image patches." In contrast, Section 2.3 ("Encoder-free architecture")

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims a 'leap in performance across STEM' benchmarks, but Table 1 shows the 12B model scores only 5.2 on HLE (a hard STEM benchmark) vs 19.5 for the 31B. The 'leap' is not uniform across sizes. Narrow the claim to 'improvements in larger models' or 'across most benchmarks'.
- **[writing]** Abstract states the model 'rivals larger, frontier open models.' Table 2 shows Gemma 4 31B (Elo 1451) ranks 43rd, trailing top open models like GLM 5.1 (1475). The claim implies parity with leaders, which data doesn't support. Qualify to 'rivals specific larger models' or cite the specific Elo range.
- **[writing]** Introduction frames 'encoder-free architecture' as a suite feature, but Table 1 shows it applies only to the 12B model; others use frozen encoders. Restrict the claim in the Abstract and Intro to the 12B model to avoid implying a family-wide shift.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a technical report for the Gemma 4 model family, an open-weight, multimodal LLM. From a safety and ethics perspective, the manuscript adequately addresses the primary risks associated with releasing such a system.

Section 7 ("Responsibility, Safety, Security") provides a comprehensive overview of the safety governance, train-time mitigations (data filtering for PII, toxic content, and unsafe utterances), and evaluation protocols. The authors explicitly state that models were evaluated without safety filters to measure inherent capabilities and report that policy violations were minimal. The "Ethical Considerations and Risk Mitigation" subsection (7.4) correctly identifies key areas of concern: bias/fairness, misinformation, and privacy, offering standard guidance for downstream developers (e.g., continuous monitoring, adherence to local regulations).

The paper does not exhibit specific, unmitigated dual-use risks that are unique to this work compared to the broader class of frontier LLMs. The "thinking mode" and "encoder-free architecture" are described as efficiency and reasoning improvements, not as mechanisms designed to bypass safety filters or deceive users covertly. The release of quantized models and drafters is standard for the field and is accompanied by the same safety policies as the base models.

No human-subjects data requiring IRB approval is described; the human evaluations mentioned (Arena) are standard third-party benchmarks where the paper reports aggregate Elo scores rather than raw personal data. The training data is described as a filtered collection of web documents and public sources, with no indication of license violations or the release of PII.

As this is a third-party preprint, the absence of a specific "broader impacts" essay is not a defect, and the existing safety section meets the disclosure standards for a technical report of this nature. There are no fatal gaps, missing disclosures, or specific actionable risks identified that would prevent the paper from being accepted in this lens.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** The paper presents a comprehensive technical report for the Gemma 4 family, but the experimental design in several key tables fails to rule out alternative explanations for the reported performance gains, specifically regarding variance, confounding variables, and baseline fairness. First, the primary evidence for the "leap in performance" (Abstract, Section 5) relies on single-point numbers in Tables 2 and 3 (e.g., MMLU Pro 85.2, AIME 89.2). There is no reporting of standard deviation, confiden

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Table 2 reports single-point benchmark scores (e.g., '85.2' on MMLU Pro) without any measure of uncertainty (SD, SE, or CI) or the number of seeds/runs used. In ML, single-run reporting is insufficient to distinguish signal from noise. Report mean ± SD over ≥3 seeds or explicitly state the result is from a single run and drop the implied precision.
- **[writing]** Table 1 (Arena Elo) reports 95% CIs (e.g., '± 8') for Gemma 4 models but provides no methodology for their calculation (e.g., bootstrap, Bayesian inference) or the number of pairwise comparisons used to derive them. Without this, the intervals cannot be verified or interpreted correctly.
- **[writing]** Section 5.2 claims Gemma 4 is 'significantly better' than Gemma 3 across benchmarks based on Table 2 point estimates. No statistical test (e.g., paired t-test, bootstrap) or p-values are reported to support this claim. Replace 'significantly better' with 'higher' or report the actual test statistics and p-values.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper generally presents a clear narrative of the Gemma 4 model family, with a logical flow from architecture to training and evaluation. However, several sections suffer from structural issues that force the reader to re-parse sentences to identify the main point. In Section 2.1, the description of long-context efficiency is buried in a long, complex sentence that lists multiple architectural choices (sliding window ratios, p-RoPE, KV sharing) before stating the result (37.5% reduction). Th
