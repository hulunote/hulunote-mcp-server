from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import os
import uuid as uuid_mod

# Initialize FastMCP server
mcp = FastMCP("hulunote")

# Constants
HULUNOTE_API_BASE = "https://www.hulunote.top"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36"

# API Token - 从环境变量读取或直接设置
API_TOKEN = os.getenv("HULUNOTE_API_TOKEN", "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6Niwicm9sZSI6Imh1bHVub3RlIiwiZXhwIjoxNzc2MTMxMzU0fQ.OFNt_h9pwanAt3Yek6h4Pgd5Rk9hHOPSgIosogn8HLk")

async def make_hulunote_request(
    endpoint: str,
    data: dict[str, Any]
) -> dict[str, Any] | None:
    """Make a request to the Hulunote API with proper error handling."""
    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        "x-functor-api-token": API_TOKEN,
        "Referer": "https://www.hulunote.top/",
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

def format_database(db: dict[str, Any]) -> str:
    """Format a database object into a readable string."""
    name = db.get('hulunote-databases/name', 'Unnamed')
    db_id = db.get('hulunote-databases/id', 'Unknown')
    desc = db.get('hulunote-databases/description', '')
    is_default = " (default)" if db.get('hulunote-databases/is-default') else ""
    is_public = " [public]" if db.get('hulunote-databases/is-public') else ""
    result = f"- {name}{is_default}{is_public}\n  ID: {db_id}"
    if desc:
        result += f"\n  Description: {desc}"
    return result

def format_note(note: dict[str, Any]) -> str:
    """Format a note object into a readable string."""
    title = note.get('hulunote-notes/title', 'Untitled')
    note_id = note.get('hulunote-notes/id', 'Unknown')
    root_nav_id = note.get('hulunote-notes/root-nav-id', 'Unknown')
    shortcut = " [shortcut]" if note.get('hulunote-notes/is-shortcut') else ""
    updated = note.get('hulunote-notes/updated-at', '')
    result = f"- {title}{shortcut}\n  Note ID: {note_id}\n  Root Nav ID: {root_nav_id}"
    if updated:
        result += f"\n  Updated: {updated}"
    return result

def format_nav(nav: dict[str, Any]) -> str:
    """Format a nav object into a readable string."""
    nav_id = nav.get('id', 'Unknown')
    content = nav.get('content', 'No content')
    parent_id = nav.get('parid', '')
    order = nav.get('same-deep-order', 0)
    parent_info = f"Parent: {parent_id}" if parent_id else "Root Level"
    return f"Nav ID: {nav_id}\nContent: {content}\n{parent_info}\nOrder: {order}"

# ============ Database Tools ============

@mcp.tool()
async def get_database_list() -> str:
    """Get all databases (notebooks) for the authenticated user. Use this first to discover available databases and their IDs."""
    result = await make_hulunote_request("/hulunote/get-database-list", {})

    if not result:
        return "Failed to fetch databases: No response from server"

    if result.get("error"):
        return f"Failed to fetch databases: {result.get('message')}"

    databases = result.get("database-list", [])
    if not databases:
        return "No databases found"

    formatted = [format_database(db) for db in databases if not db.get('hulunote-databases/is-delete')]
    header = f"Databases (Total: {len(formatted)})\n{'=' * 60}\n"
    return header + "\n".join(formatted)

# ============ Note Management Tools ============

@mcp.tool()
async def create_note(database_id: str, title: str) -> str:
    """Create a new note in Hulunote.

    Args:
        database_id: UUID of the database to create the note in (get from get_database_list)
        title: Title of the new note
    """
    data = {
        "database-id": database_id,
        "title": title
    }

    result = await make_hulunote_request("/hulunote/new-note", data)

    if not result:
        return "Failed to create note: No response from server"

    if result.get("error"):
        return f"Failed to create note: {result.get('message')}"

    note_id = result.get('hulunote-notes/id', 'Unknown')
    root_nav_id = result.get('hulunote-notes/root-nav-id', 'Unknown')
    return (
        f"Successfully created note!\n"
        f"Title: {title}\n"
        f"Note ID: {note_id}\n"
        f"Root Nav ID: {root_nav_id}\n"
        f"Database ID: {database_id}\n\n"
        f"Use create_or_update_nav with parent_id='{root_nav_id}' to add top-level outline content."
    )

