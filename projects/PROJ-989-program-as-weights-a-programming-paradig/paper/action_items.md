# Automated-review action items — Program-as-Weights: A Programming Paradigm for Fuzzy Functions

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: reject

- **[writing]** Abstract and Section 5 claim PAW (0.6B) matches Qwen3-32B (73.78% vs 68.70%). However, Table 1 shows gpt-oss-20B (20B) achieves 85.45% on FuzzyBench. The claim that PAW matches the 'state of the art' or '32B' is misleading as a smaller 20B model outperforms both. Restate the comparison to acknowledge gpt-oss-20B or clarify the specific baseline family.
- **[fatal]** Section 5 and Table 1 cite 'gpt-5.2' and 'gpt-5-mini' as baselines achieving 96.09% and 91.87%. As of the current date, no such models (GPT-5 series) exist in the public record or OpenAI's release history. These baselines appear hallucinated or future-dated, invalidating the reported performance ceiling and the comparison against PAW. Verify the actual model used or remove these rows.
- **[fatal]** Section 5 states FuzzyBench was generated using 'gpt-5.2'. Since 'gpt-5.2' is a non-existent model (see above), the provenance of the 10M-example dataset is unsupported. The dataset construction claims rely on a hallucinated source. Replace with a real model name (e.g., GPT-4o) or provide evidence of the model's existence.
- **[science]** Section 5 claims the 'gpt-5.2' data-generating model achieves 96.09% on FuzzyBench. If the model used to generate the data is hallucinated, the 'empirical ceiling' metric is also fabricated. The reported ceiling must be recalculated using a real, verifiable model to support the claim that PAW approaches the limit of the task.
- **[writing]** Section 5 cites 'Qwen3-VL-4B' and 'Qwen3-4B-Instruct-2507'. While Qwen3 is a plausible future version, the specific '2507' date suffix and the existence of a 'Qwen3-VL' variant in 2026 are unverified. If these models do not exist, the architecture description and the multimodal results in Table 2 are unsupported. Confirm the actual model versions used.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[fatal]** Figure 4: The caption 'Compile [fig-1-2.pdf]' appears to be a broken internal reference or placeholder rather than a descriptive caption, failing to explain the diagram's content.
- **[science]** Figure 4: The diagram depicts a 'Compiled Neural Program' containing both dark green and light blue bars, but the legend only defines the dark green color as 'Discrete Token', leaving the light blue bars undefined.
- **[science]** Figure 6: The caption claims the LLM is invoked 'only at compile time, not at every move,' but the UI shows 'Zog thinks...' and a 26s timer, implying a live inference step per turn that contradicts the stated architecture.
- **[writing]** Figure 6: The caption specifies '0.6B Qwen3 PAW interpreter,' but the UI header displays 'Zog is a 0.6B-parameter AI' without naming the model family (Qwen3), creating a minor inconsistency in technical specificity.
- **[writing]** Figure 8 caption contains incomplete sentences and missing references: 'Text-to-LoRA instantiation of PAW ()' and 'compose LoRA matrices... over shared learnable bases ()' lack equation numbers; 'The same pipeline holds for the prefix-tuning precursor (, with architecture' is cut off.
- **[science]** Figure 8: The 'LoRA Mapper' section shows mixing coefficients being applied to 'LoRA A Bases' and 'LoRA B Bases', but the caption does not explicitly define the composition operation (e.g., weighted sum) or clarify how the discrete pseudo-program relates to the continuous LoRA weights shown.
- **[science]** Figure 9: The caption states the v1 base layer contains 2.5M examples, but the legend for the 'Core text processing & NLP' category explicitly lists 2.95M (30%); this numerical contradiction between the text and the chart data must be resolved.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The paper is generally well-structured and avoids excessive in-group slang, but it relies on a few specific notations and subfield-specific terms that are introduced without sufficient definition for a competent reader from an adjacent field (e.g., a systems or general NLP researcher). The most significant omissions are in the mathematical notation in Section 2.2. The symbols τ (the prefix tokens), d_{teacher}, and d_{int} (or d_{in}^{(m)}) appear in equations and text without explicit definitio

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** Abstract claims '30 tokens/s' but Section 7 reports '31.6 tokens/s'. Update Abstract to match the precise value or use 'over 30 tokens/s'.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Abstract claims PAW 'matches' Qwen3-32B performance and 'runs at 30 tokens/s'. Table 1 shows PAW actually outperforms (73.78% vs 68.70%), and the 30 tok/s speed applies only to a specific quantized config (Sec 7), not the bf16 baseline used for the performance comparison. Scope the speed claim to the quantized variant or clarify the config mismatch.
- **[writing]** Abstract states PAW 'matches' Qwen3-32B performance. Table 1 shows PAW (0.6B) outperforms Qwen3-32B (73.78% vs 68.70%) on FuzzyBench. 'Matches' understates the result and implies equivalence where there is superiority. Replace 'matches' with 'outperforms' or 'surpasses' to accurately reflect the evidence in Table 1.
- **[writing]** Section 7 claims the system 'runs at 30 tokens per second on a MacBook M3'. This figure is specific to a Q5_K_M + Q4_0 quantized setup (Table 7), whereas the main results (Table 1) use bf16. The abstract and conclusion imply this speed is general to the PAW system as evaluated. Scope the claim to 'a quantized variant' to avoid implying the default model runs at this speed.
- **[writing]** Conclusion claims the paradigm shifts the role of foundation models universally from 'problem solver' to 'tool builder'. The evidence is limited to single-step fuzzy tasks on FuzzyBench and specific case studies. The conclusion omits the limitation that this shift is not yet validated for multi-step or complex agentic workflows. Narrow the claim to 'for the class of fuzzy functions evaluated'.

