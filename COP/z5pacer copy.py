import reflex as rx
from COP.layout import with_sidebar
from COP.state import State
import pacer_api
from datetime import date, timedelta
from db import fetch_all_cases, fetch_all_regions

class PacerPageState(rx.State):
    date_from: str = ""
    date_to: str = ""  # Add date_to field
    rows: list[dict] = []
    show_grid: bool = False
    sort_column: str = ""
    sort_ascending: bool = True
    regions: list[dict] = []
    selected_region: str = "All"
    cases_loaded_count: int = 0
    show_cases_loaded: bool = False

    def on_mount(self):
        """Initialize state and load data."""
        self.show_grid = False
        self.load_regions()
        self.load_grid_data()

    def load_regions(self):
        """Load regions from database."""
        try:
            self.regions = fetch_all_regions()
        except Exception as e:
            print(f"Error loading regions: {e}")
            self.regions = []

    @rx.var
    def region_options(self) -> list[str]:
        """Get region options with 'All' as first option."""
        options = ["All"]
        for region in self.regions:
            options.append(region["region_name"])
        return options

    def load_grid_data(self):
        """Load grid data when button is clicked."""
        try:
            self.rows = fetch_all_cases()
            # Sort by date_filed in descending order by default
            self.sort_column = "date_filed"
            self.sort_ascending = False
            
            def sort_key(item):
                value = item.get("date_filed", "")
                if value is None:
                    return ""
                return str(value).lower()
            
            self.rows = sorted(self.rows, key=sort_key, reverse=True)  # reverse=True for descending
            self.show_grid = True
        except Exception as e:
            print(f"Error: {e}")
            self.rows = []
            self.show_grid = False

    def load_more_cases(self):
        """Fetch more cases from PACER."""
        df = self.date_from or (date.today() - timedelta(days=1)).isoformat()
        dt = self.date_to or (date.today() - timedelta(days=1)).isoformat()
        
        cfg = pacer_api.env_cfg(pacer_api.ENV)
        token = pacer_api.authenticate(cfg["USERNAME"], cfg["PASSWORD"], cfg["AUTH_URL"])
        if not token:
            self.cases_loaded_count = 0
            self.show_cases_loaded = True
            return
        
        all_cases = []
        
        if self.selected_region == "All":
            # Loop through all regions
            for region_data in self.regions:
                region_name = region_data["region_name"]
                print(f"Searching region: {region_name}")
                cases = pacer_api.search_cases_by_date(token, cfg["PCL_API_ROOT"], df, dt, region_name)
                if cases:
                    all_cases.extend(cases)
        else:
            # Search for the specific selected region
            cases = pacer_api.search_cases_by_date(token, cfg["PCL_API_ROOT"], df, dt, self.selected_region)
            if cases:
                all_cases.extend(cases)
        
        # Store the count of total cases returned
        self.cases_loaded_count = len(all_cases)
        self.show_cases_loaded = True
        pacer_api.upsert_pacer_cases(all_cases)
        self.load_grid_data()

    def sort_data(self, column: str):
        """Sort data by column, toggle direction if same column."""
        if self.sort_column == column:
            self.sort_ascending = not self.sort_ascending
        else:
            self.sort_column = column
            self.sort_ascending = True
        
        def sort_key(item):
            value = item.get(column, "")
            if value is None:
                return ""
            return str(value).lower()
        
        self.rows = sorted(self.rows, key=sort_key, reverse=not self.sort_ascending)

    @rx.var
    def sort_icon_case_title(self) -> str:
        if self.sort_column != "case_title":
            return "↕"
        return "↑" if self.sort_ascending else "↓"

    @rx.var
    def sort_icon_court_id(self) -> str:
        if self.sort_column != "court_id":
            return "↕"
        return "↑" if self.sort_ascending else "↓"

    @rx.var
    def sort_icon_case_id(self) -> str:
        if self.sort_column != "case_id":
            return "↕"
        return "↑" if self.sort_ascending else "↓"

    @rx.var
    def sort_icon_case_number(self) -> str:
        if self.sort_column != "case_number":
            return "↕"
        return "↑" if self.sort_ascending else "↓"

    @rx.var
    def sort_icon_case_type(self) -> str:
        if self.sort_column != "case_type":
            return "↕"
        return "↑" if self.sort_ascending else "↓"

    @rx.var
    def sort_icon_date_filed(self) -> str:
        if self.sort_column != "date_filed":
            return "↕"
        return "↑" if self.sort_ascending else "↓"

    @rx.var
    def sort_icon_jurisdiction_type(self) -> str:
        if self.sort_column != "jurisdiction_type":
            return "↕"
        return "↑" if self.sort_ascending else "↓"

    def sort_by_case_title(self):
        self.sort_data("case_title")
    
    def sort_by_court_id(self):
        self.sort_data("court_id")
    
    def sort_by_case_id(self):
        self.sort_data("case_id")
    
    def sort_by_case_number(self):
        self.sort_data("case_number")
    
    def sort_by_case_type(self):
        self.sort_data("case_type")
    
    def sort_by_date_filed(self):
        self.sort_data("date_filed")
    
    def sort_by_jurisdiction_type(self):
        self.sort_data("jurisdiction_type")

