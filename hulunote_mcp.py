from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("hulunote")

# Constants
HULUNOTE_API_BASE = "https://your-hulunote-api-domain.com"  # 请替换为实际的API域名
USER_AGENT = "hulunote-mcp/1.0"

# 这里需要配置认证信息
# 可以通过环境变量或配置文件读取
API_TOKEN = ""  # 请设置你的API token

async def make_hulunote_request(
    endpoint: str, 
    data: dict[str, Any]
) -> dict[str, Any] | None:
    """Make a request to the Hulunote API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
    }
    
    # 如果需要认证，添加认证头
    if API_TOKEN:
        headers["Authorization"] = f"Bearer {API_TOKEN}"
    
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

# ============ Note Management Tools ============

@mcp.tool()
async def create_note(database_id: str, title: str) -> str:
    """Create a new note in Hulunote.

    Args:
        database_id: UUID of the database to create the note in
        title: Title of the new note
    """
    data = {
        "database_id": database_id,
        "title": title
    }
    
    result = await make_hulunote_request("/hulunote/new-note", data)
    
    if not result:
        return "Failed to create note: No response from server"
    
    if result.get("error"):
        return f"Failed to create note: {result.get('message')}"
    
    return f"Successfully created note: {title}\nNote ID: {result.get('note_id', 'Unknown')}"

@mcp.tool()
async def get_notes(database_id: str, page: int = 1, page_size: int = 20) -> str:
    """Get a paginated list of notes from a database.

    Args:
        database_id: UUID of the database
        page: Page number (default: 1)
        page_size: Number of notes per page (default: 20)
    """
    data = {
        "database_id": database_id,
        "page": page,
        "page_size": page_size
    }
    
    result = await make_hulunote_request("/hulunote/get-note-list", data)
    
    if not result:
        return "Failed to fetch notes: No response from server"
    
    if result.get("error"):
        return f"Failed to fetch notes: {result.get('message')}"
    
    notes = result.get("notes", [])
    if not notes:
        return f"No notes found on page {page}"
    
    # Format notes list
    formatted_notes = []
    for note in notes:
        formatted_notes.append(
            f"Title: {note.get('title', 'Untitled')}\n"
            f"ID: {note.get('note_id', 'Unknown')}\n"
            f"Created: {note.get('created_at', 'Unknown')}"
        )
    
    total = result.get("total", len(notes))
    header = f"Notes (Page {page}/{(total + page_size - 1) // page_size}, Total: {total})\n"
    header += "=" * 50 + "\n\n"
    
    return header + "\n\n---\n\n".join(formatted_notes)

@mcp.tool()
async def get_all_notes(database_id: str) -> str:
    """Get all notes from a database (not paginated).

    Args:
        database_id: UUID of the database
    """
    data = {
        "database_id": database_id
    }
    
    result = await make_hulunote_request("/hulunote/get-all-note-list", data)
    
    if not result:
        return "Failed to fetch notes: No response from server"
    
    if result.get("error"):
        return f"Failed to fetch notes: {result.get('message')}"
    
    notes = result.get("notes", [])
    if not notes:
        return "No notes found in this database"
    
    # Format notes list
    formatted_notes = []
    for note in notes:
        formatted_notes.append(
            f"Title: {note.get('title', 'Untitled')}\n"
            f"ID: {note.get('note_id', 'Unknown')}"
        )
    
    header = f"All Notes (Total: {len(notes)})\n"
    header += "=" * 50 + "\n\n"
    
    return header + "\n\n---\n\n".join(formatted_notes)

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
    data = {"note_id": note_id}
    
    if title is not None:
        data["title"] = title
    if content is not None:
        data["content"] = content
    
    if len(data) == 1:  # Only note_id provided
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
        "note_id": note_id,
        "nav_id": nav_id,
        "content": content,
        "parent_id": parent_id
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
        "note_id": note_id
    }
    
    result = await make_hulunote_request("/hulunote/get-note-navs", data)
    
    if not result:
        return "Failed to fetch navigation nodes: No response from server"
    
    if result.get("error"):
        return f"Failed to fetch navigation nodes: {result.get('message')}"
    
    nodes = result.get("navs", [])
    if not nodes:
        return f"No navigation nodes found for note {note_id}"
    
    # Format navigation tree
    formatted_nodes = []
    for node in nodes:
        parent_info = f"Parent: {node.get('parent_id')}" if node.get('parent_id') else "Root Level"
        formatted_nodes.append(
            f"Nav ID: {node.get('nav_id', 'Unknown')}\n"
            f"Content: {node.get('content', 'No content')}\n"
            f"{parent_info}"
        )
    
    header = f"Navigation Outline for Note {note_id} (Total: {len(nodes)})\n"
    header += "=" * 50 + "\n\n"
    
    return header + "\n\n---\n\n".join(formatted_nodes)

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
        "database_id": database_id,
        "page": page,
        "page_size": page_size
    }
    
    result = await make_hulunote_request("/hulunote/get-all-nav-by-page", data)
    
    if not result:
        return "Failed to fetch navigation nodes: No response from server"
    
    if result.get("error"):
        return f"Failed to fetch navigation nodes: {result.get('message')}"
    
    nodes = result.get("navs", [])
    if not nodes:
        return f"No navigation nodes found on page {page}"
    
    # Format nodes
    formatted_nodes = []
    for node in nodes:
        formatted_nodes.append(
            f"Nav ID: {node.get('nav_id', 'Unknown')}\n"
            f"Note ID: {node.get('note_id', 'Unknown')}\n"
            f"Content: {node.get('content', 'No content')}\n"
            f"Parent: {node.get('parent_id', 'Root')}"
        )
    
    total = result.get("total", len(nodes))
    header = f"Navigation Nodes (Page {page}/{(total + page_size - 1) // page_size}, Total: {total})\n"
    header += "=" * 50 + "\n\n"
    
    return header + "\n\n---\n\n".join(formatted_nodes)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
