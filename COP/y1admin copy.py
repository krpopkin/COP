import reflex as rx
from COP.layout import with_sidebar
from COP.state import State

def admin() -> rx.Component:
    return rx.cond(
        State.permission == "admin",
        with_sidebar(
            rx.box(
                rx.vstack(
                    rx.center(rx.heading("Admin Panel", size="7", padding="0.0em"), width="60%"),

                    rx.button("Refresh Users", on_click=State.load_users),

                    # Table Header
                    rx.hstack(
                        rx.box(rx.text("Username", weight="bold"), width="20%"),
                        rx.box(rx.text("Permission", weight="bold"), width="20%"),
                        rx.box(rx.text("Actions", weight="bold"), width="33%"),
                        width="100%"
                    ),

                    # Using the simplified display format
                    rx.foreach(
                        State.users_display,
                        lambda user_data: rx.hstack(
                            rx.text(user_data[0], width="20%"),  # username
                            rx.select(
                                ["admin", "edit", "browse"],
                                value=user_data[1],  # permission
                                on_change=lambda val: State.on_update_permission(user_data[0], val),
                                width="20%",
                            ),
                            rx.hstack(
                                rx.button(
                                    "Save",
                                    on_click=lambda _, username=user_data[0]: State.on_save_permission(username),
                                    size="1"
                                ),
                                rx.button(
                                    "Delete",
                                    on_click=lambda _, username=user_data[0]: State.on_delete_user(username),
                                    size="1",
                                    color_scheme="red"
                                ),
                            ),
                            width="100%",
                        )
                    ),

                    rx.divider(margin_y="2em"),
                    rx.heading("Add New User", size="5"),
                    rx.input(
                        placeholder="Username",
                        value=State.new_username,
                        on_change=State.set_new_username
                    ),
                    
                    rx.input(
                        placeholder="Password",
                        type_="password",
                        value=State.new_password,
                        on_change=State.set_new_password
                    ),
                    
                    rx.select(
                        ["admin", "edit", "browse"],
                        value=State.new_permission,
                        on_change=State.set_new_permission
                    ),
                    rx.button("Add User", on_click=State.on_add_user),

                    spacing="4",
                    align="start",
                    padding_top="0.0yem",  
                    padding_x="2em",   
                )
            )
        ),
        rx.heading("Unauthorized", color="red")
    )