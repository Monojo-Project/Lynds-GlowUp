#!/usr/bin/env python3
#
# Lynds Glow Up - Monojo Project
# Licencia: MIT
#

import tkinter as tk
from tkinter import messagebox
import tkinter.font as tkfont
import subprocess
import os
import sys
import json
import time
import datetime
import signal
import urllib.request
from datetime import date, timedelta

PYTHON_BIN = sys.executable
SCRIPT_PATH = os.path.abspath(sys.argv[0])
BASE_CMD = [PYTHON_BIN, SCRIPT_PATH]
CONFIG_DIR = os.path.expanduser("~/.config/lynds-glowup")


def enforce_single_instance():
    os.makedirs(CONFIG_DIR, exist_ok=True)
    pid_file = os.path.join(CONFIG_DIR, "app.pid")
    if os.path.exists(pid_file):
        try:
            with open(pid_file, "r") as f:
                old_pid = int(f.read().strip())
            os.kill(old_pid, signal.SIGTERM)
            time.sleep(0.2)
        except (ValueError, OSError):
            pass
    with open(pid_file, "w") as f:
        f.write(str(os.getpid()))


def enviar_notificacion(titulo, mensaje, icono="checkbox"):
    try:
        subprocess.run(["notify-send", "--app-name=Lynds Glow Up", f"-i", icono, "-u", "normal", titulo, mensaje])
    except Exception:
        pass


def crear_autostart():
    autostart_dir = os.path.expanduser("~/.config/autostart")
    os.makedirs(autostart_dir, exist_ok=True)
    desktop_path = os.path.join(autostart_dir, "lynds-glowup.desktop")
    exec_cmd = f"{PYTHON_BIN} {SCRIPT_PATH} --relative"
    desktop_content = f"""[Desktop Entry]
Type=Application
Exec={exec_cmd}
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Lynds Glow Up Daemon
Comment=Gestor principal y notificaciones del ecosistema Monojo
Icon=utilities-terminal
"""
    with open(desktop_path, "w") as f:
        f.write(desktop_content)


