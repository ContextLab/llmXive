---
action_items:
- id: 76e11db0b7e0
  severity: writing
  text: The manuscript references external code artifacts (e.g., GitHub repo in Introduction)
    but lacks a `reproducibility.md` or `README` section in the LaTeX source detailing
    the exact dependency versions (PyTorch, specific Qwen checkpoints), random seeds,
    and hardware specs required to replicate the 150-step training runs. Add a dedicated
    'Reproducibility' subsection in the Appendix with a checklist of environment variables
    and a `requirements.txt` snippet.
- id: 99d5252c5129
  severity: writing
  text: The paper relies on an external LLM analyzer (GLM-5.2) for skill extraction
    (Section 2.2, Appendix B). The code quality review requires the prompt template
    used for this analyzer to be included verbatim in the appendix or a supplementary
    file to ensure the skill extraction process is reproducible. Currently, only a
    figure reference exists; the actual prompt text must be provided.
- id: 403f4c00b656
  severity: writing
  text: The theoretical analysis in Appendix A contains truncated equations and proofs
    (e.g., Eq. 3.4 and the proof of Prop 3.1 appear cut off in the provided source).
    Ensure all mathematical derivations are complete and untruncated in the final
    submission to allow for verification of the routing regret bounds.
artifact_hash: ebe41e02149487ccd15d4c76bf5323b1b6f5d76f7c2ba35eb80cabef31288797
artifact_path: projects/PROJ-795-opid-on-policy-skill-distillation-for-ag/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-01T00:05:19.797563Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

The provided LaTeX source for the OPID paper demonstrates a solid structural organization but lacks the specific code-quality artifacts required for full reproducibility from scratch. While the methodology is described textually, the "code quality" of the research artifacts is compromised by missing implementation details that prevent an independent researcher from re-running the experiments.

First, the manuscript references a GitHub repository in the Introduction but does not include a `reproducibility` section or a `README` equivalent within the paper itself. For a code-quality review, it is essential to see a clear statement of the software environment. Specifically, the paper mentions training Qwen2.5 and Qwen3 models for 150 steps with specific batch sizes, but the exact versions of the RL libraries (e.g., `trl`, `vllm`), the specific commit hashes of the base models, and the hardware configuration (GPU type, count) are not explicitly listed in a machine-readable format or a dedicated table. Without this, the "150 steps" claim is not reproducible, as training dynamics can vary significantly across different library versions.

Second, the core mechanism of OPID relies on an external LLM analyzer (GLM-5.2) to extract skills (Section 2.2, Appendix B). The paper includes a figure of the analyzer prompt (`figures/OPID_analyser_prompt.pdf`) but does not provide the actual text of the prompt in the LaTeX source or a supplementary file. To ensure the skill extraction process is reproducible, the exact prompt template, including any few-shot examples or system instructions, must be provided verbatim. Relying solely on a rendered figure makes it difficult to copy-paste the prompt for replication.

Third, the theoretical analysis in Appendix A appears to suffer from truncation. The proof for Proposition 3.1 (Routing optimality) and the equations following it seem to be cut off in the provided source text. A complete paper must contain full, untruncated mathematical derivations to allow for verification. If the source file was truncated during ingestion, the final submission must ensure these sections are complete.

Finally, while the paper mentions using specific hyperparameters (e.g., $\lambda_{\mathrm{skill}} = 0.001$), there is no mention of random seeds used for the experiments. Reproducibility in RL requires fixing seeds for trajectory sampling, analyzer calls, and optimization to ensure that the reported gains are not due to stochastic variance. A `seed` parameter and its value should be explicitly stated in the Implementation Details.

To address these issues, the authors should add a "Reproducibility Checklist" in the Appendix, include the full text of the analyzer prompt, ensure all theoretical proofs are complete, and explicitly list the random seeds and software environment versions used.
