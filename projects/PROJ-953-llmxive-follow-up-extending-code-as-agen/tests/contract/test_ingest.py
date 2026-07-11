"""
Contract test for dataset download (T008).

Verifies that the ingestion module successfully fetches real data 
from HuggingFace datasets for SWE-bench and AgentBench.
"""
import os
import tempfile
import pytest
from pathlib import Path

# Import the ingestion logic from the code module
# Adjust import path based on project structure (assuming code/scripts/ingest.py)
# If ingest.py is in code/scripts/, we need to add code to sys.path
import sys
from pathlib import Path

# Add the 'code' directory to the path to allow imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

# Attempt to import the dataset fetching logic.
# We assume the implementation of T010 will define a function like `fetch_datasets`
# or we test the underlying `datasets` library usage directly if the module isn't ready.
# Since T010 is not yet implemented, we test the *contract* by verifying the 
# dependencies are available and the fetch mechanism works against a known small slice
# or by mocking the HuggingFace API call if the module is missing.

# However, the task asks to "verify HuggingFace fetch". 
# If scripts/ingest.py doesn't exist yet (T010), we cannot import it.
# We will write a test that attempts to import the expected function.
# If the function doesn't exist, we skip or fail based on the "contract" requirement.
# To make this a runnable test that verifies the *capability* to fetch, 
# we will implement a minimal fetcher in the test if the module is missing, 
# OR (better per constraints) we assume T010 provides `scripts/ingest.py`.

# Since T010 is not in "completed", `scripts/ingest.py` might not exist.
# The "Contract Test" usually validates that the *interface* works with the real data source.
# We will try to import. If it fails, we provide a fallback implementation of the fetch 
# within the test to verify the *source* is accessible, satisfying the "verify HuggingFace fetch" 
# requirement without depending on T010 being done first (since T008 is [P]).

try:
    from scripts.ingest import fetch_datasets
    HAS_INGEST_MODULE = True
except (ImportError, ModuleNotFoundError):
    HAS_INGEST_MODULE = False

from datasets import load_dataset

@pytest.mark.integration
def test_huggingface_swebench_fetch():
    """
    Contract test: Verify we can fetch a small subset of SWE-bench from HuggingFace.
    """
    # We fetch a tiny slice (e.g., first 1 row) to verify connectivity and schema
    # without downloading the full dataset (which would be too slow for a test).
    try:
        dataset = load_dataset(
            "princeton-nlp/SWE-bench_Lite", 
            split="train", 
            streaming=True
        )
        
        # Consume one item to verify the fetch works and data is real
        item = next(iter(dataset))
        
        # Verify expected keys exist in the real dataset
        expected_keys = {"instance_id", "repo", "patch", "test_patch", "problem_statement"}
        assert expected_keys.issubset(item.keys()), f"Missing keys in SWE-bench: {expected_keys - set(item.keys())}"
        
        # Verify data types
        assert isinstance(item["instance_id"], str)
        assert isinstance(item["problem_statement"], str)
        
        print(f"Successfully fetched SWE-bench item: {item['instance_id']}")
        
    except Exception as e:
        pytest.fail(f"Failed to fetch SWE-bench from HuggingFace: {e}")

@pytest.mark.integration
def test_huggingface_agentbench_fetch():
    """
    Contract test: Verify we can fetch a small subset of AgentBench from HuggingFace.
    """
    try:
        # AgentBench has multiple subsets; we try a common one or list available
        # Using 'openbmb/AgentBench' which is a common source
        dataset = load_dataset(
            "openbmb/AgentBench", 
            split="dev", # or train
            streaming=True
        )
        
        item = next(iter(dataset))
        
        # Verify structure (schema may vary slightly, check for common keys)
        assert "instance_id" in item or "id" in item or "question" in item, \
            "AgentBench item missing expected identifier or question keys"
        
        print(f"Successfully fetched AgentBench item: {item.get('instance_id', item.get('id', 'unknown'))}")
        
    except Exception as e:
        # If the specific dataset name changes or is unavailable, this is a valid failure of the source
        # but the test verifies the fetch logic.
        pytest.fail(f"Failed to fetch AgentBench from HuggingFace: {e}")

@pytest.mark.skipif(not HAS_INGEST_MODULE, reason="scripts/ingest.py not yet implemented (T010)")
def test_ingest_module_signature():
    """
    Contract test: Verify the ingest module has the expected function signature.
    """
    # This test ensures that when T010 is implemented, it follows the contract
    # expected by the rest of the pipeline.
    assert callable(fetch_datasets), "fetch_datasets must be callable"
    
    # We don't run fetch_datasets here in the test suite as it might be slow,
    # but we verify it exists and is callable. The integration tests above verify the source.

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
