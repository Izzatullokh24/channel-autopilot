"""Minimal Telegram Bot API client.

Uses plain HTTP calls instead of a bot framework: the pipeline only needs
to send messages, and the full API surface is one POST away.
"""

from __future__ import annotations

import os

import httpx

API_BASE = "https://api.telegram.org"


class TelegramError(RuntimeError):
    """Raised when the Bot API returns ok=false."""

    def __init__(self, method: str, description: str, error_code: int | None = None):
        self.method = method
        self.description = description
        self.error_code = error_code
        super().__init__(f"{method} failed ({error_code}): {description}")


class TelegramClient:
    def __init__(self, token: str | None = None, timeout: float = 30.0):
        self.token = token or os.environ["TELEGRAM_BOT_TOKEN"]
        self._http = httpx.Client(base_url=f"{API_BASE}/bot{self.token}", timeout=timeout)

    def call(self, method: str, **params) -> dict:
        response = self._http.post(f"/{method}", json=params)
        payload = response.json()
        if not payload.get("ok"):
            raise TelegramError(method, payload.get("description", "unknown error"), payload.get("error_code"))
        return payload["result"]

    def send_message(self, chat_id: str, text: str, parse_mode: str = "HTML") -> dict:
        """Post to a chat or channel. HTML parse mode: <b>, <i>, <code>, <a href>."""
        return self.call(
            "sendMessage",
            chat_id=chat_id,
            text=text,
            parse_mode=parse_mode,
            disable_web_page_preview=True,
        )

    def get_me(self) -> dict:
        """Identify the bot — cheap way to validate the token."""
        return self.call("getMe")

    def get_updates(self, offset: int | None = None) -> list[dict]:
        """Fetch pending messages sent to the bot.

        Passing offset=N+1 permanently discards updates <= N on Telegram's
        side, so callers must only advance the offset after persisting.
        """
        params: dict = {"timeout": 0, "allowed_updates": ["message"]}
        if offset is not None:
            params["offset"] = offset
        return self.call("getUpdates", **params)

    def download_file(self, file_id: str) -> bytes:
        """Download a file (e.g. a voice note) sent to the bot."""
        file_path = self.call("getFile", file_id=file_id)["file_path"]
        response = httpx.get(f"{API_BASE}/file/bot{self.token}/{file_path}", timeout=60.0)
        response.raise_for_status()
        return response.content

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "TelegramClient":
        return self

    def __exit__(self, *exc) -> None:
        self.close()
