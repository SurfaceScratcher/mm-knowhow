#!/usr/bin/env python3
"""mm-knowhow MCP Server — Keine externen Abhängigkeiten, reines JSON-RPC über stdio."""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
NOTES_DIR = PROJECT_ROOT / "notes"


# ---- Helpers ---------------------------------------------------------------

def slugify(title: str, max_len: int = 60) -> str:
    slug = title.lower()
    for old, new in [("ä", "ae"), ("ö", "oe"), ("ü", "ue"), ("ß", "ss")]:
        slug = slug.replace(old, new)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")
    return slug[:max_len]


def generate_id(title: str) -> str:
    return f"{datetime.now().strftime('%Y%m%d')}-{slugify(title)}"


def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse YAML-ish frontmatter without PyYAML. Returns (meta, body)."""
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    meta = {}
    for line in parts[1].strip().splitlines():
        line = line.strip()
        if not line or ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip().strip('"')
        # Parse simple YAML lists: [a, b, c]
        if val.startswith("[") and val.endswith("]"):
            items = [x.strip().strip('"') for x in val[1:-1].split(",") if x.strip()]
            meta[key] = items
        else:
            meta[key] = val
    return meta, parts[2].strip()


def parse_note(filepath: Path) -> dict:
    text = filepath.read_text(encoding="utf-8")
    meta, body = parse_frontmatter(text)
    meta["body"] = body
    meta["_path"] = str(filepath)
    return meta


def all_notes() -> list[dict]:
    notes = []
    for f in sorted(NOTES_DIR.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True):
        notes.append(parse_note(f))
    return notes


# ---- Tool implementations -------------------------------------------------

def search_knowledge(query: str) -> str:
    try:
        result = subprocess.run(
            ["rg", "-i", "-l", query, str(NOTES_DIR)],
            capture_output=True, text=True, timeout=10,
        )
        files = [f for f in result.stdout.strip().split("\n") if f]
    except (subprocess.TimeoutExpired, FileNotFoundError):
        files = []

    if not files:
        return f"Keine Treffer für: {query}"

    results = []
    for filepath in files[:20]:
        note = parse_note(Path(filepath))
        note_id = note.get("id", Path(filepath).stem)
        title = note.get("title", "Ohne Titel")
        tags = note.get("tags", [])

        try:
            ctx = subprocess.run(
                ["rg", "-i", "-C", "2", query, filepath],
                capture_output=True, text=True, timeout=5,
            )
            snippet = ctx.stdout.strip()[:500]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            snippet = ""

        tags_str = ", ".join(tags) if tags else "keine"
        results.append(f"## {title}\nID: {note_id}\nTags: {tags_str}\n\n{snippet}")

    return "\n\n---\n\n".join(results)


def get_note(note_id: str) -> str:
    filepath = NOTES_DIR / f"{note_id}.md"
    if not filepath.exists():
        matches = list(NOTES_DIR.glob(f"*{note_id}*"))
        if matches:
            filepath = matches[0]
        else:
            return f"Note nicht gefunden: {note_id}"
    return filepath.read_text(encoding="utf-8")


def add_note(title: str, content: str, tags: list[str] | None = None) -> str:
    tags = tags or []
    note_id = generate_id(title)
    filepath = NOTES_DIR / f"{note_id}.md"
    if filepath.exists():
        return f"Note existiert bereits: {note_id}"

    now = datetime.now().isoformat()
    tags_str = ", ".join(tags)
    filepath.write_text(
        f'---\nid: "{note_id}"\ntitle: "{title}"\ntags: [{tags_str}]\n'
        f'links: []\ncreated: "{now}"\nupdated: "{now}"\n---\n\n# {title}\n\n{content}\n',
        encoding="utf-8",
    )
    return f"Note erstellt: {note_id}"


def list_tags() -> str:
    tag_counts: dict[str, int] = {}
    for note in all_notes():
        for tag in note.get("tags", []):
            if isinstance(tag, str) and tag:
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    if not tag_counts:
        return "Keine Tags vorhanden."
    return "\n".join(f"{c:4d}  {t}" for t, c in sorted(tag_counts.items(), key=lambda x: -x[1]))


def find_by_tag(tag: str) -> str:
    matches = []
    for note in all_notes():
        if tag in note.get("tags", []):
            matches.append(f"{note.get('id', '?')}  {note.get('title', 'Ohne Titel')}")
    return "\n".join(matches) if matches else f"Keine Notizen mit Tag: {tag}"


def list_recent(count: int = 20) -> str:
    notes = all_notes()[:count]
    if not notes:
        return "Keine Notizen vorhanden."
    lines = []
    for n in notes:
        tags = n.get("tags", [])
        tag_str = f"  [{', '.join(tags)}]" if tags else ""
        lines.append(f"{n.get('id', '?')}  {n.get('title', 'Ohne Titel')}{tag_str}")
    return "\n".join(lines)


# ---- MCP Protocol (JSON-RPC over stdio) -----------------------------------

TOOLS = [
    {
        "name": "search_knowledge",
        "description": "Volltextsuche in der Wissensbasis.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "Suchbegriff"}},
            "required": ["query"],
        },
    },
    {
        "name": "get_note",
        "description": "Liest eine Note anhand ihrer ID.",
        "inputSchema": {
            "type": "object",
            "properties": {"note_id": {"type": "string", "description": "Note-ID"}},
            "required": ["note_id"],
        },
    },
    {
        "name": "add_note",
        "description": "Erstellt eine neue Wissensnotiz.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Titel"},
                "content": {"type": "string", "description": "Markdown-Inhalt"},
                "tags": {"type": "array", "items": {"type": "string"}, "description": "Tags", "default": []},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "list_tags",
        "description": "Listet alle Tags mit Anzahl auf.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "find_by_tag",
        "description": "Findet Notizen mit einem bestimmten Tag.",
        "inputSchema": {
            "type": "object",
            "properties": {"tag": {"type": "string", "description": "Tag-Name"}},
            "required": ["tag"],
        },
    },
    {
        "name": "list_recent",
        "description": "Listet die neuesten Notizen auf.",
        "inputSchema": {
            "type": "object",
            "properties": {"count": {"type": "integer", "description": "Anzahl", "default": 20}},
        },
    },
]

SERVER_INFO = {"name": "mm-knowhow", "version": "1.0.0"}
CAPABILITIES = {"tools": {}}


def handle_request(method: str, params: dict | None) -> dict | None:
    params = params or {}

    if method == "initialize":
        return {"protocolVersion": "2024-11-05", "serverInfo": SERVER_INFO, "capabilities": CAPABILITIES}

    if method == "notifications/initialized":
        return None  # notification, no response

    if method == "tools/list":
        return {"tools": TOOLS}

    if method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})
        result_text = dispatch_tool(name, args)
        return {"content": [{"type": "text", "text": result_text}]}

    return None


def dispatch_tool(name: str, args: dict) -> str:
    match name:
        case "search_knowledge":
            return search_knowledge(args["query"])
        case "get_note":
            return get_note(args["note_id"])
        case "add_note":
            return add_note(args["title"], args["content"], args.get("tags", []))
        case "list_tags":
            return list_tags()
        case "find_by_tag":
            return find_by_tag(args["tag"])
        case "list_recent":
            return list_recent(args.get("count", 20))
        case _:
            return f"Unbekanntes Tool: {name}"


def send_response(msg_id, result):
    response = {"jsonrpc": "2.0", "id": msg_id, "result": result}
    body = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(body.encode())}\r\n\r\n{body}")
    sys.stdout.flush()


def send_error(msg_id, code, message):
    response = {"jsonrpc": "2.0", "id": msg_id, "error": {"code": code, "message": message}}
    body = json.dumps(response)
    sys.stdout.write(f"Content-Length: {len(body.encode())}\r\n\r\n{body}")
    sys.stdout.flush()


def read_message() -> dict | None:
    """Read a JSON-RPC message with Content-Length header from stdin."""
    content_length = None
    while True:
        line = sys.stdin.readline()
        if not line:
            return None  # EOF
        line = line.strip()
        if not line:
            break  # empty line = end of headers
        if line.lower().startswith("content-length:"):
            content_length = int(line.split(":", 1)[1].strip())

    if content_length is None:
        return None

    body = sys.stdin.read(content_length)
    if not body:
        return None
    return json.loads(body)


def main():
    while True:
        msg = read_message()
        if msg is None:
            break

        method = msg.get("method")
        params = msg.get("params")
        msg_id = msg.get("id")

        try:
            result = handle_request(method, params)
        except Exception as e:
            if msg_id is not None:
                send_error(msg_id, -32603, str(e))
            continue

        # Notifications have no id and expect no response
        if msg_id is not None and result is not None:
            send_response(msg_id, result)


if __name__ == "__main__":
    main()
