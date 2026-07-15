"""
Integration test for full pipeline.
"""
import numpy as np
from code.synthetic.generator import generate_synthetic_nebula
from code.synthetic.artifacts import inject_noise
from code.metrics.ellipticity import calculate_ellipticity
from code.config import GENERATOR_SEED, NOISE_SEED

def test_full_pipeline():
    """
    End-to-end test: Generate -> Inject Noise -> Measure -> Compare.
    """
    # 1. Generate
    np.random.seed(GENERATOR_SEED)
    image, gt_params = generate_synthetic_nebula()
    
    # 2. Inject Noise
    np.random.seed(NOISE_SEED)
    noisy_image = inject_noise(image, 0.05)
    
    # 3. Measure
    e1, e2 = calculate_ellipticity(noisy_image)
    
    # 4. Compare (basic sanity check)
    # We expect some bias, but not a crash
    assert e1 is not None
    assert e2 is not None
    assert np.isfinite(e1)
    assert np.isfinite(e2)