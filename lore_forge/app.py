"""Main application window and entry-point logic."""

import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import os
import random
import subprocess
import platform
import shutil
import time

from .constants import (
    BG_DARK, BG_MID, BG_PANEL, BG_CARD, BG_HOVER,
    TEXT, TEXT_DIM, ACCENT, ACCENT2, SUCCESS,
    FONT_TITLE, FONT_HEAD, FONT_BODY, FONT_SMALL,
    DATA_DIR
)
from .database import DataManager
from .config import ConfigManager
from .activities import ActivitiesManager
from .widgets import flat_btn, label
from .dialogs import ActivitySuggestionDialog
from .tabs import EssayTab, ImageTab, ReferenceTab


class LoreForge:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("+TurboLore3000")
        self.root.geometry("1280x800")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG_DARK)

        self.cfg             = ConfigManager()
        self.activities      = ActivitiesManager()
        self.db              = None
        self.selected_nid    = None
        self._content_frame  = None
        self._active_nb      = None   # reference to current Notebook
        self.current_project = None

        self._apply_styles()

        # Try to restore last project, otherwise show selector
        last = self.cfg.get("last_project")
        projects_dir = DATA_DIR / "projects"
        if last and (projects_dir / last).is_dir():
            self._load_project(last)
        else:
            self._show_project_selector()

    # ── Styles ────────────────────────────────────────────────────────────────

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview",
                    background=BG_MID, foreground=TEXT,
                    fieldbackground=BG_MID, rowheight=30,
                    font=FONT_BODY, borderwidth=0)
        s.configure("Treeview.Heading",
                    background=BG_PANEL, foreground=TEXT_DIM,
                    font=FONT_SMALL, borderwidth=0)
        s.map("Treeview",
              background=[("selected", ACCENT2)],
              foreground=[("selected", TEXT)])

        s.configure("TNotebook",
                    background=BG_DARK, borderwidth=0, tabmargins=0)
        s.configure("TNotebook.Tab",
                    background=BG_MID, foreground=TEXT_DIM,
                    padding=[16, 8], font=FONT_BODY, borderwidth=0)
        s.map("TNotebook.Tab",
              background=[("selected", BG_CARD)],
              foreground=[("selected", TEXT)])

        s.configure("Vertical.TScrollbar",
                    background=BG_MID, troughcolor=BG_DARK,
                    arrowcolor=TEXT_DIM, borderwidth=0)
        s.configure("TSeparator", background=BG_PANEL)

    # ── Project Selector ──────────────────────────────────────────────────────

    def _show_project_selector(self):
        """Display the project selection screen."""
        self._maybe_migrate_legacy()

        for w in self.root.winfo_children():
            w.destroy()

        self.root.title("+TurboLore3000 — Select Project")

        container = tk.Frame(self.root, bg=BG_DARK)
        container.pack(fill="both", expand=True)

        wrapper = tk.Frame(container, bg=BG_DARK)
        wrapper.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(wrapper, text="📂 Projects", bg=BG_DARK, fg=TEXT,
                 font=FONT_TITLE).pack(pady=(0, 24))

        # Project list
        list_frame = tk.Frame(wrapper, bg=BG_MID, bd=1, relief="solid")
        list_frame.pack(fill="both", expand=True, pady=10)

        self._proj_listbox = tk.Listbox(
            list_frame, bg=BG_MID, fg=TEXT,
            selectbackground=ACCENT2, selectforeground=TEXT,
            font=FONT_BODY, bd=0, highlightthickness=0,
            width=44, height=14
        )
        self._proj_listbox.pack(side="left", fill="both", expand=True, padx=2, pady=2)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical",
                                  command=self._proj_listbox.yview)
        self._proj_listbox.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")

        self._refresh_project_list()

        # Buttons
        btn_frame = tk.Frame(wrapper, bg=BG_DARK)
        btn_frame.pack(pady=18)

        flat_btn(btn_frame, "➕  New Project", self._create_project,
                 bg=ACCENT, fg=TEXT, font=FONT_BODY, padx=14, pady=5).pack(side="left", padx=5)
        flat_btn(btn_frame, "📂  Open Project", self._open_selected_project,
                 bg=BG_PANEL, fg=TEXT, font=FONT_BODY, padx=14, pady=5).pack(side="left", padx=5)
        flat_btn(btn_frame, "🗑  Delete", self._delete_selected_project,
                 bg="#5a1a1a", fg=TEXT, font=FONT_BODY, padx=14, pady=5).pack(side="left", padx=5)

        self._proj_listbox.bind("<Double-Button-1>", lambda e: self._open_selected_project())

    def _refresh_project_list(self):
        self._proj_listbox.delete(0, "end")
        projects_dir = DATA_DIR / "projects"
        if projects_dir.exists():
            for p in sorted(projects_dir.iterdir()):
                if p.is_dir():
                    self._proj_listbox.insert("end", p.name)

    def _create_project(self):
        name = simpledialog.askstring("New Project", "Project name:", parent=self.root)
        if name and name.strip():
            name = name.strip()
            proj_dir = DATA_DIR / "projects" / name
            if proj_dir.exists():
                messagebox.showerror("Error", f"Project '{name}' already exists.", parent=self.root)
                return
            proj_dir.mkdir(parents=True)
            self._load_project(name)

    def _open_selected_project(self):
        sel = self._proj_listbox.curselection()
        if not sel:
            messagebox.showinfo("Select Project", "Please select a project from the list.", parent=self.root)
            return
        name = self._proj_listbox.get(sel[0])
        self._load_project(name)

    def _delete_selected_project(self):
        sel = self._proj_listbox.curselection()
        if not sel:
            return
        name = self._proj_listbox.get(sel[0])
        if messagebox.askyesno("Delete Project",
                               f"Delete project '{name}' and all its data?\n\nThis cannot be undone.",
                               parent=self.root):
            proj_dir = DATA_DIR / "projects" / name
            if proj_dir.exists():
                shutil.rmtree(proj_dir)
            if self.cfg.get("last_project") == name:
                self.cfg.set("last_project", None)
            self._refresh_project_list()

    def _load_project(self, name):
        self.current_project = name
        proj_path = DATA_DIR / "projects" / name
        self.db = DataManager(str(proj_path))
        self.cfg.set("last_project", name)
        self.root.title(f"+TurboLore3000 — {name}")

        for w in self.root.winfo_children():
            w.destroy()

        self.selected_nid = None
        self._content_frame = None
        self._active_nb = None
        self._build_ui()
        self._refresh_tree()

    def _maybe_migrate_legacy(self):
        """Move old single-project data into a 'Legacy' project."""
        legacy_nodes = DATA_DIR / "nodes.json"
        projects_dir = DATA_DIR / "projects"
        if not legacy_nodes.exists():
            return
        # Only migrate if no projects exist yet
        if projects_dir.exists() and any(projects_dir.iterdir()):
            return
        projects_dir.mkdir(exist_ok=True)
        legacy_proj = projects_dir / "Legacy"
        legacy_proj.mkdir(exist_ok=True)
        shutil.move(str(legacy_nodes), str(legacy_proj / "nodes.json"))
        legacy_img = DATA_DIR / "images"
        if legacy_img.exists():
            shutil.move(str(legacy_img), str(legacy_proj / "images"))

    # ── UI Layout ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        # ── Header ───────────────────────────────────────────────────────────
        hdr = tk.Frame(self.root, bg=BG_PANEL, height=54)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)

        tk.Label(hdr, text=" +TurboLore3000", bg=BG_PANEL, fg=TEXT,
                 font=("Segoe UI", 17, "bold")).pack(side="left", pady=10)
        tk.Label(hdr, text="· Creative World Builder", bg=BG_PANEL, fg=TEXT_DIM,
                 font=("Segoe UI", 11)).pack(side="left", padx=6, pady=10)

        flat_btn(hdr, "Switch Project", self._show_project_selector,
                 bg=BG_MID, pady=3, padx=10,
                 font=FONT_SMALL).pack(side="right", padx=4, pady=10)
        flat_btn(hdr, "Open Data Folder", self._open_data_folder,
                 bg=BG_MID, pady=3, padx=10,
                 font=FONT_SMALL).pack(side="right", padx=4, pady=10)

        # ── Paned layout ─────────────────────────────────────────────────────
        pane = tk.PanedWindow(self.root, orient="horizontal",
                              bg=BG_DARK, sashwidth=5,
                              sashrelief="flat", sashpad=0)
        pane.pack(fill="both", expand=True)

        # ── Left: tree panel ─────────────────────────────────────────────────
        left = tk.Frame(pane, bg=BG_MID, width=260)
        pane.add(left, minsize=180, stretch="never")

        tree_hdr = tk.Frame(left, bg=BG_MID)
        tree_hdr.pack(fill="x", padx=10, pady=8)
        tk.Label(tree_hdr, text="Nodes", bg=BG_MID, fg=TEXT,
                 font=FONT_HEAD).pack(side="left")
        flat_btn(tree_hdr, "+", self._add_root_node,
                 bg=ACCENT, fg=TEXT, font=("Segoe UI", 14, "bold"),
                 padx=7, pady=0).pack(side="right")

        tree_wrap = tk.Frame(left, bg=BG_MID)
        tree_wrap.pack(fill="both", expand=True, padx=5, pady=(0, 8))
        self.tree = ttk.Treeview(tree_wrap, show="tree", selectmode="browse")
        tsb = ttk.Scrollbar(tree_wrap, orient="vertical",
                            command=self.tree.yview)
        self.tree.configure(yscrollcommand=tsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tsb.pack(side="right", fill="y")

        self.tree.bind("<<TreeviewSelect>>", self._on_select)
        self.tree.bind("<Button-3>", self._on_right_click)

        # Context menu
        self._ctx = tk.Menu(self.root, tearoff=0,
                            bg=BG_MID, fg=TEXT,
                            activebackground=ACCENT2, activeforeground=TEXT,
                            bd=0, relief="flat")
        self._ctx.add_command(label="➕  Add Child Node",
                              command=self._add_child_node)
        self._ctx.add_command(label="✏️  Rename Node",
                              command=self._rename_node)
        self._ctx.add_separator()
        self._ctx.add_command(label="🗑️  Delete Node",
                              command=self._delete_node)

        # Hint
        label(left, "Right-click a node for options",
              fg=TEXT_DIM, bg=BG_MID, font=FONT_SMALL).pack(pady=(0, 6))

        # ── Right: content area ───────────────────────────────────────────────
        self._right = tk.Frame(pane, bg=BG_DARK)
        pane.add(self._right, minsize=600, stretch="always")

        self._show_placeholder()

    def _show_placeholder(self):
        if self._content_frame:
            self._content_frame.destroy()
        self._content_frame = tk.Frame(self._right, bg=BG_DARK)
        self._content_frame.pack(fill="both", expand=True)
        tk.Label(self._content_frame, text="⚔", bg=BG_DARK, fg=ACCENT2,
                 font=("Segoe UI", 52)).pack(expand=True, pady=(80, 5))
        label(self._content_frame,
              "Select a node from the panel to view its content.",
              fg=TEXT_DIM, bg=BG_DARK,
              font=("Segoe UI", 13)).pack()
        label(self._content_frame,
              "Click  +  to add a root node, or right-click any node to add children.",
              fg=TEXT_DIM, bg=BG_DARK,
              font=("Segoe UI", 10)).pack(pady=4)

    # ── Tree rendering ────────────────────────────────────────────────────────

    def _refresh_tree(self):
        sel = self.tree.selection()
        self.tree.delete(*self.tree.get_children())
        for nid in self.db.data["root_children"]:
            self._insert_node(nid, "")
        # Re-select
        if sel:
            try:
                self.tree.selection_set(sel)
                self.tree.see(sel[0])
            except Exception:
                pass

    def _insert_node(self, nid, parent_iid):
        n = self.db.get_node(nid)
        if not n:
            return
        total = len(n["essays"]) + len(n["images"]) + len(n["references"])
        badge = f"  ({total})" if total else ""
        icon  = "📁" if n["children"] else "📄"
        self.tree.insert(parent_iid, "end", iid=nid,
                         text=f"  {icon}  {n['name']}{badge}", open=True)
        for child in n["children"]:
            self._insert_node(child, nid)

    # ── Node selection & content rendering ────────────────────────────────────

    def _on_select(self, _):
        sel = self.tree.selection()
        if not sel:
            return
        self.selected_nid = sel[0]
        self._show_node(self.selected_nid)

    def _show_node(self, nid):
        n = self.db.get_node(nid)
        if not n:
            return

        if self._content_frame:
            self._content_frame.destroy()

        self._content_frame = tk.Frame(self._right, bg=BG_DARK)
        self._content_frame.pack(fill="both", expand=True)

        # Node header bar
        nhdr = tk.Frame(self._content_frame, bg=BG_PANEL, height=60)
        nhdr.pack(fill="x")
        nhdr.pack_propagate(False)

        tk.Label(nhdr, text=f"  📂  {n['name']}", bg=BG_PANEL, fg=TEXT,
                 font=FONT_TITLE).pack(side="left", padx=16, pady=10)

        # ✨ Request Activity button
        flat_btn(nhdr, "Request Activity  ",
                 lambda: self._request_activity(nid),
                 bg="#2a1a4a", fg="#cc99ff",
                 font=("Segoe UI", 9, "bold"),
                 pady=4, padx=10).pack(side="left", padx=10, pady=16)

        for lbl, cnt, col in [
            ("Essays", len(n["essays"]),     SUCCESS),
            ("Artwork", len(n["images"]),    ACCENT),
            ("Refs",   len(n["references"]), ACCENT2),
        ]:
            badge = tk.Frame(nhdr, bg=col, padx=9, pady=3)
            badge.pack(side="right", padx=5, pady=16)
            tk.Label(badge, text=f"{lbl}: {cnt}", bg=col, fg="white",
                     font=("Segoe UI", 9, "bold")).pack()

        # Notebook
        nb = ttk.Notebook(self._content_frame)
        nb.pack(fill="both", expand=True)
        self._active_nb = nb  # keep reference so _request_activity can switch tabs

        def refresh():
            self._refresh_tree()
            # Re-show current node after tree refresh
            self._show_node(nid)

        essay_tab = EssayTab(nb, self.db, nid, self._refresh_tree)
        nb.add(essay_tab, text="   Essays  ")

        img_tab = ImageTab(nb, self.db, nid, self._refresh_tree)
        nb.add(img_tab, text="   Artwork  ")

        ref_tab = ReferenceTab(nb, self.db, nid, self._refresh_tree)
        nb.add(ref_tab, text="   References  ")

    # ── Node management ───────────────────────────────────────────────────────

    def _add_root_node(self):
        name = simpledialog.askstring("New Node", "Node name:", parent=self.root)
        if name and name.strip():
            nid = self.db.add_node(name.strip())
            self._refresh_tree()
            self.tree.selection_set(nid)
            self._show_node(nid)

    def _add_child_node(self):
        if not self.selected_nid:
            return
        name = simpledialog.askstring("New Child Node", "Node name:",
                                      parent=self.root)
        if name and name.strip():
            nid = self.db.add_node(name.strip(), self.selected_nid)
            self._refresh_tree()
            self.tree.selection_set(nid)
            self._show_node(nid)

    def _rename_node(self):
        if not self.selected_nid:
            return
        n    = self.db.get_node(self.selected_nid)
        name = simpledialog.askstring("Rename", "New name:",
                                      initialvalue=n["name"], parent=self.root)
        if name and name.strip():
            self.db.rename_node(self.selected_nid, name.strip())
            self._refresh_tree()
            self._show_node(self.selected_nid)

    def _delete_node(self):
        if not self.selected_nid:
            return
        n = self.db.get_node(self.selected_nid)
        total = len(n["essays"]) + len(n["images"]) + len(n["references"]) + len(n["children"])
        msg = f"Delete '{n['name']}'?"
        if total:
            msg += f"\n\nThis will permanently delete all {total} entries and child nodes."
        if messagebox.askyesno("Delete Node", msg, parent=self.root):
            self.db.delete_node(self.selected_nid)
            self.selected_nid = None
            self._refresh_tree()
            self._show_placeholder()

    def _on_right_click(self, e):
        iid = self.tree.identify_row(e.y)
        if iid:
            self.tree.selection_set(iid)
            self.selected_nid = iid
            self._ctx.post(e.x_root, e.y_root)

    # ── Activity suggestion (loaded from activities.json) ─────────────────────

    def _request_activity(self, _nid=None):
        """Pick a random node and a random activity type, then show the suggestion."""
        all_nids = list(self.db.data["nodes"].keys())
        if not all_nids:
            messagebox.showinfo("No Nodes", "Add some nodes first!", parent=self.root)
            return

        result = self.activities.get_random()
        if result is None:
            messagebox.showinfo(
                "No Activities",
                "No activities found in activities.json.\n\n"
                "You can edit that file in your data folder to add your own prompts.",
                parent=self.root,
            )
            return

        activity, title, prompt = result
        node_id = random.choice(all_nids)
        node    = self.db.get_node(node_id)

        def jump_to_tab(tab_index):
            # Select the node in the tree, then switch to the requested tab
            self.tree.selection_set(node_id)
            self._show_node(node_id)
            # Defer tab switch until the notebook is rebuilt
            self.root.after(50, lambda: self._active_nb and
                            self._active_nb.select(tab_index))

        def autosave(nid, activity_title, draft, img_path):
            """Called by the dialog when it closes with valid data."""
            if not nid:
                return
            n = self.db.get_node(nid)
            if not n:
                return

            saved = False
            timestamp = int(time.time())

            # Save draft as an essay
            if draft:
                essay = {
                    "title": f"Activity: {activity_title}",
                    "content": draft
                }
                n["essays"].append(essay)
                saved = True

            # Save image into project folder and reference it
            if img_path and os.path.exists(img_path):
                img_dir = self.db.project_path / "images"
                img_dir.mkdir(exist_ok=True)

                dest = img_dir / os.path.basename(img_path)
                if dest.exists():
                    base, ext = os.path.splitext(dest.name)
                    dest = img_dir / f"{base}_{timestamp}{ext}"

                try:
                    shutil.copy2(img_path, dest)
                    n["images"].append({
                        "path": str(dest.relative_to(self.db.project_path)),
                        "label": f"Activity: {activity_title}"
                    })
                    saved = True
                except Exception as ex:
                    print(f"Failed to copy image: {ex}")

            if saved:
                if hasattr(self.db, 'save'):
                    self.db.save()
                self._refresh_tree()

        ActivitySuggestionDialog(
            self.root, node["name"], activity, title, prompt, jump_to_tab,
            node_id=node_id, db=self.db, on_autosave=autosave
        )

    def _open_data_folder(self):
        path = str(self.db.project_path) if self.db else str(DATA_DIR)
        try:
            if platform.system() == "Windows":
                os.startfile(path)
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as ex:
            messagebox.showinfo("Data folder", path, parent=self.root)

    # ── Run ───────────────────────────────────────────────────────────────────

    def run(self):

        self.root.mainloop()