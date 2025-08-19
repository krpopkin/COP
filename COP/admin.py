import reflex as rx
from COP.layout import with_sidebar
from COP.state import State
from db import fetch_all_regions, add_region, update_region, delete_region, get_conn

class RegionsState(rx.State):
    regions: list[dict] = []
    show_regions: bool = False
    new_region_name: str = ""
    region_error_message: str = ""

    def on_mount(self):
        """Initialize regions state and load data."""
        self.show_regions = False
        self.load_regions_data()

    def load_regions_data(self):
        """Load regions data from database."""
        try:
            self.regions = fetch_all_regions()
            self.show_regions = True
        except Exception as e:
            print(f"Error loading regions: {e}")
            self.regions = []
            self.show_regions = False

    def validate_region_in_court_ids(self, region_name: str) -> bool:
        """Check if region exists in court_ids table."""
        if not region_name:
            return False

        conn = get_conn()
        if conn is None:
            return False

        try:
            cur = conn.cursor()
            query = "SELECT COUNT(*) FROM court_ids WHERE region = %s"
            cur.execute(query, (region_name,))
            result = cur.fetchone()
            count = result[0] if isinstance(result, tuple) else result.get("count", 0)
            return count > 0
        except Exception:
            return False
        finally:
            conn.close()

    def add_new_region(self):
        """Add new region to database after validation."""
        self.region_error_message = ""  # Clear previous error
        
        if not self.new_region_name:
            self.region_error_message = "Please enter a region name"
            return
            
        # Check if region is valid in court_ids table
        if not self.validate_region_in_court_ids(self.new_region_name):
            self.region_error_message = "The PACER API does not support this region"
            return
            
        try:
            add_region(self.new_region_name)
            self.new_region_name = ""
            self.region_error_message = ""
            self.load_regions_data()
        except Exception as e:
            print(f"Error adding region: {e}")
            self.region_error_message = "Error adding region to database"

    def update_region_data(self, region_id: int, name: str):
        """Update region in database."""
        try:
            update_region(region_id, name)
            self.load_regions_data()
        except Exception as e:
            print(f"Error updating region: {e}")

    def delete_region_data(self, region_id: int):
        """Delete region from database."""
        try:
            delete_region(region_id)
            self.load_regions_data()
        except Exception as e:
            print(f"Error deleting region: {e}")

def admin() -> rx.Component:
    return rx.cond(
        State.permission == "admin",
        with_sidebar(
            rx.box(
                rx.vstack(
                    rx.center(rx.heading("Admin Panel", size="7", padding="0.0em"), width="100%"),

                    # Form inputs section
                    rx.hstack(
                        # Left side - Users form
                        rx.vstack(
                            rx.heading("Add New User", size="5"),
                            rx.hstack(
                                rx.input(
                                    placeholder="Username",
                                    value=State.new_username,
                                    on_change=State.set_new_username,
                                    width="120px"
                                ),
                                rx.input(
                                    placeholder="Password",
                                    type="password",
                                    value=State.new_password,
                                    on_change=State.set_new_password,
                                    width="120px"
                                ),
                                rx.select(
                                    ["admin", "edit", "browse"],
                                    value=State.new_permission,
                                    on_change=State.set_new_permission,
                                    width="100px"
                                ),
                                spacing="1",
                                align="center"
                            ),
                            spacing="4",
                            align="start",
                            width="48%"
                        ),

                        # Right side - Regions form
                        rx.vstack(
                            rx.heading("Add New Region", size="5"),
                            rx.input(
                                placeholder="Region Name",
                                value=RegionsState.new_region_name,
                                on_change=RegionsState.set_new_region_name,
                                width="200px"
                            ),
                            spacing="4",
                            align="start",
                            width="48%"
                        ),

                        spacing="4",
                        width="100%",
                        align="start"
                    ),

                    # Buttons row
                    rx.hstack(
                        rx.button("Add User", on_click=State.on_add_user),
                        rx.box(width="38%"),  # Spacer to align Add Region button with its form
                        rx.button("Add Region", on_click=RegionsState.add_new_region),
                        spacing="4",
                        width="100%",
                        align="start"
                    ),
                    
                    # Error message display for regions
                    rx.hstack(
                        rx.box(width="48%"),  # Empty space to match left column width
                        rx.cond(
                            RegionsState.region_error_message != "",
                            rx.text(
                                RegionsState.region_error_message,
                                color="red",
                                size="2",
                                weight="medium"
                            ),
                            rx.box()
                        ),
                        spacing="4",
                        width="100%"
                    ),

                    # Tables section with top alignment
                    rx.hstack(
                        # Left side - Users table
                        rx.vstack(
                            rx.divider(margin_y="1em"),
                            
                            # Users Table Header
                            rx.hstack(
                                rx.box(rx.text("Username", weight="bold"), width="25%"),
                                rx.box(rx.text("Permission", weight="bold"), width="25%"),
                                rx.box(rx.text("Actions", weight="bold"), width="50%"),
                                width="100%"
                            ),

                            # Users Table Data
                            rx.cond(
                                State.show_users,
                                rx.foreach(
                                    State.users_display,
                                    lambda user_data: rx.hstack(
                                        rx.text(user_data[0], width="25%"),  # username
                                        rx.select(
                                            ["admin", "edit", "browse"],
                                            value=user_data[1],  # permission
                                            on_change=lambda val: State.on_update_permission(user_data[0], val),
                                            width="25%",
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
                                rx.text("Loading users...", size="2")
                            ),
                            
                            spacing="2",
                            align="start",
                            width="48%"
                        ),

                        # Right side - Regions table
                        rx.vstack(
                            rx.divider(margin_y="1em"),
                            
                            # Regions Table Header
                            rx.hstack(
                                rx.box(rx.text("Region Name", weight="bold"), width="65%"),
                                rx.box(rx.text("Actions", weight="bold"), width="35%"),
                                width="100%"
                            ),

                            # Regions Table Data
                            rx.cond(
                                RegionsState.show_regions,
                                rx.foreach(
                                    RegionsState.regions,
                                    lambda region: rx.hstack(
                                        rx.box(rx.text(region["region_name"], size="2"), width="65%"),
                                        rx.box(
                                            rx.hstack(
                                                rx.button(
                                                    "Edit",
                                                    size="1"
                                                ),
                                                rx.button(
                                                    "Delete",
                                                    on_click=lambda _, region_id=region["id"]: RegionsState.delete_region_data(region_id),
                                                    size="1",
                                                    color_scheme="red"
                                                ),
                                                spacing="2",
                                            ),
                                            width="35%"
                                        ),
                                        width="100%",
                                        py="2"
                                    )
                                ),
                                rx.text("Loading regions...", size="2")
                            ),
                            
                            spacing="2",
                            align="start",
                            width="48%"
                        ),

                        spacing="4",
                        width="100%",
                        align="start"
                    ),

                    spacing="4",
                    align="start",
                    padding_top="0.0em",  
                    padding_x="2em",   
                    on_mount=[State.on_mount, RegionsState.on_mount]
                )
            )
        ),
        rx.heading("Unauthorized", color="red")
    )