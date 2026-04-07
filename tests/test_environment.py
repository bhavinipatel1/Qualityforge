import os

def test_required_config_present():
    api_key = os.environ.get("MISSING_SECRET_KEY")
    assert api_key is not None, \
        "Environment variable MISSING_SECRET_KEY is not set — check runner configuration"