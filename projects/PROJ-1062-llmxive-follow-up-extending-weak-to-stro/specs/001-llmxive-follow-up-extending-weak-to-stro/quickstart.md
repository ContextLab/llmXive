# Quickstart: Cross-Architecture Distillation

## Prerequisites

- **Python**: 3.11+
- **RAM**: 7GB+ (Free-tier runner limit).
- **Disk**: 14GB+ (for model weights and data).
- **Internet**: Access to HuggingFace Hub.

## Installation

1.  **Clone the repository** and navigate to the project directory.
2.  **Create a virtual environment**:
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```
3.  **Install dependencies**:
    ```bash
    pip install -r projects/PROJ-1062-llmxive-follow-up-extending-weak-to-stro/code/requirements.txt
    ```

## Configuration

Edit `projects/PROJ-1062-llmxive-follow-up-extending-weak-to-stro/code/config/defaults.yaml` to set:
- `teacher_pre_rl_path`: Path to pre-RL checkpoint (or synthetic base).
- `teacher_post_rl_path`: Path to post-RL checkpoint (or synthetic fine-tuned).
- `student_moe_path`: Path to MoE student weights.
- `student_ssm_path`: Path to SSM student weights.
- `batch_size`: Must be `1` for CPU.
- `gradient_accumulation_steps`: Recommended `8`.

## Running the Experiment

### 1. Download Data
```bash
python projects/PROJ-1062-llmxive-follow-up-extending-weak-to-stro/code/data/download_aime.py
```

### 2. Preprocess Data (Compute Rewards)
```bash
python projects/PROJ-1062-llmxive-follow-up-extending-weak-to-stro/code/data/preprocess.py
```
*Note: This step computes the implicit reward signal using the teacher checkpoints.*

### 3. Run Training & Evaluation (MoE)
```bash
python projects/PROJ-1062-llmxive-follow-up-extending-weak-to-stro/code/main.py --arch MoE
```

### 4. Run Training & Evaluation (SSM)
```bash
python projects/PROJ-1062-llmxive-follow-up-extending-weak-to-stro/code/main.py --arch SSM
```

### 5. Generate Statistical Report
```bash
python projects/PROJ-1062-llmxive-follow-up-extending-weak-to-stro/code/main.py --aggregate
```

## Troubleshooting

- **OOM Error**: Reduce `batch_size` to 1 (default) and ensure `gradient_accumulation_steps` is high. Check `torch.cuda.is_available()` returns `False`.
- **NaN Loss**: Check for epsilon smoothing in `reward_computation.py`.
- **Slow Execution**: Ensure `int8` quantization is enabled. The experiment is designed for a duration of several hours.; if it exceeds, reduce training steps in `defaults.yaml`.