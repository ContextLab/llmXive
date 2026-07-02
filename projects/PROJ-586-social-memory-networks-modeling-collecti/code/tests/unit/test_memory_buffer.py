from memory.buffer import get_shared_memory_buffer
      
def test_basic_buffer_operations():
    buf = get_shared_memory_buffer()
    buf.clear()
    assert buf.get_all() == []
    buf.add(type("DummyAction", (), {"token": "x"})())
    assert len(buf.get_all()) == 1

def test_reset_is_no_error():
    buf = get_shared_memory_buffer()
    buf.reset()  # should not raise
    assert True