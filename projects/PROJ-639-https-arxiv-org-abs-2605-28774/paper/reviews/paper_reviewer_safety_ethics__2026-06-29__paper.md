---
action_items:
- id: fb0d560dda06
  severity: writing
  text: Expand the Broader Impacts section to explicitly discuss dual-use risks of
    enhanced agentic tool capabilities, beyond sandboxing.
- id: 0fc924220ade
  severity: writing
  text: Address privacy implications of the web search tool usage (e.g., query logging,
    data retention by third-party APIs).
- id: 3ea62cbedb67
  severity: writing
  text: Discuss mitigation strategies for potential misuse (e.g., adversarial prompts,
    automated harmful actions) rather than stating safety is out of scope.
artifact_hash: c3a0cadd7f6fad4530caf3425af37b062e581bf6756717caa2b10b397e7c3c2b
artifact_path: projects/PROJ-639-https-arxiv-org-abs-2605-28774/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-29T10:45:59.359155Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_safety_ethics
score: 0.0
verdict: minor_revision
---

This review focuses exclusively on safety and ethics considerations regarding the proposed AXPO method for multimodal agentic reasoning.

The manuscript identifies the "Thinking-Acting Gap" and proposes a reinforcement learning method to improve tool use in Vision-Language Models. While the technical contribution is clear, the safety and ethical implications of enhancing agentic capabilities are insufficiently addressed. In the **Broader Impacts** section (Appendix, `text/9_appendix.tex`), the authors state: "Beyond this sandboxing, broader safety considerations... are out of scope for this work and were not addressed." This explicit exclusion is problematic for a paper advancing autonomous agent capabilities.

Enhanced tool-use proficiency (Python execution, web search) inherently increases dual-use risks. An agent trained to reliably execute code and search the web could be misused for automated vulnerability scanning, malicious script generation, or privacy-violating data gathering. The current discussion limits safety to "sandboxed execution," which mitigates immediate system damage but does not address the intent or downstream consequences of the agent's actions.

Additionally, the use of the Tavily search API introduces data privacy concerns. The paper notes an exclusion list for benchmark integrity (`exclude_domains = ["huggingface.co"]`) but does not discuss the privacy of search queries sent to third-party services or the potential for the agent to inadvertently expose sensitive information during tool calls.

To meet ethical standards for agentic AI research, the authors should revise the Broader Impacts section to:
1.  Explicitly enumerate potential misuse scenarios associated with improved tool reliability.
2.  Propose mitigation strategies beyond sandboxing, such as input/output filtering or human-in-the-loop verification for high-risk actions.
3.  Discuss privacy implications of external tool usage and data handling.

These changes are textual and do not require re-running experiments, but they are necessary to responsibly frame the deployment of more capable agents.
