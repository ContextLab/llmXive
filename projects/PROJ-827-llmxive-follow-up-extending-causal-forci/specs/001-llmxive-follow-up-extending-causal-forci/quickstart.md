# Quickstart: Physics-Teacher Distillation

Run the full experiment on a fresh GitHub Actions runner (or a local Linux environment with comparable resources).

## Prerequisites
- Python 3.11  
- Git clone of the repository  
- Internet access (only needed for installing packages; all data are generated locally)

## Steps

1. **Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt   # pins exact versions
   ```

2. **Set a global deterministic seed**
   ```bash
   export GLOBAL_SEED=12345
   ```

3. **Generate synthetic physics data**
   ```bash
   python -m src.data_generation.generate \
       --seed $GLOBAL_SEED \
       --num-train <N_TRAIN> \
       --num-val <N_VAL> \
       --num-test <N_TEST> \
       --output-dir data/physics
   ```
   - `<N_TRAIN>`, `<N_VAL>`, `<N_TEST>` are **[deferred]** to the implementation phase; choose values that respect the 6 h / 7 GB budget (minimum 500 training sequences, ≥ 200 test sequences for power).  
   - The script discards any NaN‑containing sequences, logs warnings, and verifies determinism by re‑running a fixed‑seed subset and comparing checksums.

4. **Generate neural‑teacher signals (baseline teacher)**
   ```bash
   python -m src.models.neural_teacher \
       --data-dir data/physics/train \
       --output-dir data/physics/neural_teacher_signals \
       --seed $GLOBAL_SEED
   ```
   This step produces frame‑wise predictions that will be used as teacher signals for the baseline diffusion model.

5. **Train the baseline diffusion model (neural‑teacher signals)**
   ```bash
   python -m src.models.diffusion_baseline \
       --train-dir data/physics/train \
       --teacher-signals data/physics/neural_teacher_signals \
       --model-size small   # uses the ~multi‑million‑parameter architecture
       --epochs 10 \
       --batch-size 4 \
       --gradient-accumulation-steps 8 \
       --checkpoint-activation \
       --output-dir outputs/baseline_diffusion
   ```

6. **Train the student diffusion model (physics teacher)**
   ```bash
   python -m src.models.diffusion_student \
       --train-dir data/physics/train \
       --teacher-signals data/physics/train/trajectories.npz \
       --model-size small   # same ~5 M‑parameter architecture as baseline
       --epochs 10 \
       --batch-size 4 \
       --gradient-accumulation-steps 8 \
       --checkpoint-activation \
       --output-dir outputs/student_physics
   ```

7. **Run evaluation on the held‑out test set**
   ```bash
   python -m src.evaluation.metrics \
       --test-dir data/physics/test \
       --baseline-checkpoint outputs/baseline_diffusion/checkpoint.pt \
       --student-checkpoint outputs/student_physics/checkpoint.pt \
       --lpips-sample 100 \   # sample size for LPIPS/FID (≤ 100)
       --fid-sample 100 \
       --output-dir outputs/metrics
   ```

8. **Statistical analysis (includes power analysis & permutation test)**
   ```bash
   python -m src.evaluation.statistical \
       --metrics-dir outputs/metrics \
       --output-dir outputs/statistics
   ```

9. **Ablation study over physics parameters**
   ```bash
   python -m src.ablation.run_ablation \
       --param friction 0.2 0.35 0.5 0.65 0.8 \
       --param elasticity 0.1 0.3 0.5 0.7 0.9 \
       --samples-per-config 3 \
       --output-dir outputs/ablation
   ```

10. **Validate contracts & metric sanity checks**
    ```bash
    pytest -m contract
    pytest tests/unit   # includes SSIM(x,x)=1, FID(S,S)=0 checks
    ```

11. **Check runtime & memory compliance (SC‑005)**
    ```bash
    cat outputs/manifest.json   # fields: wall_clock_seconds, peak_ram_gb
    # The pipeline aborts automatically if limits are exceeded; no placeholders are inserted.
    ```

Re‑running the entire pipeline with the same `GLOBAL_SEED` yields identical hashes for all outputs, confirming reproducibility (Principle I). Every metric in the final tables is a real measurement traced via `outputs/manifest.json` (Anti‑Fabrication Commitment).

---

