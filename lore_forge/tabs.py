"""The three content tabs: Essays, Artwork, References."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog, scrolledtext
from pathlib import Path

from .constants import (
    BG_CARD, BG_MID, BG_PANEL, BG_DARK, TEXT, TEXT_DIM, SUCCESS, ACCENT, ACCENT2,
    FONT_HEAD, FONT_BODY, FONT_SMALL
)
from .database import PIL_AVAILABLE
from .widgets import ScrollFrame, flat_btn, label
from .dialogs import EssayEditor


class EssayTab(tk.Frame):
    def __init__(self, master, db, node_id, refresh_cb):
        super().__init__(master, bg=BG_CARD)
        self.db         = db
        self.node_id    = node_id
        self.refresh_cb = refresh_cb
        self._build()

    def _build(self):
        # Toolbar
        bar = tk.Frame(self, bg=BG_CARD, padx=15, pady=10)
        bar.pack(fill="x")
        label(bar, "Activity 1 — Write an essay about this topic",
              fg=TEXT_DIM, bg=BG_CARD,
              font=("Segoe UI", 9, "italic")).pack(side="left")
        flat_btn(bar, "+ New Essay", self._new_essay,
                 bg=ACCENT, pady=4, padx=14).pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=15)

        # Scroll area
        self._scroll = ScrollFrame(self, bg=BG_CARD)
        self._scroll.pack(fill="both", expand=True)
        self._render()

    def _render(self):
        for w in self._scroll.inner.winfo_children():
            w.destroy()

        node   = self.db.get_node(self.node_id)
        essays = node["essays"]

        if not essays:
            label(self._scroll.inner,
                  "No essays yet — hit '+ New Essay' to start writing.",
                  fg=TEXT_DIM, bg=BG_CARD,
                  font=("Segoe UI", 12)).pack(pady=50)
            return

        for essay in reversed(essays):
            self._essay_card(self._scroll.inner, essay)

    def _essay_card(self, parent, essay):
        card = tk.Frame(parent, bg=BG_MID, padx=16, pady=12)
        card.pack(fill="x", padx=15, pady=5)

        # Header row
        hdr = tk.Frame(card, bg=BG_MID)
        hdr.pack(fill="x")
        label(hdr, essay["title"], font=FONT_HEAD, bg=BG_MID).pack(side="left")
        label(hdr, essay["created"][:10], fg=TEXT_DIM, bg=BG_MID,
              font=FONT_SMALL).pack(side="right")

        # Preview
        preview = essay["content"][:240].replace("\n", " ")
        if len(essay["content"]) > 240:
            preview += "…"
        label(card, preview, fg="#c8c8e0", bg=BG_MID, font=FONT_BODY,
              wraplength=720, justify="left", anchor="w").pack(fill="x", pady=6)

        # Buttons
        btns = tk.Frame(card, bg=BG_MID)
        btns.pack(anchor="w")
        flat_btn(btns, "✏  Read / Edit",
                 lambda e=essay: self._edit_essay(e),
                 bg=BG_PANEL, pady=3, padx=10).pack(side="left", padx=(0, 4))
        flat_btn(btns, "🗑  Delete",
                 lambda e=essay: self._delete(e),
                 bg="#3a0f1f", fg="#ff6b6b", pady=3, padx=10).pack(side="left")

    def _new_essay(self):
        EssayEditor(self, self.node_id, None, self._on_essay_saved)

    def _edit_essay(self, essay):
        def save_edit(title, content):
            self.db.update_essay(self.node_id, essay["id"], title, content)
            self._render()
            self.refresh_cb()
        EssayEditor(self, self.node_id, essay, save_edit)

    def _on_essay_saved(self, title, content):
        self.db.add_essay(self.node_id, title, content)
        self._render()
        self.refresh_cb()

    def _delete(self, essay):
        if messagebox.askyesno("Delete essay", f"Delete '{essay['title']}'?",
                               parent=self):
            self.db.delete_essay(self.node_id, essay["id"])
            self._render()
            self.refresh_cb()


class ImageTab(tk.Frame):
    """Activity 2 — Artwork (upload or draw)."""

    THUMB = (200, 160)

    def __init__(self, master, db, node_id, refresh_cb):
        super().__init__(master, bg=BG_CARD)
        self.db         = db
        self.node_id    = node_id
        self.refresh_cb = refresh_cb
        self._photos    = []
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=BG_CARD, padx=15, pady=10)
        bar.pack(fill="x")
        label(bar, "Activity 2 — Draw or upload artwork / concept art",
              fg=TEXT_DIM, bg=BG_CARD,
              font=("Segoe UI", 9, "italic")).pack(side="left")
        flat_btn(bar, "+ Upload Image", self._upload,
                 bg=ACCENT, pady=4, padx=14).pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=15)

        self._scroll = ScrollFrame(self, bg=BG_CARD)
        self._scroll.pack(fill="both", expand=True)
        self._render()

    def _render(self):
        self._photos.clear()
        for w in self._scroll.inner.winfo_children():
            w.destroy()

        node   = self.db.get_node(self.node_id)
        images = node["images"]

        if not images:
            label(self._scroll.inner,
                  "No artwork yet — upload an image to get started.",
                  fg=TEXT_DIM, bg=BG_CARD,
                  font=("Segoe UI", 12)).pack(pady=50)
            return

        grid = tk.Frame(self._scroll.inner, bg=BG_CARD)
        grid.pack(fill="both", expand=True, padx=10, pady=10)

        cols = 3
        for idx, img in enumerate(reversed(images)):
            r, c = divmod(idx, cols)
            self._image_card(grid, img, r, c)

    def _image_card(self, grid, img, row, col):
        from PIL import Image, ImageTk
        card = tk.Frame(grid, bg=BG_MID, padx=8, pady=8)
        card.grid(row=row, column=col, padx=6, pady=6, sticky="nw")

        img_path = self.db.images_dir / img["filename"]
        if PIL_AVAILABLE and img_path.exists():
            try:
                pil = Image.open(img_path)
                pil.thumbnail(self.THUMB)
                photo = ImageTk.PhotoImage(pil)
                self._photos.append(photo)
                tk.Label(card, image=photo, bg=BG_MID,
                         cursor="hand2").pack()
            except Exception:
                label(card, "[Image error]", fg=TEXT_DIM, bg=BG_MID).pack(
                    ipadx=80, ipady=50)
        else:
            label(card, "[No preview\ninstall Pillow]",
                  fg=TEXT_DIM, bg=BG_MID).pack(ipadx=60, ipady=40)

        label(card, img["title"], font=("Segoe UI", 9, "bold"), bg=BG_MID,
              wraplength=210).pack(pady=(5, 0))

        if img.get("notes"):
            label(card, img["notes"][:70], fg=TEXT_DIM, bg=BG_MID,
                  font=FONT_SMALL, wraplength=210).pack()

        label(card, img["created"][:10], fg=TEXT_DIM, bg=BG_MID,
              font=FONT_SMALL).pack(pady=(2, 4))

        flat_btn(card, "🗑  Delete",
                 lambda i=img: self._delete(i),
                 bg="#3a0f1f", fg="#ff6b6b",
                 pady=2, padx=8).pack()

    def _upload(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff"),
                       ("All files", "*.*")])
        if not path:
            return
        title = simpledialog.askstring("Artwork Title",
                                       "Title for this piece:", parent=self)
        if title is None:
            return
        notes = simpledialog.askstring("Notes (optional)",
                                       "Any notes about this artwork?",
                                       parent=self) or ""
        self.db.add_image(self.node_id, path, title or Path(path).stem, notes)
        self._render()
        self.refresh_cb()

    def _delete(self, img):
        if messagebox.askyesno("Delete image",
                               f"Delete '{img['title']}'?", parent=self):
            self.db.delete_image(self.node_id, img["id"])
            self._render()
            self.refresh_cb()


class ReferenceTab(tk.Frame):
    """Activity 3 — Reference stash with notes & tags."""

    THUMB = (130, 100)

    def __init__(self, master, db, node_id, refresh_cb):
        super().__init__(master, bg=BG_CARD)
        self.db         = db
        self.node_id    = node_id
        self.refresh_cb = refresh_cb
        self._photos    = []
        self._build()

    def _build(self):
        bar = tk.Frame(self, bg=BG_CARD, padx=15, pady=10)
        bar.pack(fill="x")
        label(bar, "Activity 3 — Gather reference images, classify with notes & tags",
              fg=TEXT_DIM, bg=BG_CARD,
              font=("Segoe UI", 9, "italic")).pack(side="left")
        flat_btn(bar, "+ Add Reference(s)", self._add_refs,
                 bg=ACCENT, pady=4, padx=14).pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=15)

        self._scroll = ScrollFrame(self, bg=BG_CARD)
        self._scroll.pack(fill="both", expand=True)
        self._render()

    def _render(self):
        self._photos.clear()
        for w in self._scroll.inner.winfo_children():
            w.destroy()

        refs = self.db.get_node(self.node_id)["references"]

        if not refs:
            label(self._scroll.inner,
                  "No references yet — add images to your stash.",
                  fg=TEXT_DIM, bg=BG_CARD,
                  font=("Segoe UI", 12)).pack(pady=50)
            return

        for ref in reversed(refs):
            self._ref_card(self._scroll.inner, ref)

    def _ref_card(self, parent, ref):
        from PIL import Image, ImageTk
        card = tk.Frame(parent, bg=BG_MID, padx=12, pady=10)
        card.pack(fill="x", padx=15, pady=4)

        # Left: thumbnail
        left = tk.Frame(card, bg=BG_MID)
        left.pack(side="left", padx=(0, 14))

        img_path = self.db.images_dir / ref["filename"]
        if PIL_AVAILABLE and img_path.exists():
            try:
                pil   = Image.open(img_path)
                pil.thumbnail(self.THUMB)
                photo = ImageTk.PhotoImage(pil)
                self._photos.append(photo)
                tk.Label(left, image=photo, bg=BG_MID).pack()
            except Exception:
                label(left, "[Error]", fg=TEXT_DIM, bg=BG_MID).pack(
                    ipadx=40, ipady=30)
        else:
            label(left, "[No preview]", fg=TEXT_DIM, bg=BG_MID).pack(
                ipadx=40, ipady=30)

        # Right: meta
        right = tk.Frame(card, bg=BG_MID)
        right.pack(side="left", fill="both", expand=True)

        # Tags
        if ref.get("tags"):
            tags_row = tk.Frame(right, bg=BG_MID)
            tags_row.pack(anchor="w", pady=(0, 5))
            for tag in ref["tags"]:
                tk.Label(tags_row, text=f"  {tag}  ", bg=ACCENT2, fg=TEXT,
                         font=FONT_SMALL, padx=2).pack(side="left", padx=2)

        # Notes
        if ref.get("notes"):
            label(right, ref["notes"], fg=TEXT, bg=BG_MID, font=FONT_BODY,
                  wraplength=550, justify="left", anchor="w").pack(
                  fill="x", pady=(0, 4))

        label(right, ref["created"][:10], fg=TEXT_DIM, bg=BG_MID,
              font=FONT_SMALL).pack(anchor="w")

        flat_btn(right, "🗑  Delete",
                 lambda r=ref: self._delete(r),
                 bg="#3a0f1f", fg="#ff6b6b", pady=2, padx=8).pack(
                 anchor="w", pady=(6, 0))

    def _add_refs(self):
        paths = filedialog.askopenfilenames(
            title="Select reference images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff"),
                       ("All files", "*.*")])
        if not paths:
            return

        # Batch dialog
        win = tk.Toplevel(self)
        win.title("Add References")
        win.geometry("500x300")
        win.configure(bg=BG_DARK)
        win.grab_set()

        label(win, f"Adding {len(paths)} image(s) to stash",
              font=FONT_HEAD, bg=BG_DARK).pack(padx=15, pady=(15, 5))

        label(win, "Why are these relevant? (notes applied to all):",
              fg=TEXT_DIM, bg=BG_DARK, font=FONT_SMALL).pack(
              anchor="w", padx=15, pady=(8, 2))
        notes_box = scrolledtext.ScrolledText(win, height=4,
                                              bg=BG_PANEL, fg=TEXT,
                                              insertbackground=TEXT,
                                              font=FONT_BODY, relief="flat")
        notes_box.pack(fill="x", padx=15)

        label(win, "Tags (comma-separated, e.g. wood, medieval, brown):",
              fg=TEXT_DIM, bg=BG_DARK, font=FONT_SMALL).pack(
              anchor="w", padx=15, pady=(8, 2))
        tags_var = tk.StringVar()
        tk.Entry(win, textvariable=tags_var, bg=BG_PANEL, fg=TEXT,
                 insertbackground=TEXT, font=FONT_BODY, relief="flat", bd=8
                 ).pack(fill="x", padx=15)

        btns = tk.Frame(win, bg=BG_DARK)
        btns.pack(fill="x", padx=15, pady=12)

        def do_add():
            notes = notes_box.get("1.0", "end-1c").strip()
            tags  = tags_var.get().strip()
            for p in paths:
                self.db.add_reference(self.node_id, p, notes, tags)
            win.destroy()
            self._render()
            self.refresh_cb()

        flat_btn(btns, "Cancel", win.destroy, bg=BG_MID).pack(side="right", padx=6)
        flat_btn(btns, "  📌  Add to Stash  ", do_add,
                 bg=SUCCESS, fg=BG_DARK,
                 font=("Segoe UI", 10, "bold")).pack(side="right")

    def _delete(self, ref):
        if messagebox.askyesno("Delete reference", "Remove this reference?",
                               parent=self):
            self.db.delete_reference(self.node_id, ref["id"])
            self._render()
            self.refresh_cb()