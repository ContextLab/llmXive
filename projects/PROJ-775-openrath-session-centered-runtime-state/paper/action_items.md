# Automated-review action items — OpenRath: Session-Centered Runtime State for Agent Systems

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 1.2 cites the 2019 PyTorch paper to support an architectural analogy for agent runtimes. The paper describes the library, not the specific design philosophy for agents. Clarify that the analogy is derived from usage patterns, not the paper's explicit claims.
- **[writing]** Section 2 cites 2025 documentation URLs for LangGraph's 'time travel' feature. To ensure long-term verifiability of this specific differentiator, consider citing a stable technical report or versioned release notes instead of generic docs.
- **[writing]** Section 5 cites a paper on indirect prompt injection to support the claim about 'data/instruction confusion.' Ensure the citation explicitly supports this specific mechanism phrasing, as the source may describe the attack differently.

## paper_reviewer_figure_critic — verdict: accept

### Figure 1

Figure 1 is a clear and well-structured diagram that effectively visualizes the transition from loop-scattered state to session-boundary artifacts. The flow is logical, the labels are legible, and the visual grouping aligns perfectly with the caption's description of the core boundary.

### Figure 2

Figure 2 effectively visualizes the OpenRath Session as a central crossing object connecting various ecosystem layers. The diagram is clear, with distinct labels for each component and arrows indicating the flow of interaction, fully supporting the caption's description of its ecosystem role.

### Figure 3

Figure 3 is a clear and well-structured flowchart that effectively visualizes the session lifecycle described in the caption. The diagram uses distinct colors and clear labels to differentiate between standard operations (Create, Place, Transform), branching logic (Fork, Main work, Branch work), and finalization steps (Merge, Persist, Replay), with no missing legends or illegible text.

### Figure 4

Figure 4 is a clear and well-structured sequence diagram that effectively illustrates the tool execution boundary described in its caption. All participating components (Agent, Memory, Session, FlowToolCall, Sandbox, Backend) are clearly labeled, and the message flow is logical and easy to follow.

### Figure 5

Figure 5 effectively visualizes the transition from a multi-session runtime to a multi-agent workflow, clearly illustrating how session state is preserved and shared across different agents. The diagram is well-structured, with distinct sections for each session and agent, and the legend at the bottom provides clear definitions for the symbols used. The caption accurately describes the figure's content and purpose.

### Figure 6

Figure 6 is a clear and well-structured flowchart that accurately visualizes the claim-to-evidence protocol described in its caption. The workflow from 'Paper claims' through the 'Smoke suite' to final outcomes ('Supported', 'Scoped', 'Gated') is logical, and all text is legible with no missing labels or confusing elements.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized software engineering and programming language jargon that creates a barrier for non-specialist readers, particularly those in social sciences, humanities, or general computer science who are not familiar with specific runtime architecture patterns. In the Abstract, the term "backend-aware" is used to describe the Session object without defining what a "backend" is in this context (e.g., an execution environment, a sandbox provider, or a cloud service)

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[science]** Section 4 claims merge requires shared sandbox handles, but Section 5 describes 'fresh' sessions with new handles. Explain how merging divergent branches is logically possible under these constraints.
- **[writing]** Figure 2 maps Memory to PyTorch Parameters, implying gradient updates, but Section 3 describes explicit recall/commit. Clarify this mechanistic mismatch to avoid misleading readers.
- **[science]** Memory is listed as a core contribution in Section 1 but is 'evidence-gated' and unimplemented in Sections 7 and 9. Reframe the contribution or provide evidence to resolve this logical gap.

## paper_reviewer_overreach — verdict: minor_revision

