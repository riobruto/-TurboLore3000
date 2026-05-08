"""Colours, fonts, paths and default values used across the app."""

from pathlib import Path

# ── Storage paths ──────────────────────────────────────────────────────────────
DATA_DIR   = Path.home() / ".lore_forge"
NODES_FILE = DATA_DIR / "nodes.json"
IMAGES_DIR = DATA_DIR / "images"
CONFIG_FILE = DATA_DIR / "config.json"

# ── Theme ──────────────────────────────────────────────────────────────────────
BG_DARK   = "#12121e"
BG_MID    = "#100f24"
BG_PANEL  = "#15161e"
BG_CARD   = "#1e1e35"
BG_HOVER  = "#252545"
ACCENT    = "#244395"
ACCENT2   = "#752877"
SUCCESS   = "#2c5926"
TEXT      = "#eaeaea"
TEXT_DIM  = "#7a7a99"
TAG_BG    = "#2a2a50"

FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_HEAD  = ("Segoe UI", 11, "bold")
FONT_BODY  = ("Segoe UI", 10)
FONT_SMALL = ("Segoe UI", 9)

DEFAULT_NODES = ["Characters", "Places", "Stories"]

# Activity types
ACTIVITY_ICONS = {"essay": "", "artwork": "", "reference": ""}
ACTIVITY_LABELS = {"essay": "Essay", "artwork": "Artwork", "reference": "References"}
ACTIVITY_COLORS = {"essay": SUCCESS, "artwork": ACCENT, "reference": ACCENT2}
TAB_INDEX = {"essay": 0, "artwork": 1, "reference": 2}