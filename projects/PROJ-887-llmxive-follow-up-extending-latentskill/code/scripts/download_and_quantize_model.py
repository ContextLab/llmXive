import os
import sys
import subprocess
import logging
from pathlib import Path
import shutil
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MODEL_NAME = "TinyLlama-1.1B-Chat-v1.0"
MODEL_REPO = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
QUANTIZATION_TYPE = "q4_0"
OUTPUT_DIR = Path("data/models")
OUTPUT_FILE = OUTPUT_DIR / f"tinyllama-1.1b-{QUANTIZATION_TYPE}.gguf"
LLAMA_CPP_REPO = "https://github.com/ggerganov/llama.cpp.git"
LLAMA_CPP_DIR = Path("llama.cpp")
MAX_MEMORY_GB = 7.0
RAM_LIMIT_GB = 6.5  # Safety margin

def ensure_llama_cpp():
    """Clone llama.cpp if not present."""
    if not LLAMA_CPP_DIR.exists():
        logger.info(f"Cloning llama.cpp to {LLAMA_CPP_DIR}...")
        subprocess.run(
            ["git", "clone", "--depth", "1", LLAMA_CPP_REPO, str(LLAMA_CPP_DIR)],
            check=True
        )
    else:
        logger.info(f"llama.cpp already exists at {LLAMA_CPP_DIR}")

    # Ensure build directory exists
    build_dir = LLAMA_CPP_DIR / "bin"
    if not build_dir.exists():
        build_dir.mkdir(parents=True, exist_ok=True)

    # Build llama.cpp if quantize tool is missing
    quantize_path = build_dir / "llama-quantize"
    if not quantize_path.exists():
        logger.info("Building llama.cpp...")
        # Build the main tools
        subprocess.run(
            ["cmake", "-B", "build", "-S", "."],
            cwd=str(LLAMA_CPP_DIR),
            check=True
        )
        subprocess.run(
            ["cmake", "--build", "build", "--config", "Release", "-j"],
            cwd=str(LLAMA_CPP_DIR),
            check=True
        )
        # Move the quantize tool to bin for easier access
        src_quantize = LLAMA_CPP_DIR / "build" / "bin" / "llama-quantize"
        if src_quantize.exists():
            shutil.copy(src_quantize, quantize_path)
            logger.info(f"Copied llama-quantize to {quantize_path}")
        else:
            # Try to find it in the build tree
            found = list((LLAMA_CPP_DIR / "build").rglob("llama-quantize"))
            if found:
                shutil.copy(found[0], quantize_path)
                logger.info(f"Copied llama-quantize from {found[0]} to {quantize_path}")
            else:
                raise RuntimeError("llama-quantize not found after build")
    else:
        logger.info(f"llama-quantize already exists at {quantize_path}")

    return quantize_path

def build_llama_cpp():
    """Ensure llama.cpp is built and quantize tool is available."""
    return ensure_llama_cpp()

def get_hf_model_path():
    """Download the model from Hugging Face using huggingface-hub."""
    try:
        from huggingface_hub import snapshot_download
    except ImportError:
        logger.error("huggingface-hub is not installed. Run: pip install huggingface-hub")
        sys.exit(1)

    logger.info(f"Downloading {MODEL_NAME} from {MODEL_REPO}...")
    # Download the model files (safetensors or pytorch)
    # We specifically need the model weights
    local_dir = Path("hf_cache") / MODEL_NAME.replace("/", "_")
    local_dir.mkdir(parents=True, exist_ok=True)

    try:
        snapshot_download(
            repo_id=MODEL_REPO,
            local_dir=str(local_dir),
            allow_patterns=["*.safetensors", "*.json", "*.txt", "tokenizer*"],
            ignore_patterns=["*.pt", "*.bin"] # Prefer safetensors
        )
        logger.info(f"Downloaded model to {local_dir}")
        return local_dir
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        # Fallback: try to find existing cache if any
        raise RuntimeError(f"Could not download model {MODEL_NAME}: {e}")

