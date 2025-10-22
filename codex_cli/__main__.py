"""Module entrypoint for ``python -m codex_cli``."""

from __future__ import annotations

from .cli import main

if __name__ == "__main__":  # pragma: no cover - exercised when executing as a module
    raise SystemExit(main())
