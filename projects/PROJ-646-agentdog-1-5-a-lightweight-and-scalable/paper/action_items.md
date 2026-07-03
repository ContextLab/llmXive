# Automated-review action items — AgentDoG 1.5: A Lightweight and Scalable Alignment Framework for AI Agent Safety and Security

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[science]** The claim that AgentDoG matches GPT-5.4 performance (Abstract, Intro) relies on citations to unreleased/future-dated sources (e.g., openai_gpt54_2026, anthropic_claude_opus_46_2026). Verify these citations exist and that the comparison data is not hallucinated or based on speculative system cards.
- **[writing]** The claim of 'around 1k samples' for training (Abstract, Sec 4.2) is supported by a purification step from 5,973 tools, but the exact final count of training trajectories used for the 0.8B-8B models is not explicitly stated in the text or tables, making the '1k' figure an unverified approximation.
- **[science]** Table 1 (e006) and Table 2 (e000) present conflicting results for AgentDoG-4B on R-Judge (92.2% vs 91.8% F1) and ATBench (72.4% vs 92.8% F1). The text does not explain which table represents the final results or why the metrics differ so drastically between the two tables.
- **[science]** The claim that the environment reduces Docker overhead by 'two orders of magnitude' (Abstract) and to '1/100' (Intro) is supported by a memory claim (<2.5GB) but lacks a direct comparison of Docker memory usage for equivalent tasks, making the specific '100x' ratio an unsupported extrapolation.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[writing]** Figure 1: The x-axis labels for the 'AgentDoG' model variants are colored orange, while the bars are also orange, creating a visual redundancy that makes the text harder to distinguish from the bars compared to the grey bars.
- **[writing]** Figure 1: The x-axis labels are rotated at a steep angle, which is necessary for fit but makes the model names (e.g., 'Qwen3-235B') difficult to read quickly.
- **[writing]** Figure 3: The caption repeatedly refers to 'Building Pipeline of .' and '...of .' with a missing model name, likely due to a placeholder variable not being replaced in the final text.
- **[writing]** Figure 3: The 'Risk Sampling' box lists '15 Risk Sources', '21 Failure Modes', and '11 Real-world Harms', but the figure does not visually depict these specific counts or categories, making the text feel disconnected from the visual flow.
- **[science]** Figure 4: The caption claims the left panel isolates 'embedded deceptive instructions,' but the visual highlights the 'Environment' block (containing resume data) and the 'Key Impact Step' (containing the instruction), failing to visually distinguish the 'benign data' from the 'deceptive instruction' as promised.
- **[writing]** Figure 4: The caption states 'Highlighted regions indicate the top-ranked components,' yet the figure uses red text highlighting without a legend or key to define what the red color signifies (e.g., attribution score, confidence, or specific token importance).
- **[science]** Figure 5: The caption claims the figure shows 'Comparative attribution analysis' and highlights 'high-impact drivers' (Steps 2, 3, 4, 5), but the rendered image displays a chronological 'Trajectory' of actions and thoughts with 'Traj Scores' rather than an attribution heatmap or importance map. The visual content does not match the caption's description of an attribution analysis.
- **[writing]** Figure 5: The figure title 'Attribution Comparison: AgentDoG vs. Base Model' is generic and does not specify the scenario (WeChat red packet) or the specific models (Qwen3-4B) mentioned in the caption, making the figure standalone context poor.
- **[writing]** Figure 6: The caption contains a grammatical error and missing subject: 'filtered agentic safety SFT data by .' and 'selected by ,' (likely missing 'AgentDoG').
- **[science]** Figure 6: The donut charts lack numerical labels or percentages on the segments, making it impossible to verify the distribution claims or compare segment sizes accurately.
- **[writing]** Figure 7: The caption 'The dual-scenario environment synthesis pipeline for agentic safety RL' is grammatically incomplete and lacks the specific subject name (e.g., 'AgentDoG') that is present in other captions (e.g., Figure 3, Figure 6).
- **[science]** Figure 7: The 'malicious query attack' path depicts a 'Malicious User Request' combined with a 'Benign Environment Context' to create a 'Safety Task Bundle'. This contradicts standard safety evaluation logic where a malicious request is typically paired with a vulnerable or corrupted context to test for failure, whereas the 'Benign User Request' path pairs with a 'Corrupted Environment Context' to create a 'Clean Task Bundle', which seems counter-intuitive for a safety synthesis pipeline.
- **[science]** Figure 8: The caption claims memory footprint remains 'highly stable' and consumes 'less than 2.5 GB', but the 'Peak RSS' data (orange dashed lines) in all three subplots shows a clear, monotonic increase with workload, contradicting the claim of stability.
- **[writing]** Figure 8: The y-axis label 'Per-Env Time (ms)' is rotated 90 degrees and difficult to read; it should be horizontal or the font size increased for clarity.
- **[writing]** Figure 9: The caption 'Our online agent safety guardrail pipeline' is too generic and fails to describe the specific components shown (e.g., AgentDoG Guardrail, Trajectory Formatter, Agent Runtime) or the data flow between the 'Autonomous Agent Execution' and 'Online Guardrail' sections.
- **[writing]** Figure 9: The text 'Judges full trajectory' inside the AgentDoG Guardrail box is grammatically awkward and likely a typo for 'Judges the full trajectory' or 'Judges full trajectory context'.
- **[writing]** Figure 10: The caption describes the figure as 'A lightweight and scalable alignment framework' but fails to name the framework (AgentDoG) or explain the specific components shown (Application 1 vs. Application 2), making the diagram difficult to interpret without reading the main text.
- **[writing]** Figure 10: The central logo contains the text 'AgentDoG', but this name is not explicitly defined in the caption, which refers to the system only as 'A lightweight and scalable alignment framework'.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Define 'MCP' (Model Context Protocol) at first use in Section 1 or 2. Currently used without definition.
- **[writing]** Define 'SFT' (Supervised Fine-Tuning) and 'RL' (Reinforcement Learning) at first use. These acronyms appear frequently without prior definition.
- **[writing]** Define 'GDPO' (Group Reward-Decoupled Normalization Policy Optimization) at first use in Section 3.3. The acronym is used before the full term is introduced.
- **[writing]** Replace 'trajectory' with 'sequence of actions' or 'execution history' in the Introduction and Section 3.1 to improve accessibility for non-specialists.
- **[writing]** Define 'ATBench' and its variants (ATBench-Claw, ATBench-Codex) clearly at first mention in Section 2. The distinction between the base and customized versions needs a plain-language explanation.
- **[writing]** Replace 'finite-state' with 'simplified deterministic' when describing the simulation environment in Section 3.4 to reduce jargon density.
- **[writing]** Define 'ASR' (Attack Success Rate) and 'TTFT' (Time To First Token) in Section 5.3 where they are first used in the table context.

