#!/usr/bin/env python3
"""Example: Save a Claude chat to Evernote programmatically."""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from claude_evernote.client import EvernoteConnector, EvernoteError


def main():
    # Get token from environment
    token = os.getenv("EVERNOTE_DEV_TOKEN")
    if not token:
        print("Error: Set EVERNOTE_DEV_TOKEN environment variable")
        print("Get a token at: https://www.evernote.com/api/DeveloperToken.action")
        return

    # Example chat content
    chat_content = """
Human: Can you explain what a Python decorator is?

Assistant: A decorator is a function that takes another function and extends its behavior without explicitly modifying it. Here's a simple example:

```python
def my_decorator(func):
    def wrapper():
        print("Before function call")
        func()
        print("After function call")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

say_hello()
```

This will output:
- Before function call
- Hello!
- After function call

Human: That's helpful, thanks!
"""

    try:
        # Initialize the connector
        connector = EvernoteConnector(
            dev_token=token,
            sandbox=False  # Set to True for sandbox.evernote.com
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
            tags=["python", "claude", "tutorial"]
        )

        print(f"✓ Note saved successfully!")
        print(f"  GUID: {note_guid}")

    except EvernoteError as e:
        print(f"Evernote error: {e}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
