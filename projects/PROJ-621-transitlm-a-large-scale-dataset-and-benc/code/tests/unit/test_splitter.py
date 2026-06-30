import json
import pytest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List

from src.lib.splitter import (
    get_sequence_edges,
    get_sequence_nodes,
    is_edge_disjoint,
    is_path_disjoint,
    split_dataset,
    load_sequences_from_file,
    save_sequences
)
from src.contracts.models import RouteSequence, GTFSGraph, StationNode, TransferEdge

@pytest.fixture
def sample_graph():
    """Create a minimal mock GTFSGraph."""
    nodes = [
        StationNode(id="A", name="Station A"),
        StationNode(id="B", name="Station B"),
        StationNode(id="C", name="Station C"),
        StationNode(id="D", name="Station D"),
    ]
    edges = [
        TransferEdge(source="A", target="B", line="L1"),
        TransferEdge(source="B", target="C", line="L1"),
        TransferEdge(source="C", target="D", line="L2"),
    ]
    return GTFSGraph(nodes=nodes, edges=edges)

@pytest.fixture
def sample_sequences():
    """Create a list of sample RouteSequence objects."""
    return [
        RouteSequence(
            id="seq1",
            origin="A",
            destination="C",
            stations=["A", "B", "C"],
            lines=["L1"],
            transfer_count=0
        ),
        RouteSequence(
            id="seq2",
            origin="C",
            destination="D",
            stations=["C", "D"],
            lines=["L2"],
            transfer_count=0
        ),
        RouteSequence(
            id="seq3",
            origin="A",
            destination="D",
            stations=["A", "B", "C", "D"],
            lines=["L1", "L2"],
            transfer_count=1
        ),
        RouteSequence(
            id="seq4",
            origin="B",
            destination="D",
            stations=["B", "C", "D"],
            lines=["L1", "L2"],
            transfer_count=1
        ),
        # A completely separate path if we had more nodes, but for this graph,
        # everything connects. Let's add a hypothetical disjoint one if we had node E.
        # For now, seq1, seq2, seq3, seq4 all share edges/nodes.
    ]

def test_get_sequence_edges():
    seq = RouteSequence(
        id="test",
        origin="A",
        destination="C",
        stations=["A", "B", "C"],
        lines=["L1"],
        transfer_count=0
    )
    edges = get_sequence_edges(seq)
    assert ("A", "B") in edges
    assert ("B", "C") in edges
    assert len(edges) == 2

def test_get_sequence_nodes():
    seq = RouteSequence(
        id="test",
        origin="A",
        destination="C",
        stations=["A", "B", "C"],
        lines=["L1"],
        transfer_count=0
    )
    nodes = get_sequence_nodes(seq)
    assert nodes == {"A", "B", "C"}

def test_is_edge_disjoint():
    seq1 = RouteSequence(
        id="s1", origin="A", destination="B", stations=["A", "B"], lines=["L1"], transfer_count=0
    )
    seq2 = RouteSequence(
        id="s2", origin="B", destination="C", stations=["B", "C"], lines=["L1"], transfer_count=0
    )
    seq3 = RouteSequence(
        id="s3", origin="A", destination="B", stations=["A", "B"], lines=["L2"], transfer_count=0
    )
    
    # seq1 and seq2 share no edges
    assert is_edge_disjoint(seq1, seq2) is True
    
    # seq1 and seq3 share the same edge (A, B)
    assert is_edge_disjoint(seq1, seq3) is False

def test_is_path_disjoint(sample_graph):
    # seq1: A -> B -> C (internal: B)
    seq1 = RouteSequence(
        id="s1", origin="A", destination="C", stations=["A", "B", "C"], lines=["L1"], transfer_count=0
    )
    # seq2: C -> D (internal: none)
    seq2 = RouteSequence(
        id="s2", origin="C", destination="D", stations=["C", "D"], lines=["L2"], transfer_count=0
    )
    # seq3: A -> D (internal: B, C) - shares B with seq1
    seq3 = RouteSequence(
        id="s3", origin="A", destination="D", stations=["A", "B", "C", "D"], lines=["L1", "L2"], transfer_count=1
    )
    
    # seq1 and seq2: 
    # seq1 internal: {B}, seq2 internal: {} -> disjoint
    assert is_path_disjoint(seq1, seq2, sample_graph) is True
    
    # seq1 and seq3:
    # seq1 internal: {B}, seq3 internal: {B, C} -> intersect {B} -> NOT disjoint
    assert is_path_disjoint(seq1, seq3, sample_graph) is False

def test_split_dataset_disjoint(sample_graph, sample_sequences):
    # With the sample sequences provided, they all share edges/nodes.
    # The splitter should put the first one in train, and the rest in test
    # if they share edges or internal nodes with the train set.
    train, test = split_dataset(sample_sequences, sample_graph, seed=42)
    
    # At least one should be in train
    assert len(train) >= 1
    
    # Check that test set is disjoint from train set
    train_edges = set()
    train_internal = set()
    for s in train:
        train_edges.update(get_sequence_edges(s))
        internal = get_sequence_nodes(s) - {s.stations[0], s.stations[-1]}
        train_internal.update(internal)
    
    for s in test:
        s_edges = get_sequence_edges(s)
        s_internal = get_sequence_nodes(s) - {s.stations[0], s.stations[-1]}
        
        # Assert edge disjoint
        assert len(s_edges.intersection(train_edges)) == 0, f"Test seq {s.id} shares edges with train"
        
        # Assert path disjoint (internal nodes)
        assert len(s_internal.intersection(train_internal)) == 0, f"Test seq {s.id} shares internal nodes with train"

def test_save_and_load_sequences():
    with TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        test_file = tmp_path / "test.json"
        
        seqs = [
            RouteSequence(
                id="x1", origin="A", destination="B", stations=["A", "B"], lines=["L1"], transfer_count=0
            )
        ]
        
        save_sequences(seqs, test_file)
        
        loaded = load_sequences_from_file(test_file)
        
        assert len(loaded) == 1
        assert loaded[0].id == "x1"
        assert loaded[0].stations == ["A", "B"]