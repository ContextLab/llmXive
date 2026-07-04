import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from models.data_models import Participant, Session, Metric
from datetime import datetime

def test_participant_creation():
    p = Participant(id="1", disability_type="visual", interface_sequence=["A", "B"])
    assert p.id == "1"
    assert p.disability_type == "visual"

def test_session_creation():
    s = Session(
        session_id="s1",
        participant_id="1",
        interface_type="Traditional",
        start_time=datetime.now()
    )
    assert s.status == "in_progress"

def test_metric_creation():
    m = Metric(metric_name="time", interface_type="A", mean=10.0, std_dev=2.0)
    assert m.mean == 10.0

if __name__ == "__main__":
    test_participant_creation()
    test_session_creation()
    test_metric_creation()
    print("All tests passed.")