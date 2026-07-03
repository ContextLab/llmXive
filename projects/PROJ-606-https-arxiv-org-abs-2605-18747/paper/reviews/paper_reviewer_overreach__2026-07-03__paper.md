---
action_items:
- id: 8fa433d24fbb
  severity: science
  text: The claim that 'LLM-simulated execution achieves 98%+ precision/recall' (Section
    4.1, Patterns and Trends) is presented as a general fact without a specific citation
    or scope definition. This risks over-generalizing results from a single method
    (QualityFlow) to the entire field of simulated execution. Please clarify the source
    and limit the claim to the specific system studied.
- id: e1e2bfeaabab
  severity: writing
  text: The statement that 'No system fully unifies both' repository-based and execution-based
    representations (Section 4.1, Patterns and Trends) is a strong negative claim.
    Given the breadth of the survey, the authors should either provide a definitive
    list of excluded systems or soften the language to 'No major system surveyed fully
    unifies...' to avoid over-claiming completeness.
- id: 75162f739ad1
  severity: writing
  text: The paper cites 'GPT-5-Codex' and 'GPT-5.1-Codex-Max' (Section 5.1) as existing
    systems trained on long-horizon interactions. As these refer to unreleased or
    hypothetical model versions (given the 2026 date context), the authors must explicitly
    state these are projections or future work, rather than presenting them as established
    empirical facts to avoid over-claiming current capabilities.
artifact_hash: cbd4e8e17c331b3d11d6d3473a72ca30389ded91296199ea84247ea30361db9d
artifact_path: projects/PROJ-606-https-arxiv-org-abs-2605-18747/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T15:39:56.055030Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The manuscript presents a comprehensive survey on "Code as Agent Harness," but several sections exhibit over-claiming by extrapolating specific findings to general principles or presenting hypothetical future states as established facts.

First, in Section 4.1 ("Patterns and Trends"), the authors state: "Self-Collaboration and QualityFlow show LLM-simulated execution achieves 98%+ precision/recall." This phrasing implies a general capability of simulated execution across the field. However, this metric is likely specific to the *QualityFlow* system's "Imagined Execution" module. Attributing this high precision to the broader concept of "LLM-simulated execution" without qualifying that it is a result of a specific, gated mechanism overstates the current state of the art. The claim should be restricted to the specific system or explicitly framed as a potential upper bound rather than a general achievement.

Second, the assertion in Section 4.1 that "No system fully unifies both" repository-based and execution-based representations is a definitive negative claim. While the survey likely covers the major works, asserting a total absence of such systems without a formal proof or exhaustive enumeration risks over-claiming the survey's completeness. It is safer to phrase this as "No *major* system surveyed fully unifies..." or to explicitly list the systems considered to justify the gap.

Third, the manuscript frequently cites systems like "GPT-5-Codex" and "GPT-5.1-Codex-Max" (Section 5.1) as if they are existing, deployed entities with specific training data characteristics. Given the paper's 2026 context, these appear to be hypothetical or future projections. Presenting them as factual, existing systems that "are explicitly trained on long-horizon, multi-turn coding interactions" constitutes an over-claim of current reality. The authors must distinguish between existing systems and projected/future capabilities to maintain scientific rigor.

Finally, the claim that "Implicit convergence... is the most prevalent pattern" (Section 4.2) is a strong quantitative assertion. While likely true based on the authors' reading, it should be supported by a brief quantitative breakdown of the surveyed systems (e.g., "X out of Y systems surveyed rely on implicit convergence") rather than a qualitative generalization, to avoid over-claiming the statistical dominance of this pattern.
