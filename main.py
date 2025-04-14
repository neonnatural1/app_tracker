import psutil
import time
import threading
import json
import os
from datetime import datetime
from datetime import timedelta
import customtkinter as ctk
import matplotlib.pyplot as plt
ctk.set_appearance_mode("Dark")        # or "Light"
ctk.set_default_color_theme("blue")    # or "green", "dark-blue"

# Apps to track (Windows .exe names)
TRACKED_APPS = {
    "opera.exe": 0,
    "discord.exe": 0,
    "code.exe": 0,  # VS Code
}

LOG_FILE = "usage_data.json"

# Load existing logs
if os.path.exists(LOG_FILE):
    with open(LOG_FILE, "r") as f:
        usage_log = json.load(f)
else:
    usage_log = {}

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def get_total_usage(mode):
    now = datetime.now()
    totals = {}

    for date_str, apps in usage_log.items():
        try:
            date = datetime.strptime(date_str, "%Y-%m-%d")
        except:
            continue

        delta = (now - date).days

        if (mode == "daily" and delta == 0) or \
           (mode == "weekly" and delta <= 6) or \
           (mode == "monthly" and delta <= 30):

            for app, secs in apps.items():
                totals[app] = totals.get(app, 0) + secs

    if not totals:
        return "  • No data yet"

    return "\n" + "\n".join(f"  • {app}: {seconds_to_str(secs)}" for app, secs in totals.items())


def save_usage():
    today = get_today()
    if today not in usage_log:
        usage_log[today] = {}

    running = [p.name().lower() for p in psutil.process_iter()]

    for app in TRACKED_APPS:
        if app in running:
            # Add just 60 seconds per minute if running
            usage_log[today][app] = usage_log[today].get(app, 0) + 60

    with open(LOG_FILE, "w") as f:
        json.dump(usage_log, f, indent=2)

REFRESH_RATE = 1  # seconds

def update_times():
    while True:
        running = [p.name().lower() for p in psutil.process_iter()]
        for app in TRACKED_APPS:
            if app in running:
                TRACKED_APPS[app] += REFRESH_RATE
        time.sleep(REFRESH_RATE)
        if app_labels:
            update_gui()

        if time.time() % 60 < REFRESH_RATE:  # once per minute
            save_usage()

def seconds_to_str(seconds):
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    mins = (seconds % 3600) // 60
    secs = seconds % 60

    if days > 0:
        return f"{days}d {hours}h {mins}m"
    elif hours > 0:
        return f"{hours}h {mins}m"
    elif mins > 0:
        return f"{mins}m {secs}s"
    else:
        return f"{secs}s"

def update_gui():
    for app, label in app_labels.items():
        label.configure(text=seconds_to_str(TRACKED_APPS[app]))

# GUI Setup
root = ctk.CTk()
root.title("App Usage Tracker")
root.geometry("420x480")

# Title
ctk.CTkLabel(
    root, text="Tracked App Usage",
    font=("Segoe UI", 20, "bold"),
    text_color="#ffffff"
).pack(pady=(20, 10))

apps_frame = ctk.CTkFrame(root, fg_color="transparent")
apps_frame.pack(pady=(10, 0))

app_labels = {}

# Tracked app list
for app in TRACKED_APPS:
    frame = ctk.CTkFrame(apps_frame, fg_color="transparent")
    frame.pack(pady=5, padx=20, fill="x")

    name_label = ctk.CTkLabel(frame, text=app, width=200, anchor="w", font=("Segoe UI", 12))
    name_label.pack(side="left", padx=(10, 0))

    label = ctk.CTkLabel(frame, text="0s", width=100, anchor="e", font=("Segoe UI", 12))
    label.pack(side="right", padx=(0, 10))

    app_labels[app] = label

# Summary Frame
summary_frame = ctk.CTkFrame(root, fg_color="transparent")
summary_frame.pack(pady=(30, 10), padx=20, fill="x")

# Collapsible section frames
summary_data = {
    "daily": {"title": "🕒 Today", "expanded": False},
    "weekly": {"title": "📆 This Week", "expanded": False},
    "monthly": {"title": "📅 This Month", "expanded": False},
}

summary_widgets = {}

def toggle_section(section_key):
    data = summary_data[section_key]
    data["expanded"] = not data["expanded"]

    btn = summary_widgets[section_key]["button"]
    lbl = summary_widgets[section_key]["label"]

    if data["expanded"]:
        btn.configure(text=f"{data['title']} ▲")
        lbl.pack()
    else:
        btn.configure(text=f"{data['title']} ▼")
        lbl.pack_forget()


