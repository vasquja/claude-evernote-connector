# AGENTS.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

CLI tool and Python library for saving Claude AI conversations as Evernote notes. Converts markdown-formatted chat content to Evernote's ENML format.

## Development Commands

```bash
# Install in development mode
pip install -e .

# Install dependencies only
pip install -r requirements.txt

# Run CLI commands
claude-evernote verify              # Test Evernote connection
claude-evernote notebooks           # List notebooks
claude-evernote save -f chat.md     # Save a chat file
```

## Architecture

### Module Structure

- `claude_evernote/client.py` - Core Evernote API integration
  - `EvernoteConnector` class wraps the evernote3 SDK
  - `_chat_to_enml()` converts markdown to ENML (Evernote Markup Language)
  - Handles notebook creation/lookup with GUID caching

- `claude_evernote/cli.py` - Click-based CLI
  - Three commands: `save`, `notebooks`, `verify`
  - Config loading from `.env`, `~/.claude-evernote.env`, or environment variables

### Key Concepts

**ENML (Evernote Markup Language)**: Evernote's XML-based format. All note content must be wrapped in `<en-note>` tags with proper XML declaration and DOCTYPE. The `_chat_to_enml()` method handles this conversion.

**Chat Format Recognition**: The converter recognizes `Human:`/`User:` and `Assistant:`/`Claude:` prefixes and styles them differently (blue for human, green for assistant).

## Configuration

Environment variables (can be set in `.env`):
- `EVERNOTE_DEV_TOKEN` - Required for API access
- `EVERNOTE_SANDBOX` - Set to "true" for sandbox.evernote.com
- `EVERNOTE_NOTEBOOK` - Default notebook name

## Dependencies

Uses `evernote3` SDK which provides `EvernoteClient`, `Types` (for Note/Notebook objects), and `Errors` (for exception handling).
