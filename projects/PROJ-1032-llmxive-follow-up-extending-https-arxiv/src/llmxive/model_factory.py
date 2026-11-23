"""Model factory for loading Phi-2 and Qwen1.5 with quantization."""
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
from src.llmxive.exceptions import ERR_CPU_LOAD_FAIL
import logging

SUPPORTED_MODELS = {
    "phi-2": "microsoft/phi-2",
    "qwen1.5-1.8b": "Qwen/Qwen1.5-1.8B"
}

def load_model(model_id: str, device: str = "cpu"):
    """Load a model with 8-bit quantization for CPU."""
    if model_id not in SUPPORTED_MODELS:
        raise ValueError(f"Unsupported model: {model_id}. Supported: {list(SUPPORTED_MODELS.keys())}")
    
    model_name = SUPPORTED_MODELS[model_id]
    
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        # Configure 8-bit quantization
        bnb_config = BitsAndBytesConfig(
            load_in_8bit=True,
            llm_int8_enable_fp32_cpu_offload=True,
            llm_int8_has_fp16_weight=False,
            llm_int8_skip_modules=["lm_head"]
        )
        
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            quantization_config=bnb_config,
            device_map="auto" if device == "cuda" else None,
            torch_dtype=torch.float16 if device == "cuda" else torch.float32,
            trust_remote_code=True
        )
        
        if device == "cpu":
            model = model.to("cpu")
        
        return model, tokenizer
        
    except Exception as e:
        logging.error(f"Failed to load model {model_name}: {str(e)}")
        raise ERR_CPU_LOAD_FAIL(f"CPU load failed for {model_name}: {str(e)}")

def get_model_size_info(model_id: str) -> dict:
    """Get approximate model size information."""
    sizes = {
        "phi-2": {"params": "2.7B", "ram_gb": 4.5},
        "qwen1.5-1.8b": {"params": "1.8B", "ram_gb": 3.2}
    }
    return sizes.get(model_id, {"params": "unknown", "ram_gb": 0})
