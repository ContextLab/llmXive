# Data Model: Graph Metadata

This document defines the schema for `graph_metadata.json`, which stores metadata for each generated network topology.

## Schema Definition

The file contains a list of objects with the following keys:

- **node_count** (int): Total number of nodes in the graph (N).
- **avg_degree** (float): Average degree of the graph (k).
- **p** (float): Rewiring probability used in Watts-Strogatz generation.
- **seed** (int): Random seed used for reproducibility.
- **checksum** (string): SHA256 checksum of the corresponding.gpickle file.

## Example Entry

```json
{
 "node_count": 500,
 "avg_degree": 4.0,
 "p": 0.1,
 "seed": 42,
 "checksum": "abc123..."
}
```