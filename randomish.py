"""
Randomish style selector - ensures all style bases are used before any repeat.

Maintains a shuffled queue of STYLE_BASES. Each call pops one base and combines
it with random phrases. When the queue empties, it reshuffles and starts over.

This gives you the variety of random phrase combinations while guaranteeing
you won't see "Van Gogh" twice until you've cycled through all 226+ bases.
"""

import json
import os
import secrets
from collections import deque
from pathlib import Path

QUEUE_FILE = Path(__file__).parent / "randomish_queue.json"


def _shuffle(items: list) -> list:
    """Cryptographically random shuffle using secrets module."""
    items = items.copy()
    shuffled = []
    while items:
        choice = secrets.choice(items)
        items.remove(choice)
        shuffled.append(choice)
    return shuffled


def _load_queue(style_bases: list) -> deque:
    """Load queue from disk, or create a new shuffled one if empty/missing."""
    if QUEUE_FILE.exists():
        try:
            with open(QUEUE_FILE) as f:
                data = json.load(f)
                if data:
                    return deque(data)
        except (json.JSONDecodeError, IOError):
            pass
    return deque(_shuffle(style_bases))


def _save_queue(queue: deque) -> None:
    """Persist queue to disk."""
    with open(QUEUE_FILE, "w") as f:
        json.dump(list(queue), f, indent=2)


def get_random_style(style_bases: list, style_phrases: list) -> str:
    """
    Get a random style that won't repeat bases until all have been used.
    
    Args:
        style_bases: List of base styles (e.g., "Van Gogh", "Cubist still life")
        style_phrases: List of modifier phrases to combine with the base
    
    Returns:
        A style string like "Van Gogh, bold colors, emotional resonance"
    """
    queue = _load_queue(style_bases)
    
    if not queue:
        queue = deque(_shuffle(style_bases))
    
    base = queue.popleft()
    _save_queue(queue)
    
    num_phrases = secrets.randbelow(3) + 1  # 1-3 phrases
    phrases = ", ".join(secrets.choice(style_phrases) for _ in range(num_phrases))
    
    return f"{base}, {phrases}"


def peek_remaining() -> int:
    """Return how many styles remain in the queue before it resets."""
    if QUEUE_FILE.exists():
        try:
            with open(QUEUE_FILE) as f:
                return len(json.load(f))
        except (json.JSONDecodeError, IOError):
            pass
    return 0


def reset_queue() -> None:
    """Clear the queue file to force a fresh shuffle on next use."""
    if QUEUE_FILE.exists():
        QUEUE_FILE.unlink()
