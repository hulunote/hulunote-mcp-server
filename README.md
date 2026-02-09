# Hulunote MCP Server

A Model Context Protocol (MCP) server that enables seamless integration between Claude and Hulunote, a powerful bidirectional linking note-taking application.

## Overview

This MCP server allows Claude to interact with Hulunote's knowledge base, enabling AI-assisted note creation, organization, and navigation. With this integration, you can leverage Claude's capabilities to build and manage your personal knowledge graph directly through natural language conversations.

## Features

- **Create Notes**: Generate new notes in any Hulunote database
- **Manage Navigation Nodes**: Create and update hierarchical navigation structures within notes
- **Retrieve Notes**: Access and list notes from your databases with pagination support
- **Bulk Operations**: Fetch all notes or navigation nodes for comprehensive knowledge management
- **Bidirectional Linking**: Take full advantage of Hulunote's bidirectional linking capabilities through AI-assisted content creation

## Available Tools

### Note Management

- `create_note` - Create a new note in a specified database
- `get_notes` - Retrieve a paginated list of notes from a database
- `get_all_notes` - Fetch all notes from a database (not paginated)
- `update_note` - Update a note's title and/or content

### Navigation Management

- `create_or_update_nav` - Create or update navigation nodes within notes
- `get_note_navigation` - Retrieve all navigation nodes for a specific note
- `get_all_navigation_nodes` - Get all navigation nodes from a database (paginated)

## Installation

### Prerequisites

- Python 3.8 or higher
- Hulunote application installed and running
- Claude Desktop or compatible MCP client

### Setup

1. Clone this repository:
```bash
git clone https://github.com/hulunote/hulunote-mcp-server.git
cd hulunote-mcp-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Configure your MCP client (e.g., Claude Desktop) to use this server by adding it to your MCP configuration file.

## Usage

### Basic Examples

**Creating a Note:**
```
Claude, create a note titled "Project Ideas" in my Test Knowledge Base
```

**Adding Navigation Content:**
```
Add a section about brainstorming techniques to the note with detailed examples
```

**Retrieving Notes:**
```
Show me all notes in my Test Knowledge Base
```

**Building Knowledge Structures:**
```
Create a comprehensive guide about machine learning with hierarchical navigation nodes covering fundamentals, algorithms, and applications
```

## Configuration

Configure the MCP server connection in your MCP client configuration file (typically `claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "hulunote": {
      "command": "python",
      "args": ["/path/to/hulunote-mcp-server/server.py"]
    }
  }
}
```

## API Reference

### create_note(database_name: str, title: str)

Creates a new note in the specified database.

**Parameters:**
- `database_name`: Name of the target database
- `title`: Title for the new note

**Returns:** Note details including ID, database ID, and root navigation ID

### create_or_update_nav(note_id: str, nav_id: str, content: str, parent_id: Optional[str])

Creates or updates a navigation node within a note.

**Parameters:**
- `note_id`: UUID of the target note
- `nav_id`: UUID for the navigation node
- `content`: Content of the navigation node
- `parent_id`: UUID of the parent node (None for root level)

**Returns:** Confirmation of the created/updated navigation node

### get_notes(database_id: str, page: int = 1, page_size: int = 20)

Retrieves a paginated list of notes from a database.

**Parameters:**
- `database_id`: UUID of the database
- `page`: Page number (default: 1)
- `page_size`: Number of notes per page (default: 20)

**Returns:** List of notes with metadata

## Use Cases

- **Knowledge Management**: Build interconnected knowledge bases with AI assistance
- **Research Organization**: Structure research notes with hierarchical navigation
- **Project Documentation**: Create comprehensive project wikis with bidirectional links
- **Learning Systems**: Develop personal learning resources with linked concepts
- **Content Planning**: Organize ideas and outlines for writing projects

## About Hulunote

Hulunote is a modern note-taking application that emphasizes bidirectional linking and knowledge graph construction. Unlike traditional hierarchical note systems, Hulunote allows you to create web-like connections between ideas, enabling:

- Automatic backlinks between related notes
- Graph visualization of knowledge connections
- Flexible navigation through linked concepts
- Emergent insights from connection discovery

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For issues and questions:
- Open an issue on GitHub
- Check the [Hulunote documentation](https://hulunote.com/docs)
- Join our community discussions

## Acknowledgments

- Built on the [Model Context Protocol](https://modelcontextprotocol.io/)
- Integrates with [Anthropic's Claude](https://www.anthropic.com/claude)
- Powers [Hulunote](https://hulunote.com/) knowledge management

---

**Note**: This MCP server requires an active Hulunote installation and proper API credentials configured in your environment.
