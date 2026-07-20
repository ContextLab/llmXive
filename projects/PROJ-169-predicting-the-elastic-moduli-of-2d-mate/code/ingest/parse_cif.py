"""
CIF parser for converting CIF files to MaterialGraph objects.
"""
from __future__ import annotations

import os
import json
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

from pymatgen.io.cif import CifParser
from pymatgen.core import Structure
from pymatgen.analysis.elasticity import ElasticTensor

from data_models.material_graph import MaterialGraph
from ingest.bias_check import ExclusionReason

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def get_atomic_properties(structure: Structure) -> Dict[str, Any]:
    """Extract atomic properties from a pymatgen Structure."""
    # Placeholder: extract some basic properties
    return {
        "num_atoms": len(structure),
        "composition": structure.composition.formula,
        "space_group": structure.get_space_group_info()[0] if structure.get_space_group_info()[0] else "Unknown"
    }

def parse_cif_file(cif_path: Path) -> Tuple[Optional[MaterialGraph], Optional[ExclusionReason]]:
    """Parse a single CIF file into a MaterialGraph."""
    try:
        parser = CifParser(str(cif_path))
        structures = parser.parse_structures()
        if not structures:
            return None, ExclusionReason(
                material_id=cif_path.stem,
                reason="No structure found in CIF",
                category="parse"
            )
        
        structure = structures[0] # Take the first structure
        
        # Extract elastic tensor if available (from CIF or metadata)
        # This is a simplification. Real data might have elastic tensor in a separate file or CIF tag.
        # For now, assume we have a placeholder or extract from structure if possible.
        # In a real scenario, we'd look for 'elastic_tensor' in the CIF or a sidecar file.
        elastic_tensor = None
        # Try to get from CIF data if present
        # This part is highly dependent on the data source format.
        # We'll assume for now that we can't get it from CIF directly and it's missing,
        # so we'll return a graph with None target_moduli and let the filter handle it.
        # Or, we assume the target_moduli is provided elsewhere and we just parse the structure.
        
        # For the purpose of this task, we'll create a graph with placeholder target_moduli
        # and let the filter step handle the validation.
        target_moduli = [0.0] * 6 # Placeholder
        
        graph = MaterialGraph(
            node_features=[], # Placeholder, would be derived from structure
            edge_features=[], # Placeholder
            target_moduli=target_moduli,
            family_id=structure.get_space_group_info()[0] if structure.get_space_group_info()[0] else "Unknown",
            material_id=cif_path.stem,
            structure_summary=get_atomic_properties(structure)
        )
        
        # Populate node/edge features based on structure (simplified)
        # This is a placeholder. Real implementation would use featurizers.
        graph.node_features = [1.0] * len(structure) # Example
        graph.edge_features = [1.0] # Example
        
        return graph, None

    except Exception as e:
        logger.error(f"Error parsing CIF {cif_path}: {e}")
        return None, ExclusionReason(
            material_id=cif_path.stem,
            reason=f"Parsing error: {str(e)}",
            category="parse"
        )

def parse_cif_directory(cif_dir: Path) -> Tuple[List[MaterialGraph], List[ExclusionReason]]:
    """Parse all CIF files in a directory."""
    graphs = []
    exclusions = []

    for cif_file in cif_dir.glob("*.cif"):
        graph, exclusion = parse_cif_file(cif_file)
        if graph:
            graphs.append(graph)
        if exclusion:
            exclusions.append(exclusion)
    
    logger.info(f"Parsed {len(graphs)} graphs, excluded {len(exclusions)}.")
    return graphs, exclusions

def main():
    parser = argparse.ArgumentParser(description="Parse CIF files to MaterialGraph.")
    parser.add_argument("--input", type=str, required=True, help="Input directory or file")
    parser.add_argument("--output", type=str, required=True, help="Output JSON file for graphs")
    
    args = parser.parse_args()
    input_path = Path(args.input)
    output_path = Path(args.output)

    if input_path.is_dir():
        graphs, exclusions = parse_cif_directory(input_path)
    else:
        graph, exclusion = parse_cif_file(input_path)
        graphs = [graph] if graph else []
        exclusions = [exclusion] if exclusion else []

    # Save graphs to JSON (simplified, not parquet)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    data = {
        "graphs": [
          {
              "node_features": g.node_features.tolist() if hasattr(g.node_features, 'tolist') else g.node_features,
              "edge_features": g.edge_features.tolist() if hasattr(g.edge_features, 'tolist') else g.edge_features,
              "target_moduli": g.target_moduli.tolist() if hasattr(g.target_moduli, 'tolist') else g.target_moduli,
              "family_id": g.family_id,
              "material_id": g.material_id,
              "structure_summary": g.structure_summary
          }
          for g in graphs
        ],
        "exclusions": [asdict(e) for e in exclusions]
    }
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    logger.info(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()
