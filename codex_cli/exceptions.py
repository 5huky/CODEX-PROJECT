"""Custom exceptions used by the Codex CLI."""

from __future__ import annotations


class CodexError(Exception):
    """Base exception for CLI errors."""


class UnauthorizedError(CodexError):
    """Raised when authentication with the Codex API fails."""

    def __init__(self, message: str, *, hint: str | None = None) -> None:
        super().__init__(message)
        self.hint = hint

    def __str__(self) -> str:  # pragma: no cover - inherited behaviour is fine
        if self.hint:
            return f"{super().__str__()} {self.hint}".strip()
        return super().__str__()
