import os
import json
from pathlib import Path
from typing import Any, Dict, Optional, List
from dataclasses import dataclass, field
from utils.logging_config import get_logger, fail_loudly

logger = get_logger(__name__)

@dataclass
class ProjectConfig:
    """Centralized project configuration holder."""
    project_root: Path
    data_dir: Path
    code_dir: Path
    state_dir: Path
    checksums_path: Path
    max_memory_gb: float = 7.0
    batch_size: int = 32
    log_level: str = "INFO"
    device: str = "cpu"
    use_streaming: bool = True
    max_frames_per_clip: int = 64
    subsample_rate: float = 1.0  # 1.0 = no subsampling

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_root": str(self.project_root),
            "data_dir": str(self.data_dir),
            "code_dir": str(self.code_dir),
            "state_dir": str(self.state_dir),
            "checksums_path": str(self.checksums_path),
            "max_memory_gb": self.max_memory_gb,
            "batch_size": self.batch_size,
            "log_level": self.log_level,
            "device": self.device,
            "use_streaming": self.use_streaming,
            "max_frames_per_clip": self.max_frames_per_clip,
            "subsample_rate": self.subsample_rate,
        }

def load_env_config() -> Dict[str, str]:
    """Load environment variables relevant to the project."""
    return {
        key: os.environ.get(key)
        for key in [
            "PROJECT_ROOT",
            "DATA_DIR",
            "CODE_DIR",
            "STATE_DIR",
            "MAX_MEMORY_GB",
            "BATCH_SIZE",
            "LOG_LEVEL",
            "DEVICE",
            "USE_STREAMING",
            "MAX_FRAMES_PER_CLIP",
            "SUBSAMPLE_RATE",
        ]
    }

def initialize_project_config() -> ProjectConfig:
    """
    Initialize the ProjectConfig by reading environment variables or using defaults.
    Ensures all required directories exist.
    """
    env_vars = load_env_config()
    root = Path(env_vars.get("PROJECT_ROOT", "."))
    data_dir = Path(env_vars.get("DATA_DIR", root / "data"))
    code_dir = Path(env_vars.get("CODE_DIR", root / "code"))
    state_dir = Path(env_vars.get("STATE_DIR", root / "state"))
    checksums_path = data_dir / ".checksums.json"

    # Ensure directories exist
    data_dir.mkdir(parents=True, exist_ok=True)
    code_dir.mkdir(parents=True, exist_ok=True)
    state_dir.mkdir(parents=True, exist_ok=True)

    # Parse numeric env vars
    max_mem = float(env_vars.get("MAX_MEMORY_GB", 7.0))
    batch = int(env_vars.get("BATCH_SIZE", 32))
    log_lvl = env_vars.get("LOG_LEVEL", "INFO")
    device = env_vars.get("DEVICE", "cpu")
    stream = env_vars.get("USE_STREAMING", "true").lower() == "true"
    max_frames = int(env_vars.get("MAX_FRAMES_PER_CLIP", 64))
    subsample = float(env_vars.get("SUBSAMPLE_RATE", 1.0))

    config = ProjectConfig(
        project_root=root,
        data_dir=data_dir,
        code_dir=code_dir,
        state_dir=state_dir,
        checksums_path=checksums_path,
        max_memory_gb=max_mem,
        batch_size=batch,
        log_level=log_lvl,
        device=device,
        use_streaming=stream,
        max_frames_per_clip=max_frames,
        subsample_rate=subsample,
    )
    logger.info(f"Project configuration initialized at {root}")
    return config

def initialize_checksums_file(config: ProjectConfig) -> None:
    """
    Initialize the checksums file if it does not exist.
    Creates the structure: {"checksums": {}, "last_updated": null, "version": "1.0"}
    """
    if not config.checksums_path.exists():
        logger.info(f"Initializing checksums file at {config.checksums_path}")
        data = {
            "checksums": {},
            "last_updated": None,
            "version": "1.0",
        }
        with open(config.checksums_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    else:
        logger.debug(f"Checksums file already exists at {config.checksums_path}")

def update_checksums(config: ProjectConfig, file_paths: List[Path], force: bool = False) -> Dict[str, str]:
    """
    Update the checksums file with SHA-256 hashes for the provided file paths.
    
    Args:
        config: The project configuration.
        file_paths: List of absolute or relative paths to files to hash.
        force: If True, overwrite existing checksums regardless of current state.
    
    Returns:
        The updated dictionary of checksums.
    """
    if not config.checksums_path.exists():
        initialize_checksums_file(config)

    with open(config.checksums_path, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    checksums = current_data.get("checksums", {})
    updated = False

    for file_path in file_paths:
        abs_path = file_path.resolve()
        if not abs_path.exists():
            fail_loudly(f"File not found for checksum update: {abs_path}")

        import hashlib
        sha256_hash = hashlib.sha256()
        with open(abs_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        new_hash = sha256_hash.hexdigest()
        rel_path = str(abs_path.relative_to(config.project_root))
        
        if force or checksums.get(rel_path) != new_hash:
            checksums[rel_path] = new_hash
            updated = True
            logger.info(f"Updated checksum for {rel_path}")

    if updated:
        current_data["checksums"] = checksums
        current_data["last_updated"] = str(Path.cwd().resolve()) # Using current time placeholder or actual timestamp
        import datetime
        current_data["last_updated"] = datetime.datetime.now().isoformat()
        
        with open(config.checksums_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2)
    
    return checksums

def verify_checksums(config: ProjectConfig, file_paths: List[Path]) -> bool:
    """
    Verify the integrity of files against the stored checksums.
    
    Returns:
        True if all files match their stored checksums, False otherwise.
    """
    if not config.checksums_path.exists():
        fail_loudly(f"Checksums file not found at {config.checksums_path}")

    with open(config.checksums_path, "r", encoding="utf-8") as f:
        current_data = json.load(f)

    checksums = current_data.get("checksums", {})
    all_valid = True

    for file_path in file_paths:
        abs_path = file_path.resolve()
        rel_path = str(abs_path.relative_to(config.project_root))
        
        if rel_path not in checksums:
            logger.warning(f"No checksum found for {rel_path}, skipping verification.")
            continue

        import hashlib
        sha256_hash = hashlib.sha256()
        with open(abs_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        
        current_hash = sha256_hash.hexdigest()
        stored_hash = checksums[rel_path]

        if current_hash != stored_hash:
            logger.error(f"Checksum mismatch for {rel_path}: expected {stored_hash}, got {current_hash}")
            all_valid = False
        else:
            logger.debug(f"Checksum verified for {rel_path}")

    if all_valid:
        logger.info("All checksums verified successfully.")
    else:
        logger.error("Checksum verification failed for some files.")
    
    return all_valid

def get_config() -> ProjectConfig:
    """
    Singleton-like getter for the project configuration.
    In a real script, this would typically be initialized once at startup.
    """
    # For simplicity in this module, we re-initialize or cache. 
    # In a larger app, use a module-level variable.
    return initialize_project_config()
