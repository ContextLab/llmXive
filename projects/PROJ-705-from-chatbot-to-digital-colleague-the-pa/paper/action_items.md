# Automated-review action items — From Chatbot to Digital Colleague: The Paradigm Shift Toward Persistent Autonomous AI

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: reject

- **[fatal]** Replace all future-dated models and benchmarks with existing, verifiable counterparts (e.g., GPT-4o, Claude 3.5 Sonnet, current Terminal-Bench).
- **[fatal]** Explicitly reframe the entire results section as a "hypothetical scenario" or "projection," clearly distinguishing it from empirical data, and remove the specific numeric scores that imply actual measurement. As it stands, the central claims regarding the performance of "OpenClaw" and the "Digital Colleague" paradigm are unsupported by any real-world evidence, rendering the paper's scientific contribution unverifiable and misleading.

## paper_reviewer_figure_critic — verdict: major_revision_science

- **[science]** Figure 1: The y-axis label 'Length of Coding Tasks AI Agents Can Complete' and the caption's definition of '50%-time horizon' as 'median task completion length' are contradictory. A 'time horizon' typically refers to the duration an agent can operate or plan ahead (e.g., 12 hours of continuous execution), whereas 'task completion length' implies the time taken to finish a single task. The caption claims the metric is 'median task completion length,' but the data points (e.g., 718.8 min) and the
- **[writing]** Figure 1: The y-axis scale is non-linear and misleading. The distance between 0 secs and 3.3 hours is visually similar to the distance between 3.3 hours and 10 hours, despite the latter being a much larger absolute interval. This distorts the perceived rate of growth, making the exponential curve appear less steep than it would on a linear or properly logarithmic scale. The axis labels (0 secs, 3.3 hours, 6.7 hours, 10 hours) are also inconsistently spaced, further confusing the reader about the
- **[writing]** Figure 1: The 'Key Takeaway' box at the bottom states 'over 12 hours for the leading models in early 2026,' but the highest data point shown (Opus 4.6) is 718.8 minutes (~12 hours) and is positioned at the very end of the x-axis (2026), not 'early 2026.' Additionally, the y-axis only goes up to 10 hours, yet the data point for Opus 4.6 (718.8 min) is plotted above the 10-hour line, creating a visual inconsistency between the axis limit and the data presented.
- **[writing]** Figure 4: The caption describes a generic 'Agent Era' loop, but the rendered image is a detailed, cartoon-style infographic labeled 'AI Agent Era' with specific numbered sections (1 Inputs, 2 Agent Controller, 3 Environment & Tools) and human characters that are not described in the caption.
- **[writing]** Figure 4: The code snippet in the 'Environment & Tools' panel is illegible due to low resolution, making the specific Python implementation details unreadable.
- **[science]** Figure 6: The figure depicts the 'Workspace Substrate' (blue box) and 'Work-Oriented Task Delivery' as part of the solution, but the caption describes Figure 6 as highlighting 'Simple tool invocation' and its limitations. The visual content actually illustrates the 'Workspace + Skill paradigm' (matching Figure 7's description) rather than just the limitations of simple tool calls.
- **[science]** Figure 6: The figure is a composite diagram showing both the 'Ephemeral Tool Calls' (red box) and the 'Workspace Substrate' (blue box). However, the caption only describes the limitations of tool invocation (the red box part) and does not mention the persistent workspace solution (the blue box part) which occupies 50% of the visual space.
- **[writing]** Figure 6: The caption states 'The figure highlights why a workspace is needed', but the figure itself is titled 'Ephemeral Tool Calls' (top) and 'Workspace Substrate' (bottom). The figure lacks a unifying title that reflects the comparison being made, making the relationship between the two halves less clear from the visual alone.
- **[science]** Figure 7: The visual content depicts a three-stage workflow (Ad-hoc Prompts -> Skill Packaging -> Composable Digital Worker) rather than the 'Workspace + Skill paradigm' described in the caption. The figure illustrates the process of creating a skill but fails to show the 'persistent workspace' or the 'combination of workspace context with skill assets' that the caption claims to demonstrate.
- **[writing]** Figure 7: The caption describes a 'Workspace + Skill paradigm' but the figure is titled 'Ad-hoc Prompts', 'Skill Packaging', and 'Composable Digital Worker', creating a disconnect between the figure's internal narrative and the caption's summary.
- **[writing]** Figure 8: The bottom banner contains a typo ('Batter alignment' instead of 'Better alignment').
- **[writing]** Figure 8: The caption claims the figure shows 'why' systems require specific data types, but the figure only illustrates 'what' the data types are (descriptive rather than explanatory).
- **[science]** Figure 10: The caption claims to summarize bottlenecks around 'task closure' and 'context management,' but the figure only depicts 'Long-Horizon & Rollback,' 'Safety & Governance,' and 'Persistent Memory,' omitting the other two claimed categories.
- **[writing]** Figure 10: The legend in Panel I uses a dashed line for 'Planned Path' and a solid line for 'Actual Trajectory,' but the visual representation of the 'Actual Trajectory' (the black line) is thick and stylized, making it difficult to distinguish from the 'Safe Checkpoint' icons along the path.
- **[science]** Figure 11: The figure is a cartoon infographic rather than a scientific diagram; it lacks the specific technical components (models, contexts, tools, skills, workspaces, memories, evaluators, governance mechanisms) mentioned in the caption, instead showing generic 'Trace Capture' and 'Synthesizer' boxes.
- **[writing]** Figure 11: The caption claims the figure illustrates a path from 'reactive chatbots' to 'digital colleagues,' but the figure starts at 'Stage I: Trace Capture' without showing the preceding chatbot or agent eras described in the paper's narrative.
- **[writing]** Figure 12: The caption contains raw LaTeX formatting code (e.g., '0.7mmbluemybluemyblue0.7mm0.7mm') instead of readable text describing the color legend for open-source vs. closed systems.
- **[science]** Figure 12: The timeline includes future dates (e.g., 'Apr 2026', 'Mar 2026') for unreleased models, which contradicts the caption's claim that nodes are labeled by 'release month'.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** Section 1 introduces 'RLVR (Reinforcement Learning with Verifiable Rewards)' and 'GRPO' without defining the acronyms or the methods. A reader from an adjacent field (e.g., NLP or HCI) will not know what these specific RL algorithms entail. Expand 'RLVR' at first use and add a brief clause defining GRPO (e.g., 'Group Relative Policy Optimization').
- **[writing]** Section 2.1 uses 'SoM' and 'UI-TARS' as examples of multimodal perception without expansion. 'SoM' (likely 'Scales of Measurement' or 'State of Mind' in this context, or a specific paper acronym) and 'UI-TARS' are undefined. Spell out 'SoM' and define 'UI-TARS' (e.g., 'User Interface Tool-Augmented Reasoning System') at first mention.
- **[writing]** Section 4.1 lists core metrics for OpenClaw benchmarks including '$	au$-bench' and 'ToolSandbox' without defining what $	au$ represents or what these specific benchmarks measure. Define the symbol $	au$ (e.g., 'time-step' or 'trajectory') and provide a one-sentence gloss for the benchmarks.
- **[writing]** Section 2.2 introduces 'System 2' reasoning referencing Kahneman. While 'System 1/2' is a known psychological concept, in this specific technical context, the paper uses it as a shorthand for 'inference-time computation' without explicitly mapping the metaphor to the technical mechanism (e.g., 'deliberate, compute-intensive reasoning'). Add a clarifying clause linking the term to the technical implementation.

## paper_reviewer_logical_consistency — verdict: accept

The paper's argument structure is logically consistent. The central thesis—that the field is shifting from "Chatbot" (fast, stateless generation) to "Digital Colleague" (slow, persistent, workspace-based execution)—is supported by a coherent progression of definitions and evidence.

1.  **Definition Consistency:** The core concepts ("Workspace," "Skill," "Task Closure") are defined in Section 1 and maintained consistently throughout. Section 2 establishes the "Chatbot" vs. "Thinking LLM" cognitive shift, while Section 3 establishes the "Agent" vs. "OpenClaw" execution shift. These two dimensions are correctly synthesized in Section 4 ("Workspace + Skill") without contradiction.
2.  **Causal/Correlational Logic:** The paper correctly frames the "Time Horizon" growth (Figure 1) as a trend supported by the emergence of specific architectures (Thinking LLMs, Workspaces), rather than claiming a direct causal mechanism where one *causes* the other without evidence. The argument that "fragmented state" (Section 3.1) leads to "brittleness" is supported by the cited benchmarks (WebArena, SWE-bench) which measure exactly that failure mode.
3.  **Evidence Alignment:** The evaluation metrics proposed in Section 4 (Task Closure, State Verifiability) logically follow from the definition of the "OpenClaw Era" (delivering a correct final workspace state). The tables (e.g., Table 1, Table 2) consistently map benchmarks to the specific era they represent, with no contradictions between the text descriptions and the table contents.
4.  **No Internal Contradictions:** The limitations section (Section 3.2) acknowledges risks (skill brittleness, security) that are consistent with the proposed solution (governance, sandboxing) in Section 5. The paper does not claim the solution is perfect, but rather that it is the necessary architectural shift, which is a valid logical stance.

The reasoning holds together: premises (current bottlenecks in statelessness) $\to$ intermediate steps (need for persistent workspaces and reusable skills) $\to$ conclusion (the "Digital Colleague" paradigm). No non-sequiturs or internal contradictions were found.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Title and Abstract claim a realized 'Paradigm Shift' to 'Digital Colleagues,' but the paper is a survey of existing works, not a demonstration of a new system achieving this. Rephrase to 'We survey the emerging paradigm shift...' to align the claim with the evidentiary basis of a literature review.
- **[writing]** Section 2.2 and Table 1 present the 'OpenClaw Era' as an established boundary with solved capabilities, yet the text admits these are 'challenges' and 'bottlenecks.' Temper language from 'The OpenClaw Era' to 'The proposed OpenClaw paradigm' and acknowledge these are aspirational goals, not demonstrated universal properties.
- **[writing]** The Conclusion states 'We have shown that... the Workspace + Skill paradigm drives this transition,' implying empirical proof. The paper provides no new experiments. Replace 'We have shown' with 'We argue' or 'We synthesize evidence suggesting' to reflect that the claim is a hypothesis supported by survey, not new data.

## paper_reviewer_safety_ethics — verdict: accept

This manuscript is a conceptual survey and framework proposal ("From Chatbot to Digital Colleague") rather than an empirical study releasing new models, datasets, or operational tools. Consequently, it does not present the specific, actionable dual-use risks (e.g., providing a novel exploit, releasing a harmful dataset, or describing a biological synthesis route) that would trigger a `fatal` or `science` severity flag.

The paper explicitly identifies and discusses the safety implications of the "Workspace + Skill" paradigm it proposes. Section 3.2 ("Limitations of the Workspace + Skill paradigm") and Section 5 ("Open Challenges") directly address critical risks including:
1.  **Supply-chain risks:** The paper notes that skills present attack surfaces and that registries require provenance tracking and sandboxing (citing `li2026prism`, `zhao2026clawguard`).
2.  **Trajectory-level safety:** It highlights the need for evaluating unsafe behavior in action chains, citing benchmarks like `ATBench-Claw` and `ClawSafety`.
3.  **Governance:** The text argues that "governance is inseparable from workspace design" and calls for permission boundaries and audit logs.

As a survey, the paper does not generate new human-subjects data, scrape private datasets, or release code that could be immediately weaponized. The risks it describes are inherent to the field of autonomous agents (which it surveys) rather than specific, unmitigated outputs of this work. The authors have appropriately acknowledged the safety challenges associated with the paradigm shift they are describing. No specific safety disclosures or mitigations are missing that would prevent publication.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[writing]** This paper presents a conceptual framework for the evolution of LLMs from chatbots to "digital colleagues," relying heavily on a narrative of paradigm shifts (Chatbot → Thinking LLM → Agent → OpenClaw). While the logical structure is sound, the scientific evidence supporting the specific claims of performance trends and the necessity of the proposed "Workspace + Skill" paradigm is currently insufficient to rule out alternative explanations like sampling noise, cherry-picked benchmarks, or model

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Tables 5-8 (e002) report benchmark scores (e.g., '94.0', '87.0') to one decimal place for dozens of models without any measure of uncertainty (SD, SE, or CI). In LLM benchmarking, single-run scores are unstable; report mean ± SD over ≥3 seeds or explicitly state these are single-run point estimates to avoid false precision.
- **[writing]** Figure 1 (horizon.pdf) plots '50%-time horizon' trends over time. The caption cites an external URL for data but does not specify the statistical aggregation method (e.g., median of N runs, best-of-K) or the sample size (N) for each data point. Clarify the aggregation metric and N in the caption to allow assessment of trend reliability.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** The manuscript presents a compelling narrative on the shift from chatbots to digital colleagues, but several structural and grammatical issues impede smooth reading. The most significant problem is the frequent use of sentence fragments and run-on sentences that force the reader to pause and re-parse. For instance, in Section 3.1, the standalone sentence "The shift is from querying external oracles to inhabiting a persistent host" lacks a main verb and context, breaking the flow. Similarly, Sect
