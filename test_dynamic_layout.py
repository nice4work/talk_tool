import flet as ft


def main(page: ft.Page):
    page.title = "Flet 3列拖拽布局 (v0.82.2 兼容版)"
    page.spacing = 0
    page.padding = 0

    # 初始宽度
    col_widths = {"left": 250, "middle": 300}

    def create_col_content(label, color):
        return ft.Container(
            content=ft.Column([
                ft.Text(label, size=20, weight="bold", color=ft.Colors.BLACK),
                ft.Divider(),
                ft.TextField(label=f"{label} 输入框", border_radius=8),
                ft.ElevatedButton("保存设置", icon=ft.Icons.SAVE),
            ], scroll=ft.ScrollMode.AUTO, tight=True),
            bgcolor=color,
            padding=15,
            expand=True,
        )

    # 定义列容器
    left_container = ft.Container(
        content=create_col_content("左侧菜单", ft.Colors.BLUE_GREY_50),
        width=col_widths["left"],
    )

    middle_container = ft.Container(
        content=create_col_content("中间看板", ft.Colors.WHITE),
        width=col_widths["middle"],
    )

    right_container = ft.Container(
        content=create_col_content("右侧详情", ft.Colors.BLUE_GREY_100),
        expand=True,
    )

    # --- 关键修正：使用 primary_delta ---

    def on_left_drag(e: ft.DragUpdateEvent):
        # primary_delta 是当前轴向的偏移量
        new_width = left_container.width + e.primary_delta
        if 100 < new_width < 600:
            left_container.width = new_width
            left_container.update()

    def on_middle_drag(e: ft.DragUpdateEvent):
        new_width = middle_container.width + e.primary_delta
        if 150 < new_width < 800:
            middle_container.width = new_width
            middle_container.update()

    # 拖拽手柄
    def resizer(on_drag_func):
        return ft.GestureDetector(
            content=ft.VerticalDivider(width=5, thickness=2, color=ft.Colors.BLUE_200),
            # 使用针对性的横向拖拽事件
            on_horizontal_drag_update=on_drag_func,
            mouse_cursor=ft.MouseCursor.RESIZE_LEFT_RIGHT,
        )

    # 页面布局
    page.add(
        ft.Row(
            controls=[
                left_container,
                resizer(on_left_drag),
                middle_container,
                resizer(on_middle_drag),
                right_container,
            ],
            expand=True,
            spacing=0,
        )
    )


if __name__ == "__main__":
    ft.run(main)