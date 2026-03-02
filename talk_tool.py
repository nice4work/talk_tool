import flet as ft
import json
import os
import uuid
import asyncio
import subprocess
import platform

DATA_FILE = "context_templates.json"
PLACEHOLDER_TEXT = "在此输入你具体要问的问题，它会自动附加在所有模板内容之后..."


def main(page: ft.Page):
    page.title = "ContextFlow Pro (Flet 版)"
    page.theme_mode = ft.ThemeMode.DARK
    page.padding = 20
    page.window_width = 1100
    page.window_height = 750
    page.scroll = ft.ScrollMode.HIDDEN

    templates = {}
    selected_ids = set()

    def load_data():
        if not os.path.exists(DATA_FILE):
            return {
                str(uuid.uuid4())[:8]: {"title": "Vue3 项目规范",
                                        "content": "# Vue3 规范\n- 使用 script setup\n- 禁止 any"},
                str(uuid.uuid4())[:8]: {"title": "Python 风格指南",
                                        "content": "# Python 规范\n- 遵循 PEP8\n- 类型提示完整"}
            }
        try:
            # 尝试使用 UTF-8 编码读取
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except UnicodeDecodeError:
            # 回退到其他编码
            try:
                with open(DATA_FILE, 'r', encoding='gbk') as f:
                    return json.load(f)
            except Exception:
                return {}
        except Exception:
            return {}

    def save_data():
        # 确保使用 UTF-8 编码保存，并且禁用 ensure_ascii 以正确处理中文
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
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
        expand=True,  # 填满父容器
    )

    question_input = ft.TextField(
        label="➕ 追加当前问题",
        multiline=True,
        min_lines=3,
        max_lines=6,
        hint_text=PLACEHOLDER_TEXT,
        shift_enter=True,
        on_change=lambda e: update_preview(),
    )

    checkbox_list = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=5)

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
                parts.append(header + data['content'])

        question = get_real_question()
        if question:
            header = f"\n\n{'=' * 20} [Question] {'=' * 20}\n\n"
            parts.append(header + question)

        return "".join(parts).lstrip() if parts else ""

    def update_preview(e=None):
        result = build_content_string()
        if not result:
            preview_text.value = "(等待操作：请勾选左侧模板 或 在底部输入问题)"
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
                label=data['title'],
                value=t_id in selected_ids,
                on_change=lambda e, tid=t_id: on_checkbox_change(e, tid)
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

        # 使用系统原生剪贴板命令
        try:
            if platform.system() == 'Darwin':  # macOS
                # macOS 需要设置 LANG 环境变量来正确处理 UTF-8
                env = os.environ.copy()
                env['LANG'] = 'en_US.UTF-8'
                subprocess.run(['pbcopy'], input=final_string.encode('utf-8'), check=True, env=env)
            elif platform.system() == 'Windows':
                subprocess.run(['clip'], input=final_string.encode('utf-8'), check=True)
            else:  # Linux
                subprocess.run(['xclip', '-selection', 'clipboard'], input=final_string.encode('utf-8'), check=True)
        except Exception as ex:
            page.snack_bar = ft.SnackBar(ft.Text(f"复制失败: {str(ex)}"))
            page.snack_bar.open = True
            page.update()
            return

        # 3. 更新按钮 UI (成功分支)
        button = e.control
        original_content = button.content
        # 保存原始样式对象引用，避免丢失
        original_bgcolor = None
        if button.style:
            original_bgcolor = button.style.bgcolor

        # 修改按钮状态
        button.content = f"✅ 已复制 ({len(final_string)} 字符)"
        if button.style:
            button.style.bgcolor = "green"
        else:
            button.style = ft.ButtonStyle(bgcolor="green")  # 注意是 ButtonStyle 不是 ButtonStyle

        page.update()

        await asyncio.sleep(2)

        # 恢复按钮状态
        button.content = original_content
        if button.style:
            button.style.bgcolor = original_bgcolor
        page.update()

    def clear_all(e):
        selected_ids.clear()
        question_input.value = ""
        refresh_sidebar()
        update_preview()

    def create_new_template(e):
        title_field = ft.TextField(label="模板标题", expand=True)
        content_field = ft.TextField(label="模板内容", multiline=True, min_lines=10, expand=True)

        def save_dialog(e):
            if not title_field.value or not content_field.value:
                page.snack_bar = ft.SnackBar(ft.Text("标题和内容不能为空"))
                page.snack_bar.open = True
                page.update()
                return

            new_id = str(uuid.uuid4())[:8]
            templates[new_id] = {"title": title_field.value, "content": content_field.value}
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
            content=ft.Column([title_field, content_field], tight=True),
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

    # ================= 布局组装 (最终修复版) =================

    sidebar = ft.Container(
        content=ft.Column([
            ft.Text("📚 模板库", size=20, weight=ft.FontWeight.BOLD),
            ft.Button("+ 新建模板", on_click=create_new_template, icon="add"),
            ft.Divider(),
            checkbox_list
        ], scroll=ft.ScrollMode.AUTO, expand=True),
        width=280,
        padding=15,
        border_radius=10,
        expand=False
    )

    info_row = ft.Row([
        ft.Text("💡 操作：勾选左侧模板 + 底部输入问题 -> 自动生成拼接内容", size=12, color="grey_400")
    ])

    input_section = ft.Column([
        ft.Row([
            ft.Text("➕ 追加当前问题:", weight=ft.FontWeight.BOLD, size=14),
        ], alignment=ft.MainAxisAlignment.START),
        question_input,
        ft.Row([
            ft.Button("🧹 清空选择", on_click=clear_all, icon="cleaning_services"),
            ft.Container(expand=True),
            btn_generate := ft.Button("⚡ 生成并复制全部内容", on_click=generate_and_copy, icon="content_copy",
                                      height=50),
        ], alignment=ft.MainAxisAlignment.END)
    ], spacing=10)

    # 【关键修复】
    # 1. 创建一个 Column 专门用于包裹预览区
    # 2. 设置 expand=True 让它占据剩余空间
    # 3. 设置 scroll=Auto 让它内部滚动
    preview_scroll_column = ft.Column(
        controls=[preview_text],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=0
    )

    # 主布局 Column
    # 结构：[Info] + [Scrollable Preview Column] + [Fixed Input Section]
    main_area = ft.Container(
        content=ft.Column(
            controls=[
                info_row,
                ft.Divider(height=10, color="transparent"),
                preview_scroll_column,  # 可滚动的中间部分
                ft.Divider(height=15, color="transparent"),
                input_section  # 固定的底部部分
            ],
            spacing=0,
            # 父 Column 不需要 scroll，因为子元素 preview_scroll_column 已经处理了滚动
        ),
        expand=True,
        padding=20
    )

    page.add(
        ft.Row([sidebar, main_area], expand=True, spacing=20)
    )

    refresh_sidebar()
    update_preview()


if __name__ == "__main__":
    ft.run(main)