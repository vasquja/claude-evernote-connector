"""Tests for the Evernote client module."""

from unittest.mock import MagicMock

from claude_evernote.client import EvernoteError


class TestChatToEnml:
    """Tests for the _chat_to_enml method."""

    def test_basic_text(self, connector):
        """Test basic text conversion."""
        result = connector._chat_to_enml("Hello world")
        assert "<div>Hello world</div>" in result
        assert result.startswith('<?xml version="1.0" encoding="UTF-8"?>')
        assert "<en-note>" in result
        assert "</en-note>" in result

    def test_html_escaping(self, connector):
        """Test that HTML entities are escaped."""
        result = connector._chat_to_enml("Test <script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_header_h1(self, connector):
        """Test H1 header conversion."""
        result = connector._chat_to_enml("# Main Title")
        assert "<h1>Main Title</h1>" in result

    def test_header_h2(self, connector):
        """Test H2 header conversion."""
        result = connector._chat_to_enml("## Section Title")
        assert "<h2>Section Title</h2>" in result

    def test_header_h3(self, connector):
        """Test H3 header conversion."""
        result = connector._chat_to_enml("### Subsection")
        assert "<h3>Subsection</h3>" in result

    def test_code_block(self, connector):
        """Test code block conversion."""
        content = "```python\ndef hello():\n    pass\n```"
        result = connector._chat_to_enml(content)
        assert "font-family: monospace" in result
        assert "background-color: #f5f5f5" in result
        assert "def hello():" in result

    def test_unclosed_code_block(self, connector):
        """Test handling of unclosed code blocks."""
        content = "```python\ndef hello():\n    pass"
        result = connector._chat_to_enml(content)
        # Should still include the code content
        assert "def hello():" in result
        assert "</en-note>" in result

    def test_inline_code(self, connector):
        """Test inline code conversion."""
        result = connector._chat_to_enml("Use `print()` function")
        assert "font-family: monospace" in result
        assert "print()" in result

    def test_bold_text(self, connector):
        """Test bold text conversion."""
        result = connector._chat_to_enml("This is **bold** text")
        assert "<strong>bold</strong>" in result

    def test_italic_text(self, connector):
        """Test italic text conversion."""
        result = connector._chat_to_enml("This is *italic* text")
        assert "<em>italic</em>" in result

    def test_bullet_list_dash(self, connector):
        """Test bullet list with dashes."""
        result = connector._chat_to_enml("- Item one\n- Item two")
        assert "<div>" in result

    def test_bullet_list_asterisk(self, connector):
        """Test bullet list with asterisks."""
        result = connector._chat_to_enml("* Item one\n* Item two")
        assert "<div>" in result

    def test_numbered_list(self, connector):
        """Test numbered list conversion."""
        result = connector._chat_to_enml("1. First\n2. Second")
        assert "1. First" in result
        assert "2. Second" in result

    def test_human_marker(self, connector):
        """Test Human: marker styling."""
        result = connector._chat_to_enml("Human: Hello there")
        assert "color: #0066cc" in result
        assert "font-weight: bold" in result

    def test_assistant_marker(self, connector):
        """Test Assistant: marker styling."""
        result = connector._chat_to_enml("Assistant: Hi!")
        assert "color: #009933" in result
        assert "font-weight: bold" in result

    def test_user_marker(self, connector):
        """Test User: marker styling."""
        result = connector._chat_to_enml("User: Hello")
        assert "color: #0066cc" in result

    def test_claude_marker(self, connector):
        """Test Claude: marker styling."""
        result = connector._chat_to_enml("Claude: Hello")
        assert "color: #009933" in result

    def test_empty_lines_become_br(self, connector):
        """Test that empty lines become line breaks."""
        result = connector._chat_to_enml("Line 1\n\nLine 2")
        assert "<br/>" in result

    def test_complex_content(self, connector, sample_chat_content):
        """Test complex content with multiple elements."""
        result = connector._chat_to_enml(sample_chat_content)
        assert "<h1>Chat with Claude</h1>" in result
        assert "color: #0066cc" in result  # Human marker
        assert "color: #009933" in result  # Assistant marker
        assert "<strong>bold</strong>" in result
        assert "<em>italic</em>" in result

    def test_inline_code_preserves_asterisks(self, connector):
        """Test that asterisks inside inline code are not converted to italic."""
        result = connector._chat_to_enml("Use `*args` in Python")
        # The asterisk should be preserved inside code, not converted to <em>
        assert "*args" in result
        assert "<em>args</em>" not in result

    def test_inline_code_with_special_chars(self, connector):
        """Test inline code with HTML special characters."""
        result = connector._chat_to_enml("Use `<div>` tag")
        assert "&lt;div&gt;" in result
        assert "<div>" not in result or result.count("<div>") == 1  # Only wrapper div


class TestListNotebooks:
    """Tests for the list_notebooks method."""

    def test_returns_notebooks(self, connector, mock_note_store):
        """Test listing notebooks."""
        mock_notebook = MagicMock()
        mock_notebook.name = "Test Notebook"
        mock_notebook.guid = "test-guid"
        mock_note_store.listNotebooks.return_value = [mock_notebook]

        # Clear cache
        connector._notebooks_cache = None

        result = connector.list_notebooks()
        assert len(result) == 1
        assert result[0].name == "Test Notebook"

    def test_caches_results(self, connector, mock_note_store):
        """Test that results are cached."""
        mock_notebook = MagicMock()
        mock_note_store.listNotebooks.return_value = [mock_notebook]

        # Clear cache
        connector._notebooks_cache = None

        connector.list_notebooks()
        connector.list_notebooks()

        # Should only be called once due to caching
        assert mock_note_store.listNotebooks.call_count == 1


class TestGetNotebookGuid:
    """Tests for the get_notebook_guid method."""

    def test_returns_none_for_empty_name(self, connector):
        """Test that None is returned for empty notebook name."""
        assert connector.get_notebook_guid(None) is None
        assert connector.get_notebook_guid("") is None

    def test_finds_existing_notebook(self, connector, mock_note_store):
        """Test finding an existing notebook by name."""
        mock_notebook = MagicMock()
        mock_notebook.name = "My Notebook"
        mock_notebook.guid = "notebook-guid-123"
        mock_note_store.listNotebooks.return_value = [mock_notebook]
        connector._notebooks_cache = None

        result = connector.get_notebook_guid("My Notebook")
        assert result == "notebook-guid-123"

    def test_case_insensitive_match(self, connector, mock_note_store):
        """Test case-insensitive notebook name matching."""
        mock_notebook = MagicMock()
        mock_notebook.name = "My Notebook"
        mock_notebook.guid = "notebook-guid-123"
        mock_note_store.listNotebooks.return_value = [mock_notebook]
        connector._notebooks_cache = None

        result = connector.get_notebook_guid("my notebook")
        assert result == "notebook-guid-123"

    def test_creates_notebook_if_not_found(self, connector, mock_note_store):
        """Test that a new notebook is created if not found."""
        mock_note_store.listNotebooks.return_value = []
        mock_created = MagicMock()
        mock_created.guid = "new-notebook-guid"
        mock_note_store.createNotebook.return_value = mock_created
        connector._notebooks_cache = None

        result = connector.get_notebook_guid("New Notebook")
        assert result == "new-notebook-guid"
        mock_note_store.createNotebook.assert_called_once()


class TestCreateNotebook:
    """Tests for the create_notebook method."""

    def test_creates_notebook(self, connector, mock_note_store):
        """Test notebook creation."""
        mock_created = MagicMock()
        mock_created.guid = "created-guid"
        mock_note_store.createNotebook.return_value = mock_created

        result = connector.create_notebook("Test Notebook")
        assert result == "created-guid"

    def test_invalidates_cache(self, connector, mock_note_store):
        """Test that cache is invalidated after creation."""
        connector._notebooks_cache = ["cached_data"]
        mock_created = MagicMock()
        mock_created.guid = "created-guid"
        mock_note_store.createNotebook.return_value = mock_created

        connector.create_notebook("Test")
        assert connector._notebooks_cache is None


class TestSaveChat:
    """Tests for the save_chat method."""

    def test_saves_with_title(self, connector, mock_note_store):
        """Test saving a chat with a custom title."""
        mock_note = MagicMock()
        mock_note.guid = "note-guid"
        mock_note_store.createNote.return_value = mock_note

        result = connector.save_chat("Hello", title="My Title")
        assert result == "note-guid"

    def test_saves_with_auto_title(self, connector, mock_note_store):
        """Test saving a chat with auto-generated title."""
        mock_note = MagicMock()
        mock_note.guid = "note-guid"
        mock_note_store.createNote.return_value = mock_note

        result = connector.save_chat("Hello")
        assert result == "note-guid"

    def test_saves_with_tags(self, connector, mock_note_store):
        """Test saving a chat with tags."""
        mock_note = MagicMock()
        mock_note.guid = "note-guid"
        mock_note_store.createNote.return_value = mock_note

        connector.save_chat("Hello", tags=["tag1", "tag2"])
        mock_note_store.createNote.assert_called_once()

    def test_saves_to_notebook(self, connector, mock_note_store):
        """Test saving a chat to a specific notebook."""
        mock_notebook = MagicMock()
        mock_notebook.name = "Target"
        mock_notebook.guid = "target-guid"
        mock_note_store.listNotebooks.return_value = [mock_notebook]
        connector._notebooks_cache = None

        mock_note = MagicMock()
        mock_note.guid = "note-guid"
        mock_note_store.createNote.return_value = mock_note

        result = connector.save_chat("Hello", notebook_name="Target")
        assert result == "note-guid"


class TestEvernoteError:
    """Tests for the EvernoteError exception."""

    def test_is_exception(self):
        """Test that EvernoteError is an Exception."""
        error = EvernoteError("test message")
        assert isinstance(error, Exception)
        assert str(error) == "test message"
