"""Pytest configuration and fixtures."""

from unittest.mock import MagicMock, patch

import pytest


@pytest.fixture
def mock_note_store():
    """Create a mock note store."""
    store = MagicMock()
    store.listNotebooks.return_value = []
    return store


@pytest.fixture
def mock_evernote_client(mock_note_store):
    """Create a mock Evernote client."""
    with patch("claude_evernote.client.EvernoteClient") as mock_client:
        instance = MagicMock()
        instance.get_note_store.return_value = mock_note_store
        mock_client.return_value = instance
        yield mock_client


@pytest.fixture
def connector(mock_evernote_client, mock_note_store):
    """Create an EvernoteConnector with mocked dependencies."""
    from claude_evernote.client import EvernoteConnector

    conn = EvernoteConnector("fake_token", sandbox=True)
    return conn


@pytest.fixture
def sample_chat_content():
    """Sample chat content for testing."""
    return (
        "# Chat with Claude\n\n"
        "Human: Hello, how are you?\n\n"
        "Assistant: I'm doing well, thank you!\n\n"
        "## Code Example\n\n"
        "```python\n"
        "def hello():\n"
        "    print('Hello')\n"
        "```\n\n"
        "- Item 1\n"
        "- Item 2\n\n"
        "Some **bold** and *italic* text with `inline code`.\n"
    )
