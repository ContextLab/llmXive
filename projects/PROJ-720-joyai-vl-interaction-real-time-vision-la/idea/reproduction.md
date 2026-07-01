# Reproduce & validate: JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/   (clone of https://github.com/jd-opensource/JoyAI-VL-Interaction)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** JoyAI-VL-Interaction: Real-Time Vision-Language Interaction Intelligence

**Abstract:** Many moments in the real world do not wait for a user to ask. A fire starts on a security monitor, an expression flickers across a video call, or a product a viewer wants flashes by in a livestream. Yet today's large models remain mostly turn-based by design: they answer only when addressed, and even video-call apps that appear interactive still operate as question-answer systems, reacting only when polled or prompted. We argue for a different paradigm: a model that is present in the world like a person. It continuously watches what is happening now, decides on its own whether to speak or stay silent, interacts in real time, and delegates to a background model when the problem is hard. To advance interaction models and their adoption across domains, we make two fully open-sourced contributions. First, we release JoyAI-VL-Interaction, an 8B-scale, vision-first VL-interaction model. The model makes the response decision internally, choosing each second to stay silent, respond, or delegate to a background model, and it excels at vision-triggered responsiveness and time awareness. We pair it with a transferable training recipe, from which capabilities we never trained for emerge, such as guiding a shopper through changing app screens or improvising a lecture from a slide deck. Second, we release a complete, deployable system built around that model. The system streams any ongoing video into the model, making it genuinely present in the world. All other components are pluggable, including ASR/TTS modules, memory, visualization UI, and a background brain that can connect to any API or agent. Across six real-world scenarios, human raters prefer JoyAI-VL-Interaction over the in-app video-call assistants of Doubao and Gemini by a wide margin. To our knowledge, this is the first open, vision-driven interaction model released together with its training recipe, data, and complete deployable system.

## Shipped code — file tree (`projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/`)

