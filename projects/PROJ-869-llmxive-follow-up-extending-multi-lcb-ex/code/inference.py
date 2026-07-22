"""
Inference Engine: Loads the model and generates code.
"""
from code.config import config
from code.utils.logger import get_logger

logger = get_logger(__name__)

def load_model():
    """Load the GGUF model."""
    try:
        from llama_cpp import Llama
        logger.info(f"Loading model from {config.model_path}")
        llm = Llama(
            model_path=config.model_path,
            n_ctx=config.model_max_context,
            n_threads=4,
        )
        return llm
    except ImportError:
        raise RuntimeError("llama-cpp-python not installed.")
    except Exception as e:
        raise RuntimeError(f"Failed to load model: {e}")

def generate_code(llm, prompt: str, temperature: float = 0.0, max_tokens: int = 500) -> str:
    """Generate code from a prompt."""
    try:
        output = llm(
            prompt,
            max_tokens=max_tokens,
            temperature=temperature,
            echo=False,
            stop=["\n\n", "```"] # Simple stop sequences
        )
        return output['choices'][0]['text']
    except Exception as e:
        logger.error(f"Generation error: {e}")
        return ""
