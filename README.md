# Hulunote MCP Server

A Model Context Protocol (MCP) server that enables seamless integration between Claude and [Hulunote](https://www.hulunote.top), a powerful bidirectional linking note-taking application.

## Features

- **Browse Databases**: List all available databases (notebooks)
- **Create Notes**: Generate new notes in any Hulunote database
- **Manage Outline Nodes**: Create, update, and delete hierarchical navigation structures within notes
- **Retrieve Notes**: Access and list notes from your databases with pagination support
- **Bulk Operations**: Fetch all notes or navigation nodes for comprehensive knowledge management

## Available Tools

### Database

| Tool | Description |
|------|-------------|
| `get_database_list` | List all databases for the authenticated user |

### Note Management

| Tool | Description |
|------|-------------|
| `create_note` | Create a new note in a database |
| `get_notes` | Get paginated list of notes |
| `get_all_notes` | Get all notes (not paginated) |
| `update_note` | Update a note's title/content |
| `delete_note` | Soft delete a note |

### Outline Navigation

| Tool | Description |
|------|-------------|
| `create_or_update_nav` | Create or update an outline node |
| `get_note_navigation` | Get all outline nodes for a note |
| `delete_nav` | Soft delete an outline node |
| `get_all_navigation_nodes` | Get all outline nodes in a database (paginated) |

## Installation

### Prerequisites

- Python 3.10 or higher
- pip

### Setup

1. Clone this repository:
```bash
git clone https://github.com/xlisp/hulunote-mcp-server.git
cd hulunote-mcp-server
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your API token:
```bash
export HULUNOTE_API_TOKEN="your-jwt-token-here"
```

To get your token: log in to [Hulunote](https://www.hulunote.top), open browser DevTools > Network tab, and copy the `x-functor-api-token` header value from any API request.

## Configuration

### Claude Desktop

Add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "hulunote": {
      "command": "python",
      "args": ["/path/to/hulunote-mcp-server/hulunote_mcp.py"],
      "env": {
        "HULUNOTE_API_TOKEN": "your-jwt-token-here"
      }
    }
  }
}
```

## Usage

```
List my Hulunote databases
```

```
Create a note titled "Project Ideas" in database 0a1e78c8-...
```

```
Add an outline node saying "This is a great bidirectional linking note!" to the note
```

## API Authentication

This server uses the `x-functor-api-token` header for authentication with the Hulunote API at `https://www.hulunote.top`. The token is a JWT issued upon login.

## License

MIT
