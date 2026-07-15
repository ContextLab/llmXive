"""
state.py - Artifact Hashing and Versioning

Implements Constitution Principle V: All artifacts must be cryptographically hashed
and versioned to ensure reproducibility and traceability.

This module provides utilities to:
1. Compute deterministic SHA-256 hashes for files and directories.
2. Generate version identifiers based on content hashes.
3. Track artifact lineage (dependencies and outputs).
4. Persist version manifests to disk.
"""

import hashlib
import json
import os
import pickle
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from config import Config, Paths


@dataclass
class ArtifactManifest:
    """
    Manifest for a single artifact, capturing its content hash,
    metadata, and lineage.
    """
    artifact_id: str
    file_path: str
    content_hash: str
    file_size_bytes: int
    created_at: str
    version: str
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    source_type: str = "generated"  # options: generated, downloaded, raw


class StateManager:
    """
    Manages artifact hashing, versioning, and manifest persistence.
    Ensures all outputs adhere to Constitution Principle V.
    """

    def __init__(self, config: Config, paths: Optional[Paths] = None):
        self.config = config
        self.paths = paths or config.paths
        self._manifest_cache: Dict[str, ArtifactManifest] = {}
        self._version_counter: Dict[str, int] = {}

    def _compute_file_hash(self, file_path: Union[str, Path]) -> str:
        """
        Computes the SHA-256 hash of a file's contents.
        Reads in chunks to handle large files without memory overflow.
        """
        sha256_hash = hashlib.sha256()
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Cannot hash non-existent file: {path}")

        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def _compute_directory_hash(self, dir_path: Union[str, Path]) -> str:
        """
        Computes a deterministic hash for a directory by hashing
        sorted file paths and their individual hashes.
        """
        dir_hash = hashlib.sha256()
        path = Path(dir_path)
        if not path.exists():
            raise FileNotFoundError(f"Cannot hash non-existent directory: {path}")

        # Sort files to ensure deterministic order
        files = sorted(path.rglob("*"))

        for file_path in files:
            if file_path.is_file():
                # Include relative path in hash to catch moves
                rel_path = file_path.relative_to(path)
                dir_hash.update(str(rel_path).encode("utf-8"))
                # Include content hash
                file_hash = self._compute_file_hash(file_path)
                dir_hash.update(file_hash.encode("utf-8"))

        return dir_hash.hexdigest()

    def _get_next_version(self, artifact_id: str) -> str:
        """
        Generates a version string for a given artifact ID.
        Format: v{count}
        """
        if artifact_id not in self._version_counter:
            self._version_counter[artifact_id] = 0
        else:
            self._version_counter[artifact_id] += 1

        return f"v{self._version_counter[artifact_id]}"

    def register_artifact(
        self,
        file_path: Union[str, Path],
        artifact_id: str,
        source_type: str = "generated",
        dependencies: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ArtifactManifest:
        """
        Registers a new artifact by computing its hash and creating a manifest.

        Args:
            file_path: Path to the artifact file.
            artifact_id: Unique identifier for this type of artifact (e.g., 'codebook_v0').
            source_type: 'generated', 'downloaded', or 'raw'.
            dependencies: List of artifact_ids this artifact depends on.
            metadata: Additional key-value metadata.

        Returns:
            The created ArtifactManifest.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Artifact not found at registration: {path}")

        content_hash = self._compute_file_hash(path)
        version = self._get_next_version(artifact_id)
        timestamp = datetime.utcnow().isoformat()

        manifest = ArtifactManifest(
            artifact_id=artifact_id,
            file_path=str(path.resolve()),
            content_hash=content_hash,
            file_size_bytes=path.stat().st_size,
            created_at=timestamp,
            version=version,
            dependencies=dependencies or [],
            metadata=metadata or {},
            source_type=source_type,
        )

        self._manifest_cache[artifact_id] = manifest
        return manifest

    def save_manifest(
        self, manifest: ArtifactManifest, output_dir: Optional[Union[str, Path]] = None
    ) -> Path:
        """
        Saves an artifact manifest to a JSON file.
        Default location: {paths.results}/manifests/{artifact_id}_{version}.json
        """
        if output_dir is None:
            output_dir = self.paths.results / "manifests"

        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{manifest.artifact_id}_{manifest.version}.json"
        output_path = output_dir / filename

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(asdict(manifest), f, indent=2)

        return output_path

    def load_manifest(self, artifact_id: str, version: str) -> ArtifactManifest:
        """
        Loads a manifest from disk.
        """
        manifest_path = (
            self.paths.results / "manifests" / f"{artifact_id}_{version}.json"
        )
        if not manifest_path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        return ArtifactManifest(**data)

    def verify_artifact(self, artifact_id: str, version: str) -> bool:
        """
        Verifies that an artifact's current content hash matches its manifest.
        Returns True if valid, False otherwise.
        """
        try:
            manifest = self.load_manifest(artifact_id, version)
            current_hash = self._compute_file_hash(manifest.file_path)
            return current_hash == manifest.content_hash
        except (FileNotFoundError, KeyError) as e:
            # Log error in real implementation
            return False

    def generate_lineage_report(self, artifact_id: str, version: str) -> Dict[str, Any]:
        """
        Generates a report showing the full lineage of an artifact,
        including all dependencies recursively.
        """
        report = {
            "root": f"{artifact_id}:{version}",
            "lineage": [],
        }

        def traverse(aid: str, ver: str, depth: int = 0):
            try:
                manifest = self.load_manifest(aid, ver)
                entry = {
                    "id": aid,
                    "version": ver,
                    "hash": manifest.content_hash,
                    "source": manifest.source_type,
                    "dependencies": manifest.dependencies,
                }
                report["lineage"].append(entry)

                for dep_id in manifest.dependencies:
                    # We need to find the version of the dependency.
                    # In a real system, the manifest would store the specific version ID
                    # or we would need a lookup table. For now, we assume latest or
                    # require explicit versioning in dependencies.
                    # Here we just note the ID.
                    traverse(dep_id, "unknown", depth + 1)
            except FileNotFoundError:
                report["lineage"].append({
                    "id": aid,
                    "version": ver,
                    "status": "MISSING"
                })

        traverse(artifact_id, version)
        return report

    def hash_python_source(self, module_name: str) -> str:
        """
        Computes a hash for a Python source module based on its file content.
        Used for versioning code artifacts.
        """
        # Assuming code/ is in the same structure as config.paths
        code_dir = self.paths.code
        module_path = code_dir / f"{module_name}.py"
        return self._compute_file_hash(module_path)

    def save_code_snapshot(self, artifact_id: str, module_names: List[str]) -> ArtifactManifest:
        """
        Creates a manifest snapshot for a set of code modules.
        """
        # We create a temporary file or dict to hash the state of the code
        snapshot_data = {}
        for mod in module_names:
            try:
                h = self.hash_python_source(mod)
                snapshot_data[mod] = h
            except FileNotFoundError:
                snapshot_data[mod] = "NOT_FOUND"

        # Create a temp file to hash the combined state
        temp_path = self.paths.results / "temp_code_snapshot.json"
        temp_path.parent.mkdir(parents=True, exist_ok=True)
        with open(temp_path, "w") as f:
            json.dump(snapshot_data, f)

        manifest = self.register_artifact(
            file_path=temp_path,
            artifact_id=artifact_id,
            source_type="generated",
            metadata={"modules": module_names},
        )
        
        # Clean up temp file after registration (hash is already computed)
        temp_path.unlink()
        return manifest

def get_state_manager(config: Optional[Config] = None) -> StateManager:
    """
    Factory function to get a configured StateManager.
    """
    if config is None:
        from config import Config
        config = Config()
    return StateManager(config)