"""
Prompt management module for llmXive.
Loads and manages verified RobotBench prompts for video generation.
"""
import json
import os
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any, Union

# Import utilities from existing project modules
from src.utils.logging import get_logger
from src.utils.io_utils import ensure_dirs

# Configure logger
logger = get_logger(__name__)

# Default paths relative to project root
DEFAULT_PROMPTS_PATH = "data/raw/robotbench_prompts.json"
CACHE_DIR = "data/curated/prompt_cache"

class PromptManager:
    """
    Manages loading, caching, and retrieval of prompts.
    Handles verified RobotBench prompts.
    """

    def __init__(self, prompts_path: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the PromptManager.

        Args:
            prompts_path: Path to the JSON file containing prompts.
            cache_dir: Directory for caching processed prompts.
        """
        self.prompts_path = prompts_path or DEFAULT_PROMPTS_PATH
        self.cache_dir = cache_dir or CACHE_DIR
        self._prompts: List[Dict[str, Any]] = []
        self._loaded = False
        self._metadata: Dict[str, Any] = {}

        # Ensure cache directory exists
        ensure_dirs(Path(self.cache_dir))
        logger.info(f"PromptManager initialized. Prompts source: {self.prompts_path}, Cache: {self.cache_dir}")

    def load_prompts(self) -> List[Dict[str, Any]]:
        """
        Load prompts from the specified JSON file.
        Raises FileNotFoundError if the file does not exist.
        Raises ValueError if the JSON format is invalid.

        Returns:
            List of prompt dictionaries.
        """
        if self._loaded:
            logger.debug("Prompts already loaded, returning cached version.")
            return self._prompts

        prompts_file = Path(self.prompts_path)
        if not prompts_file.exists():
            raise FileNotFoundError(
                f"Verified prompts file not found at: {self.prompts_path}. "
                "Ensure RobotBench prompts have been downloaded to data/raw/."
            )

        logger.info(f"Loading prompts from {self.prompts_path}")
        try:
            with open(prompts_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Handle different possible JSON structures
            if isinstance(data, list):
                self._prompts = data
            elif isinstance(data, dict) and 'prompts' in data:
                self._prompts = data['prompts']
            else:
                raise ValueError(f"Unexpected JSON structure in {self.prompts_path}")

            # Validate structure
            for i, p in enumerate(self._prompts):
                if not isinstance(p, dict):
                    raise ValueError(f"Prompt at index {i} is not a dictionary")
                if 'text' not in p:
                    raise ValueError(f"Prompt at index {i} missing 'text' field")

            self._loaded = True
            self._metadata = {
                'count': len(self._prompts),
                'source': str(prompts_file),
                'checksum': self._calculate_checksum(prompts_file)
            }
            logger.info(f"Successfully loaded {len(self._prompts)} prompts. Checksum: {self._metadata['checksum'][:16]}...")
            return self._prompts

        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format in {self.prompts_path}: {e}")

    def get_prompts(self, limit: Optional[int] = None, seed: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Retrieve prompts, optionally limiting the number and shuffling.

        Args:
            limit: Maximum number of prompts to return.
            seed: Random seed for shuffling (for reproducibility).

        Returns:
            List of prompt dictionaries.
        """
        if not self._loaded:
            self.load_prompts()

        prompts = self._prompts.copy()

        if seed is not None:
            import random
            random.seed(seed)
            random.shuffle(prompts)

        if limit is not None and limit > 0:
            prompts = prompts[:limit]

        return prompts

    def get_prompt_by_id(self, prompt_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific prompt by its ID.

        Args:
            prompt_id: The unique identifier of the prompt.

        Returns:
            The prompt dictionary if found, None otherwise.
        """
        if not self._loaded:
            self.load_prompts()

        for prompt in self._prompts:
            if prompt.get('id') == prompt_id:
                return prompt
        return None

    def get_prompt_texts(self, limit: Optional[int] = None, seed: Optional[int] = None) -> List[str]:
        """
        Retrieve just the text content of prompts.

        Args:
            limit: Maximum number of prompts to return.
            seed: Random seed for shuffling.

        Returns:
            List of prompt text strings.
        """
        prompts = self.get_prompts(limit=limit, seed=seed)
        return [p['text'] for p in prompts]

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of the prompts file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about the loaded prompts."""
        if not self._loaded:
            self.load_prompts()
        return self._metadata.copy()

    def save_cache(self, output_path: Optional[str] = None) -> str:
        """
        Save the current prompts to a cache file.

        Args:
            output_path: Optional path for the cache file. Defaults to cache_dir.

        Returns:
            Path to the saved cache file.
        """
        if not self._loaded:
            self.load_prompts()

        if output_path is None:
            output_path = str(Path(self.cache_dir) / "prompts_cache.json")

        output_file = Path(output_path)
        ensure_dirs(output_file)

        cache_data = {
            'metadata': self._metadata,
            'prompts': self._prompts
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, indent=2)

        logger.info(f"Prompts cache saved to {output_path}")
        return str(output_file)


# Global instance for convenience
_global_prompt_manager: Optional[PromptManager] = None


def get_prompt_manager(prompts_path: Optional[str] = None) -> PromptManager:
    """
    Get or create the global PromptManager instance.

    Args:
        prompts_path: Optional path to override the default prompts file.

    Returns:
        The global PromptManager instance.
    """
    global _global_prompt_manager
    if _global_prompt_manager is None:
        _global_prompt_manager = PromptManager(prompts_path=prompts_path)
    return _global_prompt_manager


def load_robotbench_prompts(prompts_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to load RobotBench prompts.

    Args:
        prompts_path: Optional path to the prompts JSON file.

    Returns:
        List of prompt dictionaries.
    """
    manager = get_prompt_manager(prompts_path)
    return manager.load_prompts()


def get_prompts(limit: Optional[int] = None, seed: Optional[int] = None, prompts_path: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Convenience function to get prompts with optional limiting.

    Args:
        limit: Maximum number of prompts to return.
        seed: Random seed for shuffling.
        prompts_path: Optional path to the prompts JSON file.

    Returns:
        List of prompt dictionaries.
    """
    manager = get_prompt_manager(prompts_path)
    return manager.get_prompts(limit=limit, seed=seed)


def main():
    """Main entry point for testing prompt loading."""
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Try to load from default path
        manager = PromptManager()
        prompts = manager.load_prompts()
        
        logger.info(f"Loaded {len(prompts)} prompts")
        if prompts:
            logger.info(f"First prompt: {prompts[0].get('text', 'N/A')[:100]}...")
            logger.info(f"Metadata: {manager.get_metadata()}")
            
            # Test retrieval
            sample = manager.get_prompts(limit=3)
            logger.info(f"Sample of 3 prompts loaded successfully")
            
    except FileNotFoundError as e:
        logger.error(f"Prompts file not found: {e}")
        logger.info("Expected: data/raw/robotbench_prompts.json must exist with real RobotBench prompts.")
        raise
    except ValueError as e:
        logger.error(f"Invalid prompts format: {e}")
        raise


if __name__ == "__main__":
    main()