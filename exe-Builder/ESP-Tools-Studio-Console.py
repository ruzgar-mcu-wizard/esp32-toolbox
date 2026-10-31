from __future__ import annotations

import os
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "ESP Tools Studio"
BASE_DIR = Path(__file__).resolve().parent

CHIPS = [
    "auto", "esp8266", "esp32", "esp32s2", "esp32s3",
    "esp32c3", "esp32c2", "esp32c6", "esp32c61",
    "esp32c5", "esp32h2", "esp32h21", "esp32p4",
    "esp32h4", "esp32s31",
]

BAUD_RATES = [
    "115200", "230400", "460800", "921600", "1500000",
    "2000000", "3000000"
]

BEFORE_OPTIONS = {
    "5.5.0": [
        "default-reset", "usb-reset", "no-reset", "no-reset-no-sync"
    ],
    "4.12.0": [
        "default_reset", "usb_reset", "no_reset", "no_reset_no_sync"
    ],
}

AFTER_OPTIONS = {
    "5.5.0": [
        "hard-reset", "soft-reset", "no-reset", "no-reset-stub", "watchdog-reset"
    ],
    "4.12.0": [
        "hard_reset", "soft_reset", "no_reset", "no_reset_stub", "watchdog_reset",
    ],
}

TOOLS = {
    "esptool":   {"5.5.0": "esptool.exe",   "4.12.0": "esptool_4.12.exe"},
    "espsecure": {"5.5.0": "espsecure.exe", "4.12.0": "espsecure_4.12.exe"},
    "espefuse":  {"5.5.0": "espefuse.exe",  "4.12.0": "espefuse_4.12.exe"},
}

ESPTOOL_COMMANDS = {
    "5.5.0": [
        "write-flash", "read-flash", "erase-flash", "erase-region",
        "read-mac", "flash-id", "elf2image", "image-info", "merge-bin",
        "version", "verify-flash", "load-ram", "dump-mem", "read-mem",
        "write-mem", "read-flash-status", "write-flash-status",
        "read-flash-sfdp", "get-security-info", "chip-id", "run",
    ],
    "4.12.0": [
        "write_flash", "read_flash", "erase_flash", "erase_region",
        "read_mac", "flash_id", "elf2image", "image_info", "merge_bin",
        "version", "verify_flash", "load_ram", "dump_mem", "read_mem",
        "write_mem", "read_flash_status", "write_flash_status",
        "read_flash_sfdp", "get_security_info", "chip_id", "run",
    ],
}

ESPSECURE_COMMANDS = [
    "digest_secure_bootloader", "generate_signing_key", "sign_data",
    "verify_signature", "extract_public_key", "digest_rsa_public_key",
    "digest_sbv2_public_key", "signature_info_v2", "digest_private_key",
    "generate_flash_encryption_key", "decrypt_flash_data", "encrypt_flash_data",
]

ESPEFUSE_COMMANDS = [
    "burn_efuse", "read_protect_efuse", "write_protect_efuse",
    "burn_block_data", "burn_bit", "adc_info", "dump", "summary",
    "execute_scripts", "check_error", "burn_key", "burn_key_digest",
    "set_flash_voltage", "burn_custom_mac", "get_custom_mac",
]

DESTRUCTIVE_EFUSE = {
    "burn_efuse", "read_protect_efuse", "write_protect_efuse",
    "burn_block_data", "burn_bit", "burn_key", "burn_key_digest",
    "set_flash_voltage", "burn_custom_mac", "execute_scripts",
}
ERASE_COMMANDS = {"erase-flash", "erase_flash", "erase-region", "erase_region"}


