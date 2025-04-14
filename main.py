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
        label["text"] = seconds_to_str(TRACKED_APPS[app])

# GUI
root = ctk.CTk()
root.title("App Usage Tracker")
root.geometry("300x200")

app_labels = {}

ctk.CTkLabel(root, text="Tracked App Usage", font=("Helvetica", 14, "bold")).pack(pady=10)

for app in TRACKED_APPS:
    frame = ctk.CTkFrame(root)
    frame.pack()
    ctk.CTkLabel(frame, text=app, width=15, anchor="w").pack(side="left")
    label = ctk.CTkLabel(frame, text="0m 0s", width=10)
    label.pack(side="left")
    app_labels[app] = label

# Summary Frame
summary_frame = ctk.CTkFrame(root)
summary_frame.pack(pady=10)

def update_summary():
    daily = get_total_usage("daily")
    weekly = get_total_usage("weekly")
    monthly = get_total_usage("monthly")

    summary_label["text"] = (
        f"🕒 Today: {daily}\n"
        f"📆 This Week: {weekly}\n"
        f"📅 This Month: {monthly}"
    )

summary_label = ctk.CTkLabel(summary_frame, text="", justify="left", font=("Helvetica", 10))
summary_label.pack()

# Update summary every 30 seconds
def auto_update_summary():
    while True:
        update_summary()
        time.sleep(30)

threading.Thread(target=auto_update_summary, daemon=True).start()
threading.Thread(target=update_times, daemon=True).start()

def on_exit():
    save_usage()  # store current session
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_exit)

root.mainloop()