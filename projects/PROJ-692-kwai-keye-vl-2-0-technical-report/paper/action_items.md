# Automated-review action items — Kwai Keye-VL-2.0 Technical Report

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** The claim that Keye-VL-2.0 'pioneers the application of Multimodal DeepSeek Sparse Attention (DSA) in the visual domain' (Introduction) is unsupported. The cited source (deepseek2025v32) describes DSA for text-only LLMs. The paper provides no evidence that the cited work or any prior art applied DSA to visual tokens, making the 'pioneer' claim potentially overstated without a specific citation for the visual adaptation.
- **[writing]** The abstract and Introduction claim 'lossless 256K context processing' and 'losslessly' handling video contexts. However, Section 1.2 explicitly describes an 'Adaptive Video Pixel Budget' with scaling factors (0.125, 0.25, 0.5, 1.0) for videos exceeding 256s. This implies information reduction (subsampling) for long videos, contradicting the 'lossless' claim. The term should be qualified (e.g., 'lossless up to X duration' or 'context-efficient').
- **[writing]** Table 1 (Video Understanding) lists 'Video-MME-v2 Non-Lin' scores where Keye-VL-2.0 (18.5/24.2) is significantly lower than Qwen3-VL 235B (26.3/28.1), yet the text below the table states Keye-VL-2.0 'achieves best results on... Video-MME-v2 accuracy'. While the 'ACC' row supports this, the inclusion of the 'Non-Lin' row in the same table without clarification creates ambiguity about the 'best results' claim across the full benchmark suite.
- **[writing]** The citation 'openai2026gpt55' (Introduction) refers to a 2026 report for 'GPT-5.5'. Given the current date context of the paper (2026), this is a future-dated citation. While acceptable for a preprint in that timeline, the claim that this model 'demonstrates substantial progress' relies on a source that may not be publicly verifiable or stable at the time of review, requiring the authors to ensure the URL and data are accessible.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 4: The 'Decode Cost' y-axis scale is inconsistent with the 'Prefill Cost' scale (0.0–3.2 vs 0.0–0.06), yet the visual height of the 'Full Attention' line is nearly identical in both plots. This creates a misleading visual impression that the absolute cost reduction is similar in both phases, whereas the caption and axis labels imply a much larger absolute saving in decode. The scales should be comparable or explicitly noted as different to avoid misinterpretation.
- **[writing]** Figure 4: The legend at the top right ('DSA' and 'Full Attention') is not directly connected to the lines in the plots; while colors match, adding a small line sample next to each label in the legend would improve clarity.
- **[science]** Figure 5: The caption states 'Higher is better unless otherwise specified,' but the benchmark 'Video-MME-v2 ACC (64 Frames/512 Frames)' lists 'ACC' (Accuracy), which is a percentage metric. The values (e.g., 35.3 / 42.4) are likely percentages, yet the caption's phrasing suggests a general rule that might confuse readers if some benchmarks are actually loss-based or require lower scores. The caption should explicitly list any benchmarks where 'Lower is better' to avoid ambiguity, or confirm all
- **[writing]** Figure 5: The benchmark name 'Video-MME-v2 ACC (64 Frames/512 Frames)' is split across two lines in a way that breaks the logical grouping of the metric name and its configuration. It should be formatted to keep 'Video-MME-v2 ACC' together or clearly indicate the frame configurations as sub-rows or a single continuous label.
- **[writing]** Figure 5: The benchmark 'VideoMMMU' is listed without a clear definition of what 'MMMU' stands for in the context of video (e.g., is it a video adaptation of the MMMU benchmark?). While the caption mentions 'detailed benchmark descriptions... provided in the subsections below,' the figure itself should ideally include a footnote or abbreviation key for clarity.

## paper_reviewer_jargon_police — verdict: full_revision

