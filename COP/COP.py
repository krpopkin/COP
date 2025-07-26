import reflex as rx
from rxconfig import config
from COP import pacer, admin
from db import get_user
from COP.state import State 

def index() -> rx.Component:
    return rx.container(
        rx.color_mode.button(position="top-right"),
        rx.vstack(
            rx.heading("Criminal Opportunity Program (COP)", size="8", padding="1em"),
            rx.form(
                rx.vstack(
                    rx.input(
                        placeholder="User ID",
                        on_change=State.set_userid,
                        size="3",
                    ),
                    rx.input(
                        placeholder="Password",
                        type_="password",
                        on_change=State.set_password,
                        size="3",
                    ),
                    rx.button("Login", on_click=State.on_login, size="3"), 
                    rx.cond(
                        State.login_error != "",
                        rx.text(State.login_error, color="red"),
                        rx.box()
                    ),
                ),
                width="100%",
                max_width="400px",
            ),
            spacing="6",
            justify="center",
            align="center",
            min_height="85vh",
        ),
    )


app = rx.App()
app.add_page(index, route="/")
app.add_page(pacer.pacer, route="/pacer")
app.add_page(admin.admin, route="/admin")
