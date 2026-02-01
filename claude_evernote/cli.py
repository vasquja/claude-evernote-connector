"""Command-line interface for Claude-Evernote connector."""

import logging
import os
import sys
from pathlib import Path
from typing import Optional

import click
from dotenv import load_dotenv

from .client import EvernoteConnector, EvernoteError

# Configure logging
logger = logging.getLogger(__name__)


def get_config() -> dict[str, Optional[str] | bool]:
    """
    Load configuration from environment variables.

    Returns:
        Dictionary containing token, sandbox, and notebook settings.
    """
    # Try to load .env from current directory or home directory
    env_paths = [
        Path.cwd() / ".env",
        Path.home() / ".claude-evernote.env",
        Path(__file__).parent.parent / ".env",
    ]

    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            logger.debug("Loaded environment from %s", env_path)
            break

    return {
        "token": os.getenv("EVERNOTE_DEV_TOKEN"),
        "sandbox": os.getenv("EVERNOTE_SANDBOX", "false").lower() == "true",
        "notebook": os.getenv("EVERNOTE_NOTEBOOK", ""),
    }


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging for the CLI.

    Args:
        verbose: If True, set logging level to DEBUG.
    """
    level = logging.DEBUG if verbose else logging.WARNING
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


@click.group()
@click.version_option()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging")
def cli(verbose: bool) -> None:
    """Claude to Evernote Connector - Save Claude chats as Evernote notes."""
    setup_logging(verbose)


@cli.command()
@click.option("--title", "-t", help="Title for the note (auto-generated if not provided)")
@click.option("--notebook", "-n", help="Target notebook name")
@click.option("--tags", "-g", multiple=True, help="Tags to apply (can be used multiple times)")
@click.option("--file", "-f", "input_file", type=click.Path(exists=True), help="Input file containing chat content")
@click.option("--token", envvar="EVERNOTE_DEV_TOKEN", help="Evernote developer token")
@click.option("--sandbox", is_flag=True, help="Use Evernote sandbox environment")
def save(
    title: Optional[str],
    notebook: Optional[str],
    tags: tuple[str, ...],
    input_file: Optional[str],
    token: Optional[str],
    sandbox: bool,
) -> None:
    """
    Save a Claude chat to Evernote.

    Chat content can be provided via:
    - A file using --file
    - Piped input (e.g., cat chat.md | claude-evernote save)
    - Interactive input (type or paste, then Ctrl+D to finish)

    Examples:
        claude-evernote save --file chat.txt --title "My Chat"
        cat conversation.md | claude-evernote save -n "Claude Chats"
        claude-evernote save -t "Quick Note" -g claude -g ai
    """
    config = get_config()

    # Get token from args or config
    dev_token = token or config.get("token")
    if not dev_token:
        click.echo("Error: No Evernote developer token provided.", err=True)
        click.echo("Set EVERNOTE_DEV_TOKEN environment variable or use --token", err=True)
        click.echo("\nGet a token at: https://www.evernote.com/api/DeveloperToken.action", err=True)
        sys.exit(1)

    # Get sandbox setting
    use_sandbox = sandbox or bool(config.get("sandbox"))

    # Get notebook from args or config
    notebook_config = config.get("notebook")
    target_notebook = notebook or (notebook_config if notebook_config else None)

    # Read chat content
    if input_file:
        logger.debug("Reading content from file: %s", input_file)
        with open(input_file, encoding="utf-8") as f:
            chat_content = f.read()
    elif not sys.stdin.isatty():
        # Reading from pipe
        logger.debug("Reading content from stdin pipe")
        chat_content = sys.stdin.read()
    else:
        # Interactive input
        click.echo("Enter chat content (Ctrl+D when done):")
        chat_content = sys.stdin.read()

    if not chat_content.strip():
        click.echo("Error: No content provided.", err=True)
        sys.exit(1)

    # Convert tags tuple to list
    tag_list = list(tags) if tags else None

    # Save to Evernote
    try:
        logger.info("Connecting to Evernote (sandbox=%s)", use_sandbox)
        connector = EvernoteConnector(str(dev_token), sandbox=use_sandbox)
        note_guid = connector.save_chat(
            chat_content=chat_content,
            title=title,
            notebook_name=target_notebook,
            tags=tag_list,
        )
        click.echo("Note saved successfully!")
        click.echo(f"  GUID: {note_guid}")
        if target_notebook:
            click.echo(f"  Notebook: {target_notebook}")
        logger.info("Note saved with GUID: %s", note_guid)
    except EvernoteError as e:
        logger.error("Evernote error: %s", e)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ConnectionError as e:
        logger.error("Connection error: %s", e)
        click.echo(f"Connection error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--token", envvar="EVERNOTE_DEV_TOKEN", help="Evernote developer token")
@click.option("--sandbox", is_flag=True, help="Use Evernote sandbox environment")
def notebooks(token: Optional[str], sandbox: bool) -> None:
    """List all notebooks in your Evernote account."""
    config = get_config()

    dev_token = token or config.get("token")
    if not dev_token:
        click.echo("Error: No Evernote developer token provided.", err=True)
        sys.exit(1)

    use_sandbox = sandbox or bool(config.get("sandbox"))

    try:
        logger.info("Connecting to Evernote to list notebooks")
        connector = EvernoteConnector(str(dev_token), sandbox=use_sandbox)
        notebook_list = connector.list_notebooks()

        click.echo(f"Found {len(notebook_list)} notebooks:\n")
        for nb in notebook_list:
            default_marker = " (default)" if nb.defaultNotebook else ""
            click.echo(f"  - {nb.name}{default_marker}")
    except EvernoteError as e:
        logger.error("Evernote error: %s", e)
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ConnectionError as e:
        logger.error("Connection error: %s", e)
        click.echo(f"Connection error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option("--token", envvar="EVERNOTE_DEV_TOKEN", help="Evernote developer token")
@click.option("--sandbox", is_flag=True, help="Use Evernote sandbox environment")
def verify(token: Optional[str], sandbox: bool) -> None:
    """Verify your Evernote connection and credentials."""
    config = get_config()

    dev_token = token or config.get("token")
    if not dev_token:
        click.echo("No Evernote developer token found.", err=True)
        click.echo("\nTo set up:")
        click.echo("1. Get a token at: https://www.evernote.com/api/DeveloperToken.action")
        click.echo("2. Set EVERNOTE_DEV_TOKEN environment variable")
        click.echo("   Or create a .env file with: EVERNOTE_DEV_TOKEN=your_token")
        sys.exit(1)

    use_sandbox = sandbox or bool(config.get("sandbox"))
    env_type = "sandbox" if use_sandbox else "production"

    click.echo(f"Verifying connection to Evernote ({env_type})...")

    try:
        logger.info("Verifying Evernote connection")
        connector = EvernoteConnector(str(dev_token), sandbox=use_sandbox)
        user_store = connector.client.get_user_store()
        user = user_store.getUser()

        click.echo("\nConnection successful!")
        click.echo(f"  Username: {user.username}")
        click.echo(f"  Email: {user.email}")

        notebooks_list = connector.list_notebooks()
        click.echo(f"  Notebooks: {len(notebooks_list)}")
        logger.info("Connection verified for user: %s", user.username)
    except EvernoteError as e:
        logger.error("Evernote error during verification: %s", e)
        click.echo(f"\nConnection failed: {e}", err=True)
        sys.exit(1)
    except ConnectionError as e:
        logger.error("Connection error during verification: %s", e)
        click.echo(f"\nConnection failed: {e}", err=True)
        sys.exit(1)


def main() -> None:
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