class LyndsGlowUp:
    def __init__(self, root, close_callback):
        self.root = root
        self.close_callback = close_callback
        self.root.title("Lynds Glow Up")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#0A0A0A")
        self.root.bind("<Escape>", lambda e: self.close_callback())

        self.bg_color = "#0A0A0A"
        self.card_color = "#141414"
        self.accent_color = "#00FF66"
        self.text_color = "#FFFFFF"
        self.muted_green = "#005522"
        self.danger_color = "#FF3333"
        self.dim_color = "#333333"
        self.done_color = "#555555"
        self.warning_color = "#FFA500"

        self.data_file = os.path.join(CONFIG_DIR, "app_state.json")
        self.data = {
            "challenge_active": False,
            "target_days": 0,
            "difficulty": "Fácil",
            "start_date": "",
            "last_date": "",
            "daily_locked": False,
            "objectives": [],
            "history": {},
            "fixed_objectives": []
        }

        self.today_str = date.today().isoformat()
        self.load_data()
        self.check_new_day()
        self.quote_of_the_day = self.fetch_daily_quote()
        self.setup_base_ui()
        self.render_view()
        self.update_live_clock()

    def fetch_daily_quote(self):
        url = "https://raw.githubusercontent.com/Monojo-Project/Lynds-GlowUp/main/DAYLY"
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as response:
                return response.read().decode('utf-8').strip()
        except Exception:
            return "La constancia es la base del Monojo.\n- Maestro Casata"

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "r") as file:
                    loaded_data = json.load(file)
                    for key in self.data.keys():
                        if key in loaded_data:
                            self.data[key] = loaded_data[key]
            except Exception:
                pass

    def save_data(self):
        if self.data["objectives"]:
            total = len(self.data["objectives"])
            completed = sum(1 for obj in self.data["objectives"] if obj["completed"])
            self.data["history"][self.today_str] = {
                "score": (completed / total) * 100,
                "completed": completed,
                "total": total
            }
        with open(self.data_file, "w") as file:
            json.dump(self.data, file, indent=4)

    def check_new_day(self):
        if self.data["challenge_active"] and self.data["last_date"] != self.today_str:
            self.data["objectives"] = [{"text": t, "completed": False} for t in self.data.get("fixed_objectives", [])]
            self.data["daily_locked"] = False
            self.data["last_date"] = self.today_str
            self.save_data()

    def setup_base_ui(self):
        top_bar = tk.Frame(self.root, bg=self.bg_color)
        top_bar.pack(fill=tk.X, padx=30, pady=20)

        title = tk.Label(top_bar, text="⚡ LYNDS GLOW UP ⚡", font=("Courier New", 22, "bold"), fg=self.accent_color, bg=self.bg_color)
        title.pack(side=tk.LEFT)

        exit_btn = tk.Button(top_bar, text="[X] SALIR AL CORE (ESC)", font=("Courier New", 12, "bold"), fg=self.bg_color, bg=self.danger_color, bd=0, padx=10, command=self.close_callback)
        exit_btn.pack(side=tk.RIGHT)

        self.main_container = tk.Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=50, pady=10)

    def update_live_clock(self):
        if hasattr(self, "clock_label") and self.clock_label.winfo_exists():
            now_str = datetime.datetime.now().strftime("%H:%M:%S")
            self.clock_label.config(text=f"SYS_TIME: {now_str}")
        self.root.after(1000, self.update_live_clock)

    def calculate_metrics(self):
        history = self.data.get("history", {})
        start_date_str = self.data.get("start_date")
        if not start_date_str or not history:
            return {"streak": 0, "efficiency": 0, "rank": "Cachorro del Monojo", "completed_days": 0}

        completed_days = sum(1 for d in history.values() if (d.get("score") if isinstance(d, dict) else d) == 100)
        total_scores = [d.get("score", 0) if isinstance(d, dict) else d for d in history.values()]
        efficiency = sum(total_scores) / len(total_scores) if total_scores else 0
        streak = 0
        check_date = date.today()
        today_str = check_date.isoformat()

        if today_str not in history or history[today_str].get("score", 0) != 100:
            check_date -= timedelta(days=1)
        while True:
            d_str = check_date.isoformat()
            if d_str in history and history[d_str].get("score", 0) == 100:
                streak += 1
                check_date -= timedelta(days=1)
            else:
                break

        if completed_days <= 2:
            rank = "Cachorro del Monojo 🐾"
        elif completed_days <= 7:
            rank = "Script Kiddie 💻"
        elif completed_days <= 15:
            rank = "SysAdmin Local 🛠️"
        elif completed_days <= 29:
            rank = "Kernel Developer 🐧"
        else:
            rank = "Maestro Casata Approved 👑"
        return {"streak": streak, "efficiency": efficiency, "rank": rank, "completed_days": completed_days}

    def render_view(self):
        for widget in self.main_container.winfo_children():
            widget.destroy()
        if not self.data["challenge_active"]:
            self.build_setup_view()
        elif not self.data["daily_locked"]:
            self.build_planning_view()
        else:
            self.build_tracking_view()

    def build_setup_view(self):
        container = tk.Frame(self.main_container, bg=self.bg_color)
        container.place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(container, text="INICIAR PROTOCOLO GLOW UP", font=("Courier New", 24, "bold"), fg=self.accent_color, bg=self.bg_color).pack(pady=(0, 20))
        tk.Label(container, text="Duración del reto (Días):", font=("Courier New", 14), fg=self.text_color, bg=self.bg_color).pack(pady=(0, 10))
        self.days_var = tk.StringVar(value="30")
        tk.Entry(container, textvariable=self.days_var, font=("Courier New", 20, "bold"), bg=self.card_color, fg=self.accent_color, insertbackground=self.accent_color, bd=1, relief=tk.SOLID, justify="center", width=5).pack(pady=5)
        tk.Label(container, text="Selecciona el nivel de compromiso:", font=("Courier New", 14), fg=self.text_color, bg=self.bg_color).pack(pady=(20, 10))
        diff_frame = tk.Frame(container, bg=self.bg_color)
        diff_frame.pack(pady=10)
        self.diff_var = tk.StringVar(value="Fácil")
        dificultades = [
            ("FÁCIL", "Fácil", "#00FF66", "Puedes abortar la misión completa si las cosas se complican."),
            ("DURO", "Duro", "#FF3333", "Sin escapatoria. El botón de abortar desaparecerá.")
        ]
        for text, mode, color, desc in dificultades:
            rb = tk.Radiobutton(diff_frame, text=text, variable=self.diff_var, value=mode, font=("Courier New", 14, "bold"), bg=self.bg_color, fg=color, selectcolor=self.card_color, activebackground=self.bg_color, activeforeground=color)
            rb.pack(anchor="w")
            tk.Label(diff_frame, text=desc, font=("Courier New", 10, "italic"), fg=self.text_color, bg=self.bg_color).pack(anchor="w", padx=30, pady=(0, 10))
        tk.Button(container, text="CONFIRMAR PARÁMETROS", font=("Courier New", 16, "bold"), bg=self.accent_color, fg=self.bg_color, bd=0, command=self.start_challenge, padx=20, pady=10).pack(pady=30)

    def start_challenge(self):
        try:
            days = int(self.days_var.get())
            if days <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Introduce un número válido de días.")
            return
        fixed = self.data.get("fixed_objectives") or []
        self.data.update({
            "challenge_active": True,
            "target_days": days,
            "difficulty": self.diff_var.get(),
            "start_date": self.today_str,
            "last_date": self.today_str,
            "objectives": [{"text": t, "completed": False} for t in fixed],
            "history": {}
        })
        self.save_data()
        self.render_view()

    def build_planning_view(self):
        container = tk.Frame(self.main_container, bg=self.bg_color)
        container.place(relx=0.5, rely=0.5, anchor="center", width=800, height=600)

        tk.Label(container, text="PLANIFICACIÓN DEL DÍA", font=("Courier New", 18), fg=self.text_color, bg=self.bg_color).pack(pady=(0, 5))
        tk.Label(container, text="Vence a tus demonios (Sugerencias a evitar): Soberbia, Avaricia, Lujuria, Ira, Gula, Envidia, Pereza", font=("Courier New", 10, "italic"), fg=self.warning_color, bg=self.bg_color).pack(pady=(0, 15))

        input_frame = tk.Frame(container, bg=self.bg_color)
        input_frame.pack(fill=tk.X, pady=10)
        self.entry_var = tk.StringVar()
        entry = tk.Entry(input_frame, textvariable=self.entry_var, font=("Courier New", 16), bg=self.card_color, fg=self.accent_color, insertbackground=self.accent_color, bd=1, relief=tk.SOLID)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=10, padx=(0, 10))
        entry.bind("<Return>", lambda e: self.add_objective_logic())
        entry.focus()
        tk.Button(input_frame, text="AÑADIR", font=("Courier New", 14, "bold"), bg=self.bg_color, fg=self.accent_color, bd=1, relief=tk.SOLID, command=self.add_objective_logic).pack(side=tk.RIGHT, ipadx=20, ipady=5)

        canvas_frame = tk.Frame(container, bg=self.card_color, bd=1, relief=tk.SOLID)
        canvas_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        self.canvas = tk.Canvas(canvas_frame, bg=self.card_color, highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=self.canvas.yview)
        self.plan_list_frame = tk.Frame(self.canvas, bg=self.card_color)

        self.plan_list_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        self.canvas_window = self.canvas.create_window((0, 0), window=self.plan_list_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)

        def on_canvas_configure(event):
            self.canvas.itemconfig(self.canvas_window, width=event.width)
        self.canvas.bind('<Configure>', on_canvas_configure)

        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.refresh_planning_list()
        tk.Button(container, text="▶ BLOQUEAR Y COMENZAR DÍA", font=("Courier New", 16, "bold"), bg=self.accent_color, fg=self.bg_color, bd=0, command=self.lock_day).pack(fill=tk.X, ipady=10, pady=(10, 0))

    def add_objective_logic(self):
        text = self.entry_var.get().strip()
        if text:
            if not any(obj["text"] == text for obj in self.data["objectives"]):
                self.data["objectives"].append({"text": text, "completed": False})
            if text not in self.data.get("fixed_objectives", []):
                self.data.setdefault("fixed_objectives", []).append(text)
            self.entry_var.set("")
            self.save_data()
            self.refresh_planning_list()

    def refresh_planning_list(self):
        for w in self.plan_list_frame.winfo_children():
            w.destroy()
        for idx, obj in enumerate(self.data["objectives"]):
            f = tk.Frame(self.plan_list_frame, bg=self.card_color)
            f.pack(fill=tk.X, padx=10, pady=5)
            tk.Label(f, text=f"> {obj['text']}", font=("Courier New", 14), fg=self.text_color, bg=self.card_color).pack(side=tk.LEFT)
            tk.Button(f, text="[X]", fg=self.danger_color, bg=self.card_color, bd=0, command=lambda i=idx: self.delete_objective(i)).pack(side=tk.RIGHT)

    def delete_objective(self, index):
        text = self.data["objectives"][index]["text"]
        del self.data["objectives"][index]
        if text in self.data.get("fixed_objectives", []):
            self.data["fixed_objectives"].remove(text)
        self.save_data()
        self.refresh_planning_list()

    def lock_day(self):
        if not self.data["objectives"]:
            messagebox.showwarning("Aviso", "Añade al menos un objetivo para comenzar.")
            return
        self.data["daily_locked"] = True
        self.save_data()
        crear_autostart()
        self.render_view()

    def build_tracking_view(self):
        metrics = self.calculate_metrics()

        # Panel Izquierdo
        left_panel = tk.Frame(self.main_container, bg=self.bg_color)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 20))

        # 1. Cabecera (Se ancla arriba)
        tk.Label(left_panel, text=f"HOY: {self.today_str} | ENFOQUE: {self.data['difficulty'].upper()}", font=("Courier New", 16, "bold"), fg=self.accent_color, bg=self.bg_color, anchor="w").pack(side=tk.TOP, fill=tk.X, pady=(0, 10))

        # 2. Contenedor de la gráfica y días (Se ancla ABAJO para que nunca desaparezca ni se deforme)
        table_container = tk.Frame(left_panel, bg=self.card_color, bd=1, relief=tk.SOLID)
        table_container.pack(side=tk.BOTTOM, fill=tk.X)

        tk.Label(table_container, text=f"PROGRESO GLOBAL Y DIÁGRA DE ACTIVIDAD", font=("Courier New", 12, "bold"), fg=self.text_color, bg=self.card_color).pack(anchor="w", padx=10, pady=5)
        self.build_stonks_chart(table_container)

        grid_frame = tk.Frame(table_container, bg=self.card_color)
        grid_frame.pack(padx=10, pady=10, anchor="w")
        self.history_detail_label = tk.Label(table_container, text="Haz clic en un nodo de cuadrícula para ver detalles históricos.", font=("Courier New", 10, "italic"), fg=self.accent_color, bg=self.card_color)
        self.history_detail_label.pack(anchor="w", padx=10, pady=(0, 10))
        self.build_progress_table(grid_frame)

        # 3. Contenedor de Checkboxes con SCROLL (Ocupa el espacio intermedio que sobra)
        tasks_outer_frame = tk.Frame(left_panel, bg=self.card_color, bd=1, relief=tk.SOLID)
        tasks_outer_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, pady=(0, 15))

        tasks_canvas = tk.Canvas(tasks_outer_frame, bg=self.card_color, highlightthickness=0)
        tasks_scrollbar = tk.Scrollbar(tasks_outer_frame, orient="vertical", command=tasks_canvas.yview)
        tasks_inner_frame = tk.Frame(tasks_canvas, bg=self.card_color)

        tasks_inner_frame.bind(
            "<Configure>",
            lambda e: tasks_canvas.configure(scrollregion=tasks_canvas.bbox("all"))
        )
        tasks_canvas.bind_all("<Button-4>", lambda e: tasks_canvas.yview_scroll(-1, "units"))
        tasks_canvas.bind_all("<Button-5>", lambda e: tasks_canvas.yview_scroll(1, "units"))

        canvas_window_tasks = tasks_canvas.create_window((0, 0), window=tasks_inner_frame, anchor="nw")
        tasks_canvas.configure(yscrollcommand=tasks_scrollbar.set)

        def on_tasks_canvas_configure(event):
            tasks_canvas.itemconfig(canvas_window_tasks, width=event.width)
        tasks_canvas.bind('<Configure>', on_tasks_canvas_configure)

        tasks_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tasks_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.normal_font = tkfont.Font(family="Courier New", size=16)
        self.strike_font = tkfont.Font(family="Courier New", size=16, overstrike=1)
        self.checkboxes = []
        for idx, obj in enumerate(self.data["objectives"]):
            var = tk.BooleanVar(value=obj["completed"])
            chk = tk.Checkbutton(tasks_inner_frame, text=obj["text"], variable=var, bg=self.card_color, fg=self.text_color if not var.get() else self.done_color, selectcolor=self.bg_color, activebackground=self.card_color, activeforeground=self.accent_color, font=self.strike_font if var.get() else self.normal_font, highlightthickness=0, anchor="w", padx=20, pady=10, command=lambda i=idx, v=var: self.toggle_objective(i, v))
            chk.pack(fill=tk.X)
            self.checkboxes.append(chk)

        # Panel Derecho (Estadísticas y Botones)
        right_panel = tk.Frame(self.main_container, bg=self.bg_color, width=350)
        right_panel.pack(side=tk.RIGHT, fill=tk.Y)
        right_panel.pack_propagate(False)
        tk.Button(right_panel, text="🎵 ABRIR MONOJO MUSIC", font=("Courier New", 14, "bold"), bg=self.card_color, fg=self.accent_color, bd=1, relief=tk.SOLID, command=self.open_monojo_music).pack(fill=tk.X, pady=(0, 15), ipady=8)

        quote_frame = tk.Frame(right_panel, bg=self.card_color, bd=1, relief=tk.SOLID)
        quote_frame.pack(fill=tk.X, pady=(0, 15))
        tk.Label(quote_frame, text="FRASE DEL DÍA", font=("Courier New", 10, "bold"), fg=self.accent_color, bg=self.card_color).pack(pady=(5, 0))
        tk.Message(quote_frame, text=f'"{self.quote_of_the_day}"', font=("Courier New", 11, "italic"), fg=self.text_color, bg=self.card_color, width=300, justify="center").pack(pady=8, padx=10)

        stats_frame = tk.Frame(right_panel, bg=self.card_color, bd=1, relief=tk.SOLID)
        stats_frame.pack(fill=tk.X, pady=5)
        tk.Label(stats_frame, text="📊 RENDIMIENTO DEL SISTEMA", font=("Courier New", 11, "bold"), fg=self.accent_color, bg=self.card_color).pack(pady=(5, 5))
        tk.Label(stats_frame, text=f"RANGO: {metrics['rank']}", font=("Courier New", 11, "bold"), fg=self.text_color, bg=self.card_color, anchor="w").pack(fill=tk.X, padx=15, pady=2)
        tk.Label(stats_frame, text=f"RACHA: 🔥 {metrics['streak']} DÍAS SEGUIDOS", font=("Courier New", 11), fg=self.warning_color, bg=self.card_color, anchor="w").pack(fill=tk.X, padx=15, pady=2)
        tk.Label(stats_frame, text=f"EFICIENCIA: {metrics['efficiency']:.1f}%", font=("Courier New", 11), fg=self.text_color, bg=self.card_color, anchor="w").pack(fill=tk.X, padx=15, pady=2)

        total_days = self.data["target_days"]
        done_days = metrics["completed_days"]
        progress_pct = int((done_days / total_days) * 100) if total_days > 0 else 0
        bar_length = 12
        filled_blocks = int((done_days / total_days) * bar_length) if total_days > 0 else 0
        empty_blocks = bar_length - filled_blocks
        tk.Label(stats_frame, text="PROGRESO RETO:", font=("Courier New", 10), fg=self.done_color, bg=self.card_color, anchor="w").pack(fill=tk.X, padx=15, pady=(10, 0))
        tk.Label(stats_frame, text=f"[{'█' * filled_blocks}{'░' * empty_blocks}] {progress_pct}%", font=("Courier New", 12, "bold"), fg=self.accent_color, bg=self.card_color, anchor="w").pack(fill=tk.X, padx=15, pady=(0, 10))

        bottom_container = tk.Frame(right_panel, bg=self.bg_color)
        bottom_container.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        self.clock_label = tk.Label(bottom_container, text="SYS_TIME: 00:00:00", font=("Courier New", 14, "bold"), fg=self.muted_green, bg=self.bg_color)
        self.clock_label.pack(pady=5)
        if self.data.get("difficulty", "Fácil") == "Fácil":
            tk.Button(bottom_container, text="⏹ ABORTAR MISIÓN", font=("Courier New", 10, "bold"), bg=self.bg_color, fg=self.danger_color, bd=1, relief=tk.SOLID, command=self.reset_all).pack(fill=tk.X, pady=5, ipady=5)

    def build_stonks_chart(self, parent):
        chart_frame = tk.Frame(parent, bg=self.card_color)
        chart_frame.pack(fill=tk.X, padx=10, pady=5)

        canvas_width = 780
        canvas_height = 140

        canvas = tk.Canvas(chart_frame, width=canvas_width, height=canvas_height, bg=self.bg_color, bd=0, highlightthickness=1, highlightbackground=self.dim_color)
        canvas.pack(fill=tk.X, pady=5)

        start_date_str = self.data.get("start_date")
        if not start_date_str:
            return

        start_d = datetime.datetime.strptime(start_date_str, "%Y-%m-%d").date()
        total_days = self.data["target_days"]
        today_d = date.today()

        points_data = []
        for day_i in range(1, total_days + 1):
            target_date_str = (start_d + timedelta(days=day_i - 1)).isoformat()
            if target_date_str in self.data["history"]:
                day_data = self.data["history"][target_date_str]
                score = day_data.get("score", 0) if isinstance(day_data, dict) else day_data
                points_data.append((day_i, score))
            elif target_date_str == self.today_str:
                if self.data["objectives"]:
                    total = len(self.data["objectives"])
                    completed = sum(1 for obj in self.data["objectives"] if obj["completed"])
                    score = (completed / total) * 100
                    points_data.append((day_i, score))
                else:
                    points_data.append((day_i, 0))
            else:
                if (start_d + timedelta(days=day_i - 1)) <= today_d:
                    points_data.append((day_i, 0))

        if not points_data:
            return

        padding_x = 50
        padding_y = 15
        graph_width = canvas_width - (2 * padding_x)
        graph_height = canvas_height - (2 * padding_y)

        for pct, label in [(0, "0%"), (50, "50%"), (100, "100%")]:
            y_guideline = padding_y + graph_height - (pct / 100) * graph_height
            canvas.create_line(padding_x, y_guideline, canvas_width - padding_x, y_guideline, fill=self.dim_color, dash=(2, 4))
            canvas.create_text(padding_x - 10, y_guideline, text=label, fill=self.done_color, font=("Courier New", 9), anchor="e")

        coords = []
        divisor_dias = (total_days - 1) if total_days > 1 else 1
        for day_num, score in points_data:
            x = padding_x + ((day_num - 1) / divisor_dias) * graph_width
            y = padding_y + graph_height - (score / 100) * graph_height
            coords.append((x, y))

        if len(coords) > 1:
            poly_coords = [coords[0][0], padding_y + graph_height]
            for cx, cy in coords:
                poly_coords.extend([cx, cy])
            poly_coords.extend([coords[-1][0], padding_y + graph_height])
            canvas.create_polygon(poly_coords, fill="#00220A", outline="")

        for i in range(len(coords) - 1):
            canvas.create_line(coords[i][0], coords[i][1], coords[i+1][0], coords[i+1][1], fill=self.accent_color, width=3)

        for i, (cx, cy) in enumerate(coords):
            day_num, score = points_data[i]
            node_color = self.accent_color if score == 100 else (self.warning_color if score > 0 else self.danger_color)
            r = 3
            canvas.create_oval(cx - r, cy - r, cx + r, cy + r, fill=node_color, outline=self.bg_color, width=1)
            if i == 0 or i == len(coords) - 1 or score == 100:
                canvas.create_text(cx, cy - 12, text=f"{int(score)}%", fill=self.text_color, font=("Courier New", 8, "bold"))

    def toggle_objective(self, index, var):
        self.data["objectives"][index]["completed"] = var.get()
        self.save_data()
        self.render_view()

    def build_progress_table(self, parent):
        start_d = datetime.datetime.strptime(self.data["start_date"], "%Y-%m-%d").date()
        today_d = date.today()
        current_day_num = (today_d - start_d).days + 1
        cols = 14
        for day_i in range(1, self.data["target_days"] + 1):
            row = (day_i - 1) // cols
            col = (day_i - 1) % cols
            target_date_str = (start_d + timedelta(days=day_i - 1)).isoformat()
            bg_col, fg_col = self.dim_color, "#777777"
            if day_i < current_day_num or (day_i == current_day_num and target_date_str in self.data["history"]):
                score = self.data["history"].get(target_date_str, {}).get("score", 0) if isinstance(self.data["history"].get(target_date_str), dict) else self.data["history"].get(target_date_str, 0)
                if score == 100:
                    bg_col, fg_col = self.accent_color, self.bg_color
                elif score > 0:
                    bg_col, fg_col = self.muted_green, self.text_color
                else:
                    bg_col, fg_col = self.danger_color, self.text_color
            if day_i == current_day_num:
                bg_col, fg_col = "#FFFF00", self.bg_color
            lbl = tk.Label(parent, text=f"{day_i:02d}", font=("Courier New", 10, "bold"), bg=bg_col, fg=fg_col, width=3, height=1, cursor="hand2")
            lbl.grid(row=row, column=col, padx=2, pady=2)
            lbl.bind("<Button-1>", lambda e, d=day_i, ds=target_date_str: self.show_day_details(d, ds))

    def show_day_details(self, day_num, date_str):
        if date_str in self.data["history"]:
            data = self.data["history"][date_str]
            if isinstance(data, dict):
                self.history_detail_label.config(text=f"Día {day_num} ({date_str}): {data.get('completed', 0)}/{data.get('total', 0)} tareas cumplidas.")
            else:
                self.history_detail_label.config(text=f"Día {day_num} ({date_str}): Eficiencia calculada al {int(data)}%")
        else:
            self.history_detail_label.config(text=f"Día {day_num}: {'En curso...' if date_str == self.today_str else 'Sin registros de actividad.'}")

    def reset_all(self):
        if messagebox.askyesno("Abortar Misión", "¿De verdad quieres rendirte?\nTu rango y racha serán destruidos."):
            self.data.update({"challenge_active": False, "target_days": 0, "difficulty": "Fácil", "start_date": "", "last_date": "", "daily_locked": False, "objectives": [], "history": {}, "fixed_objectives": []})
            self.save_data()
            self.render_view()

    def open_monojo_music(self):
        try:
            subprocess.Popen(["monojo-music"])
        except FileNotFoundError:
            pass


