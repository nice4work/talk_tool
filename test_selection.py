import flet as ft

async def main(page: ft.Page):
    def on_button_click(e):
        print(f"TextField value: {text_field.value}")
        print(f"TextField has selection_start: {hasattr(text_field, 'selection_start')}")
        print(f"TextField has selection_end: {hasattr(text_field, 'selection_end')}")
        if hasattr(text_field, 'selection_start') and hasattr(text_field, 'selection_end'):
            print(f"Selection start: {text_field.selection_start}")
            print(f"Selection end: {text_field.selection_end}")
            if text_field.selection_start is not None and text_field.selection_end is not None:
                selected_text = text_field.value[text_field.selection_start:text_field.selection_end]
                print(f"Selected text: {selected_text}")

    text_field = ft.TextField(
        value="Hello world, this is a test",
        multiline=True,
        min_lines=5,
        width=400
    )

    page.add(
        text_field,
        ft.ElevatedButton("Get Selection", on_click=on_button_click)
    )

ft.run(main)