def pacer() -> rx.Component:
    yday = (date.today() - timedelta(days=1)).isoformat()

    content = rx.vstack(
        rx.heading("Information from PACER", size="7", text_align="center", width="100%", py="1em"),

        rx.text("Retrieve new PACER cases", weight="bold", size="4", align="left", width="100%"),

        rx.hstack(
            rx.vstack(
                rx.text("Date from", weight="medium"),
                rx.input(
                    type="date",
                    value=yday,
                    width="14rem",
                    on_change=PacerPageState.set_date_from,
                ),
                align="start",
                spacing="1",
            ),
            rx.vstack(
                rx.text("Date to", weight="medium"),
                rx.input(
                    type="date", 
                    value=yday, 
                    width="14rem",
                    on_change=PacerPageState.set_date_to,  # Add on_change handler
                ),
                align="start",
                spacing="1",
            ),
            rx.vstack(
                rx.text("Region", weight="medium"),
                rx.select(
                    items=PacerPageState.region_options,
                    value=PacerPageState.selected_region,
                    on_change=PacerPageState.set_selected_region,
                    width="14rem"
                ),
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
            rx.cond(
                PacerPageState.show_cases_loaded,
                rx.text(
                    f"Total new cases loaded: {PacerPageState.cases_loaded_count}",
                    size="3",
                    weight="medium",
                    color="green"
                ),
                rx.text("")
            ),
            align="start",
            spacing="4",
            width="100%",
        ),

        rx.text("Cases previously retrieved from PACER", weight="bold", size="4", mt="5", align="left", width="100%"),

        # Table displays automatically on page load
        rx.cond(
            PacerPageState.show_grid,
            rx.box(
                rx.vstack(
                    # Header row
                    rx.hstack(
                        rx.box(
                            rx.hstack(
                                rx.text("Case Title", weight="bold", size="2"),
                                rx.button(
                                    PacerPageState.sort_icon_case_title,
                                    variant="ghost",
                                    size="1",
                                    on_click=PacerPageState.sort_by_case_title,
                                ),
                                spacing="1",
                            ),
                            width="20%"
                        ),
                        rx.box(
                            rx.hstack(
                                rx.text("Court ID", weight="bold", size="2"),
                                rx.button(
                                    PacerPageState.sort_icon_court_id,
                                    variant="ghost",
                                    size="1",
                                    on_click=PacerPageState.sort_by_court_id,
                                ),
                                spacing="1",
                            ),
                            width="15%"
                        ),
                        rx.box(
                            rx.hstack(
                                rx.text("Case ID", weight="bold", size="2"),
                                rx.button(
                                    PacerPageState.sort_icon_case_id,
                                    variant="ghost",
                                    size="1",
                                    on_click=PacerPageState.sort_by_case_id,
                                ),
                                spacing="1",
                            ),
                            width="15%"
                        ),
                        rx.box(
                            rx.hstack(
                                rx.text("Case Number", weight="bold", size="2"),
                                rx.button(
                                    PacerPageState.sort_icon_case_number,
                                    variant="ghost",
                                    size="1",
                                    on_click=PacerPageState.sort_by_case_number,
                                ),
                                spacing="1",
                            ),
                            width="15%"
                        ),
                        rx.box(
                            rx.hstack(
                                rx.text("Case Type", weight="bold", size="2"),
                                rx.button(
                                    PacerPageState.sort_icon_case_type,
                                    variant="ghost",
                                    size="1",
                                    on_click=PacerPageState.sort_by_case_type,
                                ),
                                spacing="1",
                            ),
                            width="15%"
                        ),
                        rx.box(
                            rx.hstack(
                                rx.text("Date Filed", weight="bold", size="2"),
                                rx.button(
                                    PacerPageState.sort_icon_date_filed,
                                    variant="ghost",
                                    size="1",
                                    on_click=PacerPageState.sort_by_date_filed,
                                ),
                                spacing="1",
                            ),
                            width="10%"
                        ),
                        rx.box(
                            rx.hstack(
                                rx.text("Jurisdiction", weight="bold", size="2"),
                                rx.button(
                                    PacerPageState.sort_icon_jurisdiction_type,
                                    variant="ghost",
                                    size="1",
                                    on_click=PacerPageState.sort_by_jurisdiction_type,
                                ),
                                spacing="1",
                            ),
                            width="10%"
                        ),
                        width="100%",
                        border_bottom="2px solid #333",
                        pb="2"
                    ),
                    # Data rows
                    rx.foreach(
                        PacerPageState.rows,
                        lambda case_data: rx.vstack(
                            rx.hstack(
                                rx.box(
                                    rx.link(
                                        case_data["case_title"],
                                        href=case_data["case_link"],
                                        target="_blank",
                                        size="2"
                                    ), 
                                    width="20%"
                                ),
                                rx.box(rx.text(case_data["court_id"], size="2"), width="15%"),
                                rx.box(rx.text(case_data["case_id"], size="2"), width="15%"),
                                rx.box(rx.text(case_data["case_number"], size="2"), width="15%"),
                                rx.box(rx.text(case_data["case_type"], size="2"), width="15%"),
                                rx.box(rx.text(case_data["date_filed"], size="2"), width="10%"),
                                rx.box(rx.text(case_data["jurisdiction_type"], size="2"), width="10%"),
                                width="100%",
                                py="2"
                            ),
                            rx.box(
                                width="100%",
                                height="1px",
                                bg="#ddd"
                            ),
                            spacing="0",
                            width="100%"
                        )
                    ),
                    spacing="0",
                ),
                width="100%",
                overflow_x="auto"
            ),
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