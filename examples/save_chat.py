#!/usr/bin/env python3
"""Example: Save a Claude chat to Evernote programmatically."""

import os

from dotenv import load_dotenv

from claude_evernote.client import EvernoteConnector, EvernoteError

# Load environment variables from .env file
load_dotenv()


def main() -> None:
    """Main function to demonstrate saving a chat to Evernote."""
    # Get token from environment
    token = os.getenv("EVERNOTE_DEV_TOKEN")
    if not token:
        print("Error: Set EVERNOTE_DEV_TOKEN environment variable")
        print("Get a token at: https://www.evernote.com/api/DeveloperToken.action")
        return

    # Example chat content
    chat_content = (
        "Human: Can you explain what a Python decorator is?\n\n"
        "Assistant: A decorator is a function that takes another function "
        "and extends its behavior without explicitly modifying it. "
        "Here's a simple example:\n\n"
        "```python\n"
        "def my_decorator(func):\n"
        "    def wrapper():\n"
        '        print("Before function call")\n'
        "        func()\n"
        '        print("After function call")\n'
        "    return wrapper\n\n"
        "@my_decorator\n"
        "def say_hello():\n"
        '    print("Hello!")\n\n'
        "say_hello()\n"
        "```\n\n"
        "This will output:\n"
        "- Before function call\n"
        "- Hello!\n"
        "- After function call\n\n"
        "Human: That's helpful, thanks!\n"
    )

    try:
        # Initialize the connector
        connector = EvernoteConnector(
            dev_token=token,
            sandbox=False,  # Set to True for sandbox.evernote.com
        )

        # List available notebooks
        print("Available notebooks:")
        for nb in connector.list_notebooks():
            print(f"  - {nb.name}")
        print()

        # Save the chat
        note_guid = connector.save_chat(
            chat_content=chat_content,
            title="Python Decorators Explained",
            notebook_name=None,  # Use default notebook
            tags=["python", "claude", "tutorial"],
        )

        print("Note saved successfully!")
        print(f"  GUID: {note_guid}")

    except EvernoteError as e:
        print(f"Evernote error: {e}")
    except ConnectionError as e:
        print(f"Connection error: {e}")


if __name__ == "__main__":
    main()
