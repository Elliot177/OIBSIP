import sqlite3
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

# Set Matplotlib backend before importing pyplot/figure
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.dates as mdates


class DatabaseManager:
    """
    Handles SQLite database operations for multi-user management 
    and historical BMI record persistence with complete error handling.
    """
    def __init__(self, db_name="bmi_tracker.db"):
        self.db_name = db_name
        self.init_db()

    def get_connection(self):
        """Establishes connection to the SQLite database."""
        conn = sqlite3.connect(self.db_name)
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        """Creates required database tables if they do not exist."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS bmi_records (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        weight REAL NOT NULL,
                        height REAL NOT NULL,
                        unit_system TEXT NOT NULL,
                        bmi REAL NOT NULL,
                        category TEXT NOT NULL,
                        recorded_at TEXT NOT NULL,
                        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {e}")

    def get_all_users(self):
        """Fetches list of all registered users."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM users ORDER BY name ASC")
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not fetch user list: {e}")
            return []

    def add_user(self, name):
        """Adds a new user profile to the database."""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (name, created_at) VALUES (?, ?)", (name, now))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            messagebox.showwarning("Duplicate User", f"A user named '{name}' already exists.")
            return None
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to create user: {e}")
            return None

    def add_record(self, user_id, weight, height, unit_system, bmi, category):
        """Saves a new BMI calculation entry."""
        try:
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO bmi_records (user_id, weight, height, unit_system, bmi, category, recorded_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (user_id, weight, height, unit_system, bmi, category, now))
                conn.commit()
                return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to save record: {e}")
            return False

    def get_user_records(self, user_id):
        """Fetches all historical BMI entries for a given user."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT id, weight, height, unit_system, bmi, category, recorded_at
                    FROM bmi_records
                    WHERE user_id = ?
                    ORDER BY recorded_at ASC
                """, (user_id,))
                return cursor.fetchall()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Could not fetch history: {e}")
            return []

    def delete_record(self, record_id):
        """Deletes a single BMI entry by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM bmi_records WHERE id = ?", (record_id,))
                conn.commit()
                return True
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to delete record: {e}")
            return False


class BMICalculatorApp:
    """
    Full-featured Tkinter GUI application for multi-user BMI tracking,
    historical logging, and Matplotlib trend visualization.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("BMI Health Tracker & Trend Analyzer")
        self.root.geometry("980x700")
        self.root.minsize(900, 640)

        self.db = DatabaseManager()

        # Theme Color Palette (Modern Dark Slate theme)
        self.bg_color = "#1E1E2E"
        self.card_color = "#2A2A3D"
        self.accent_color = "#89B4FA"
        self.fg_color = "#CDD6F4"
        self.subtext_color = "#A6ADC8"

        # BMI Category Colors
        self.cat_colors = {
            "Underweight": "#38BDF8",  # Sky Blue
            "Normal weight": "#4ADE80", # Vibrant Green
            "Overweight": "#FACC15",    # Amber Yellow
            "Obese": "#F87171"          # Soft Red
        }

        self.root.configure(bg=self.bg_color)
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self._configure_styles()

        # State Variables
        self.selected_user_id = tk.IntVar(value=0)
        self.unit_system = tk.StringVar(value="metric") # 'metric' or 'imperial'
        self.weight_var = tk.StringVar(value="")
        self.height_var = tk.StringVar(value="")

        self._build_ui()
        self._load_users()

    def _configure_styles(self):
        """Configures ttk style attributes to match dark theme."""
        self.style.configure(".", background=self.bg_color, foreground=self.fg_color)
        self.style.configure("TFrame", background=self.bg_color)
        self.style.configure("Card.TFrame", background=self.card_color, relief="flat")

        self.style.configure("TLabel", background=self.bg_color, foreground=self.fg_color, font=("Segoe UI", 10))
        self.style.configure("Card.TLabel", background=self.card_color, foreground=self.fg_color, font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", background=self.bg_color, foreground=self.accent_color, font=("Segoe UI", 16, "bold"))
        
        self.style.configure("Action.TButton", font=("Segoe UI", 10, "bold"), padding=8, background=self.accent_color, foreground="#11111B")
        self.style.map("Action.TButton", background=[("active", "#B4BEFE")])

        self.style.configure("TRadiobutton", background=self.card_color, foreground=self.fg_color, font=("Segoe UI", 10))
        self.style.map("TRadiobutton", foreground=[("active", self.accent_color)], background=[("active", self.card_color)])

        self.style.configure("TNotebook", background=self.bg_color, borderwidth=0)
        self.style.configure("TNotebook.Tab", background=self.card_color, foreground=self.fg_color, padding=[12, 6], font=("Segoe UI", 10, "bold"))
        self.style.map("TNotebook.Tab", background=[("selected", self.accent_color)], foreground=[("selected", "#11111B")])

        # Treeview styling
        self.style.configure("Treeview", background="#181825", foreground=self.fg_color, fieldbackground="#181825", rowheight=25)
        self.style.configure("Treeview.Heading", background=self.card_color, foreground=self.accent_color, font=("Segoe UI", 10, "bold"))

    def _build_ui(self):
        """Constructs main layout grid split between input panel and tab views."""
        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header Title
        header_frame = ttk.Frame(main_container)
        header_frame.pack(fill=tk.X, pady=(0, 15))
        ttk.Label(header_frame, text="⚖️ BMI Calculator & Health Analyzer", style="Title.TLabel").pack(side=tk.LEFT)

        # Content Split Layout (Left: Input & Results | Right: History & Visual Graphs)
        content_box = ttk.Frame(main_container)
        content_box.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(content_box, width=380)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 15))

        right_panel = ttk.Frame(content_box)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self._build_input_panel(left_panel)
        self._build_output_tabs(right_panel)

    def _build_input_panel(self, parent):
        """Constructs controls for user selection, measurement input, and unit toggling."""
        # 1. User Profile Selector Card
        user_card = ttk.Frame(parent, style="Card.TFrame", padding="12")
        user_card.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(user_card, text=" Select User Profile", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 6))

        combo_row = ttk.Frame(user_card, style="Card.TFrame")
        combo_row.pack(fill=tk.X)

        self.user_dropdown = ttk.Combobox(combo_row, state="readonly", font=("Segoe UI", 10))
        self.user_dropdown.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
        self.user_dropdown.bind("<<ComboboxSelected>>", self._on_user_selected)

        add_btn = tk.Button(
            combo_row, text="+ New", command=self._add_new_user_dialog,
            bg=self.accent_color, fg="#11111B", font=("Segoe UI", 9, "bold"), bd=0, padx=8, pady=4
        )
        add_btn.pack(side=tk.RIGHT)

        # 2. Measurements Entry Card
        input_card = ttk.Frame(parent, style="Card.TFrame", padding="12")
        input_card.pack(fill=tk.X, pady=(0, 12))

        ttk.Label(input_card, text=" Enter Measurements", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 8))

        # Unit Selector Toggle
        unit_row = ttk.Frame(input_card, style="Card.TFrame")
        unit_row.pack(fill=tk.X, pady=(0, 10))

        ttk.Radiobutton(
            unit_row, text="Metric (kg, cm)", value="metric",
            variable=self.unit_system, command=self._update_unit_labels, style="TRadiobutton"
        ).pack(side=tk.LEFT, padx=(0, 15))

        ttk.Radiobutton(
            unit_row, text="Imperial (lbs, in)", value="imperial",
            variable=self.unit_system, command=self._update_unit_labels, style="TRadiobutton"
        ).pack(side=tk.LEFT)

        # Weight Entry Field
        self.weight_lbl = ttk.Label(input_card, text="Weight (kg):", style="Card.TLabel")
        self.weight_lbl.pack(anchor=tk.W, pady=(4, 2))

        self.weight_entry = tk.Entry(
            input_card, textvariable=self.weight_var, font=("Consolas", 12),
            bg="#181825", fg="#A6E3A1", insertbackground="white", relief="flat", bd=4
        )
        self.weight_entry.pack(fill=tk.X, pady=(0, 8))

        # Height Entry Field
        self.height_lbl = ttk.Label(input_card, text="Height (cm):", style="Card.TLabel")
        self.height_lbl.pack(anchor=tk.W, pady=(4, 2))

        self.height_entry = tk.Entry(
            input_card, textvariable=self.height_var, font=("Consolas", 12),
            bg="#181825", fg="#A6E3A1", insertbackground="white", relief="flat", bd=4
        )
        self.height_entry.pack(fill=tk.X, pady=(0, 12))

        # Calculate Button
        calc_btn = ttk.Button(
            input_card, text="⚡ Calculate & Save BMI",
            style="Action.TButton", command=self.calculate_bmi
        )
        calc_btn.pack(fill=tk.X)

        # 3. Result Summary Card
        self.result_card = ttk.Frame(parent, style="Card.TFrame", padding="12")
        self.result_card.pack(fill=tk.BOTH, expand=True)

        ttk.Label(self.result_card, text=" Results Overview", style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=(0, 6))

        self.bmi_display_lbl = tk.Label(
            self.result_card, text="--.--", font=("Segoe UI", 28, "bold"),
            bg=self.card_color, fg=self.fg_color
        )
        self.bmi_display_lbl.pack(anchor=tk.CENTER, pady=(2, 0))

        self.category_badge = tk.Label(
            self.result_card, text="Awaiting Input", font=("Segoe UI", 11, "bold"),
            bg="#45475A", fg="white", padx=12, pady=4
        )
        self.category_badge.pack(anchor=tk.CENTER, pady=(4, 10))

        self.ideal_weight_lbl = ttk.Label(
            self.result_card, text="Ideal Weight Range: --",
            style="Card.TLabel", font=("Segoe UI", 9)
        )
        self.ideal_weight_lbl.pack(anchor=tk.CENTER)

    def _build_output_tabs(self, parent):
        """Constructs tabbed notebook containing trend graphs and history table views."""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)

        # Tab 1: Matplotlib Chart View
        self.chart_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.chart_tab, text=" BMI Trend Chart")

        # Create Embedded Matplotlib Figure
        self.fig = Figure(figsize=(5, 4), dpi=100, facecolor=self.bg_color)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_facecolor("#181825")

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_tab)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Tab 2: Historical Log Table
        self.history_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(self.history_tab, text="📜 History Log")

        # Treeview Table for records
        columns = ("id", "date", "weight", "height", "bmi", "category")
        self.tree = ttk.Treeview(self.history_tab, columns=columns, show="headings", selectmode="browse")

        self.tree.heading("date", text="Date & Time")
        self.tree.heading("weight", text="Weight")
        self.tree.heading("height", text="Height")
        self.tree.heading("bmi", text="BMI")
        self.tree.heading("category", text="Category")

        self.tree.column("id", width=0, stretch=False)
        self.tree.column("date", width=140, anchor=tk.CENTER)
        self.tree.column("weight", width=80, anchor=tk.CENTER)
        self.tree.column("height", width=80, anchor=tk.CENTER)
        self.tree.column("bmi", width=70, anchor=tk.CENTER)
        self.tree.column("category", width=120, anchor=tk.CENTER)

        scrollbar = ttk.Scrollbar(self.history_tab, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)

        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Table Action Buttons
        hist_btn_frame = ttk.Frame(self.history_tab)
        hist_btn_frame.pack(fill=tk.X, pady=(8, 0))

        del_btn = tk.Button(
            hist_btn_frame, text=" Delete Selected Entry", command=self._delete_selected_record,
            bg="#F87171", fg="#11111B", font=("Segoe UI", 9, "bold"), bd=0, padx=10, pady=4
        )
        del_btn.pack(side=tk.RIGHT)

    def _load_users(self):
        """Loads registered users into dropdown box."""
        users = self.db.get_all_users()
        self.user_map = {name: uid for uid, name in users}

        names = list(self.user_map.keys())
        self.user_dropdown['values'] = names

        if names:
            self.user_dropdown.current(0)
            self._on_user_selected()
        else:
            self.user_dropdown.set("No users - Click + New")

    def _on_user_selected(self, event=None):
        """Callback triggered when a user is chosen from the dropdown."""
        selected_name = self.user_dropdown.get()
        if selected_name in self.user_map:
            self.selected_user_id.set(self.user_map[selected_name])
            self._refresh_data_views()

    def _add_new_user_dialog(self):
        """Opens prompt dialog to create a new user profile."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Create User Profile")
        dialog.geometry("320x150")
        dialog.configure(bg=self.bg_color)
        dialog.transient(self.root)
        dialog.grab_set()

        ttk.Label(dialog, text="Enter User Name:", font=("Segoe UI", 10, "bold")).pack(pady=(15, 5))
        name_entry = tk.Entry(dialog, font=("Segoe UI", 11), bg="#181825", fg="white", insertbackground="white")
        name_entry.pack(pady=5, padx=20, fill=tk.X)
        name_entry.focus()

        def save():
            name = name_entry.get().strip()
            if not name:
                messagebox.showwarning("Input Error", "User name cannot be empty.", parent=dialog)
                return
            
            uid = self.db.add_user(name)
            if uid:
                dialog.destroy()
                self._load_users()
                self.user_dropdown.set(name)
                self._on_user_selected()

        tk.Button(
            dialog, text="Save Profile", command=save,
            bg=self.accent_color, fg="#11111B", font=("Segoe UI", 9, "bold"), bd=0, pady=4
        ).pack(pady=10)

    def _update_unit_labels(self):
        """Updates text labels based on active unit system."""
        if self.unit_system.get() == "metric":
            self.weight_lbl.config(text="Weight (kg):")
            self.height_lbl.config(text="Height (cm):")
        else:
            self.weight_lbl.config(text="Weight (lbs):")
            self.height_lbl.config(text="Height (inches):")

    def calculate_bmi(self):
        """
        Validates user input, calculates BMI value, evaluates health category,
        computes target weight range, and saves entry to SQLite database.
        """
        user_id = self.selected_user_id.get()
        if user_id == 0:
            messagebox.showwarning("User Required", "Please select or create a user profile first.")
            return

        # Input Parsing and Validation
        try:
            weight = float(self.weight_var.get())
            height = float(self.height_var.get())
        except ValueError:
            messagebox.showerror("Input Error", "Please enter valid numeric values for weight and height.")
            return

        if weight <= 0 or height <= 0:
            messagebox.showerror("Input Error", "Weight and height must be strictly positive numbers.")
            return

        unit = self.unit_system.get()

        # Compute BMI formula
        if unit == "metric":
            # Height converted from cm to meters
            height_m = height / 100.0
            bmi = weight / (height_m ** 2)
            min_ideal_wt = 18.5 * (height_m ** 2)
            max_ideal_wt = 24.9 * (height_m ** 2)
            wt_unit_str = "kg"
        else:
            # Imperial: 703 * lbs / (in^2)
            bmi = 703 * weight / (height ** 2)
            min_ideal_wt = (18.5 * (height ** 2)) / 703.0
            max_ideal_wt = (24.9 * (height ** 2)) / 703.0
            wt_unit_str = "lbs"

        # Categorization based on standard WHO thresholds
        if bmi < 18.5:
            category = "Underweight"
        elif 18.5 <= bmi <= 24.9:
            category = "Normal weight"
        elif 25.0 <= bmi <= 29.9:
            category = "Overweight"
        else:
            category = "Obese"

        # Save to Database
        if self.db.add_record(user_id, weight, height, unit, round(bmi, 2), category):
            self._update_result_display(bmi, category, min_ideal_wt, max_ideal_wt, wt_unit_str)
            self._refresh_data_views()

    def _update_result_display(self, bmi, category, min_wt, max_wt, unit_str):
        """Renders color-coded BMI badge and ideal weight suggestions."""
        self.bmi_display_lbl.config(text=f"{bmi:.2f}")

        cat_color = self.cat_colors.get(category, "#45475A")
        self.category_badge.config(text=category, bg=cat_color, fg="#11111B" if category in ["Normal weight", "Overweight"] else "white")
        self.ideal_weight_lbl.config(text=f"Target Normal Range: {min_wt:.1f} - {max_wt:.1f} {unit_str}")

    def _refresh_data_views(self):
        """Refreshes both the history treeview and the Matplotlib line graph."""
        user_id = self.selected_user_id.get()
        if user_id == 0:
            return

        records = self.db.get_user_records(user_id)

        # 1. Update History Table View
        for row in self.tree.get_children():
            self.tree.delete(row)

        for r in records:
            rec_id, w, h, u, bmi_val, cat, rec_time = r
            unit_suffix = "kg / cm" if u == "metric" else "lbs / in"
            self.tree.insert("", tk.END, values=(rec_id, rec_time, f"{w} ({unit_suffix.split('/')[0].strip()})", f"{h}", f"{bmi_val:.2f}", cat))

        # 2. Update Matplotlib Chart
        self._plot_trend_chart(records)

    def _plot_trend_chart(self, records):
        """Plots time-series line graph of historical BMI values with healthy range shading."""
        self.ax.clear()

        # Re-apply dark theme styling to subplots
        self.ax.set_facecolor("#181825")
        self.ax.tick_params(colors=self.fg_color, labelsize=9)
        for spine in self.ax.spines.values():
            spine.set_color("#45475A")

        if not records:
            self.ax.text(
                0.5, 0.5, "No BMI entries recorded yet.\nCalculate your first BMI to see trends!",
                color=self.subtext_color, ha="center", va="center", transform=self.ax.transAxes, fontsize=11
            )
            self.canvas.draw()
            return

        # Parse Dates and BMI values
        dates = [datetime.datetime.strptime(r[6], "%Y-%m-%d %H:%M:%S") for r in records]
        bmis = [r[4] for r in records]

        # Draw Normal Weight Target Range Band (18.5 - 24.9)
        self.ax.axhspan(18.5, 24.9, color="#4ADE80", alpha=0.15, label="Normal Range (18.5 - 24.9)")

        # Plot Trend Line
        self.ax.plot(dates, bmis, color=self.accent_color, marker="o", linewidth=2.5, markersize=6, label="BMI Trend")

        # Format Axes
        self.ax.set_title("BMI Progress Over Time", color=self.fg_color, fontsize=12, fontweight="bold", pad=10)
        self.ax.set_ylabel("BMI Value", color=self.fg_color, fontsize=10)
        self.ax.grid(True, linestyle="--", alpha=0.2, color="#A6ADC8")
        
        if len(dates) > 1:
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d\n%H:%M"))
            self.fig.autofmt_xdate(rotation=0, ha="center")

        self.ax.legend(facecolor=self.card_color, edgecolor="#45475A", labelcolor=self.fg_color, loc="upper left", fontsize=8)
        self.fig.tight_layout()
        self.canvas.draw()

    def _delete_selected_record(self):
        """Deletes selected history record from database and refreshes view."""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Selection Required", "Please select a record entry to delete.")
            return

        item_values = self.tree.item(selected[0], "values")
        rec_id = item_values[0]

        if messagebox.askyesno("Confirm Delete", "Are you sure you want to remove this record?"):
            if self.db.delete_record(rec_id):
                self._refresh_data_views()


def main():
    root = tk.Tk()
    app = BMICalculatorApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()