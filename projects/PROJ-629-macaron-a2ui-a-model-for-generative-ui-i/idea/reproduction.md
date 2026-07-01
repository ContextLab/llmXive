# Reproduce & validate: Macaron-A2UI: A Model for Generative UI in Personal Agents

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/   (clone of https://github.com/MindLab-Research/Macaron-A2UI-Bench)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Macaron-A2UI: A Model for Generative UI in Personal Agents

**Abstract:** As personal agents evolve to handle complex, user-centric tasks, static plain-text chat is rapidly becoming a bottleneck. Generative UI emerges as the necessary new interface layer, dynamically synthesizing the right controls, options, and state from the interaction context in real time. We present Macaron-A2UI, a model for Generative UI in personal agents. Our goal is to move beyond text-only interaction by enabling agents to generate natural language together with lightweight, executable UI actions for information collection, preference refinement, confirmation, and multi-goal organization. We build a large-scale Generative UI corpus from heterogeneous dialogue sources, introduce A2UI-Bench for controlled evaluation, and train 30B, 235B and 754B models with parameter-efficient LoRA-based supervised fine-tuning followed by reward-driven reinforcement learning. The best Macaron-A2UI model reaches 75.6 overall on A2UI-Bench without explicit schema hints, surpassing the strongest full-schema frontier baseline. We release the models, benchmark, and evaluation protocol to support future work on Generative UI for personal agents.

## Shipped code — file tree (`projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/`)

```
.env.example
.gitignore
README.md
UPSTREAM.md
data/eval_300/annomi_tasks.json
data/eval_300/esconv_tasks.json
data/eval_300/manifest.json
data/eval_300/multiwoz_tasks.json
data/eval_300/sgd_tasks.json
data/source/annomi_tasks.json
data/source/esconv_tasks.json
data/source/multiwoz_tasks.json
data/source/sgd_tasks.json
evaluate_api_model.py
prepare_eval_split.py
prompts/__init__.py
prompts/generation_minimal.txt
prompts/l2_judge.txt
prompts/l3_judge.txt
render/A2UI_RENDER_MECHANISM.md
render/README.md
render/index.html
render/package-lock.json
render/package.json
render/public/showcase/qwen-235b-rl/data.json
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_00b81ae7.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_0a2f41ec.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_0c68cc84.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_3e6654fa.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_46de6e7f.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_4893d7f4.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_4bf30f18.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_51a28490.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_656b51c6.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_6d042c61.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_7b4db2b4.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_7c895e90.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_b593cbc2.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_beb0e11e.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_c52408b4.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_d08d7bd9.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_d2d818fb.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_d454226f.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_d6183997.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_annomi_d68f15ed.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_077b93a4.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_0bd89198.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_0bee8edd.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_193371ce.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_33eb51e6.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_404065da.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_57087aef.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_5bd44e81.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_73b3af62.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_7c66d172.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_7d663ed3.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_8f83dfab.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_a50a869e.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_b8f986c2.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_c083c3d1.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_e21a6d9a.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_e76fad46.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_esconv_ecbb9574.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_0fb5769d.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_2c7e2be8.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_337aa64f.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_6186b816.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_70b48c8c.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_761bd410.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_7aff55cd.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_7f807a6b.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_860caa07.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_86a675b7.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_904a05d2.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_93c0accf.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_94de9df1.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_992c060a.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_9d1330b6.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_ac673771.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_ccc516e6.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_d75c5c58.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_df6b99ea.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_e99752bf.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_multiwoz_f98c7ca3.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_0142b146.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_08b87053.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_0d2536d8.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_109f1732.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_13e52bc5.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_15b43b85.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_1627beef.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_1c1ad8d1.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_380caba6.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_3e0bc565.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_7d94fdce.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_7deb6b21.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_907f9070.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_9919e9ec.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_a13869f0.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_a4ca4345.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_a8f1b298.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_aa822927.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_aacd150d.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_b48b2e5b.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_d0d2d268.png
render/public/showcase/qwen-235b-rl/images/compare/atomic_sgd_d19f1462.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_07c27061__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_07c27061__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_0e33d68e__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_0e33d68e__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_0e33d68e__step04.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_29b11ef9__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_29b11ef9__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_2f868e5d__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_2f868e5d__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_3b3579bc__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_3b3579bc__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_3b3579bc__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_3b3579bc__step04.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_3c6a67cc__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_3c6a67cc__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_3c6a67cc__step04.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_3eea64ca__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_3eea64ca__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_449e668f__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_449e668f__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_5289711a__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_5289711a__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_71b4203c__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_71b4203c__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_76ff2e91__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_76ff2e91__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_79b9046f__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_79b9046f__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_79b9046f__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_7d6e1b63__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_7d6e1b63__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_873035b6__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_873035b6__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_873035b6__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_9c7157c0__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_adcee1ba__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_adcee1ba__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_c957ea97__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_c957ea97__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_c957ea97__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_db7ac937__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_dc6be520__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_dc6be520__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_dc6be520__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_dc6be520__step04.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_e40f82e7__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_e40f82e7__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_e43fd2c2__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_e43fd2c2__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_e6525298__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_eb1a69bc__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_eb1a69bc__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_eb1a69bc__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_eda2d028__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_eda2d028__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_eda2d028__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_annomi_f004d76b__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_0ddeeeac__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_0e86e8a3__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_0e86e8a3__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_0e86e8a3__step04.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_201a0ee7__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_201a0ee7__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_201a0ee7__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_201a0ee7__step04.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_23a70952__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_23a70952__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_23a70952__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_23a70952__step04.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_3928d8d8__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_3928d8d8__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_3928d8d8__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_3ee7772a__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_3ee7772a__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_41073737__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_41073737__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_51cbafe3__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_51cbafe3__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_51cbafe3__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_5bddd753__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_5bddd753__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_5e3fab1d__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_5e3fab1d__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_6d677bfd__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_6d677bfd__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_6d677bfd__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_6ef190a2__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_6ef190a2__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_6ef190a2__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_6ef190a2__step04.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_70201fc1__step01.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_70201fc1__step02.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_70201fc1__step03.png
render/public/showcase/qwen-235b-rl/images/compare/depth_esconv_70201fc1__step04.png
… (truncated)
```

## Detected entry points

- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/evaluate_api_model.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/prepare_eval_split.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/render_check.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/visual_compare_models.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/visual_eval.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/a2ui_prompt.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/a2ui_schema.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/a2ui_schema_registry.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/ui_examples.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/a2ui_lint/component_schema.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/a2ui_lint/context.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/a2ui_lint/diagnostics.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/a2ui_lint/formatters.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/a2ui_lint/level1_structural.py`
- `projects/PROJ-629-macaron-a2ui-a-model-for-generative-ui-i/external/Macaron-A2UI-Bench/vendor/a2ui_demo/server/a2ui_lint/level2_references.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Macaron-A2UI-Bench` — not re-implementing it.
