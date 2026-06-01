from __future__ import annotations

import sys


class ValidationResult:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


def check_python_version(
    minimum: tuple[int, int] = (3, 10),
) -> ValidationResult:
    result = ValidationResult()

    if sys.version_info < minimum:
        result.errors.append(
            f"Python {minimum[0]}.{minimum[1]}+ is required. "
            f"Found {sys.version_info.major}.{sys.version_info.minor}."
        )

    return result