```
.gitignore
JoyAI-VL-Interaction-Reportv1.pdf
LICENSE
README.md
README.zh-CN.md
datasets/README.md
datasets/convert_data.py
doc/.gitkeep
doc/architecture.md
doc/architecture.zh-CN.md
doc/getting_started.md
doc/getting_started.zh-CN.md
doc/rtsp_streaming.md
doc/rtsp_streaming.zh-CN.md
doc/troubleshooting.md
doc/troubleshooting.zh-CN.md
img/.gitkeep
img/banner.svg
img/capability-grid.svg
img/joyvl-system-architecture.png
img/overview.png
img/readme-hero.gif
install/README.md
install/README.zh-CN.md
install/constraints.txt
install/download-models.sh
install/install-audio-runtime.sh
install/install.sh
install/pyproject.asr.toml
install/pyproject.background-agent.toml
install/pyproject.toml
install/pyproject.tts.toml
install/tests/run_real_env_tests.sh
install/tests/verify_real_env.py
services/asr/README.md
services/asr/README.zh-CN.md
services/asr/asr_adapter.py
services/asr/pyproject.toml
services/asr/scripts/run-adapter.sh
services/asr/scripts/run-model.sh
services/asr/scripts/run.sh
services/background-agent/README.md
services/background-agent/README.zh-CN.md
services/background-agent/background-agent.env
services/background-agent/codex-home/.gitkeep
services/background-agent/codex_api/__init__.py
services/background-agent/codex_api/main.py
services/background-agent/pyproject.toml
services/background-agent/scripts/run.sh
services/background-agent/uv.lock
services/scripts/run.sh
services/scripts/stop.sh
services/tts/README.md
services/tts/README.zh-CN.md
services/tts/config/qwen3_tts_lowmem.yaml
services/tts/pyproject.toml
services/tts/scripts/run-adapter.sh
services/tts/scripts/run-model.sh
services/tts/scripts/run.sh
services/tts/tts_adapter.py
services/webinfer/README.md
services/webinfer/README.zh-CN.md
services/webinfer/live_adapter.py
services/webinfer/memory_summarizer.py
services/webinfer/scripts/run.sh
services/webinfer/scripts/start_adapter.sh
services/webinfer/scripts/start_all_models.sh
services/webinfer/scripts/start_model.sh
services/webinfer/scripts/start_summary_model.sh
services/webinfer/scripts/stop.sh
services/webui/README.md
services/webui/README.zh-CN.md
services/webui/pyproject.toml
services/webui/scripts/generate_cert.sh
services/webui/scripts/start_server.sh
services/webui/scripts/stop_server.sh
services/webui/src/joy_interaction_webui/__init__.py
services/webui/src/joy_interaction_webui/asr.py
services/webui/src/joy_interaction_webui/background_model.py
services/webui/src/joy_interaction_webui/local_file_server.py
services/webui/src/joy_interaction_webui/rtsp_track.py
services/webui/src/joy_interaction_webui/server.py
services/webui/src/joy_interaction_webui/static/favicon/apple-touch-icon.png
services/webui/src/joy_interaction_webui/static/favicon/favicon-96x96.png
services/webui/src/joy_interaction_webui/static/favicon/favicon.ico
services/webui/src/joy_interaction_webui/static/favicon/favicon.svg
services/webui/src/joy_interaction_webui/static/favicon/site.webmanifest
services/webui/src/joy_interaction_webui/static/favicon/web-app-manifest-192x192.png
services/webui/src/joy_interaction_webui/static/favicon/web-app-manifest-512x512.png
services/webui/src/joy_interaction_webui/static/images/.gitkeep
services/webui/src/joy_interaction_webui/static/images/README.md
services/webui/src/joy_interaction_webui/static/images/README.zh-CN.md
services/webui/src/joy_interaction_webui/static/images/dgx-spark_256px.png
services/webui/src/joy_interaction_webui/static/images/jetson-agx-orin-devkit_256px.png
services/webui/src/joy_interaction_webui/static/images/jetson-agx-thor-devkit_256px.png
services/webui/src/joy_interaction_webui/static/images/jetson-orin-nano-devkit_217px.png
services/webui/src/joy_interaction_webui/static/images/m48-gpu-ampere-256px-grn.png
services/webui/src/joy_interaction_webui/static/images/m48-gpu-chip-text-256px-grn.png
services/webui/src/joy_interaction_webui/static/images/m48-laptop-256px-blk.png
services/webui/src/joy_interaction_webui/static/images/m48-laptop-256px-wht.png
services/webui/src/joy_interaction_webui/static/images/m48-workstation-256px-blk.png
services/webui/src/joy_interaction_webui/static/images/m48-workstation-256px-wht.png
services/webui/src/joy_interaction_webui/static/images/simple-logo.svg
services/webui/src/joy_interaction_webui/static/index.html
services/webui/src/joy_interaction_webui/tts.py
services/webui/src/joy_interaction_webui/video_processor.py
services/webui/src/joy_interaction_webui/vlm_service.py
```

## Detected entry points

- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/background-agent/codex_api/main.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/datasets/convert_data.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/install/tests/verify_real_env.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/asr/asr_adapter.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/tts/tts_adapter.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webinfer/live_adapter.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webinfer/memory_summarizer.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webui/src/joy_interaction_webui/asr.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webui/src/joy_interaction_webui/background_model.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webui/src/joy_interaction_webui/local_file_server.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webui/src/joy_interaction_webui/rtsp_track.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webui/src/joy_interaction_webui/server.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webui/src/joy_interaction_webui/tts.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webui/src/joy_interaction_webui/video_processor.py`
- `projects/PROJ-720-joyai-vl-interaction-real-time-vision-la/external/JoyAI-VL-Interaction/services/webui/src/joy_interaction_webui/vlm_service.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `JoyAI-VL-Interaction` — not re-implementing it.
