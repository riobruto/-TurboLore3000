"""Reusable UI widgets used across the app."""

import tkinter as tk
from tkinter import ttk

from .constants import BG_CARD, BG_MID, BG_PANEL, BG_HOVER, TEXT, TEXT_DIM, FONT_BODY, FONT_SMALL


class ScrollFrame(tk.Frame):
    """A vertically scrollable container."""

    def __init__(self, master, bg=BG_CARD, **kw):
        super().__init__(master, bg=bg, **kw)
        self._canvas = tk.Canvas(self, bg=bg, highlightthickness=0, bd=0)
        self._sb     = ttk.Scrollbar(self, orient="vertical",
                                     command=self._canvas.yview)
        self.inner   = tk.Frame(self._canvas, bg=bg)

        self._win = self._canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self._canvas.configure(yscrollcommand=self._sb.set)

        self._canvas.pack(side="left", fill="both", expand=True)
        self._sb.pack(side="right", fill="y")

        self.inner.bind("<Configure>", self._on_inner_resize)
        self._canvas.bind("<Configure>", self._on_canvas_resize)
        self._bind_wheel(self.inner)

    def _on_inner_resize(self, _):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_resize(self, e):
        self._canvas.itemconfig(self._win, width=e.width)

    def _bind_wheel(self, widget):
        widget.bind("<MouseWheel>",  self._on_wheel, add="+")
        widget.bind("<Button-4>",   lambda e: self._canvas.yview_scroll(-1, "units"), add="+")
        widget.bind("<Button-5>",   lambda e: self._canvas.yview_scroll(1, "units"), add="+")

    def _on_wheel(self, e):
        delta = -1 if e.delta > 0 else 1
        self._canvas.yview_scroll(delta, "units")


def flat_btn(parent, text, cmd, bg=BG_PANEL, fg=TEXT, font=FONT_BODY,
             padx=12, pady=5, cursor="hand2", **kw):
    return tk.Button(parent, text=text, command=cmd, bg=bg, fg=fg,
                     font=font, padx=padx, pady=pady, relief="flat",
                     activebackground=BG_HOVER, activeforeground=TEXT,
                     cursor=cursor, bd=0, **kw)


def label(parent, text, font=FONT_BODY, fg=TEXT, bg=BG_CARD, **kw):
    return tk.Label(parent, text=text, font=font, fg=fg, bg=bg, **kw)