- **[writing]** Section 1.2 claims 'Memory is treated as an agent-bound persistent state plane' as a realized design, yet Section 5 and Table 2 admit the memory plane is 'not yet substantiated' and 'evidence-gated.' This over-claims the maturity of a core component relied upon by the central thesis.
- **[science]** Contribution 3 in Section 1.4 lists 'Backend-aware boundaries for tools and memory' as a delivered technical contribution. However, Section 5 confirms the memory plane is unimplemented and evidence-gated. Reframe this as a 'proposed boundary' to align with the actual evidence status.
- **[writing]** The Abstract and Section 1.1 assert 'fork, merge, and replay' are explicit runtime operations generally. Evidence (Section 7) only supports 'lineage export' and 'local sandbox.' Scope these claims to the verified local subset to avoid over-claiming general replay capabilities.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** Section 9 (Limitations) explicitly states 'No safety property is claimed' despite the system enabling tool execution and sandboxed code. Authors must add a dedicated 'Safety and Risk Mitigation' subsection detailing specific guardrails against indirect prompt injection, tool misuse, and sandbox escape, or explicitly state the system is for research-only use with no production deployment path.
- **[writing]** The 'Sandbox' and 'Tool' abstractions (Section 4) allow agents to execute code and modify files. The paper lacks a discussion on data privacy, specifically how sensitive user data or secrets are handled within the session state and whether the sandbox enforces network isolation to prevent data exfiltration.
- **[writing]** The 'Memory' component is described as a 'session-visible persistent plane' (Section 4). The authors must clarify if this memory stores PII or sensitive context and whether the system includes mechanisms for user consent, data retention limits, or the 'right to be forgotten' (deletion of specific session branches).

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper claims 'deterministic' lineage export and workflow transcripts (Table 2, Section 7) but provides no statistical evidence of reproducibility across runs. Include a quantitative measure (e.g., hash collision rate or exact match percentage over N=100 runs) to substantiate the 'deterministic' claim.
- **[science]** The 'evidence packets' (Section 7) are described as 'pass' or 'skip' without sample sizes or control conditions. To support the claim of 'auditable' runtime, provide the number of test cases executed, the specific inputs used, and a comparison against a baseline (e.g., standard JSON logging) to demonstrate the added value of the Session object.
- **[science]** The 'memory plane' is explicitly marked as 'evidence-gated' and 'not yet substantiated' (Table 1, Section 6) yet is listed as a core contribution. The central thesis relies on a complete runtime state; the absence of empirical evidence for the memory component weakens the claim that the system is fully 'inspectable' and 'replayable' as described.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[writing]** Definition of "Deterministic" vs. Statistical Variance: The paper repeatedly claims "deterministic" behavior for lineage export and workflow composition (Section 7, Table 4). If the system is truly deterministic, statistical variance is zero, and standard statistical tests are inapplicable. If there are stochastic elements (e.g., in tool selection or memory recall when not in "smoke test" mode), the paper must specify the number of trials ($n$) and the observed variance (e.g., standard deviation
- **[writing]** Evidence for "Memory Plane" Claims: The Memory component is listed as "evidence-gated" and "not yet substantiated" (Section 5, Table 2; Section 9, Table 5). While the authors correctly avoid making unsupported claims, the criteria for moving this from "gated" to "supported" should include a statistical power analysis or a defined sample size for future evaluation. Merely stating that "source anchors are absent" is a software engineering status; a statistical review requires knowing what data vol
- **[writing]** Scope of "Focused Tests": Section 7 mentions "focused tests" and a pytest_report as evidence. For a statistical review, it is crucial to know if these tests involve randomized inputs or edge-case sampling. If the evaluation is purely deterministic (fixed inputs, fixed outputs), the claim of "inspectability" is a software engineering property, not a statistical one. The text should explicitly state that no statistical generalization is claimed for these specific results to avoid misinterpretation

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 4 (Runtime Architecture), the sentence 'The session loop combines built-in and user tools, sends schemas to the provider, resolves returned tool calls by name, validates arguments, and invokes the selected tool with the active session' is a long, dense list of actions. Consider breaking this into two sentences or using a bulleted list to improve readability and clarify the sequence of operations.
- **[writing]** Throughout the manuscript (e.g., Abstract, Section 1.2, Section 3), the phrase 'PyTorch-like' or 'PyTorch-inspired' is used to describe the programming model. While the analogy is explained, the repetition of 'PyTorch' in close proximity to 'tensor' and 'forward' can be slightly distracting. Consider varying the phrasing (e.g., 'composable computation model') after the initial definition to maintain flow without losing the core analogy.
- **[writing]** In Section 5 (Multi-Agent Multi-Session Design), the paragraph beginning 'The engineering examples use this shape...' contains a sentence fragment: 'The domain-specific roles differ, but the runtime contract does not.' This is grammatically acceptable as a stylistic choice but feels abrupt. Consider integrating it into the previous sentence or expanding it slightly to ensure smooth cohesion with the surrounding text.
