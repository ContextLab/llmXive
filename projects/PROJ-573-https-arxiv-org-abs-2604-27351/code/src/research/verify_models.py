"""
Model Verification Script for T006.
Verifies that candidate models for the benchmark are CPU-tractable (< 1 GB weights).
"""
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from huggingface_hub import HfApi, hf_hub_download, model_info
from huggingface_hub.utils import RepositoryNotFoundError, RevisionNotFoundError

logger = logging.getLogger(__name__)

# Constants
MAX_MODEL_SIZE_GB = 1.0
MAX_MODEL_SIZE_MB = MAX_MODEL_SIZE_GB * 1024
RESEARCH_MD_PATH = PROJECT_ROOT / "research.md"
OUTPUT_JSON_PATH = PROJECT_ROOT / "data" / "model_verification_results.json"

# Candidate models to verify based on task description:
# TimeSeries-Transformer, TabPFN, Distilled LLM
CANDIDATE_MODELS = [
    {
        "name": "TimeSeries-Transformer",
        "hf_id": "google/t5-small", # Using T5-small as a proxy for a lightweight transformer often adapted for TS, or a specific small TS model if available. 
        # Note: Specific "TimeSeries-Transformer" on HF might vary. Using a small, verified CPU-tractable transformer as the representative.
        # Alternative: "huggingface/transformers" examples often use small configs.
        # Let's use a concrete small model often used for TS in literature if available, otherwise a generic small one.
        # "nvidia/TimesFormer" is too big. 
        # Let's use "unitary/toxic-bert" or similar small BERT for text, but for TS?
        # Re-reading task: "TimeSeries-Transformer". 
        # Common small TS model: "lucidrains/t5-past-future-prediction" or similar.
        # To be safe and real, we will check a specific small model ID that fits the description or a standard small transformer.
        # Let's use "Salesforce/instructblip" - no, too big.
        # Let's use "hf-internal-testing/tiny-random-bert" for the "Distilled LLM" check logic, but we need real models.
        # Real small models:
        # TabPFN: "tabpfn/tabpfn-v2-400k" (often large) -> "tabpfn/tabpfn-v2-100k" or similar? 
        # Actually, TabPFN is often > 1GB. We must check.
        # Distilled LLM: "distilbert-base-uncased" or "microsoft/phi-1.5" (too big). "TinyLlama/TinyLlama-1.1B-Chat-v1.0" (too big). 
        # "google/gemma-2b" (too big).
        # Let's use specific known small models:
        # 1. TabPFN: "tabpfn/tabpfn-v2-400k" is ~1GB+. Let's try "tabpfn/tabpfn-v2-100k" if exists, or check the big one and report.
        # 2. Distilled LLM: "distilbert-base-uncased" (~250MB).
        # 3. TimeSeries: "nvidia/timesformer" is big. "unitary/toxic-bert" is text.
        # Let's use "hf-internal-testing/tiny-random-bert" as a placeholder for "Distilled LLM" logic if real ones fail, 
        # BUT task says "Real data only". We must try real ones.
        
        # Updated Candidate List based on "CPU tractable < 1GB" requirement:
        # 1. TabPFN: "tabpfn/tabpfn-v2-400k" is ~1.1GB. "tabpfn/tabpfn-v2-100k" might be smaller.
        #    Let's check "tabpfn/tabpfn-v2-400k" and report.
        # 2. Distilled LLM: "distilbert-base-uncased" (250MB).
        # 3. TimeSeries: "google/t5-small" (200MB) used as a lightweight transformer backbone.
        
        "hf_id": "tabpfn/tabpfn-v2-400k" # Will verify size
    },
    {
        "name": "Distilled LLM",
        "hf_id": "distilbert-base-uncased"
    },
    {
        "name": "TimeSeries-Transformer",
        "hf_id": "google/t5-small" # Proxy for lightweight transformer architecture
    }
]

def get_model_size_mb(hf_id: str) -> float:
    """
    Fetches the total size of a model's files from HuggingFace Hub.
    Returns size in MB.
    """
    try:
        api = HfApi()
        info = api.model_info(hf_id)
        
        # Sum up sizes of all files
        total_bytes = 0
        for sibling in info.siblings:
            if sibling.size:
                total_bytes += sibling.size
        
        return total_bytes / (1024 * 1024)
    except (RepositoryNotFoundError, RevisionNotFoundError) as e:
        logger.error(f"Model {hf_id} not found: {e}")
        return -1.0
    except Exception as e:
        logger.error(f"Error fetching info for {hf_id}: {e}")
        return -1.0

def update_research_md(results: List[Dict[str, Any]]) -> bool:
    """
    Updates research.md with the Model Verification section.
    """
    if not RESEARCH_MD_PATH.exists():
        logger.warning(f"research.md not found at {RESEARCH_MD_PATH}. Creating a new section.")
        content = ""
    else:
        content = RESEARCH_MD_PATH.read_text(encoding="utf-8")

    section_marker = "## Model Verification"
    if section_marker in content:
        # Find the section and replace everything until next section or end
        start_idx = content.find(section_marker)
        # Find next section starting with ##
        next_section_idx = content.find("\n## ", start_idx + len(section_marker))
        if next_section_idx == -1:
            next_section_idx = len(content)
        
        new_content = content[:start_idx]
    else:
        new_content = content + "\n\n"
        start_idx = len(new_content)

    # Build the new section
    section_text = f"""## Model Verification

This section documents the verification of model weights for CPU-tractability (< 1 GB).

| Model Name | HF ID | Size (MB) | CPU Tractable (< 1 GB) |
| :--- | :--- | :--- | :--- |
"""
    for res in results:
        status = "✅ Yes" if res.get("cpu_tractable", False) else "❌ No"
        size_str = f"{res['size_mb']:.2f}"
        section_text += f"| {res['model_name']} | {res['hf_id']} | {size_str} | {status} |\n"

    section_text += "\n"

    # Append the new section
    final_content = new_content + section_text + content[next_section_idx:]

    try:
        RESEARCH_MD_PATH.write_text(final_content, encoding="utf-8")
        logger.info("research.md updated successfully.")
        return True
    except Exception as e:
        logger.error(f"Failed to update research.md: {e}")
        return False

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    
    # Ensure data directory exists
    OUTPUT_JSON_PATH.parent.mkdir(parents=True, exist_ok=True)

    results = []
    logger.info(f"Verifying {len(CANDIDATE_MODELS)} models...")

    for model in CANDIDATE_MODELS:
        name = model["name"]
        hf_id = model["hf_id"]
        logger.info(f"Checking {name} ({hf_id})...")
        
        size_mb = get_model_size_mb(hf_id)
        cpu_tractable = 0 <= size_mb < MAX_MODEL_SIZE_MB

        result_entry = {
            "model_name": name,
            "hf_id": hf_id,
            "size_mb": size_mb,
            "cpu_tractable": cpu_tractable
        }
        results.append(result_entry)
        logger.info(f"  -> Size: {size_mb:.2f} MB, CPU Tractable: {cpu_tractable}")

    # Save JSON results
    with open(OUTPUT_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {OUTPUT_JSON_PATH}")

    # Update research.md
    update_research_md(results)

    # Print summary
    print("\n--- Model Verification Summary ---")
    for r in results:
        status = "PASS" if r["cpu_tractable"] else "FAIL"
        print(f"{r['model_name']}: {r['size_mb']:.2f} MB [{status}]")
    
    # Return 0 if all pass, 1 if any fail (for CI gating if needed)
    all_pass = all(r["cpu_tractable"] for r in results)
    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())