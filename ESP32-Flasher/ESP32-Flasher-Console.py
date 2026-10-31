from __future__ import annotations

import os
import queue
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

APP_TITLE = "ESP32 Firmware Installer"
BASE_DIR = Path(__file__).resolve().parent

BAUD_RATES = [
    "115200", "230400", "460800", "921600", "1500000",
    "2000000", "3000000"
]

class ESPInstallerGUI:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title(APP_TITLE)
        self.root.geometry("600x400")
        self.root.minsize(600, 400)
        self.root.configure(bg="#111111")

        # Disable mousewheel scrolling on all Comboboxes globally
        self.root.bind_class("TCombobox", "<MouseWheel>", lambda e: "break")

        self.events: queue.Queue = queue.Queue()
        self.running = False
        self.current_process = None

        self.bin_path = tk.StringVar(value="")
        self.offset = tk.StringVar(value="0x00000")
        self.port = tk.StringVar(value="")
        self.baud = tk.StringVar(value="921600")

        self._build_ui()
        self._refresh_ports()
        self.root.after(80, self._poll)

    def _build_ui(self) -> None:
        # Top Header
        top = tk.Frame(self.root, bg="#1a1a1a", height=50)
        top.pack(fill="x")
        top.pack_propagate(False)

        tk.Label(
            top, text="ESP32 FIRMWARE INSTALLER",
            font=("Segoe UI", 12, "bold"),
            fg="#eeeeee", bg="#1a1a1a",
        ).pack(side="left", padx=16)

        self.status_var = tk.StringVar(value="Ready")
        tk.Label(
            top, textvariable=self.status_var,
            font=("Segoe UI", 9), fg="#888888", bg="#1a1a1a",
        ).pack(side="right", padx=16)

        # Main Form Area
        form = tk.Frame(self.root, bg="#111111", padx=16, pady=16)
        form.pack(fill="x")

        # Firmware Binary File
        tk.Label(form, text="Firmware (.bin)", fg="#aaaaaa", bg="#111111", font=("Segoe UI", 9)).grid(row=0, column=0, sticky="w", pady=4)
        file_row = tk.Frame(form, bg="#111111")
        file_row.grid(row=1, column=0, columnspan=4, sticky="ew", pady=(0, 10))
        
        tk.Entry(file_row, textvariable=self.bin_path, bg="#0d0d0d", fg="white", insertbackground="white", relief="flat", font=("Consolas", 10)).pack(side="left", fill="x", expand=True, ipady=4, padx=(0, 6))
        tk.Button(file_row, text="Browse", font=("Segoe UI", 9), fg="#ccc", bg="#2a2a2a", relief="flat", padx=12, cursor="hand2", command=self._browse_bin).pack(side="right")

        # Offset, Baud Rate, COM Port
        tk.Label(form, text="Flash Offset", fg="#aaaaaa", bg="#111111", font=("Segoe UI", 9)).grid(row=2, column=0, sticky="w", pady=4)
        tk.Label(form, text="Baud Rate", fg="#aaaaaa", bg="#111111", font=("Segoe UI", 9)).grid(row=2, column=1, sticky="w", pady=4, padx=(10, 0))
        tk.Label(form, text="COM Port", fg="#aaaaaa", bg="#111111", font=("Segoe UI", 9)).grid(row=2, column=2, sticky="w", pady=4, padx=(10, 0))

        tk.Entry(form, textvariable=self.offset, bg="#0d0d0d", fg="white", insertbackground="white", relief="flat", font=("Consolas", 10), width=16).grid(row=3, column=0, sticky="w", ipady=4, pady=(0, 16))
        
        baud_box = ttk.Combobox(form, textvariable=self.baud, values=BAUD_RATES, width=14, state="readonly")
        baud_box.grid(row=3, column=1, sticky="w", pady=(0, 16), padx=(10, 0))

        # Port Selection Row
        port_frame = tk.Frame(form, bg="#111111")
        port_frame.grid(row=3, column=2, sticky="w", pady=(0, 16), padx=(10, 0))
        
        self.port_box = ttk.Combobox(port_frame, textvariable=self.port, width=14)
        self.port_box.pack(side="left", padx=(0, 4))
        tk.Button(port_frame, text="↻", font=("Segoe UI", 9), fg="#ccc", bg="#2a2a2a", relief="flat", width=3, cursor="hand2", command=self._refresh_ports).pack(side="left")

        # Flash Action Button
        self.run_btn = tk.Button(
            form, text="▶  FLASH FIRMWARE",
            font=("Segoe UI", 11, "bold"),
            fg="white", bg="#16a34a",
            activeforeground="white", activebackground="#22c55e",
            relief="flat", padx=20, pady=8,
            cursor="hand2",
            command=self._start_flash,
        )
        self.run_btn.grid(row=3, column=3, sticky="e", padx=(20, 0))
        form.columnconfigure(3, weight=1)

        # Console Output Box
        console_frame = tk.Frame(self.root, bg="#1a1a1a")
        console_frame.pack(fill="both", expand=True, padx=16, pady=(0, 16))

        header = tk.Frame(console_frame, bg="#1a1a1a")
        header.pack(fill="x", padx=8, pady=(6, 2))
        tk.Label(header, text="Flash Output Logs", fg="#888888", bg="#1a1a1a", font=("Segoe UI", 9)).pack(side="left")
        tk.Button(header, text="Clear", font=("Segoe UI", 8), fg="#aaaaaa", bg="#2a2a2a", relief="flat", padx=8, pady=2, cursor="hand2", command=self._clear_output).pack(side="right")

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

    def _refresh_ports(self) -> None:
        ports = []
        try:
            import serial.tools.list_ports
            # Exclude COM1 (legacy phantom port on Windows)
            ports = [p.device for p in serial.tools.list_ports.comports() if p.device.upper() != "COM1"]
        except ImportError:
            messagebox.showinfo("pyserial required", "Install pyserial using:\npip install pyserial")
            return

        self.port_box["values"] = ports
        if ports:
            if self.port.get() not in ports:
                self.port.set(ports[0])
            self.status_var.set(f"{len(ports)} port(s) found")
        else:
            self.status_var.set("No ports found")

    def _browse_bin(self) -> None:
        path = filedialog.askopenfilename(
            filetypes=[("Binary Firmware", "*.bin"), ("All files", "*.*")]
        )
        if path:
            self.bin_path.set(path)

    def _start_flash(self) -> None:
        if self.running:
            messagebox.showwarning("Busy", "Flashing is already in progress.")
            return

        bin_file = self.bin_path.get().strip()
        if not bin_file or not Path(bin_file).is_file():
            messagebox.showerror("Missing File", "Please select a valid firmware (.bin) file.")
            return

        port = self.port.get().strip()
        if not port:
            messagebox.showerror("Missing Port", "Please select a valid COM port.")
            return

        offset = self.offset.get().strip() or "0x10000"
        baud = self.baud.get().strip() or "921600"

        # Resolve path to local esptool.exe
        esptool_path = BASE_DIR / "esptool.exe"
        if not esptool_path.is_file():
            messagebox.showerror("Missing esptool.exe", f"Could not find esptool.exe in:\n{BASE_DIR}")
            return

        # Exact command construction:
        # esptool.exe --chip auto --port COMxx --baud 921600 --before default-reset --after hard-reset write-flash offset binfile
        args = [
            str(esptool_path),
            "--chip", "auto",
            "--port", port,
            "--baud", baud,
            "--before", "default-reset",
            "--after", "hard-reset",
            "write-flash",
            offset,
            bin_file
        ]

        self.running = True
        self.run_btn.configure(state="disabled", bg="#555555")
        self.status_var.set("Flashing…")

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
                        self.status_var.set("Flash Successful!")
                        self._append(f"\n[SUCCESS] Exit code {data}\n\n\n", "success")
                        messagebox.showinfo("Success", "Firmware flashed successfully!")
                    else:
                        self.status_var.set(f"Flash Failed ({data})")
                        self._append(f"\n[ERROR] Exit code {data}\n\n\n", "error")
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

def main() -> None:
    root = tk.Tk()
    ESPInstallerGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
