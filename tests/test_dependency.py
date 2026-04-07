def test_external_package_available():
    try:
        import nonexistent_analytics_sdk
    except ImportError as e:
        raise ImportError(
            f"ModuleNotFoundError: No module named 'nonexistent_analytics_sdk'. "
            f"Run: pip install nonexistent_analytics_sdk"
        ) from e