def run_main():
    root = tk.Tk()
    app = None

    def on_closing():
        if app and (not app.data.get("challenge_active") or not app.data.get("daily_locked")):
            messagebox.showinfo("Lynds Glow Up", "El sistema entrará en hibernación.\nEl Maestro Casata te esperará.")
            root.destroy()
            sys.exit(0)
        else:
            enviar_notificacion("⚡ Lynds Glow Up", "Operador: Sistema oculto en segundo plano. Modo centinela activado.", "system-run")
            subprocess.Popen(BASE_CMD + ["--secondary"], start_new_session=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            root.destroy()
            sys.exit(0)

    app = LyndsGlowUp(root, on_closing)
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()


def run_secondary():
    launched_today = False
    while True:
        now = datetime.datetime.now()

        if now.hour >= 22 and not launched_today:
            enviar_notificacion("⚡ Lynds Glow Up", "¡Son las 10 PM!\nAbriendo terminal de misiones...", "terminal")
            subprocess.Popen(BASE_CMD + ["--main"])
            launched_today = True
            sys.exit(0)

        if now.hour < 22:
            launched_today = False

        json_path = os.path.join(CONFIG_DIR, "app_state.json")
        try:
            if os.path.exists(json_path):
                with open(json_path, "r") as f:
                    data = json.load(f)

                if data.get("challenge_active") and data.get("daily_locked"):
                    pending = sum(1 for obj in data.get("objectives", []) if not obj.get("completed", True))

                    if pending > 0:
                        difficulty = data.get("difficulty", "Fácil")
                        notify = False
                        msg = ""

                        if difficulty == "Duro":
                            if now.minute % 15 == 0 and now.second < 30:
                                notify = True
                                msg = f"¡Alerta Operativa! Quedan {pending} tareas. El Maestro Casata exige resultados inmediatos."
                        else:
                            if (now.minute == 0 or now.minute == 30) and now.second < 30:
                                notify = True
                                msg = f"No te olvides, te quedan {pending} tareas pendientes para hoy."

                        if notify:
                            enviar_notificacion("⚡ Aviso de Sistema", msg, "dialog-warning")
                            time.sleep(60)
        except Exception:
            pass

        time.sleep(30)


def run_relative():
    now = datetime.datetime.now()
    if now.hour >= 22:
        subprocess.Popen(BASE_CMD + ["--main"])
    else:
        subprocess.Popen(BASE_CMD + ["--secondary"])


if __name__ == "__main__":
    os.makedirs(CONFIG_DIR, exist_ok=True)
    enforce_single_instance()

    if len(sys.argv) > 1:
        modo = sys.argv[1]
        if modo == "--main":
            run_main()
        elif modo == "--secondary":
            run_secondary()
        elif modo == "--relative":
            run_relative()
        else:
            print("Uso: lynds-glowup [--main | --secondary | --relative]")
    else:
        run_main()
