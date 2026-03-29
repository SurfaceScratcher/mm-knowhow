# mm-knowhow — Persönliche Wissensbasis

## Was ist das?
Ein Zettelkasten-System für persönliches Wissensmanagement. Alle Daten sind Markdown-Dateien mit YAML-Frontmatter im Verzeichnis `notes/`.

## DATENSCHUTZ — KRITISCH
- NIEMALS Noten-Inhalte an externe Dienste oder APIs senden
- NIEMALS Cloud-Sync oder externe Uploads vorschlagen
- Alle Operationen bleiben lokal auf diesem Dateisystem
- Beim Extrahieren von Wissen aus Gesprächen: nur als lokale Notizen speichern

## Verzeichnisstruktur
- `notes/`       — Alle Wissensnotizen (flaches Verzeichnis, eine .md pro Note)
- `templates/`   — Noten-Vorlagen
- `bin/kh`       — CLI-Tool (Bash)
- `mcp/`         — MCP-Server (Python)
- `config.yml`   — Konfiguration

## Noten-Format
Jede Note ist eine Markdown-Datei in `notes/` mit YAML-Frontmatter:

```yaml
---
id: "YYYYMMDD-slug-aus-titel"
title: "Menschenlesbarer Titel"
tags: [tag1, tag2, tag3]
links: [andere-note-id-1, andere-note-id-2]
created: "ISO-8601 Zeitstempel"
updated: "ISO-8601 Zeitstempel"
---
```

Body ist Standard-Markdown. Verlinke auf andere Notizen mit `[[note-id|Anzeigename]]` Syntax (z.B. `[[20260329-docker-networking|Docker Networking]]`).

## Notizen suchen
- Volltext: `rg -i "query" notes/`
- Nach Tag: `rg 'tags:.*tagname' notes/`
- Nach Titel: `rg '^title:.*query' notes/ -i`
- Alle Note-IDs: `ls notes/*.md | sed 's|notes/||;s|\.md||'`
- Backlinks finden: `rg '\[\[note-id(\|[^\]]+)?\]\]' notes/`

## Neue Note erstellen
1. ID generieren: `YYYYMMDD-slug` (z.B. `20260329-docker-networking`)
2. Slug-Regeln: Kleinbuchstaben, Umlaute auflösen (ä→ae), Sonderzeichen→Bindestrich, max 60 Zeichen
3. Datei erstellen: `notes/{id}.md`
4. Frontmatter-Format wie oben verwenden
5. Tags: Kleinbuchstaben, Bindestrich für Mehrwort-Tags
6. `[[andere-note-id|Titel der Note]]` Links im Body für Verknüpfungen

## Wissen aus Gesprächen extrahieren
Wenn der User dich bittet, Wissen aus einem Gespräch zu speichern:
1. Kernaussage, Technik oder Fakt identifizieren
2. Passenden Titel und Slug generieren
3. Relevante Tags aus bestehenden wählen (prüfe mit `rg -oN 'tags: \[([^\]]*)\]' notes/ --replace '$1' | tr ',' '\n' | sed 's/^ *//' | sort -u`)
4. Note in `notes/` schreiben im obigen Format
5. Falls verwandte Notizen existieren: `[[note-id|Titel]]` Links in beide Richtungen setzen
6. Dem User bestätigen, was gespeichert wurde

## CLI-Tool
Das `kh` Kommando in `bin/` bietet: add, quick, search, tags, find-tag, links, list, edit, stats.
Nutze `kh help` für Details.
