import os
import sys
import subprocess
import logging
from pathlib import Path
import shutil
import tempfile
import psutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_MODEL_ID = "TinyLlama/TinyLlama-1B-Chat-v1.0"
DEFAULT_QUANTIZATION = "q4_0"
GGUF_REPO = "https://github.com/ggerganov/llama.cpp"
GGUF_BRANCH = "master"
GGUF_BUILD_DIR = "code/llama.cpp"
MODEL_OUTPUT_DIR = "data/processed/models"
MEMORY_THRESHOLD_GB = 7.0

def ensure_llama_cpp() -> Path:
    """Ensure llama.cpp is cloned and built."""
    build_dir = Path(GGUF_BUILD_DIR)
    bin_path = build_dir / "bin" / "llama-quantize"
    if not build_dir.exists():
        logger.info(f"Cloning {GGUF_REPO} to {build_dir}...")
        build_dir.mkdir(parents=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", "-b", GGUF_BRANCH, GGUF_REPO, str(build_dir)],
            check=True
        )
    else:
        logger.info(f"llama.cpp already exists at {build_dir}")

    if not bin_path.exists():
        logger.info("Building llama.cpp...")
        # Ensure cmake is available
        try:
            subprocess.run(["cmake", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("cmake is required but not found. Please install cmake and retry.")
            raise RuntimeError("cmake not found")

        subprocess.run(
            ["cmake", "-B", "build", "-DCMAKE_BUILD_TYPE=Release"],
            cwd=build_dir,
            check=True
        )
        subprocess.run(
            ["cmake", "--build", "build", "--config", "Release", "-j"],
            cwd=build_dir,
            check=True
        )
        # Move binary to expected location if build structure differs
        build_bin = build_dir / "build" / "bin" / "llama-quantize"
        if build_bin.exists():
            build_bin.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(build_bin), str(bin_path))
            logger.info(f"Moved binary to {bin_path}")
        else:
            logger.warning(f"Expected binary not found at {bin_path} or {build_bin}, checking build dir...")
            # Fallback search
            for f in build_dir.rglob("llama-quantize*"):
                if f.is_file():
                    bin_path.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(f), str(bin_path))
                    logger.info(f"Found and moved binary from {f} to {bin_path}")
                    break
    
    return bin_path

def build_llama_cpp() -> Path:
    """Build llama.cpp if not already built."""
    return ensure_llama_cpp()

def get_hf_model_path(model_id: str) -> Path:
    """
    Download the model from HuggingFace to a local cache directory.
    Returns the path to the model directory.
    """
    from huggingface_hub import snapshot_download
    
    logger.info(f"Downloading model {model_id} from HuggingFace...")
    try:
        local_dir = Path(MODEL_OUTPUT_DIR) / model_id.replace("/", "_")
        local_dir.mkdir(parents=True, exist_ok=True)
        
        # Download only the necessary files (config, tokenizer, model weights)
        # We exclude large files like training data if any
        allow_patterns = ["*.json", "*.txt", "*.safetensors", "*.bin", "*.model"]
        
        path = snapshot_download(
            repo_id=model_id,
            local_dir=str(local_dir),
            allow_patterns=allow_patterns,
            repo_type="model"
        )
        logger.info(f"Model downloaded to {path}")
        return Path(path)
    except Exception as e:
        logger.error(f"Failed to download model {model_id}: {e}")
        raise

def check_memory_fit(model_path: Path) -> bool:
    """
    Estimate model size and check if it fits within memory threshold.
    This is a heuristic based on file sizes.
    """
    total_size_bytes = 0
    for file in model_path.rglob("*"):
        if file.is_file():
            total_size_bytes += file.stat().st_size
    
    total_size_gb = total_size_bytes / (1024**3)
    logger.info(f"Estimated model size: {total_size_gb:.2f} GB")
    
    if total_size_gb > MEMORY_THRESHOLD_GB:
        logger.warning(f"Model size ({total_size_gb:.2f} GB) exceeds threshold ({MEMORY_THRESHOLD_GB} GB).")
        return False
    return True

