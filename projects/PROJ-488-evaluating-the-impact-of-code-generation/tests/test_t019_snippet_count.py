"""
Tests for T019: Snippet count verification.
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from snippet_counter import main, MIN_SNIPPETS_PER_GROUP, VALIDATED_DIR

def test_count_logic_with_files(tmp_path):
    """
    Simulate the environment where T018 has produced validated files.
    Verify that T019 counts them correctly and passes if >= 1000.
    """
    # Setup temp directories mimicking project structure
    data_dir = tmp_path / "data" / "processed"
    validated_dir = data_dir / "validated"
    validated_dir.mkdir(parents=True)

    # Create mock validated files
    # Human group: 1005 snippets
    human_file = validated_dir / "codesearchnet_validated.jsonl"
    with open(human_file, 'w') as f:
        for i in range(1005):
            f.write(json.dumps({"id": i, "code": "def x(): pass"}) + "\n")

    # LLM group: 1005 snippets
    llm_file = validated_dir / "codegen_validated.jsonl"
    with open(llm_file, 'w') as f:
        for i in range(1005):
            f.write(json.dumps({"id": i, "code": "def y(): pass"}) + "\n")

    # Mock the global path constants in the module
    import snippet_counter
    original_validated_dir = snippet_counter.VALIDATED_DIR
    snippet_counter.VALIDATED_DIR = validated_dir

    try:
        # Run main
        # Since main() calls sys.exit(0) on success, we need to catch SystemExit
        try:
            result = main()
            assert result == 0, "Main should return 0 on success"
        except SystemExit as e:
            assert e.code == 0, f"Expected exit code 0, got {e.code}"
    finally:
        # Restore
        snippet_counter.VALIDATED_DIR = original_validated_dir

def test_count_logic_failure_human(tmp_path):
    """
    Verify T019 fails with error 104 if human count < 1000.
    """
    data_dir = tmp_path / "data" / "processed"
    validated_dir = data_dir / "validated"
    validated_dir.mkdir(parents=True)

    # Human: 999 (Fail)
    human_file = validated_dir / "codesearchnet_validated.jsonl"
    with open(human_file, 'w') as f:
        for i in range(999):
            f.write(json.dumps({"id": i, "code": "def x(): pass"}) + "\n")

    # LLM: 1005
    llm_file = validated_dir / "codegen_validated.jsonl"
    with open(llm_file, 'w') as f:
        for i in range(1005):
            f.write(json.dumps({"id": i, "code": "def y(): pass"}) + "\n")

    import snippet_counter
    original_validated_dir = snippet_counter.VALIDATED_DIR
    snippet_counter.VALIDATED_DIR = validated_dir

    try:
        try:
            main()
            assert False, "Should have exited with code 104"
        except SystemExit as e:
            assert e.code == 104, f"Expected exit code 104, got {e.code}"
    finally:
        snippet_counter.VALIDATED_DIR = original_validated_dir

def test_count_logic_failure_llm(tmp_path):
    """
    Verify T019 fails with error 104 if LLM count < 1000.
    """
    data_dir = tmp_path / "data" / "processed"
    validated_dir = data_dir / "validated"
    validated_dir.mkdir(parents=True)

    # Human: 1005
    human_file = validated_dir / "codesearchnet_validated.jsonl"
    with open(human_file, 'w') as f:
        for i in range(1005):
            f.write(json.dumps({"id": i, "code": "def x(): pass"}) + "\n")

    # LLM: 999 (Fail)
    llm_file = validated_dir / "codegen_validated.jsonl"
    with open(llm_file, 'w') as f:
        for i in range(999):
            f.write(json.dumps({"id": i, "code": "def y(): pass"}) + "\n")

    import snippet_counter
    original_validated_dir = snippet_counter.VALIDATED_DIR
    snippet_counter.VALIDATED_DIR = validated_dir

    try:
        try:
            main()
            assert False, "Should have exited with code 104"
        except SystemExit as e:
            assert e.code == 104, f"Expected exit code 104, got {e.code}"
    finally:
        snippet_counter.VALIDATED_DIR = original_validated_dir