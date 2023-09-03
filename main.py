import json
import os
from datetime import datetime
from pathlib import Path

import argparse

from chatgpt_conversations import (
    conversation_to_graph,
    sanitize_title,
    graph_to_markdown,
    save_to_obsidian,
)


def main(file_path: Path, vault_path: Path):
    # Your anonymization and conversation-to-Markdown logic here
    print(f"Processing {file_path} and saving to {vault_path}")
    os.makedirs(vault_path, exist_ok=True)
    with open(file_path, "r") as f:
        chat_data = json.load(f)
        for conversation in chat_data:
            conversation_graph = conversation_to_graph(conversation)
            title = sanitize_title(
                conversation.get(
                    "title", f"Untitled Conversation-{conversation.get('id')}"
                )
            )
            # Get the date of the conversation
            create_time = datetime.fromtimestamp(
                conversation.get("create_time", datetime.utcnow())
            )
            markdown_data = graph_to_markdown(
                title=title, create_time=create_time, graph=conversation_graph
            )
            if markdown_data:
                save_to_obsidian(title, markdown_data, vault_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert ChatGPT conversations to Obsidian-friendly Markdown."
    )

    parser.add_argument(
        "-i",
        "--input-file",
        required=True,
        type=Path,
        help="Path to the input JSON file containing ChatGPT conversations.",
    )
    parser.add_argument(
        "-o",
        "--output-directory",
        required=True,
        type=Path,
        help="Path to the output Markdown file.",
    )

    args = parser.parse_args()

    main(args.input_file, args.output_directory)
