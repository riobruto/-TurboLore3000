"""Standalone popup windows (essay editor, activity suggestion)."""

import tkinter as tk
from tkinter import scrolledtext, filedialog

from .constants import (
    BG_DARK, BG_MID, BG_PANEL, TEXT, TEXT_DIM, SUCCESS, ACCENT, ACCENT2,
    FONT_HEAD, FONT_BODY, FONT_SMALL,
    ACTIVITY_ICONS, ACTIVITY_LABELS, ACTIVITY_COLORS, TAB_INDEX
)
from .widgets import flat_btn


class EssayEditor(tk.Toplevel):
    """Essay editor with live char counter, top action bar, and fluid resizing."""

    def __init__(self, master, node_id, essay, on_save, max_chars=10000):
        super().__init__(master)
        self.node_id = node_id
        self.essay = essay          # None = new essay
        self.on_save = on_save
        self.max_chars = max_chars

        self.title("Essay Editor — +TurboLore3000")
        self.geometry("820x580")
        self.minsize(640, 400)      # prevent collapsing on small screens
        self.configure(bg=BG_DARK)
        self._build()
        self._update_counter()

    # ── helpers ──────────────────────────────────────────────────────────────
    def _update_counter(self):
        """Refresh the live character counter."""
        title_len = len(self._title_var.get())
        body_len  = len(self._text.get("1.0", "end-1c"))
        total     = title_len + body_len
        remain    = self.max_chars - total

        if remain < 0:
            colour = "#ff6b6b"                       # over limit — red
            text   = f"Over by {abs(remain):,} chars"
        elif remain < 200:
            colour = "#ffcc66"                       # warning — yellow
            text   = f"{total:,} / {self.max_chars:,}  ({remain} left)"
        else:
            colour = TEXT_DIM                        # nominal — dim
            text   = f"{total:,} / {self.max_chars:,}"

        self._counter.config(text=text, fg=colour)

    # ── ui ───────────────────────────────────────────────────────────────────
    def _build(self):
        # ═════════════════════════════════════════════════════════════════════
        #  TOP ACTION BAR  (Save / Cancel + live counter)
        # ═════════════════════════════════════════════════════════════════════
        top = tk.Frame(self, bg=BG_DARK, padx=15, pady=10)
        top.pack(fill="x")

        self._counter = tk.Label(top, text="", bg=BG_DARK, fg=TEXT_DIM,
                                 font=FONT_SMALL)
        self._counter.pack(side="left")

        flat_btn(top, "Cancel", self.destroy, bg=BG_MID).pack(side="right", padx=6)
        flat_btn(top, "  💾  Save  ", self._save,
                 bg=SUCCESS, fg=BG_DARK,
                 font=("Segoe UI", 10, "bold")).pack(side="right")

        # ═════════════════════════════════════════════════════════════════════
        #  TITLE
        # ═════════════════════════════════════════════════════════════════════
        hdr = tk.Frame(self, bg=BG_DARK, padx=15)   # <-- plain int here
        hdr.pack(fill="x", pady=(0, 8))             # <-- tuple goes here

        tk.Label(hdr, text="Title:", bg=BG_DARK, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(anchor="w")

        self._title_var = tk.StringVar(
            value=self.essay["title"] if self.essay else "")
        self._title_var.trace_add("write", lambda *_: self._update_counter())

        tk.Entry(hdr, textvariable=self._title_var, bg=BG_PANEL, fg=TEXT,
                 insertbackground=TEXT, font=("Segoe UI", 13),
                 relief="flat", bd=8).pack(fill="x", pady=(2, 0))

        sep = tk.Frame(self, bg=BG_PANEL, height=1)
        sep.pack(fill="x")

        # ═════════════════════════════════════════════════════════════════════
        #  BODY  (expandable)
        # ═════════════════════════════════════════════════════════════════════
        self._text = scrolledtext.ScrolledText(
            self, bg=BG_MID, fg=TEXT, insertbackground=TEXT,
            font=("Segoe UI", 11), relief="flat", wrap="word",
            padx=18, pady=14, selectbackground=ACCENT2)
        self._text.pack(fill="both", expand=True, padx=0, pady=0)

        if self.essay:
            self._text.insert("1.0", self.essay["content"])

        # Update counter on any change
        self._text.bind("<KeyRelease>", lambda e: self._update_counter())
        self._text.bind("<ButtonRelease>", lambda e: self._update_counter())
        self._text.bind("<<Paste>>", lambda e: self.after(10, self._update_counter))

    # ── save ─────────────────────────────────────────────────────────────────
    def _save(self):
        from tkinter import messagebox
        title   = self._title_var.get().strip()
        content = self._text.get("1.0", "end-1c").strip()

        if not title:
            messagebox.showwarning("No title", "Please enter a title.", parent=self)
            return

        total = len(title) + len(content)
        if total > self.max_chars:
            messagebox.showwarning(
                "Character limit exceeded",
                f"This essay is {total:,} characters.\n"
                f"Maximum allowed is {self.max_chars:,}.\n\n"
                "Please shorten it before saving.", parent=self)
            return

        self.on_save(title, content)
        self.destroy()


class ActivitySuggestionDialog(tk.Toplevel):
    """Shows the activity suggestion and lets the user act on it.
    Autosaves draft text / image if the window is closed with valid data."""

    def __init__(self, master, node_name, activity_type, title, prompt, on_jump,
                 node_id=None, db=None, on_autosave=None):
        super().__init__(master)
        self.on_jump = on_jump
        self.activity_type = activity_type
        self.node_id = node_id
        self.db = db
        self.on_autosave = on_autosave
        self._activity_title = title

        self.title("Activity Suggestion — +TurboLore3000")
        self.geometry("620x520")
        self.resizable(False, False)
        self.configure(bg=BG_DARK)
        self.grab_set()

        icon  = ACTIVITY_ICONS.get(activity_type, "✨")
        color = ACTIVITY_COLORS.get(activity_type, ACCENT)
        act_label = ACTIVITY_LABELS.get(activity_type, activity_type.title())

        # ── Colour bar at top ─────────────────────────────────────────────────
        bar = tk.Frame(self, bg=color, height=6)
        bar.pack(fill="x")

        # ── Header ────────────────────────────────────────────────────────────
        hdr = tk.Frame(self, bg=BG_PANEL, padx=24, pady=16)
        hdr.pack(fill="x")

        tk.Label(hdr, text=f"{icon}  {act_label}", bg=BG_PANEL, fg=color,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        tk.Label(hdr, text=f"for  {node_name}", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Segoe UI", 11)).pack(side="left", padx=8)

        # ── Title ─────────────────────────────────────────────────────────────
        tk.Label(self, text=title, bg=BG_DARK, fg=TEXT,
                 font=("Segoe UI", 14, "bold"),
                 wraplength=570, justify="left").pack(anchor="w", padx=24, pady=(18, 6))

        # ── Prompt body ───────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG_MID, padx=18, pady=14)
        body.pack(fill="both", expand=True, padx=24, pady=(0, 10))

        tk.Label(body, text=prompt, bg=BG_MID, fg="#c8c8e0",
                 font=("Segoe UI", 10), wraplength=540,
                 justify="left", anchor="nw").pack(fill="both", expand=True)

        # ── Quick Draft ───────────────────────────────────────────────────────
        tk.Label(self, text="Quick Draft (autosaved on close):", bg=BG_DARK, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(anchor="w", padx=24, pady=(8, 4))

        self._draft = scrolledtext.ScrolledText(
            self, bg=BG_MID, fg=TEXT, insertbackground=TEXT,
            font=("Segoe UI", 10), relief="flat", wrap="word",
            height=5, padx=10, pady=8, selectbackground=ACCENT2)
        self._draft.pack(fill="x", padx=24, pady=(0, 8))

        # ── Image attachment ──────────────────────────────────────────────────
        img_frame = tk.Frame(self, bg=BG_DARK)
        img_frame.pack(fill="x", padx=24, pady=(0, 8))

        tk.Label(img_frame, text="Image:", bg=BG_DARK, fg=TEXT_DIM,
                 font=FONT_SMALL).pack(side="left")

        self._img_var = tk.StringVar()
        tk.Entry(img_frame, textvariable=self._img_var, bg=BG_PANEL, fg=TEXT,
                 insertbackground=TEXT, font=("Segoe UI", 10),
                 relief="flat", bd=6).pack(side="left", fill="x", expand=True, padx=6)

        flat_btn(img_frame, "Browse…", self._browse_image,
                 bg=BG_MID, font=FONT_SMALL, padx=8).pack(side="left")

        # ── Buttons ───────────────────────────────────────────────────────────
        btns = tk.Frame(self, bg=BG_DARK, padx=24, pady=12)
        btns.pack(fill="x")

        flat_btn(btns, "Dismiss", self._on_close, bg=BG_MID).pack(side="right", padx=6)
        flat_btn(btns, f"  {icon}  Start this activity  ",
                 self._start, bg=color,
                 fg=BG_DARK if color == SUCCESS else TEXT,
                 font=("Segoe UI", 10, "bold")).pack(side="right")

        # Intercept the window-manager close button
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── helpers ──────────────────────────────────────────────────────────────
    def _browse_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp"),
                ("All files", "*.*")
            ],
            parent=self
        )
        if path:
            self._img_var.set(path)

    def _has_content(self):
        """Return True if the user entered draft text or selected an image."""
        draft = self._draft.get("1.0", "end-1c").strip()
        img = self._img_var.get().strip()
        return bool(draft or img)

    def _autosave(self):
        """Save draft + image via the callback if data is present."""
        if not self._has_content():
            return False
        draft = self._draft.get("1.0", "end-1c").strip()
        img = self._img_var.get().strip()
        if self.on_autosave:
            self.on_autosave(self.node_id, self._activity_title, draft, img)
        return True

    def _on_close(self):
        """Dismiss / WM_CLOSE handler: autosave if valid, then destroy."""
        self._autosave()
        self.destroy()

    def _start(self):
        """Start activity: autosave draft, jump to tab, then close."""
        self._autosave()
        self.on_jump(TAB_INDEX.get(self.activity_type, 0))
        self.destroy()