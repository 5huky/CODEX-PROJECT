from __future__ import annotations

from unittest.mock import patch

from codex_cli import main
from codex_cli.exceptions import UnauthorizedError


def test_status_command_surface_authentication_hint(capsys):
    error_message = (
        "Authentication failed with the Codex API (401 Unauthorized). Details: Invalid token"
    )
    hint = "Double-check the CODEX_API_KEY value or run `codex auth login` to refresh your credentials."

    with patch("codex_cli.cli.CodexClient") as mock_client:
        instance = mock_client.return_value
        instance.request.side_effect = UnauthorizedError(error_message, hint=hint)

        exit_code = main(["status", "--api-key", "dummy"])  # allow per-command API key

    assert exit_code == 1
    captured = capsys.readouterr()
    assert "401 Unauthorized" in captured.err
    assert "CODEX_API_KEY" in captured.err
    assert "codex auth login" in captured.err


def test_status_command_success_prints_confirmation(capsys):
    with patch("codex_cli.cli.CodexClient") as mock_client:
        instance = mock_client.return_value
        response = instance.request.return_value
        response.status = 200
        response.body = b"{}"

        exit_code = main(["status", "--api-key", "dummy"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert "Successfully connected" in out


def test_version_command_prints_package_version(capsys):
    with patch("codex_cli.cli._determine_version", return_value="1.2.3"):
        exit_code = main(["version"])

    assert exit_code == 0
    out = capsys.readouterr().out
    assert out.strip() == "codex-cli 1.2.3"
