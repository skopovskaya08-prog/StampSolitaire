# Stamp Solitaire

A picture-based solitaire card game written in Python with Pygame. Cards are styled as postage stamps; instead of suits, each card shows a picture that belongs to a category (fruits, animals, sport, sweets, and more).

No ads, no move limits, unlimited undo.

## How to play

- The table has 5 columns. Hidden cards are face down; the bottom card of each column is face up.
- Face-up cards of the **same category** can be stacked on each other. Any picture can go on an empty column.
- Click the deck (top right) to draw a card. When the deck is empty, click it again to recycle the drawn cards.
- **Category cards** (with a star) go into an empty slot in the middle row. Then collect all 5 pictures of that category into the slot. A completed category frees the slot.
- Clear every card from the table to win.

**Controls:** click a face-up card to select it (and any cards below it), then click a column or slot to move it there. **Hint** shows a possible move, **Undo** reverts moves, **New Game** starts over.

## Run it

Requires Python 3.10+.

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install pygame
python game.py
```

## Project structure

```
game.py      game logic, drawing and main loop
images/      card pictures (PNG)
```

## Roadmap

- Drag-and-drop instead of click-to-move
- Animations and sound
- More categories and difficulty levels
- Packaging as a standalone macOS app

## Credits

Card pictures: [Twemoji](https://github.com/jdecked/twemoji) by Twitter, Inc. and contributors, licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

## Author

Alisa Skopovskaia, Computer Science (Cyber Security) student at Asia Pacific University, Malaysia.
