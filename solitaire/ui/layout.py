"""Geometria da mesa: onde cada carta e cada local ficam na tela.

Código puro (sem Tkinter), para poder ser testado sem janela. Só usa consultas
somente leitura do jogo (``GameView``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from ..card import Card
from ..location import LocationKind, LocationRef
from ..view import GameView

CARD_W, CARD_H = 72, 100
H_GAP, V_GAP = 18, 30
MARGIN = 20
DOWN_OFFSET = 14   # deslocamento entre cartas viradas para baixo, numa coluna
UP_OFFSET = 28     # deslocamento entre cartas visíveis, numa coluna
TABLEAU_Y = MARGIN + CARD_H + V_GAP
CANVAS_W = 2 * MARGIN + 7 * CARD_W + 6 * H_GAP
CANVAS_H = 700

Rect = Tuple[int, int, int, int]  # x, y, largura, altura


@dataclass(frozen=True)
class PlacedCard:
    card: Card
    ref: LocationRef
    x: int
    y: int
    face_up: bool

    def contains(self, px: int, py: int) -> bool:
        return self.x <= px < self.x + CARD_W and self.y <= py < self.y + CARD_H


class Layout:
    def __init__(self, view: GameView) -> None:
        self._view = view

    # --- locais -------------------------------------------------------------------

    @staticmethod
    def _column_x(position: int) -> int:
        return MARGIN + position * (CARD_W + H_GAP)

    def slot_rect(self, ref: LocationRef) -> Rect:
        """Retângulo de uma carta na posição-base do local."""
        if ref.kind is LocationKind.STOCK:
            return (self._column_x(0), MARGIN, CARD_W, CARD_H)
        if ref.kind is LocationKind.WASTE:
            return (self._column_x(1), MARGIN, CARD_W, CARD_H)
        if ref.kind is LocationKind.FOUNDATION:
            return (self._column_x(3 + ref.index), MARGIN, CARD_W, CARD_H)
        return (self._column_x(ref.index), TABLEAU_Y, CARD_W, CARD_H)

    def target_rect(self, ref: LocationRef) -> Rect:
        """Área ocupada por um local (colunas crescem com suas cartas)."""
        x, y, w, h = self.slot_rect(ref)
        if ref.kind is LocationKind.COLUMN:
            placed = [p for p in self.placed_cards() if p.ref == ref]
            if placed:
                return (x, y, w, placed[-1].y + CARD_H - y)
        return (x, y, w, h)

    def location_at(self, px: int, py: int) -> Optional[LocationRef]:
        """Local sob o ponto (com folga nas bordas). Colunas se estendem para baixo."""
        half_h, half_v = H_GAP // 2, V_GAP // 2
        for ref in self._view.locations():
            x, y, w, h = self.slot_rect(ref)
            top = y - half_v
            bottom = float("inf") if ref.kind is LocationKind.COLUMN else y + h + half_v
            if x - half_h <= px < x + w + half_h and top <= py < bottom:
                return ref
        return None

    # --- cartas ---------------------------------------------------------------------

    def placed_cards(self) -> List[PlacedCard]:
        """Todas as cartas com posição, na ordem de desenho (a última fica por cima)."""
        placed: List[PlacedCard] = []
        for ref in self._view.locations():
            x, y, _, _ = self.slot_rect(ref)
            for card in self._view.cards_at(ref):
                face_up = self._view.is_face_up(card)
                placed.append(PlacedCard(card, ref, x, y, face_up))
                if ref.kind is LocationKind.COLUMN:
                    y += UP_OFFSET if face_up else DOWN_OFFSET
        return placed

    def card_at(self, px: int, py: int) -> Optional[PlacedCard]:
        """Carta visualmente mais acima sob o ponto."""
        for placed in reversed(self.placed_cards()):
            if placed.contains(px, py):
                return placed
        return None
