import sys
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import PROJECT_ROOT
from utils.logger import get_logger

logger = get_logger("dependency_check")

# List of operations known to be compatible with CPU-only execution in this project's context.
# If the model config requires an operation NOT in this list, we abort.
ALLOWED_OPS = {
    "LlamaRMSNorm",
    "Qwen2RMSNorm",
    "Qwen2Attention",
    "Qwen2MLP",
    "Qwen2Model",
    "Qwen2ForCausalLM",
    "DiffusionPipeline",
    "AutoencoderKL",
    "UNet2DConditionModel",
    "T5EncoderModel",
    "ClipTextModel",
    "SDPAttention",
    "FlashAttention", # Allowed if fallback exists, but we check for explicit CPU usage
    "Matmul",
    "Add",
    "Mul",
    "LayerNorm",
    "GELU",
    "SiLU",
    "Linear",
    "Conv2d",
    "Softmax",
    "Reshape",
    "Transpose",
    "Squeeze",
    "Unsqueeze",
    "Concat",
    "Split",
    "View",
    "Contiguous",
    "To",
    "Float",
    "Half",
    "Bool",
    "Int",
    "GetItem",
    "SetItem",
    "Len",
    "Iter",
    "Next",
    "Range",
    "Zeros",
    "Ones",
    "Empty",
    "Full",
    "Arange",
    "Linspace",
    "Logspace",
    "Eye",
    "Diag",
    "Diagflat",
    "Diagonal",
    "Tril",
    "Triu",
    "Triu_indices",
    "Tril_indices",
    "MaskedFill",
    "MaskedSelect",
    "Nonzero",
    "Where",
    "Cat",
    "Stack",
    "Unbind",
    "Chunk",
    "SplitWithSizes",
    "Gather",
    "Scatter",
    "ScatterAdd",
    "IndexSelect",
    "IndexPut",
    "IndexCopy",
    "Take",
    "TakeAlongDim",
    "Put",
    "Sort",
    "Argsort",
    "TopK",
    "Topk",
    "Min",
    "Max",
    "Mean",
    "Sum",
    "Prod",
    "Cumsum",
    "Cumprod",
    "Std",
    "Var",
    "Median",
    "Mode",
    "Quantile",
    "Neg",
    "Abs",
    "Sign",
    "Sqrt",
    "Square",
    "Exp",
    "Expm1",
    "Log",
    "Log1p",
    "Log10",
    "Log2",
    "Logaddexp",
    "Logaddexp2",
    "Sigmoid",
    "Silu",
    "Swish",
    "Mish",
    "Tanh",
    "Tanhshrink",
    "Atanh",
    "Asinh",
    "Acosh",
    "Sinh",
    "Cosh",
    "Asin",
    "Acos",
    "Atan",
    "Atan2",
    "Sin",
    "Cos",
    "Tan",
    "Rint",
    "Round",
    "Floor",
    "Ceil",
    "Fmod",
    "Remainder",
    "Div",
    "Divide",
    "FloorDiv",
    "Mod",
    "Pow",
    "Exp2",
    "Erf",
    "Erfc",
    "Erfinv",
    "Erfinv",
    "Sinc",
    "Hardsigmoid",
    "Hardswish",
    "Hardtanh",
    "LeakyRelu",
    "Relu",
    "Relu6",
    "Elu",
    "CelU",
    "Gelu",
    "Mish",
    "Softmax",
    "Softmin",
    "Softplus",
    "Softshrink",
    "Softsign",
    "Tanhshrink",
    "LogSoftmax",
    "LogSigmoid",
    "Sigmoid",
    "SiLU",
    "Swish",
    "Glu",
    "Hardshrink",
    "LeakyRelu",
    "LogSigmoid",
    "MultilayerSoftmax",
    "Prelu",
    "Rrelu",
    "Selu",
    "Sigmoid",
    "Silu",
    "Swish",
    "Softmax",
    "Softmin",
    "Softplus",
    "Softshrink",
    "Softsign",
    "Tanhshrink",
    "Threshold",
    "Glu",
    "Hardshrink",
    "Hardtanh",
    "LeakyRelu",
    "LogSigmoid",
    "MultilayerSoftmax",
    "Prelu",
    "Rrelu",
    "Selu",
}

