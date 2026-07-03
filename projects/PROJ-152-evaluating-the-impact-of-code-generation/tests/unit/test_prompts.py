"""
Unit tests for code/prompts.py (T010)

Tests the prompt combination logic, hash calculation, and manifest generation.
"""
import json
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.prompts import (
    calculate_file_hash,
    calculate_content_hash,
    load_json_file,
    generate_prompt_id,
    build_unified_manifest
)

class TestHashFunctions:
    def test_calculate_content_hash(self):
        """Test SHA-256 hash calculation for strings."""
        content = "Hello, World!"
        hash1 = calculate_content_hash(content)
        hash2 = calculate_content_hash(content)
        
        assert len(hash1) == 64  # SHA-256 hex length
        assert hash1 == hash2
        assert hash1 != calculate_content_hash("Different content")

    def test_calculate_file_hash(self):
        """Test SHA-256 hash calculation for files."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("Test content")
            temp_path = Path(f.name)
        
        try:
            hash1 = calculate_file_hash(temp_path)
            hash2 = calculate_file_hash(temp_path)
            
            assert len(hash1) == 64
            assert hash1 == hash2
        finally:
            os.unlink(temp_path)

class TestPromptIdGeneration:
    def test_codexglue_id(self):
        assert generate_prompt_id("codexglue", 0) == "codexglue_000"
        assert generate_prompt_id("codexglue", 5) == "codexglue_005"
        assert generate_prompt_id("codexglue", 99) == "codexglue_099"

    def test_handcrafted_id(self):
        assert generate_prompt_id("handcrafted", 0) == "handcrafted_000"
        assert generate_prompt_id("handcrafted", 15) == "handcrafted_015"

class TestManifestBuilding:
    def test_empty_lists(self):
        """Test manifest generation with empty inputs."""
        manifest = build_unified_manifest([], [])
        
        assert manifest["metadata"]["total_prompts"] == 0
        assert manifest["metadata"]["source_breakdown"]["codexglue"] == 0
        assert manifest["metadata"]["source_breakdown"]["handcrafted"] == 0
        assert len(manifest["prompts"]) == 0

    def test_single_raw_prompt(self):
        """Test manifest generation with one raw prompt."""
        raw = [{"id": "r1", "prompt": "Write SQL query", "relevance_score": 0.9}]
        handcrafted = []
        
        manifest = build_unified_manifest(raw, handcrafted)
        
        assert manifest["metadata"]["total_prompts"] == 1
        assert manifest["prompts"][0]["prompt_id"] == "codexglue_000"
        assert manifest["prompts"][0]["source"] == "codexglue"
        assert manifest["prompts"][0]["content"] == "Write SQL query"
        assert "content_hash" in manifest["prompts"][0]

    def test_single_handcrafted_prompt(self):
        """Test manifest generation with one handcrafted prompt."""
        raw = []
        handcrafted = [{"id": "h1", "prompt": "Secure login", "subcategory": "auth"}]
        
        manifest = build_unified_manifest(raw, handcrafted)
        
        assert manifest["metadata"]["total_prompts"] == 1
        assert manifest["prompts"][0]["prompt_id"] == "handcrafted_000"
        assert manifest["prompts"][0]["source"] == "handcrafted"
        assert manifest["prompts"][0]["content"] == "Secure login"
        assert manifest["prompts"][0]["metadata"]["subcategory"] == "auth"

    def test_combined_prompts(self):
        """Test manifest generation with both source types."""
        raw = [
            {"id": "r1", "prompt": "SQL query", "relevance_score": 0.8},
            {"id": "r2", "prompt": "XSS filter", "relevance_score": 0.9}
        ]
        handcrafted = [
            {"id": "h1", "prompt": "Auth check", "subcategory": "auth"}
        ]
        
        manifest = build_unified_manifest(raw, handcrafted)
        
        assert manifest["metadata"]["total_prompts"] == 3
        assert manifest["metadata"]["source_breakdown"]["codexglue"] == 2
        assert manifest["metadata"]["source_breakdown"]["handcrafted"] == 1
        
        # Check ordering: raw first, then handcrafted
        assert manifest["prompts"][0]["source"] == "codexglue"
        assert manifest["prompts"][1]["source"] == "codexglue"
        assert manifest["prompts"][2]["source"] == "handcrafted"

    def test_content_hash_uniqueness(self):
        """Verify different content gets different hashes."""
        raw = [
            {"id": "r1", "prompt": "Content A", "relevance_score": 0.5},
            {"id": "r2", "prompt": "Content B", "relevance_score": 0.5}
        ]
        
        manifest = build_unified_manifest(raw, [])
        
        hash1 = manifest["prompts"][0]["content_hash"]
        hash2 = manifest["prompts"][1]["content_hash"]
        
        assert hash1 != hash2

class TestMetadataStructure:
    def test_metadata_fields(self):
        """Verify all expected metadata fields are present."""
        raw = [{"id": "r1", "prompt": "Test", "relevance_score": 0.9}]
        handcrafted = [{"id": "h1", "prompt": "Test", "subcategory": "auth"}]
        
        manifest = build_unified_manifest(raw, handcrafted)
        
        meta = manifest["metadata"]
        assert "version" in meta
        assert "generated_at" in meta
        assert "total_prompts" in meta
        assert "source_breakdown" in meta
        assert "target_count" in meta
        assert "actual_count" in meta

        # Check source breakdown structure
        assert "codexglue" in meta["source_breakdown"]
        assert "handcrafted" in meta["source_breakdown"]