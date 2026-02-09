from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os

# Initialize FastMCP server
mcp = FastMCP("hulunote")

# Constants
HULUNOTE_API_BASE = "https://www.hulunote.top"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36"

# API Token - 从环境变量读取或直接设置
API_TOKEN = os.getenv("HULUNOTE_API_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MSwicm9sZSI6Imh1bHVub3RlIiwiZXhwIjoxNzcyNDUxMDgyfQ.LVQdd2tWKuB1d3089lFiej1ezRhimvrmfyrhOuur1BE")

async def make_hulunote_request(
    endpoint: str, 
    data: dict[str, Any]
) -> dict[str, Any] | None:
    """Make a request to the Hulunote API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "X-Functor-Api-Token": API_TOKEN,
        "Referer": "https://www.hulunote.top/",
        "sec-ch-ua": '"Not(A:Brand";v="8", "Chromium";v="144", "Google Chrome";v="144"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
    }
    
    url = f"{HULUNOTE_API_BASE}{endpoint}"
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                url, 
                json=data, 
                headers=headers, 
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            return {
                "error": True,
                "message": f"HTTP error occurred: {str(e)}"
            }
        except Exception as e:
            return {
                "error": True,
                "message": f"An error occurred: {str(e)}"
            }

def format_note(note: dict[str, Any]) -> str:
    """Format a note object into a readable string."""
    return f"""