## paper_reviewer_safety_ethics — verdict: accept

The paper presents a novel programming paradigm (Program-as-Weights) for compiling natural-language specifications into small, locally executable neural artifacts. From a safety and ethics perspective, the work is low-risk. The primary dataset, FuzzyBench, is explicitly described as fully synthetic, generated by an LLM (`gpt-5.2`), and contains no scraped personal data, PII, or human-subject information; thus, no IRB/consent statement is required. The authors release the dataset and code, but the content is synthetic task specifications and inputs/outputs, posing no re-identification risk.

The paper includes a "Broader Impacts" section (Appendix \ref{appendix:broader_impacts}) that correctly identifies the shift from cloud-based to local execution as a positive impact (reduced API dependency, improved reproducibility) and reasonably assesses the negative impacts. The authors argue that the released interpreter is small (0.6B parameters) and specialized for specific fuzzy functions, limiting its utility for general-purpose disinformation or fraud compared to frontier models. This assessment is proportionate to the system's design.

There are no indications of dual-use capabilities that are unmitigated. The system is designed to run locally and offline, which inherently reduces the risk of mass-scale automated abuse compared to API-based services. The "fuzzy functions" described (log monitoring, JSON repair, intent classification) are benign developer tools. The paper does not describe methods for generating exploits, biological agents, or surveillance tools. The use of synthetic data avoids the ethical pitfalls of scraping user content without consent.

No specific safety or ethical gaps were identified that require disclosure or mitigation beyond what is already present. The work is a standard algorithmic/methodological contribution with appropriate, albeit brief, consideration of its impact.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The central claim of the paper—that the Program-as-Weights (PAW) paradigm enables a 0.6B model to outperform a 32B model on fuzzy tasks via a compiler-generated adapter—is not yet supported by the experimental design presented. The primary evidence relies on comparisons against baselines that are not controlled for input context and a test set that is entirely synthetic and generated by the same model family used to create the training data. First, the comparison in Table 1 between PAW (0.6B) an

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** The paper presents a novel paradigm but lacks rigorous statistical reporting for its quantitative claims. The primary issue is the absence of uncertainty quantification. Section 5 and Table 1 report precise point estimates (e.g., 73.78% vs 68.70%) for the main comparison between PAW and baselines, but do not report the number of random seeds used, nor the standard deviation or confidence intervals. In the context of training neural networks, performance varies significantly across seeds; reporti

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The paper is generally well-written, with a clear narrative arc and strong technical exposition. The abstract effectively summarizes the method and results, and the introduction successfully frames the problem and solution. However, there are several instances where sentence structure impedes immediate comprehension or where the tone fluctuates between formal and informal. In the Introduction, the description of the compile pipeline initially suggests two identical models before clarifying their
