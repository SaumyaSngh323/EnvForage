from envforge_agent.validation import check_python_version


def test_python_version_check_passes() -> None:
    result = check_python_version((3, 10))
    assert result.is_valid
    assert result.errors == []