class ScrollableFrame(tk.Frame):
    """Simple vertical scrollable frame."""
    def __init__(self, parent, bg="#1a1a1a", **kwargs):
        super().__init__(parent, bg=bg, **kwargs)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.inner = tk.Frame(self.canvas, bg=bg)

        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Leave>", self._unbind_mousewheel)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _bind_mousewheel(self, event):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbind_mousewheel(self, event):
        self.canvas.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ESPToolsGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("1200x800")
        self.root.minsize(1000, 680)
        self.root.configure(bg="#111111")

        # Disable mousewheel scrolling on all Comboboxes globally
        self.root.bind_class("TCombobox", "<MouseWheel>", lambda e: "break")

        self.events: queue.Queue = queue.Queue()
        self.running = False
        self.current_process = None

        self.version = tk.StringVar(value="5.5.0")
        self.tool = tk.StringVar(value="esptool")
        self.chip = tk.StringVar(value="auto")
        self.port = tk.StringVar(value="")
        self.baud = tk.StringVar(value="115200")
        self.before = tk.StringVar(value=BEFORE_OPTIONS["5.5.0"][0])
        self.after = tk.StringVar(value=AFTER_OPTIONS["5.5.0"][0])

        self.no_stub = tk.BooleanVar(value=False)
        self.verbose = tk.BooleanVar(value=False)
        self.trace = tk.BooleanVar(value=False)
        self.silent = tk.BooleanVar(value=False)
        self.debug = tk.BooleanVar(value=False)
        self.virt = tk.BooleanVar(value=False)
        self.postpone = tk.BooleanVar(value=False)
        self.do_not_confirm = tk.BooleanVar(value=False)

        self.command = tk.StringVar()
        self.extra_args = tk.StringVar()
        self.file_path = tk.StringVar()
        self.second_file = tk.StringVar()
        self.output_path = tk.StringVar()
        self.offset = tk.StringVar(value="0x10000")
        self.size = tk.StringVar(value="0x100000")

        # Specific fields for espsecure/espefuse GUI interaction
        self.secure_key_path = tk.StringVar()
        self.secure_input_path = tk.StringVar()
        self.secure_output_path = tk.StringVar()
        
        self.efuse_field = tk.StringVar()
        self.efuse_value = tk.StringVar()

        self._build()
        self._refresh_commands()
        self._refresh_ports()
        self._update_preview()
        self.root.after(80, self._poll)

    def _build(self) -> None:
        # Top bar
        top = tk.Frame(self.root, bg="#1a1a1a", height=48)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(
            top, text="ESP TOOLS STUDIO",
            font=("Segoe UI", 14, "bold"),
            fg="#eeeeee", bg="#1a1a1a",
        ).pack(side="left", padx=16)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            top, textvariable=self.status_var,
            font=("Segoe UI", 10), fg="#888888", bg="#1a1a1a",
        ).pack(side="right", padx=16)

        # Tool selector
        tool_bar = tk.Frame(self.root, bg="#111111", pady=8)
        tool_bar.pack(fill="x", padx=12)

        self.tool_btns = {}
        for name in ("esptool", "espsecure", "espefuse"):
            btn = tk.Button(
                tool_bar,
                text=name.upper(),
                font=("Segoe UI", 10, "bold"),
                fg="#cccccc", bg="#222222",
                activeforeground="white", activebackground="#333333",
                relief="flat", padx=18, pady=6,
                cursor="hand2",
                command=lambda n=name: self._select_tool(n),
            )
            btn.pack(side="left", padx=(0, 6))
            self.tool_btns[name] = btn

        tk.Label(tool_bar, text="Version", fg="#888888", bg="#111111",
                 font=("Segoe UI", 9)).pack(side="left", padx=(20, 6))
        ver = ttk.Combobox(tool_bar, textvariable=self.version,
                           values=["5.5.0", "4.12.0"], width=8, state="readonly")
        ver.pack(side="left")
        self.version.trace_add("write", lambda *_: self._on_version_changed())

        self._highlight_tool("esptool")

        # Main area
        main = tk.Frame(self.root, bg="#111111")
        main.pack(fill="both", expand=True, padx=12, pady=(4, 8))

        # Left panel (scrollable)
        left_container = tk.Frame(main, bg="#1a1a1a", width=250)
        left_container.pack(side="left", fill="y", padx=(0, 10))
        left_container.pack_propagate(False)

        self.left_scroll = ScrollableFrame(left_container, bg="#1a1a1a")
        self.left_scroll.pack(fill="both", expand=True)
        self._build_left(self.left_scroll.inner)

        # Right side
        right = tk.Frame(main, bg="#111111")
        right.pack(side="left", fill="both", expand=True)

        # Content (scrollable)
        self.content_container = tk.Frame(right, bg="#1a1a1a")
        self.content_container.pack(fill="both", expand=True)

        self.content_scroll = ScrollableFrame(self.content_container, bg="#1a1a1a")
        self.content_scroll.pack(fill="both", expand=True)

        self.pages = {}
        self._build_esptool_page()
        self._build_espsecure_page()
        self._build_espefuse_page()
        self._show_page("esptool")

        # Command bar
        cmd_frame = tk.Frame(self.root, bg="#1a1a1a", pady=8)
        cmd_frame.pack(fill="x", padx=12)

        tk.Label(cmd_frame, text="Command", fg="#888888", bg="#1a1a1a",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=10)

        self.preview = tk.Text(
            cmd_frame, height=2, wrap="word",
            bg="#0d0d0d", fg="#4ade80",
            font=("Consolas", 9),
            relief="flat", padx=8, pady=6,
            highlightthickness=0,
        )
        self.preview.pack(fill="x", padx=10, pady=(2, 8))
        self.preview.configure(state="disabled")

        btn_row = tk.Frame(cmd_frame, bg="#1a1a1a")
        btn_row.pack(fill="x", padx=10)

        tk.Button(
            btn_row, text="Clear Output",
            font=("Segoe UI", 9),
            fg="#cccccc", bg="#2a2a2a",
            activeforeground="white", activebackground="#3a3a3a",
            relief="flat", padx=12, pady=5,
            cursor="hand2",
            command=self._clear_output,
        ).pack(side="left")

        self.run_btn = tk.Button(
            btn_row, text="▶  RUN",
            font=("Segoe UI", 11, "bold"),
            fg="white", bg="#16a34a",
            activeforeground="white", activebackground="#22c55e",
            relief="flat", padx=28, pady=8,
            cursor="hand2",
            command=self._run,
        )
        self.run_btn.pack(side="right")

        # Console
        console_frame = tk.Frame(self.root, bg="#1a1a1a")
        console_frame.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        header = tk.Frame(console_frame, bg="#1a1a1a")
        header.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(header, text="Output", fg="#888888", bg="#1a1a1a",
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Button(
            header, text="Copy",
            font=("Segoe UI", 8),
            fg="#aaaaaa", bg="#2a2a2a",
            relief="flat", padx=8, pady=2,
            cursor="hand2",
            command=self._copy_output,
        ).pack(side="right")

        self.output = tk.Text(
            console_frame, wrap="word",
            bg="#0d0d0d", fg="#d4d4d4",
            font=("Consolas", 9),
            relief="flat", padx=10, pady=8,
            highlightthickness=0,
        )
        scroll = ttk.Scrollbar(console_frame, orient="vertical", command=self.output.yview)
        self.output.configure(yscrollcommand=scroll.set)
        self.output.pack(side="left", fill="both", expand=True, padx=(8, 0), pady=(0, 8))
        scroll.pack(side="right", fill="y", pady=(0, 8), padx=(0, 8))

        self.output.tag_configure("error", foreground="#f87171")
        self.output.tag_configure("success", foreground="#4ade80")
        self.output.tag_configure("info", foreground="#60a5fa")

    def _build_left(self, parent: tk.Frame) -> None:
        def section(title: str) -> None:
            tk.Label(parent, text=title, fg="#4ade80", bg="#1a1a1a",
                     font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=12, pady=(14, 4))

        def labeled(label: str, widget) -> None:
            tk.Label(parent, text=label, fg="#888888", bg="#1a1a1a",
                     font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(6, 1))
            widget.pack(fill="x", padx=12)

        section("CONNECTION")

        chip = ttk.Combobox(parent, textvariable=self.chip, values=CHIPS)
        labeled("Chip", chip)
        self.chip.trace_add("write", lambda *_: self._update_preview())

        tk.Label(parent, text="Port", fg="#888888", bg="#1a1a1a",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(6, 1))
        port_row = tk.Frame(parent, bg="#1a1a1a")
        port_row.pack(fill="x", padx=12)
        self.port_box = ttk.Combobox(port_row, textvariable=self.port)
        self.port_box.pack(side="left", fill="x", expand=True)
        self.port.trace_add("write", lambda *_: self._update_preview())
        tk.Button(
            port_row, text="↻", font=("Segoe UI", 9),
            fg="#cccccc", bg="#2a2a2a", relief="flat",
            width=3, cursor="hand2",
            command=self._refresh_ports,
        ).pack(side="right", padx=(4, 0))

        baud = ttk.Combobox(parent, textvariable=self.baud, values=BAUD_RATES)
        labeled("Baud", baud)
        self.baud.trace_add("write", lambda *_: self._update_preview())

        ver = self.version.get()
        self.before_box = ttk.Combobox(parent, textvariable=self.before, values=BEFORE_OPTIONS.get(ver, []))
        labeled("Before", self.before_box)
        self.before.trace_add("write", lambda *_: self._update_preview())

        self.after_box = ttk.Combobox(parent, textvariable=self.after, values=AFTER_OPTIONS.get(ver, []))
        labeled("After", self.after_box)
        self.after.trace_add("write", lambda *_: self._update_preview())

        section("OPTIONS")

        opts = [
            ("No stub", self.no_stub),
            ("Verbose", self.verbose),
            ("Trace", self.trace),
            ("Silent", self.silent),
            ("Debug", self.debug),
            ("Virtual", self.virt),
            ("Postpone", self.postpone),
            ("Skip confirm", self.do_not_confirm),
        ]
        for text, var in opts:
            tk.Checkbutton(
                parent, text=text, variable=var,
                fg="#cccccc", bg="#1a1a1a",
                selectcolor="#222222",
                activeforeground="white", activebackground="#1a1a1a",
                font=("Segoe UI", 9),
                command=self._update_preview,
            ).pack(anchor="w", padx=12, pady=1)

        # spacer so last items aren't stuck to the bottom edge
        tk.Frame(parent, bg="#1a1a1a", height=20).pack()

    def _build_esptool_page(self) -> None:
        page = tk.Frame(self.content_scroll.inner, bg="#1a1a1a")
        self.pages["esptool"] = page

        tk.Label(page, text="QUICK ACTIONS", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 8))

        grid = tk.Frame(page, bg="#1a1a1a")
        grid.pack(fill="x", padx=10)

        actions = [
            ("Write Flash", "write"),
            ("Read Flash", "read"),
            ("Erase Flash", "erase"),
            ("Erase Region", "erase_region"),
            ("Verify", "verify"),
            ("Flash ID", "flash_id"),
            ("Read MAC", "read_mac"),
            ("Chip ID", "chip_id"),
            ("Security Info", "security"),
        ]
        for i, (text, action) in enumerate(actions):
            b = tk.Button(
                grid, text=text,
                font=("Segoe UI", 9),
                fg="#ddd", bg="#2a2a2a",
                activeforeground="white", activebackground="#3a3a3a",
                relief="flat", padx=8, pady=6,
                cursor="hand2",
                command=lambda a=action: self._flash_action(a),
            )
            b.grid(row=i // 3, column=i % 3, sticky="ew", padx=3, pady=3)
        for c in range(3):
            grid.columnconfigure(c, weight=1)

        tk.Label(page, text="FILES", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(16, 6))

        def file_row(label, var, save=False):
            row = tk.Frame(page, bg="#1a1a1a")
            row.pack(fill="x", padx=12, pady=3)
            tk.Label(row, text=label, fg="#888", bg="#1a1a1a",
                     font=("Segoe UI", 9), width=12, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, bg="#0d0d0d", fg="white",
                     insertbackground="white", relief="flat").pack(
                side="left", fill="x", expand=True, padx=6, ipady=3)
            if save:
                tk.Button(row, text="Save", font=("Segoe UI", 8),
                          fg="#ccc", bg="#2a2a2a", relief="flat", padx=8,
                          cursor="hand2", command=self._save_output).pack(side="right")
            else:
                tk.Button(row, text="Browse", font=("Segoe UI", 8),
                          fg="#ccc", bg="#2a2a2a", relief="flat", padx=8,
                          cursor="hand2",
                          command=lambda: self._browse(var)).pack(side="right")

        file_row("Firmware", self.file_path)
        file_row("Second file", self.second_file)
        file_row("Output", self.output_path, save=True)

        tk.Label(page, text="ADDRESS", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(14, 6))
        addr = tk.Frame(page, bg="#1a1a1a")
        addr.pack(fill="x", padx=12)
        tk.Label(addr, text="Offset", fg="#888", bg="#1a1a1a",
                 font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(addr, textvariable=self.offset, width=14,
                 bg="#0d0d0d", fg="white", relief="flat").pack(side="left", padx=6, ipady=3)
        tk.Label(addr, text="Size", fg="#888", bg="#1a1a1a",
                 font=("Segoe UI", 9)).pack(side="left", padx=(12, 0))
        tk.Entry(addr, textvariable=self.size, width=14,
                 bg="#0d0d0d", fg="white", relief="flat").pack(side="left", padx=6, ipady=3)

        tk.Label(page, text="CUSTOM COMMAND", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(16, 6))
        self.cmd_box = ttk.Combobox(page, textvariable=self.command, state="readonly")
        self.cmd_box.pack(fill="x", padx=12, pady=(0, 4))
        self.cmd_box.bind("<<ComboboxSelected>>", lambda e: self._update_preview())

        tk.Entry(page, textvariable=self.extra_args,
                 bg="#0d0d0d", fg="white", insertbackground="white",
                 relief="flat").pack(fill="x", padx=12, ipady=4)
        tk.Label(page, text="Extra arguments", fg="#666", bg="#1a1a1a",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(2, 20))

        self.command.trace_add("write", lambda *_: self._update_preview())
        self.extra_args.trace_add("write", lambda *_: self._update_preview())

    def _build_espsecure_page(self) -> None:
        page = tk.Frame(self.content_scroll.inner, bg="#1a1a1a")
        self.pages["espsecure"] = page

        tk.Label(page, text="ESPSECURE", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(16, 4))
        tk.Label(page, text="Signing, encryption and key utilities",
                 fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(anchor="w", padx=14)

        tk.Label(page, text="Command", fg="#888", bg="#1a1a1a",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=14, pady=(16, 2))
        self.secure_box = ttk.Combobox(page, textvariable=self.command, state="readonly")
        self.secure_box.pack(fill="x", padx=12)
        self.secure_box.bind("<<ComboboxSelected>>", lambda e: self._update_secure_preview())

        tk.Label(page, text="FILE PARAMETERS", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(16, 6))

        def secure_row(label, var):
            row = tk.Frame(page, bg="#1a1a1a")
            row.pack(fill="x", padx=12, pady=3)
            tk.Label(row, text=label, fg="#888", bg="#1a1a1a",
                     font=("Segoe UI", 9), width=12, anchor="w").pack(side="left")
            tk.Entry(row, textvariable=var, bg="#0d0d0d", fg="white",
                     insertbackground="white", relief="flat").pack(
                side="left", fill="x", expand=True, padx=6, ipady=3)
            tk.Button(row, text="Browse", font=("Segoe UI", 8),
                      fg="#ccc", bg="#2a2a2a", relief="flat", padx=8,
                      cursor="hand2",
                      command=lambda: self._browse(var)).pack(side="right")

        secure_row("Key File", self.secure_key_path)
        secure_row("Input File", self.secure_input_path)
        secure_row("Output File", self.secure_output_path)

        tk.Label(page, text="CUSTOM ARGUMENTS", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(16, 6))
        tk.Entry(page, textvariable=self.extra_args,
                 bg="#0d0d0d", fg="white", insertbackground="white",
                 relief="flat").pack(fill="x", padx=12, ipady=4)
        tk.Label(page, text="Extra arguments (e.g. --version 2)", fg="#666", bg="#1a1a1a",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(2, 20))

        self.secure_key_path.trace_add("write", lambda *_: self._update_secure_preview())
        self.secure_input_path.trace_add("write", lambda *_: self._update_secure_preview())
        self.secure_output_path.trace_add("write", lambda *_: self._update_secure_preview())
        self.extra_args.trace_add("write", lambda *_: self._update_preview())

    def _update_secure_preview(self) -> None:
        cmd = self.command.get()
        args = []
        
        # Build smart argument structure based on typical espsecure patterns
        if "key" in cmd and self.secure_key_path.get():
            args += ["--keyfile", self.secure_key_path.get()]
        if self.secure_output_path.get():
            if "sign" in cmd or "encrypt" in cmd or "decrypt" in cmd or "key" in cmd:
                args += ["--output", self.secure_output_path.get()]
        if self.secure_input_path.get():
            args.append(self.secure_input_path.get())

        if args:
            self.extra_args.set(subprocess.list2cmdline(args))
        self._update_preview()

    def _build_espefuse_page(self) -> None:
        page = tk.Frame(self.content_scroll.inner, bg="#1a1a1a")
        self.pages["espefuse"] = page

        tk.Label(page, text="ESPEFUSE", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(16, 4))
        tk.Label(page, text="eFuse operations - some are irreversible",
                 fg="#888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(anchor="w", padx=14)

        tk.Label(page, text="Command", fg="#888", bg="#1a1a1a",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=14, pady=(16, 2))
        self.efuse_box = ttk.Combobox(page, textvariable=self.command, state="readonly")
        self.efuse_box.pack(fill="x", padx=12)
        self.efuse_box.bind("<<ComboboxSelected>>", lambda e: self._update_efuse_preview())

        tk.Label(page, text="EFUSE PARAMETERS", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(16, 6))

        efuse_row = tk.Frame(page, bg="#1a1a1a")
        efuse_row.pack(fill="x", padx=12, pady=3)
        tk.Label(efuse_row, text="eFuse / Field", fg="#888", bg="#1a1a1a",
                 font=("Segoe UI", 9), width=12, anchor="w").pack(side="left")
        tk.Entry(efuse_row, textvariable=self.efuse_field, bg="#0d0d0d", fg="white",
                 insertbackground="white", relief="flat").pack(
            side="left", fill="x", expand=True, padx=6, ipady=3)

        efuse_val_row = tk.Frame(page, bg="#1a1a1a")
        efuse_val_row.pack(fill="x", padx=12, pady=3)
        tk.Label(efuse_val_row, text="Value / Data", fg="#888", bg="#1a1a1a",
                 font=("Segoe UI", 9), width=12, anchor="w").pack(side="left")
        tk.Entry(efuse_val_row, textvariable=self.efuse_value, bg="#0d0d0d", fg="white",
                 insertbackground="white", relief="flat").pack(
            side="left", fill="x", expand=True, padx=6, ipady=3)

        tk.Label(page, text="CUSTOM ARGUMENTS", fg="#4ade80", bg="#1a1a1a",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(16, 6))
        tk.Entry(page, textvariable=self.extra_args,
                 bg="#0d0d0d", fg="white", insertbackground="white",
                 relief="flat").pack(fill="x", padx=12, ipady=4)
        tk.Label(page, text="Extra arguments", fg="#666", bg="#1a1a1a",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(2, 20))

        self.efuse_field.trace_add("write", lambda *_: self._update_efuse_preview())
        self.efuse_value.trace_add("write", lambda *_: self._update_efuse_preview())
        self.extra_args.trace_add("write", lambda *_: self._update_preview())

    def _update_efuse_preview(self) -> None:
        field = self.efuse_field.get().strip()
        val = self.efuse_value.get().strip()
        args = []
        if field:
            args.append(field)
        if val:
            args.append(val)
        if args:
            self.extra_args.set(subprocess.list2cmdline(args))
        self._update_preview()

    def _select_tool(self, name: str) -> None:
        self.tool.set(name)
        self._highlight_tool(name)
        self._show_page(name)
        self._refresh_commands()

    def _highlight_tool(self, name: str) -> None:
        for key, btn in self.tool_btns.items():
            if key == name:
                btn.configure(bg="#16a34a", fg="white")
            else:
                btn.configure(bg="#222222", fg="#cccccc")

    def _show_page(self, name: str) -> None:
        for key, page in self.pages.items():
            page.pack_forget()
        self.pages[name].pack(fill="both", expand=True)
        # force scrollregion update
        self.content_scroll.inner.update_idletasks()
        self.content_scroll.canvas.configure(scrollregion=self.content_scroll.canvas.bbox("all"))

    def _refresh_ports(self) -> None:
        ports = []
        try:
            import serial.tools.list_ports
            # Filter out COM1 (legacy phantom port on Windows)
            ports = [p.device for p in serial.tools.list_ports.comports() if p.device.upper() != "COM1"]
        except ImportError:
            messagebox.showinfo(
                "pyserial required",
                "Install pyserial to detect ports:\n\npy -m pip install pyserial",
            )
            return

        self.port_box["values"] = ports
        if ports:
            if self.port.get() not in ports:
                self.port.set(ports[0])
            self.status_var.set(f"{len(ports)} port(s) found")
        else:
            self.status_var.set("No ports found")
        self._update_preview()

    def _browse(self, var: tk.StringVar) -> None:
        path = filedialog.askopenfilename(
            filetypes=[
                ("Files", "*.bin *.elf *.hex *.pem *.key"),
                ("All files", "*.*"),
            ]
        )
        if path:
            var.set(path)

    def _save_output(self) -> None:
        path = filedialog.asksaveasfilename(
            defaultextension=".bin",
            filetypes=[("Binary", "*.bin"), ("All files", "*.*")],
        )
        if path:
            self.output_path.set(path)

    def _flash_action(self, action: str) -> None:
        is_new = self.version.get() == "5.5.0"
        mapping = {
            "write": "write-flash" if is_new else "write_flash",
            "read": "read-flash" if is_new else "read_flash",
            "erase": "erase-flash" if is_new else "erase_flash",
            "erase_region": "erase-region" if is_new else "erase_region",
            "verify": "verify-flash" if is_new else "verify_flash",
            "flash_id": "flash-id" if is_new else "flash_id",
            "read_mac": "read-mac" if is_new else "read_mac",
            "chip_id": "chip-id" if is_new else "chip_id",
            "security": "get-security-info" if is_new else "get_security_info",
        }
        cmd = mapping[action]
        args = []

        if action in ("write", "verify"):
            if not self.file_path.get():
                messagebox.showwarning("Missing file", "Select a firmware file first.")
                return
            args = [self.offset.get(), self.file_path.get()]
        elif action == "read":
            if not self.output_path.get():
                messagebox.showwarning("Missing output", "Choose an output file first.")
                return
            args = [self.offset.get(), self.size.get(), self.output_path.get()]
        elif action == "erase_region":
            args = [self.offset.get(), self.size.get()]

        self.command.set(cmd)
        self.extra_args.set(subprocess.list2cmdline(args))
        self._update_preview()
        self._run()

    def _on_version_changed(self) -> None:
        ver = self.version.get()

        # Update before and after dropdown options
        before_opts = BEFORE_OPTIONS.get(ver, [])
        after_opts = AFTER_OPTIONS.get(ver, [])

        if hasattr(self, "before_box"):
            self.before_box["values"] = before_opts
        if hasattr(self, "after_box"):
            self.after_box["values"] = after_opts

        if self.before.get() not in before_opts and before_opts:
            self.before.set(before_opts[0])
        if self.after.get() not in after_opts and after_opts:
            self.after.set(after_opts[0])

        self._refresh_commands()

    def _refresh_commands(self) -> None:
        tool = self.tool.get()
        ver = self.version.get()

        if tool == "esptool":
            cmds = ESPTOOL_COMMANDS[ver]
            box = getattr(self, "cmd_box", None)
        elif tool == "espsecure":
            cmds = ESPSECURE_COMMANDS
            box = getattr(self, "secure_box", None)
        else:
            cmds = ESPEFUSE_COMMANDS
            box = getattr(self, "efuse_box", None)

        if box is not None:
            box["values"] = cmds
        if self.command.get() not in cmds:
            self.command.set(cmds[0] if cmds else "")
        self._update_preview()

    def _get_exe(self) -> Path:
        return BASE_DIR / TOOLS[self.tool.get()][self.version.get()]

    def _common_args(self) -> list[str]:
        tool = self.tool.get()
        args = []
        if tool in ("esptool", "espefuse"):
            args += ["--chip", self.chip.get()]
            if self.port.get().strip():
                args += ["--port", self.port.get().strip()]
            if self.baud.get().strip():
                args += ["--baud", self.baud.get().strip()]

            if tool == "esptool":
                if self.before.get():
                    args += ["--before", self.before.get()]
                if self.after.get():
                    args += ["--after", self.after.get()]
                if self.no_stub.get():
                    args.append("--no-stub")
                if self.trace.get():
                    args.append("--trace")
                if self.verbose.get():
                    args.append("--verbose")
                if self.silent.get():
                    args.append("--silent")
            else:
                if self.debug.get():
                    args.append("--debug")
                if self.virt.get():
                    args.append("--virt")
                if self.do_not_confirm.get():
                    args.append("--do-not-confirm")
                if self.postpone.get():
                    args.append("--postpone")
        return args

    def _parse_extra(self, text: str) -> list[str]:
        if not text.strip():
            return []
        if os.name == "nt":
            import ctypes
            from ctypes import wintypes
            shell32 = ctypes.WinDLL("shell32", use_last_error=True)
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            shell32.CommandLineToArgvW.argtypes = [wintypes.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
            shell32.CommandLineToArgvW.restype = ctypes.POINTER(wintypes.LPWSTR)
            kernel32.LocalFree.argtypes = [wintypes.HLOCAL]
            kernel32.LocalFree.restype = wintypes.HLOCAL
            argc = ctypes.c_int()
            argv = shell32.CommandLineToArgvW("dummy " + text, ctypes.byref(argc))
            if not argv:
                raise ValueError("Could not parse arguments")
            try:
                return [argv[i] for i in range(1, argc.value)]
            finally:
                kernel32.LocalFree(argv)
        import shlex
        return shlex.split(text)

    def _build_command(self) -> list[str]:
        exe = self._get_exe()
        if not exe.is_file():
            raise FileNotFoundError(f"Executable not found:\n{exe}")
        cmd = self.command.get().strip()
        if not cmd:
            raise ValueError("No command selected")
        return [str(exe)] + self._common_args() + [cmd] + self._parse_extra(self.extra_args.get())

    def _update_preview(self) -> None:
        if not hasattr(self, "preview"):
            return
        try:
            text = subprocess.list2cmdline(self._build_command())
        except Exception as e:
            text = f"{self.command.get()} {self.extra_args.get()}\n({e})"
        self.preview.configure(state="normal")
        self.preview.delete("1.0", "end")
        self.preview.insert("1.0", text)
        self.preview.configure(state="disabled")

    def _run(self) -> None:
        if self.running:
            messagebox.showwarning("Busy", "A command is already running.")
            return
        try:
            args = self._build_command()
        except Exception as e:
            messagebox.showerror("Cannot run", str(e))
            return

        tool = self.tool.get()
        cmd = self.command.get()

        if tool == "espefuse" and cmd in DESTRUCTIVE_EFUSE:
            if not messagebox.askyesno(
                "Irreversible operation",
                "This may permanently change eFuses and can brick the chip.\n\nContinue?",
                icon="warning",
            ):
                return

        if tool == "esptool" and cmd in ERASE_COMMANDS:
            if not messagebox.askyesno("Erase flash?", "This will erase flash data.\n\nContinue?", icon="warning"):
                return

        self.running = True
        self.run_btn.configure(state="disabled", bg="#555555")
        self.status_var.set("Running…")

        self._append("\n" + "─" * 60 + "\n", "info")
        self._append(subprocess.list2cmdline(args) + "\n\n", "info")

        threading.Thread(target=self._worker, args=(args,), daemon=True).start()

    def _worker(self, args: list[str]) -> None:
        try:
            flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            proc = subprocess.Popen(
                args,
                cwd=BASE_DIR,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
                creationflags=flags,
            )
            self.current_process = proc
            for line in iter(proc.stdout.readline, ""):
                self.events.put(("out", line))
            proc.stdout.close()
            self.events.put(("done", proc.wait()))
        except Exception as e:
            self.events.put(("err", str(e)))

    def _poll(self) -> None:
        try:
            while True:
                kind, data = self.events.get_nowait()
                if kind == "out":
                    self._append(data)
                elif kind == "done":
                    self.running = False
                    self.current_process = None
                    self.run_btn.configure(state="normal", bg="#16a34a")
                    if data == 0:
                        self.status_var.set("Completed")
                        self._append(f"\nExit code {data}\n", "success")
                    else:
                        self.status_var.set(f"Failed ({data})")
                        self._append(f"\nExit code {data}\n", "error")
                elif kind == "err":
                    self.running = False
                    self.current_process = None
                    self.run_btn.configure(state="normal", bg="#16a34a")
                    self.status_var.set("Error")
                    self._append(f"\nERROR: {data}\n", "error")
                    messagebox.showerror("Error", data)
        except queue.Empty:
            pass
        self.root.after(80, self._poll)

    def _append(self, text: str, tag: str | None = None) -> None:
        self.output.configure(state="normal")
        if tag:
            self.output.insert("end", text, tag)
        else:
            self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="normal")

    def _clear_output(self) -> None:
        self.output.delete("1.0", "end")

    def _copy_output(self) -> None:
        self.root.clipboard_clear()
        self.root.clipboard_append(self.output.get("1.0", "end-1c"))
        self.status_var.set("Copied")


def main() -> None:
    root = tk.Tk()
    ESPToolsGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()