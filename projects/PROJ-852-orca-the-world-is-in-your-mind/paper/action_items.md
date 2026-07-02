# Automated-review action items — Orca: The World is in Your Mind

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: full_revision

- **[fatal]** Citation keys for future-dated or non-existent models (e.g., 'GPT54', 'Gemini-3.1-pro', 'Qwen3.5', 'DeepSeek-V4') are unsupported by the provided bibliography. The bib file contains entries for these, but they cite 2025/2026 dates and URLs that do not exist in the public domain as of the current date. Claims of performance against these baselines (e.g., Table 1, Table 3) are factually unverifiable and likely hallucinated.
- **[science]** The claim that Orca-4B achieves a 51.8 average score on text benchmarks (Table 1) and outperforms 'V-JEPA 2.1' (75.4 on MVBench) is internally inconsistent. The text states Orca is 'best among same-size VLMs and large-size world models,' yet V-JEPA 2.1's MVBench score (75.4) is significantly higher than Orca's (65.3). The comparison logic in the text does not support the conclusion drawn.
- **[writing]** The citation 'judge1.5' is used in Section 5.1 (Metrics) and Table 4 but is missing from the provided bibliography (TR_Ref.bib). The claim that PRM-as-a-Judge and 'judge1.5' are used for diagnostics cannot be verified.
- **[science]** The paper claims 'no action-labeled data was used in pre-training' (Section 5.1.2) yet cites 'pi0.5' (a VLA model trained on robot data) as a baseline. While this is a valid comparison, the text implies Orca's action capabilities emerge solely from video, but the baseline comparison does not isolate the effect of action-label pre-training in the baselines (e.g., V-JEPA 2.1 vs Orca) clearly enough to support the 'emergence' claim without further ablation.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'OOD' (out-of-distribution) at first use in Section 3.2 (Appendix Evaluation Settings) and Section 4.2.3.
- **[writing]** Define 'VLA' (Vision-Language-Action) at first use in Section 3.2 and Section 4.2.3.
- **[writing]** Define 'MBA' (Multiple Binary Accuracy) at first use in Section 3.2 under TemporalBench description.
- **[writing]** Define 'TI2I' (instruction-conditional image-to-image) at first use in Section 4.2.1 (PRICE-V0.1 description).
- **[writing]** Define 'LoRA' (Low-Rank Adaptation) at first use in Section 4.2.2 (Vision Readout settings).
- **[writing]** Define 'PRM' (Process Reward Model) at first use in Section 3.2 (Metrics) and Section 4.2.3.
- **[writing]** Define 'FSDP' (Fully Sharded Data Parallel) at first use in Section 4.1 (Infrastructure).
- **[writing]** Define 'DiT' (Diffusion Transformer) at first use in Section 4.2.3 (Action Readout).
- **[writing]** Define 'MMDiT' at first use in Section 4.2.2 (Vision Readout settings).
- **[writing]** Replace 'readout' with 'decoder' or 'interface' in several instances (e.g., Section 4.2, 4.3) to reduce jargon density for non-specialists.

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** "The paper presents a coherent logical flow from the 'world latent' hypothesis to the multi-modal readout results. The central claim—that pre-training on state transitions (without action labels) yields a latent space that improves downstream text, image, and action tasks—is supported by the scaling laws (Figures 1-2) and the ablation study. The logic that 'stronger latent leads to stronger readouts' (Answer 1.2) follows directly from the observed correlation between pre-training loss and downst

## paper_reviewer_overreach — verdict: full_revision

