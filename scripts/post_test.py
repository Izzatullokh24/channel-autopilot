"""Send a test post to the channel to verify the pipeline end-to-end.

Usage:
    python scripts/post_test.py            # dry run: validates token, prints the post
    python scripts/post_test.py --publish  # actually posts to the channel
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from autopilot.telegram import TelegramClient  # noqa: E402

TEST_POST = (
    "🤖 <b>Texnik test</b>\n\n"
    "Bu post GitHub Actions orqali avtomatik yuborildi — "
    "kanal uchun qurayotgan avtomatlashtirish tizimining birinchi qadami.\n\n"
    "<i>Tez orada bu haqda batafsil yozaman.</i>"
)


def load_dotenv() -> None:
    """Tiny .env loader so local runs work without extra dependencies."""
    env_file = Path(__file__).resolve().parent.parent / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
    load_dotenv()
    if not os.environ.get("TELEGRAM_BOT_TOKEN"):
        sys.exit(
            "TELEGRAM_BOT_TOKEN is not set. Locally: copy .env.example to .env and fill it in. "
            "In CI: add it as a GitHub Actions secret."
        )
    publish = "--publish" in sys.argv
    channel = os.environ.get("TELEGRAM_CHANNEL_ID", "@izzatullokhnotes")

    with TelegramClient() as client:
        me = client.get_me()
        print(f"Authenticated as @{me['username']} (id={me['id']})")

        if not publish:
            print(f"Dry run — would post to {channel}:\n\n{TEST_POST}")
            return

        result = client.send_message(channel, TEST_POST)
        print(f"Posted to {channel}, message_id={result['message_id']}")


if __name__ == "__main__":
    main()