for key, data in summary_data.items():
    # Frame per section
    section_frame = ctk.CTkFrame(summary_frame, fg_color="transparent")
    section_frame.pack(fill="x", pady=2)

    # Toggle button
    def make_toggle(k):
        return lambda: toggle_section(k)

    btn = ctk.CTkButton(section_frame, text=f"{data['title']} ▼", width=200, command=make_toggle(key))
    btn.pack()

    # Label for that section (initially hidden)
    lbl = ctk.CTkLabel(section_frame, text="", justify="left", anchor="w", font=("Segoe UI", 12))
    lbl.pack(pady=(0, 5))
    lbl.pack_forget()

    summary_widgets[key] = {"button": btn, "label": lbl}

def open_usage_graph(period="weekly"):
    selected_app = app_selector.get()
    if not selected_app:
        return

    now = datetime.now()
    days = 7 if period == "weekly" else 30

    labels = []
    values = []

    for i in range(days - 1, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        labels.append(day[5:])  # Show MM-DD

        day_usage = usage_log.get(day, {}).get(selected_app, 0)
        values.append(round(day_usage / 3600, 2))  # convert to hours

    plt.figure(figsize=(9, 4))
    plt.bar(labels, values)
    plt.title(f"{period.capitalize()} Usage for {selected_app}")
    plt.ylabel("Hours")
    plt.xlabel("Day")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# App selection dropdown
app_selector = ctk.CTkOptionMenu(
    root,
    values=list(TRACKED_APPS.keys()),
    width=200
)
app_selector.pack(pady=(10, 5))
app_selector.set(list(TRACKED_APPS.keys())[0])  # default selection

# Buttons
button_frame = ctk.CTkFrame(root, fg_color="transparent")
button_frame.pack(pady=10)

ctk.CTkButton(button_frame, text="📆 Weekly Graph", command=lambda: open_usage_graph("weekly")).pack(side="left", padx=10)
ctk.CTkButton(button_frame, text="📅 Monthly Graph", command=lambda: open_usage_graph("monthly")).pack(side="left", padx=10)

# App Manager Frame
manage_frame = ctk.CTkFrame(root, fg_color="transparent")
manage_frame.pack(pady=(10, 10))

entry = ctk.CTkEntry(manage_frame, placeholder_text="Enter app name (e.g., notepad.exe)", width=250)
entry.grid(row=0, column=0, padx=5)

def add_app():
    new_app = entry.get().strip().lower()
    if not new_app or new_app in TRACKED_APPS:
        return
    TRACKED_APPS[new_app] = 0

    # Create GUI row
    frame = ctk.CTkFrame(apps_frame, fg_color="transparent")
    frame.pack(pady=5, padx=20, fill="x")

    name_label = ctk.CTkLabel(frame, text=new_app, width=200, anchor="w", font=("Segoe UI", 12))
    name_label.pack(side="left", padx=(10, 0))

    label = ctk.CTkLabel(frame, text="0s", width=100, anchor="e", font=("Segoe UI", 12))
    label.pack(side="right", padx=(0, 10))

    app_labels[new_app] = label

    # Update dropdown
    app_selector.configure(values=list(TRACKED_APPS.keys()))
    entry.delete(0, 'end')

def remove_app():
    target = entry.get().strip().lower()
    if target not in TRACKED_APPS:
        return
    del TRACKED_APPS[target]
    label = app_labels.pop(target, None)
    if label:
        label.master.destroy()  # remove GUI row

    # Update dropdown
    app_selector.configure(values=list(TRACKED_APPS.keys()))
    entry.delete(0, 'end')

ctk.CTkButton(manage_frame, text="Add", command=add_app).grid(row=0, column=1, padx=5)
ctk.CTkButton(manage_frame, text="Remove", command=remove_app).grid(row=0, column=2, padx=5)

summary_label = ctk.CTkLabel(
    summary_frame,
    text="",
    justify="left",
    font=("Segoe UI", 12),
    anchor="w",
)
summary_label.pack()

# Update summary every second
def update_summary():
    while True:
        for key in summary_data:
            if summary_data[key]["expanded"]:
                summary_widgets[key]["label"].configure(text=get_total_usage(key))
        time.sleep(1)

def on_exit():
    save_usage()  # store current session
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_exit)

threading.Thread(target=update_summary, daemon=True).start()
threading.Thread(target=update_times, daemon=True).start()

root.mainloop()