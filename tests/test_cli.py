"""Tests for the CLI module."""

import os
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from claude_evernote.cli import cli, get_config


class TestGetConfig:
    """Tests for the get_config function."""

    def test_returns_dict(self):
        """Test that get_config returns a dictionary."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_config()
            assert isinstance(config, dict)
            assert "token" in config
            assert "sandbox" in config
            assert "notebook" in config

    def test_reads_token_from_env(self):
        """Test reading token from environment."""
        with patch.dict(os.environ, {"EVERNOTE_DEV_TOKEN": "test-token"}):
            config = get_config()
            assert config["token"] == "test-token"

    def test_sandbox_default_false(self):
        """Test that sandbox defaults to False."""
        with patch.dict(os.environ, {}, clear=True):
            config = get_config()
            assert config["sandbox"] is False

    def test_sandbox_from_env(self):
        """Test reading sandbox setting from environment."""
        with patch.dict(os.environ, {"EVERNOTE_SANDBOX": "true"}):
            config = get_config()
            assert config["sandbox"] is True

    def test_notebook_from_env(self):
        """Test reading notebook from environment."""
        with patch.dict(os.environ, {"EVERNOTE_NOTEBOOK": "My Notebook"}):
            config = get_config()
            assert config["notebook"] == "My Notebook"


class TestCliSave:
    """Tests for the save command."""

    def test_requires_token(self):
        """Test that save command requires a token."""
        runner = CliRunner()
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(cli, ["save"], input="test content")
            assert result.exit_code != 0
            assert "No Evernote developer token" in result.output

    def test_requires_content(self):
        """Test that save command requires content."""
        runner = CliRunner()
        with patch.dict(os.environ, {"EVERNOTE_DEV_TOKEN": "test-token"}):
            with patch("claude_evernote.cli.EvernoteConnector"):
                result = runner.invoke(cli, ["save"], input="")
                assert result.exit_code != 0
                assert "No content provided" in result.output

    def test_saves_from_stdin(self):
        """Test saving content from stdin."""
        runner = CliRunner()
        with patch.dict(os.environ, {"EVERNOTE_DEV_TOKEN": "test-token"}):
            with patch("claude_evernote.cli.EvernoteConnector") as mock_connector:
                mock_instance = MagicMock()
                mock_instance.save_chat.return_value = "note-guid-123"
                mock_connector.return_value = mock_instance

                result = runner.invoke(cli, ["save"], input="Test content")
                assert result.exit_code == 0
                assert "saved successfully" in result.output

    def test_saves_from_file(self, tmp_path):
        """Test saving content from a file."""
        test_file = tmp_path / "chat.txt"
        test_file.write_text("Test content from file", encoding="utf-8")

        runner = CliRunner()
        with patch.dict(os.environ, {"EVERNOTE_DEV_TOKEN": "test-token"}):
            with patch("claude_evernote.cli.EvernoteConnector") as mock_connector:
                mock_instance = MagicMock()
                mock_instance.save_chat.return_value = "note-guid-123"
                mock_connector.return_value = mock_instance

                result = runner.invoke(cli, ["save", "--file", str(test_file)])
                assert result.exit_code == 0

    def test_saves_with_title(self):
        """Test saving with a custom title."""
        runner = CliRunner()
        with patch.dict(os.environ, {"EVERNOTE_DEV_TOKEN": "test-token"}):
            with patch("claude_evernote.cli.EvernoteConnector") as mock_connector:
                mock_instance = MagicMock()
                mock_instance.save_chat.return_value = "note-guid"
                mock_connector.return_value = mock_instance

                result = runner.invoke(
                    cli, ["save", "--title", "My Title"], input="content"
                )
                assert result.exit_code == 0
                mock_instance.save_chat.assert_called_once()
                call_kwargs = mock_instance.save_chat.call_args[1]
                assert call_kwargs["title"] == "My Title"

    def test_saves_with_tags(self):
        """Test saving with tags."""
        runner = CliRunner()
        with patch.dict(os.environ, {"EVERNOTE_DEV_TOKEN": "test-token"}):
            with patch("claude_evernote.cli.EvernoteConnector") as mock_connector:
                mock_instance = MagicMock()
                mock_instance.save_chat.return_value = "note-guid"
                mock_connector.return_value = mock_instance

                result = runner.invoke(
                    cli, ["save", "-g", "tag1", "-g", "tag2"], input="content"
                )
                assert result.exit_code == 0
                call_kwargs = mock_instance.save_chat.call_args[1]
                assert call_kwargs["tags"] == ["tag1", "tag2"]


class TestCliNotebooks:
    """Tests for the notebooks command."""

    def test_requires_token(self):
        """Test that notebooks command requires a token."""
        runner = CliRunner()
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(cli, ["notebooks"])
            assert result.exit_code != 0
            assert "No Evernote developer token" in result.output

    def test_lists_notebooks(self):
        """Test listing notebooks."""
        runner = CliRunner()
        with patch.dict(os.environ, {"EVERNOTE_DEV_TOKEN": "test-token"}):
            with patch("claude_evernote.cli.EvernoteConnector") as mock_connector:
                mock_notebook = MagicMock()
                mock_notebook.name = "Test Notebook"
                mock_notebook.defaultNotebook = False

                mock_instance = MagicMock()
                mock_instance.list_notebooks.return_value = [mock_notebook]
                mock_connector.return_value = mock_instance

                result = runner.invoke(cli, ["notebooks"])
                assert result.exit_code == 0
                assert "Test Notebook" in result.output

    def test_shows_default_notebook(self):
        """Test that default notebook is marked."""
        runner = CliRunner()
        with patch.dict(os.environ, {"EVERNOTE_DEV_TOKEN": "test-token"}):
            with patch("claude_evernote.cli.EvernoteConnector") as mock_connector:
                mock_notebook = MagicMock()
                mock_notebook.name = "Default"
                mock_notebook.defaultNotebook = True

                mock_instance = MagicMock()
                mock_instance.list_notebooks.return_value = [mock_notebook]
                mock_connector.return_value = mock_instance

                result = runner.invoke(cli, ["notebooks"])
                assert result.exit_code == 0
                assert "(default)" in result.output


class TestCliVerify:
    """Tests for the verify command."""

    def test_requires_token(self):
        """Test that verify command requires a token."""
        runner = CliRunner()
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(cli, ["verify"])
            assert result.exit_code != 0
            assert "No Evernote developer token" in result.output

    def test_verifies_connection(self):
        """Test verifying connection."""
        runner = CliRunner()
        with patch.dict(os.environ, {"EVERNOTE_DEV_TOKEN": "test-token"}):
            with patch("claude_evernote.cli.EvernoteConnector") as mock_connector:
                mock_user = MagicMock()
                mock_user.username = "testuser"
                mock_user.email = "test@example.com"

                mock_user_store = MagicMock()
                mock_user_store.getUser.return_value = mock_user

                mock_instance = MagicMock()
                mock_instance.client.get_user_store.return_value = mock_user_store
                mock_instance.list_notebooks.return_value = []
                mock_connector.return_value = mock_instance

                result = runner.invoke(cli, ["verify"])
                assert result.exit_code == 0
                assert "Connection successful" in result.output
                assert "testuser" in result.output


class TestCliVersion:
    """Tests for version option."""

    def test_shows_version(self):
        """Test that --version shows version."""
        runner = CliRunner()
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0
        assert "version" in result.output.lower()
