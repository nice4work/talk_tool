import flet as ft

async def main(page: ft.Page):
    def on_button_click(e):
        print("=== TextField Properties ===")
        print(f"Type: {type(text_field)}")
        print(f"Dir: {dir(text_field)}")
        print("\n=== Common properties ===")
        print(f"Has value: {hasattr(text_field, 'value')}")
        print(f"Has selection: {hasattr(text_field, 'selection')}")
        print(f"Has selected_text: {hasattr(text_field, 'selected_text')}")
        print(f"Has selection_start: {hasattr(text_field, 'selection_start')}")
        print(f"Has selection_end: {hasattr(text_field, 'selection_end')}")
        print(f"Has selection_base: {hasattr(text_field, 'selection_base')}")
        print(f"Has selection_extent: {hasattr(text_field, 'selection_extent')}")

    text_field = ft.TextField(
        value="Hello world, this is a test",
        multiline=True,
        min_lines=5,
        width=400
    )

    page.add(
        text_field,
        ft.ElevatedButton("Check Properties", on_click=on_button_click)
    )

ft.run(main)