# mm-knowhow

A terminal-first personal knowledge management system in the Zettelkasten style. Notes are plain Markdown files with YAML frontmatter, searchable via CLI, accessible to AI assistants, and compatible with graphical editors like Obsidian.

## Features

- **Zettelkasten-style notes** with bidirectional `[[links]]`, tags, and timestamps
- **CLI tool (`kh`)** for fast capture and search from the terminal
- **AI integration** via [CLAUDE.md](CLAUDE.md) (Claude Code) and a local [MCP server](mcp/server.py)
- **Obsidian-compatible** format (`[[id|Title]]` links, YAML frontmatter, flat directory)
- **Privacy-first** -- everything runs locally, no cloud, no external APIs, no model training
- **Zero dependencies** -- only Bash, Python 3 standard library, and `ripgrep`

## Requirements

- **Bash** 4+
- **ripgrep** (`rg`)
- **fzf** (optional, for interactive search)
- **Python 3.10+** (only for the MCP server)
- A text editor (defaults to `$EDITOR`, falls back to `nvim`)

Developed and tested on Termux (Android), but works on any Linux/macOS system.

## Installation

```bash
git clone https://github.com/YOUR_USER/mm-knowhow.git
cd mm-knowhow

# Make the CLI executable and add it to PATH
chmod +x bin/kh
echo 'export PATH="'"$(pwd)"'/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

On Termux:
```bash
pkg install ripgrep fzf python
```

On Debian/Ubuntu:
```bash
sudo apt install ripgrep fzf python3
```

On macOS:
```bash
brew install ripgrep fzf python3
```

## Usage

### Capture knowledge

```bash
# Create a note (opens your editor)
kh add "Docker Bridge Networking"

# Quick note without editor
kh quick "Git Rebase Tip" -m "Always use rebase --onto for moving commit ranges"

# Quick note via pipe
echo "Use rg -C 3 for context lines" | kh quick "ripgrep Context Flag"
```

### Find knowledge

```bash
# Full-text search (interactive with fzf)
kh search "docker"

# List all tags with counts
kh tags

# Find notes by tag
kh find-tag networking

# Show links to and from a note
kh links 20260329-docker-bridge-networking

# List recent notes
kh list
kh list 50
```

### Edit and manage

```bash
# Find and edit a note (fuzzy match or fzf)
kh edit docker
kh edit

# Show stats
kh stats
```

## Note format

Each note is a Markdown file in `notes/` with YAML frontmatter:

```markdown
---
id: "20260329-docker-bridge-networking"
title: "Docker Bridge Networking"
tags: [docker, networking, linux]
links: [20260315-container-basics]
created: "2026-03-29T14:30:00+0200"
updated: "2026-03-29T14:30:00+0200"
---

# Docker Bridge Networking

Your content here. Link to other notes with [[20260315-container-basics|Container Basics]].
```

- **ID**: `YYYYMMDD-slug` derived from title (lowercase, max 60 chars)
- **Tags**: flat list in frontmatter, lowercase
- **Links**: `[[note-id|Display Title]]` in body text (Obsidian-compatible)
- **Files**: stored flat in `notes/`, one `.md` per note

## AI integration

### Claude Code

The repository includes a [CLAUDE.md](CLAUDE.md) that instructs Claude Code how to read, search, and create notes. When working in this directory, Claude Code can:

- Search the knowledge base
- Create new notes from conversations
- Follow links between notes

No setup needed -- Claude Code reads `CLAUDE.md` automatically.

### MCP Server

A local MCP server exposes the knowledge base to any MCP-compatible AI client (Claude Code, Claude Desktop, etc.). It uses stdio transport with zero external dependencies.

**Available tools:**

| Tool | Description |
|------|-------------|
| `search_knowledge` | Full-text search across all notes |
| `get_note` | Read a specific note by ID |
| `add_note` | Create a new note |
| `list_tags` | List all tags with counts |
| `find_by_tag` | Find notes with a specific tag |
| `list_recent` | List most recent notes |

**Setup:**

Create a `.mcp.json` in the project root (already included):

```json
{
  "mcpServers": {
    "mm-knowhow": {
      "command": "python3",
      "args": ["mcp/server.py"]
    }
  }
}
```

The MCP server requires only Python 3 standard library -- no `pip install` needed.

## Obsidian compatibility

The `notes/` directory can be opened directly as an Obsidian vault. All features work out of the box:

- YAML frontmatter is recognized
- `[[id|Title]]` links resolve correctly
- Tags from frontmatter appear in Obsidian's tag pane

## Project structure

```
mm-knowhow/
├── README.md
├── CLAUDE.md           # AI assistant instructions
├── config.yml          # Configuration
├── .mcp.json           # MCP server registration
├── .gitignore
├── notes/              # All knowledge notes (flat)
├── templates/
│   └── default.md      # Note template
├── bin/
│   └── kh              # CLI tool (Bash)
└── mcp/
    └── server.py       # MCP server (Python, no dependencies)
```

## Privacy

- All data stays on your local filesystem
- The MCP server communicates only via stdio (no network ports)
- `CLAUDE.md` explicitly instructs AI assistants not to send data externally
- No telemetry, no analytics, no cloud sync

## License

MIT
