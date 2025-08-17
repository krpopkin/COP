import reflex as rx 
from db import get_user, get_all_users, add_user, update_user_permission, delete_user

class State(rx.State):
    """The app state."""
    userid: str = ""
    password: str = ""
    permission: str = ""
    login_error: str = ""

    # Raw data from database
    users: list[dict] = []  
    # Simplified for UI display
    users_display: list[list] = []  
    show_users: bool = False

    new_username: str = ""
    new_password: str = ""
    new_permission: str = "browse"
    
    edit_permission: dict[str, str] = {}

    def on_mount(self):
        """Initialize state and load data."""
        self.show_users = False
        self.load_users()

    def on_login(self):
        user = get_user(self.userid, self.password)
        if user:
            self.permission = user["permission"]
            self.login_error = ""
            return rx.redirect("/pacer")  
        else:
            self.login_error = "Invalid credentials"
            
    def load_users(self):
        try:
            self.users = get_all_users()
            self.edit_permission = {user["username"]: user["permission"] for user in self.users}
            
            # Create the simplified display format
            self.users_display = [[user["username"], user["permission"]] for user in self.users]
            self.show_users = True
        except Exception as e:
            print(f"Error loading users: {e}")
            self.users = []
            self.users_display = []
            self.show_users = False

    def on_add_user(self):
        try:
            add_user(self.new_username, self.new_password, self.new_permission)
            self.new_username = ""
            self.new_password = ""
            self.new_permission = "browse"
            self.load_users()
        except Exception as e:
            print(f"Error adding user: {e}")

    def on_update_permission(self, username: str, permission: str):
        self.edit_permission[username] = permission

    def on_save_permission(self, username: str):
        try:
            update_user_permission(username, self.edit_permission[username])
            self.load_users()
        except Exception as e:
            print(f"Error saving permission: {e}")

    def on_delete_user(self, username: str):
        try:
            delete_user(username)
            self.load_users()
        except Exception as e:
            print(f"Error deleting user: {e}")