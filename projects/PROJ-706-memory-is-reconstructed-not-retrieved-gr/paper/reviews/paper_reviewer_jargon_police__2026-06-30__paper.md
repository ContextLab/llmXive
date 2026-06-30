---
action_items:
- id: 6542b1c4c130
  severity: writing
  text: 'Section 3.1: ''heterogeneous graph'' should be ''graph containing different
    types of nodes''; ''combinatorial explosion'' should be ''exponential growth in
    search space''.'
- id: fbcea298f1e0
  severity: writing
  text: 'Section 4.3: ''approximation-theoretic view'' should be ''theoretical perspective
    based on function approximation''; ''hypothesis classes'' should be ''sets of
    possible input-output mappings''.'
- id: be5fa6a752cc
  severity: writing
  text: 'Appendix C.1: ''payload'' should be ''content''; ''branching bound'' should
    be ''maximum number of neighbors''.'
- id: 888f148b67d2
  severity: writing
  text: "Appendix C.2: '0\u20131 loss' should be 'binary loss function'; 'population\
    \ risk' should be 'expected error over all possible data points'."
- id: fe65007336d7
  severity: writing
  text: "Appendix C.3: 'active policy' should be 'policy that adapts based on observations';\
    \ 'passive policy' should be 'policy that selects actions based only on the query'.\
    \ Additionally, acronyms like 'CTC' (Cue\u2013Tag\u2013Content) and 'MRAgent'\
    \ are not defined at first use. The term 'engrams' in Section 8.2 is used without\
    \ definition. The phrase 'needle-in-a-haystack' in Appendix C.4 is an idiomatic\
    \ expression that should be replaced with 'finding a specific item in a large\
    \ dataset'. These issues collectivel"
artifact_hash: b428847249c815694ce34a179b14e661a1c8a1e001ab2124c52ead974dee57ea
artifact_path: projects/PROJ-706-memory-is-reconstructed-not-retrieved-gr/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-06-30T02:30:04.816080Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_jargon_police
score: 0.0
verdict: minor_revision
---

The paper exhibits significant jargon overuse that hinders accessibility for non-specialist readers. Key terms such as 'heterogeneous graph', 'combinatorial explosion', 'engrams', 'approximation-theoretic view', 'hypothesis classes', 'compositional action space', 'population risk', 'approximation error', '0–1 loss', 'branching bound', 'payload', 'TopK', 'CRUD operations', 'multi-hop', 'distillation', 'active set', 'reconstructed context', 'traversal actions', 'routing function', 'state-dependent exploration', 'tool invocations', 'needle-in-a-haystack', 'binary tree', 'ground-truth', 'prior', 'irreducible error', 'distribution', 'active policy', 'passive policy', 'retrieval budget', and 'node-retrieval operator' are used without definition or with overly technical phrasing. 

Specific instances include:
- Section 3.1: 'heterogeneous graph' should be 'graph containing different types of nodes'; 'combinatorial explosion' should be 'exponential growth in search space'.
- Section 4.3: 'approximation-theoretic view' should be 'theoretical perspective based on function approximation'; 'hypothesis classes' should be 'sets of possible input-output mappings'.
- Appendix C.1: 'payload' should be 'content'; 'branching bound' should be 'maximum number of neighbors'.
- Appendix C.2: '0–1 loss' should be 'binary loss function'; 'population risk' should be 'expected error over all possible data points'.
- Appendix C.3: 'active policy' should be 'policy that adapts based on observations'; 'passive policy' should be 'policy that selects actions based only on the query'.

Additionally, acronyms like 'CTC' (Cue–Tag–Content) and 'MRAgent' are not defined at first use. The term 'engrams' in Section 8.2 is used without definition. The phrase 'needle-in-a-haystack' in Appendix C.4 is an idiomatic expression that should be replaced with 'finding a specific item in a large dataset'. 

These issues collectively exclude non-specialist readers and violate the principle of clear scientific communication. The authors should replace technical jargon with plain language, define all acronyms and specialized terms at first use, and avoid idiomatic expressions.
