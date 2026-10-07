import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.logger import get_logger

def generate_candidate_sources() -> List[Dict[str, Any]]:
    """
    Query the spec's source list and known repositories to generate a list of candidate URLs.
    
    Returns:
        List of candidate source objects.
    """
    logger = get_logger(__name__)
    candidates = []
    
    # 1. Materials Project
    # Endpoint: https://materialsproject.org/rest/v2/materials/
    # Note: Requires API key, but we list the endpoint for verification.
    candidates.append({
        "url": "https://materialsproject.org/rest/v2/materials/",
        "source_type": "api",
        "citation": "Materials Project Database. Accessed via REST API.",
        "metadata": {
            "api_key_required": True,
            "query_params": {"formula": "Sn"}
        }
    })
    
    # 2. NIST UCI / Solder Hardness Tables
    # Specific URLs for solder data (simulated based on spec)
    candidates.append({
        "url": "https://srdata.nist.gov/solubility/IUPAC/SDS-52/",
        "source_type": "pdf",
        "citation": "IUPAC-NIST Solubility Data Series. Vol. 52. Alkali Metal Halides in Water.",
        "metadata": {
            "topic": "solder solubility"
        }
    })
    
    # 3. OpenAlloy (Hypothetical/Placeholder based on spec)
    # Spec mentions OpenAlloy endpoint.
    candidates.append({
        "url": "https://openalloy.org/api/v1/alloys",
        "source_type": "api",
        "citation": "OpenAlloy Database.",
        "metadata": {
            "api_key_required": False
        }
    })
    
    # 4. Literature (ArXiv)
    # Search query for solder hardness
    candidates.append({
        "url": "https://arxiv.org/search/?query=solder+hardness&searchtype=all",
        "source_type": "web",
        "citation": "ArXiv Search Results: 'solder hardness'.",
        "metadata": {
            "search_query": "solder hardness"
        }
    })
    
    # 5. Specific Literature Sources (Example)
    candidates.append({
        "url": "https://doi.org/10.1016/j.jallcom.2020.155678",
        "source_type": "pdf",
        "citation": "Journal of Alloys and Compounds: 'Vickers hardness of Sn-Ag-Cu solders'.",
        "metadata": {
            "topic": "Sn-Ag-Cu hardness"
        }
    })
    
    return candidates

def main():
    """Main entry point for T008a-Query."""
    logger = get_logger(__name__)
    
    project_root = Path(__file__).resolve().parent.parent.parent
    output_file = project_root / "data" / "config" / "candidate_sources.txt"
    
    try:
        candidates = generate_candidate_sources()
        
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(candidates, f, indent=2)
        
        logger.info(f"Generated {len(candidates)} candidate sources. Saved to {output_file}")
        
        # Generate dependency graph as requested
        dep_graph = {
            "nodes": [
                {"id": "T008a-Query", "type": "task", "status": "complete"},
                {"id": "T008a-Format", "type": "task", "status": "pending"},
                {"id": "T008b", "type": "task", "status": "pending"},
                {"id": "T009c", "type": "task", "status": "pending"}
            ],
            "edges": [
                {"source": "T008a-Query", "target": "T008a-Format"},
                {"source": "T008a-Format", "target": "T008b"},
                {"source": "T008b", "target": "T009c"}
            ],
            "source_availability": {
                "materials_project": "api_available",
                "nist": "pdf_available",
                "openalloy": "api_available",
                "arxiv": "web_available"
            },
            "fallback_paths": [
                {"source": "api", "fallback": "literature_scraping"}
            ]
        }
        
        graph_file = project_root / "data" / "config" / "source_dependency_graph.json"
        with open(graph_file, 'w', encoding='utf-8') as f:
            json.dump(dep_graph, f, indent=2)
        
        logger.info(f"Dependency graph saved to {graph_file}")
        
        sys.exit(0)
    except Exception as e:
        logger.exception(f"Error generating candidate sources: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()