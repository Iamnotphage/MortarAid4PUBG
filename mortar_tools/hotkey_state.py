import time


class HotkeyStateMachine:
    """Track Alt/Q combo timing and in-flow exit guard state."""

    def __init__(self, start_combo_max_interval: float, exit_combo_guard_seconds: float):
        self.start_combo_max_interval = float(start_combo_max_interval)
        self.exit_combo_guard_seconds = float(exit_combo_guard_seconds)

        self.alt_is_down = False
        self.q_is_down = False
        self.alt_down_at = 0.0
        self.q_down_at = 0.0
        self.start_hotkey_latched = False

        self.exit_combo_count = 0
        self.startup_guard_deadline = 0.0
        self.immediate_exit_requested = False

    def enter_measurement(self, started_at: float = None) -> None:
        # Guard only the first seconds after entering measurement to absorb accidental combos.
        now = time.monotonic() if started_at is None else float(started_at)
        self.exit_combo_count = 0
        self.startup_guard_deadline = now + self.exit_combo_guard_seconds
        self.immediate_exit_requested = False

    def set_start_combo_max_interval(self, value: float) -> None:
        self.start_combo_max_interval = float(value)

    def on_alt_press(self, is_measuring: bool):
        if self.alt_is_down:
            return None
        self.alt_is_down = True
        self.alt_down_at = time.monotonic()
        return self._try_trigger_combo(is_measuring)

    def on_alt_release(self) -> None:
        self.alt_is_down = False
        self.start_hotkey_latched = False

    def on_q_press(self, is_measuring: bool):
        if self.q_is_down:
            return None
        self.q_is_down = True
        self.q_down_at = time.monotonic()
        return self._try_trigger_combo(is_measuring)

    def on_q_release(self) -> None:
        self.q_is_down = False
        self.start_hotkey_latched = False

    def _try_trigger_combo(self, is_measuring: bool):
        if self.start_hotkey_latched:
            return None
        if not (self.alt_is_down and self.q_is_down):
            return None

        if abs(self.alt_down_at - self.q_down_at) > self.start_combo_max_interval:
            return None

        self.start_hotkey_latched = True
        if is_measuring:
            self._register_exit_combo()
            return None
        return "start"

    def _register_exit_combo(self) -> None:
        now = time.monotonic()

        # During startup guard window: defer exit decision until window ends.
        if self.startup_guard_deadline > 0.0 and now <= self.startup_guard_deadline:
            self.exit_combo_count += 1
            return

        # After startup window: exit immediately on a valid combo.
        self.immediate_exit_requested = True

    def consume_exit_request(self) -> bool:
        """
        Return True when exit should happen now.
        1) After startup guard window: exit immediately.
        2) In startup guard window: only a single combo exits when window closes.
        """
        if self.immediate_exit_requested:
            self.immediate_exit_requested = False
            return True

        if self.startup_guard_deadline <= 0.0:
            return False

        if time.monotonic() < self.startup_guard_deadline:
            return False

        should_exit = self.exit_combo_count == 1
        self.exit_combo_count = 0
        self.startup_guard_deadline = 0.0
        return should_exit

    def reset_exit_window(self) -> None:
        self.exit_combo_count = 0
        self.startup_guard_deadline = 0.0
        self.immediate_exit_requested = False
