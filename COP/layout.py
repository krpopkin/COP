#################################################################################
# Contains global layouts of...
# 1. left nav
#
#################################################################################
import reflex as rx

def sidebar() -> rx.Component:
    return rx.box(
        rx.vstack(
            rx.link("Pacer", href="/pacer"),
            rx.link("Admin", href="/admin"),
            rx.link("Logout", href="/"),
            spacing="4",
            align="start",
            padding_top="4em"
        ),
        width="200px",
        padding="1em",
        border_right="1px solid lightgray",
        min_height="100vh",
    )


def with_sidebar(content: rx.Component) -> rx.Component:
    return rx.hstack(
        sidebar(),
        rx.box(content, padding="2em", width="100%"),
    )