@mcp.tool()
async def get_notes(database_id: str, page: int = 1, size: int = 20) -> str:
    """Get a paginated list of notes from a database.

    Args:
        database_id: UUID of the database
        page: Page number (default: 1)
        size: Number of notes per page (default: 20)
    """
    data = {
        "database-id": database_id,
        "page": page,
        "size": size
    }

    result = await make_hulunote_request("/hulunote/get-note-list", data)

    if not result:
        return "Failed to fetch notes: No response from server"

    if result.get("error"):
        return f"Failed to fetch notes: {result.get('message')}"

    notes = result.get("note-list", [])
    all_pages = result.get("all-pages", 1)
    if not notes:
        return f"No notes found on page {page}"

    formatted = [format_note(note) for note in notes]
    header = f"Notes (Page {page} of {all_pages}, Count: {len(notes)})\n{'=' * 60}\n"
    return header + "\n".join(formatted)

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

    notes = result.get("note-list", [])
    if not notes:
        return "No notes found in this database"

    formatted = [format_note(note) for note in notes]
    header = f"All Notes (Total: {len(notes)})\n{'=' * 60}\n"
    return header + "\n".join(formatted)

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
    data: dict[str, Any] = {"note-id": note_id}

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

@mcp.tool()
async def delete_note(note_id: str) -> str:
    """Delete a note (soft delete).

    Args:
        note_id: UUID of the note to delete
    """
    data: dict[str, Any] = {
        "note-id": note_id,
        "is-delete": True
    }

    result = await make_hulunote_request("/hulunote/update-hulunote-note", data)

    if not result:
        return "Failed to delete note: No response from server"

    if result.get("error"):
        return f"Failed to delete note: {result.get('message')}"

    return f"Successfully deleted note {note_id}"

# ============ Outline Navigation Tools ============

@mcp.tool()
async def create_or_update_nav(
    note_id: str,
    content: str,
    parent_id: str,
    nav_id: str | None = None,
    order: float = 1.0
) -> str:
    """Create or update a navigation node in a note's outline.

    Args:
        note_id: UUID of the note
        content: Content of the navigation node
        parent_id: UUID of the parent node. Use the note's root-nav-id for top-level nodes.
        nav_id: UUID of the navigation node. If omitted, a new UUID is generated (create mode).
        order: Ordering value among siblings (default: 1.0)
    """
    if nav_id is None:
        nav_id = str(uuid_mod.uuid4())

    data: dict[str, Any] = {
        "note-id": note_id,
        "id": nav_id,
        "parid": parent_id,
        "content": content,
        "order": order,
    }

    result = await make_hulunote_request("/hulunote/create-or-update-nav", data)

    if not result:
        return "Failed to create/update navigation node: No response from server"

    if result.get("error"):
        return f"Failed to create/update navigation node: {result.get('message')}"

    created_id = result.get("id", nav_id)
    return (
        f"Successfully created/updated navigation node\n"
        f"Nav ID: {created_id}\n"
        f"Parent ID: {parent_id}\n"
        f"Content: {content}\n"
        f"Order: {order}"
    )

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

    nodes = result.get("nav-list", [])
    if not nodes:
        return f"No navigation nodes found for note {note_id}"

    # Build tree structure for display
    formatted_nodes = []
    for node in nodes:
        formatted_nodes.append(format_nav(node))

    header = f"Navigation Outline for Note {note_id} (Total: {len(nodes)})\n{'=' * 60}\n"
    return header + "\n---\n".join(formatted_nodes)

@mcp.tool()
async def delete_nav(note_id: str, nav_id: str) -> str:
    """Delete a navigation node (soft delete).

    Args:
        note_id: UUID of the note
        nav_id: UUID of the navigation node to delete
    """
    data: dict[str, Any] = {
        "note-id": note_id,
        "id": nav_id,
        "is-delete": True,
    }

    result = await make_hulunote_request("/hulunote/create-or-update-nav", data)

    if not result:
        return "Failed to delete navigation node: No response from server"

    if result.get("error"):
        return f"Failed to delete navigation node: {result.get('message')}"

    return f"Successfully deleted navigation node {nav_id}"

@mcp.tool()
async def get_all_navigation_nodes(
    database_id: str,
    page: int = 1,
    size: int = 100
) -> str:
    """Get all navigation nodes from a database (paginated).

    Args:
        database_id: UUID of the database
        page: Page number (default: 1)
        size: Number of nodes per page (default: 100)
    """
    data = {
        "database-id": database_id,
        "page": page,
        "size": size
    }

    result = await make_hulunote_request("/hulunote/get-all-nav-by-page", data)

    if not result:
        return "Failed to fetch navigation nodes: No response from server"

    if result.get("error"):
        return f"Failed to fetch navigation nodes: {result.get('message')}"

    nodes = result.get("nav-list", [])
    all_pages = result.get("all-pages", 1)
    if not nodes:
        return f"No navigation nodes found on page {page}"

    # Format nodes
    formatted_nodes = []
    for node in nodes:
        formatted_nodes.append(format_nav(node))

    header = f"Navigation Nodes (Page {page} of {all_pages}, Count: {len(nodes)})\n{'=' * 60}\n"
    return header + "\n---\n".join(formatted_nodes)

if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='stdio')
