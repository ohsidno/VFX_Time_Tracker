import tkinter as tk
from tkinter import ttk, messagebox
from tkcalendar import Calendar
import requests
from datetime import datetime
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import sv_ttk  

# Server Config
SERVER_URL = "http://127.0.0.1:5000"
MODERN_COLORS = ['#5B9BD5', '#ED7D31', '#A5A5A5', '#FFC000', '#4472C4', '#70AD47', '#255E91', '#9E480E']

class TimeTrackerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VFX Time Tracker Client")
        self.root.geometry("1400x850")
        self.user_info = None

        # Theme
        sv_ttk.set_theme("light") 
        self.style = ttk.Style()
        self.style.configure("TNotebook.Tab", font=('Helvetica', 12, 'bold'), padding=[10, 5])
        self.style.configure("Treeview.Heading", font=('Helvetica', 12, 'bold'))
        self.style.configure("Treeview", font=('Helvetica', 11), rowheight=28)
        self.style.configure("TLabel", font=('Helvetica', 12))
        self.style.configure("TButton", font=('Helvetica', 12, 'bold'))
        self.style.configure("Header.TLabel", font=('Helvetica', 20, 'bold'))
        self.style.configure("Summary.TLabel", font=('Helvetica', 14, 'bold'))

        self.create_login_screen()

    def create_login_screen(self):
        self.clear_screen()
        
        login_frame = ttk.Frame(self.root, padding="40")
        login_frame.pack(expand=True)

        ttk.Label(login_frame, text="VFX Time Tracker", style="Header.TLabel").pack(pady=20)

        ttk.Label(login_frame, text="Username").pack(pady=(10,2))
        self.username_entry = ttk.Entry(login_frame, width=40, font=('Helvetica', 12))
        self.username_entry.pack()

        ttk.Label(login_frame, text="Password").pack(pady=(10,2))
        self.password_entry = ttk.Entry(login_frame, show="*", width=40, font=('Helvetica', 12))
        self.password_entry.pack()

        button_frame = ttk.Frame(login_frame)
        button_frame.pack(pady=30)

        ttk.Button(button_frame, text="Login", command=self.login, style="Accent.TButton").pack(side=tk.LEFT, padx=10, ipady=5)
        ttk.Button(button_frame, text="Register", command=self.create_register_screen).pack(side=tk.LEFT, padx=10, ipady=5)

    def create_register_screen(self):
        register_window = tk.Toplevel(self.root)
        register_window.title("Register New User")
        register_window.geometry("400x350")

        register_frame = ttk.Frame(register_window, padding="20")
        register_frame.pack(expand=True, fill=tk.BOTH)

        ttk.Label(register_frame, text="Create New Account", style="Header.TLabel").pack(pady=10)
        ttk.Label(register_frame, text="Username").pack(pady=5)
        reg_username = ttk.Entry(register_frame, width=40)
        reg_username.pack()
        ttk.Label(register_frame, text="Password").pack(pady=5)
        reg_password = ttk.Entry(register_frame, show="*", width=40)
        reg_password.pack()
        ttk.Label(register_frame, text="Confirm Password").pack(pady=5)
        reg_confirm_password = ttk.Entry(register_frame, show="*", width=40)
        reg_confirm_password.pack()

        def submit_registration():
            username, password, confirm = reg_username.get(), reg_password.get(), reg_confirm_password.get()
            if not username or not password:
                messagebox.showerror("Error", "All fields are required.", parent=register_window)
                return
            if password != confirm:
                messagebox.showerror("Error", "Passwords do not match.", parent=register_window)
                return
            try:
                response = requests.post(f"{SERVER_URL}/api/register", json={"username": username, "password": password})
                if response.status_code == 201:
                    messagebox.showinfo("Success", "User created successfully!", parent=register_window)
                    register_window.destroy()
                else:
                    messagebox.showerror("Registration Failed", response.json().get("message"), parent=register_window)
            except requests.exceptions.RequestException as e:
                messagebox.showerror("Connection Error", f"Could not connect: {e}", parent=register_window)

        ttk.Button(register_frame, text="Register", command=submit_registration, style="Accent.TButton").pack(pady=20, ipady=5)

    def login(self):
        username, password = self.username_entry.get(), self.password_entry.get()
        if not username or not password:
            messagebox.showerror("Error", "Username and password are required.")
            return
        try:
            response = requests.post(f"{SERVER_URL}/api/login", json={"username": username, "password": password})
            if response.status_code == 200:
                self.user_info = response.json().get("user")
                self.create_main_screen()
            else:
                messagebox.showerror("Login Failed", response.json().get("message"))
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}")

    def create_main_screen(self):
        self.clear_screen()
        
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        left_panel = ttk.Frame(main_frame, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        ttk.Label(left_panel, text=f"Welcome, {self.user_info['username']}", style="Header.TLabel").pack(pady=10)
        self.cal = Calendar(left_panel, selectmode='day', date_pattern='yyyy-mm-dd', font="Helvetica 12")
        self.cal.pack(pady=10, fill="x")

        right_panel = ttk.Notebook(main_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.logs_tab = ttk.Frame(right_panel, padding="10")
        right_panel.add(self.logs_tab, text='Daily Logs')
        self.create_logs_tab_content()

        self.reports_tab = ttk.Frame(right_panel, padding="10")
        right_panel.add(self.reports_tab, text='My Reports')
        self.create_reports_tab_content()
        
        self.cal.bind("<<CalendarSelected>>", self.on_date_select)
        self.on_date_select(None)

    def create_logs_tab_content(self):
        top_frame = ttk.Frame(self.logs_tab)
        top_frame.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(top_frame, text="Sessions", padding="10")
        log_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        columns = ("id", "app", "task", "session", "start", "end", "duration")
        self.tree = ttk.Treeview(log_frame, columns=columns, show='headings')
        for col in columns: self.tree.heading(col, text=col.capitalize())
        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("duration", width=100, anchor=tk.E)
        self.tree.pack(fill=tk.BOTH, expand=True)

        summary_container = ttk.Frame(top_frame)
        summary_container.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        summary_frame = ttk.LabelFrame(summary_container, text="Daily Summary", padding="10")
        summary_frame.pack(fill=tk.BOTH, expand=True)
        self.summary_text = tk.Text(summary_frame, width=40, font=('Courier', 11), state='disabled', relief='flat', background=self.style.lookup('TFrame', 'background'))
        self.summary_text.pack(fill=tk.BOTH, expand=True)

        bottom_frame = ttk.Frame(self.logs_tab)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        self.total_time_label = ttk.Label(bottom_frame, text="Total time: 0.00 minutes")
        self.total_time_label.pack(side=tk.LEFT)
        ttk.Button(bottom_frame, text="Launch Manager Dashboard", command=self.launch_dashboard).pack(side=tk.RIGHT)

    def create_reports_tab_content(self):
        ttk.Label(self.reports_tab, text="Performance on Selected Day", style="Header.TLabel").pack(pady=10)
        charts_frame = ttk.Frame(self.reports_tab)
        charts_frame.pack(fill=tk.BOTH, expand=True)

        self.task_fig = Figure(figsize=(5, 4), dpi=100)
        self.task_ax = self.task_fig.add_subplot(111)
        self.task_canvas = FigureCanvasTkAgg(self.task_fig, master=charts_frame)
        self.task_canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        self.app_fig = Figure(figsize=(5, 4), dpi=100)
        self.app_ax = self.app_fig.add_subplot(111)
        self.app_canvas = FigureCanvasTkAgg(self.app_fig, master=charts_frame)
        self.app_canvas.get_tk_widget().pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

    def on_date_select(self, event):
        self.fetch_and_update_all(self.cal.get_date())

    def fetch_and_update_all(self, date):
        try:
            params = {"user_id": self.user_info['id'], "date": date}
            response = requests.get(f"{SERVER_URL}/api/get_logs", params=params)
            if response.status_code == 200:
                logs = response.json().get("logs", [])
                self.update_logs_tab(logs)
                self.update_reports_tab(logs)
            else:
                messagebox.showerror("Error", "Failed to fetch logs.")
        except requests.exceptions.RequestException as e:
            messagebox.showerror("Connection Error", f"Could not connect: {e}")

    def update_logs_tab(self, logs):
        for i in self.tree.get_children(): self.tree.delete(i)
        total_duration = sum(log.get('duration', 0) for log in logs)
        for log in logs:
            self.tree.insert("", "end", values=(
                log['id'], log['app_name'], log.get('task_name', 'N/A'),
                log['session_name'], 
                datetime.fromisoformat(log['start_time']).strftime('%H:%M:%S'),
                datetime.fromisoformat(log['end_time']).strftime('%H:%M:%S'),
                f"{log.get('duration', 0):.2f}"
            ))
        self.total_time_label.config(text=f"Total time worked: {total_duration:.2f} minutes")
        self.update_summary(logs)

    def update_summary(self, logs):
        self.summary_text.config(state='normal')
        self.summary_text.delete(1.0, tk.END)
        if not logs:
            self.summary_text.insert(tk.END, "No sessions for this day.")
        else:
            df = pd.DataFrame(logs)
            self.summary_text.insert(tk.END, "--- Time by Task ---\n")
            task_summary = df.groupby('task_name')['duration'].sum()
            for task, dur in task_summary.items(): self.summary_text.insert(tk.END, f"{task or 'N/A':<20} {dur:>7.2f} min\n")
            
            self.summary_text.insert(tk.END, "\n--- Time by App ---\n")
            app_summary = df.groupby('app_name')['duration'].sum()
            for app, dur in app_summary.items(): self.summary_text.insert(tk.END, f"{app:<20} {dur:>7.2f} min\n")
        self.summary_text.config(state='disabled')

    def update_reports_tab(self, logs):
        for ax in [self.task_ax, self.app_ax]: ax.clear()
        
        if not logs:
            for ax in [self.task_ax, self.app_ax]:
                ax.text(0.5, 0.5, 'No data for this day', ha='center', va='center')
        else:
            df = pd.DataFrame(logs)
            
            # Chart
            task_summary = df.groupby('task_name')['duration'].sum()
            self.task_ax.pie(task_summary, labels=task_summary.index, autopct='%1.1f%%', startangle=90, colors=MODERN_COLORS, wedgeprops=dict(width=0.4))
            self.task_ax.axis('equal')
            self.task_ax.set_title("Task Breakdown")

            # Bar Chart
            app_summary = df.groupby('app_name')['duration'].sum()
            self.app_ax.bar(app_summary.index, app_summary.values, color=MODERN_COLORS)
            self.app_ax.set_ylabel('Duration (minutes)')
            self.app_ax.set_title("Application Usage")
            self.app_ax.tick_params(axis='x', rotation=45)

        self.task_fig.tight_layout()
        self.app_fig.tight_layout()
        self.task_canvas.draw()
        self.app_canvas.draw()

    def launch_dashboard(self):
        import webbrowser
        webbrowser.open(f"{SERVER_URL}/dashboard")

    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == "__main__":
    plt.style.use('seaborn-v0_8-whitegrid')
    root = tk.Tk()
    app = TimeTrackerApp(root)
    root.mainloop()

