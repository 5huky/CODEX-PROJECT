"""HTTP client used by the Codex CLI."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Mapping, MutableMapping, Optional
from urllib import error as urllib_error
from urllib import request as urllib_request

from .exceptions import CodexError, UnauthorizedError

_DEFAULT_BASE_URL = "https://api.openai.com/v1"


@dataclass
class CodexResponse:
    """Simple container for HTTP responses."""

    status: int
    headers: Mapping[str, str]
    body: bytes

    def json(self) -> object:
        """Return the response body decoded as JSON."""

        if not self.body:
            return None
        return json.loads(self.body.decode("utf-8"))

    def text(self) -> str:
        """Return the response body decoded as UTF-8 text."""

        return self.body.decode("utf-8", errors="replace")


class CodexClient:
    """Minimal HTTP client responsible for talking to the Codex API."""

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        opener: Optional[urllib_request.OpenerDirector] = None,
    ) -> None:
        self.api_key = api_key or os.environ.get("CODEX_API_KEY")
        if not self.api_key:
            raise UnauthorizedError(
                "No Codex API key configured.",
                hint=(
                    "Provide one via the --api-key option or set the CODEX_API_KEY "
                    "environment variable."
                ),
            )

        configured_base_url = base_url or os.environ.get("CODEX_API_BASE_URL")
        self.base_url = (configured_base_url or _DEFAULT_BASE_URL).rstrip("/")
        self._opener = opener or urllib_request.build_opener()

    def request(
        self,
        method: str,
        path: str,
        *,
        headers: Optional[Mapping[str, str]] = None,
        data: Optional[bytes | str] = None,
    ) -> CodexResponse:
        """Perform an HTTP request and return a :class:`CodexResponse`."""

        url = _join_url(self.base_url, path)
        request_headers: MutableMapping[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "User-Agent": "codex-cli/0.1",
        }
        if headers:
            request_headers.update(headers)

        req = urllib_request.Request(url=url, method=method.upper(), headers=dict(request_headers))

        if data is not None:
            req.data = _prepare_body(data)

        try:
            with self._opener.open(req) as response:
                body = response.read()
                return CodexResponse(response.getcode(), response.headers, body)
        except urllib_error.HTTPError as exc:
            return self._handle_http_error(exc, url)
        except urllib_error.URLError as exc:  # pragma: no cover - network errors are rare in tests
            raise CodexError(f"Failed to connect to {url}: {exc.reason}") from exc

    def _handle_http_error(self, exc: urllib_error.HTTPError, url: str) -> CodexResponse:
        body = exc.read() if exc.fp else b""
        detail = _extract_error_detail(body)
        if exc.code == 401:
            raise UnauthorizedError(
                _format_unauthorized_message(detail),
                hint=(
                    "Double-check the CODEX_API_KEY value or run `codex auth login` "
                    "to refresh your credentials."
                ),
            ) from None
        raise CodexError(f"HTTP {exc.code} error while calling {url}: {detail}") from None


def _prepare_body(data: bytes | str) -> bytes:
    if isinstance(data, bytes):
        return data
    return data.encode("utf-8")


def _join_url(base: str, path: str) -> str:
    if not path:
        return base
    return f"{base}/{path.lstrip('/')}"


def _extract_error_detail(body: bytes) -> str:
    if not body:
        return "No additional error details were provided."
    text = body.decode("utf-8", errors="replace").strip()
    if not text:
        return "No additional error details were provided."
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        return text

    if isinstance(payload, dict):
        error = payload.get("error")
        if isinstance(error, dict):
            message = error.get("message")
            code = error.get("code")
            if message and code:
                return f"{message} (code: {code})"
            if message:
                return message
            if code:
                return str(code)
        if isinstance(error, str):
            return error
        message = payload.get("message")
        if isinstance(message, str):
            return message

    return text


def _format_unauthorized_message(detail: str) -> str:
    base = "Authentication failed with the Codex API (401 Unauthorized)."
    if detail:
        base = f"{base} Details: {detail}"
    return base
