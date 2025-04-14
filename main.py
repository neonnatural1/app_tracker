import psutil
import time
import threading
import json
import os
from datetime import datetime
from datetime import timedelta
import customtkinter as ctk
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
    total = {}

    for date_str, apps in usage_log.items():
        date = datetime.strptime(date_str, "%Y-%m-%d")
        delta = (now - date).days

        if (mode == "daily" and delta == 0) or \
           (mode == "weekly" and delta <= 6) or \
           (mode == "monthly" and delta <= 30):

            for app, secs in apps.items():
                total[app] = total.get(app, 0) + secs

    return ", ".join(f"{app}: {seconds_to_str(secs)}" for app, secs in total.items())


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

app_labels = {}

# Title
ctk.CTkLabel(
    root, text="Tracked App Usage",
    font=("Segoe UI", 20, "bold"),
    text_color="#ffffff"
).pack(pady=(20, 10))

# Tracked app list
for app in TRACKED_APPS:
    frame = ctk.CTkFrame(root, fg_color="transparent")
    frame.pack(pady=5, padx=20, fill="x")

    name_label = ctk.CTkLabel(frame, text=app, width=200, anchor="w", font=("Segoe UI", 12))
    name_label.pack(side="left", padx=(10, 0))

    label = ctk.CTkLabel(frame, text="0s", width=100, anchor="e", font=("Segoe UI", 12))
    label.pack(side="right", padx=(0, 10))

    app_labels[app] = label

# Summary Frame
summary_frame = ctk.CTkFrame(root, fg_color="transparent")
summary_frame.pack(pady=(30, 10), padx=20, fill="x")

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
        daily = get_total_usage("daily")
        weekly = get_total_usage("weekly")
        monthly = get_total_usage("monthly")

        summary_label.configure(
            text=(
                f"🕒 Today: {daily}\n"
                f"📆 This Week: {weekly}\n"
                f"📅 This Month: {monthly}"
            )
        )
        time.sleep(1)

def on_exit():
    save_usage()  # store current session
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_exit)

threading.Thread(target=update_summary, daemon=True).start()
threading.Thread(target=update_times, daemon=True).start()

root.mainloop()