Title: {note.get('hulunote-notes/title', 'Untitled')}
Note ID: {note.get('hulunote-notes/id', 'Unknown')}
Database ID: {note.get('hulunote-notes/database-id', 'Unknown')}
Root Nav ID: {note.get('hulunote-notes/root-nav-id', 'Unknown')}
Created: {note.get('hulunote-notes/created-at', 'Unknown')}
Updated: {note.get('hulunote-notes/updated-at', 'Unknown')}
Public: {note.get('hulunote-notes/is-public', False)}
Page Views: {note.get('hulunote-notes/pv', 0)}
"""

# ============ Note Management Tools ============

@mcp.tool()
async def create_note(database_name: str, title: str) -> str:
    """Create a new note in Hulunote.

    Args:
        database_name: Name of the database to create the note in
        title: Title of the new note
    """
    data = {
        "database-name": database_name,
        "title": title
    }
    
    result = await make_hulunote_request("/hulunote/new-note", data)
    
    if not result:
        return "Failed to create note: No response from server"
    
    if result.get("error"):
        return f"Failed to create note: {result.get('message')}"
    
    return f"Successfully created note!\n{format_note(result)}"

@mcp.tool()
async def get_notes(database_id: str, page: int = 1, page_size: int = 20) -> str:
    """Get a paginated list of notes from a database.

    Args:
        database_id: UUID of the database
        page: Page number (default: 1)
        page_size: Number of notes per page (default: 20)
    """
    data = {
        "database-id": database_id,
        "page": page,
        "page-size": page_size
    }
    
    result = await make_hulunote_request("/hulunote/get-note-list", data)
    
    if not result:
        return "Failed to fetch notes: No response from server"
    
    if result.get("error"):
        return f"Failed to fetch notes: {result.get('message')}"
    
    # 根据实际返回格式调整
    notes = result.get("notes", result if isinstance(result, list) else [])
    if not notes:
        return f"No notes found on page {page}"
    
    # Format notes list
    formatted_notes = []
    for note in notes:
        formatted_notes.append(format_note(note))
    
    total = result.get("total", len(notes))
    header = f"Notes (Page {page}, Total: {total})\n"
    header += "=" * 60 + "\n"
    
    return header + "\n---\n".join(formatted_notes)

@mcp.tool()
async def get_all_notes(database_id: str) -> str:
    """Get all notes from a database (not paginated).

    Args:
        database_id: UUID of the database
    """
    data = {
        "database-id": database_id
    }
    
    result = await make_hulunote_request("/hulunote/get-all-note-list", data)
    
    if not result:
        return "Failed to fetch notes: No response from server"
    
    if result.get("error"):
        return f"Failed to fetch notes: {result.get('message')}"
    
    notes = result.get("notes", result if isinstance(result, list) else [])
    if not notes:
        return "No notes found in this database"
    
    # Format notes list
    formatted_notes = []
    for note in notes:
        formatted_notes.append(format_note(note))
    
    header = f"All Notes (Total: {len(notes)})\n"
    header += "=" * 60 + "\n"
    
    return header + "\n---\n".join(formatted_notes)

@mcp.tool()
async def update_note(
    note_id: str, 
    title: str | None = None, 
    content: str | None = None
) -> str:
    """Update a note's title and/or content.

    Args:
        note_id: UUID of the note to update
        title: New title (optional)
        content: New content (optional)
    """
    data = {"note-id": note_id}
    
    if title is not None:
        data["title"] = title
    if content is not None:
        data["content"] = content
    
    if len(data) == 1:  # Only note-id provided
        return "Please provide at least a title or content to update"
    
    result = await make_hulunote_request("/hulunote/update-hulunote-note", data)
    
    if not result:
        return "Failed to update note: No response from server"
    
    if result.get("error"):
        return f"Failed to update note: {result.get('message')}"
    
    updates = []
    if title:
        updates.append(f"Title: {title}")
    if content:
        updates.append(f"Content updated")
    
    return f"Successfully updated note {note_id}\n" + "\n".join(updates)

# ============ Outline Navigation Tools ============

@mcp.tool()
async def create_or_update_nav(
    note_id: str,
    nav_id: str,
    content: str,
    parent_id: str | None = None
) -> str:
    """Create or update a navigation node in a note's outline.

    Args:
        note_id: UUID of the note
        nav_id: UUID of the navigation node
        content: Content of the navigation node
        parent_id: UUID of the parent node (None for root level)
    """
    data = {
        "note-id": note_id,
        "nav-id": nav_id,
        "content": content,
        "parent-id": parent_id
    }
    
    result = await make_hulunote_request("/hulunote/create-or-update-nav", data)
    
    if not result:
        return "Failed to create/update navigation node: No response from server"
    
    if result.get("error"):
        return f"Failed to create/update navigation node: {result.get('message')}"
    
    parent_info = f"under parent {parent_id}" if parent_id else "at root level"
    return f"Successfully created/updated navigation node {nav_id} {parent_info}\nContent: {content}"

@mcp.tool()
async def get_note_navigation(note_id: str) -> str:
    """Get all navigation nodes for a note.

    Args:
        note_id: UUID of the note
    """
    data = {
        "note-id": note_id
    }
    
    result = await make_hulunote_request("/hulunote/get-note-navs", data)
    
    if not result:
        return "Failed to fetch navigation nodes: No response from server"
    
    if result.get("error"):
        return f"Failed to fetch navigation nodes: {result.get('message')}"
    
    nodes = result.get("navs", result if isinstance(result, list) else [])
    if not nodes:
        return f"No navigation nodes found for note {note_id}"
    
    # Format navigation tree
    formatted_nodes = []
    for node in nodes:
        parent_id = node.get('hulunote-navs/parent-id') or node.get('parent-id')
        parent_info = f"Parent: {parent_id}" if parent_id else "Root Level"
        
        formatted_nodes.append(
            f"Nav ID: {node.get('hulunote-navs/id') or node.get('nav-id', 'Unknown')}\n"
            f"Content: {node.get('hulunote-navs/content') or node.get('content', 'No content')}\n"
            f"{parent_info}"
        )
    
    header = f"Navigation Outline for Note {note_id} (Total: {len(nodes)})\n"
    header += "=" * 60 + "\n"
    
    return header + "\n---\n".join(formatted_nodes)

@mcp.tool()
async def get_all_navigation_nodes(
    database_id: str,
    page: int = 1,
    page_size: int = 100
) -> str:
    """Get all navigation nodes from a database (paginated).

    Args:
        database_id: UUID of the database
        page: Page number (default: 1)
        page_size: Number of nodes per page (default: 100)
    """
    data = {
        "database-id": database_id,
        "page": page,
        "page-size": page_size
    }
    
    result = await make_hulunote_request("/hulunote/get-all-nav-by-page", data)
    
    if not result:
        return "Failed to fetch navigation nodes: No response from server"
    
    if result.get("error"):
        return f"Failed to fetch navigation nodes: {result.get('message')}"
    
    nodes = result.get("navs", result if isinstance(result, list) else [])
    if not nodes:
        return f"No navigation nodes found on page {page}"
    
    # Format nodes
    formatted_nodes = []
    for node in nodes:
        formatted_nodes.append(
            f"Nav ID: {node.get('hulunote-navs/id') or node.get('nav-id', 'Unknown')}\n"
            f"Note ID: {node.get('hulunote-navs/note-id') or node.get('note-id', 'Unknown')}\n"
            f"Content: {node.get('hulunote-navs/content') or node.get('content', 'No content')}\n"
            f"Parent: {node.get('hulunote-navs/parent-id') or node.get('parent-id', 'Root')}"
        )
    
    total = result.get("total", len(nodes))
    header = f"Navigation Nodes (Page {page}, Total: {total})\n"
    header += "=" * 60 + "\n"
    
    return header + "\n---\n".join(formatted_nodes)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
