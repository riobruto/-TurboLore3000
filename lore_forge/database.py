"""All persistence lives here. Data is a dict kept in memory and flushed to JSON."""

import json
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from .constants import DATA_DIR, DEFAULT_NODES


try:
    from PIL import Image, ImageTk
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class DataManager:
    def __init__(self, project_path=None):
        # If no project path is given, fall back to the legacy root directory
        self.project_path = Path(project_path) if project_path else DATA_DIR
        self.nodes_file   = self.project_path / "nodes.json"
        self.images_dir   = self.project_path / "images"

        self.project_path.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(exist_ok=True)
        self.data = self._load()

    # ── Load / Save ──────────────────────────────────────────────────────────

    def _load(self):
        if self.nodes_file.exists():
            try:
                with open(self.nodes_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return self._default_data()

    def save(self):
        with open(self.nodes_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=2, ensure_ascii=False)

    def _default_data(self):
        d = {"nodes": {}, "root_children": []}
        for name in DEFAULT_NODES:
            nid = self._uid()
            d["nodes"][nid] = self._empty_node(nid, name, parent=None)
            d["root_children"].append(nid)
        return d

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _uid():
        return uuid.uuid4().hex[:10]

    @staticmethod
    def _empty_node(nid, name, parent):
        return {
            "id": nid, "name": name, "parent": parent,
            "children": [],
            "essays": [], "images": [], "references": [],
        }

    def get_node(self, nid):
        return self.data["nodes"].get(nid)

    # ── Node CRUD ─────────────────────────────────────────────────────────────

    def add_node(self, name, parent_id=None):
        nid = self._uid()
        self.data["nodes"][nid] = self._empty_node(nid, name, parent_id)
        if parent_id and parent_id in self.data["nodes"]:
            self.data["nodes"][parent_id]["children"].append(nid)
        else:
            self.data["root_children"].append(nid)
        self.save()
        return nid

    def rename_node(self, nid, new_name):
        self.data["nodes"][nid]["name"] = new_name
        self.save()

    def delete_node(self, nid):
        node = self.data["nodes"].get(nid)
        if not node:
            return
        for child in list(node["children"]):
            self.delete_node(child)
        # Remove image files
        for entry in node["images"] + node["references"]:
            f = self.images_dir / entry["filename"]
            if f.exists():
                f.unlink()
        parent = node["parent"]
        if parent and parent in self.data["nodes"]:
            self.data["nodes"][parent]["children"].remove(nid)
        elif nid in self.data["root_children"]:
            self.data["root_children"].remove(nid)
        del self.data["nodes"][nid]
        self.save()

    # ── Essay CRUD ────────────────────────────────────────────────────────────

    def add_essay(self, nid, title, content):
        entry = {"id": self._uid(), "title": title, "content": content,
                 "created": datetime.now().isoformat()}
        self.data["nodes"][nid]["essays"].append(entry)
        self.save()
        return entry

    def update_essay(self, nid, eid, title, content):
        for e in self.data["nodes"][nid]["essays"]:
            if e["id"] == eid:
                e.update({"title": title, "content": content,
                           "updated": datetime.now().isoformat()})
                break
        self.save()

    def delete_essay(self, nid, eid):
        n = self.data["nodes"][nid]
        n["essays"] = [e for e in n["essays"] if e["id"] != eid]
        self.save()

    # ── Image CRUD ────────────────────────────────────────────────────────────

    def add_image(self, nid, src, title, notes=""):
        eid  = self._uid()
        ext  = Path(src).suffix.lower() or ".png"
        dest = self.images_dir / f"img_{eid}{ext}"
        shutil.copy2(src, dest)
        entry = {"id": eid, "title": title, "filename": dest.name,
                 "notes": notes, "created": datetime.now().isoformat()}
        self.data["nodes"][nid]["images"].append(entry)
        self.save()
        return entry

    def delete_image(self, nid, eid):
        n = self.data["nodes"][nid]
        for img in n["images"]:
            if img["id"] == eid:
                f = self.images_dir / img["filename"]
                if f.exists(): f.unlink()
                break
        n["images"] = [i for i in n["images"] if i["id"] != eid]
        self.save()

    # ── Reference CRUD ────────────────────────────────────────────────────────

    def add_reference(self, nid, src, notes="", tags=""):
        eid  = self._uid()
        ext  = Path(src).suffix.lower() or ".png"
        dest = self.images_dir / f"ref_{eid}{ext}"
        shutil.copy2(src, dest)
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        entry = {"id": eid, "filename": dest.name, "notes": notes,
                 "tags": tag_list, "created": datetime.now().isoformat()}
        self.data["nodes"][nid]["references"].append(entry)
        self.save()
        return entry

    def delete_reference(self, nid, eid):
        n = self.data["nodes"][nid]
        for ref in n["references"]:
            if ref["id"] == eid:
                f = self.images_dir / ref["filename"]
                if f.exists(): f.unlink()
                break
        n["references"] = [r for r in n["references"] if r["id"] != eid]
        self.save()