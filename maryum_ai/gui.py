from __future__ import annotations

import gi

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk  # noqa: E402

from .config import MaryumConfig
from .controller import AssistantState, MaryumController


class MaryumWindow(Gtk.Window):
    def __init__(self, config: MaryumConfig):
        super().__init__(title="Maryum Assistant")
        self.set_border_width(10)
        self.set_default_size(420, 200)

        self.controller = MaryumController(config, self._on_state)
        self.confirm_pending: str | None = None

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self.add(root)

        self.status_label = Gtk.Label(label="Status: disconnected")
        root.pack_start(self.status_label, False, False, 0)

        controls = Gtk.Box(spacing=6)
        root.pack_start(controls, False, False, 0)

        self.start_btn = Gtk.Button(label="Start Listening")
        self.start_btn.connect("clicked", lambda _btn: self.controller.start())
        controls.pack_start(self.start_btn, True, True, 0)

        self.stop_btn = Gtk.Button(label="Disconnect")
        self.stop_btn.connect("clicked", lambda _btn: self.controller.stop())
        controls.pack_start(self.stop_btn, True, True, 0)

        self.mute_btn = Gtk.ToggleButton(label="Mute Mic")
        self.mute_btn.connect("toggled", self._on_mute_toggled)
        controls.pack_start(self.mute_btn, True, True, 0)

        self.emergency_btn = Gtk.Button(label="EMERGENCY STOP")
        self.emergency_btn.connect("clicked", lambda _btn: self.controller.emergency_stop())
        root.pack_start(self.emergency_btn, False, False, 0)

        note = Gtk.Label(
            label=(
                "Risky actions (delete/install/sudo/network-sensitive) must be confirmed "
                "before execution."
            )
        )
        note.set_line_wrap(True)
        root.pack_start(note, False, False, 0)

        self.connect("destroy", self._on_destroy)

    def _on_state(self, state: AssistantState) -> None:
        Gtk.idle_add(self.status_label.set_text, f"Status: {state.value}")

    def _on_mute_toggled(self, button: Gtk.ToggleButton) -> None:
        self.controller.set_muted(button.get_active())

    def _on_destroy(self, _widget: Gtk.Widget) -> None:
        self.controller.stop()
        Gtk.main_quit()


def run_gui(config: MaryumConfig) -> None:
    win = MaryumWindow(config)
    win.show_all()
    Gtk.main()
