---
action_items:
- id: 6c0fa702590a
  severity: science
  text: The claim that MemGUI-8B-SFT achieves the 'best open-data 8B performance'
    (Sec 6) is overreaching. The paper compares against closed-source or proprietary
    models (e.g., Gemini, M3A) and does not explicitly benchmark against all relevant
    open-weight 8B baselines (e.g., specific fine-tuned variants of Llama-3.2-Vision
    or other community models) to substantiate the superlative 'best'.
- id: 0618c58a2244
  severity: writing
  text: The introduction (Sec 1) attributes performance drops solely to 'passive ReAct-style
    prompting' causing 'prompt explosion.' This is an over-simplification that ignores
    other potential factors like visual grounding degradation or action space complexity
    in long horizons, which are not ruled out by the provided ablation studies.
- id: de08488879b0
  severity: science
  text: "The claim that 'Full ConAct reduces total failures by 41% (99\u219258)' (Fig\
    \ 4 caption) lacks statistical rigor. Without confidence intervals, p-values,\
    \ or a description of the variance across multiple seeds/runs, this specific percentage\
    \ reduction is presented as a definitive fact rather than an observed trend, risking\
    \ over-interpretation of stochastic results."
artifact_hash: 7ba9201f0f49d9384a35f3eca07d4fd8d448c0da222a8a4e9472044b7e857c18
artifact_path: projects/PROJ-781-memgui-agent-an-end-to-end-long-horizon/paper/metadata.json
backend: dartmouth
feedback: ''
github_authenticated: false
model_name: qwen.qwen3.5-122b
prompt_version: 1.1.0
reviewed_at: '2026-07-03T18:52:41.989576Z'
reviewer_kind: llm
reviewer_name: paper_reviewer_overreach
score: 0.0
verdict: minor_revision
---

The paper makes several claims that extend beyond the immediate evidence provided in the text, particularly regarding the exclusivity of the proposed solution's effectiveness and the universality of the identified failure modes.

First, the conclusion (Sec 6) and abstract assert that MemGUI-8B-SFT achieves the "best open-data 8B performance." While the authors provide a strong comparison against the Qwen3-VL-8B baseline and other end-to-end models, the term "best" is a superlative that requires a comprehensive sweep of the current open-weight landscape. The paper does not explicitly benchmark against other fine-tuned 8B models (e.g., specific community fine-tunes of Llama-3.2-Vision or other recent open-source VLMs) that might exist. Without this broader comparison, the claim of being the absolute "best" is an overreach; it should be qualified as "competitive" or "state-of-the-art among the specific baselines tested."

Second, the Introduction (Sec 1) presents a causal narrative that the degradation in long-horizon tasks is "attributed to passive ReAct-style prompting, which causes prompt explosion." This phrasing implies that context management is the *primary* or *sole* bottleneck. However, the ablation studies (Table 2) show that while ConAct helps, the baseline 235B model still struggles significantly on hard tasks (34.2% P@1). The paper does not sufficiently rule out alternative explanations for the remaining failures, such as limitations in visual grounding over long sequences, action space complexity, or the inherent difficulty of the tasks themselves. Attributing the problem almost exclusively to "prompt explosion" oversimplifies the problem space.

Finally, the error analysis in Figure 4 caption states that "Full ConAct reduces total failures by 41% (99→58)." Presenting this as a precise integer reduction without reporting variance, standard deviation, or statistical significance (e.g., p-values from a t-test or bootstrap confidence intervals) is scientifically risky. In stochastic agent evaluations, a single run's count can fluctuate. Claiming a definitive 41% reduction without error bars or multiple-seed reporting suggests a level of certainty that the data does not support. The authors should either provide the statistical backing for this specific number or rephrase it to reflect the observed trend (e.g., "reduced failures by approximately 40% across our evaluation").
