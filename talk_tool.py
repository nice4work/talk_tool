import flet as ft
import json
import os
import uuid
import asyncio
import subprocess
import platform

from wcwidth import width

DATA_FILE = "context_templates.json"
PLACEHOLDER_TEXT = "在此输入你具体要问的问题，它会自动附加在所有模板内容之后..."

# 默认忽略的目录和文件
DEFAULT_IGNORE_PATTERNS = {
    "__pycache__", ".git", ".svn", ".hg", "node_modules", ".venv", "venv",
    ".idea", ".vscode", ".DS_Store", "*.pyc", "*.pyo", ".env", "dist", "build",
    "__MACOSX", ".pytest_cache", ".mypy_cache", ".tox", "*.egg-info"
}

# 扩展名到语言的映射
EXT_LANG_MAP = {
    ".py": "python", ".js": "javascript", ".ts": "typescript", ".tsx": "tsx",
    ".jsx": "jsx", ".vue": "vue", ".html": "html", ".css": "css", ".scss": "scss",
    ".json": "json", ".yaml": "yaml", ".yml": "yaml", ".toml": "toml",
    ".md": "markdown", ".sh": "bash", ".bash": "bash", ".zsh": "bash",
    ".sql": "sql", ".java": "java", ".go": "go", ".rs": "rust", ".rb": "ruby",
    ".swift": "swift", ".kt": "kotlin", ".xml": "xml", ".c": "c", ".cpp": "cpp",
    ".h": "c", ".hpp": "cpp", ".txt": "text",
}


def _should_ignore_entry(entry, ignore_patterns):
    """判断一个文件/目录名是否应被忽略"""
    if entry.startswith("."):
        return True
    for pattern in ignore_patterns:
        if pattern.startswith("*"):
            if entry.endswith(pattern[1:]):
                return True
        elif entry == pattern:
            return True
    return False


def generate_tree_structure(root_path: str, prefix: str = "", ignore_patterns: set = None) -> str:
    """递归生成目录树结构字符串"""
    if ignore_patterns is None:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS
    
    result = []
    root_name = os.path.basename(root_path) or root_path
    
    if not prefix:  # 根目录
        result.append(f"{root_name}/")
    
    try:
        entries = sorted(os.listdir(root_path))
    except PermissionError:
        return f"{prefix}[权限不足]\n"
    
    # 过滤掉忽略的文件和目录
    filtered_entries = []
    for entry in entries:
        # 过滤隐藏文件和隐藏文件夹（以.开头）
        if entry.startswith("."):
            continue
        should_ignore = False
        for pattern in ignore_patterns:
            if pattern.startswith("*"):
                if entry.endswith(pattern[1:]):
                    should_ignore = True
                    break
            elif entry == pattern:
                should_ignore = True
                break
        if not should_ignore:
            filtered_entries.append(entry)
    
    entries = filtered_entries
    dirs = []
    files = []
    
    for entry in entries:
        full_path = os.path.join(root_path, entry)
        if os.path.isdir(full_path):
            dirs.append(entry)
        else:
            files.append(entry)
    
    # 合并目录和文件，目录在前
    all_items = [(d, True) for d in dirs] + [(f, False) for f in files]
    
    for i, (item, is_dir) in enumerate(all_items):
        is_last = (i == len(all_items) - 1)
        connector = "└── " if is_last else "├── "
        
        if is_dir:
            result.append(f"{prefix}{connector}{item}/")
            new_prefix = prefix + ("    " if is_last else "│   ")
            subtree = generate_tree_structure(
                os.path.join(root_path, item), 
                new_prefix, 
                ignore_patterns
            )
            if subtree:
                result.append(subtree)
        else:
            result.append(f"{prefix}{connector}{item}")
    
    return "\n".join(result)


