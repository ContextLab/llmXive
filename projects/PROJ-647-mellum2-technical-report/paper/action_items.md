# Automated-review action items — Mellum2 Technical Report

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** Verify the MMLU-Pro baseline score of 48.6% for Qwen2.5-7B cited in Table 1. Public benchmarks often report higher scores for this model. Ensure the cited source (qwen2.5) supports this specific value to validate the claim of surpassing it.
- **[writing]** Clarify the unit for the RULER score '0.64' in Section 3. The cited paper (hsieh2024ruler) typically reports percentages. Specify if this is 64% or a normalized metric to avoid misinterpretation of the result's magnitude.
- **[science]** Confirm the existence and benchmark score of 'Ministral-3-14B' in Table 3. The cited source (liu2026ministral3) may not list a 14B variant. Verify if this model and its 42.4% LiveCodeBench score are accurately represented in the reference.
- **[writing]** Reconcile the 167B token count for the 'Thinking' SFT variant with the prompt counts in Table 2. The prompt counts are nearly identical to the 'Instruct' variant. Explain if the token difference stems from longer sequences or unlisted data volume.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The caption 'Throughput mode' contradicts the y-axis label 'Latency (s)'; the figure displays latency, not throughput.
- **[writing]** Figure 1: The legend defines 'Mellum 4B' and 'Qwen2.5-7B' but the plot contains dozens of unlabeled data points (e.g., 'T:11.6B', 'A:2.5B') that are not defined in the caption or legend.
- **[writing]** Figure 1: The x-axis label 'Depth (Layers)' is ambiguous as the tick marks (24, 26, 28...) do not clearly correspond to the specific model configurations labeled on the plot.
- **[science]** Figure 2: The caption describes 'Throughput mode (concurrent requests)', but the plot axes are 'Width (Hidden Dimension)' and 'Depth (Layers)', and the colorbar is 'Latency (s)'. The figure displays a latency contour map, not throughput or concurrent request data, contradicting the caption.
- **[science]** Figure 2: The legend identifies 'Mellum 4B' and 'Qwen2.5-7B', but the plot contains a dense grid of data points (grey circles) with specific values (e.g., '7.05B', '8.62B') that are not explained in the caption or legend. It is unclear if these points represent the models or a parameter sweep.
- **[science]** Figure 3: The caption claims to compare 'MoE models' (plural) with Sliding Window Attention, but the plot only explicitly labels one MoE model ('Mellum 2') and a group of '6 other candidate configs' without specifying if they are MoE or their window sizes. This makes the claim of comparing 'MoE models' (plural) unsupported by the visual data.
- **[writing]** Figure 3: The text '6 other candidate configs' is rendered in a very light gray font that is difficult to read against the white background, reducing legibility.
- **[science]** Figure 4: The caption 'Qwen2.5-7B (dense)' is too generic and fails to describe the specific comparison shown (Muon vs. AdamW vs. Muon Moonlight) or the metric (Validation loss), making the figure's purpose unclear without external context.
- **[writing]** Figure 4: The top annotation 'Muon (Megatron defaults) — diverged -> 2.47 at 21B' is rendered in a very small, light orange font that is difficult to read against the white background.
- **[writing]** Figure 4: The legend labels 'AdamW' and 'Muon (Moonlight)' are placed directly on the plot area without a distinct legend box or leader lines, which can be confusing if the lines were to cross or overlap.
- **[writing]** Figure 6: The caption contains raw LaTeX formatting artifacts ('uniform $$-bump' and 'unchanged-$$') instead of the readable method names ('Uniform RoPE base' and 'Unchanged RoPE base') shown in the plot labels.
- **[writing]** Figure 6: The caption references 'See for caveats on the absolute scores' but lacks the specific figure or section number to which the reader should refer.
- **[writing]** Figure 7: The caption references 'See for a comment on absolute RULER scores' but does not specify which section, figure, or table to consult.
- **[science]** Figure 7: The x-axis label 'Long-context training tokens (B)' is ambiguous; it is unclear if 'B' refers to billions of tokens or a specific batch size parameter.
- **[writing]** Figure 8: The annotation 'RULER plateau (≈30 B)' is present but lacks a definition in the caption or legend explaining what the 'RULER plateau' signifies in the context of load-balancing loss.
- **[science]** Figure 8: The y-axis label 'Load-balancing loss' is generic; the caption does not specify the exact loss function or metric used (e.g., auxiliary loss coefficient, specific MoE load-balancing formula), making it difficult to interpret the absolute values.
- **[writing]** Figure 10: The caption contains a sentence fragment ('matches the sync latency...') that lacks a subject, failing to explicitly state that 'Mellum 2' is the model being described.
- **[science]** Figure 10: The 'Sync (single request)' chart displays raw values (193 vs 192) but does not visually represent the 'matches' claim in the caption, as the bars are distinct in length without error bars to indicate statistical equivalence.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on domain-specific acronyms and proprietary or niche terminology that are not defined upon first use, creating a barrier for non-specialist readers. In the Abstract and Section 2 (Model Architecture), terms like Muon, YaRN, MTP, GQA, and SWA are introduced as acronyms or proper nouns without their full expansions or explanations. For instance, "Muon optimizer" and "YaRN" are critical to the methodology but remain undefined. Similarly, Section 3 (Long Context Extensi

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** The claim that the model 'matches Qwen2.5-7B throughput' (Abstract, Intro) is contradicted by the specific metric in Section 6, which states Mellum2 achieves '21% higher throughput' (20.2 req/s vs 16.7 req/s). The conclusion should reflect the actual performance gain rather than a match.
- **[writing]** In Section 4.3 (RL algorithm), the text states 'No KL term to SFT reference,' yet the loss formula includes a masking term M(rho) derived from the ratio of training to inference probabilities. The logical link between the absence of a KL penalty and the presence of this specific truncation mechanism needs explicit clarification to avoid confusion about the objective function.
- **[writing]** Section 5.2 claims the 'Thinking' variant uses a 'cold restart from SFT-Thinking' for RL, but the evaluation tables (Table 7) show a progression from SFT to RL. The logical flow of the training pipeline (Cold restart vs. continued fine-tuning) should be explicitly defined to ensure the reported gains are correctly attributed to the RL stage.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that Mellum2 'matches Qwen2.5-7B throughput on H100' (Sec 1) and 'matches sync latency' (Sec 6) is over-claimed without explicit hardware configuration details (e.g., batch size, sequence length, precision mode) in the text. The throughput figure (20.2 req/s) is highly sensitive to these parameters; without them, the comparison is not reproducible or verifiable.
- **[writing]** The statement that the model is 'competitive with 4B–14B open baselines at 2.5B dense compute' (Abstract) over-extrapolates the results. While it matches Qwen2.5-7B in throughput, the pre-training evaluation (Table 1) shows it underperforming Qwen2.5-7B on HumanEval (41.5% vs 55.5%) and MMLU (70.9% vs 71.8%). The 'competitive' claim requires qualification regarding the specific trade-off between speed and accuracy.
- **[science]** The assertion that 'Muon + FP8 recipe' enabled 'Stable training at 10T tokens' (Sec 1) is a causal claim not fully supported by the provided ablation data. The paper mentions Muon and FP8 but does not present a controlled ablation isolating these factors from the MoE architecture or data curriculum to prove they were the sole or primary drivers of stability at that scale.
- **[writing]** The claim that 'Layer-selective YaRN... outperforms uniform RoPE base' (Sec 3) is supported by RULER scores, but the text admits 'Absolute scores are conservative due to a prompt-formatting issue' (Sec 3). The paper should explicitly state that the *relative* improvement is the valid finding, rather than implying the absolute performance is fully realized, to avoid over-claiming the model's actual long-context capability.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper reports a significant safety regression in the RL-trained 'Instruct' variant (HarmBench score increases from 8.4% to 23.1%, Section Post-Training Evaluation). The authors must explicitly discuss the mechanism of this degradation and provide a mitigation strategy or a clear warning for users deploying the RL variant in sensitive environments.
- **[writing]** The 'Thinking' variant is trained on a mix including 'Reasoning' and 'Math' with RLVR. The paper does not address the risk of these models generating harmful content within their 'reasoning traces' (chain-of-thought) which might be visible to users or logged, potentially bypassing standard safety filters that only inspect final outputs.
- **[writing]** The RL data mix includes 'Agentic tool use' and 'Code' with programmatically verifiable rewards. The authors must clarify if the code execution sandbox used for reward verification is fully isolated to prevent the model from executing malicious payloads (e.g., data exfiltration, system compromise) during the training loop itself.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** Table 1 (Pre-training) and Tables 3-4 (Post-training) report single-point benchmark scores without confidence intervals, standard deviations, or seed counts. For claims of statistical significance (e.g., MMLU-Pro 59.3% vs 48.6%), the authors must report the number of evaluation seeds and variance to rule out random fluctuation.
- **[science]** The RLVR section (Sec 4.2) claims performance gains from 'IcePop truncation' and 'concision penalties' but provides no ablation study isolating these specific components from the base GRPO algorithm. Without a controlled comparison (e.g., GRPO vs. GRPO+IcePop), the attribution of gains to these specific mechanisms is unsupported.
- **[science]** The long-context extension (Sec 3) cites a RULER score of 0.64 at 64K but notes a 'prompt-formatting issue' in the appendix. The authors must clarify if the reported scores are corrected for this issue or if the 0.64 figure is an underestimate. If the latter, the claim of 'competitive' long-context performance requires re-evaluation with corrected metrics.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** Report uncertainty metrics (standard deviation or confidence intervals) for all benchmark scores in Tables 1, 4, and 5. Single-point estimates without variance measures prevent assessment of statistical significance, especially for small margins (e.g., MMLU-Pro 59.3% vs 58.6%).
- **[science]** Clarify the statistical methodology for RLVR evaluation. Specify the number of independent seeds, sampling temperature, and whether results are averaged over multiple runs or single deterministic passes. The lack of variance reporting in RL tables (e.g., LiveCodeBench 75.1% vs 69.9%) obscures result stability.
- **[science]** Define the statistical basis for the '21% higher throughput' claim in Section 6. Provide the sample size (number of requests), confidence interval, or p-value supporting this difference against the Qwen2.5-7B baseline to rule out random fluctuation.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript contains significant structural fragmentation. Section 5 (Long Context) and Section 6 (Post-Training) appear to be duplicated or split across disjointed chunks (e000 vs e001/e002), resulting in repeated figure captions, table definitions, and narrative text. The authors must consolidate these sections into a single, continuous flow to ensure readability.
- **[writing]** In Section 3.1 (Architecture Design Decisions), the text abruptly transitions from discussing dense vs. sparse configurations to a benchmark table without a clear introductory sentence explaining the table's purpose or the specific metrics being compared. A brief lead-in sentence is required to improve cohesion.
- **[writing]** The 'IcePop truncation' mechanism is introduced in Section 6.3.1 (RL algorithm) with a reference to an undefined variable $ho_t$ and parameters $lpha, eta$ without prior definition in the text. The manuscript should explicitly define these variables and their physical meaning before presenting the loss formula.
- **[writing]** Several figure captions (e.g., Fig 2, Fig 3, Fig 4) end with ellipses ('...') or incomplete sentences (e.g., '... See \cref{app:ruler-formatting} for caveats...'). These captions must be rewritten as complete, self-contained sentences to meet standard technical writing conventions.
