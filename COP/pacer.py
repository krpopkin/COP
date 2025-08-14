import reflex as rx
from COP.layout import with_sidebar
from COP.state import State
import pacer_api
from datetime import date, timedelta
from db import fetch_all_cases


class PacerPageState(rx.State):
    date_from: str = ""
    rows: list[dict] = []

    def on_mount(self):
        """Load initial data from the DB when the page mounts."""
        try:
            self.rows = fetch_all_cases()
        except Exception:
            self.rows = []

    def load_more_cases(self):
        """Fetch more cases from PACER, upsert to DB, then refresh the grid data."""
        df = self.date_from or (date.today() - timedelta(days=1)).isoformat()
        cfg = pacer_api.env_cfg(pacer_api.ENV)
        token = pacer_api.authenticate(cfg["USERNAME"], cfg["PASSWORD"], cfg["AUTH_URL"])
        if not token:
            print("Auth failed.")
            return
        cases = pacer_api.search_cases_by_date(token, cfg["PCL_API_ROOT"], df)
        pacer_api.upsert_pacer_cases(cases)
        # Refresh grid from DB
        try:
            self.rows = fetch_all_cases()
        except Exception:
            self.rows = []


COLUMNS = [
    "court_id", "case_id", "case_number", "case_type", "case_title", "date_filed",
    "jurisdiction_type", "case_link", "case_summary", "parties", "attorney",
]


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

        # === DATA TABLE (sortable + search + pagination) ===
        rx.box(
            rx.data_table(
                data=PacerPageState.rows,   # reactive: list[dict] from DB
                columns=COLUMNS,            # enforce column order/labels
                search=True,
                sort=True,
                pagination={"limit": 25},   # 25 rows per page
                width="100%",
            ),
            width="100%",
        ),

        align="start",
        spacing="4",
        width="100%",
        on_mount=PacerPageState.on_mount,   # load initial data
    )

    return rx.cond(
        (State.permission == "admin") | (State.permission == "edit") | (State.permission == "browse"),
        with_sidebar(rx.box(content, px="2em", pb="2em", width="100%")),  # normal padding (no badge)
        rx.heading("Unauthorized", color="red"),
    )