- **[science]** The manuscript suffers from significant jargon overuse, frequently introducing complex acronyms and proprietary terms without definition, which alienates non-specialist readers. The Abstract immediately fails to define 'DSA' (DeepSeek Sparse Attention) and 'MOPD' (Cross-Modal Multi-Teacher On-Policy Distillation), presenting them as standard terms rather than specific architectural choices. This pattern continues throughout the text: 'GSPO' (Section 4.2.2), 'SPRR' (Section 4.2.3), and 'ExtraIO'

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The manuscript presents a technically dense report on Kwai Keye-VL-2.0, but several logical inconsistencies and unsupported causal claims undermine the rigor of the conclusions. First, the claim of "lossless 256K context processing" (Abstract) contradicts the described mechanism of DeepSeek Sparse Attention (DSA). Section 1.3 details a "Lightning Indexer" that selects a Top-k subset of tokens ($k=2048$) for aggregation. By definition, attending to a sparse subset of the context implies informati

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** The manuscript exhibits significant over-claiming regarding the novelty and capabilities of the proposed architecture, particularly in the Abstract and Introduction. First, the term "lossless 256K context processing" (Abstract; Section 1) is technically inaccurate and misleading. The core mechanism described, DeepSeek Sparse Attention (DSA), relies on a "MQA-Style Lightning Indexer" to select a Top-k subset of tokens (Equation 1, Section 1.3). By definition, selecting a subset of tokens constitu

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper describes training on massive web-scraped datasets (LAION, DataComp) and synthetic data generation but lacks a dedicated section on data privacy, consent, and copyright compliance. Explicitly address how personally identifiable information (PII) was handled and whether opt-out mechanisms were respected to mitigate legal and ethical risks.
- **[writing]** The 'Agentic RL' section details capabilities for autonomous tool use, booking services, and payment execution (Case VI). The manuscript must include a safety analysis regarding potential misuse for unauthorized transactions, fraud, or supply chain attacks, and describe any guardrails or human-in-the-loop constraints implemented.
- **[writing]** The 'Anatomical Reasoning' case study (Case III) involves medical diagrams and the correction of scientific errors. The authors should clarify that the model is not a diagnostic tool and include a disclaimer to prevent users from relying on its outputs for medical decision-making, mitigating risks of harm from hallucinations in critical domains.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Table 1 (Video-MME-v2) reports a 13.9 point gap between Keye-VL-2.0 (42.4) and Qwen3.5 (28.5) on 512-frame inputs, yet the text claims 'state-of-the-art' without reporting standard deviation or confidence intervals. Provide statistical significance testing (e.g., t-tests) or error bars to confirm this gain is not due to random variance.
- **[science]** The claim of 'lossless 256K context' (Abstract, Section 1) lacks empirical validation. The paper reports performance on 512-frame benchmarks but does not provide a controlled ablation study comparing 256K context performance against a dense-attention baseline or a subsampled baseline to prove the 'lossless' nature of the sparse aggregation.
- **[science]** The Video-RL section (Section 3.2.4) cites a '1% improvement' from 31K video samples but does not specify the baseline metric or the specific benchmark subset. Without the baseline score and the specific evaluation protocol, this effect size is unverifiable and risks p-hacking interpretation.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Table 1 (Video Eval) and Table 2 (Code Eval) report single-point accuracy scores without confidence intervals or standard deviations. Given the stochastic nature of LLM inference and benchmark sampling, report 95% CIs or results over multiple seeds to establish statistical significance of the claimed margins (e.g., 74.1 vs 70.5 on LongVideoBench).
- **[science]** The claim of '1% improvement' from Video RL (Section 4.2.4) lacks statistical context. Specify the baseline score, the sample size (N=31K), and the variance of the metric to determine if this gain is statistically significant or within the noise floor of the evaluation protocol.
- **[writing]** The 'Non-Lin' metric in Table 1 (Video-MME-v2) shows a performance drop for Keye-VL-2.0 compared to InternVL3.5. The text does not discuss the statistical significance of this degradation or potential confounding factors (e.g., specific video length distributions) that might explain the variance.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In the Introduction, the phrase 'temporal continuousness' is non-standard and likely a misuse of 'continuity' or 'temporal coherence'. Replace with 'temporal continuity' to improve clarity and professional tone.
- **[writing]** The term 'agentic intelligence' appears in the Abstract and Introduction but is never explicitly defined. Given the paper's focus on agent tasks, a brief definition or clarification of the specific capabilities implied by this term is necessary for reader understanding.
- **[writing]** In Section 1.3, the phrase 'MQA-Style Lightning Indexer' uses 'Lightning' as a proper noun without prior introduction or citation. If this is a specific component name, it should be introduced formally; otherwise, consider a more descriptive term like 'Fast' or 'Efficient'.
- **[writing]** The Case Study section (Section 5) contains inconsistent formatting for case labels (e.g., 'Case VI' appears before 'Case II' in the provided text chunks). Ensure the case studies are ordered logically (I through VI) and that all \label and ef commands correspond to the correct sequence.
