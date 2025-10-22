from __future__ import annotations

import json
from io import BytesIO

import pytest

from codex_cli.client import CodexClient
from codex_cli.exceptions import UnauthorizedError


class DummyOpener:
    def __init__(self, error=None, response=None):
        self.error = error
        self.response = response
        self.requests = []

    def open(self, request):
        self.requests.append(request)
        if self.error:
            raise self.error
        return self.response


class DummyResponse:
    def __init__(self, status=200, body=b"", headers=None):
        self._status = status
        self._body = BytesIO(body)
        self.headers = headers or {}

    def read(self):
        return self._body.read()

    def getcode(self):
        return self._status

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


def make_http_error(code=401, message="Unauthorized", payload=None):
    body = BytesIO()
    if payload is not None:
        body.write(json.dumps(payload).encode("utf-8"))
        body.seek(0)
    return urllib_error.HTTPError(
        url="https://api.example.com/v1/test",
        code=code,
        msg=message,
        hdrs=None,
        fp=body,
    )


from urllib import error as urllib_error


def test_missing_api_key_raises_helpful_error(monkeypatch):
    monkeypatch.delenv("CODEX_API_KEY", raising=False)
    with pytest.raises(UnauthorizedError) as excinfo:
        CodexClient(api_key=None, opener=DummyOpener())
    message = str(excinfo.value)
    assert "CODEX_API_KEY" in message


def test_unauthorized_response_surface_hint(monkeypatch):
    error_payload = {"error": {"message": "Invalid API key", "code": "invalid_api_key"}}
    http_error = make_http_error(payload=error_payload)
    opener = DummyOpener(error=http_error)

    client = CodexClient(api_key="secret", base_url="https://api.example.com", opener=opener)

    with pytest.raises(UnauthorizedError) as excinfo:
        client.request("GET", "/status")

    message = str(excinfo.value)
    assert "401 Unauthorized" in message
    assert "Invalid API key" in message
    assert "CODEX_API_KEY" in message

    [request] = opener.requests
    assert request.get_header("Authorization") == "Bearer secret"


def test_successful_request_returns_response(monkeypatch):
    response = DummyResponse(status=204, body=b"", headers={"x-test": "1"})
    opener = DummyOpener(response=response)

    client = CodexClient(api_key="secret", base_url="https://api.example.com", opener=opener)

    result = client.request("GET", "/status")

    assert result.status == 204
    assert result.headers["x-test"] == "1"
    assert result.body == b""

