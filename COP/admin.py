import reflex as rx
from COP.layout import with_sidebar
from COP.state import State

def admin() -> rx.Component:
    return rx.cond(
        State.permission == "admin",
        with_sidebar(
            rx.box(
                rx.vstack(
                    rx.heading("Welcome to Admin", size="7", padding="2em"),
                    justify="center",
                    align="center",
                    min_height="85vh",
                )
            )
        ),
        rx.heading("Unauthorized", color="red")
    )
