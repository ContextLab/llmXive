---
action_items:
- id: 025ba9f8b9f7
  severity: science
  text: Clarify the logical boundary between 'Code for Acting' (Sec 2.2) and 'Tool
    Use' (Sec 3.3) to reduce taxonomic redundancy in agent-environment interactions.
- id: aea5492e989f
  severity: science
  text: Explicitly link the 'shared state gap' identified in Sec 4.3 back to the specific
    memory mechanism limitations discussed in Sec 3.2.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-02T05:21:00.097429Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_logical_consistency
score: 0.0
verdict: minor_revision
---

The survey presents a logically coherent three-layer taxonomy (Interface, Mechanisms, Scaling) that consistently frames code as the operational substrate for agent systems. The definition of 'code as agent harness' is maintained throughout the manuscript, with claims regarding executability and statefulness supported by the cited literature in Sections 2 and 3. The causal argument that code transforms stateless models into functional agents via harnesses is well-structured and aligns with the provided examples (e.g., Section 1 Introduction).

However, there is a logical redundancy in the classification of agent-environment interactions that weakens the distinctness of the taxonomy layers. Section 2.2 ('Code for Acting') describes code as an action interface for grounded skill selection and policy generation, explicitly citing systems that map intent to executable behaviors. Section 3.3 ('Tool Use') similarly describes tools as the action and observation layer connecting the agent to the environment, citing systems that use tools for repository navigation and execution. While the authors frame Section 2 as an 'interface' and Section 3 as a 'mechanism', the functional descriptions overlap significantly in the text (e.g., both discuss environment interaction and execution feedback). This creates a logical ambiguity where a single system capability could fit into two layers, reducing the taxonomic rigor. To strengthen the argument, the authors should explicitly delineate the boundary between 'acting' (high-level policy/skill abstraction) and 'tool use' (specific API/environment calls) to ensure the layers remain mutually exclusive where claimed.

Additionally, the claim in Section 4.3 ('The central gap is the lack of formal shared substrates') is logically consistent with the earlier discussion on implicit state in Multi-Agent Systems (MAS). However, the argument would be more robust if it explicitly referenced the specific memory mechanism limitations discussed in Section 3.2 (e.g., 'Context Compaction' or 'Multi-Agent Memory') as the root cause of this gap. Currently, the connection between the mechanism-level analysis and the MAS-level gap is implied but not causally linked in the text. Strengthening this link would ensure the open problems section follows deductively from the mechanism review.

Overall, the logical flow is strong, but resolving these taxonomic overlaps and causal links will improve the internal consistency of the survey's framework.
