# Reproduce & validate: Data Journalist Agent: Transforming Data into Verifiable Multimodal Stories

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/   (clone of https://github.com/QinghongLin/data2story-skill)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Data Journalist Agent: Transforming Data into Verifiable Multimodal Stories

**Abstract:** Data tells stories that shape society; the data journalist's job is to turn raw information into stories non-experts can trust. A high-quality news feature takes a newsroom team weeks: hunting for context, running statistics, choosing an angle, and designing visuals. Recent agents handle individual steps well: data-science agents close the analysis loop, while design agents synthesize beautiful websites. But can an agent serve as a data journalist end to end? We introduce Data Journalist Agent (Data2Story), a multi-agent framework that orchestrates specialized roles into a single virtual newsroom. Data2Story contributes two innovations. (i) Claims are evidence-grounded: an Inspector links every number, angle, and asset back to data, code, or an external reference. (ii) Articles are multimodally generative: rather than defaulting to plain text and static charts, Data2Story reasons about what readers will want to see, then deploys multimodal tools, such as interactive maps for geography and audio for music. We evaluate Data2Story on 18 articles, each paired with the originally published expert piece, along four axes: (a) human-agent angle coverage; (b) rubric evaluation with 53 participants across five dimensions; (c) computer-use agents as judges, a cost-saving proxy for how readers navigate interactive articles; and (d) verifiability, where a coding verifier re-executes statements against the data and checks claims against references. Data2Story produces competitive, evidence-traceable multimedia stories, with particular strength in transparency and auditability. Human articles retain an edge in editorial angle, creative design, and presentation. We position Data2Story as a collaborator for journalists, enabling more evidence-based, transparent, and verifiable reporting. Code and demos are available at https://data2story.github.io.

## Shipped code — file tree (`projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/`)

```
.gitignore
LICENSE
README.md
assets/gallery.png
assets/logo.png
assets/pipeline.png
assets/teaser.png
pro/.gitignore
pro/README.md
pro/data/.gitkeep
pro/package-lock.json
pro/package.json
pro/skills/data2story-pro/SKILL.md
pro/skills/data2story-pro/TEAMS.md
pro/skills/data2story-pro/analyst/SKILL.md
pro/skills/data2story-pro/analyst/references/data_table_rules.json
pro/skills/data2story-pro/analyst/references/field_rules.json
pro/skills/data2story-pro/analyst/references/paper_mode.json
pro/skills/data2story-pro/analyst/references/schema.json
pro/skills/data2story-pro/auditor/SKILL.md
pro/skills/data2story-pro/auditor/references/checks.json
pro/skills/data2story-pro/auditor/references/fix_patterns.json
pro/skills/data2story-pro/auditor/references/flagship_contract.json
pro/skills/data2story-pro/auditor/references/report_types.json
pro/skills/data2story-pro/auditor/scripts/playtest_drive.js
pro/skills/data2story-pro/auditor/scripts/render_capture.js
pro/skills/data2story-pro/cinematographer/SKILL.md
pro/skills/data2story-pro/cinematographer/references/cinematic_recipes.json
pro/skills/data2story-pro/cinematographer/references/example_cinematic_scroll.html
pro/skills/data2story-pro/cinematographer/references/schema.json
pro/skills/data2story-pro/copywriter/SKILL.md
pro/skills/data2story-pro/copywriter/references/schema.json
pro/skills/data2story-pro/critic/SKILL.md
pro/skills/data2story-pro/critic/references/rubric.json
pro/skills/data2story-pro/designer/SKILL.md
pro/skills/data2story-pro/designer/references/audio_rules.json
pro/skills/data2story-pro/designer/references/diversity_rules.json
pro/skills/data2story-pro/designer/references/field_rules.json
pro/skills/data2story-pro/designer/references/schema.json
pro/skills/data2story-pro/designer/references/tools.json
pro/skills/data2story-pro/designer/references/video_pipeline.json
pro/skills/data2story-pro/designer/references/visual_modes.json
pro/skills/data2story-pro/designer/scripts/openrouter-embeddings/SKILL.md
pro/skills/data2story-pro/designer/scripts/openrouter-embeddings/config.json
pro/skills/data2story-pro/designer/scripts/openrouter-embeddings/scripts/embed.py
pro/skills/data2story-pro/designer/scripts/openrouter-image2video/SKILL.md
pro/skills/data2story-pro/designer/scripts/openrouter-image2video/config.json
pro/skills/data2story-pro/designer/scripts/openrouter-image2video/scripts/generate_video_from_image.py
pro/skills/data2story-pro/designer/scripts/openrouter-text2image/SKILL.md
pro/skills/data2story-pro/designer/scripts/openrouter-text2image/config.json
pro/skills/data2story-pro/designer/scripts/openrouter-text2image/scripts/generate_image.py
pro/skills/data2story-pro/designer/scripts/openrouter-text2music/SKILL.md
pro/skills/data2story-pro/designer/scripts/openrouter-text2music/config.json
pro/skills/data2story-pro/designer/scripts/openrouter-text2music/scripts/generate_music.py
pro/skills/data2story-pro/designer/scripts/openrouter-text2video/SKILL.md
pro/skills/data2story-pro/designer/scripts/openrouter-text2video/config.json
pro/skills/data2story-pro/designer/scripts/openrouter-text2video/scripts/generate_video.py
pro/skills/data2story-pro/designer/scripts/optimize_assets.py
pro/skills/data2story-pro/detective/SKILL.md
pro/skills/data2story-pro/detective/examples/README.md
pro/skills/data2story-pro/detective/examples/fetch_hle_images.py
pro/skills/data2story-pro/detective/examples/fetch_venue_weather.py
pro/skills/data2story-pro/detective/references/categories.json
pro/skills/data2story-pro/detective/references/field_rules.json
pro/skills/data2story-pro/detective/references/instance_verification.json
pro/skills/data2story-pro/detective/references/paper_mode.json
pro/skills/data2story-pro/detective/references/schema.json
pro/skills/data2story-pro/detective/scripts/fetch_flags.py
pro/skills/data2story-pro/detective/scripts/fetch_images.py
pro/skills/data2story-pro/detective/scripts/fetch_logos.py
pro/skills/data2story-pro/detective/scripts/fetch_openverse.py
pro/skills/data2story-pro/editor/SKILL.md
pro/skills/data2story-pro/editor/references/editor_md_template.json
pro/skills/data2story-pro/editor/references/field_rules.json
pro/skills/data2story-pro/editor/references/media_hints.json
pro/skills/data2story-pro/editor/references/narrative_angles.json
pro/skills/data2story-pro/editor/references/schema.json
pro/skills/data2story-pro/evals/README.md
pro/skills/data2story-pro/evals/fixtures/06_resolution_gate_green/audit/playtest_report.json
pro/skills/data2story-pro/evals/fixtures/06_resolution_gate_green/auditor.json
pro/skills/data2story-pro/evals/fixtures/06_resolution_gate_green/detective.json
pro/skills/data2story-pro/evals/fixtures/06_resolution_gate_red/audit/playtest_report.json
pro/skills/data2story-pro/evals/fixtures/06_resolution_gate_red/auditor.json
pro/skills/data2story-pro/evals/fixtures/06_resolution_gate_red/detective.json
pro/skills/data2story-pro/evals/fixtures/07_asset_hygiene/.gitignore
pro/skills/data2story-pro/evals/fixtures/07_asset_hygiene/assets/.gitkeep
pro/skills/data2story-pro/evals/fixtures/07_asset_hygiene/detective.json
pro/skills/data2story-pro/evals/fixtures/07_asset_hygiene/index.html
pro/skills/data2story-pro/evals/reports/.gitkeep
pro/skills/data2story-pro/evals/scenarios/01_meteorite_flagship.md
pro/skills/data2story-pro/evals/scenarios/02_abstract_dataset.md
pro/skills/data2story-pro/evals/scenarios/03_regression_gaps.md
pro/skills/data2story-pro/evals/scenarios/04_new_rules_fire.md
pro/skills/data2story-pro/evals/scenarios/05_titling_fires.md
pro/skills/data2story-pro/evals/scenarios/06_resolution_gate.md
pro/skills/data2story-pro/evals/scenarios/07_asset_hygiene.md
pro/skills/data2story-pro/evals/scripts/recurrence_report.py
pro/skills/data2story-pro/evals/scripts/run_evals.py
pro/skills/data2story-pro/hero/SKILL.md
pro/skills/data2story-pro/hero/references/hero_recipes.json
pro/skills/data2story-pro/hero/references/schema.json
pro/skills/data2story-pro/ideation/SKILL.md
pro/skills/data2story-pro/ideation/references/schema.json
pro/skills/data2story-pro/ideation/references/sparring_brief.md
pro/skills/data2story-pro/imagineer/SKILL.md
pro/skills/data2story-pro/imagineer/references/schema.json
pro/skills/data2story-pro/inspector/SKILL.md
pro/skills/data2story-pro/inspector/references/cell_registry.schema.json
pro/skills/data2story-pro/inspector/references/examples/cell_registry.example.json
pro/skills/data2story-pro/inspector/references/examples/run_cells.example.json
pro/skills/data2story-pro/inspector/references/examples/verify_map.example.json
pro/skills/data2story-pro/inspector/references/inspector_panel_internals.json
pro/skills/data2story-pro/inspector/references/inspector_panel_reference.html
pro/skills/data2story-pro/inspector/references/inspector_schema.json
pro/skills/data2story-pro/inspector/references/notebook_template.ipynb
pro/skills/data2story-pro/inspector/references/reproducible_notebook.md
pro/skills/data2story-pro/inspector/references/run_cells.schema.json
pro/skills/data2story-pro/inspector/references/verify_map.schema.json
pro/skills/data2story-pro/inspector/scripts/generate_viewer.py
pro/skills/data2story-pro/inspector/scripts/relocate_unreferenced.py
pro/skills/data2story-pro/inspector/scripts/validate.py
pro/skills/data2story-pro/inspector/scripts/verify.py
pro/skills/data2story-pro/interaction/SKILL.md
pro/skills/data2story-pro/interaction/references/interaction_recipes.json
pro/skills/data2story-pro/programmer/SKILL.md
pro/skills/data2story-pro/programmer/references/component_implementations.json
pro/skills/data2story-pro/programmer/references/data_resolution.json
pro/skills/data2story-pro/programmer/references/layout_rules.json
pro/skills/data2story-pro/programmer/references/traceability.json
pro/skills/data2story-pro/references/topic_profile.json
pro/skills/data2story-pro/scout/SKILL.md
pro/skills/data2story-pro/scout/references/license_allowlist.json
pro/skills/data2story-pro/scout/references/manifest_schema.json
pro/skills/data2story-pro/scout/references/media_verification.json
pro/skills/data2story-pro/scout/references/schema.json
pro/skills/data2story-pro/scout/scripts/fetch_live_status.py
pro/skills/data2story-pro/scout/scripts/fetch_music.py
pro/skills/data2story-pro/scout/scripts/fetch_stock.py
pro/skills/dataviz-craft/SKILL.md
pro/skills/dataviz-craft/references/annotation_layers.json
pro/skills/dataviz-craft/references/axis_label_polish.json
pro/skills/dataviz-craft/references/chart_chooser.json
pro/skills/dataviz-craft/references/d3_fallback_recipes.json
pro/skills/dataviz-craft/references/encoding_craft.json
pro/skills/dataviz-craft/references/vega_recipes.json
pro/skills/find-data/SKILL.md
pro/skills/find-data/references/completeness_gates.md
pro/skills/find-data/references/examples/good_economist.md
pro/skills/find-data/references/examples/good_theme.md
pro/skills/find-data/references/input_mode_dispatch.md
pro/skills/find-data/tools/README_template.md
pro/skills/find-data/tools/audit.py
pro/skills/find-data/tools/browse_local.py
pro/skills/find-data/tools/dip_query.py
pro/skills/find-data/tools/fetch.py
pro/skills/find-data/tools/selftest.py
pro/skills/frontend-design/SKILL.md
pro/skills/frontend-design/references/abstract_excellence.json
pro/skills/frontend-design/references/components.json
pro/skills/frontend-design/references/design_tokens.json
pro/skills/frontend-design/references/exemplars/cinematic_flagship.md
pro/skills/frontend-design/references/exemplars/titling_captioning.md
pro/skills/frontend-design/references/finish.json
pro/skills/frontend-design/references/interaction.json
pro/skills/frontend-design/references/interaction_playbook.json
pro/skills/frontend-design/references/layout.json
pro/skills/frontend-design/references/media_presentation.json
pro/skills/frontend-design/references/motion.json
pro/skills/frontend-design/references/pitfalls.json
pro/skills/frontend-design/references/quality_rubric.json
pro/skills/frontend-design/references/themes.json
pro/skills/frontend-design/references/typography.json
pro/skills/sparring-partner/SKILL.md
pro/skills/sparring-partner/references/checklists.md
pro/skills/sparring-partner/references/methodologies.md
pro/skills/sparring-partner/references/profile.template.md
pro/skills/sparring-partner/references/question-bank.md
skills/data2story/SKILL.md
skills/data2story/analyst/SKILL.md
skills/data2story/analyst/references/data_table_rules.json
skills/data2story/analyst/references/field_rules.json
skills/data2story/analyst/references/paper_mode.json
skills/data2story/analyst/references/schema.json
skills/data2story/auditor/SKILL.md
skills/data2story/auditor/references/checks.json
skills/data2story/auditor/references/fix_patterns.json
skills/data2story/auditor/references/report_types.json
skills/data2story/designer/SKILL.md
skills/data2story/designer/references/audio_rules.json
skills/data2story/designer/references/diversity_rules.json
skills/data2story/designer/references/field_rules.json
skills/data2story/designer/references/schema.json
skills/data2story/designer/references/tools.json
skills/data2story/designer/references/visual_modes.json
skills/data2story/designer/scripts/openrouter-embeddings/SKILL.md
skills/data2story/designer/scripts/openrouter-embeddings/config.json
skills/data2story/designer/scripts/openrouter-embeddings/scripts/embed.py
skills/data2story/designer/scripts/openrouter-image2video/SKILL.md
skills/data2story/designer/scripts/openrouter-image2video/config.json
skills/data2story/designer/scripts/openrouter-image2video/scripts/generate_video_from_image.py
… (truncated)
```

## Detected entry points

- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/pro/skills/find-data/tools/audit.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/pro/skills/find-data/tools/browse_local.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/pro/skills/find-data/tools/dip_query.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/pro/skills/find-data/tools/fetch.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/pro/skills/find-data/tools/selftest.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/skills/data2story/detective/scripts/fetch_flags.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/skills/data2story/detective/scripts/fetch_hle_images.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/skills/data2story/detective/scripts/fetch_images.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/skills/data2story/detective/scripts/fetch_logos.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/skills/data2story/detective/scripts/fetch_venue_weather.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/skills/data2story/inspector/scripts/generate_viewer.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/skills/data2story/inspector/scripts/verify.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/pro/skills/data2story-pro/designer/scripts/optimize_assets.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/pro/skills/data2story-pro/detective/examples/fetch_hle_images.py`
- `projects/PROJ-719-data-journalist-agent-transforming-data/external/data2story-skill/pro/skills/data2story-pro/detective/examples/fetch_venue_weather.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `data2story-skill` — not re-implementing it.
