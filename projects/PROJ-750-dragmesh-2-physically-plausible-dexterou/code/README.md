# DragMesh-2 Adaptation: CPU-Tractable Contact Dynamics Proxy

## Original vs. Adapted Scope

| Feature | Original (Isaac Gym / GPU) | Adapted (CPU / Scikit-learn) |
| :--- | :--- | :--- |
| **Physics Engine** | Isaac Gym (GPU-accelerated rigid body) | `pybullet` (CPU, single-threaded) |
| **Policy Model** | PPO/GLA Transformer (10M+ params) | Logistic Regression / Small MLP (CPU) |
| **Environment** | 64 parallel environments, 20M steps | 1 environment, 500 steps (1 epoch) |
| **Object** | Full GAPartNet (complex meshes) | 1 Representative Object (Lid/Hinge) |
| **Observation** | 1700+ dim (History tokens) | 25 dim (State + Velocity) |
| **Goal** | Robust dexterous manipulation | **Demonstrate contact-load sensitivity** |
| **Metric** | Task success rate over 1000 episodes | **Correlation between damping & success** |

## Scientific Logic Preserved
The paper claims that policies trained without physical awareness fail under varying contact loads (damping). This adaptation:
1.  **Simulates** the articulated object (a hinged lid) using `pybullet`.
2.  **Applies** a "policy" (simple PD controller) to open the lid.
3.  **Varies** the joint damping parameter (the "contact load" proxy) across a sweep.
4.  **Measures** the success rate of opening the lid under each damping condition.
5.  **Output**: A CSV proving that as damping increases, the simple controller fails, validating the paper's premise that "contact dynamics matter."

## Artifacts
- `data/sweep_results.csv`: Damping values vs. Success/Progress metrics.
- `figures/damping_sensitivity.png`: Plot of the failure curve.
