"""Evernote client for creating notes from Claude chats."""

import html
import logging
import re
from datetime import datetime
from typing import Optional

import evernote.edam.error.ttypes as Errors
import evernote.edam.type.ttypes as Types
from evernote.api.client import EvernoteClient

# Configure logging
logger = logging.getLogger(__name__)

# Style constants for ENML output
STYLES = {
    "code_block": "font-family: monospace; background-color: #f5f5f5; padding: 10px; margin: 10px 0; white-space: pre-wrap;",
    "inline_code": "font-family: monospace; background-color: #f0f0f0; padding: 2px 4px;",
    "human": "color: #0066cc; font-weight: bold; margin-top: 15px;",
    "assistant": "color: #009933; font-weight: bold; margin-top: 15px;",
}


class EvernoteConnector:
    """Connector for saving Claude chats to Evernote."""

    def __init__(self, dev_token: str, sandbox: bool = False) -> None:
        """
        Initialize the Evernote connector.

        Args:
            dev_token: Evernote developer token
            sandbox: Use sandbox environment (default: False for production)
        """
        logger.debug("Initializing EvernoteConnector (sandbox=%s)", sandbox)
        self.client = EvernoteClient(token=dev_token, sandbox=sandbox)
        self.note_store = self.client.get_note_store()
        self._notebooks_cache: Optional[list[Types.Notebook]] = None

    def list_notebooks(self) -> list[Types.Notebook]:
        """List all notebooks in the user's account."""
        if self._notebooks_cache is None:
            logger.debug("Fetching notebooks from Evernote")
            self._notebooks_cache = self.note_store.listNotebooks()
        return self._notebooks_cache

    def get_notebook_guid(self, notebook_name: Optional[str] = None) -> Optional[str]:
        """
        Get the GUID for a notebook by name.

        Args:
            notebook_name: Name of the notebook. If None, returns None (uses default).

        Returns:
            Notebook GUID or None for default notebook.
        """
        if not notebook_name:
            return None

        notebooks = self.list_notebooks()
        for notebook in notebooks:
            if notebook.name.lower() == notebook_name.lower():
                logger.debug("Found notebook '%s' with GUID: %s", notebook_name, notebook.guid)
                return notebook.guid

        # Notebook not found, create it
        logger.info("Notebook '%s' not found, creating it", notebook_name)
        return self.create_notebook(notebook_name)

    def create_notebook(self, name: str) -> str:
        """
        Create a new notebook.

        Args:
            name: Name for the new notebook.

        Returns:
            GUID of the created notebook.
        """
        notebook = Types.Notebook()
        notebook.name = name
        created = self.note_store.createNotebook(notebook)
        self._notebooks_cache = None  # Invalidate cache
        logger.info("Created notebook '%s' with GUID: %s", name, created.guid)
        return created.guid

    def save_chat(
        self,
        chat_content: str,
        title: Optional[str] = None,
        notebook_name: Optional[str] = None,
        tags: Optional[list[str]] = None,
    ) -> str:
        """
        Save a Claude chat as an Evernote note.

        Args:
            chat_content: The chat content (markdown format supported)
            title: Note title (auto-generated if not provided)
            notebook_name: Target notebook name (uses default if not specified)
            tags: List of tags to apply to the note

        Returns:
            GUID of the created note.

        Raises:
            ValueError: If chat_content is empty.
            EvernoteError: If note creation fails.
        """
        if not chat_content or not chat_content.strip():
            raise ValueError("chat_content cannot be empty")

        note = Types.Note()

        # Set title
        if title:
            note.title = title
        else:
            note.title = f"Claude Chat - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        logger.debug("Creating note with title: %s", note.title)

        # Set notebook
        notebook_guid = self.get_notebook_guid(notebook_name)
        if notebook_guid:
            note.notebookGuid = notebook_guid

        # Set tags
        if tags:
            note.tagNames = tags
            logger.debug("Adding tags: %s", tags)

        # Convert chat content to ENML
        note.content = self._chat_to_enml(chat_content)

        # Create the note
        try:
            created_note = self.note_store.createNote(note)
            logger.info("Note created with GUID: %s", created_note.guid)
            return created_note.guid
        except Errors.EDAMUserException as e:
            logger.error("Failed to create note: %s", e.errorCode)
            raise EvernoteError(f"Failed to create note: {e.errorCode}") from e
        except Errors.EDAMSystemException as e:
            logger.error("Evernote system error: %s", e.message)
            raise EvernoteError(f"Evernote system error: {e.message}") from e

    def _chat_to_enml(self, content: str) -> str:
        """
        Convert chat content (markdown) to Evernote Markup Language (ENML).

        Args:
            content: Chat content in markdown format.

        Returns:
            ENML-formatted content.
        """
        # Start with ENML header
        enml = '<?xml version="1.0" encoding="UTF-8"?>'
        enml += '<!DOCTYPE en-note SYSTEM "http://xml.evernote.com/pub/enml2.dtd">'
        enml += "<en-note>"

        # Process the content
        lines = content.split("\n")
        in_code_block = False
        code_block_content: list[str] = []

        for line in lines:
            # Handle code blocks
            if line.startswith("```"):
                if in_code_block:
                    # End code block
                    code_text = html.escape("\n".join(code_block_content))
                    enml += f'<div style="{STYLES["code_block"]}">{code_text}</div>'
                    code_block_content = []
                    in_code_block = False
                else:
                    # Start code block
                    in_code_block = True
                continue

            if in_code_block:
                code_block_content.append(line)
                continue

            # Handle empty lines
            if not line.strip():
                enml += "<br/>"
                continue

            # Handle headers (check before escaping)
            if line.startswith("### "):
                enml += f"<h3>{html.escape(line[4:])}</h3>"
            elif line.startswith("## "):
                enml += f"<h2>{html.escape(line[3:])}</h2>"
            elif line.startswith("# "):
                enml += f"<h1>{html.escape(line[2:])}</h1>"
            # Handle Human/Assistant markers (common in Claude chats)
            elif line.startswith("Human:") or line.startswith("User:"):
                enml += f'<div style="{STYLES["human"]}">{html.escape(line)}</div>'
            elif line.startswith("Assistant:") or line.startswith("Claude:"):
                enml += f'<div style="{STYLES["assistant"]}">{html.escape(line)}</div>'
            # Handle bullet points
            elif line.strip().startswith("- ") or line.strip().startswith("* "):
                bullet_content = html.escape(line.strip()[2:])
                enml += f"<div>- {bullet_content}</div>"
            # Handle numbered lists
            elif re.match(r"^\d+\.\s", line.strip()):
                enml += f"<div>{html.escape(line)}</div>"
            # Handle inline formatting
            else:
                enml += f"<div>{self._process_inline_formatting(line)}</div>"

        # Close any unclosed code block
        if in_code_block and code_block_content:
            code_text = html.escape("\n".join(code_block_content))
            enml += f'<div style="{STYLES["code_block"]}">{code_text}</div>'
            logger.debug("Closed unclosed code block at end of content")

        enml += "</en-note>"
        return enml

    def _process_inline_formatting(self, line: str) -> str:
        """
        Process inline markdown formatting (code, bold, italic).

        Uses placeholder approach to prevent formatting inside code spans.

        Args:
            line: A single line of text to process.

        Returns:
            Line with inline formatting converted to HTML.
        """
        # First, extract and replace inline code with placeholders
        # This prevents bold/italic patterns from matching inside code
        code_blocks: list[str] = []
        placeholder_template = "\x00CODE{}\x00"

        def save_code(match: re.Match[str]) -> str:
            code_blocks.append(match.group(1))
            return placeholder_template.format(len(code_blocks) - 1)

        # Extract inline code first
        processed = re.sub(r"`([^`]+)`", save_code, line)

        # Now escape HTML entities
        processed = html.escape(processed)

        # Convert **bold** to strong
        processed = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", processed)

        # Convert *italic* to em (only single asterisks, not inside bold)
        processed = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", processed)

        # Restore code blocks with proper styling
        for i, code in enumerate(code_blocks):
            escaped_code = html.escape(code)
            styled_code = f'<span style="{STYLES["inline_code"]}">{escaped_code}</span>'
            processed = processed.replace(
                html.escape(placeholder_template.format(i)),
                styled_code
            )

        return processed


class EvernoteError(Exception):
    """Custom exception for Evernote-related errors."""

    pass
