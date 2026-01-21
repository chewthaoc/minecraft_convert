from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog

import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap.dialogs import Messagebox
from ttkbootstrap.scrolled import ScrolledText

from .converter import (
    ConversionResult,
    convert_batch,
    convert_world,
    list_target_versions,
)


class App(ttk.Frame):
    def __init__(self, master: ttk.Window) -> None:
        super().__init__(master)
        self.pack(fill=BOTH, expand=YES, padx=20, pady=20)
        
        # Configuration
        self.master = master
        self.master.minsize(800, 600)
        
        # Variables
        self._i18n = {
            "en": {
                "app_title": "Minecraft World Converter (Pro)",
                "header_title": "MC World Converter",
                "lang_label": "Language:",
                "tab_single": "Single Mode",
                "tab_batch": "Batch Mode",
                "log_frame": "System Log",
                "options_frame": "Settings",
                "direction_label": "Direction:",
                "target_ver_label": "Target Ver:",
                "force_repair": "Force Repair (Re-save chunks)",
                "input_world": "Input World:",
                "output_folder": "Output Folder:",
                "browse": "📁 Browse",
                "start_conversion": "🚀 Start Conversion",
                "batch_add": "➕ Add",
                "batch_remove": "➖ Remove",
                "batch_clear": "🗑️ Clear",
                "output_root": "Output Root Directory:",
                "batch_convert": "🚀 Batch Convert",
                "status_ready": "Ready",
                "status_running": "Running...",
                "status_finished": "Finished",
                "status_failed": "Failed",
                "warn_missing_paths": "Please provide both input and output paths.",
                "warn_input_error": "Input Error",
                "warn_output_nonempty": "Output folder is not empty and may be overwritten. Continue?",
                "warn_confirm_overwrite": "Confirm Overwrite",
                "warn_list_empty": "List is empty. Please add worlds.",
                "warn_select_output_root": "Please select an output root directory.",
                "msg_success": "Success",
                "msg_failure": "Failure",
                "latest": "Latest",
            },
            "zh": {
                "app_title": "Minecraft 存档转换工具 (Pro)",
                "header_title": "MC 存档转换器",
                "lang_label": "语言：",
                "tab_single": "单个模式",
                "tab_batch": "批量模式",
                "log_frame": "系统日志",
                "options_frame": "转换设置",
                "direction_label": "转换方向：",
                "target_ver_label": "目标版本：",
                "force_repair": "强制修复（重新保存区块）",
                "input_world": "输入存档：",
                "output_folder": "输出位置：",
                "browse": "📁 浏览",
                "start_conversion": "🚀 开始转换",
                "batch_add": "➕ 添加",
                "batch_remove": "➖ 移除",
                "batch_clear": "🗑️ 清空",
                "output_root": "输出根目录：",
                "batch_convert": "🚀 批量转换",
                "status_ready": "就绪",
                "status_running": "正在运行转换任务...",
                "status_finished": "任务完成",
                "status_failed": "任务失败",
                "warn_missing_paths": "请填写完整的输入和输出路径。",
                "warn_input_error": "输入错误",
                "warn_output_nonempty": "输出目录非空，可能会覆盖文件。是否继续？",
                "warn_confirm_overwrite": "确认覆盖",
                "warn_list_empty": "列表为空，请添加存档。",
                "warn_select_output_root": "请选择输出根目录。",
                "msg_success": "成功",
                "msg_failure": "失败",
                "latest": "最新",
            },
        }
        self.lang_var = tk.StringVar(value="en")
        self._status_key = "status_ready"
        self.input_var = tk.StringVar()
        self.output_var = tk.StringVar()
        self.direction_var = tk.StringVar(value="bedrock-to-java")
        self.version_var = tk.StringVar(value=self._t("latest"))
        self.batch_output_var = tk.StringVar()
        self.repair_var = tk.BooleanVar(value=False)
        self.status_var = tk.StringVar()
        
        # Internal State
        self._log_queue: queue.Queue[str] = queue.Queue()
        self._result_queue: queue.Queue[ConversionResult] = queue.Queue()
        self._worker: threading.Thread | None = None
        self._input_paths: list[str] = []

        # UI Construction
        self._setup_ui()
        
        # Logic Init
        self.direction_var.trace_add("write", lambda *_: self._refresh_versions())
        self._apply_language()
        self.after(100, self._poll_queues)

    def _t(self, key: str) -> str:
        lang = self.lang_var.get()
        return self._i18n.get(lang, self._i18n["en"]).get(key, key)

    def _set_status(self, key: str) -> None:
        self._status_key = key
        self.status_var.set(self._t(key))

    def _setup_ui(self) -> None:
        # --- Header ---
        header_frame = ttk.Frame(self)
        header_frame.pack(fill=X, pady=(0, 20))

        self.header_title_label = ttk.Label(
            header_frame,
            font=("Helvetica", 24, "bold"),
        )
        self.header_title_label.pack(side=LEFT)
        
        ttk.Label(
            header_frame,
            text="v0.1.0",
        ).pack(side=LEFT, padx=10, pady=(12, 0))

        lang_frame = ttk.Frame(header_frame)
        lang_frame.pack(side=RIGHT)
        self.lang_label = ttk.Label(lang_frame)
        self.lang_label.pack(side=LEFT, padx=(0, 6))
        self._lang_map = {"English": "en", "中文": "zh"}
        self._lang_display = {v: k for k, v in self._lang_map.items()}
        self.lang_display_var = tk.StringVar(value=self._lang_display[self.lang_var.get()])
        self.lang_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.lang_display_var,
            values=list(self._lang_map.keys()),
            state="readonly",
            width=9,
        )
        self.lang_combo.pack(side=LEFT)
        self.lang_combo.bind("<<ComboboxSelected>>", self._on_language_selected)

        # --- Main Content (Tabs) ---
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=BOTH, expand=YES, pady=(0, 20))

        # Tab 1: Single Mode
        self.tab_single = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_single, text="")
        self._setup_single_tab()

        # Tab 2: Batch Mode
        self.tab_batch = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_batch, text="")
        self._setup_batch_tab()

        # --- Settings/Log Area ---
        # Shared Log Area at bottom
        self.log_frame = ttk.LabelFrame(self)
        log_frame = self.log_frame
        log_frame.pack(fill=BOTH, expand=YES)
        
        self.log_text = ScrolledText(log_frame, height=8, autohide=True)
        self.log_text.pack(fill=BOTH, expand=YES)

        # Status Bar
        status_bar = ttk.Frame(self)
        status_bar.pack(fill=X, pady=(10, 0))
        ttk.Label(status_bar, textvariable=self.status_var).pack(side=LEFT)
        
        # REFACTOR: Move Options Up
        # Removing Notebook for a second to inject Options below Header
        self.notebook.pack_forget()
        
        self._setup_global_options()
        self.notebook.pack(fill=BOTH, expand=YES, pady=10)

    def _setup_global_options(self) -> None:
        self.opt_container = ttk.LabelFrame(self)
        opt_container = self.opt_container
        opt_container.pack(fill=X)

        # Grid layout for options
        opt_container.columnconfigure(1, weight=1)
        opt_container.columnconfigure(3, weight=1)

        # Row 0: Direction
        self.lbl_direction = ttk.Label(opt_container)
        self.lbl_direction.grid(row=0, column=0, sticky=E, padx=5, pady=5)
        
        dir_frame = ttk.Frame(opt_container)
        dir_frame.grid(row=0, column=1, sticky=W, padx=5)
        
        modes = [
            ("Bedrock → Java", "bedrock-to-java"),
            ("Java → Bedrock", "java-to-bedrock"),
            ("Java → Java", "java-to-java"),
            ("Bedrock → Bedrock", "bedrock-to-bedrock")
        ]
        
        for text, val in modes:
            ttk.Radiobutton(
                dir_frame,
                text=text,
                value=val,
                variable=self.direction_var,
            ).pack(side=LEFT, padx=2)

        # Row 0 (Right): Version
        self.lbl_target_ver = ttk.Label(opt_container)
        self.lbl_target_ver.grid(row=0, column=2, sticky=E, padx=5, pady=5)
        self.version_combo = ttk.Combobox(opt_container, textvariable=self.version_var, state="readonly", width=15)
        self.version_combo.grid(row=0, column=3, sticky=W, padx=5)

        # Row 1: Extra Options
        self.chk_force_repair = ttk.Checkbutton(
            opt_container,
            variable=self.repair_var,
        )
        self.chk_force_repair.grid(row=1, column=1, columnspan=3, sticky=W, padx=7, pady=10)

    def _setup_single_tab(self) -> None:
        # Input
        self.lbl_input = ttk.Label(self.tab_single)
        self.lbl_input.pack(anchor=W)
        input_frame = ttk.Frame(self.tab_single)
        input_frame.pack(fill=X, pady=(5, 15))
        
        ttk.Entry(input_frame, textvariable=self.input_var).pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        self.btn_browse_input = ttk.Button(input_frame, command=self._pick_input)
        self.btn_browse_input.pack(side=LEFT)

        # Output
        self.lbl_output = ttk.Label(self.tab_single)
        self.lbl_output.pack(anchor=W)
        output_frame = ttk.Frame(self.tab_single)
        output_frame.pack(fill=X, pady=(5, 20))
        
        ttk.Entry(output_frame, textvariable=self.output_var).pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        self.btn_browse_output = ttk.Button(output_frame, command=self._pick_output)
        self.btn_browse_output.pack(side=LEFT)

        # Action
        self.btn_convert_single = ttk.Button(
            self.tab_single,
            command=self._start_single_conversion,
            width=30,
        )
        self.btn_convert_single.pack(pady=10)

    def _setup_batch_tab(self) -> None:
        # List Area
        list_frame = ttk.Frame(self.tab_batch)
        list_frame.pack(fill=BOTH, expand=YES, pady=(0, 10))
        
        self.batch_list = tk.Listbox(list_frame, height=5, selectmode="extended", borderwidth=1, relief="solid")
        self.batch_list.pack(side=LEFT, fill=BOTH, expand=YES)
        
        toolbar = ttk.Frame(list_frame)
        toolbar.pack(side=LEFT, fill=Y, padx=5)
        
        self.btn_add = ttk.Button(toolbar, command=self._add_batch_input, width=8)
        self.btn_add.pack(pady=2)
        self.btn_remove = ttk.Button(toolbar, command=self._remove_batch_input, width=8)
        self.btn_remove.pack(pady=2)
        self.btn_clear = ttk.Button(toolbar, command=self._clear_batch_inputs, width=8)
        self.btn_clear.pack(pady=2)

        # Output Root
        self.lbl_batch_output = ttk.Label(self.tab_batch)
        self.lbl_batch_output.pack(anchor=W)
        out_frame = ttk.Frame(self.tab_batch)
        out_frame.pack(fill=X, pady=5)
        
        ttk.Entry(out_frame, textvariable=self.batch_output_var).pack(side=LEFT, fill=X, expand=YES, padx=(0, 5))
        self.btn_browse_batch = ttk.Button(out_frame, command=self._pick_batch_output)
        self.btn_browse_batch.pack(side=LEFT)

        # Action
        self.btn_convert_batch = ttk.Button(
            self.tab_batch,
            command=self._start_batch_conversion,
            width=30,
        )
        self.btn_convert_batch.pack(pady=15)

    def _pick_input(self) -> None:
        path = filedialog.askdirectory()
        if path: self.input_var.set(path)

    def _pick_output(self) -> None:
        path = filedialog.askdirectory()
        if path: self.output_var.set(path)

    def _pick_batch_output(self) -> None:
        path = filedialog.askdirectory()
        if path: self.batch_output_var.set(path)

    def _add_batch_input(self) -> None:
        path = filedialog.askdirectory()
        if path and path not in self._input_paths:
            self._input_paths.append(path)
            self.batch_list.insert(tk.END, path)

    def _remove_batch_input(self) -> None:
        selection = self.batch_list.curselection()
        for idx in reversed(selection):
            self.batch_list.delete(idx)
            del self._input_paths[idx]

    def _clear_batch_inputs(self) -> None:
        self.batch_list.delete(0, tk.END)
        self._input_paths.clear()

    def _start_single_conversion(self) -> None:
        self._initiate_conversion(mode="single")

    def _start_batch_conversion(self) -> None:
        self._initiate_conversion(mode="batch")

    def _initiate_conversion(self, mode: str) -> None:
        if self._worker and self._worker.is_alive():
            return

        # Common Params
        direction = self.direction_var.get()
        target_version = self._normalize_version()
        force_repair = self.repair_var.get()

        # Mode Specifics
        if mode == "single":
            inp = self.input_var.get().strip()
            out = self.output_var.get().strip()
            if not inp or not out:
                Messagebox.show_warning(self._t("warn_missing_paths"), self._t("warn_input_error"))
                return
            
            out_path = Path(out)
            if out_path.exists() and any(out_path.iterdir()):
                confirm = Messagebox.show_question(self._t("warn_output_nonempty"), self._t("warn_confirm_overwrite"))
                if confirm != "Yes": return
            
            args = (mode, inp, out, direction, target_version, force_repair)
            
        else: # batch
            if not self._input_paths:
                Messagebox.show_warning(self._t("warn_list_empty"), self._t("warn_input_error"))
                return
            out = self.batch_output_var.get().strip()
            if not out:
                Messagebox.show_warning(self._t("warn_select_output_root"), self._t("warn_input_error"))
                return
            
            args = (mode, self._input_paths, out, direction, target_version, force_repair)

        # UI State Lock
        self._lock_ui(True)
        self.log_text.delete("1.0", tk.END)
        self._set_status("status_running")

        self._worker = threading.Thread(
            target=self._run_conversion,
            args=args,
            daemon=True
        )
        self._worker.start()

    def _lock_ui(self, locked: bool) -> None:
        state = DISABLED if locked else NORMAL
        self.btn_convert_single.configure(state=state)
        self.btn_convert_batch.configure(state=state)

    def _run_conversion(
        self,
        mode: str,
        input_path: str | list[str],
        output_path: str,
        direction: str,
        target_version: str | None,
        force_repair: bool,
    ) -> None:
        try:
            if mode == "batch":
                result = convert_batch(
                    input_paths=input_path, # type: ignore
                    output_root=output_path,
                    direction=direction,
                    target_version=target_version,
                    force_repair=force_repair,
                    log=self._log_queue.put,
                )
            else:
                result = convert_world(
                    input_path=input_path, # type: ignore
                    output_path=output_path,
                    direction=direction,
                    target_version=target_version,
                    force_repair=force_repair,
                    log=self._log_queue.put,
                )
            self._result_queue.put(result)
        except Exception as e:
            self._log_queue.put(f"CRITICAL ERROR: {e}")
            self._result_queue.put(ConversionResult(False, str(e), [] if mode=="batch" else None))

    def _poll_queues(self) -> None:
        while not self._log_queue.empty():
            msg = self._log_queue.get()
            self.log_text.insert(tk.END, msg + "\n")
            self.log_text.see(tk.END)

        if not self._result_queue.empty():
            res = self._result_queue.get()
            self._lock_ui(False)
            
            status_key = "status_finished" if res.success else "status_failed"
            self._set_status(status_key)
            
            icon = "info" if res.success else "error"
            title = self._t("msg_success") if res.success else self._t("msg_failure")
            Messagebox.show_info(res.message, title=title)
            
            self._worker = None

        self.after(100, self._poll_queues)

    def _normalize_version(self) -> str | None:
        value = self.version_var.get().strip()
        if not value or value in {self._i18n["en"]["latest"], self._i18n["zh"]["latest"]}:
            return None
        return value

    def _refresh_versions(self) -> None:
        target_platform = (
            "java"
            if self.direction_var.get() in {"bedrock-to-java", "java-to-java"}
            else "bedrock"
        )
        try:
            versions = list_target_versions(target_platform)
        except Exception:
            versions = []

        latest_label = self._t("latest")
        values = [latest_label, *versions]
        self.version_combo["values"] = values
        current = self.version_var.get()
        if current in {self._i18n["en"]["latest"], self._i18n["zh"]["latest"]}:
            self.version_var.set(latest_label)
        if self.version_var.get() not in values:
            self.version_var.set(latest_label)
        self.version_combo.current(0)

    def _on_language_selected(self, _event: tk.Event | None = None) -> None:
        display = self.lang_display_var.get()
        code = self._lang_map.get(display, "en")
        if code != self.lang_var.get():
            self.lang_var.set(code)
            self._apply_language()

    def _apply_language(self) -> None:
        self.master.title(self._t("app_title"))
        self.header_title_label.configure(text=self._t("header_title"))
        self.lang_label.configure(text=self._t("lang_label"))
        self.log_frame.configure(text=self._t("log_frame"))
        self.opt_container.configure(text=self._t("options_frame"))
        self.lbl_direction.configure(text=self._t("direction_label"))
        self.lbl_target_ver.configure(text=self._t("target_ver_label"))
        self.chk_force_repair.configure(text=self._t("force_repair"))
        self.lbl_input.configure(text=self._t("input_world"))
        self.lbl_output.configure(text=self._t("output_folder"))
        self.btn_browse_input.configure(text=self._t("browse"))
        self.btn_browse_output.configure(text=self._t("browse"))
        self.btn_convert_single.configure(text=self._t("start_conversion"))
        self.btn_add.configure(text=self._t("batch_add"))
        self.btn_remove.configure(text=self._t("batch_remove"))
        self.btn_clear.configure(text=self._t("batch_clear"))
        self.lbl_batch_output.configure(text=self._t("output_root"))
        self.btn_browse_batch.configure(text=self._t("browse"))
        self.btn_convert_batch.configure(text=self._t("batch_convert"))
        self.notebook.tab(self.tab_single, text=f" {self._t('tab_single')} ")
        self.notebook.tab(self.tab_batch, text=f" {self._t('tab_batch')} ")
        self._set_status(self._status_key)
        self._refresh_versions()


def main() -> None:
    # Themes: cosmo, flatly, journal, darkly, superhero, solar
    app = ttk.Window(title="MC World Converter", themename="cosmo")
    App(app)
    app.mainloop()


if __name__ == "__main__":
    main()