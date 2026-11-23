import pytest
import json
from datetime import datetime
from code.data_models.splicing_event import SplicingEvent

def test_splicing_event_creation():
    """Test basic creation of a SplicingEvent."""
    event = SplicingEvent(
        event_id="SE_chr1_12345",
        gene_id="GENE001",
        delta_psi=0.15,
        fdr=0.03,
        flank_seq="ATCGATCGATCG",
        phyloP_score=-2.5,
        accelerated_flag=True
    )
    assert event.event_id == "SE_chr1_12345"
    assert event.gene_id == "GENE001"
    assert event.delta_psi == 0.15
    assert event.fdr == 0.03
    assert event.flank_seq == "ATCGATCGATCG"
    assert event.phyloP_score == -2.5
    assert event.accelerated_flag is True
    assert isinstance(event.created_at, datetime)

def test_splicing_event_to_dict():
    """Test conversion to dictionary."""
    event = SplicingEvent(
        event_id="SE_chr2_67890",
        gene_id="GENE002",
        delta_psi=-0.2,
        fdr=0.01,
        flank_seq="GCGCGCGC",
        phyloP_score=1.5,
        accelerated_flag=False
    )
    data = event.to_dict()
    assert data['event_id'] == "SE_chr2_67890"
    assert data['gene_id'] == "GENE002"
    assert data['delta_psi'] == -0.2
    assert data['fdr'] == 0.01
    assert data['flank_seq'] == "GCGCGCGC"
    assert data['phyloP_score'] == 1.5
    assert data['accelerated_flag'] is False
    assert 'created_at' in data

def test_splicing_event_to_json():
    """Test JSON serialization."""
    event = SplicingEvent(
        event_id="SE_chr3_11111",
        gene_id="GENE003",
        delta_psi=0.05,
        fdr=0.08,
        flank_seq="TATATATA",
        phyloP_score=-1.0,
        accelerated_flag=False
    )
    json_str = event.to_json()
    data = json.loads(json_str)
    assert data['event_id'] == "SE_chr3_11111"
    assert data['gene_id'] == "GENE003"
    assert data['delta_psi'] == 0.05
    assert data['fdr'] == 0.08
    assert data['phyloP_score'] == -1.0
    assert data['accelerated_flag'] is False

def test_splicing_event_from_dict():
    """Test creation from dictionary."""
    data = {
        'event_id': "SE_chr4_22222",
        'gene_id': "GENE004",
        'delta_psi': 0.25,
        'fdr': 0.005,
        'flank_seq': "CGCGCGCG",
        'phyloP_score': -3.0,
        'accelerated_flag': True,
        'created_at': datetime(2023, 1, 1, 12, 0, 0)
    }
    event = SplicingEvent.from_dict(data)
    assert event.event_id == "SE_chr4_22222"
    assert event.gene_id == "GENE004"
    assert event.delta_psi == 0.25
    assert event.fdr == 0.005
    assert event.flank_seq == "CGCGCGCG"
    assert event.phyloP_score == -3.0
    assert event.accelerated_flag is True
    assert event.created_at == datetime(2023, 1, 1, 12, 0, 0)

def test_splicing_event_from_json():
    """Test creation from JSON string."""
    json_str = json.dumps({
        'event_id': "SE_chr5_33333",
        'gene_id': "GENE005",
        'delta_psi': -0.12,
        'fdr': 0.04,
        'flank_seq': "ATATATAT",
        'phyloP_score': -2.1,
        'accelerated_flag': True,
        'created_at': "2023-06-15T10:30:00"
    })
    event = SplicingEvent.from_json(json_str)
    assert event.event_id == "SE_chr5_33333"
    assert event.gene_id == "GENE005"
    assert event.delta_psi == -0.12
    assert event.fdr == 0.04
    assert event.flank_seq == "ATATATAT"
    assert event.phyloP_score == -2.1
    assert event.accelerated_flag is True
    assert isinstance(event.created_at, datetime)

def test_splicing_event_round_trip():
    """Test that to_dict/from_dict and to_json/from_json are reversible."""
    original = SplicingEvent(
        event_id="SE_chr6_44444",
        gene_id="GENE006",
        delta_psi=0.18,
        fdr=0.02,
        flank_seq="GATCGATC",
        phyloP_score=-2.8,
        accelerated_flag=True
    )
    
    # Test dict round trip
    data = original.to_dict()
    restored_dict = SplicingEvent.from_dict(data)
    assert original == restored_dict

    # Test JSON round trip
    json_str = original.to_json()
    restored_json = SplicingEvent.from_json(json_str)
    assert original == restored_json

def test_splicing_event_equality():
    """Test equality operator."""
    event1 = SplicingEvent(
        event_id="SE_chr7_55555",
        gene_id="GENE007",
        delta_psi=0.1,
        fdr=0.05,
        flank_seq="AAAA",
        phyloP_score=-2.0,
        accelerated_flag=True
    )
    event2 = SplicingEvent(
        event_id="SE_chr7_55555",
        gene_id="GENE007",
        delta_psi=0.1,
        fdr=0.05,
        flank_seq="AAAA",
        phyloP_score=-2.0,
        accelerated_flag=True
    )
    event3 = SplicingEvent(
        event_id="SE_chr8_66666",
        gene_id="GENE008",
        delta_psi=0.2,
        fdr=0.06,
        flank_seq="BBBB",
        phyloP_score=-3.0,
        accelerated_flag=True
    )
    
    assert event1 == event2
    assert event1 != event3

def test_splicing_event_hash():
    """Test hashability for use in sets and dicts."""
    event = SplicingEvent(
        event_id="SE_chr9_77777",
        gene_id="GENE009",
        delta_psi=0.09,
        fdr=0.07,
        flank_seq="CCCC",
        phyloP_score=-1.5,
        accelerated_flag=False
    )
    event_set = {event}
    assert event in event_set

def test_splicing_event_none_phylop():
    """Test handling of None phyloP_score."""
    event = SplicingEvent(
        event_id="SE_chr10_88888",
        gene_id="GENE010",
        delta_psi=0.11,
        fdr=0.03,
        flank_seq="DDDD",
        phyloP_score=None,
        accelerated_flag=False
    )
    assert event.phyloP_score is None
    assert event.accelerated_flag is False

def test_splicing_event_invalid_accelerated_flag():
    """Test that accelerated_flag is consistent with phyloP_score."""
    # If phyloP_score is <= -2.0, accelerated_flag should be True
    event1 = SplicingEvent(
        event_id="SE_chr11_99999",
        gene_id="GENE011",
        delta_psi=0.13,
        fdr=0.04,
        flank_seq="EEEE",
        phyloP_score=-2.5,
        accelerated_flag=True
    )
    assert event1.accelerated_flag is True

    # If phyloP_score is > -2.0, accelerated_flag should be False
    event2 = SplicingEvent(
        event_id="SE_chr12_10101",
        gene_id="GENE012",
        delta_psi=0.14,
        fdr=0.05,
        flank_seq="FFFF",
        phyloP_score=-1.0,
        accelerated_flag=False
    )
    assert event2.accelerated_flag is False