import ctypes
import os
import sys
import tkinter as tk
import tkinter.font as tkfont
import pyautogui
import time
import mouse
import keyboard
import mortar_tools.calculator as calc
from mortar_tools.hotkey_state import HotkeyStateMachine
from mortar_tools.i18n_texts import I18N_TEXTS
from mortar_tools.settings_store import AppSettings, load_settings, resolve_settings_path, save_settings

class main():
    PJP_SCALE = (
        121, 133, 145, 157, 169, 181, 193, 204, 216, 228,
        239, 250, 262, 273, 284, 295, 307, 317, 328, 339,
        350, 360, 371, 381, 391, 401, 411, 421, 431, 440,
        450, 459, 468, 477, 486, 495, 503, 512, 520, 528,
        536, 544, 551, 559, 566, 573, 580, 587, 593, 600,
        606, 612, 618, 624, 629, 634, 639, 644, 649, 653,
        658, 662, 666, 669, 673, 676, 679, 682, 685, 687,
        689, 691, 693, 695, 696, 697, 698, 699, 699, 700, 700,
    )
    RESET_TO_MAX_SCROLL_STEPS = 170
    RESET_SCROLL_INTERVAL = 0.002
    ADJUST_SCROLL_INTERVAL = 0.005
    RESULT_HOLD_SECONDS = 5

    def __init__(self):
        self.title = "Mortar Distance Measurement Tool"
        self.geometry = "360x220"
        self.start_hotkey = "alt+q"
        self.point_hotkey = "alt+left"
        self.point_modifier = self.point_hotkey.split("+", 1)[0]
        self.reset_hotkey = "alt+right"
        self.start_combo_max_interval = 0.5
        self.exit_combo_guard_seconds = 1.5
        self.start_combo_options = [0.3, 0.5, 0.8]
        self.reset_requested = False
        self.is_measuring = False
        self.exit_signal = object()
        self.start_requested = False
        self.language = "en"
        self.hotkey_state = HotkeyStateMachine(
            start_combo_max_interval=self.start_combo_max_interval,
            exit_combo_guard_seconds=self.exit_combo_guard_seconds,
        )
        self.root = None
        self.current_page = "home"
        self.content_frame = None
        self.home_frame = None
        self.settings_frame = None
        self.help_frame = None
        self.message_label = None
        self.language_var = None
        self.start_interval_var = None
        self.help_images = []
        self.settings_path = resolve_settings_path()
        self.i18n = I18N_TEXTS
        self.use_windows_key_polling = sys.platform == "win32"
        self.prev_alt_down = False
        self.prev_q_down = False
        self.prev_r_down = False
        self.trigger_help_visible = False
        self.last_solution_value = None
        self.r_trigger_deadline = 0.0
        self.pjp_scroll_sequence = tuple(reversed(self.PJP_SCALE))
        self.ui_colors = {
            "bg": "#f2f5fa",
            "surface": "#ffffff",
            "surface_alt": "#eef3fb",
            "border": "#d1daea",
            "title": "#183153",
            "text": "#29415f",
            "muted": "#61738a",
            "accent": "#2d72d2",
            "accent_hover": "#245fb0",
            "accent_soft": "#e7f0ff",
            "button_text": "#ffffff",
        }

        settings = load_settings(self.settings_path, self.start_combo_options)
        if settings.language in self.i18n:
            self.language = settings.language
        self.start_combo_max_interval = settings.start_combo_max_interval
        self.hotkey_state.set_start_combo_max_interval(self.start_combo_max_interval)
        self.title = self.t("window_title")

    def persist_settings(self):
        save_settings(
            self.settings_path,
            AppSettings(
                language=self.language,
                start_combo_max_interval=self.start_combo_max_interval,
            ),
        )

    def t(self, key, **kwargs):
        text = self.i18n[self.language][key]
        if kwargs:
            return text.format(**kwargs)
        return text

    def get_ui_font(self):
        if self.language == "zh":
            return ("Microsoft YaHei UI", 11)
        return ("Consolas", 12)

    def fit_window_to_content(self):
        if self.root is None or self.message_label is None:
            return

        text = self.get_info_text()
        lines = text.splitlines()
        if not lines:
            lines = [""]

        font = tkfont.Font(font=self.message_label.cget("font"))
        max_text_width = max(font.measure(line) for line in lines)
        lines_height = font.metrics("linespace") * len(lines)

        width = max(360, max_text_width + 36)
        height = max(220, lines_height + 90)

        self.root.geometry(f"{width}x{height}")
        self.root.minsize(width, height)

    def update_window_size_for_page(self):
        if self.root is None:
            return

        if self.current_page == "settings":
            base_width = 580
            base_height = 360
            self.root.update_idletasks()

            width = base_width
            height = base_height
            if self.settings_frame is not None:
                width = max(base_width, self.settings_frame.winfo_reqwidth() + 20)
                height = max(base_height, self.settings_frame.winfo_reqheight() + 24)

            max_height = max(base_height, self.root.winfo_screenheight() - 100)
            height = min(height, max_height)

            self.root.geometry(f"{width}x{height}")
            self.root.minsize(base_width, base_height)
            return

        if self.current_page == "help":
            base_width = 760
            base_height = 620
            self.root.update_idletasks()

            width = base_width
            height = base_height
            if self.help_frame is not None:
                width = max(base_width, self.help_frame.winfo_reqwidth() + 20)
                height = max(base_height, self.help_frame.winfo_reqheight() + 24)

            max_height = max(base_height, self.root.winfo_screenheight() - 80)
            height = min(height, max_height)

            self.root.geometry(f"{width}x{height}")
            self.root.minsize(base_width, base_height)
            return

        self.fit_window_to_content()

    def get_info_text(self):
        return (
            f"{self.t('control_title')}\n"
            f"{self.t('control_start')}\n"
            f"{self.t('control_point')}\n\n"
            f"{self.t('control_reset')}\n"
            f"{self.t('control_adjust_r')}\n\n"
        )

    def set_language(self, lang):
        if lang not in self.i18n:
            return
        self.language = lang
        self.title = self.t("window_title")
        self.persist_settings()
        self.refresh_ui_texts()

    def create_menu(self):
        if self.root is None:
            return

        menu_bar = tk.Menu(
            self.root,
            bg=self.ui_colors["surface"],
            fg=self.ui_colors["text"],
            activebackground=self.ui_colors["accent_soft"],
            activeforeground=self.ui_colors["title"],
            tearoff=0,
        )
        menu_bar.add_command(label=self.t("menu_home"), command=self.show_home_page)
        menu_bar.add_command(label=self.t("menu_settings"), command=self.show_settings_page)
        menu_bar.add_command(label=self.t("menu_help"), command=self.show_help_page)
        self.root.config(menu=menu_bar)

    def create_pages(self):
        self.content_frame = tk.Frame(self.root, bg=self.ui_colors["bg"])
        self.content_frame.pack(fill="both", expand=True)

        self.home_frame = tk.Frame(self.content_frame, bg=self.ui_colors["bg"])
        self.settings_frame = tk.Frame(self.content_frame, bg=self.ui_colors["bg"])
        self.help_frame = tk.Frame(self.content_frame, bg=self.ui_colors["bg"])

        home_card = tk.Frame(
            self.home_frame,
            bg=self.ui_colors["surface"],
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.ui_colors["border"],
        )
        home_card.pack(fill="both", expand=True, padx=14, pady=14)

        self.message_label = tk.Label(
            home_card,
            text="",
            justify="left",
            anchor="nw",
            bg=self.ui_colors["surface"],
            fg=self.ui_colors["text"],
            padx=14,
            pady=12,
        )
        self.message_label.pack(fill="both", expand=True)

        self.language_var = tk.StringVar(value=self.language)
        self.start_interval_var = tk.DoubleVar(value=self.start_combo_max_interval)

    def _load_help_image(self, filename, max_width=640):
        image_path = self._resolve_resource_path("img", filename)
        if not os.path.exists(image_path):
            return None
        try:
            image = tk.PhotoImage(file=image_path)
        except tk.TclError:
            return None

        width = image.width()
        if width <= 0:
            return image
        if width <= max_width:
            return image

        ratio = max(1, (width + max_width - 1) // max_width)
        return image.subsample(ratio, ratio)

    def _resolve_resource_path(self, *parts):
        base_dir = getattr(sys, "_MEIPASS", None)
        if base_dir:
            return os.path.join(base_dir, *parts)
        return os.path.join(os.path.dirname(os.path.abspath(__file__)), *parts)

    def build_help_page(self):
        if self.help_frame is None:
            return

        for child in self.help_frame.winfo_children():
            child.destroy()
        self.help_images = []

        ui_font = self.get_ui_font()
        title_font = (ui_font[0], ui_font[1] + 3, "bold")
        body_font = (ui_font[0], ui_font[1])
        subtitle_font = (ui_font[0], ui_font[1], "bold")

        shell = tk.Frame(self.help_frame, bg=self.ui_colors["bg"])
        shell.pack(fill="both", expand=True, padx=12, pady=12)

        title_card = tk.Frame(
            shell,
            bg=self.ui_colors["surface"],
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.ui_colors["border"],
        )
        title_card.pack(fill="x", pady=(0, 10))

        tk.Label(
            title_card,
            text=self.t("help_title"),
            font=title_font,
            fg=self.ui_colors["title"],
            bg=self.ui_colors["surface"],
            anchor="w",
            padx=14,
            pady=10,
        ).pack(fill="x")

        content_card = tk.Frame(
            shell,
            bg=self.ui_colors["surface"],
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.ui_colors["border"],
        )
        content_card.pack(fill="both", expand=True)

        canvas = tk.Canvas(
            content_card,
            bg=self.ui_colors["surface"],
            highlightthickness=0,
            bd=0,
        )
        scrollbar = tk.Scrollbar(content_card, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        inner = tk.Frame(canvas, bg=self.ui_colors["surface"])
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_inner_configure(_event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_configure(event):
            canvas.itemconfig(window_id, width=event.width)

        inner.bind("<Configure>", on_inner_configure)
        canvas.bind("<Configure>", on_canvas_configure)

        def add_text(text, font=None, fg=None, pady=(0, 6)):
            tk.Label(
                inner,
                text=text,
                font=font or body_font,
                justify="left",
                anchor="w",
                wraplength=700,
                fg=fg or self.ui_colors["text"],
                bg=self.ui_colors["surface"],
            ).pack(fill="x", padx=12, pady=pady)

        def add_image(filename):
            img = self._load_help_image(filename)
            if img is None:
                return
            self.help_images.append(img)
            tk.Label(inner, image=img, bg=self.ui_colors["surface"]).pack(anchor="w", padx=12, pady=(0, 10))

        add_text(self.t("help_line_start"))
        add_text(self.t("help_line_point"))
        add_text(self.t("help_line_reset"))
        add_text(self.t("help_line_r"), pady=(0, 10))
        add_text(self.t("help_line_settings"), pady=(0, 8))
        add_text(self.t("help_line_config"), font=subtitle_font)
        add_text(self.t("help_line_config_lang"))
        add_text(self.t("help_line_config_trigger"), pady=(0, 10))
        add_text(self.t("help_line_note"), fg=self.ui_colors["muted"], pady=(0, 12))
        add_text(self.t("help_step_group_12"), font=subtitle_font)
        add_text(self.t("help_step_1"), pady=(0, 4))
        add_image("guide-step1.png")
        add_text(self.t("help_step_2"), pady=(0, 4))
        add_image("guide-step2.png")
        add_text(self.t("help_step_group_3"), font=subtitle_font)
        add_text(self.t("help_step_3"), pady=(0, 10))
        add_text(self.t("help_result"), font=subtitle_font)

        canvas.yview_moveto(0)

    def build_settings_page(self):
        if self.settings_frame is None or self.language_var is None or self.start_interval_var is None:
            return

        for child in self.settings_frame.winfo_children():
            child.destroy()

        ui_font = self.get_ui_font()
        title_font = (ui_font[0], ui_font[1] + 3, "bold")
        section_title_font = (ui_font[0], ui_font[1] + 1, "bold")
        body_font = (ui_font[0], ui_font[1])

        language_var = self.language_var
        start_interval_var = self.start_interval_var

        language_var.set(self.language)
        start_interval_var.set(self.start_combo_max_interval)

        self.settings_frame.configure(bg=self.ui_colors["bg"])

        shell = tk.Frame(self.settings_frame, bg=self.ui_colors["bg"])
        shell.pack(fill="both", expand=True, padx=16, pady=14)

        footer = tk.Frame(shell, bg=self.ui_colors["bg"], height=48)
        footer.pack(side="bottom", fill="x", pady=(2, 0))
        footer.pack_propagate(False)

        content_area = tk.Frame(shell, bg=self.ui_colors["bg"])
        content_area.pack(side="top", fill="both", expand=True)

        title_card = tk.Frame(
            content_area,
            bg=self.ui_colors["surface"],
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.ui_colors["border"],
        )
        title_card.pack(fill="x", pady=(0, 12))
        tk.Label(
            title_card,
            text=self.t("settings_title"),
            font=title_font,
            fg=self.ui_colors["title"],
            bg=self.ui_colors["surface"],
            anchor="w",
            padx=16,
            pady=12,
        ).pack(fill="x")

        language_card = tk.Frame(
            content_area,
            bg=self.ui_colors["surface"],
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.ui_colors["border"],
            padx=12,
            pady=10,
        )
        language_card.pack(fill="x", pady=(0, 10))
        tk.Label(
            language_card,
            text=self.t("menu_language"),
            font=section_title_font,
            fg=self.ui_colors["title"],
            bg=self.ui_colors["surface"],
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        language_options = tk.Frame(language_card, bg=self.ui_colors["surface"])
        language_options.pack(fill="x")
        for value, label_key in (("en", "menu_lang_en"), ("zh", "menu_lang_zh")):
            tk.Radiobutton(
                language_options,
                text=self.t(label_key),
                value=value,
                variable=language_var,
                command=lambda: self.set_language(language_var.get()),
                font=body_font,
                indicatoron=False,
                bg=self.ui_colors["surface_alt"],
                fg=self.ui_colors["text"],
                selectcolor=self.ui_colors["accent"],
                activebackground=self.ui_colors["accent_hover"],
                activeforeground=self.ui_colors["button_text"],
                width=12,
                padx=10,
                pady=6,
                bd=1,
                relief="solid",
                highlightthickness=0,
            ).pack(side="left", padx=(0, 10))

        trigger_card = tk.Frame(
            content_area,
            bg=self.ui_colors["surface"],
            relief="flat",
            bd=1,
            highlightthickness=1,
            highlightbackground=self.ui_colors["border"],
            padx=12,
            pady=10,
        )
        trigger_card.pack(fill="x", pady=(0, 10))
        tk.Label(
            trigger_card,
            text=self.t("menu_trigger_window"),
            font=section_title_font,
            fg=self.ui_colors["title"],
            bg=self.ui_colors["surface"],
            anchor="w",
        ).pack(fill="x", pady=(0, 8))

        trigger_row = tk.Frame(trigger_card, bg=self.ui_colors["surface"])
        trigger_row.pack(fill="x")

        trigger_options = tk.Frame(trigger_row, bg=self.ui_colors["surface"])
        trigger_options.pack(side="left", fill="x", expand=True)
        for option in self.start_combo_options:
            tk.Radiobutton(
                trigger_options,
                text=self.t("menu_trigger_window_value", value=option),
                value=option,
                variable=start_interval_var,
                command=lambda v=option: self.set_start_combo_interval(v),
                font=body_font,
                indicatoron=False,
                bg=self.ui_colors["surface_alt"],
                fg=self.ui_colors["text"],
                selectcolor=self.ui_colors["accent"],
                activebackground=self.ui_colors["accent_hover"],
                activeforeground=self.ui_colors["button_text"],
                width=9,
                padx=10,
                pady=6,
                bd=1,
                relief="solid",
                highlightthickness=0,
            ).pack(side="left", padx=(0, 10))

        help_button = tk.Button(
            trigger_row,
            text=self.t("settings_help"),
            command=self.toggle_trigger_help,
            font=body_font,
            bg=self.ui_colors["surface_alt"],
            fg=self.ui_colors["accent"],
            activebackground=self.ui_colors["accent_soft"],
            activeforeground=self.ui_colors["accent"],
            relief="solid",
            bd=1,
            highlightthickness=0,
            padx=12,
            pady=6,
            cursor="hand2",
        )
        help_button.pack(side="right")

        if self.trigger_help_visible:
            hint_box = tk.Frame(
                trigger_card,
                bg=self.ui_colors["accent_soft"],
                relief="flat",
                bd=1,
                highlightthickness=1,
                highlightbackground=self.ui_colors["border"],
            )
            hint_box.pack(fill="x", pady=(9, 0))
            tk.Label(
                hint_box,
                text=self.t("settings_hint"),
                font=body_font,
                justify="left",
                anchor="w",
                wraplength=532,
                fg=self.ui_colors["muted"],
                bg=self.ui_colors["accent_soft"],
                padx=12,
                pady=9,
            ).pack(fill="x")

        back_button = tk.Button(
            footer,
            text=self.t("settings_back"),
            command=self.show_home_page,
            font=body_font,
            bg=self.ui_colors["accent"],
            fg=self.ui_colors["button_text"],
            activebackground=self.ui_colors["accent_hover"],
            activeforeground=self.ui_colors["button_text"],
            relief="solid",
            bd=1,
            padx=16,
            pady=8,
            cursor="hand2",
        )
        back_button.pack(anchor="w", pady=4)

    def show_page(self, page):
        self.current_page = page
        if self.home_frame is not None:
            self.home_frame.pack_forget()
        if self.settings_frame is not None:
            self.settings_frame.pack_forget()
        if self.help_frame is not None:
            self.help_frame.pack_forget()

        if page == "settings":
            if self.settings_frame is not None:
                self.settings_frame.pack(fill="both", expand=True)
        elif page == "help":
            if self.help_frame is not None:
                self.help_frame.pack(fill="both", expand=True)
        else:
            if self.home_frame is not None:
                self.home_frame.pack(fill="both", expand=True)

        self.update_window_size_for_page()

    def show_home_page(self):
        self.show_page("home")

    def show_settings_page(self):
        self.build_settings_page()
        self.show_page("settings")
        if self.root is not None:
            self.root.after_idle(self.update_window_size_for_page)

    def show_help_page(self):
        self.build_help_page()
        self.show_page("help")
        if self.root is not None:
            self.root.after_idle(self.update_window_size_for_page)

    def set_start_combo_interval(self, value):
        value = float(value)
        if value not in self.start_combo_options:
            return
        self.start_combo_max_interval = value
        self.hotkey_state.set_start_combo_max_interval(value)
        self.persist_settings()
        self.refresh_ui_texts()

    def toggle_trigger_help(self):
        self.trigger_help_visible = not self.trigger_help_visible
        if self.current_page == "settings":
            self.build_settings_page()
            self.update_window_size_for_page()

    def refresh_ui_texts(self):
        if self.root is not None:
            self.root.title(self.t("window_title"))
            self.create_menu()
        if self.message_label is not None:
            self.message_label.config(font=self.get_ui_font())
            self.message_label.config(text=self.get_info_text())
        if self.current_page == "settings":
            self.build_settings_page()
        if self.current_page == "help":
            self.build_help_page()
        self.update_window_size_for_page()

    
    def create_static_window(self):
        window = tk.Toplevel(self.root)
        window.overrideredirect(True)
        window.attributes("-topmost", True)
        label = tk.Label(window, font=("Helvetica", 14), bg="yellow", padx=10, pady=5)
        label.pack()
        window.update_idletasks()
        window.geometry("+0+0")
        window.lift()
        return window, label

    def _set_overlay_text(self, window, label, key, **kwargs):
        label.config(text=self.t(key, **kwargs))
        window.update()
        self.pump_main_ui()

    def pump_main_ui(self):
        if self.root is None:
            return
        try:
            self.root.update_idletasks()
            self.root.update()
        except tk.TclError:
            pass

    def wait_with_ui(self, seconds, interval=0.03, allow_exit=False):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            if allow_exit and self.hotkey_state.consume_exit_request():
                return "exit"
            self.pump_main_ui()
            time.sleep(interval)
        return "ok"

    def get_point(self):
        # Block until a valid point, reset, or exit signal is received.
        pos = None

        def on_click(event):
            nonlocal pos
            if not isinstance(event, mouse.ButtonEvent) or event.event_type != 'down':
                return

            modifier_pressed = self.is_modifier_pressed()

            if modifier_pressed and event.button == 'right':
                self.reset_requested = True
                return

            if modifier_pressed and event.button == 'left':
                pos = pyautogui.position()
        mouse.hook(on_click)

        try:
            # 等待用户点击
            while pos is None:
                if self.hotkey_state.consume_exit_request():
                    return self.exit_signal
                if self.reset_requested:
                    return None
                self.pump_main_ui()
                time.sleep(0.03)  # 防止 CPU 过载，同时提高退出与重置响应速度
            return pos
        finally:
            mouse.unhook(on_click)

    def _is_vk_down(self, vk_code):
        if not self.use_windows_key_polling:
            return False
        try:
            return bool(ctypes.windll.user32.GetAsyncKeyState(vk_code) & 0x8000)
        except Exception:
            return False

    def is_modifier_pressed(self):
        if self.use_windows_key_polling:
            return self._is_vk_down(0x12)
        return self.hotkey_state.alt_is_down or keyboard.is_pressed(self.point_modifier)

    def poll_global_hotkeys(self):
        if self.use_windows_key_polling:
            alt_down = self._is_vk_down(0x12)
            q_down = self._is_vk_down(ord("Q"))
            r_down = self._is_vk_down(ord("R"))

            if alt_down and not self.prev_alt_down:
                self.on_alt_press(None)
            elif self.prev_alt_down and not alt_down:
                self.on_alt_release(None)

            if q_down and not self.prev_q_down:
                self.on_q_press(None)
            elif self.prev_q_down and not q_down:
                self.on_q_release(None)

            if r_down and not self.prev_r_down:
                self.on_r_press(None)

            self.prev_alt_down = alt_down
            self.prev_q_down = q_down
            self.prev_r_down = r_down

        if self.root is not None:
            self.root.after(15, self.poll_global_hotkeys)

    def request_reset(self):
        if self.is_measuring:
            self.reset_requested = True

    def on_alt_press(self, _event):
        action = self.hotkey_state.on_alt_press(self.is_measuring)
        if action == "start":
            self.start_requested = True

    def on_alt_release(self, _event):
        self.hotkey_state.on_alt_release()

    def on_q_press(self, _event):
        action = self.hotkey_state.on_q_press(self.is_measuring)
        if action == "start":
            self.start_requested = True

    def on_q_release(self, _event):
        self.hotkey_state.on_q_release()

    def on_r_press(self, _event):
        if time.monotonic() > self.r_trigger_deadline:
            return
        self.apply_auto_scroll_to_last_solution()

    def apply_auto_scroll_to_last_solution(self):
        if self.last_solution_value is None:
            return

        # Hard reset wheel state: scroll down enough times to clamp mortar scale to 700.
        for _ in range(self.RESET_TO_MAX_SCROLL_STEPS):
            mouse.wheel(-1)
            time.sleep(self.RESET_SCROLL_INTERVAL)

        scroll_plan = self._get_scroll_plan_from_solution(self.last_solution_value)
        if scroll_plan is None:
            return

        full_steps, fractional_step = scroll_plan
        if full_steps <= 0 and fractional_step <= 0:
            return

        for _ in range(full_steps):
            # Positive wheel value is upward scroll in the mouse package.
            mouse.wheel(1)
            time.sleep(self.ADJUST_SCROLL_INTERVAL)

        if fractional_step > 0:
            mouse.wheel(fractional_step)

    def _get_scroll_plan_from_solution(self, value):
        if value is None:
            return None

        value = float(value)
        if value <= 0:
            return None

        rounded_value = int(round(value))
        min_value = self.PJP_SCALE[0]
        max_value = self.PJP_SCALE[-1]
        rounded_value = max(min_value, min(max_value, rounded_value))

        if rounded_value in self.PJP_SCALE:
            return self._get_scroll_steps_from_default(rounded_value), 0.0

        for index in range(len(self.PJP_SCALE) - 1):
            lower = self.PJP_SCALE[index]
            upper = self.PJP_SCALE[index + 1]
            if not (lower <= rounded_value <= upper):
                continue

            interval = upper - lower
            if interval <= 0:
                continue

            full_steps = self._get_scroll_steps_from_default(upper)
            fractional_step = round((upper - rounded_value) / interval, 1)
            if fractional_step >= 1.0:
                full_steps += 1
                fractional_step = 0.0
            return full_steps, max(0.0, fractional_step)

        return self._get_scroll_steps_from_default(max_value), 0.0

    def _get_scroll_steps_from_default(self, target_value):
        for index, candidate in enumerate(self.pjp_scroll_sequence):
            if candidate == target_value:
                return index
        return 0

    def process_pending_actions(self):
        # Keep UI-thread dispatch for start requests from either hook or polling path.
        if self.start_requested and not self.is_measuring:
            self.start_requested = False
            self.start_measurement()
        if self.root is not None:
            self.root.after(30, self.process_pending_actions)

    def _get_step_point(self, window, label, text):
        label.config(text=text)
        window.update()
        return self.get_point()

    def _measure_two_points(self, window, label, first_key, second_key):
        point1 = self._get_step_point(window, label, self.t(first_key))
        if point1 is self.exit_signal:
            return self.exit_signal, self.exit_signal
        if point1 is None:
            return None, None
        point2 = self._get_step_point(window, label, self.t(second_key))
        if point2 is self.exit_signal:
            return self.exit_signal, self.exit_signal
        if point2 is None:
            return None, None
        return point1, point2

    def _run_measurement_once(self, window, label):
        calculator = calc.calculator()
        screen_height = pyautogui.size().height
        calculator.set_viewport_height(screen_height)

        # get point1 and point2 for scale factor
        point1, point2 = self._measure_two_points(window, label, "step_scale_1", "step_scale_2")
        if point1 is self.exit_signal:
            return "exit"
        if point1 is None:
            return "reset"

        # calculate scale factor
        calculator.set_scale_factor(point1, point2)

        # get point1 and point2 for distance
        point1, point2 = self._measure_two_points(window, label, "step_measure_1", "step_measure_2")
        if point1 is self.exit_signal:
            return "exit"
        if point1 is None:
            return "reset"

        # calculate horizontal distance
        calculator.get_horizontal_distance(point1, point2)
        self._set_overlay_text(window, label, "max_distance", value=calculator.horizontal_distance)

        # get elevation angle point
        point = self._get_step_point(window, label, self.t("step_elevation"))
        if point is self.exit_signal:
            return "exit"
        if point is None:
            return "reset"

        # calculate elevation angle
        self._set_overlay_text(window, label, "elevation_value", value=calculator.get_evelation_angle(point))

        # calculate final distance
        self._set_overlay_text(
            window,
            label,
            "distance_value",
            value=calculator.solve(calculator.evelation_angle, calculator.horizontal_distance),
        )
        self.last_solution_value = calculator.result
        self.r_trigger_deadline = time.monotonic() + self.RESULT_HOLD_SECONDS

        return "done"
    
    def start_measurement(self):
        # Measurement state machine: done -> close, reset -> restart, exit -> close now.
        if self.is_measuring:
            return

        self.is_measuring = True
        self.last_solution_value = None
        self.r_trigger_deadline = 0.0
        self.hotkey_state.enter_measurement()
        window, label = self.create_static_window()

        try:
            while True:
                self.reset_requested = False
                self.last_solution_value = None
                self.r_trigger_deadline = 0.0
                status = self._run_measurement_once(window, label)

                if status == "exit":
                    window.withdraw()
                    window.update_idletasks()
                    break

                if status == "reset":
                    self._set_overlay_text(window, label, "reset_restarting")
                    if self.wait_with_ui(0.2, allow_exit=True) == "exit":
                        window.withdraw()
                        window.update_idletasks()
                        break
                    continue

                if self.wait_with_ui(self.RESULT_HOLD_SECONDS, allow_exit=True) == "exit":
                    window.withdraw()
                    window.update_idletasks()
                    break
                break
        finally:
            self.reset_requested = False
            self.is_measuring = False
            self.last_solution_value = None
            self.r_trigger_deadline = 0.0
            self.hotkey_state.reset_exit_window()
            window.destroy()

    def main(self):
        # register hotkeys
        if self.use_windows_key_polling:
            self.prev_alt_down = self._is_vk_down(0x12)
            self.prev_q_down = self._is_vk_down(ord("Q"))
            self.prev_r_down = self._is_vk_down(ord("R"))
        else:
            keyboard.add_hotkey(self.reset_hotkey, self.request_reset)
            keyboard.on_press_key(self.point_modifier, self.on_alt_press)
            keyboard.on_release_key(self.point_modifier, self.on_alt_release)
            keyboard.on_press_key("q", self.on_q_press)
            keyboard.on_release_key("q", self.on_q_release)
            keyboard.on_press_key("r", self.on_r_press)

        # create UI
        self.root = tk.Tk()
        self.root.geometry(self.geometry)
        self.root.configure(bg=self.ui_colors["bg"])
        self.root.attributes("-topmost", True)

        self.create_pages()

        self.refresh_ui_texts()
        self.show_home_page()
        self.process_pending_actions()
        self.poll_global_hotkeys()
        self.root.mainloop()

if __name__ == "__main__":
    app = main()
    app.main()