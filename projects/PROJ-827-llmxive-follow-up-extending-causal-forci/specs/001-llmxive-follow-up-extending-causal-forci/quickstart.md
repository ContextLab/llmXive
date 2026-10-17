# Quickstart: Physics‑Teacher Distillation

The following commands run the entire end‑to‑end experiment on a fresh GitHub Actions runner (or a local Linux environment with the same resources).

## Prerequisites
- Python 3.11 installed.
- `git clone` the repository.
- Internet access (to download Box2D metadata and metric reference datasets).

## Step‑by‑Step

1. **Create and activate the virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt   # pins all versions
   ```

2. **Set deterministic seeds (once per run)**
   ```bash
   export GLOBAL_SEED=12345
   ```

3. **Generate physics‑teacher data**
   ```bash
   python -m src.data_generation.generate \
       --seed $GLOBAL_SEED \
       --num-train 5000 \
       --num-val 1000 \
       --num-test 1000 \
       --output-dir data/physics
   ```
   - Produces `data/physics/train/`, `val/`, `test/` with `.mp4` videos and `.npz` trajectories.
   - The script logs any NaN‑containing sequences and discards them (fulfilling FR‑006).

4. **Train the neural‑teacher baseline on the original Causal Forcing++ data**
   ```bash
   python -m src.models.neural_teacher \
       --dataset causal_forcing_pp \
       --epochs 20 \
       --batch-size 8 \
       --output-dir outputs/neural_teacher
   ```

5. **Train the **control** neural‑teacher baseline on the synthetic physics data**
   ```bash
   python -m src.models.neural_teacher \
       --dataset physics \
       --data-dir data/physics/train \
       --epochs 20 \
       --batch-size 8 \
       --output-dir outputs/neural_teacher_physics
   ```

6. **Train the student model on physics data**
   ```bash
   python -m src.models.student_diffusion \
       --train-dir data/physics/train \
       --val-dir data/physics/val \
       --epochs 6 \
       --batch-size 8 \
       --gradient-accumulation-steps 4 \
       --checkpoint-activation \
       --output-dir outputs/student_physics
   ```

7. **Run evaluation (shared held‑out test set)**
   ```bash
   python -m src.evaluation.metrics \
       --test-dir data/physics/test \
       --neural-checkpoint outputs/neural_teacher/checkpoint.pt \
       --control-checkpoint outputs/neural_teacher_physics/checkpoint.pt \
       --student-checkpoint outputs/student_physics/checkpoint.pt \
       --output-dir outputs/metrics
   ```

8. **Statistical analysis (includes power analysis)**
   ```bash
   python -m src.evaluation.statistical \
       --metrics-dir outputs/metrics \
       --output-dir outputs/statistics
   ```

9. **Ablation study (optional)**
   ```bash
   python -m src.ablation.run_ablation \
       --param friction 0.2 0.5 0.8 \
       --param elasticity 0.1 0.5 0.9 \
       --samples-per-config 500 \
       --output-dir outputs/ablation
   ```

10. **Validate contracts**
    ```bash
    pytest -m contract
    ```

11. **Check runtime & memory compliance (SC‑005)**
    ```bash
    cat outputs/manifest.json   # contains wall_clock_seconds and peak_ram_gb
    # The run will abort automatically if limits are exceeded.
    ```

12. **Inspect the final manifest**
    ```bash
    cat outputs/manifest.json
    ```

All generated artifacts are version‑hashed; re‑running the pipeline with the same `GLOBAL_SEED` yields identical hashes, confirming reproducibility (Principle I).

---


