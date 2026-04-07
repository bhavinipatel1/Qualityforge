import time
import pytest

def test_api_response_time():
    start = time.time()
    time.sleep(6)  # simulates a slow operation
    elapsed = time.time() - start
    assert elapsed < 5, f"Timeout: operation took {elapsed:.1f}s, exceeded 5s limit"