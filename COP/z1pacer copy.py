import reflex as rx
from COP.layout import with_sidebar
from COP.state import State
import pacer_api
from datetime import date, timedelta
from db import fetch_all_cases

class PacerPageState(rx.State):
    date_from: str = ""
    rows: list[dict] = []
    show_grid: bool = False

    def on_mount(self):
        """Initialize state."""
        self.show_grid = False

    def load_grid_data(self):
        """Load grid data when button is clicked."""
        try:
            self.rows = fetch_all_cases()
            self.show_grid = True
        except Exception as e:
            print(f"Error: {e}")
            self.rows = []
            self.show_grid = False

    def load_more_cases(self):
        """Fetch more cases from PACER."""
        df = self.date_from or (date.today() - timedelta(days=1)).isoformat()
        cfg = pacer_api.env_cfg(pacer_api.ENV)
        token = pacer_api.authenticate(cfg["USERNAME"], cfg["PASSWORD"], cfg["AUTH_URL"])
        if not token:
            return
        cases = pacer_api.search_cases_by_date(token, cfg["PCL_API_ROOT"], df)
        pacer_api.upsert_pacer_cases(cases)
        self.load_grid_data()

def pacer() -> rx.Component:
    yday = (date.today() - timedelta(days=1)).isoformat()
    region_options = ["All"]

    content = rx.vstack(
        rx.heading("Information from PACER", size="7", text_align="center", width="100%", py="1em"),

        rx.text("Retrieve new PACER cases", weight="bold", size="4", align="left", width="100%"),

        rx.hstack(
            rx.vstack(
                rx.text("Date from"),
                rx.input(
                    type_="date",
                    default_value=yday,
                    width="14rem",
                    on_change=PacerPageState.set_date_from,
                ),
                align="start",
                spacing="1",
            ),
            rx.vstack(
                rx.text("Date to"),
                rx.input(type_="date", default_value=yday, width="14rem"),
                align="start",
                spacing="1",
            ),
            rx.vstack(
                rx.text("Region"),
                rx.select(items=region_options, default_value="All", width="14rem"),
                align="start",
                spacing="1",
            ),
            spacing="6",
            width="100%",
            align="start",
            wrap="wrap",
        ),

        rx.hstack(
            rx.button("Load more cases", on_click=PacerPageState.load_more_cases),
            align="start",
            width="100%",
        ),

        rx.text("Cases previously retrieved from PACER", weight="bold", size="4", mt="5", align="left", width="100%"),

        # Simple load button
        rx.hstack(
            rx.button(
                "Load Cases into Table", 
                on_click=PacerPageState.load_grid_data,
                size="2",
            ),
            align="start",
            width="100%",
            mb="3",
        ),

        # Only show table when button is clicked
        rx.cond(
            PacerPageState.show_grid,
            # Table displaying case details with links
            rx.box(
                rx.vstack(
                    rx.hstack(
                        rx.box(rx.text("Case Title", weight="bold"), width="20%"),
                        rx.box(rx.text("Case Link", weight="bold"), width="15%"),
                        rx.box(rx.text("Case Summary", weight="bold"), width="15%"),
                        rx.box(rx.text("Parties", weight="bold"), width="15%"),
                        rx.box(rx.text("Attorney", weight="bold"), width="15%"),
                        width="100%"
                    ),
                    rx.foreach(
                        PacerPageState.rows,
                        lambda case_data: rx.hstack(
                            rx.text(case_data["case_title"], width="20%"),
                            rx.link(
                                "link",
                                href=case_data["case_link"],
                                target="_blank",  # Open in new tab
                                width="15%"
                            ),
                            rx.link(
                                "link",
                                href=case_data["case_summary"],
                                target="_blank",  # Open in new tab
                                width="15%"
                            ),
                            rx.link(
                                "link",
                                href=case_data["parties"],
                                target="_blank",  # Open in new tab
                                width="15%"
                            ),
                            rx.link(
                                "link",
                                href=case_data["attorney"],
                                target="_blank",  # Open in new tab
                                width="15%"
                            ),
                            width="100%"
                        )
                    ),
                ),
                width="100%",
            ),
            # Simple message when table isn't shown
            rx.box(
                rx.center(
                    rx.text("Click 'Load Cases into Table' to display the data"),
                    height="400px",
                ),
                border="1px solid #ddd",
                width="100%",
            ),
        ),

        align="start",
        spacing="4",
        width="100%",
        on_mount=PacerPageState.on_mount,
    )

    return rx.cond(
        (State.permission == "admin") | (State.permission == "edit") | (State.permission == "browse"),
        with_sidebar(rx.box(content, px="2em", pb="2em", width="100%")),
        rx.heading("Unauthorized", color="red"),
    )