def convert_to_gguf(model_dir, quantize_tool):
    """Convert the HF model to GGUF format."""
    gguf_file = model_dir / "model.gguf"
    
    # Find the convert script in llama.cpp
    convert_script = LLAMA_CPP_DIR / "convert.py"
    if not convert_script.exists():
        # Try to find it in the repo
        found = list(LLAMA_CPP_DIR.rglob("convert.py"))
        if found:
            convert_script = found[0]
        else:
            raise RuntimeError("convert.py not found in llama.cpp")

    logger.info(f"Converting {model_dir} to GGUF...")
    
    # Run conversion
    cmd = [
        sys.executable, str(convert_script),
        str(model_dir),
        "--outfile", str(gguf_file)
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Conversion successful: {gguf_file}")
        return gguf_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Conversion failed: {e}")
        raise

def quantize_gguf(gguf_file, quantize_tool, output_path, quantization_type):
    """Quantize the GGUF model."""
    if not gguf_file.exists():
        raise FileNotFoundError(f"GGUF file not found: {gguf_file}")
    
    if not quantize_tool.exists():
        raise FileNotFoundError(f"Quantize tool not found: {quantize_tool}")

    logger.info(f"Quantizing {gguf_file} to {quantization_type}...")
    
    cmd = [
        str(quantize_tool),
        str(gguf_file),
        str(output_path),
        quantization_type
    ]
    
    try:
        # Check memory before running
        import psutil
        process = psutil.Process()
        mem_gb = process.memory_info().rss / (1024 ** 3)
        logger.info(f"Current process memory usage: {mem_gb:.2f} GB")
        
        if mem_gb > RAM_LIMIT_GB:
            logger.warning(f"Current memory usage ({mem_gb:.2f} GB) exceeds limit ({RAM_LIMIT_GB} GB). Proceeding with caution.")
        
        subprocess.run(cmd, check=True)
        logger.info(f"Quantization successful: {output_path}")
        
        # Verify file size
        file_size_gb = output_path.stat().st_size / (1024 ** 3)
        logger.info(f"Output file size: {file_size_gb:.2f} GB")
        
        if file_size_gb > MAX_MEMORY_GB:
            logger.warning(f"Output file size ({file_size_gb:.2f} GB) exceeds RAM limit ({MAX_MEMORY_GB} GB). Inference may fail.")
        
        return output_path
    except subprocess.CalledProcessError as e:
        logger.error(f"Quantization failed: {e}")
        raise

def download_and_quantize():
    """Main workflow: download, convert, quantize."""
    # Ensure output directory exists
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Ensure llama.cpp is ready
    quantize_tool = build_llama_cpp()

    # Step 2: Download model from Hugging Face
    try:
        # Try to use huggingface_hub if available
        model_dir = get_hf_model_path()
    except ImportError:
        logger.error("huggingface-hub not installed. Cannot download model.")
        sys.exit(1)
    except RuntimeError as e:
        logger.error(f"Failed to download model: {e}")
        sys.exit(1)

    # Step 3: Convert to GGUF
    try:
        gguf_file = convert_to_gguf(model_dir, quantize_tool)
    except Exception as e:
        logger.error(f"Conversion failed: {e}")
        sys.exit(1)

    # Step 4: Quantize
    try:
        final_output = quantize_gguf(gguf_file, quantize_tool, OUTPUT_FILE, QUANTIZATION_TYPE)
        logger.info(f"Final model ready at: {final_output}")
        return final_output
    except Exception as e:
        logger.error(f"Quantization failed: {e}")
        sys.exit(1)

def main():
    """Entry point for the script."""
    logger.info("Starting model download and quantization...")
    start_time = time.time()
    
    try:
        output_path = download_and_quantize()
        elapsed = time.time() - start_time
        logger.info(f"Completed in {elapsed:.2f} seconds. Output: {output_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
