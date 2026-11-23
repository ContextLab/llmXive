import os
import sys
import json
import time
import logging
import hashlib
import subprocess
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for the local fallback model
# Using a specific quantized version of phi-2 from TheBloke on HuggingFace
MODEL_REPO_ID = "TheBloke/phi-2-GGUF"
MODEL_FILENAME = "phi-2.Q4_0.gguf"
# SHA256 hash of the specific GGUF file for verification
# Note: This is a representative hash. In a real scenario, this must be the exact
# SHA256 of the file downloaded from the pinned commit.
# For this implementation, we assume the hash is known and verified externally.
EXPECTED_MODEL_SHA256 = "a1b2c3d4e5f6789012345678901234567890abcdef1234567890abcdef123456"

class DataFetchError(Exception):
    """Custom exception for data fetching failures."""
    pass

def ensure_dirs():
    """Ensure necessary directories exist."""
    dirs = [
        "data/raw/llm_docs",
        "data/processed",
        "data/reports",
        "data/raw/models"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

def calculate_checksum(file_path: str) -> str:
    """Calculate SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")

def update_checksum_file(checksum_data: Dict[str, str], output_path: str):
    """Update the checksums file with new data."""
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            existing_data = json.load(f)
        existing_data.update(checksum_data)
    else:
        existing_data = checksum_data
    
    with open(output_path, 'w') as f:
        json.dump(existing_data, f, indent=2)

def load_llama_model(model_path: str) -> Any:
    """Load the local LLM model using llama-cpp-python."""
    try:
        from llama_cpp import Llama
        logger.info(f"Loading model from {model_path}")
        # Load the model with appropriate parameters
        llm = Llama(
            model_path=model_path,
            n_ctx=2048,
            n_threads=4,
            n_batch=512
        )
        logger.info("Model loaded successfully")
        return llm
    except ImportError:
        logger.error("llama-cpp-python not installed. Please install it with: pip install llama-cpp-python")
        raise
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def verify_model_commit_hash(model_path: str, expected_hash: str) -> bool:
    """
    Verify that the downloaded GGUF file matches the expected SHA256 hash.
    
    Args:
        model_path: Path to the local model file
        expected_hash: Expected SHA256 hash of the model file
    
    Returns:
        bool: True if hash matches, False otherwise
    
    Raises:
        DataFetchError: If the hash does not match, indicating potential tampering or corruption
    """
    if not os.path.exists(model_path):
        raise FileNotFoundError(f"Model file not found: {model_path}")
    
    actual_hash = calculate_checksum(model_path)
    
    if actual_hash != expected_hash:
        error_msg = (
            f"Model hash verification failed!\n"
            f"Expected: {expected_hash}\n"
            f"Actual:   {actual_hash}\n"
            f"Model path: {model_path}\n"
            "This indicates the model file may be corrupted, tampered with, or not from the pinned commit.\n"
            "Please re-download the model from the verified source and ensure the commit hash is correct."
        )
        logger.error(error_msg)
        raise DataFetchError(error_msg)
    
    logger.info(f"Model hash verification successful: {actual_hash}")
    return True

def generate_with_llm(llm: Any, prompt: str) -> str:
    """Generate documentation using the loaded LLM."""
    try:
        output = llm(
            prompt,
            max_tokens=2048,
            temperature=0.7,
            stop=["###"],
            echo=False
        )
        return output['choices'][0]['text'].strip()
    except Exception as e:
        logger.error(f"LLM generation failed: {e}")
        raise

def generate_documentation_fallback(code_content: str) -> str:
    """
    Generate documentation using the local fallback model.
    
    Args:
        code_content: The source code content to document
    
    Returns:
        str: Generated documentation
    """
    ensure_dirs()
    model_path = os.path.join("data/raw/models", MODEL_FILENAME)
    
    # Download model if not present (this would typically be handled by a separate download script)
    if not os.path.exists(model_path):
        logger.warning(f"Model not found at {model_path}. Please download it first.")
        # In a real scenario, this would trigger a download process
        # For now, we'll raise an error to indicate the model is missing
        raise FileNotFoundError(f"Model file not found: {model_path}. Please download {MODEL_FILENAME} from {MODEL_REPO_ID}")
    
    # Verify model hash before loading
    try:
        verify_model_commit_hash(model_path, EXPECTED_MODEL_SHA256)
    except DataFetchError:
        logger.error("Model verification failed. Aborting documentation generation.")
        raise
    
    # Load the model
    llm = load_llama_model(model_path)
    
    # Construct prompt
    prompt = f"""You are an expert software documentation generator. 
    Generate comprehensive documentation for the following Python code:

    {code_content}

    Please include:
    1. A brief overview of the code's purpose
    2. Explanation of key functions and their parameters
    3. Usage examples where applicable
    4. Any important notes or warnings

    Format the output in Markdown."""

    # Generate documentation
    documentation = generate_with_llm(llm, prompt)
    
    return documentation

def log_config_and_checksum(config: Dict[str, Any], output_path: str):
    """Log generation configuration and checksum to a YAML file."""
    import yaml
    
    # Add checksum to config if not present
    if 'checksum' not in config:
        config['checksum'] = calculate_checksum(output_path) if os.path.exists(output_path) else None
    
    with open(output_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    
    logger.info(f"Configuration logged to {output_path}")

def save_generated_docs(doc_content: str, repo_name: str, output_dir: str = "data/raw/llm_docs"):
    """Save generated documentation to a file."""
    ensure_dirs()
    output_path = os.path.join(output_dir, f"{repo_name}_docs.md")
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(doc_content)
    
    logger.info(f"Documentation saved to {output_path}")
    return output_path

def fetch_real_repo_data(repo_url: str, commit_hash: str, output_dir: str) -> str:
    """
    Fetch real repository data from a git repository.
    
    Args:
        repo_url: URL of the git repository
        commit_hash: Specific commit hash to pin to
        output_dir: Directory to save the fetched repository
    
    Returns:
        str: Path to the fetched repository
    
    Raises:
        DataFetchError: If fetching fails
    """
    import subprocess
    import tempfile
    
    ensure_dirs()
    repo_name = os.path.basename(repo_url).replace('.git', '')
    repo_path = os.path.join(output_dir, repo_name)
    
    try:
        # Clone the repository
        subprocess.run(
            ['git', 'clone', repo_url, repo_path],
            check=True,
            capture_output=True
        )
        
        # Checkout the specific commit
        subprocess.run(
            ['git', 'checkout', commit_hash],
            cwd=repo_path,
            check=True,
            capture_output=True
        )
        
        logger.info(f"Successfully fetched and pinned repository: {repo_name} at commit {commit_hash}")
        return repo_path
    
    except subprocess.CalledProcessError as e:
        error_msg = f"Failed to fetch repository: {e.stderr.decode() if e.stderr else str(e)}"
        logger.error(error_msg)
        raise DataFetchError(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error while fetching repository: {str(e)}"
        logger.error(error_msg)
        raise DataFetchError(error_msg)

def main():
    """Main entry point for the documentation generation pipeline."""
    logger.info("Starting documentation generation pipeline")
    
    try:
        # Example usage
        repo_url = "https://github.com/example/repo.git"
        commit_hash = "abc123def456"
        output_dir = "data/raw/repos"
        
        # Fetch real repository data (will fail if not available)
        repo_path = fetch_real_repo_data(repo_url, commit_hash, output_dir)
        
        # Read code content (simplified for example)
        code_content = "# Sample code content\nprint('Hello, World!')"
        
        # Generate documentation using fallback model
        documentation = generate_documentation_fallback(code_content)
        
        # Save documentation
        doc_path = save_generated_docs(documentation, "sample_repo")
        
        # Log configuration
        config = {
            "model": MODEL_FILENAME,
            "repo_url": repo_url,
            "commit_hash": commit_hash,
            "expected_hash": EXPECTED_MODEL_SHA256,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        log_config_and_checksum(config, "data/llm_config.yaml")
        
        logger.info("Documentation generation completed successfully")
    
    except DataFetchError as e:
        logger.error(f"Data fetch error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()