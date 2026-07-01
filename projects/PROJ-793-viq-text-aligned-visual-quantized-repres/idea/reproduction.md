# Reproduce & validate: ViQ: Text-Aligned Visual Quantized Representations at Any Resolution

## This is a REPRODUCTION project — the implementation ALREADY EXISTS

The code that implements this paper has been vendored, unchanged, as a git
submodule at:

    projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/   (clone of https://github.com/yuxumin/ViQ)

The task is NOT to build anything from scratch. The task is to **run, validate,
and reproduce** the shipped implementation end-to-end and confirm it executes
and produces real artifacts.

## Ingested paper

**Title:** ViQ: Text-Aligned Visual Quantized Representations at Any Resolution

**Abstract:** A unified representation for text and vision is a natural pursuit, as it enables simpler multimodal modeling and more efficient training. However, representing images as discrete signals in the same way as text inevitably introduces severe information loss. Existing work struggles to balance low-level details and high-level semantics in discrete representations: reconstruction-oriented representations often lack semantic information, whereas semantically stronger features typically suffer from severe loss of detail. We present ViQ, a Visual Quantized Representations framework, which is designed to balance semantics and details in discrete representations while supporting inputs at native resolutions, thereby enabling it to serve as a unified and general discrete representation for arbitrary visual inputs. Our approach structures quantization learning into two stages: text-aligned pre-training and feature discretization. With text-aligned pre-training, we enhance the visual encoder semantic-rich supervision from the pretrained language model and enable it to process native-resolution visual inputs. During discretization, we propose a proximal representation learning strategy to progressively compact the feature space, along with a position-aware head-wise quantization mechanism that enables flexible processing of arbitrary resolutions. Extensive experiments on multimodal tasks demonstrate that ViQ achieves competitive performance compared to state-of-the-art multimodal vision encoders with continuous and high-dimensional visual features, while maintaining high precision in low-level reconstruction. We also show that multimodal training with visual quantized representations largely improves efficiency, yielding up to 20\%-70\% acceleration with different base LLMs and training recipes.

## Shipped code — file tree (`projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/`)

```
.gitattributes
.gitignore
LICENSE
README.md
assets/hunyuan_logo.png
assets/pipeline.png
assets/speedup.png
assets/teaser.png
assets/verify_0.jpeg
assets/verify_1.jpg
scripts/build_env.sh
scripts/example.sh
scripts/example_dataset/example.json
scripts/example_dataset/images/blue_square.png
scripts/example_dataset/images/green_triangle.png
scripts/example_dataset/images/red_circle.png
scripts/example_dataset/images/yellow_circle.png
scripts/zero1.json
viq_inference/ViQ.py
viq_inference/converter/convert_weight.py
viq_inference/converter/run_convert.sh
viq_inference/modeling_viq.py
viq_train/llava_viq/__init__.py
viq_train/llava_viq/_paths.py
viq_train/llava_viq/constants.py
viq_train/llava_viq/conversation.py
viq_train/llava_viq/mm_utils.py
viq_train/llava_viq/model/__init__.py
viq_train/llava_viq/model/language_model/llava_llama.py
viq_train/llava_viq/model/language_model/llava_qwen2.py
viq_train/llava_viq/model/llava_arch.py
viq_train/llava_viq/model/multimodal_encoder/assets/default_processor/preprocessor_config.json
viq_train/llava_viq/model/multimodal_encoder/builder.py
viq_train/llava_viq/model/multimodal_encoder/encoders/__init__.py
viq_train/llava_viq/model/multimodal_encoder/encoders/siglip_vit_anyres.py
viq_train/llava_viq/model/multimodal_encoder/encoders/siglip_vit_anyres_viq.py
viq_train/llava_viq/model/multimodal_encoder/envir_defines.py
viq_train/llava_viq/model/multimodal_encoder/heads/__init__.py
viq_train/llava_viq/model/multimodal_encoder/heads/dual_vq_head.py
viq_train/llava_viq/model/multimodal_encoder/heads/movq_modules.py
viq_train/llava_viq/model/multimodal_encoder/heads/vae_heads.py
viq_train/llava_viq/model/multimodal_encoder/heads/vitvq_modules.py
viq_train/llava_viq/model/multimodal_encoder/layers/__init__.py
viq_train/llava_viq/model/multimodal_encoder/layers/_common.py
viq_train/llava_viq/model/multimodal_encoder/layers/model_utils.py
viq_train/llava_viq/model/multimodal_encoder/losses/__init__.py
viq_train/llava_viq/model/multimodal_encoder/losses/lpips.py
viq_train/llava_viq/model/multimodal_encoder/losses/perceptual_loss.py
viq_train/llava_viq/model/multimodal_encoder/quantizers/VQ_packer.py
viq_train/llava_viq/model/multimodal_encoder/quantizers/__init__.py
viq_train/llava_viq/model/multimodal_encoder/quantizers/bsq.py
viq_train/llava_viq/model/multimodal_encoder/quantizers/fake_quantizer.py
viq_train/llava_viq/model/multimodal_encoder/quantizers/fsq.py
viq_train/llava_viq/model/multimodal_encoder/quantizers/lfq.py
viq_train/llava_viq/model/multimodal_encoder/quantizers/simvq.py
viq_train/llava_viq/model/multimodal_encoder/quantizers/vq.py
viq_train/llava_viq/model/multimodal_encoder/vae/__init__.py
viq_train/llava_viq/model/multimodal_encoder/vae/autoencoder_kl_qwenimage.py
viq_train/llava_viq/model/multimodal_encoder/vae/ldm/config.yaml
viq_train/llava_viq/model/multimodal_encoder/vae/ldm/model.py
viq_train/llava_viq/model/multimodal_encoder/vae/ldm/vae.py
viq_train/llava_viq/model/multimodal_projector/builder.py
viq_train/llava_viq/model/multimodal_projector/pooler_projector.py
viq_train/llava_viq/model/multimodal_resampler/builder.py
viq_train/llava_viq/train/llava_trainer.py
viq_train/llava_viq/train/train.py
```

## Detected entry points

- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/train/train.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_inference/ViQ.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_inference/modeling_viq.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_inference/converter/convert_weight.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/constants.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/conversation.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/mm_utils.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/model/llava_arch.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/train/llava_trainer.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/model/language_model/llava_llama.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/model/language_model/llava_qwen2.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/model/multimodal_encoder/builder.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/model/multimodal_encoder/envir_defines.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/model/multimodal_projector/builder.py`
- `projects/PROJ-793-viq-text-aligned-visual-quantized-repres/external/ViQ/viq_train/llava_viq/model/multimodal_projector/pooler_projector.py`

## What "done" means here

1. The submodule's real entry script(s) run via the quickstart run-book.
2. The run produces real artifacts (data/figures) — no fabricated results.
3. The reproduction is reported against the paper's claims.

Because the implementation already exists, the spec/plan/tasks below describe
RUNNING and VALIDATING `ViQ` — not re-implementing it.
