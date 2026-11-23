# Research Handoff Note

## Pipeline Architecture
The pipeline is modular, consisting of distinct stages for Ingestion, Clustering, Training, Inference, Simulation, and Evaluation. Each stage produces artifacts consumed by the next.

## Known Limitations
1. **CPU Constraints**:
 - **Memory Bandwidth**: Large-scale BERT embedding generation is bottlenecked by single-threaded CPU performance.
 - **Simulation Speed**: PyBullet simulation runs significantly slower than GPU-accelerated alternatives.
2. **Clustering Heuristics**:
 - The `k_reduction_step_size` (default 5) is a heuristic. Future research may optimize this dynamically based on data density.
3. **Model Complexity**:
 - Decision Trees may overfit on small clusters; CGMMs may struggle with high-dimensional action spaces.

## Recommendations for Next Phase
1. **Algorithmic Optimizations**:
 - **Model Pruning**: Apply pruning techniques to Decision Trees to reduce inference latency.
 - **Quantization**: Explore INT8 quantization for BERT embeddings to reduce memory footprint.
2. **Efficient Clustering**:
 - Investigate Mini-Batch K-Means for faster initial clustering on larger subsets.
3. **CPU-Specific Tuning**:
 - Optimize PyBullet physics steps for CPU cache locality.
 - Use multi-threading for BERT embedding generation (via `transformers` parallelism) without GPU offloading.

## Next Steps
- Validate the pipeline on a larger, more diverse dataset.
- Experiment with alternative non-neural architectures (e.g., Random Forests, XGBoost).
- Refine the VLA Proxy baseline for better ground truth approximation.
