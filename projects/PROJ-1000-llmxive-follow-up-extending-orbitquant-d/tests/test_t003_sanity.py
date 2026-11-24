import torch
import pytest
from config import Config
from models.flux_wan_loader import load_dit_model
from models.dit_wrapper import DiTActivationCapture
from analysis.entropy_proxy import compute_semantic_entropy
from quantization.w2a4_engine import W2A4Quantizer
from quantization.static_baseline import get_static_rotation_matrix

def test_t003_pipeline_sanity():
    prompt = "a cat on a sofa"
    cfg = Config()
    
    # 1. Model Loader
    pipe, wrapper = load_dit_model("SD2.1", device="cpu")
    assert pipe is not None
    assert wrapper is not None
    
    # 2. Activation Variance
    capture = DiTActivationCapture(pipe, wrapper)
    variances = capture.measure_activation_variance(prompt)
    assert isinstance(variances, dict)
    assert len(variances) > 0
    for v in variances.values():
        assert isinstance(v, float)
    
    # 3. Semantic Entropy
    entropy = compute_semantic_entropy(prompt, num_samples=2)
    assert isinstance(entropy, float)
    
    # 4. W2A4 Quantizer
    quantizer = W2A4Quantizer(cfg)
    test_tensor = torch.randn(1, 128)
    rot_mat = get_static_rotation_matrix(128)
    quantized = quantizer.quantize_activation(test_tensor, rotation_matrix=rot_mat)
    
    assert quantized.shape == test_tensor.shape
    assert quantized.dtype == torch.float32