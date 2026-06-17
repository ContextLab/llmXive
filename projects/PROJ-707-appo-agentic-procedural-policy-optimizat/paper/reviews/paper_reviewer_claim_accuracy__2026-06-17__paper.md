---
action_items:
- id: 032d435c56aa
  severity: science
  text: The manuscript claims that APPO keeps "efficient tool-calls" but provides
    no quantitative measurement (e.g., average number of tool calls per episode) to
    substantiate this. Add a metric and corresponding results or remove/qualify the
    claim.
- id: 9c5bf34bc374
  severity: writing
  text: The statement that APPO "consistently improves strong agentic RL baselines
    by nearly 4 points" is not uniformly supported by the reported numbers (e.g.,
    on the Llama 3.1-8B backbone the gain over ARPO is ~2.1 points). Adjust the wording
    to reflect the actual observed improvements across backbones.
- id: f30015b8da5d
  severity: writing
  text: Several citations (e.g., \cite{wang2025beyond}, \cite{guo2025segment}) are
    used to back broad assertions about procedural knowledge and credit assignment,
    but the cited works do not directly discuss "procedures" as defined in this paper.
    Verify that each citation specifically supports the claim, or replace with more
    appropriate references.
artifact_hash: 3a43673385ee45c44ff0ac04e7e12a654dbb1cefe913b5676a26e486f2c9fad4
artifact_path: projects/PROJ-707-appo-agentic-procedural-policy-optimizat/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: openai.gpt-oss-120b
prompt_version: 1.1.0
reviewed_at: '2026-06-17T21:18:27.612592Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_claim_accuracy
score: 0.0
verdict: minor_revision
---

The review concentrates on the factual correctness of the manuscript’s claims and the adequacy of the citations that are meant to support them.

**1. Magnitude of reported improvements**  
The abstract and introduction assert that APPO “consistently improves strong agentic RL baselines by nearly 4 points.” Table 1 shows a 2.1‑point gain over ARPO on the Llama 3.1‑8B backbone (57.4 vs 55.3) and a 3.9‑point gain on Qwen2.5‑7B (62.2 vs 58.3). The “nearly 4 points” phrasing only holds for the latter model and overstates the improvement for the former. The claim should be qualified (e.g., “up to ≈ 4 points”) or the reported numbers should be adjusted.

**2. Efficiency of tool‑calls**  
Multiple sections claim that APPO “keeps efficient tool‑calls” and “maintains behavior interpretability.” No quantitative metric (average tool‑call count, latency, or overhead) is presented in any table, figure, or appendix. Without empirical evidence, this claim is unsupported. The authors need to add a concrete measurement or retract the statement.

**3. Relevance of procedural‑knowledge citations**  
The paper introduces “procedures” as fine‑grained decision points and cites works such as \cite{wang2025beyond} and \cite{guo2025segment}. Those references discuss procedural reasoning or segment‑level credit assignment but do not explicitly define or evaluate the exact notion of “procedures” used here. Consequently, the citations do not fully substantiate the novelty claim. The authors should either locate more directly relevant literature or clarify how the cited papers relate to their definition.

**4. Theoretical claims in Theorem 1**  
Theorem 1 assumes a monotonic relationship between conditional reward variance and the branching score (BS). This assumption is not empirically validated in the main text. Providing data that high‑BS tokens indeed exhibit higher variance, or tempering the theorem’s scope, would strengthen the claim.

**5. Pilot study and Figure 1**  
Figure 1’s entropy distribution, accuracy versus entropy/BS, and pass@k plots align with the manuscript’s statements that decision points are broadly distributed and that raw token entropy is not a reliable predictor of downstream impact. These claims appear adequately supported.

**6. Ablation results**  
Table 3 demonstrates consistent performance drops when the Branching Score is replaced by pure entropy, when the future‑aware advantage term is removed, or when dual‑group advantage estimation is omitted. The corresponding narrative correctly reflects these findings.

**Overall assessment**  
The core experimental results are sound, but a few high‑level claims are either overstated or lack supporting evidence. Addressing the tool‑call efficiency metric, calibrating the improvement‑magnitude language, and ensuring citation relevance will bring the manuscript into full factual alignment.