def build_tree_nodes(root_path, depth=0, ignore_patterns=None):
    """递归构建扁平化的文件树节点列表"""
    if ignore_patterns is None:
        ignore_patterns = DEFAULT_IGNORE_PATTERNS
    
    nodes = []
    try:
        entries = sorted(os.listdir(root_path))
    except PermissionError:
        return nodes
    
    dirs = []
    files = []
    for entry in entries:
        if _should_ignore_entry(entry, ignore_patterns):
            continue
        full_path = os.path.join(root_path, entry)
        if os.path.isdir(full_path):
            dirs.append(entry)
        else:
            files.append(entry)
    
    # 目录在前，文件在后
    for d in dirs:
        full_path = os.path.join(root_path, d)
        node = {
            "path": full_path,
            "name": d,
            "is_dir": True,
            "depth": depth,
            "expanded": depth == 0,  # 根目录直接子项默认展开
        }
        nodes.append(node)
        # 递归构建子节点
        children = build_tree_nodes(full_path, depth + 1, ignore_patterns)
        node["_children_count"] = len(children)
        nodes.extend(children)
    
    for f in files:
        full_path = os.path.join(root_path, f)
        nodes.append({
            "path": full_path,
            "name": f,
            "is_dir": False,
            "depth": depth,
            "expanded": False,
        })
    
    return nodes


def read_file_content(file_path):
    """读取文件内容，处理编码错误"""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        try:
            with open(file_path, "r", encoding="gbk") as f:
                return f.read()
        except Exception:
            return "[无法读取: 二进制或编码不支持]"
    except Exception as ex:
        return f"[无法读取: {ex}]"


def get_lang_from_ext(file_path):
    """根据文件扩展名推断语言"""
    _, ext = os.path.splitext(file_path)
    return EXT_LANG_MAP.get(ext.lower(), "")


