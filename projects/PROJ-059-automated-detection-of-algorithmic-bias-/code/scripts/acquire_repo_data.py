import os
import sys
import logging
from pathlib import Path
from typing import Generator, Dict, Any

try:
    from datasets import load_dataset
except ImportError:
    raise ImportError(
        "The 'datasets' library is required. "
        "Install it via: pip install datasets"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

def stream_python_files() -> Generator[Dict[str, Any], None, None]:
    """
    Stream Python files from the codeparrot/github-code dataset.
    
    Yields:
        Dict containing 'repo_id', 'file_path', 'content' for each Python file.
    
    Raises:
        RuntimeError: If the dataset fetch fails.
    """
    logger.info("Initializing stream from codeparrot/github-code dataset...")
    
    try:
        # Load the dataset in streaming mode to avoid memory overload
        # We filter for Python files based on the 'language' field
        ds = load_dataset(
            'codeparrot/github-code',
            split='train',
            streaming=True,
            trust_remote_code=True
        )
    except Exception as e:
        logger.error(f"Failed to load dataset: {e}")
        raise RuntimeError(
            f"CRITICAL: Failed to fetch real data from codeparrot/github-code. "
            f"Task requires real data. Error: {e}"
        ) from e

    count = 0
    for item in ds:
        # Filter for Python files
        if item.get('language') == 'python':
            count += 1
            yield {
                'repo_id': item.get('repo_id', 'unknown'),
                'file_path': item.get('path', 'unknown'),
                'content': item.get('content', '')
            }
            if count >= 500:
                logger.info(f"Successfully retrieved 500 Python files.")
                break
    
    if count < 500:
        logger.warning(f"Only retrieved {count} Python files. Less than target 500.")

def save_repo_content(stream: Generator[Dict[str, Any], None, None], output_dir: Path):
    """
    Saves the content of streamed Python files into the output directory.
    
    Structure:
        data/raw/{repo_id}/{file_path}
    
    Args:
        stream: Generator of file dictionaries.
        output_dir: Base directory to save files.
    
    Raises:
        RuntimeError: If saving fails.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Saving files to {output_dir}")

    saved_count = 0
    for item in stream:
        repo_id = item['repo_id']
        file_path = item['file_path']
        content = item['content']

        if not content:
            continue

        # Construct safe path
        repo_dir = output_dir / repo_id
        repo_dir.mkdir(parents=True, exist_ok=True)
        
        target_path = repo_dir / file_path
        
        try:
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content, encoding='utf-8')
            saved_count += 1
        except Exception as e:
            logger.error(f"Failed to save {target_path}: {e}")
            # Continue processing other files unless critical

        if saved_count % 50 == 0:
            logger.info(f"Saved {saved_count} files...")

    logger.info(f"Total files saved: {saved_count}")

def main():
    """
    Main entry point for acquiring repository data.
    
    This function streams 500 Python repositories from the Hugging Face
    codeparrot/github-code dataset and saves them to data/raw.
    
    It FAILS LOUDLY if the dataset cannot be accessed.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / 'data' / 'raw'
    
    logger.info(f"Target directory: {output_dir}")
    
    # Stream data
    stream = stream_python_files()
    
    # Save to disk
    save_repo_content(stream, output_dir)
    
    logger.info("Data acquisition complete.")

if __name__ == '__main__':
    main()