## paper_reviewer_overreach — verdict: full_revision

- **[science]** The manuscript exhibits significant overreach in its claims regarding performance equivalence, resource efficiency, and data efficiency, which are not fully substantiated by the provided experimental data. First, the Abstract and Introduction repeatedly claim that AgentDoG achieves performance "comparable to GPT-5.4" and "matches closed-source models." However, the results tables (Table 1, Table 2) do not present a direct, head-to-head comparison with GPT-5.4 on the specific ATBench or R-Judge m

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The paper details synthetic attack generation (e.g., WhatsApp injection) in Appendix C. Authors must add an ethics statement restricting dataset use to safety research, consider redacting specific exploit payloads to prevent dual-use, and clarify the license.
- **[writing]** The online guardrail evaluation (Section 5) lacks confirmation that testing occurred in isolated, non-production environments. A statement confirming sandbox-only deployment is required to address potential service disruption risks.
- **[writing]** The influence-function purification method (Section 4.2) does not address potential bias in sample selection. Authors should clarify how diversity of safety risks was maintained to avoid filtering out edge cases.

## paper_reviewer_scientific_evidence — verdict: full_revision

- **[science]** The manuscript presents a compelling framework for agent safety, but the scientific evidence supporting the central claims requires significant strengthening. The most critical issue is the lack of statistical rigor in the experimental results. The claim that AgentDoG-4B matches or exceeds GPT-5.4 (Table 1, Sec 4.4) is presented with point estimates only. Given the relatively small test sets (e.g., ATBench-Claw has 500 trajectories), the absence of confidence intervals or p-values makes it impos

## paper_reviewer_statistical_analysis — verdict: full_revision

- **[science]** The statistical rigor of the evaluation section requires significant strengthening before the claims can be accepted. First, the central claim of achieving state-of-the-art performance with "around 1k samples" (Abstract; Section 4.2) is statistically unsupported. The manuscript does not specify the exact number of samples used, nor does it provide a variance analysis. Given the high dimensionality of the task, a sample size of ~1,000 is small. The authors must report the exact count, the standar

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 3.2 (Data Preparation), the phrase 'around 1k samples' is used repeatedly. Replace with a precise integer (e.g., '1,024 samples') or a specific range to maintain scientific rigor and consistency with the '1,000 trajectories' mentioned in Section 2.3.
- **[writing]** Section 4.1 contains a sentence fragment: 'Mixture: 1:2 safety-critical to benign (50,000 benign trajectories from ToolBench, ToolAlpaca, ToolACE).' Rewrite as a complete sentence, e.g., 'The final dataset maintains a 1:2 mixture of safety-critical to benign trajectories, incorporating 50,000 benign samples from...'
- **[writing]** In Section 5.2, the text states '35 retained CIK‑Bench cases' but the table caption refers to 'CIK‑Bench' without defining the acronym earlier in the section. Ensure 'CIK-Bench' is defined upon first use or replaced with the full name if it is not a standard benchmark.
- **[writing]** The abstract claims the framework updates the safety taxonomy for 'Codex/OpenClaw scenarios,' but the Introduction (Section 1) and Section 2.3 distinguish between 'ATBench-Claw' and 'ATBench-Codex' as separate benchmark instances. Clarify in the abstract whether the taxonomy update applies to both distinct scenarios or a unified one.
