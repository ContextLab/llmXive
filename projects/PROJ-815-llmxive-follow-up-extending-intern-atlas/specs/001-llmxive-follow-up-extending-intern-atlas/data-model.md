# Data Model: llmXive Follow-up (Extending Intern-Atlas)

This document defines the core data structures used throughout the project pipeline,
specifically for representing research papers, their retraction status, and derived
topological features.

## 1. MethodNode

Represents a single research paper (node) in the citation graph.

```yaml
MethodNode:
 type: object
 description: "A research paper node in the citation network."
 fields:
 paper_id:
 type: string
 description: "Unique identifier for the paper (e.g., DOI or internal hash)."
 required: true
 title:
 type: string
 description: "Title of the paper."
 required: true
 year:
 type: integer
 description: "Publication year."
 required: true
 outgoing_edges:
 type: list
 description: "List of edges where this paper is the source."
 items:
 type: object
 fields:
 target_id: string
 edge_type: string # 'improves', 'replaces', 'extends'
 metadata: object
 required: true
 incoming_citations:
 type: list
 description: "List of papers that cite this paper."
 items:
 type: string # paper_id of the citing paper
 required: true
```

## 2. RetractionLabel

Represents the retraction status and details for a specific paper.

```yaml
RetractionLabel:
 type: object
 description: "Metadata regarding the retraction status of a paper."
 fields:
 paper_id:
 type: string
 description: "Unique identifier matching the MethodNode."
 required: true
 status:
 type: integer
 description: "Retraction status code: 0=Robust, 1=Fragile, 2=Retraction-Only."
 required: true
 source:
 type: string
 description: "Source of the retraction data (e.g., 'RetractionWatch', 'PubMed')."
 required: true
 retraction_reason:
 type: string
 description: "Textual reason for retraction if applicable (e.g., 'methodological error', 'fraud')."
 required: false
 nullable: true
```

## 3. TopologicalFeatures

Derived numerical features calculated from the graph structure for a specific node.

```yaml
TopologicalFeatures:
 type: object
 description: "Computed topological metrics for a paper node."
 fields:
 paper_id:
 type: string
 description: "Unique identifier matching the MethodNode."
 required: true
 bottleneck_resolution_ratio:
 type: float
 description: "Ratio of (improves + replaces) edges to total outgoing edges."
 required: true
 branching_entropy:
 type: float
 description: "Shannon entropy of the downstream method types."
 required: true
 citation_count:
 type: integer
 description: "Total number of incoming citations."
 required: true
 retraction_status_binary:
 type: integer
 description: "Binary label: 1 if status is Fragile (1) or Retraction-Only (2), 0 if Robust (0)."
 required: true
```