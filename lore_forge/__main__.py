"""Entry point for `python -m lore_forge`."""

from .app import LoreForge

if __name__ == "__main__":
    app = LoreForge()
    app.run()
