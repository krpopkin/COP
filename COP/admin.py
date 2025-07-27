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

                    # Table Body
                    rx.foreach(
                        State.users,
                        lambda user: rx.hstack(
                            rx.text(user[0], width="20%"),
                            rx.select(
                                ["admin", "edit", "browse"],
                                value=State.edit_permission[user[0]],
                                on_change=lambda val: State.on_update_permission(user[0], val),
                                width="20%",
                            ),
                            rx.hstack(
                                rx.button(
                                    "Save",
                                    on_click=lambda: State.on_save_permission(user[0]),
                                    size="1"
                                ),
                                rx.button(
                                    "Delete",
                                    on_click=lambda: State.on_delete_user(user[0]),
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
                        value=State.new_username,  # ✅ bind to state
                        on_change=State.set_new_username
                    ),
                    
                    rx.input(
                        placeholder="Password",
                        type_="password",
                        value=State.new_password,  # ✅ bind to state
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
                    #padding="2em",
                    padding_top="0.0yem",  
                    padding_x="2em",   
                )
            )
        ),
        rx.heading("Unauthorized", color="red")
    )