def pick_directory_native(title="选择文件夹"):
    """使用系统原生方式选择文件夹，避免 tkinter 与 Flet 冲突"""
    system = platform.system()
    try:
        if system == "Darwin":
            # macOS: 使用 osascript 调用原生文件夹选择器
            result = subprocess.run(
                ["osascript", "-e",
                 f'POSIX path of (choose folder with prompt "{title}")'],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return result.stdout.strip()
        elif system == "Windows":
            # Windows: 使用 PowerShell 的 FolderBrowserDialog
            ps_script = (
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
                f"$f.Description = '{title}'; "
                "if ($f.ShowDialog() -eq 'OK') { $f.SelectedPath }"
            )
            result = subprocess.run(
                ["powershell", "-Command", ps_script],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        else:
            # Linux: 使用 zenity
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory", f"--title={title}"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode == 0:
                return result.stdout.strip()
    except Exception:
        pass
    return None


def main(page: ft.Page):
    page.title = "ContextFlow Pro (Flet 版)"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 0
    page.window_width = 1400
    page.window_height = 800
    # 设置窗口图标 (Windows 上有效，macOS Dock 图标需在打包时通过 --icon 设置)
    if page.window:
        page.window.icon = "app.ico"

    templates = {}
    selected_ids = set()
    project_state = {"path": None, "tree_nodes": [], "selected_files": set()}

    def load_data():
        if not os.path.exists(DATA_FILE):
            return {
                str(uuid.uuid4())[:8]: {
                    "title": "Vue3 项目规范",
                    "content": "# Vue3 规范\n- 使用 script setup\n- 禁止 any",
                },
                str(uuid.uuid4())[:8]: {
                    "title": "Python 风格指南",
                    "content": "# Python 规范\n- 遵循 PEP8\n- 类型提示完整",
                },
            }
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except UnicodeDecodeError:
            try:
                with open(DATA_FILE, "r", encoding="gbk") as f:
                    return json.load(f)
            except Exception:
                return {}
        except Exception:
            return {}

    def save_data():
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)

    templates = load_data()

    # ================= UI 组件定义 =================

    # 预览文本框
    preview_text = ft.TextField(
        label="👁️ 拼接预览 (最终发送内容)",
        multiline=True,
        min_lines=10,
        read_only=True,
        border_color="transparent",
        focused_border_color="transparent",
        content_padding=15,
    )

    preview_container = ft.Container(
        content=ft.Column([preview_text], scroll=ft.ScrollMode.AUTO, expand=True),
        height=200,
    )

    question_input = ft.TextField(
        label="➕ 追加当前问题",
        multiline=True,
        min_lines=5,
        max_lines=20,
        hint_text=PLACEHOLDER_TEXT,
        shift_enter=True,
        on_change=lambda e: update_preview(),
    )

    question_container = ft.Container(
        content=ft.Column([question_input], scroll=ft.ScrollMode.AUTO, expand=True),
        height=120,
    )

    checkbox_list = ft.Column(spacing=5)
    file_tree_column = ft.Column(spacing=2)

    # ================= 文件树相关逻辑 =================

    def is_node_visible(nodes, index):
        """判断节点是否应该可见（所有父节点都展开）"""
        node = nodes[index]
        if node["depth"] == 0:
            return True
        # 向上找父节点
        target_depth = node["depth"] - 1
        for j in range(index - 1, -1, -1):
            if nodes[j]["depth"] == target_depth and nodes[j]["is_dir"]:
                if not nodes[j]["expanded"]:
                    return False
                return is_node_visible(nodes, j)
        return True

    def on_toggle_folder(node):
        """折叠/展开文件夹"""
        node["expanded"] = not node["expanded"]
        render_file_tree()

    def on_file_checkbox_change(e, file_path):
        """文件勾选/取消回调"""
        if e.control.value:
            project_state["selected_files"].add(file_path)
        else:
            project_state["selected_files"].discard(file_path)
        update_preview()

    def render_file_tree():
        """将 tree_nodes 渲染为控件列表（简化版，与 test_layout 一致）"""
        file_tree_column.controls.clear()
        nodes = project_state["tree_nodes"]

        if not nodes:
            file_tree_column.controls.append(
                ft.Text("点击上方 Open Project\n选择一个项目文件夹",
                        size=12, color="grey_500", text_align=ft.TextAlign.CENTER)
            )
            page.update()
            return

        for i, node in enumerate(nodes):
            if not is_node_visible(nodes, i):
                continue

            indent_str = "  " * node["depth"]

            if node["is_dir"]:
                arrow = "▼" if node["expanded"] else "▶"
                file_tree_column.controls.append(
                    ft.Row(
                        [
                            ft.Container(width=node["depth"] * 16),
                            ft.TextButton(
                                content=ft.Text(f"{arrow} 📁 {node['name']}"),
                                on_click=lambda e, n=node: on_toggle_folder(n),
                                style=ft.ButtonStyle(padding=2),
                            ),
                        ],
                        spacing=0,
                    )
                )
            else:
                file_tree_column.controls.append(
                    ft.Row(
                        [
                            ft.Container(width=node["depth"] * 16 + 20),
                            ft.Checkbox(
                                label=node["name"],
                                value=node["path"] in project_state["selected_files"],
                                on_change=lambda e, p=node["path"]: on_file_checkbox_change(e, p),
                                scale=0.8,
                            ),
                        ],
                        spacing=0,
                    )
                )

        page.update()

    def select_all_files(e):
        """全选所有可见文件"""
        for node in project_state["tree_nodes"]:
            if not node["is_dir"]:
                project_state["selected_files"].add(node["path"])
        render_file_tree()
        update_preview()

    def deselect_all_files(e):
        """取消全选"""
        project_state["selected_files"].clear()
        render_file_tree()
        update_preview()

    # ================= 项目打开逻辑 =================

    def open_project(e):
        """打开项目文件夹"""
        result = pick_directory_native("选择项目文件夹")

        if result:
            project_state["path"] = result
            project_state["selected_files"].clear()
            project_state["tree_nodes"] = build_tree_nodes(result)
            render_file_tree()
            # render_file_tree 已调用 page.update()，不再重复

    # ================= 核心逻辑 =================

    def get_real_question():
        val = question_input.value.strip() if question_input.value else ""
        return "" if val == PLACEHOLDER_TEXT else val

    def build_content_string():
        parts = []
        for t_id in selected_ids:
            if t_id in templates:
                data = templates[t_id]
                header = f"\n\n{'=' * 20} [Context: {data['title']}] {'=' * 20}\n\n"
                parts.append(header + data["content"])

        # 添加选中文件的内容
        if project_state["selected_files"]:
            root_path = project_state["path"] or ""
            for fpath in sorted(project_state["selected_files"]):
                # 计算相对路径
                try:
                    rel_path = os.path.relpath(fpath, root_path)
                except ValueError:
                    rel_path = fpath
                lang = get_lang_from_ext(fpath)
                content = read_file_content(fpath)
                header = f"\n\n{'=' * 20} [File: {rel_path}] {'=' * 20}\n\n"
                parts.append(header + f"```{lang}\n{content}\n```")

        question = get_real_question()
        if question:
            header = f"\n\n{'=' * 20} [Question] {'=' * 20}\n\n"
            parts.append(header + question)

        return "".join(parts).lstrip() if parts else ""

    def update_preview(e=None):
        result = build_content_string()
        if not result:
            preview_text.value = "(等待操作：请勾选左侧模板 / 打开项目选择文件 / 在底部输入问题)"
        else:
            preview_text.value = result
        page.update()

    def on_checkbox_change(e, t_id):
        cb = e.control
        if cb.value:
            selected_ids.add(t_id)
        else:
            selected_ids.discard(t_id)
        update_preview()

    def refresh_sidebar():
        checkbox_list.controls.clear()
        for t_id, data in templates.items():
            cb = ft.Checkbox(
                label=data["title"],
                value=t_id in selected_ids,
                on_change=lambda e, tid=t_id: on_checkbox_change(e, tid),
            )
            checkbox_list.controls.append(cb)
        page.update()

    async def generate_and_copy(e):
        final_string = build_content_string()
        if not final_string:
            page.snack_bar = ft.SnackBar(ft.Text("请至少选择一个模板或输入一个问题！"))
            page.snack_bar.open = True
            page.update()
            return

        try:
            if platform.system() == "Darwin":
                env = os.environ.copy()
                env["LANG"] = "en_US.UTF-8"
                subprocess.run(
                    ["pbcopy"], input=final_string.encode("utf-8"), check=True, env=env
                )
            elif platform.system() == "Windows":
                subprocess.run(["clip"], input=final_string.encode("utf-8"), check=True)
            else:
                subprocess.run(
                    ["xclip", "-selection", "clipboard"],
                    input=final_string.encode("utf-8"),
                    check=True,
                )
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"复制失败: {str(ex)}"))
            page.snack_bar.open = True
            page.update()
            return

        button = e.control
        original_content = button.content
        original_bgcolor = None
        if button.style:
            original_bgcolor = button.style.bgcolor

        button.content = f"✅ 已复制 ({len(final_string)} 字符)"
        if button.style:
            button.style.bgcolor = "green"
        else:
            button.style = ft.ButtonStyle(bgcolor="green")

        page.update()
        await asyncio.sleep(2)

        button.content = original_content
        if button.style:
            button.style.bgcolor = original_bgcolor
        page.update()

    def clear_all(e):
        selected_ids.clear()
        question_input.value = ""
        project_state["path"] = None
        project_state["tree_nodes"] = []
        project_state["selected_files"].clear()
        render_file_tree()
        refresh_sidebar()
        update_preview()

    def create_new_template(e):
        title_field = ft.TextField(label="模板标题", expand=True, dense=True)
        content_field = ft.TextField(
            label="模板内容", multiline=True, min_lines=10, expand=True, dense=True
        )

        def save_dialog(e):
            if not title_field.value or not content_field.value:
                page.snack_bar = ft.SnackBar(ft.Text("标题和内容不能为空"))
                page.snack_bar.open = True
                page.update()
                return

            new_id = str(uuid.uuid4())[:8]
            templates[new_id] = {
                "title": title_field.value,
                "content": content_field.value,
            }
            save_data()
            refresh_sidebar()
            update_preview()
            dlg_modal.open = False
            page.update()

            page.snack_bar = ft.SnackBar(ft.Text("模板创建成功"))
            page.snack_bar.open = True
            page.update()

        dlg_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("新建模板"),
            content=ft.Column([title_field, content_field], tight=True, spacing=5),
            actions=[
                ft.TextButton("取消", on_click=lambda e: close_dlg(dlg_modal)),
                ft.TextButton("保存", on_click=save_dialog),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        def close_dlg(dlg):
            dlg.open = False
            page.update()

        page.overlay.append(dlg_modal)
        dlg_modal.open = True
        page.update()

    # ================= 布局组装 =================

    # AppBar
    page.appbar = ft.AppBar(
        title=ft.Text("ContextFlow Pro", size=18, weight=ft.FontWeight.BOLD),
        center_title=False,
        actions=[
            ft.Button("📁 Open Project", on_click=open_project, icon="folder_open"),
            ft.Container(width=10),
        ],
    )

    # 左栏 - 模板库
    sidebar = ft.Container(
        content=ft.Column(
            [
                ft.Text("📚 模板库", size=18, weight=ft.FontWeight.BOLD),
                ft.Button("+ 新建模板", on_click=create_new_template, icon="add"),
                ft.Divider(),
                checkbox_list,
            ],
            alignment=ft.MainAxisAlignment.START,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=10,
        border_radius=10,
        expand=1,  # flex factor 1
    )

    # 中间栏 - 项目文件树 (scroll 放在外层 Column 上，file_tree_column 直接作为子项)
    tree_panel = ft.Container(
        content=ft.Column(
            [
                ft.Text("📂 项目文件", size=18, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                file_tree_column,
                ft.Divider(),
                ft.Row(
                    [
                        ft.TextButton("全选", on_click=select_all_files, icon="select_all"),
                        ft.TextButton("取消全选", on_click=deselect_all_files, icon="deselect"),
                    ],
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=5,
                ),
            ],
            spacing=5,
            scroll=ft.ScrollMode.AUTO,
        ),
        padding=10,
        border_radius=10,
        expand=2,
    )

    # 右栏 - 预览 + 输入
    info_row = ft.Row(
        [
            ft.Text(
                "💡 勾选左侧模板 + 中间文件 + 底部问题 → 生成拼接内容",
                size=12,
                color="grey_400",
            )
        ]
    )

    input_section = ft.Column(
        [
            ft.Row(
                [
                    ft.Text("➕ 追加当前问题:", weight=ft.FontWeight.BOLD, size=14),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            question_container,
            ft.Row(
                [
                    ft.Button(
                        "🧹 清空选择", on_click=clear_all, icon="cleaning_services"
                    ),
                    ft.Container(expand=True),
                    btn_generate := ft.Button(
                        "⚡ 生成并复制全部内容",
                        on_click=generate_and_copy,
                        icon="content_copy",
                        height=50,
                    ),
                ],
                alignment=ft.MainAxisAlignment.END,
            ),
        ],
        spacing=10,
    )

    main_area = ft.Container(
        content=ft.Column(
            controls=[
                info_row,
                ft.Divider(height=10, color="transparent"),
                preview_container,
                ft.Divider(height=15, color="transparent"),
                input_section,
            ],
            spacing=0,
            expand=True,
        ),
        expand=3,  # flex factor 3
        padding=15,
    )

    # 三栏布局（与 test_layout.py 一致的模式）
    page.add(
        ft.Row(
            [sidebar, tree_panel, main_area],
            expand=True,
            spacing=2,
        )
    )

    refresh_sidebar()
    render_file_tree()
    update_preview()


if __name__ == "__main__":
    ft.run(main)