- **[science]** Claiming the 'world latent' alone drives robot success is overreach. The Action Expert uses 200 trajectories/task. The gain may stem from fine-tuning data or architecture, not just pre-training. Clarify the causal link or reduce the claim.
- **[science]** The paper states the model 'alleviates robot data scarcity' via zero-shot latent, yet evaluation uses 200 trajectories per task for the Action Expert. This contradicts the zero-shot implication. The claim overstates generalization without the fine-tuning data.
- **[science]** Attributing performance gains solely to the 'world latent' is unsupported. Baselines use the same Action Expert and training data. The gap may be due to initialization or optimization, not the paradigm. Rule out confounders before claiming causal efficacy.
- **[writing]** Listing 'Quantum' and 'Proteins' as future readout targets is a severe overreach for a 4B video-language model. No evidence or theory supports generalizing macroscopic video dynamics to quantum states. Remove or heavily qualify this speculative claim.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[science]** The paper lacks explicit IRB/IACUC approval statements or ethical clearance for the real-robot experiments described in Section 4.3 (Appendix). Given the use of physical hardware and potential for physical harm during OOD failures, a formal safety protocol or ethics board approval statement is required.
- **[science]** The evaluation relies on LLM judges (Gemini 3.1 Pro, GPT 5.4) for scoring image and action generation (Section 4.2, Appendix). The paper does not address the potential for bias, hallucination, or safety misalignment in these automated judges, nor does it provide a human-in-the-loop verification step for safety-critical failures.
- **[writing]** The 'PRICE-V0.1' benchmark and real-robot tasks involve physical interactions. The paper does not explicitly discuss the safety measures taken to prevent physical damage to the robot or the environment during the 'failure' scenarios described in Figures 5-9 (Appendix). A safety mitigation statement is needed.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The claim that action generation emerges from video pre-training lacks causal evidence. The ablation study does not isolate the 'world latent' contribution from the base VLM's inherent capabilities. A controlled experiment is required.
- **[science]** The real-robot evaluation uses only 200 trajectories per task. With 5 tasks and 2 OOD settings, statistical power is low. Report confidence intervals or perform significance testing on FNS/DRR metrics to validate gains over pi_0.5.
- **[science]** The PRICE-V0.1 benchmark relies entirely on LLM judges without validation against human ground truth. Provide inter-rater reliability analysis or correlation with human ratings to support the quantitative claims of superiority.
- **[science]** The scaling law analysis does not clarify if the 12.5K video hours contain duplicates. Clarify the data deduplication strategy and plot loss vs. unique video duration to substantiate the scalability claim.

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The ablation study (Table 4) reports single-point averages for complex downstream tasks (Text, Image, Action) without standard deviations, confidence intervals, or significance testing. Given the high variance in LLM benchmarks, claim 'All three objectives provide the most balanced downstream readouts' is statistically unsupported without error bars or p-values.
- **[science]** The real-robot evaluation (Table 3) uses a rule-based scoring system with integer points. The paper reports mean scores (e.g., 36.6 vs 31.2) but omits the number of independent trials (N) per task and model, and lacks statistical tests (e.g., t-test, Mann-Whitney U) to confirm if the observed differences are significant or due to random variance in robot execution.
- **[science]** The image prediction benchmark (Table 2) relies on LLM judges (Gemini, GPT-5.4) scoring on a 1-5 scale. The paper reports mean and standard deviation but does not address inter-rater reliability (e.g., Cohen's Kappa) or the potential bias of using proprietary models as ground truth, which undermines the statistical validity of the '59.8' score claim.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript contains significant structural redundancy. Sections 'Evaluation' (e001) and 'Loss of Proposed Learning Paradigm' (e002) repeat identical content, figures, and tables. The authors must consolidate these into a single, coherent narrative flow to improve readability and remove confusion.
- **[writing]** In Section 'Evaluation Settings' (Appendix), the list of baselines includes 'SmolVLM2', but the bibliography and main text consistently refer to 'SmolVLM'. Ensure consistent naming conventions throughout the manuscript to avoid reader confusion.
- **[writing]** Several figure captions (e.g., Fig. 1 in e002) are truncated or incomplete in the source text (e.g., 'Unconsciou...'). Ensure all captions are fully written and grammatically complete before final compilation.
