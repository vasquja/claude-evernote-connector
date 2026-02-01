# Claude to Evernote Connector

Save your Claude AI conversations as Evernote notes with a simple CLI tool.

## Features

- Save Claude chats to Evernote with formatted content
- Markdown support (headers, code blocks, lists, bold, italic)
- Custom titles, notebooks, and tags
- Pipe-friendly for automation
- Environment variable configuration

## Installation

```bash
cd ~/claude-evernote-connector
pip install -e .
```

Or install dependencies directly:

```bash
pip install -r requirements.txt
```

## Setup

### 1. Get an Evernote Developer Token

1. Visit https://www.evernote.com/api/DeveloperToken.action
2. Log in with your Evernote account
3. Click "Create a developer token"
4. Copy the token (starts with `S=`)

**Note:** Developer tokens may have limited availability. If unavailable, you'll need to request API access from Evernote.

### 2. Configure Your Token

Create a `.env` file in the project directory or `~/.claude-evernote.env`:

```bash
cp .env.example .env
# Edit .env and add your token
```

Or set an environment variable:

```bash
export EVERNOTE_DEV_TOKEN="S=s1:U=xxxxx:E=xxxxx:..."
```

### 3. Verify Connection

```bash
claude-evernote verify
```

## Usage

### Save a Chat from a File

```bash
claude-evernote save --file conversation.md --title "Python Help"
```

### Save from Clipboard (macOS)

```bash
pbpaste | claude-evernote save -t "Quick Chat"
```

### Save with Notebook and Tags

```bash
claude-evernote save -f chat.txt -n "AI Chats" -g claude -g coding -t "API Design Discussion"
```

### Interactive Input

```bash
claude-evernote save -t "My Chat"
# Type or paste content, then press Ctrl+D
```

### List Notebooks

```bash
claude-evernote notebooks
```

## Command Reference

### `save`

Save a chat to Evernote.

| Option | Short | Description |
|--------|-------|-------------|
| `--file` | `-f` | Input file containing chat content |
| `--title` | `-t` | Note title (auto-generated if not provided) |
| `--notebook` | `-n` | Target notebook name |
| `--tags` | `-g` | Tags to apply (use multiple times for multiple tags) |
| `--token` | | Override Evernote token |
| `--sandbox` | | Use sandbox environment |

### `notebooks`

List all notebooks in your Evernote account.

### `verify`

Verify your Evernote connection and display account info.

## Chat Format

The connector handles common chat formats:

```markdown
Human: How do I reverse a string in Python?

Assistant: You can reverse a string using slicing:

```python
text = "hello"
reversed_text = text[::-1]
print(reversed_text)  # "olleh"
```

Human: Thanks!
```

The connector automatically:
- Highlights Human/User messages in blue
- Highlights Assistant/Claude messages in green
- Formats code blocks with monospace font
- Converts markdown headers, lists, and emphasis

## Python API

You can also use the connector programmatically:

```python
from claude_evernote.client import EvernoteConnector

# Initialize connector
connector = EvernoteConnector(
    dev_token="your_token_here",
    sandbox=False
)

# Save a chat
chat_content = """
Human: What is Python?

Assistant: Python is a high-level programming language...
"""

note_guid = connector.save_chat(
    chat_content=chat_content,
    title="Python Question",
    notebook_name="Claude Chats",
    tags=["python", "claude"]
)

print(f"Created note: {note_guid}")
```

## Troubleshooting

### "Developer tokens are currently unavailable"

Evernote has restricted developer token access. Alternatives:
1. Request API access at https://dev.evernote.com/
2. Use OAuth authentication (requires registered application)

### "Authentication failed"

- Verify your token is correct
- Check if you're using sandbox vs production (tokens are environment-specific)
- Tokens expire after 1 year; generate a new one if needed

### "Rate limit reached"

Evernote has API rate limits. Wait a few minutes and try again.

## License

MIT
