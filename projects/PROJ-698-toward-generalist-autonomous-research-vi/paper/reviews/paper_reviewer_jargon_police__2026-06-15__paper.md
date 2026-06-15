---
action_items:
- id: d5243eb2c62f
  severity: writing
  text: Define ReAct at first use in Section 1; currently appears as 'ReAct-style
    search harness' without explaining it as reasoning+acting framework.
- id: 35ec1322c2a5
  severity: writing
  text: Define MLE-Bench Lite acronym at first mention in Section 3.2; 'MLE' not expanded
    anywhere in main text.
- id: 6434dfb59f01
  severity: writing
  text: Define HLE and DeepSearchQA benchmarks when first mentioned in Section 4.5;
    currently appear without context for non-specialists.
- id: fd5a4668250d
  severity: writing
  text: Replace 'held-out' with 'test set' or 'unseen test data' at first use; 'held-out'
    is standard ML jargon but may exclude broader readers.
- id: aa4f81f646de
  severity: writing
  text: Replace 'worktree' with 'isolated working copy' or 'separate code branch'
    on first occurrence; git-specific terminology excludes non-developers.
- id: a69998c116c8
  severity: writing
  text: Replace 'backpropagate' when describing insight propagation in Section 3.2;
    this term suggests gradient backpropagation and may confuse readers.
- id: 104c35fe7955
  severity: writing
  text: Replace 'scalar scores' with 'numerical scores' for accessibility; 'scalar'
    is technical notation.
- id: 24d7f805a2ad
  severity: writing
  text: Define 'artifact' early when first used to mean 'research code/output' to
    distinguish from general usage.
- id: eb82bb8c69de
  severity: writing
  text: Replace 'frontier control' with 'search frontier management' or 'active hypothesis
    tracking' for clarity.
- id: 8dac8cfd561e
  severity: writing
  text: Define 'backbone model' in Section 4.4 or use 'base LLM' for consistency with
    general ML terminology.
artifact_hash: 88742764198e42271ebc43f37d5e1e51228f45ab317f6876141f053d5db6ac69
artifact_path: projects/PROJ-698-toward-generalist-autonomous-research-vi/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-15T11:39:09.160408Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

**Jargon Overuse Review**

This paper contains substantial technical jargon that reduces accessibility for non-specialist readers. While many terms are defined, the density and consistency of specialized terminology creates barriers.

**Acronyms Not Defined at First Use:**

1. **ReAct** (Section 1, Table 1): Appears as "ReAct-style search harness" without explaining it refers to the reasoning+acting framework. Non-specialists cannot parse this.

2. **MLE-Bench Lite** (Section 3.2): The acronym "MLE" is never expanded in the main text. Appears in abstract, introduction, and experiments without definition.

3. **HLE and DeepSearchQA** (Section 4.5): Two search-agent tasks appear without any explanation of what they are or their domain.

**Terms That Could Be Simplified:**

1. **"held-out"** (throughout): This is standard ML terminology but excludes readers unfamiliar with train/dev/test splits. Replace with "test set" or "unseen data" at first use with parenthetical explanation.

2. **"worktree"** (Section 3.2, Appendix): Git-specific terminology. Replace with "isolated working copy" or "separate code branch" on first occurrence.

3. **"backpropagate"** (Section 3.2, Algorithm 1): When used for insight propagation, this suggests gradient backpropagation and may confuse readers. Use "propagate upward" or "summarize and share."

4. **"scalar scores"** (Section 3): Replace with "numerical scores" for accessibility.

5. **"frontier control"** (Section 3.2): Replace with "search frontier management" or "active hypothesis tracking."

6. **"backbone model"** (Section 4.4): Use "base LLM" for consistency with general ML terminology.

7. **"evidence-conditioned"** (Section 5): Replace with "based on prior experimental results."

8. **"material"** (Section 3, AO formulation): This is an unusual term for "research code/output." Replace with "code artifact" or "initial implementation" for clarity.

**Recommendation:**

The paper should add a "Terminology" subsection in the Introduction or Appendix that defines all specialized terms (AO, HTR, ReAct, MLE-Bench, worktree, held-out, etc.). This would allow the main text to maintain technical precision while remaining accessible to a broader research community.
