"""
Unit tests for pathway aggregation mapping (T017).

Tests the logic for mapping genes to pathways (KEGG/GO) and aggregating
herbivore-response vectors to pathway-level features.

This test suite validates:
1. Correct mapping of gene IDs to pathway IDs.
2. Proper aggregation of log2FC values within pathways.
3. Handling of genes not present in any pathway.
4. Handling of pathways with no mapped genes.
5. Variance-based pathway selection logic.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
import sys
import json

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from src.utils.schemas import PathwayMapping, AggregatedFeatures
from src.utils.config import get_config


class TestPathwayAggregationMapping:
    """Test suite for pathway aggregation and mapping logic."""

    @pytest.fixture
    def sample_pathway_mapping(self) -> Dict[str, List[str]]:
        """Create a sample pathway mapping for testing."""
        return {
            "AT1G01010": ["KEGG:00010", "KEGG:00020"],
            "AT1G01020": ["KEGG:00010"],
            "AT1G01030": ["KEGG:00030", "KEGG:00040"],
            "AT1G01040": ["KEGG:00020", "KEGG:00030"],
            "AT1G01050": ["KEGG:00050"],
            "AT1G01060": [],  # Gene with no pathways
            "AT1G01070": ["KEGG:00010", "KEGG:00020", "KEGG:00030"],
        }

    @pytest.fixture
    def sample_response_vector(self) -> pd.Series:
        """Create a sample herbivore-response vector (log2FC values)."""
        data = {
            "AT1G01010": 2.5,
            "AT1G01020": -1.2,
            "AT1G01030": 0.8,
            "AT1G01040": -0.5,
            "AT1G01050": 3.1,
            "AT1G01060": 1.5,  # Gene with no pathways
            "AT1G01070": -2.0,
            "AT1G01080": 1.0,  # Gene not in mapping
        }
        return pd.Series(data, name="log2fc")

    @pytest.fixture
    def sample_pathway_mapping_schema(self, sample_pathway_mapping: Dict[str, List[str]]) -> Dict:
        """Create a PathwayMapping schema object from the sample mapping."""
        return PathwayMapping(
            gene_id="AT1G01010",
            pathway_ids=["KEGG:00010", "KEGG:00020"]
        )

    def test_pathway_mapping_creation(self, sample_pathway_mapping_schema):
        """Test that PathwayMapping schema is created correctly."""
        assert sample_pathway_mapping_schema.gene_id == "AT1G01010"
        assert "KEGG:00010" in sample_pathway_mapping_schema.pathway_ids
        assert "KEGG:00020" in sample_pathway_mapping_schema.pathway_ids
        assert len(sample_pathway_mapping_schema.pathway_ids) == 2

    def test_aggregated_features_schema(self):
        """Test that AggregatedFeatures schema is created correctly."""
        agg_features = AggregatedFeatures(
            pathway_id="KEGG:00010",
            mean_log2fc=1.5,
            gene_count=3,
            variance=0.5
        )
        assert agg_features.pathway_id == "KEGG:00010"
        assert agg_features.mean_log2fc == 1.5
        assert agg_features.gene_count == 3
        assert agg_features.variance == 0.5

    def test_map_genes_to_pathways(self, sample_pathway_mapping):
        """Test mapping genes to pathways."""
        # Reverse mapping: pathway -> list of genes
        pathway_to_genes: Dict[str, List[str]] = {}
        
        for gene_id, pathway_ids in sample_pathway_mapping.items():
            for pathway_id in pathway_ids:
                if pathway_id not in pathway_to_genes:
                    pathway_to_genes[pathway_id] = []
                pathway_to_genes[pathway_id].append(gene_id)
        
        # Verify the reverse mapping
        assert "KEGG:00010" in pathway_to_genes
        assert "AT1G01010" in pathway_to_genes["KEGG:00010"]
        assert "AT1G01020" in pathway_to_genes["KEGG:00010"]
        assert "AT1G01070" in pathway_to_genes["KEGG:00010"]
        
        assert "KEGG:00050" in pathway_to_genes
        assert pathway_to_genes["KEGG:00050"] == ["AT1G01050"]

    def test_aggregate_response_vector(self, sample_pathway_mapping, sample_response_vector):
        """Test aggregation of response vector to pathway level."""
        # Reverse mapping: pathway -> list of genes
        pathway_to_genes: Dict[str, List[str]] = {}
        
        for gene_id, pathway_ids in sample_pathway_mapping.items():
            for pathway_id in pathway_ids:
                if pathway_id not in pathway_to_genes:
                    pathway_to_genes[pathway_id] = []
                pathway_to_genes[pathway_id].append(gene_id)
        
        # Aggregate: mean log2FC for genes in each pathway
        aggregated: Dict[str, Dict] = {}
        
        for pathway_id, genes in pathway_to_genes.items():
            # Get log2FC values for genes in this pathway
            values = [sample_response_vector[gene_id] for gene_id in genes if gene_id in sample_response_vector.index]
            
            if values:
                mean_val = np.mean(values)
                var_val = np.var(values) if len(values) > 1 else 0.0
                aggregated[pathway_id] = {
                    "mean_log2fc": mean_val,
                    "gene_count": len(values),
                    "variance": var_val
                }
        
        # Verify aggregation results
        assert "KEGG:00010" in aggregated
        # Genes in KEGG:00010: AT1G01010 (2.5), AT1G01020 (-1.2), AT1G01070 (-2.0)
        expected_mean_kegg_00010 = (2.5 + (-1.2) + (-2.0)) / 3
        assert np.isclose(aggregated["KEGG:00010"]["mean_log2fc"], expected_mean_kegg_00010)
        assert aggregated["KEGG:00010"]["gene_count"] == 3
        
        # KEGG:00050 has only one gene
        assert "KEGG:00050" in aggregated
        assert np.isclose(aggregated["KEGG:00050"]["mean_log2fc"], 3.1)
        assert aggregated["KEGG:00050"]["gene_count"] == 1

    def test_genes_without_pathways(self, sample_pathway_mapping, sample_response_vector):
        """Test handling of genes that are not mapped to any pathway."""
        # Gene AT1G01060 has no pathways, AT1G01080 is not in mapping
        # These should be excluded from aggregation
        
        # Reverse mapping: pathway -> list of genes
        pathway_to_genes: Dict[str, List[str]] = {}
        
        for gene_id, pathway_ids in sample_pathway_mapping.items():
            for pathway_id in pathway_ids:
                if pathway_id not in pathway_to_genes:
                    pathway_to_genes[pathway_id] = []
                pathway_to_genes[pathway_id].append(gene_id)
        
        # Aggregate
        aggregated: Dict[str, Dict] = {}
        for pathway_id, genes in pathway_to_genes.items():
            values = [sample_response_vector[gene_id] for gene_id in genes if gene_id in sample_response_vector.index]
            if values:
                aggregated[pathway_id] = {
                    "mean_log2fc": np.mean(values),
                    "gene_count": len(values),
                    "variance": np.var(values) if len(values) > 1 else 0.0
                }
        
        # Verify that genes without pathways are not included in any pathway
        all_pathway_genes = set()
        for genes in pathway_to_genes.values():
            all_pathway_genes.update(genes)
        
        assert "AT1G01060" not in all_pathway_genes  # No pathways defined
        assert "AT1G01080" not in all_pathway_genes  # Not in mapping

    def test_pathways_with_no_genes(self, sample_pathway_mapping, sample_response_vector):
        """Test handling of pathways that have no mapped genes in the response vector."""
        # Create a mapping where a pathway exists but has no genes in the response vector
        extended_mapping = sample_pathway_mapping.copy()
        extended_mapping["AT1G99999"] = ["KEGG:00999"]  # Pathway with no genes in response vector
        
        # Reverse mapping
        pathway_to_genes: Dict[str, List[str]] = {}
        for gene_id, pathway_ids in extended_mapping.items():
            for pathway_id in pathway_ids:
                if pathway_id not in pathway_to_genes:
                    pathway_to_genes[pathway_id] = []
                pathway_to_genes[pathway_id].append(gene_id)
        
        # Aggregate
        aggregated: Dict[str, Dict] = {}
        for pathway_id, genes in pathway_to_genes.items():
            values = [sample_response_vector[gene_id] for gene_id in genes if gene_id in sample_response_vector.index]
            if values:
                aggregated[pathway_id] = {
                    "mean_log2fc": np.mean(values),
                    "gene_count": len(values),
                    "variance": np.var(values) if len(values) > 1 else 0.0
                }
        
        # KEGG:00999 should not be in aggregated because no genes from it are in the response vector
        assert "KEGG:00999" not in aggregated

    def test_variance_based_selection(self, sample_pathway_mapping, sample_response_vector):
        """Test variance-based pathway selection logic."""
        # Reverse mapping
        pathway_to_genes: Dict[str, List[str]] = {}
        for gene_id, pathway_ids in sample_pathway_mapping.items():
            for pathway_id in pathway_ids:
                if pathway_id not in pathway_to_genes:
                    pathway_to_genes[pathway_id] = []
                pathway_to_genes[pathway_id].append(gene_id)
        
        # Aggregate
        aggregated: Dict[str, Dict] = {}
        for pathway_id, genes in pathway_to_genes.items():
            values = [sample_response_vector[gene_id] for gene_id in genes if gene_id in sample_response_vector.index]
            if values:
                aggregated[pathway_id] = {
                    "mean_log2fc": np.mean(values),
                    "gene_count": len(values),
                    "variance": np.var(values) if len(values) > 1 else 0.0
                }
        
        # Sort by variance (descending) and select top N
        n_top = 3
        sorted_pathways = sorted(aggregated.items(), key=lambda x: x[1]["variance"], reverse=True)
        top_pathways = [p[0] for p in sorted_pathways[:n_top]]
        
        # Verify we got the top 3 by variance
        assert len(top_pathways) == n_top
        assert all(p in aggregated for p in top_pathways)
        
        # Verify the selected pathways have the highest variances
        all_variances = [(p, data["variance"]) for p, data in aggregated.items()]
        all_variances.sort(key=lambda x: x[1], reverse=True)
        expected_top = [p[0] for p in all_variances[:n_top]]
        
        assert set(top_pathways) == set(expected_top)

    def test_empty_response_vector(self, sample_pathway_mapping):
        """Test handling of an empty response vector."""
        empty_vector = pd.Series(dtype=float)
        
        # Reverse mapping
        pathway_to_genes: Dict[str, List[str]] = {}
        for gene_id, pathway_ids in sample_pathway_mapping.items():
            for pathway_id in pathway_ids:
                if pathway_id not in pathway_to_genes:
                    pathway_to_genes[pathway_id] = []
                pathway_to_genes[pathway_id].append(gene_id)
        
        # Aggregate
        aggregated: Dict[str, Dict] = {}
        for pathway_id, genes in pathway_to_genes.items():
            values = [empty_vector[gene_id] for gene_id in genes if gene_id in empty_vector.index]
            if values:
                aggregated[pathway_id] = {
                    "mean_log2fc": np.mean(values),
                    "gene_count": len(values),
                    "variance": np.var(values) if len(values) > 1 else 0.0
                }
        
        # No pathways should be aggregated
        assert len(aggregated) == 0

    def test_single_gene_pathway(self, sample_pathway_mapping, sample_response_vector):
        """Test handling of pathways with only a single gene."""
        # KEGG:00050 has only one gene (AT1G01050)
        
        # Reverse mapping
        pathway_to_genes: Dict[str, List[str]] = {}
        for gene_id, pathway_ids in sample_pathway_mapping.items():
            for pathway_id in pathway_ids:
                if pathway_id not in pathway_to_genes:
                    pathway_to_genes[pathway_id] = []
                pathway_to_genes[pathway_id].append(gene_id)
        
        # Aggregate
        aggregated: Dict[str, Dict] = {}
        for pathway_id, genes in pathway_to_genes.items():
            values = [sample_response_vector[gene_id] for gene_id in genes if gene_id in sample_response_vector.index]
            if values:
                aggregated[pathway_id] = {
                    "mean_log2fc": np.mean(values),
                    "gene_count": len(values),
                    "variance": np.var(values) if len(values) > 1 else 0.0
                }
        
        # Verify single-gene pathway
        assert "KEGG:00050" in aggregated
        assert aggregated["KEGG:00050"]["gene_count"] == 1
        assert aggregated["KEGG:00050"]["variance"] == 0.0  # Variance of single value is 0
        assert np.isclose(aggregated["KEGG:00050"]["mean_log2fc"], 3.1)

    def test_pathway_mapping_schema_validation(self):
        """Test that PathwayMapping schema validates correctly."""
        # Valid mapping
        mapping = PathwayMapping(
            gene_id="AT1G01010",
            pathway_ids=["KEGG:00010", "KEGG:00020"]
        )
        assert mapping.gene_id == "AT1G01010"
        assert len(mapping.pathway_ids) == 2

        # Empty pathway_ids should be allowed (gene with no pathways)
        mapping_empty = PathwayMapping(
            gene_id="AT1G01060",
            pathway_ids=[]
        )
        assert mapping_empty.gene_id == "AT1G01060"
        assert len(mapping_empty.pathway_ids) == 0

    def test_aggregated_features_schema_validation(self):
        """Test that AggregatedFeatures schema validates correctly."""
        # Valid aggregation
        agg = AggregatedFeatures(
            pathway_id="KEGG:00010",
            mean_log2fc=1.5,
            gene_count=3,
            variance=0.5
        )
        assert agg.pathway_id == "KEGG:00010"
        assert agg.mean_log2fc == 1.5
        assert agg.gene_count == 3
        assert agg.variance == 0.5

        # Zero variance (single gene)
        agg_zero_var = AggregatedFeatures(
            pathway_id="KEGG:00050",
            mean_log2fc=3.1,
            gene_count=1,
            variance=0.0
        )
        assert agg_zero_var.variance == 0.0

    def test_integration_with_schemas(self, sample_pathway_mapping, sample_response_vector):
        """Test integration of aggregation logic with schema validation."""
        # Reverse mapping
        pathway_to_genes: Dict[str, List[str]] = {}
        for gene_id, pathway_ids in sample_pathway_mapping.items():
            for pathway_id in pathway_ids:
                if pathway_id not in pathway_to_genes:
                    pathway_to_genes[pathway_id] = []
                pathway_to_genes[pathway_id].append(gene_id)
        
        # Aggregate and validate with schema
        aggregated_features: List[AggregatedFeatures] = []
        
        for pathway_id, genes in pathway_to_genes.items():
            values = [sample_response_vector[gene_id] for gene_id in genes if gene_id in sample_response_vector.index]
            if values:
                agg = AggregatedFeatures(
                    pathway_id=pathway_id,
                    mean_log2fc=np.mean(values),
                    gene_count=len(values),
                    variance=np.var(values) if len(values) > 1 else 0.0
                )
                aggregated_features.append(agg)
        
        # Verify all items are valid AggregatedFeatures
        assert len(aggregated_features) > 0
        for feat in aggregated_features:
            assert isinstance(feat, AggregatedFeatures)
            assert feat.pathway_id is not None
            assert feat.mean_log2fc is not None
            assert feat.gene_count > 0
            assert feat.variance >= 0