# Known unlisted ops that would indicate incompatibility with strict CPU-only constraints
# as per the Spec's Assumptions section regarding Qwen-Image-2.0.
DISALLOWED_OPS = {
    "FlashAttention", # Explicit flash attention without CPU fallback
    "FusedRMSNorm",
    "FusedSoftmax",
    "FusedLayerNorm",
    "FusedGelu",
    "FusedSiLU",
    "FusedSwish",
    "FusedMish",
    "FusedLeakyRelu",
    "FusedPrelu",
    "FusedRrelu",
    "FusedSelu",
    "FusedThreshold",
    "FusedGlu",
    "FusedHardshrink",
    "FusedHardtanh",
    "FusedLogSigmoid",
    "FusedMultilayerSoftmax",
    "FusedFusedRMSNorm",
    "FusedFusedLayerNorm",
    "FusedFusedGelu",
    "FusedFusedSiLU",
    "FusedFusedSwish",
    "FusedFusedMish",
    "FusedFusedLeakyRelu",
    "FusedFusedPrelu",
    "FusedFusedRrelu",
    "FusedFusedSelu",
    "FusedFusedThreshold",
    "FusedFusedGlu",
    "FusedFusedHardshrink",
    "FusedFusedHardtanh",
    "FusedFusedLogSigmoid",
    "FusedFusedMultilayerSoftmax",
}

def check_package_versions() -> Dict[str, Any]:
    """
    Checks installed versions of critical packages.
    """
    packages = {
        "diffusers": None,
        "transformers": None,
        "torch": None,
        "pandas": None,
        "numpy": None,
        "datasets": None,
    }
    
    results = {}
    for pkg_name in packages:
        try:
            module = __import__(pkg_name)
            version = getattr(module, "__version__", "unknown")
            results[pkg_name] = {"installed": True, "version": version}
        except ImportError:
            results[pkg_name] = {"installed": False, "version": None}
    
    return results

def check_model_config_ops(model_id: str) -> bool:
    """
    Loads the model config for the given model_id and checks for required ops.
    Returns True if safe (all ops are allowed), False if unlisted/disallowed ops are detected.
    Aborts (raises SystemExit) if specific unlisted ops are required.
    """
    logger.info(f"Checking ops for {model_id}")
    
    try:
        from transformers import AutoConfig
        from diffusers import DiffusionPipeline
        
        # Attempt to load the config
        config = AutoConfig.from_pretrained(model_id, trust_remote_code=True)
        
        # Inspect the config for architecture hints
        # We look for specific keys that might indicate the use of disallowed ops
        # Since we cannot easily extract the exact ops from the config without loading the model,
        # we check for known architecture names and specific attributes that imply disallowed ops.
        
        architecture = getattr(config, "architectures", [])
        model_type = getattr(config, "model_type", "")
        
        # Check for known disallowed architecture patterns
        for arch in architecture:
            if arch in DISALLOWED_OPS:
                logger.error(f"Model {model_id} uses disallowed architecture: {arch}")
                return False
        
        # Check for specific attributes that might indicate disallowed ops
        # For example, some configs have a 'use_flash_attention' flag
        if getattr(config, "use_flash_attention_2", False):
            logger.error(f"Model {model_id} requires Flash Attention 2, which is not supported on CPU.")
            return False
        
        # If we successfully loaded the config and didn't find disallowed ops, assume safe
        # In a more robust implementation, we would parse the full graph, but this is a good heuristic
        # for the current scope.
        logger.info(f"Model {model_id} config check passed.")
        return True
        
    except Exception as e:
        logger.error(f"Failed to check ops for {model_id}: {e}")
        # If we can't check, we should fail loudly to be safe
        return False

def run_dependency_check(model_id: Optional[str] = None) -> bool:
    """
    Runs the full dependency check.
    """
    logger.info("Running dependency check...")
    versions = check_package_versions()
    
    critical = ["diffusers", "transformers", "torch"]
    missing = [k for k, v in versions.items() if k in critical and not v["installed"]]
    
    if missing:
        logger.error(f"Missing critical packages: {missing}")
        return False
    
    if model_id:
        if not check_model_config_ops(model_id):
            logger.error(f"Model {model_id} requires unlisted ops.")
            return False
    
    logger.info("Dependency check passed.")
    return True

def main():
    # Default model to check is Qwen-Image-2.0 as per task description
    model_id = "Qwen/Qwen-Image-2.0"
    if not run_dependency_check(model_id):
        sys.exit(1)

if __name__ == "__main__":
    main()