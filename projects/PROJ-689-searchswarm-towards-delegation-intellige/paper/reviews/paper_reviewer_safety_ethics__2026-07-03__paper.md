---
action_items:
- id: caec90bdb94a
  severity: writing
  text: 'The paper presents a multi-agent system (SearchSwarm) designed for long-horizon
    deep research, utilizing web browsing tools and delegated sub-agents. From a safety
    and ethics perspective, the primary concerns revolve around data privacy, the
    potential for generating hallucinated citations in a research context, and the
    dual-use nature of autonomous information gathering. Data Privacy and Consent:
    In Section 3.3 ("Supervised Fine-tuning"), the authors state that data is sourced
    from RedSearcher a'
artifact_hash: 23164a835e9fc14f10b36f04bd2aeba4213e5a3b759192c46a449dbfe25b61f3
artifact_path: projects/PROJ-689-searchswarm-towards-delegation-intellige/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T17:13:56.292721Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

The paper presents a multi-agent system (SearchSwarm) designed for long-horizon deep research, utilizing web browsing tools and delegated sub-agents. From a safety and ethics perspective, the primary concerns revolve around data privacy, the potential for generating hallucinated citations in a research context, and the dual-use nature of autonomous information gathering.

**Data Privacy and Consent:**
In Section 3.3 ("Supervised Fine-tuning"), the authors state that data is sourced from RedSearcher and OpenSeeker and that they will "open-source our harness, weights, and data." While the source datasets are external, the authors must explicitly confirm in the manuscript that the synthesized trajectories used for training do not contain Personally Identifiable Information (PII) or private user queries from the original datasets. Given the nature of "deep research," there is a risk that user prompts could contain sensitive personal or corporate information. A statement confirming that a privacy filter was applied to the training data before release is necessary to ensure compliance with data protection norms.

**Hallucination and Misinformation:**
The system is designed to produce "citation-grounded reports" (Section 3.2). However, the case study in Appendix C (Section 5) demonstrates the model synthesizing complex facts about real-world infrastructure projects (e.g., Coomera Connector, Inland Rail) and specific corporate joint ventures. While the example shows correct retrieval, the reliance on LLMs to synthesize these reports carries a risk of "citation hallucination," where the model invents plausible-sounding but non-existent sources or misattributes facts. The paper should include a discussion on the robustness of the citation verification mechanism and the potential for the system to be used to generate misleading research reports if the verification step is bypassed or fails.

**Dual-Use and Autonomous Browsing:**
The system employs autonomous web browsing tools (`search`, `visit`, `google_scholar`) to gather information. While intended for research, this capability could be misused for automated scraping of restricted content, social engineering (by gathering personal details), or generating disinformation campaigns at scale. The authors should briefly address these dual-use risks in the "Limitations" or "Ethical Considerations" section, perhaps noting that the system is intended for benign research tasks and that the authors have not tested it against adversarial prompts designed to extract sensitive data.

**Conclusion:**
The paper does not appear to violate fundamental ethical principles, but it lacks explicit statements regarding data privacy in the released artifacts and the potential risks of autonomous information gathering. Addressing these points will strengthen the paper's ethical standing.
