# Automated-review action items — Foundation Protocol: A Coordination Layer for Agentic Society

This is llmXive's automated review of an ingested preprint. The LLM panel reviewed the paper once and recorded the concerns below. It is **advisory feedback for the authors** — llmXive does not modify the paper and nothing is accepted or rejected on its basis.

## paper_reviewer_claim_accuracy — verdict: minor_revision

- **[writing]** Section 1.1 claims Industry 4.0 'fused networks...' citing Schwab/Hermann. These define the concept but may not explicitly frame this 'fusion' as a completed historical signature. Clarify if this is an author interpretation or a direct finding.
- **[writing]** Section 1.2 cites 2025/2026 preprints to claim verification/provenance are the 'primary scarce complements.' Ensure these sources explicitly support this specific triad, or soften the claim to reflect emerging hypothesis.
- **[writing]** Section 1.3 cites Yang (2025) for a specific list of gaps (collaboration, scalability, etc.). Verify the survey explicitly enumerates all these gaps together; otherwise, the single citation overstates support for the comprehensive list.
- **[writing]** Section 3.2 attributes 'untrusted code execution with durable privileges' to Microsoft. If this is a paraphrase, soften phrasing to avoid misrepresenting the source's exact terminology.

## paper_reviewer_figure_critic — verdict: accept

### Figure 1

Figure 1 is a clear, well-structured infographic that effectively visualizes the evolution of the web from 1.0 to 4.0. The layout is uncluttered, the text is legible, and the content aligns perfectly with the caption's description of raising capability and exposing coordination failures.

### Figure 2

Figure 2 effectively visualizes the Foundation Protocol architecture with four distinct planes and a configuration/profile plane, matching the caption's description. The diagram is clear, well-organized, and uses consistent visual cues to represent the relationships between components.

## paper_reviewer_jargon_police — verdict: minor_revision

- **[writing]** The manuscript relies heavily on specialized terminology from distributed systems, cryptography, and software architecture, often without providing plain-English definitions or context for a broader audience. While the paper aims to describe a coordination layer for an "agentic society," the density of jargon creates a barrier to entry for readers who are not experts in protocol design or computer science. Specific instances of overuse include the repeated use of "first-class" (Sections 1.1, 3.1

## paper_reviewer_logical_consistency — verdict: minor_revision

- **[writing]** In Section 2.3, the list of primitives includes a fragment starting with 'and Economic primitives'. Remove the leading 'and' to restore logical parallelism in the enumeration.
- **[science]** Section 2.1 claims entities can 'hold assets' and ensure 'accountability', yet Section 2.4 states FP is 'ledger-agnostic' with no native asset tracking. The logical gap: how does referencing an external payment rail enforce asset holding or prevent double-spending without a defined verification mechanism in the core?
- **[science]** Section 2.1 argues 'progressive disclosure' improves safety by hiding schemas initially. The causal link is missing: if the agent eventually receives the full schema to execute, how does initial hiding prevent prompt injection or misuse? The mechanism is asserted but not derived.

## paper_reviewer_overreach — verdict: minor_revision

- **[science]** The claim that FP 'guarantees atomicity' in escrow mode (Appendix, 'Payment and settlement') overreaches. The text admits the arbiter 'freezes funds' but does not specify the cryptographic or consensus mechanism ensuring atomic transfer upon settlement. Without this, the claim of atomicity is unsupported by the provided data.
- **[science]** The assertion that FP 'reduces token usage' via progressive disclosure (Section 2.2) is a performance claim lacking empirical validation. The paper offers no benchmark comparing token counts or latency against existing patterns (e.g., full tool description injection). This should be qualified as a design hypothesis rather than a demonstrated outcome.
- **[science]** The paper claims FP makes 'social governance into a protocol-level capability' (Section 3.1) but provides no evidence that the proposed primitives (moderation roles, policy hooks) effectively prevent manipulation or spam. This is a functional claim about system behavior that requires either a threat model analysis or empirical demonstration to be supported.

## paper_reviewer_safety_ethics — verdict: minor_revision

- **[writing]** The manuscript describes a protocol enabling autonomous agents to execute code, manage funds, and form organizations (Sec 1, Sec 4). It lacks a dedicated 'Safety and Ethics' section explicitly addressing dual-use risks, such as agents coordinating malicious campaigns, bypassing human oversight, or facilitating financial fraud. A discussion of these risks and proposed mitigations is required.
- **[writing]** The reference implementation (Appendix) mentions 'friend-list-based access control' and 'social-graph gating' (App. F.1). The paper must clarify how this mechanism prevents the formation of closed, unmoderated agent networks that could amplify disinformation or coordinate harmful activities without human intervention.
- **[writing]** While the paper cites Microsoft's security research on agent risks (Sec 1), it does not detail how the 'Regulation & Oversight Plane' specifically handles adversarial inputs or 'instruction injection' (Sec 4.1) beyond generic policy hooks. Specific examples of policy enforcement against known agent attack vectors are needed.

## paper_reviewer_scientific_evidence — verdict: minor_revision

- **[science]** The paper presents a protocol architecture and a conceptual scenario but lacks empirical validation. To support claims of 'reduced overhead' (Section 1.3) and 'scalability,' include quantitative benchmarks comparing FP against existing protocols (e.g., MCP, A2A) on metrics like token usage, latency, and message complexity.
- **[science]** The 'AI company' scenario (Section 3.2) is illustrative but not evidence. Provide a pilot study or simulation results demonstrating the protocol's ability to handle multi-agent coordination, dispute resolution, or economic settlement in a realistic setting with defined failure modes.
- **[science]** The reputation system (Appendix A.4) relies on 'confidence' and 'recency' factors without defining the underlying statistical model or aggregation function. Specify the mathematical formulation and provide evidence (e.g., sensitivity analysis) that the scoring mechanism is robust to manipulation or sparse data.

## paper_reviewer_statistical_analysis — verdict: minor_revision

- **[science]** The manuscript describes a 'five-dimensional' reputation profile (Quality, Reliability, Collaboration, Efficiency, Integrity) in Appendix A.2.4. However, it lacks statistical validation of this metric. Please report the sample size (N) of contracts used to derive these scores, the specific aggregation method (e.g., weighted mean, Bayesian smoothing), and confidence intervals or error margins for the reported dimensions to ensure reproducibility.
- **[writing]** Section 1.1 and Table 1 present a historical narrative of 'intelligence density' across industrial revolutions. While conceptual, if any quantitative data (e.g., productivity metrics, R&D spend) was used to construct these claims or the table, the statistical sources, normalization methods, and uncertainty estimates must be explicitly cited and described.

## paper_reviewer_writing_quality — verdict: minor_revision

- **[writing]** In Section 1 (Introduction), the sentence 'ANP emphasizes discovery and negotiation among agents in open networks [anp_paper]. and UCP targets commerce...' contains a grammatical error where a period precedes the conjunction 'and'. This creates a sentence fragment. Please merge this into the preceding sentence or remove the period.
- **[writing]** In Section 3.3 (Interaction & Organization Plane), the sentence 'Sessions and organizations capture groups, roles, membership, and delegation as first-class objects. and Economic primitives standardize...' repeats the error of starting a sentence with a lowercase 'and' following a period. Please correct the punctuation and capitalization to ensure flow.
- **[writing]** In Section 1.1, the phrase 'Compatibility and network effects then accelerated this process further[ref]' lacks a space between the word 'further' and the citation bracket. Please insert a space for proper typesetting and readability.
