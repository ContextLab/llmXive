# Quickstart: Physics-Teacher Distillation

The following commands run the entire end‑to‑end experiment on a fresh GitHub Actions runner (or a local Linux environment with the same resources).

## Prerequisites
- Python 3.11 installed.
- `git clone` the repository.
- Internet access (to download the verified Box2D metadata JSON **if needed**; the current pipeline generates worlds internally, so this step can be omitted).

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
       --num-train <N_TRAIN> \
       --num-val <N_VAL> \
       --num-test <N_TEST> \
       --output-dir data/physics
   ```
   - Sequence counts are **[deferred]** to implementation, chosen to fit the 6 h / 7 GB budget.
   - Produces `data/physics/train/`, `val/`, `test/` with `.mp4` videos and `.npz` trajectories.
   - The script logs any NaN‑containing sequences and discards them (fulfilling the relevant functional requirement), and re‑runs a fixed‑seed subset to verify determinism by checksum comparison (as defined in the functional specification).

4. **Train the neural‑teacher baseline**
   ```bash
   python -m src.models.neural_teacher \
       --dataset physics \
       --data-dir data/physics/train \
       --epochs <EPOCHS> \
       --batch-size 8 \
       --output-dir outputs/neural_teacher
   ```
   - This ConvLSTM video‑prediction model learns to predict the next frame from the current frame **without** explicit trajectory input, providing the neural teacher signal.

5. **Train the student model on physics data**
   ```bash
   python -m src.models.student_diffusion \
       --train-dir data/physics/train \
       --val-dir data/physics/val \
       --epochs <EPOCHS> \
       --batch-size 8 \
       --gradient-accumulation-steps 4 \
       --checkpoint-activation \
       --output-dir outputs/student_physics
   ```

6. **Run evaluation (shared held‑out test set)**
   ```bash
   python -m src.evaluation.metrics \
       --test-dir data/physics/test \
       --neural-checkpoint outputs/neural_teacher/checkpoint.pt \
       --student-checkpoint outputs/student_physics/checkpoint.pt \
       --output-dir outputs/metrics
   ```

7. **Statistical analysis (includes power analysis)**
   ```bash
   python -m src.evaluation.statistical \
       --metrics-dir outputs/metrics \
       --output-dir outputs/statistics
   ```

8. **Ablation study**
   ```bash
   python -m src.ablation.run_ablation \
       --param friction 0.2 0.35 0.5 0.65 0.8 \
       --param elasticity 0.1 0.3 0.5 0.7 0.9 \
       --samples-per-config 3 \
       --output-dir outputs/ablation
   ```
   - Five levels per parameter, three random seeds per level (total 15 sequences per setting), ensuring sufficient degrees of freedom for regression.

9. **Validate contracts and metric ground truths**
   ```bash
   pytest -m contract
   pytest tests/unit   # includes analytic metric identity tests (SSIM(x,x)=1, FID(S,S)=0)
   ```

10. **Check runtime & memory compliance (SC‑005)**
    ```bash
    cat outputs/manifest.json   # contains wall_clock_seconds and peak_ram_gb
    # The run aborts automatically if limits are exceeded — it never truncates or substitutes values.
    ```

All generated artifacts are version‑hashed; re‑running the pipeline with the same `GLOBAL_SEED` yields identical hashes, confirming reproducibility (Principle I). **Every reported metric is a real measurement** traced via `outputs/manifest.json`; the pipeline fails loudly rather than emitting placeholder values (Anti‑Fabrication Commitment).

---

