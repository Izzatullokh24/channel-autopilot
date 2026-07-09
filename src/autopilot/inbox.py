"""Idea inbox: turn messages sent to the bot into queue files.

Each note becomes one markdown file with frontmatter in the (private) queue
repo. Only messages from the channel author are accepted — the bot is
public, and anything in the queue eventually publishes under the author's
name.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .telegram import TelegramClient

TASHKENT = timezone(timedelta(hours=5))


@dataclass
class IngestResult:
    saved: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    unknown_senders: dict[int, str] = field(default_factory=dict)


def _load_offset(queue_dir: Path) -> int | None:
    offset_file = queue_dir / "state" / "offset.json"
    if offset_file.exists():
        return json.loads(offset_file.read_text(encoding="utf-8"))["last_update_id"]
    return None


def _save_offset(queue_dir: Path, last_update_id: int) -> None:
    offset_file = queue_dir / "state" / "offset.json"
    offset_file.parent.mkdir(parents=True, exist_ok=True)
    offset_file.write_text(json.dumps({"last_update_id": last_update_id}), encoding="utf-8")


def _note_document(created: datetime, note_type: str, update_id: int, body: str, extra: dict | None = None) -> str:
    lines = [
        "---",
        f"id: {update_id}",
        f"created: {created.isoformat()}",
        "source: telegram",
        f"type: {note_type}",
        "status: new",
    ]
    for key, value in (extra or {}).items():
        lines.append(f"{key}: {value}")
    lines += ["---", "", body, ""]
    return "\n".join(lines)


def ingest(client: TelegramClient, queue_dir: Path, author_id: int | None, write: bool) -> IngestResult:
    """Pull pending bot messages and write them into the queue.

    With write=False nothing is persisted and the Telegram offset is not
    advanced, so a dry run never loses notes. With author_id=None runs in
    bootstrap mode: reports sender ids so the allowlist can be configured.
    """
    result = IngestResult()
    stored_offset = _load_offset(queue_dir)
    updates = client.get_updates(offset=stored_offset + 1 if stored_offset is not None else None)

    last_update_id = stored_offset
    for update in updates:
        update_id = update["update_id"]
        last_update_id = max(last_update_id or 0, update_id)
        message = update.get("message")
        if not message:
            result.skipped.append(f"u{update_id}: not a message")
            continue

        sender = message.get("from", {})
        sender_id = sender.get("id")
        sender_name = sender.get("username") or sender.get("first_name") or "?"
        if author_id is None:
            result.unknown_senders[sender_id] = sender_name
            continue
        if sender_id != author_id:
            result.skipped.append(f"u{update_id}: ignored sender {sender_id} (@{sender_name})")
            continue

        created = datetime.fromtimestamp(message["date"], tz=TASHKENT)
        stem = f"{created:%Y%m%d-%H%M%S}-u{update_id}"

        if message.get("text"):
            document = _note_document(created, "text", update_id, message["text"].strip())
        elif message.get("voice"):
            voice = message["voice"]
            media_rel = f"media/{stem}.ogg"
            if write:
                media_file = queue_dir / "queue" / media_rel
                media_file.parent.mkdir(parents=True, exist_ok=True)
                media_file.write_bytes(client.download_file(voice["file_id"]))
            document = _note_document(
                created,
                "voice",
                update_id,
                "(voice note — transcription pending)",
                extra={"media": media_rel, "duration_seconds": voice.get("duration", 0)},
            )
        else:
            result.skipped.append(f"u{update_id}: unsupported message type")
            continue

        note_rel = f"queue/{stem}.md"
        if write:
            note_file = queue_dir / note_rel
            note_file.parent.mkdir(parents=True, exist_ok=True)
            note_file.write_text(document, encoding="utf-8")
        result.saved.append(note_rel)

    if write and last_update_id is not None and last_update_id != stored_offset:
        _save_offset(queue_dir, last_update_id)

    return result
