"""Command line interface for the Codex CLI."""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Optional

from .client import CodexClient
from .exceptions import CodexError, UnauthorizedError


def build_parser() -> argparse.ArgumentParser:
    parent = argparse.ArgumentParser(add_help=False)
    parent.add_argument(
        "--api-key",
        dest="api_key",
        help="Codex API key. Overrides the CODEX_API_KEY environment variable.",
    )
    parent.add_argument(
        "--base-url",
        dest="base_url",
        help="Override the API base URL. Defaults to https://api.openai.com/v1.",
    )

    parser = argparse.ArgumentParser(
        description="Utility commands for interacting with the Codex API.",
        parents=[parent],
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command")

    status_parser = subparsers.add_parser(
        "status",
        parents=[parent],
        help="Check connectivity with the Codex API.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    status_parser.add_argument(
        "--path",
        default="/v1/models",
        help="Endpoint path to call when performing the connectivity check.",
    )
    status_parser.add_argument(
        "--method",
        default="GET",
        help="HTTP method to use for the connectivity check.",
    )
    status_parser.set_defaults(handler=_handle_status)

    return parser


def main(argv: Optional[Iterable[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    handler = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return 1

    client_kwargs = {}
    if getattr(args, "api_key", None):
        client_kwargs["api_key"] = args.api_key
    if getattr(args, "base_url", None):
        client_kwargs["base_url"] = args.base_url

    try:
        client = CodexClient(**client_kwargs)
    except UnauthorizedError as exc:
        _print_error(str(exc))
        return 1
    except CodexError as exc:
        _print_error(str(exc))
        return 1

    return handler(args, client)


def _handle_status(args: argparse.Namespace, client: CodexClient) -> int:
    try:
        response = client.request(args.method, args.path)
    except UnauthorizedError as exc:
        _print_error(str(exc))
        return 1
    except CodexError as exc:
        _print_error(str(exc))
        return 1

    message = f"Successfully connected to the Codex API (HTTP {response.status})."
    if response.body:
        message = f"{message} Response size: {len(response.body)} bytes."
    print(message)
    return 0


def _print_error(message: str) -> None:
    print(f"Error: {message}", file=sys.stderr)

