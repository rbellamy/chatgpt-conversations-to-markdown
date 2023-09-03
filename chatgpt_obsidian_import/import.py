import json
import os
import re

import networkx as nx
from datetime import datetime
from typing import Dict, Any, Optional

from networkx import DiGraph


def conversation_to_graph(conversation: Dict[str, Any]) -> Optional[DiGraph]:
    graph = nx.DiGraph()  # Create a directed graph object

    # Check if 'mapping' exists in the conversation data
    if "mapping" not in conversation:
        return None

    # Loop through each message in the mapping
    for msg_id, msg_data in conversation["mapping"].items():
        # Check for None values before proceeding
        if msg_data is None:
            continue

        msg = msg_data.get("message")
        if msg is None:
            continue
        role = msg.get("author", {}).get("role", "unknown")
        text = msg.get("content", {}).get("parts", [""])[0]
        metadata = msg.get("metadata", {})

        # Check if the message contains code blocks, and close them if neeeded.
        # Does not fixup anything above the last code block
        tick_count = text.count("```")
        if tick_count > 0 and tick_count % 2 != 0:
            text += "\n```"

        # Create a node for this message
        graph.add_node(msg_id, role=role, text=text, metadata=metadata)

        # Check if this message is a reply to another
        parent_id = msg_data.get("parent")
        if parent_id:
            graph.add_edge(parent_id, msg_id)

    return graph


def pretty_print_json_in_markdown(data: Any) -> str:
    pretty_json = json.dumps(data, indent=4, sort_keys=True)
    return f"\n```json\n{pretty_json}\n```"


def sanitize_title(title: str) -> str:
    return (
        re.sub(r"[^\w\s-]", "", title.replace("&", "and")).strip('"').replace("  ", " ")
    )


def collapsible_metadata_markdown(graph, node):
    if "metadata" in graph.nodes[node] and graph.nodes[node]["metadata"] != {}:
        abstract = "[!abstract]- metadata\n"
        metadata = graph.nodes[node]["metadata"]
        abstract += f"{pretty_print_json_in_markdown(metadata)}\n"
        markdown_data = ""
        for line in abstract.splitlines():
            markdown_data += f"> {line}\n"
        return markdown_data
    return None


def graph_to_markdown(title: str, create_time: datetime, graph: nx.DiGraph) -> str:
    # Generate Markdown from the graph
    markdown_output = f"# {title}\n\n_({create_time:%Y-%m-%d %H:%M:%S})_\n"
    # Get the root node (node with in-degree of zero)
    in_degrees = dict(graph.in_degree())
    if isinstance(in_degrees, dict):
        root_nodes = [n for n, d in in_degrees.items() if d == 0]
        if not root_nodes:
            return markdown_output

        root_node = root_nodes[0]

        # Depth-first search traversal to generate Markdown
        for node in nx.dfs_preorder_nodes(graph, source=root_node):
            if graph.nodes[node] == {}:  # Skip nodes with no data
                continue

            role = graph.nodes[node]["role"]
            match role:
                case "system":
                    role = "⚙️ system"
                case "assistant":
                    role = "🤖 assistant"
                case "tool":
                    role = "🛠️ tool"
                case "user":
                    role = "👤 user"
                case _:
                    role = "unknown"
            text = graph.nodes[node]["text"]
            metadata_markdown = collapsible_metadata_markdown(graph, node)
            if metadata_markdown and text:
                markdown_output += "\n---\n"
                markdown_output += f"{metadata_markdown}\n_**{role}**_:\n{text}\n"
            elif text:
                markdown_output += "\n---\n"
                markdown_output += f"_**{role}**_:\n{text}\n"

    return f"{markdown_output}\n"


def save_to_obsidian(title: str, markdown_data: str, obsidian_vault_path: str) -> None:
    with open(f"{obsidian_vault_path}/{title}.md", "w") as f:
        f.write(markdown_data)


if __name__ == "__main__":
    file_path = "../.data/conversations.json"
    vault_path = "../.data/ChatGPT Conversations"
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
            save_to_obsidian(title, markdown_data, vault_path)
