# Reproduce & validate: Crafter: A Multi-Agent Harness for Editable Scientific Figure Generation from Diverse Inputs

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/   (clone of https://github.com/HaozheZhao/Crafter)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** Crafter: A Multi-Agent Harness for Editable Scientific Figure Generation from Diverse Inputs

**Abstract:** Scientific figures are among the most effective means of communicating complex research ideas, yet producing publication-quality illustrations remains one of the most labor-intensive parts of paper preparation. Existing automated systems each target a single figure type under text-only input, leaving the diversity of types and conditions researchers actually use unaddressed; their raster outputs further cannot be locally revised. Because scientific figures are structured compositions of discrete semantic components, the localized errors generators produce on such layouts demand not a stronger backbone but a harness. We instantiate this harness in two complementary systems: Crafter, a multi-agent harness for figure generation that generalizes across figure types and input conditions without architectural changes, and CraftEditor, which applies the same pattern to convert raster outputs into editable SVGs. Moreover, we introduce CraftBench, a benchmark spanning three figure types and four input conditions with human quality annotation. Experiments show that Crafter substantially outperforms both standalone generators and the agentic baseline on PaperBanana-Bench and CraftBench, with ablations confirming each component's independent contribution; CraftEditor faithfully converts outputs into editable SVGs that surpass all baselines. Our code and benchmark are available at https://github.com/HaozheZhao/Crafter.

## Shipped code — file tree (`projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/`)

```
.env.example
.gitignore
LICENSE
README.md
assets/craftbench_distribution.png
assets/craftbench_examples.png
assets/crafter_architecture.png
assets/editable_demo.png
assets/editable_output_pipeline.png
assets/editor_qualitative.png
configs/default.yaml
convert.py
craftbench/LICENSE
craftbench/README.md
craftbench/evaluation/__init__.py
craftbench/evaluation/api.py
craftbench/evaluation/images.py
craftbench/evaluation/judge.py
craftbench/evaluation/requirements.txt
craftbench/evaluation/run_eval.py
craftbench/images/gt/craftbench-0001.png
craftbench/images/gt/craftbench-0004.png
craftbench/images/gt/craftbench-0026.png
craftbench/images/inputs/craftbench-0004.png
craftbench/images/inputs/craftbench-0026.png
craftbench/manifest.json
craftbench/samples/craftbench-0001.json
craftbench/samples/craftbench-0004.json
craftbench/samples/craftbench-0026.json
crafter/__init__.py
crafter/cli.py
crafter/editor/__init__.py
crafter/editor/_env.py
crafter/editor/approach/__init__.py
crafter/editor/approach/af_supplemental_detect.py
crafter/editor/approach/agent_prompt_writer.py
crafter/editor/approach/classify_vector_codeable.py
crafter/editor/approach/extract_icons.py
crafter/editor/approach/hallucination_guard.py
crafter/editor/approach/harness/__init__.py
crafter/editor/approach/harness/build_marked.py
crafter/editor/approach/harness/checkers/__init__.py
crafter/editor/approach/harness/checkers/arrow.py
crafter/editor/approach/harness/checkers/missing_text.py
crafter/editor/approach/harness/checkers/overlap.py
crafter/editor/approach/harness/checkers/paddle_text.py
crafter/editor/approach/harness/checkers/position.py
crafter/editor/approach/harness/checkers/structural.py
crafter/editor/approach/harness/checkers/style.py
crafter/editor/approach/harness/checkers/text_overflow.py
crafter/editor/approach/harness/checkers/text_recovery.py
crafter/editor/approach/harness/checkers/text_size.py
crafter/editor/approach/harness/compose.py
crafter/editor/approach/harness/judge.py
crafter/editor/approach/harness/prompt_evolver.py
crafter/editor/approach/harness/raster_cleanup.py
crafter/editor/approach/harness/refine.py
crafter/editor/approach/icon_taxonomy.py
crafter/editor/approach/iter_svg_fix.py
crafter/editor/approach/post_classify_rules.py
crafter/editor/approach/prompt_selector.py
crafter/editor/approach/stage_a_harness.py
crafter/editor/approach/style_analyzer.py
crafter/editor/approach/test_text_referring_grounding.py
crafter/editor/caption_sam3_referring/__init__.py
crafter/editor/caption_sam3_referring/build_referring_pairs.py
crafter/editor/cli.py
crafter/editor/composition.py
crafter/editor/config.py
crafter/editor/extraction.py
crafter/editor/pipeline.py
crafter/editor/processing.py
crafter/editor/raster_to_svg/__init__.py
crafter/editor/raster_to_svg/agents/__init__.py
crafter/editor/raster_to_svg/agents/judge.py
crafter/editor/raster_to_svg/agents/paddle_text_extractor.py
crafter/editor/raster_to_svg/config.py
crafter/editor/raster_to_svg/model_router.py
crafter/editor/raster_to_svg/schema.py
crafter/editor/raster_to_svg/skill.md
crafter/editor/raster_to_svg/tools/__init__.py
crafter/editor/raster_to_svg/tools/sam3_client.py
crafter/generation/__init__.py
crafter/generation/cli.py
crafter/generation/core/__init__.py
crafter/generation/core/config.py
crafter/generation/craft/__init__.py
crafter/generation/craft/agent_judge.py
crafter/generation/craft/agent_registry.py
crafter/generation/craft/backends/__init__.py
crafter/generation/craft/backends/base.py
crafter/generation/craft/backends/chat_image.py
crafter/generation/craft/backends/gpt_image.py
crafter/generation/craft/critic.py
crafter/generation/craft/figure_spec.py
crafter/generation/craft/image_generator.py
crafter/generation/craft/paper_reader.py
crafter/generation/craft/phases/__init__.py
crafter/generation/craft/phases/generation.py
crafter/generation/craft/phases/polish.py
crafter/generation/craft/phases/reading.py
crafter/generation/craft/phases/refinement.py
crafter/generation/craft/phases/selection.py
crafter/generation/craft/prompt_refiner.py
crafter/generation/craft/reference_search.py
crafter/generation/craft/role_planner.py
crafter/generation/craft/session.py
crafter/generation/craft/sketch_analyzer.py
crafter/generation/craft/skill_evolver.py
crafter/generation/craft/skill_manager.py
crafter/generation/craft/skills/critic.md
crafter/generation/craft/skills/drawer.md
crafter/generation/craft/skills/drawer_poster.md
crafter/generation/craft/skills/paper_reader.md
crafter/generation/craft/skills/planner.md
crafter/generation/craft/skills/retriever.md
crafter/generation/craft/skills/stylist.md
crafter/generation/craft/svg_generator.py
crafter/generation/craft/text_critic.py
crafter/generation/craft/venue_styles.py
crafter/generation/craft/visual_grounder.py
crafter/generation/craft/visual_metaphor_translator.py
crafter/shared/__init__.py
crafter/shared/config.py
crafter/shared/judge.py
crafter/shared/model_router.py
crafter/shared/providers/__init__.py
crafter/shared/providers/_config.py
crafter/shared/providers/base.py
crafter/shared/providers/image_edit.py
crafter/shared/providers/llm.py
crafter/shared/providers/rmbg.py
crafter/shared/providers/sam3.py
crafter/shared/sam3_client.py
demo.py
examples/sample_figure.png
examples/sample_inpaint_input.png
examples/sample_inpaint_paper.txt
examples/sample_instruction_inpaint.txt
examples/sample_instruction_t2i.txt
examples/sample_paper.txt
inference.py
pyproject.toml
requirements.txt
scripts/sam3_server.py
```

## Detected entry points

- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/demo.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/convert.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/inference.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/crafter/cli.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/scripts/sam3_server.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/craftbench/evaluation/api.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/craftbench/evaluation/images.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/craftbench/evaluation/judge.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/craftbench/evaluation/run_eval.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/crafter/editor/cli.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/crafter/editor/composition.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/crafter/editor/config.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/crafter/editor/extraction.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/crafter/editor/pipeline.py`
- `projects/PROJ-656-crafter-a-multi-agent-harness-for-editab/external/Crafter/crafter/editor/processing.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `Crafter` — not re-implementing it.