def convert_to_gguf(model_path: Path, quantization: str = DEFAULT_QUANTIZATION) -> Path:
    """
    Convert HuggingFace model to GGUF format using llama.cpp.
    """
    quantize_bin = ensure_llama_cpp()
    output_dir = Path(MODEL_OUTPUT_DIR)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine output filename
    model_name = model_path.name.replace("_", "-")
    output_file = output_dir / f"{model_name}-{quantization}.gguf"
    
    # Prepare arguments for llama-convert.py or llama-quantize
    # Note: The standard flow is: download -> convert to GGUF (llama-convert.py) -> quantize
    # However, often llama.cpp provides a script to do this in one go or we use the quantize tool directly on the converted file.
    # Let's assume we first convert to GGUF (fp16) then quantize.
    
    # Step 1: Convert to GGUF (fp16)
    # We need the llama-convert.py script from llama.cpp
    convert_script = Path(GGUF_BUILD_DIR) / "convert.py"
    if not convert_script.exists():
        # Try to find it in the repo
        for f in Path(GGUF_BUILD_DIR).rglob("convert*.py"):
            if f.is_file():
                convert_script = f
                break
    
    if not convert_script.exists():
        logger.error("Could not find convert.py in llama.cpp directory.")
        raise FileNotFoundError("convert.py not found")

    logger.info(f"Converting {model_path} to GGUF (fp16)...")
    temp_gguf = output_dir / f"{model_name}-fp16.gguf"
    
    try:
        subprocess.run(
            [
                sys.executable, str(convert_script),
                "--outfile", str(temp_gguf),
                "--outtype", "f16",
                str(model_path)
            ],
            check=True,
            capture_output=False
        )
        logger.info(f"Converted to {temp_gguf}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Conversion failed: {e}")
        # Fallback: try llama-convert if available
        logger.warning("Trying alternative conversion method if available...")
        raise

    # Step 2: Quantize
    logger.info(f"Quantizing {temp_gguf} to {quantization}...")
    try:
        subprocess.run(
            [
                str(quantize_bin),
                str(temp_gguf),
                str(output_file),
                quantization
            ],
            check=True,
            capture_output=False
        )
        logger.info(f"Quantized model saved to {output_file}")
        
        # Clean up intermediate fp16 file
        if temp_gguf.exists():
            temp_gguf.unlink()
            logger.info(f"Removed intermediate file {temp_gguf}")
            
        return output_file
    except subprocess.CalledProcessError as e:
        logger.error(f"Quantization failed: {e}")
        raise

def quantize_gguf(gguf_path: Path, quantization: str = DEFAULT_QUANTIZATION) -> Path:
    """
    Quantize an existing GGUF file.
    """
    quantize_bin = ensure_llama_cpp()
    output_dir = gguf_path.parent
    output_name = gguf_path.stem + f"-{quantization}.gguf"
    output_file = output_dir / output_name
    
    logger.info(f"Quantizing {gguf_path} to {quantization}...")
    subprocess.run(
        [
            str(quantize_bin),
            str(gguf_path),
            str(output_file),
            quantization
        ],
        check=True
    )
    return output_file

def download_and_quantize(model_id: str = DEFAULT_MODEL_ID, quantization: str = DEFAULT_QUANTIZATION) -> Path:
    """
    Main entry point: Download model, check memory, convert to GGUF, quantize.
    """
    logger.info(f"Starting process for model: {model_id}")
    
    # Check memory
    # Note: We can't know exact size until downloaded, but we can estimate or check after download
    # For safety, we download first, then check size, then convert if it fits.
    # If it doesn't fit, we raise an error as per requirement.
    
    try:
        model_path = get_hf_model_path(model_id)
    except Exception as e:
        logger.error(f"Failed to download model: {e}")
        raise

    if not check_memory_fit(model_path):
        logger.error(f"Model {model_id} is too large for {MEMORY_THRESHOLD_GB}GB limit. Aborting.")
        raise MemoryError(f"Model size exceeds {MEMORY_THRESHOLD_GB}GB threshold")

    gguf_path = convert_to_gguf(model_path, quantization)
    logger.info(f"Successfully created GGUF model at {gguf_path}")
    return gguf_path

def main():
    """
    CLI entry point.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Download and quantize a model to GGUF.")
    parser.add_argument("--model_id", type=str, default=DEFAULT_MODEL_ID, help="HuggingFace model ID")
    parser.add_argument("--quantization", type=str, default=DEFAULT_QUANTIZATION, help="Quantization type (e.g., q4_0)")
    args = parser.parse_args()

    try:
        gguf_path = download_and_quantize(args.model_id, args.quantization)
        logger.info(f"Final GGUF model available at: {gguf_path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
