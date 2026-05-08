"""User-editable activity prompts loaded from activities.json."""

import json
import random
from pathlib import Path

from .constants import DATA_DIR


DEFAULT_ACTIVITIES = {
    "essay": [
        {
            "title": "Write an Origin Story",
            "prompt": "Craft a short prose piece exploring how this subject came to be. "
                      "Focus on a single defining moment or turning point that shaped its identity."
        },
        {
            "title": "A Day in the Life",
            "prompt": "Write a first-person or close-third account of an ordinary day for this subject. "
                      "Let small details reveal character, culture, or place."
        },
        {
            "title": "Secrets & Hidden Depths",
            "prompt": "Write an essay uncovering something not immediately obvious about this subject — "
                      "a hidden flaw, a buried history, or a contradiction that makes it more interesting."
        },
        {
            "title": "Relationships & Tensions",
            "prompt": "Explore how this subject connects to or conflicts with others in your world. "
                      "Who does it rely on? Who fears it? Who misunderstands it?"
        },
        {
            "title": "Legacy & Mythology",
            "prompt": "Write a short piece about how this subject is remembered, mythologized, or "
                      "misrepresented by others in your world long after the fact."
        },
    ],
    "artwork": [
        {
            "title": "Visual Character Sheet",
            "prompt": "Create or upload a full reference image showing this subject from multiple angles "
                      "or in different moods. Include at least one detail close-up."
        },
        {
            "title": "Scene Illustration",
            "prompt": "Illustrate a defining scene or moment — something that captures the emotional "
                      "core of this subject in a single image."
        },
        {
            "title": "Colour Palette & Mood Board",
            "prompt": "Put together a visual that establishes the colour language of this subject: "
                      "dominant tones, accent colours, textures, and lighting mood."
        },
        {
            "title": "Concept Variations",
            "prompt": "Upload two or three concept sketches exploring different visual directions "
                      "for this subject before committing to a final design."
        },
        {
            "title": "Environment & Context",
            "prompt": "Create an image showing where this subject lives, works, or belongs — "
                      "the space around it should say as much as the subject itself."
        },
    ],
    "reference": [
        {
            "title": "Real-World Texture Hunt",
            "prompt": "Gather 3–5 reference photos focusing on materials and surfaces relevant to this "
                      "subject. Tag each with the texture name and a note on when to use it."
        },
        {
            "title": "Historical Parallels",
            "prompt": "Find real historical images that share aesthetic or thematic DNA with this subject. "
                      "Note the era, culture, and what specific element you're borrowing."
        },
        {
            "title": "Lighting & Atmosphere",
            "prompt": "Collect references specifically for the lighting conditions that best suit this "
                      "subject — golden hour, candlelight, overcast, dramatic shadow, etc."
        },
        {
            "title": "Fashion & Costume Details",
            "prompt": "Gather reference images of clothing, accessories, or material culture that "
                      "inform how this subject dresses or equips itself. Tag by garment type."
        },
        {
            "title": "Flora, Fauna & Environment",
            "prompt": "Source references of natural elements — plants, animals, weather, terrain — "
                      "that belong in the world of this subject. Tag by ecosystem or season."
        },
    ],
}


class ActivitiesManager:
    def __init__(self):
        self.filepath = DATA_DIR / "activities.json"
        self.data = self._load()

    def _load(self):
        if self.filepath.exists():
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    loaded = json.load(f)
                    if loaded and any(loaded.values()):
                        return loaded
            except Exception:
                pass
        # Write defaults if missing or corrupt
        self._save(DEFAULT_ACTIVITIES)
        return {k: v[:] for k, v in DEFAULT_ACTIVITIES.items()}

    def _save(self, data):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def get_categories(self):
        return [c for c in self.data.keys() if self.data[c]]

    def get_random(self, category=None):
        """Return (category, title, prompt) for a random activity."""
        cats = self.get_categories()
        if not cats:
            return None
        if category is None or category not in self.data or not self.data[category]:
            category = random.choice(cats)
        item = random.choice(self.data[category])
        return category, item["title"], item["prompt"]

    def reload(self):
        """Reload from disk (useful if the user edited the file externally)."""
        self.data = self._load()