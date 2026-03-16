# Agent Guidelines for AI Talk Tool

## Overview
This is a Flet-based desktop application for generating AI context prompts. The application allows users to select templates, files from projects, and questions to create comprehensive context for AI assistants.

## Build Commands
- `make build` - Package the application using Flet (creates standalone executable)
- `python talk_tool.py` - Run the application in development mode
- `flet run talk_tool.py` - Alternative development mode execution

## Test Commands
- `python test_selection.py` - Test text field selection functionality
- `python test_flet_selection.py` - Test Flet text field properties
- `python test_layout.py` - Test layout and file tree rendering
- To run a single test: `python path/to/test_file.py`

## Dependencies
- Install with: `pip install -r requirements.txt`
- Primary dependency: `flet==0.81.0`
- Secondary dependency: `pyperclip==1.8.2`
- Additional dependency: `wcwidth` (used in main application)

## Code Style Guidelines

### Imports
- Import standard library modules first, then third-party, then local modules
- Group imports with blank lines between groups
- Use explicit imports over wildcard imports
- Example:
```python
import flet as ft
import json
import os
import uuid
import asyncio
import subprocess
import platform

from wcwidth import width
```

### Formatting
- Follow PEP 8 style guide
- Use 4 spaces for indentation (no tabs)
- Maximum line length of 88-100 characters
- Use f-strings for string formatting
- Use docstrings for functions that are not obvious
- Keep related code grouped together with logical spacing

### Naming Conventions
- Use snake_case for variables and functions
- Use PascalCase for classes (though none are present in this project)
- Use UPPERCASE for constants
- Use descriptive names (e.g., `project_state`, `selected_ids`)
- Prefix private/internal functions with underscore (`_should_ignore_entry`)

### Type Hints
- Functions should include type hints where clarity is beneficial
- Parameter types should be specified when not obvious
- Return types should be specified for complex functions

### Error Handling
- Handle UnicodeDecodeError when reading files (try UTF-8 first, then fallback to GBK)
- Use try-except blocks around file operations
- Gracefully handle PermissionError when accessing directories
- Provide meaningful error messages to users through SnackBar notifications

### Structure
- Long functions are acceptable if they represent a cohesive UI component
- Group related functionality with comments (e.g., "================= UI 组件定义 =================")
- Separate major components with clear visual breaks
- Maintain consistent ordering: imports, constants, helper functions, main logic, UI setup

### Special Considerations
- Application uses Chinese interface text alongside English comments
- File encoding handling prioritizes UTF-8 with GBK fallback
- Cross-platform file selection using native dialogs (macOS, Windows, Linux)
- Asynchronous operations for clipboard copying with visual feedback
- File tree rendering with expand/collapse functionality
- Large text field content is managed efficiently

## Testing Approach
- Test files are standalone and can be run individually
- UI functionality is tested through Flet's testing capabilities
- Layout and component rendering can be verified with test_layout.py
- Text selection functionality has dedicated test files
- Mock external dependencies when testing core logic

## Linting
- Run `python -m py_compile *.py` to check syntax
- No specific linter configured, but PEP 8 compliance is expected
- Manual verification of code style and structure is recommended