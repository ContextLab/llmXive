# Reproduce & validate: MobileForge: Annotation-Free Adaptation for Mobile GUI Agents with Hierarchical Feedback-Guided Policy Optimization

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/   (clone of https://github.com/kwai/MobileForge)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** MobileForge: Annotation-Free Adaptation for Mobile GUI Agents with Hierarchical Feedback-Guided Policy Optimization

**Abstract:** MLLM-based mobile GUI agents have made substantial progress in UI understanding and action execution, but adapting them to real target apps remains costly because mobile apps are numerous, frequently updated, and hard to cover with human-written tasks, demonstrations, or reward labels. Existing annotation-free GUI learning reduces manual supervision, yet lacks a unified substrate connecting target-app exploration, curriculum mining, rollout execution, and feedback, while policy optimization often relies on isolated rollouts and coarse rewards that are hard to convert into reliable improvement signals. We present MobileForge, an annotation-free adaptation system for mobile GUI agents. MobileForge consists of MobileGym, which grounds task generation and rollout evaluation in real mobile app interaction, and Hierarchical Feedback-Guided Policy Optimization (HiFPO), which turns trajectory outcomes, step-level process feedback, and corrective hints into hint-contextualized step-level GRPO updates. Using only automatically generated annotation-free adaptation data, MobileForge adapts Qwen3-VL-8B to 67.2% Pass@3 on AndroidWorld, close to the closed-data GUI-specialized GUI-Owl-1.5-8B base model at 69.0%. The MobileForge-adapted ForgeOwl-8B further reaches 77.6% Pass@3 on AndroidWorld and 41.0% success on the out-of-domain MobileWorld GUI-only split, establishing the strongest open-data mobile GUI agent in our evaluation. Code, data, and trained models will be released at https://mobile-forge.github.io/.

## Shipped code — file tree (`projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/`)

```
CITATION.cff
LICENSE
README.md
citations.bib
docs/acknowledgements.md
docs/assets/hifpo.png
docs/assets/main-performance.png
docs/assets/mobileforge-logo.png
docs/assets/mobileforge-overview.png
docs/assets/mobilegym.png
docs/data_release.md
docs/evaluation_results.md
docs/models.md
docs/pipeline.md
evaluation/androidworld/CONTRIBUTING.md
evaluation/androidworld/Dockerfile
evaluation/androidworld/LICENSE
evaluation/androidworld/README.md
evaluation/androidworld/android_world/__init__.py
evaluation/androidworld/android_world/agents/README.md
evaluation/androidworld/android_world/agents/__init__.py
evaluation/androidworld/android_world/agents/agent_utils.py
evaluation/androidworld/android_world/agents/base_agent.py
evaluation/androidworld/android_world/agents/coordinate_resize.py
evaluation/androidworld/android_world/agents/function_call_mobile_answer.py
evaluation/androidworld/android_world/agents/gui_owl.py
evaluation/androidworld/android_world/agents/human_agent.py
evaluation/androidworld/android_world/agents/infer.py
evaluation/androidworld/android_world/agents/long_term_memory_utils.py
evaluation/androidworld/android_world/agents/m3a.py
evaluation/androidworld/android_world/agents/m3a_utils.py
evaluation/androidworld/android_world/agents/mobile_agent_utils_new.py
evaluation/androidworld/android_world/agents/new_json_action.py
evaluation/androidworld/android_world/agents/qwen3_vl.py
evaluation/androidworld/android_world/agents/random_agent.py
evaluation/androidworld/android_world/agents/retry_utils.py
evaluation/androidworld/android_world/agents/seeact.py
evaluation/androidworld/android_world/agents/seeact_utils.py
evaluation/androidworld/android_world/agents/t3a.py
evaluation/androidworld/android_world/agents/ui_tars.py
evaluation/androidworld/android_world/agents/uitars_utils.py
evaluation/androidworld/android_world/checkpointer.py
evaluation/androidworld/android_world/constants.py
evaluation/androidworld/android_world/env/__init__.py
evaluation/androidworld/android_world/env/actuation.py
evaluation/androidworld/android_world/env/adb_utils.py
evaluation/androidworld/android_world/env/android_world_controller.py
evaluation/androidworld/android_world/env/device_constants.py
evaluation/androidworld/android_world/env/env_launcher.py
evaluation/androidworld/android_world/env/interface.py
evaluation/androidworld/android_world/env/json_action.py
evaluation/androidworld/android_world/env/representation_utils.py
evaluation/androidworld/android_world/env/setup_device/__init__.py
evaluation/androidworld/android_world/env/setup_device/apps.py
evaluation/androidworld/android_world/env/setup_device/setup.py
evaluation/androidworld/android_world/env/tools.py
evaluation/androidworld/android_world/episode_runner.py
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/AccessibilityForwarder.kt
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/AccessibilityForwarderTest.kt
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/AccessibilityTreeCreator.kt
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/AccessibilityTreeCreatorTest.kt
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/AndroidManifest.xml
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/AndroidManifest_lite.xml
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/FlagsBroadcastReceiver.kt
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/FlagsBroadcastReceiverTest.kt
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/LogFlags.kt
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/ParentChildNodePair.kt
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/UniqueIdsGenerator.kt
evaluation/androidworld/android_world/google/apps/java/com/google/androidenv/accessibilityforwarder/res/xml/accessibility_forwarder_service.xml
evaluation/androidworld/android_world/multi_attempt_runner.py
evaluation/androidworld/android_world/registry.py
evaluation/androidworld/android_world/suite_utils.py
evaluation/androidworld/android_world/task_evals/__init__.py
evaluation/androidworld/android_world/task_evals/common_validators/__init__.py
evaluation/androidworld/android_world/task_evals/common_validators/contacts_validators.py
evaluation/androidworld/android_world/task_evals/common_validators/file_validators.py
evaluation/androidworld/android_world/task_evals/common_validators/phone_validators.py
evaluation/androidworld/android_world/task_evals/common_validators/sms_validators.py
evaluation/androidworld/android_world/task_evals/common_validators/sqlite_validators.py
evaluation/androidworld/android_world/task_evals/composite/__init__.py
evaluation/androidworld/android_world/task_evals/composite/markor_sms.py
evaluation/androidworld/android_world/task_evals/composite/system.py
evaluation/androidworld/android_world/task_evals/information_retrieval/__init__.py
evaluation/androidworld/android_world/task_evals/information_retrieval/activity_app_utils.py
evaluation/androidworld/android_world/task_evals/information_retrieval/calendar_utils.py
evaluation/androidworld/android_world/task_evals/information_retrieval/datetime_utils.py
evaluation/androidworld/android_world/task_evals/information_retrieval/information_retrieval.py
evaluation/androidworld/android_world/task_evals/information_retrieval/information_retrieval_registry.py
evaluation/androidworld/android_world/task_evals/information_retrieval/joplin_app_utils.py
evaluation/androidworld/android_world/task_evals/information_retrieval/proto/__init__.py
evaluation/androidworld/android_world/task_evals/information_retrieval/proto/state.proto
evaluation/androidworld/android_world/task_evals/information_retrieval/proto/state_pb2.py
evaluation/androidworld/android_world/task_evals/information_retrieval/proto/state_pb2_grpc.py
evaluation/androidworld/android_world/task_evals/information_retrieval/proto/task.proto
evaluation/androidworld/android_world/task_evals/information_retrieval/proto/task_pb2.py
evaluation/androidworld/android_world/task_evals/information_retrieval/proto/task_pb2_grpc.py
evaluation/androidworld/android_world/task_evals/information_retrieval/proto/tasks.textproto
evaluation/androidworld/android_world/task_evals/information_retrieval/proto_utils.py
evaluation/androidworld/android_world/task_evals/information_retrieval/task_app_utils.py
evaluation/androidworld/android_world/task_evals/miniwob/__init__.py
evaluation/androidworld/android_world/task_evals/miniwob/miniwob_base.py
evaluation/androidworld/android_world/task_evals/miniwob/miniwob_registry.py
evaluation/androidworld/android_world/task_evals/robustness_study/__init__.py
evaluation/androidworld/android_world/task_evals/robustness_study/goal_template_variation.py
evaluation/androidworld/android_world/task_evals/robustness_study/screen_variation.py
evaluation/androidworld/android_world/task_evals/single/__init__.py
evaluation/androidworld/android_world/task_evals/single/audio_recorder.py
evaluation/androidworld/android_world/task_evals/single/browser.py
evaluation/androidworld/android_world/task_evals/single/calendar/__init__.py
evaluation/androidworld/android_world/task_evals/single/calendar/calendar.py
evaluation/androidworld/android_world/task_evals/single/calendar/calendar_evaluators.py
evaluation/androidworld/android_world/task_evals/single/calendar/calendar_utils.py
evaluation/androidworld/android_world/task_evals/single/calendar/events_generator.py
evaluation/androidworld/android_world/task_evals/single/camera.py
evaluation/androidworld/android_world/task_evals/single/clock.py
evaluation/androidworld/android_world/task_evals/single/contacts.py
evaluation/androidworld/android_world/task_evals/single/expense.py
evaluation/androidworld/android_world/task_evals/single/files.py
evaluation/androidworld/android_world/task_evals/single/generic.py
evaluation/androidworld/android_world/task_evals/single/markor.py
evaluation/androidworld/android_world/task_evals/single/osmand.py
evaluation/androidworld/android_world/task_evals/single/phone.py
evaluation/androidworld/android_world/task_evals/single/recipe.py
evaluation/androidworld/android_world/task_evals/single/retro_music.py
evaluation/androidworld/android_world/task_evals/single/simple_draw_pro.py
evaluation/androidworld/android_world/task_evals/single/simple_gallery_pro.py
evaluation/androidworld/android_world/task_evals/single/sms.py
evaluation/androidworld/android_world/task_evals/single/system.py
evaluation/androidworld/android_world/task_evals/single/vlc.py
evaluation/androidworld/android_world/task_evals/task_eval.py
evaluation/androidworld/android_world/task_evals/utils/__init__.py
evaluation/androidworld/android_world/task_evals/utils/receipt_generator.py
evaluation/androidworld/android_world/task_evals/utils/schema.py
evaluation/androidworld/android_world/task_evals/utils/sqlite_schema_utils.py
evaluation/androidworld/android_world/task_evals/utils/sqlite_test_utils.py
evaluation/androidworld/android_world/task_evals/utils/sqlite_utils.py
evaluation/androidworld/android_world/task_evals/utils/user_data_generation.py
evaluation/androidworld/android_world/task_metadata.json
evaluation/androidworld/android_world/utils/__init__.py
evaluation/androidworld/android_world/utils/app_snapshot.py
evaluation/androidworld/android_world/utils/contacts_utils.py
evaluation/androidworld/android_world/utils/datetime_utils.py
evaluation/androidworld/android_world/utils/fake_adb_responses.py
evaluation/androidworld/android_world/utils/file_test_utils.py
evaluation/androidworld/android_world/utils/file_utils.py
evaluation/androidworld/android_world/utils/fuzzy_match_lib.py
evaluation/androidworld/android_world/utils/plotting.py
evaluation/androidworld/android_world/utils/test_utils.py
evaluation/androidworld/apps/MODULE.bazel
evaluation/androidworld/apps/MODULE.bazel.lock
evaluation/androidworld/apps/WORKSPACE.bzlmod
evaluation/androidworld/apps/java/com/google/androidenv/AppConfiguration.kt
evaluation/androidworld/apps/java/com/google/androidenv/BUILD.bazel
evaluation/androidworld/apps/java/com/google/androidenv/Logger.kt
evaluation/androidworld/apps/java/com/google/androidenv/LoggerTest.kt
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/AndroidManifest.xml
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/BUILD.bazel
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/AndroidManifest.xml
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/BUILD.bazel
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/MainActivity.kt
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/LICENSE
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/shapes.js
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/book-flight/domestic.js
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_0.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_1.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_2.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_3.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_4.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_5.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_6.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_7.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_8.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/checkbox-numbers/ch_9.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/click-pie/raphael.icons.min.js
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/click-pie/raphael.min.js
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/click-pie/wheelnav.min.js
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/drag-cube/blank.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/drag-cube/cube.css
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/drag-cube/cube.js
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/delete.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/email-inbox.css
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/forward.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/left-arrow-white.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/left-arrow.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/reply.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/search.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/send.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/star-clicked.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox/star.png
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/email-inbox-nl/templates.js
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/ajax-loader.gif
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/file.gif
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/folder-closed.gif
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/folder.gif
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/minus.gif
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/plus.gif
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/treeview-black-line.gif
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/treeview-black.gif
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/treeview-default-line.gif
evaluation/androidworld/apps/java/com/google/androidenv/miniwob/app/assets/html/common/special/navigate-tree/images/treeview-default.gif
… (truncated)
```

## Detected entry points

- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/explore/curriculum_generator_refactored_add_aw_few-shot/main.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/explore/parallel_exploration/main.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/rollout/data_analyzer/main.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/explore/data_process/vis-exploration-output/main.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/training/verl/trainer/main.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/rollout/run.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/evaluation/androidworld/run.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/rollout/framework/models/AndroidWorld/run.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/explore/build_page_graph.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/explore/evaluate_existing_trajectories.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/explore/exploration_and_mining.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/explore/interactive_parallel_exploration.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/rollout/concurrent_execution.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/rollout/config_loader.py`
- `projects/PROJ-782-mobileforge-annotation-free-adaptation-f/external/MobileForge/evaluation/androidworld/checkpoint_parser.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `MobileForge` — not re-implementing it.
