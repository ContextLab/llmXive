"""
Configuration for the Bidirectional Evolutionary Search (BES) framework.
Specifically handles the forward step LLM configuration.

This module generates the configuration file for the small pre-trained LLM
(distilbert-base-uncased) used in the forward step of the BES loop.

Constraints:
- device='cpu' is enforced.
- bitsandbytes is explicitly forbidden (no 8-bit quantization on CPU).
- This task is for configuration generation ONLY; no model download occurs here.
- Explicitly mandates optimum.onnxruntime quantization flags for CPU execution.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration values
DEFAULT_MODEL_ID = "distilbert-base-uncased"
DEFAULT_DEVICE = "cpu"
DEFAULT_REVISION = None  # Use latest if not specified
DEFAULT_MAX_LENGTH = 512
DEFAULT_BATCH_SIZE = 1
DEFAULT_TEMPERATURE = 0.7
DEFAULT_TOP_K = 50
DEFAULT_TOP_P = 0.95

# CPU optimization flags
# Disable bitsandbytes as it requires CUDA and is forbidden by task constraints
USE_BITSANDBYTES = False
USE_IPEx = True
IPEX_PRECISION = "bf16"  # Use bfloat16 for Intel AMX/AVX512 support if available, else fallback to fp32

# Optimum ONNX Runtime configuration
# Explicitly mandate optimum.onnxruntime quantization flags for CPU execution to prevent OOM
USE_OPTIMUM_ONNXRUNTIME = True
ONNX_QUANTIZATION = "8-bit"
ONNX_DEVICE = "cpu"

class BESConfig:
    """Configuration container for BES components."""

    def __init__(
        self,
        model_id: str = DEFAULT_MODEL_ID,
        device: str = DEFAULT_DEVICE,
        revision: Optional[str] = DEFAULT_REVISION,
        max_length: int = DEFAULT_MAX_LENGTH,
        batch_size: int = DEFAULT_BATCH_SIZE,
        temperature: float = DEFAULT_TEMPERATURE,
        top_k: int = DEFAULT_TOP_K,
        top_p: float = DEFAULT_TOP_P,
        use_ipex: bool = USE_IPEx,
        ipex_precision: str = IPEX_PRECISION,
        use_bitsandbytes: bool = USE_BITSANDBYTES,
        use_optimum_onnxruntime: bool = USE_OPTIMUM_ONNXRUNTIME,
        onnx_quantization: str = ONNX_QUANTIZATION,
        onnx_device: str = ONNX_DEVICE,
    ):
        self.model_id = model_id
        self.device = device
        self.revision = revision
        self.max_length = max_length
        self.batch_size = batch_size
        self.temperature = temperature
        self.top_k = top_k
        self.top_p = top_p
        self.use_ipex = use_ipex
        self.ipex_precision = ipex_precision
        self.use_bitsandbytes = use_bitsandbytes
        self.use_optimum_onnxruntime = use_optimum_onnxruntime
        self.onnx_quantization = onnx_quantization
        self.onnx_device = onnx_device

        # Validation
        if self.device != "cpu":
            raise ValueError("Forward step configuration only supports 'cpu' device to ensure compatibility with CI runners.")
        if self.use_bitsandbytes:
            raise ValueError("bitsandbytes is forbidden in this configuration (CPU-only constraint).")
        if self.use_ipex and self.ipex_precision not in ["bf16", "fp32"]:
            raise ValueError(f"Invalid IPEX precision: {self.ipex_precision}. Must be 'bf16' or 'fp32'.")
        if self.use_optimum_onnxruntime and self.onnx_device != "cpu":
            raise ValueError("Optimum ONNX Runtime configuration requires 'cpu' device in this context.")

    def to_dict(self) -> Dict[str, Any]:
        """Convert config to a dictionary for serialization."""
        return {
            "model_id": self.model_id,
            "device": self.device,
            "revision": self.revision,
            "max_length": self.max_length,
            "batch_size": self.batch_size,
            "temperature": self.temperature,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "use_ipex": self.use_ipex,
            "ipex_precision": self.ipex_precision,
            "use_bitsandbytes": self.use_bitsandbytes,
            "use_optimum_onnxruntime": self.use_optimum_onnxruntime,
            "onnx_quantization": self.onnx_quantization,
            "onnx_device": self.onnx_device,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BESConfig":
        """Create a config instance from a dictionary."""
        return cls(
            model_id=data.get("model_id", DEFAULT_MODEL_ID),
            device=data.get("device", DEFAULT_DEVICE),
            revision=data.get("revision", DEFAULT_REVISION),
            max_length=data.get("max_length", DEFAULT_MAX_LENGTH),
            batch_size=data.get("batch_size", DEFAULT_BATCH_SIZE),
            temperature=data.get("temperature", DEFAULT_TEMPERATURE),
            top_k=data.get("top_k", DEFAULT_TOP_K),
            top_p=data.get("top_p", DEFAULT_TOP_P),
            use_ipex=data.get("use_ipex", USE_IPEx),
            ipex_precision=data.get("ipex_precision", IPEX_PRECISION),
            use_bitsandbytes=data.get("use_bitsandbytes", USE_BITSANDBYTES),
            use_optimum_onnxruntime=data.get("use_optimum_onnxruntime", USE_OPTIMUM_ONNXRUNTIME),
            onnx_quantization=data.get("onnx_quantization", ONNX_QUANTIZATION),
            onnx_device=data.get("onnx_device", ONNX_DEVICE),
        )

    def save(self, path: Path) -> None:
        """Save configuration to a YAML file."""
        import yaml
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(self.to_dict(), f)

    @classmethod
    def load(cls, path: Path) -> "BESConfig":
        """Load configuration from a YAML file."""
        import yaml
        if not path.exists():
            # Return default config if file doesn't exist
            return cls()
        with open(path, "r") as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

def get_default_config() -> BESConfig:
    """Return a default BESConfig instance."""
    return BESConfig()

def main():
    """CLI entry point to generate a default config file."""
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Generate BES configuration file.")
    parser.add_argument(
        "--output",
        type=str,
        default="code/bes/bes_config.yaml",
        help="Path to output configuration file.",
    )
    args = parser.parse_args()

    config = get_default_config()
    config.save(Path(args.output))
    print(f"Configuration saved to {args.output}")

if __name__ == "__main__":
    main()