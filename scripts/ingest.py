"""Ingest ideas sent to the bot into the queue repo.

Usage:
    python scripts/ingest.py           # dry run: shows what would be ingested
    python scripts/ingest.py --write   # save notes + advance the offset

Environment:
    TELEGRAM_BOT_TOKEN   bot token
    AUTHOR_TELEGRAM_ID   your Telegram user id (allowlist); unset = bootstrap
    QUEUE_DIR            path to the queue repo checkout
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from autopilot.inbox import ingest  # noqa: E402
from autopilot.telegram import TelegramClient  # noqa: E402


def load_dotenv() -> None:
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
        sys.exit("TELEGRAM_BOT_TOKEN is not set.")

    write = "--write" in sys.argv
    author_raw = os.environ.get("AUTHOR_TELEGRAM_ID")
    author_id = int(author_raw) if author_raw else None
    queue_dir = Path(os.environ.get("QUEUE_DIR", "../channel-autopilot-queue")).resolve()

    if write and not queue_dir.is_dir():
        sys.exit(f"QUEUE_DIR does not exist: {queue_dir}")
    if author_id is None:
        print("AUTHOR_TELEGRAM_ID not set — bootstrap mode: listing senders, saving nothing.")

    with TelegramClient() as client:
        result = ingest(client, queue_dir, author_id, write=write)

    for sender_id, name in result.unknown_senders.items():
        print(f"sender: id={sender_id} (@{name})")
    for entry in result.skipped:
        print(f"skipped: {entry}")
    for note in result.saved:
        print(f"{'saved' if write else 'would save'}: {note}")
    if not (result.saved or result.skipped or result.unknown_senders):
        print("No pending updates.")


if __name__ == "__main__":
    main()
