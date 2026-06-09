---
action_items:
- id: accae5eed9ca
  severity: science
  text: Code repository is referenced externally (github.com/CentreChen/EmbFilter)
    but not included in submission. For code quality review, actual implementation
    files must be accessible to verify reproducibility, modularity, and test coverage.
- id: 0a9fcbe17559
  severity: writing
  text: Algorithm pseudocode and PyTorch implementation in the appendix are commented
    out (# comments). Include working code snippets or at minimum un-comment the implementation
    for reviewer verification.
- id: e858b91931c4
  severity: science
  text: No dependency specification (requirements.txt, environment.yml, or similar)
    is included in the paper artifacts. Add explicit dependency list for reproducibility
    from scratch.
artifact_hash: 694aa60fc8ffd3b190e6ddc550509dfa2e47bde4175f0797a9228a9e466061a8
artifact_path: projects/PROJ-682-your-unembedding-matrix-is-secretly-a-fe/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-09T16:21:03.518914Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_code_quality_paper
score: 0.0
verdict: minor_revision
---

This paper review is limited to the code_quality_paper lens, which focuses on code artifacts that produced the research results.

**Critical Limitation**: The actual implementation code is hosted on an external GitHub repository (https://github.com/CentreChen/EmbFilter) and is not included in the paper submission. Without access to the code, I cannot evaluate:
- Code readability and modularity
- Test coverage and quality
- Dependency management
- Reproducibility from scratch

**Paper-Internal Code Artifacts**:

1. **Algorithm Pseudocode** (lines 260-280, commented out): The `Algorithm 1` pipeline for EmbFilter is entirely commented out with `%` markers. This prevents reviewers from verifying the method's correctness even at the pseudo-code level.

2. **PyTorch Implementation** (lines 780-810, Appendix): Similarly commented out. A working implementation snippet should be included for reproducibility verification.

3. **No Dependency Specification**: The paper mentions "official MTEB implementation" but provides no requirements.txt, environment.yml, or package version specifications. This is essential for reproducing experiments from scratch.

**Recommendations**:
- Include the actual implementation files as supplementary material, or provide a working code snippet in the appendix
- Add a `requirements.txt` or `environment.yml` specifying exact dependency versions
- Uncomment the algorithm and implementation examples for reviewer verification
- Ensure the GitHub repository includes comprehensive tests and documentation

Without these artifacts, the reproducibility claim in the abstract ("Our code is available at...") cannot be independently verified by reviewers, which is a standard requirement for publication.
