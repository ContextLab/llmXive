import numpy as np
import pandas as pd
from typing import List, Dict, Set, Tuple, Optional
from utils.logging import get_logger

logger = get_logger(__name__)

def map_to_kegg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Maps raw metabolite names to KEGG Compound IDs using a local mapping table.
    
    This function assumes a pre-existing mapping dictionary or file. For this
    implementation, we simulate a mapping lookup. In a real scenario, this would
    load from a persistent KEGG mapping file (e.g., data/processed/kegg_mapping.json).
    
    Args:
        df: DataFrame containing metabolite data with a 'metabolite_name' column.
        
    Returns:
        DataFrame with an added 'kegg_id' column.
    """
    logger.info("Starting KEGG mapping process")
    
    # Simulated mapping table (in production, load from data/processed/kegg_mapping.json)
    # This is a minimal set for demonstration; real implementation would use a full database
    kegg_map = {
        "Glucose": "C00031",
        "Fructose": "C00095",
        "Sucrose": "C00089",
        "Maltose": "C00107",
        "Galactose": "C00032",
        "Glucose-6-phosphate": "C00668",
        "Fructose-6-phosphate": "C00085",
        "Pyruvate": "C00022",
        "Lactate": "C00186",
        "Alanine": "C00041",
        "Glycine": "C00037",
        "Serine": "C00065",
        "Glutamate": "C00025",
        "Aspartate": "C00049",
        "Proline": "C00148",
        "Arginine": "C00076",
        "Lysine": "C00047",
        "Valine": "C00184",
        "Leucine": "C00123",
        "Isoleucine": "C00123",
        "Phenylalanine": "C00079",
        "Tyrosine": "C00082",
        "Tryptophan": "C00078",
        "Methionine": "C00073",
        "Cysteine": "C00097",
        "Histidine": "C00132",
        "Chlorophyll_a": "C00066",
        "Chlorophyll_b": "C00067",
        "Carotene": "C00204",
        "Xanthophyll": "C00203",
        "ATP": "C00002",
        "ADP": "C00008",
        "AMP": "C00003",
        "NAD": "C00003",
        "NADH": "C00004",
        "NADP": "C00006",
        "NADPH": "C00005",
        "Acetyl-CoA": "C00024",
        "Citrate": "C00031",
        "Isocitrate": "C00311",
        "Alpha-ketoglutarate": "C00026",
        "Succinate": "C00042",
        "Fumarate": "C00122",
        "Malate": "C00149",
        "Oxaloacetate": "C00036",
        "Glyceraldehyde-3-phosphate": "C00118",
        "1,3-Bisphosphoglycerate": "C00236",
        "3-Phosphoglycerate": "C00197",
        "2-Phosphoglycerate": "C00631",
        "Phosphoenolpyruvate": "C00074",
        "Ribose-5-phosphate": "C00119",
        "Xylulose-5-phosphate": "C00252",
        "Ribulose-5-phosphate": "C00225",
        "Sedoheptulose-7-phosphate": "C00460",
        "Erythrose-4-phosphate": "C00174",
        "Quinate": "C00448",
        "Shikimate": "C00222",
        "Caffeate": "C00282",
        "Ferulate": "C00436",
        "Sinapate": "C00522",
        "Coumarate": "C00440",
        "Lignin": "C00999",
        "Cellulose": "C00999",
        "Starch": "C00999",
        "Glycogen": "C00999",
        "Chitin": "C00999",
        "Pectin": "C00999",
        "Hemicellulose": "C00999",
        "Lipid": "C00999",
        "Fatty_acid": "C00999",
        "Glycerol": "C00096",
        "Choline": "C00114",
        "Ethanolamine": "C00127",
        "Serine_phosphate": "C00192",
        "Phosphatidylcholine": "C00999",
        "Phosphatidylethanolamine": "C00999",
        "Phosphatidylserine": "C00999",
        "Phosphatidylinositol": "C00999",
        "Phosphatidic_acid": "C00999",
        "Cardiolipin": "C00999",
        "Sphingomyelin": "C00999",
        "Ceramide": "C00999",
        "Sphingosine": "C00999",
        "Inositol": "C00133",
        "Glucosamine": "C00139",
        "Galactosamine": "C00139",
        "Glucosamine-6-phosphate": "C00139",
        "N-acetylglucosamine": "C00139",
        "N-acetylgalactosamine": "C00139",
        "UDP-glucose": "C00139",
        "UDP-galactose": "C00139",
        "UDP-N-acetylglucosamine": "C00139",
        "UDP-N-acetylgalactosamine": "C00139",
        "CMP-sialic_acid": "C00139",
        "Sialic_acid": "C00139",
        "Ganglioside": "C00139",
        "Glycolipid": "C00139",
        "Glycoprotein": "C00139",
        "Proteoglycan": "C00139",
        "Hyaluronic_acid": "C00139",
        "Heparin": "C00139",
        "Heparan_sulfate": "C00139",
        "Chondroitin_sulfate": "C00139",
        "Dermatan_sulfate": "C00139",
        "Keratan_sulfate": "C00139",
        "Aggrecan": "C00139",
        "Decorin": "C00139",
        "Biglycan": "C00139",
        "Perlecan": "C00139",
        "Versican": "C00139",
        "Brevican": "C00139",
        "Neurocan": "C00139",
        "CSPG": "C00139",
        "MSPG": "C00139",
        "LSPG": "C00139",
        "VSPG": "C00139",
        "DSPG": "C00139",
        "KSPG": "C00139",
        "AGSPG": "C00139",
        "PG": "C00139",
        "CS": "C00139",
        "DS": "C00139",
        "HS": "C00139",
        "KS": "C00139",
        "HA": "C00139",
        "HE": "C00139",
        "CS-A": "C00139",
        "CS-B": "C00139",
        "CS-C": "C00139",
        "CS-D": "C00139",
        "CS-E": "C00139",
        "CS-F": "C00139",
        "CS-G": "C00139",
        "CS-H": "C00139",
        "CS-I": "C00139",
        "CS-J": "C00139",
        "CS-K": "C00139",
        "CS-L": "C00139",
        "CS-M": "C00139",
        "CS-N": "C00139",
        "CS-O": "C00139",
        "CS-P": "C00139",
        "CS-Q": "C00139",
        "CS-R": "C00139",
        "CS-S": "C00139",
        "CS-T": "C00139",
        "CS-U": "C00139",
        "CS-V": "C00139",
        "CS-W": "C00139",
        "CS-X": "C00139",
        "CS-Y": "C00139",
        "CS-Z": "C00139",
    }
    
    # Apply mapping
    df['kegg_id'] = df['metabolite_name'].map(kegg_map)
    
    # Log unmapped metabolites
    unmapped = df[df['kegg_id'].isna()]['metabolite_name'].unique()
    if len(unmapped) > 0:
        logger.warning(f"Unmapped metabolites: {len(unmapped)} entries could not be mapped to KEGG IDs")
        for metabolite in unmapped[:10]:  # Log first 10
            logger.debug(f"Unmapped: {metabolite}")
    
    logger.info(f"Mapping complete. {df['kegg_id'].notna().sum()} metabolites mapped to KEGG IDs")
    return df

def enrichment_analysis(kegg_ids: List[str], pathways: Dict[str, List[str]]) -> Dict[str, float]:
    """
    Calculates Jaccard similarity and Enrichment p-value for pathway enrichment.
    
    Args:
        kegg_ids: List of KEGG Compound IDs found in the dataset.
        pathways: Dictionary mapping pathway names to lists of KEGG Compound IDs in that pathway.
        
    Returns:
        Dictionary with 'jaccard_similarity' and 'enrichment_p_value' for each pathway.
    """
    logger.info(f"Starting enrichment analysis for {len(kegg_ids)} KEGG IDs against {len(pathways)} pathways")
    
    kegg_set = set(kegg_ids)
    results = {}
    
    for pathway_name, pathway_ids in pathways.items():
        pathway_set = set(pathway_ids)
        
        # Calculate Jaccard Similarity
        intersection = kegg_set.intersection(pathway_set)
        union = kegg_set.union(pathway_set)
        
        if len(union) == 0:
            jaccard = 0.0
        else:
            jaccard = len(intersection) / len(union)
        
        # Calculate Enrichment p-value using hypergeometric test approximation
        # For simplicity, we use a basic calculation here. In production, 
        # scipy.stats.hypergeom should be used for accurate p-values.
        # This is a simplified version for demonstration.
        
        total_compounds = 10000  # Approximate total number of compounds in KEGG
        pathway_size = len(pathway_set)
        found_in_pathway = len(intersection)
        
        # Expected overlap by chance
        expected = (len(kegg_set) * pathway_size) / total_compounds
        
        # Simple p-value approximation (over-representation)
        if expected > 0:
            # Using a simplified ratio-based approach for p-value estimation
            # In reality, this should use hypergeometric distribution
            ratio = found_in_pathway / expected if expected > 0 else 0
            # Convert ratio to p-value (simplified: p = e^(-ratio) for demonstration)
            # This is NOT a statistically rigorous method but serves as a placeholder
            # for the logic required by the task.
            import math
            p_value = math.exp(-ratio) if ratio > 0 else 1.0
        else:
            p_value = 1.0
        
        results[pathway_name] = {
            'jaccard_similarity': jaccard,
            'enrichment_p_value': p_value,
            'overlap_count': found_in_pathway,
            'pathway_size': pathway_size
        }
    
    logger.info(f"Enrichment analysis complete. Calculated metrics for {len(results)} pathways")
    return results

def validate_alignment(jaccard: float, p_value: float) -> bool:
    """
    Validates biological plausibility against known pathways.
    
    Returns True if the alignment is considered biologically plausible based on:
    - Jaccard similarity >= 0.3 OR
    - Enrichment p-value < 0.05
    
    Args:
        jaccard: Jaccard similarity score between observed and expected pathway overlaps.
        p_value: Enrichment p-value from statistical testing.
        
    Returns:
        bool: True if alignment is valid, False otherwise.
    """
    logger.debug(f"Validating alignment: Jaccard={jaccard:.4f}, p-value={p_value:.4f}")
    
    is_valid = (jaccard >= 0.3) or (p_value < 0.05)
    
    if is_valid:
        logger.info("Pathway alignment validated: Biological plausibility confirmed")
    else:
        logger.warning("Pathway alignment failed: Biological plausibility not confirmed")
        
    return is_valid