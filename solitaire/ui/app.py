"""Janela do Solitaire (Tkinter).

A janela só desenha o estado e repassa eventos: não contém regras (RNF03). Ela se
registra como observador do ``Game`` e se redesenha a cada mudança (RF26). A
pontuação (RF03) não é exibida.
"""

from __future__ import annotations

import tkinter as tk
from typing import Optional

from ..card import Card, Color, Suit
from ..game import Game, GameEvent
from ..location import STOCK_REF
from ..strategy import AutoStrategy, NullStrategy
from .drag import DragController
from .layout import (CANVAS_H, CANVAS_W, CARD_H, CARD_W, UP_OFFSET, Layout)

FELT = "#0b6b3a"
SLOT_OUTLINE = "#2e8b57"
CARD_FACE = "#fdfdfd"
CARD_BACK = "#1f4e9c"
CARD_BACK_INNER = "#3f6fc0"
INK = {Color.RED: "#c62828", Color.BLACK: "#1a1a1a"}
VALID_COLOR = "#7CFC00"
INVALID_COLOR = "#ff5252"

SUIT_GLYPH = {Suit.HEARTS: "\u2665", Suit.DIAMONDS: "\u2666", Suit.CLUBS: "\u2663", Suit.SPADES: "\u2660"}
RANK_FONT = ("Arial", 13, "bold")
SUIT_FONT = ("Segoe UI Symbol", 13, "bold")
BIG_SUIT_FONT = ("Segoe UI Symbol", 30)


class SolitaireApp:
    def __init__(self, root: tk.Misc, game: Optional[Game] = None) -> None:
        self.root = root
        self.game = game if game is not None else Game()
        self.layout = Layout(self.game.view)
        self.drag = DragController(self.game, self.layout)

        bar = tk.Frame(root)
        bar.pack(side=tk.TOP, fill=tk.X)
        self.undo_button = tk.Button(bar, text="Desfazer (Ctrl+Z)", command=self.undo)
        self.undo_button.pack(side=tk.LEFT, padx=4, pady=4)
        self.auto_button = tk.Button(bar, text="Jogada automática (A)", command=self.auto_play)
        self.auto_button.pack(side=tk.LEFT, padx=4, pady=4)
        self.auto_enabled = tk.BooleanVar(master=root, value=True)
        tk.Checkbutton(
            bar, text="Jogo automático ativado", variable=self.auto_enabled,
            command=self._toggle_auto,
        ).pack(side=tk.LEFT, padx=8)
        self.status = tk.Label(bar, text="", font=("Arial", 12, "bold"), fg="#006400")
        self.status.pack(side=tk.RIGHT, padx=8)

        self.canvas = tk.Canvas(root, width=CANVAS_W, height=CANVAS_H, bg=FELT, highlightthickness=0)
        self.canvas.pack(side=tk.TOP)
        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        root.bind("<Control-z>", lambda _e: self.undo())
        root.bind("<a>", lambda _e: self.auto_play())

        self.game.add_observer(self._on_game_event)
        self.redraw()

    # --- comandos (apenas delegam ao jogo) --------------------------------------------

    def undo(self) -> None:
        self.game.undo()

    def auto_play(self) -> None:
        self.game.auto_play()

    def _toggle_auto(self) -> None:
        self.game.set_strategy(AutoStrategy() if self.auto_enabled.get() else NullStrategy())

    # --- eventos ------------------------------------------------------------------------

    def _on_game_event(self, _event: GameEvent) -> None:
        self.redraw()

    def _on_press(self, event) -> None:
        self.drag.press(event.x, event.y)
        self.redraw()

    def _on_motion(self, event) -> None:
        self.drag.motion(event.x, event.y)
        self.redraw()

    def _on_release(self, event) -> None:
        self.drag.release(event.x, event.y)
        self.redraw()

    # --- desenho --------------------------------------------------------------------------

    def redraw(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        self._draw_slots()
        dragged = set(self.drag.state.cards) if self.drag.state else set()
        for placed in self.layout.placed_cards():
            if placed.card not in dragged:
                self._draw_card(placed.x, placed.y, placed.card, placed.face_up)
        self._draw_drag()
        self._update_controls()

    def _draw_slots(self) -> None:
        for ref in self.game.view.locations():
            x, y, w, h = self.layout.slot_rect(ref)
            self.canvas.create_rectangle(x, y, x + w, y + h, outline=SLOT_OUTLINE, width=2, dash=(4, 3))
        if self.game.can_start_new_game():                       # RF01
            x, y, w, h = self.layout.slot_rect(STOCK_REF)
            self.canvas.create_text(x + w // 2, y + h // 2, text="Nova\npartida",
                                    fill="white", font=("Arial", 11, "bold"), justify=tk.CENTER)

    def _draw_card(self, x: int, y: int, card: Card, face_up: bool) -> None:
        c = self.canvas
        if not face_up:
            c.create_rectangle(x, y, x + CARD_W, y + CARD_H, fill=CARD_BACK, outline="#0d2a5c", width=2)
            c.create_rectangle(x + 6, y + 6, x + CARD_W - 6, y + CARD_H - 6, outline=CARD_BACK_INNER, width=2)
            return
        ink = INK[card.color]
        glyph = SUIT_GLYPH[card.suit]
        c.create_rectangle(x, y, x + CARD_W, y + CARD_H, fill=CARD_FACE, outline="#333333", width=2)
        c.create_text(x + 6, y + 4, text=card.rank.symbol, anchor="nw", fill=ink, font=RANK_FONT)
        c.create_text(x + CARD_W - 6, y + 4, text=glyph, anchor="ne", fill=ink, font=SUIT_FONT)
        c.create_text(x + CARD_W // 2, y + CARD_H // 2 + 12, text=glyph, fill=ink, font=BIG_SUIT_FONT)

    def _draw_drag(self) -> None:
        state = self.drag.state
        if state is None:
            return
        if state.target is not None and state.target != state.origin:   # RF32
            x, y, w, h = self.layout.target_rect(state.target)
            color = VALID_COLOR if state.valid else INVALID_COLOR
            self.canvas.create_rectangle(x - 4, y - 4, x + w + 4, y + h + 4, outline=color, width=4)
        x0, y0 = state.x - state.grab_dx, state.y - state.grab_dy
        for i, card in enumerate(state.cards):
            self._draw_card(x0, y0 + i * UP_OFFSET, card, True)

    def _update_controls(self) -> None:
        self.undo_button.config(state=tk.NORMAL if self.game.can_undo() else tk.DISABLED)
        won = self.game.is_won
        self.status.config(text="Vitória! Clique no monte vazio para jogar de novo." if won else "")


def main() -> None:
    root = tk.Tk()
    root.title("Solitaire")
    root.resizable(False, False)
    SolitaireApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
