"""
PolymerGraph entity class for representing polymer structures as graphs.

This module defines the core data structure for polymers in the permeability
prediction pipeline, including node and edge feature schemas.
"""

from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import numpy as np

# Node feature schema definitions
NODE_FEATURES = {
    'atom_type': {
        'description': 'Element symbol (e.g., "C", "N", "O", "S", "Cl")',
        'type': str,
        'required': True
    },
    'hybridization': {
        'description': 'Hybridization state (sp, sp2, sp3, etc.)',
        'type': str,
        'required': True
    },
    'formal_charge': {
        'description': 'Formal charge on the atom',
        'type': int,
        'required': False,
        'default': 0
    },
    'atomic_number': {
        'description': 'Atomic number of the element',
        'type': int,
        'required': True
    },
    'mass': {
        'description': 'Atomic mass in Daltons',
        'type': float,
        'required': False
    },
    'degree': {
        'description': 'Number of bonds connected to this atom',
        'type': int,
        'required': False,
        'default': 0
    },
    'is_aromatic': {
        'description': 'Whether the atom is part of an aromatic system',
        'type': bool,
        'required': False,
        'default': False
    }
}

# Edge feature schema definitions
EDGE_FEATURES = {
    'bond_type': {
        'description': 'Type of bond (SINGLE, DOUBLE, TRIPLE, AROMATIC)',
        'type': str,
        'required': True
    },
    'is_conjugated': {
        'description': 'Whether the bond is part of a conjugated system',
        'type': bool,
        'required': False,
        'default': False
    },
    'is_in_ring': {
        'description': 'Whether the bond is part of a ring structure',
        'type': bool,
        'required': False,
        'default': False
    },
    'bond_order': {
        'description': 'Numerical bond order (1.0, 1.5, 2.0, 3.0)',
        'type': float,
        'required': False
    },
    'stereochemistry': {
        'description': 'Stereochemistry of the bond (NONE, CIS, TRANS, etc.)',
        'type': str,
        'required': False,
        'default': 'NONE'
    }
}

@dataclass
class PolymerGraph:
    """
    Represents a polymer structure as a graph with nodes (atoms) and edges (bonds).
    
    Attributes:
        nodes: List of dictionaries, each representing an atom with its features
        edges: List of tuples (source_idx, target_idx, edge_features_dict)
        metadata: Dictionary for additional graph-level information
        repeat_unit_indices: Optional indices marking the repeat unit boundaries
        molecular_weight: Calculated molecular weight of the structure
    """
    nodes: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[Tuple[int, int, Dict[str, Any]]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    repeat_unit_indices: Optional[Tuple[int, int]] = None
    molecular_weight: Optional[float] = None
    
    def __post_init__(self):
        """Validate and initialize the graph structure."""
        self._validate_nodes()
        self._validate_edges()
        self._compute_metadata_if_missing()
    
    def _validate_nodes(self) -> None:
        """Validate that all nodes have required features."""
        for i, node in enumerate(self.nodes):
            for feature_name, feature_def in NODE_FEATURES.items():
                if feature_def['required'] and feature_name not in node:
                    raise ValueError(
                        f"Node {i} missing required feature: {feature_name}"
                    )
                if feature_name not in node and 'default' in feature_def:
                    node[feature_name] = feature_def['default']
    
    def _validate_edges(self) -> None:
        """Validate that all edges have required features and valid indices."""
        num_nodes = len(self.nodes)
        for edge in self.edges:
            if len(edge) != 3:
                raise ValueError("Edge must be a tuple of (source_idx, target_idx, features)")
            
            source_idx, target_idx, features = edge
            
            if not (0 <= source_idx < num_nodes and 0 <= target_idx < num_nodes):
                raise ValueError(
                    f"Edge references invalid node indices: {source_idx}, {target_idx}. "
                    f"Graph has {num_nodes} nodes."
                )
            
            for feature_name, feature_def in EDGE_FEATURES.items():
                if feature_def['required'] and feature_name not in features:
                    raise ValueError(
                        f"Edge ({source_idx}, {target_idx}) missing required feature: {feature_name}"
                    )
                if feature_name not in features and 'default' in feature_def:
                    features[feature_name] = feature_def['default']
    
    def _compute_metadata_if_missing(self) -> None:
        """Compute default metadata if not provided."""
        if 'num_nodes' not in self.metadata:
            self.metadata['num_nodes'] = len(self.nodes)
        if 'num_edges' not in self.metadata:
            self.metadata['num_edges'] = len(self.edges)
        if 'is_connected' not in self.metadata:
            self.metadata['is_connected'] = self._check_connectivity()
    
    def _check_connectivity(self) -> bool:
        """Simple connectivity check using BFS."""
        if len(self.nodes) == 0:
            return True
        if len(self.edges) == 0:
            return len(self.nodes) == 1
        
        # Build adjacency list
        adj = {i: set() for i in range(len(self.nodes))}
        for source_idx, target_idx, _ in self.edges:
            adj[source_idx].add(target_idx)
            adj[target_idx].add(source_idx)
        
        # BFS from first node
        visited = {0}
        queue = [0]
        while queue:
            current = queue.pop(0)
            for neighbor in adj[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return len(visited) == len(self.nodes)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the graph to a dictionary representation."""
        return {
            'nodes': self.nodes,
            'edges': [
                {'source': s, 'target': t, 'features': f} 
                for s, t, f in self.edges
            ],
            'metadata': self.metadata,
            'repeat_unit_indices': self.repeat_unit_indices,
            'molecular_weight': self.molecular_weight
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PolymerGraph':
        """Create a PolymerGraph from a dictionary representation."""
        return cls(
            nodes=data.get('nodes', []),
            edges=[
                (e['source'], e['target'], e['features']) 
                for e in data.get('edges', [])
            ],
            metadata=data.get('metadata', {}),
            repeat_unit_indices=data.get('repeat_unit_indices'),
            molecular_weight=data.get('molecular_weight')
        )
    
    def add_node(self, features: Dict[str, Any]) -> int:
        """Add a node to the graph and return its index."""
        self.nodes.append(features)
        self.metadata['num_nodes'] = len(self.nodes)
        return len(self.nodes) - 1
    
    def add_edge(self, source_idx: int, target_idx: int, features: Dict[str, Any]) -> None:
        """Add an edge to the graph."""
        self.edges.append((source_idx, target_idx, features))
        self.metadata['num_edges'] = len(self.edges)
    
    def get_node_features(self, node_idx: int) -> Dict[str, Any]:
        """Get features for a specific node."""
        if 0 <= node_idx < len(self.nodes):
            return self.nodes[node_idx]
        raise IndexError(f"Node index {node_idx} out of range")
    
    def get_edge_features(self, edge_idx: int) -> Dict[str, Any]:
        """Get features for a specific edge."""
        if 0 <= edge_idx < len(self.edges):
            return self.edges[edge_idx][2]
        raise IndexError(f"Edge index {edge_idx} out of range")
    
    def get_adjacency_list(self) -> Dict[int, List[Tuple[int, Dict[str, Any]]]]:
        """Get an adjacency list representation of the graph."""
        adj = {i: [] for i in range(len(self.nodes))}
        for source_idx, target_idx, features in self.edges:
            adj[source_idx].append((target_idx, features))
            adj[target_idx].append((source_idx, features))
        return adj
    
    def __len__(self) -> int:
        """Return the number of nodes in the graph."""
        return len(self.nodes)
    
    def __repr__(self) -> str:
        return (
            f"PolymerGraph(nodes={len(self.nodes)}, edges={len(self.edges)}, "
            f"mw={self.molecular_weight:.2f} Da)"
        )