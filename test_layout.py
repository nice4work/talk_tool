import flet as ft
import os
import subprocess
import platform

DEFAULT_IGNORE_PATTERNS = {
    "__pycache__", ".git", ".svn", ".hg", "node_modules", ".venv", "venv",
    ".idea", ".vscode", ".DS_Store", "*.pyc", "*.pyo", ".env", "dist", "build",
}

def build_tree_nodes(root_path, depth=0):
    nodes = []
    try:
        entries = sorted(os.listdir(root_path))
    except PermissionError:
        return nodes
    dirs, files = [], []
    for entry in entries:
        if entry.startswith("."):
            continue
        skip = False
        for p in DEFAULT_IGNORE_PATTERNS:
            if p.startswith("*") and entry.endswith(p[1:]):
                skip = True; break
            elif entry == p:
                skip = True; break
        if skip:
            continue
        full = os.path.join(root_path, entry)
        if os.path.isdir(full):
            dirs.append((entry, full))
        else:
            files.append((entry, full))
    for name, full in dirs:
        node = {"path": full, "name": name, "is_dir": True, "depth": depth, "expanded": depth == 0}
        nodes.append(node)
        nodes.extend(build_tree_nodes(full, depth + 1))
    for name, full in files:
        nodes.append({"path": full, "name": name, "is_dir": False, "depth": depth, "expanded": False})
    return nodes

def main(page: ft.Page):
    page.title = "Layout Test"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1200
    page.window_height = 600

    tree_nodes = []
    file_tree_col = ft.Column(spacing=2)

    def render_tree():
        file_tree_col.controls.clear()
        if not tree_nodes:
            file_tree_col.controls.append(ft.Text("No project opened", size=12, color="grey"))
        else:
            for node in tree_nodes:
                # Simple visibility: only show depth 0 and expanded children
                if node["depth"] == 0:
                    indent = node["depth"] * 20
                    if node["is_dir"]:
                        file_tree_col.controls.append(
                            ft.Text(f"{'  ' * indent}📁 {node['name']}", size=12)
                        )
                    else:
                        file_tree_col.controls.append(
                            ft.Checkbox(label=node["name"], scale=0.8)
                        )
                elif node["depth"] == 1:
                    # Only show if parent expanded
                    if node["is_dir"]:
                        file_tree_col.controls.append(
                            ft.Text(f"    📁 {node['name']}", size=12)
                        )
                    else:
                        file_tree_col.controls.append(
                            ft.Row([ft.Container(width=20), ft.Checkbox(label=node["name"], scale=0.8)], spacing=0)
                        )
        page.update()

    def on_open(e):
        result = subprocess.run(
            ["osascript", "-e", 'POSIX path of (choose folder with prompt "Select folder")'],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode == 0 and result.stdout.strip():
            path = result.stdout.strip()
            tree_nodes.clear()
            tree_nodes.extend(build_tree_nodes(path))
            print(f"Loaded {len(tree_nodes)} nodes from {path}")
            render_tree()
            print(f"file_tree_col has {len(file_tree_col.controls)} controls")

    page.appbar = ft.AppBar(
        title=ft.Text("Test App"),
        actions=[ft.Button("Open", on_click=on_open)],
    )

    left = ft.Container(
        content=ft.Column([ft.Text("LEFT PANEL", size=16), ft.Text("item 1"), ft.Text("item 2")]),
        bgcolor="blue900",
        padding=10,
        expand=1,
    )

    middle = ft.Container(
        content=ft.Column(
            [
                ft.Text("MIDDLE - File Tree", size=16),
                ft.Divider(),
                file_tree_col,
            ],
            scroll=ft.ScrollMode.AUTO,
        ),
        bgcolor="green900",
        padding=10,
        expand=2,
    )

    right = ft.Container(
        content=ft.Column([ft.Text("RIGHT PANEL", size=16), ft.Text("Preview area")]),
        bgcolor="red900",
        padding=10,
        expand=3,
    )

    page.add(ft.Row([left, middle, right], expand=True, spacing=2))

    # 预加载当前目录的文件树
    tree_nodes.extend(build_tree_nodes("/Users/joy/Documents/workshop/python_projects/github/apps/talk_tool"))
    print(f"Pre-loaded {len(tree_nodes)} nodes")
    render_tree()
    print(f"file_tree_col has {len(file_tree_col.controls)} controls")

ft.run(main)
