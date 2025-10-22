# Codex CLI Helper

This repository provides a lightweight helper CLI for checking connectivity with the Codex API.
It focuses on surfacing clearer diagnostics when authentication fails (for example when the
server responds with a `401 Unauthorized` error).

## Installation

The project ships as a standard Python package. Install it in your active virtual environment
with `pip`:

```bash
pip install .
```

For local development you can install it in editable mode instead:

```bash
pip install -e .
```

Installation exposes a `codex-cli` console script, so you do not have to invoke the module
manually.

## Usage

After installation you can run the connectivity check with either the console script or the module
entry point:

```bash
codex-cli status --api-key YOUR_API_KEY
# or
python -m codex_cli status --api-key YOUR_API_KEY
```

If you omit `--api-key`, the CLI falls back to the `CODEX_API_KEY` environment variable. You can
also change the base URL via `--base-url` or the `CODEX_API_BASE_URL` environment variable.

A successful call prints a confirmation message including the HTTP status code. When the server
responds with `401 Unauthorized`, the CLI now provides a detailed explanation along with guidance on
how to fix the problem (for example by re-running `codex auth login` or updating the API key).

## Testing

Run the unit tests with:

```bash
pytest
```
