---
action_items:
- id: 70833a079e1d
  severity: writing
  text: The claim that S-Agent is the 'first tool-use agent for multi-view and long-video
    spatial intelligence' (Abstract, Intro) is overreaching given the existence of
    concurrent works like Think3D (cited in Related Work) which also handles active
    3D exploration. The distinction needs to be more precise regarding 'continuous'
    vs 'active exploration' to avoid hyperbole.
- id: 0ef390611296
  severity: writing
  text: The statement that S-Agent-8B 'performs comparably to advanced closed-source
    models (e.g., GPT-5.4 and Gemini 3)' (Abstract, Intro) is not fully supported
    by the data. Table 1 shows S-Agent-8B (41.6%) trailing GPT-5.4 (41.9%) on MMSI-Bench
    and trailing Gemini 3 Pro (60.9%) on ReVSI. The claim should be tempered to 'competitive
    with' or 'approaching' rather than 'comparable to' given these specific deficits.
- id: cf01dbf4d61e
  severity: writing
  text: The claim that S-Agent 'surpasses... all open-weight spatial models' (Abstract)
    is contradicted by Table 1 and Related Work, where SN-SI-1.3-IVL3-8B scores 61.3%
    on ViewSpatial-Bench, outperforming S-Agent's 60.0%. The claim of surpassing 'all'
    is inaccurate on this benchmark and needs qualification.
artifact_hash: daf6f96ab0f7dc8b7f7a6cf5f7a9c2a699ed007819d222e3f1594a2f92961a95
artifact_path: projects/PROJ-747-s-agent-spatial-tool-use-elicits-reasoni/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-02T19:57:47.910660Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the immediate evidence provided in the results tables, particularly regarding "firsts" and absolute superiority over all baselines.

First, the Abstract and Introduction repeatedly claim S-Agent is the "first tool-use agent for multi-view and long-video spatial intelligence." While the authors cite concurrent work like Think3D in the Related Work section, the main text dismisses prior art as focusing on "static images" or "single-image 3D QA." However, Think3D (cited as `zhang2026think3d`) is described in the Related Work as equipping agents with "3D reconstruction and camera-manipulation tools, enabling active exploration through ego/global-view switching." If Think3D also handles multi-view or video inputs via active exploration, the "first" claim is an overreach. The distinction between "continuous multi-view" and "active exploration" should be explicitly clarified to justify the "first" assertion, rather than broadly dismissing prior concurrent work.

Second, the claim that the distilled model S-Agent-8B "performs comparably to advanced closed-source models (e.g., GPT-5.4 and Gemini 3)" (Abstract, Introduction) is not fully supported by the quantitative results. In Table 1 (MMSI-Bench), S-Agent-8B scores 41.6%, while GPT-5.4 scores 41.9%. In Table 3 (ReVSI), S-Agent-8B scores 52.8%, while Gemini 3 Pro scores 60.9%. While the performance is competitive, stating it is "comparable" to models that consistently outperform it by 1-8 percentage points on key benchmarks is an overstatement. The language should be adjusted to "competitive with" or "approaching the performance of" to accurately reflect the data.

Third, the Abstract states that S-Agent "surpasses... all open-weight spatial models." Table 1 shows S-Agent (46.4%) outperforming the listed open-weight spatial models (e.g., SN-SI-1.1-Qwen3VL-8B at 38.1%, VST-7B-SFT at 32.5%). However, the Related Work section and Table 1 caption mention SN-SI-1.3-IVL3-8B, which achieves 61.3% on ViewSpatial-Bench (a benchmark where S-Agent scores 60.0%). If SN-SI-1.3-IVL3-8B is considered an "open-weight spatial model" (which the context implies), the claim of surpassing "all" such models is factually incorrect on the ViewSpatial benchmark. The claim should be qualified to specify which benchmarks or which subset of models are surpassed.

Finally, the claim in the Introduction that "Simply and directly applying the S-Agent framework consistently improves the spatial reasoning ability of these VLMs" is slightly overreaching. Table 2 shows that for the Qwen3-VL-8B backbone, the zero-shot S-Agent variant (30.7% on MMSI) actually performs *worse* than the base Qwen3-VL-8B-Instruct (31.1%). The text acknowledges this in Section 4.2 ("simply equipping the base Qwen3-VL-8B-Instruct with S-Agent does not consistently improve performance"), but the Introduction's phrasing suggests a universal improvement that the data contradicts for specific base models. The Introduction should be revised to reflect that improvements are consistent for *stronger* planners (like GPT-5.4) or that the framework *enables* improvement which is then realized through distillation, rather than implying the zero-shot framework alone always improves performance.
