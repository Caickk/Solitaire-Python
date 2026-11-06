"""Controle do arraste com o mouse (RF32), sem Tkinter.

- Ao arrastar uma carta do tableau, todas as cartas sobre ela vão juntas (RF18).
  A sequência é "transportada" como texto serializado e reconstituída ao soltar,
  sem alterar identidade nem ordem das cartas (RNF05).
- Durante o arraste, a indicação de destino válido vem de ``Game.can_move``;
  esta classe não conhece nenhuma regra (RF21, RNF03).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from ..card import Card
from ..game import Game
from ..location import STOCK_REF, LocationRef
from ..serialization import deserialize_cards, serialize_cards
from .layout import Layout


@dataclass
class DragState:
    payload: str                 # sequência serializada (base -> topo)
    cards: Tuple[Card, ...]      # sequência reconstituída a partir do payload
    origin: LocationRef
    x: int                       # posição atual do cursor
    y: int
    grab_dx: int                 # onde, dentro da carta, ela foi agarrada
    grab_dy: int
    target: Optional[LocationRef] = None
    valid: bool = False


class DragController:
    def __init__(self, game: Game, layout: Layout) -> None:
        self._game = game
        self._layout = layout
        self.state: Optional[DragState] = None

    def press(self, x: int, y: int) -> bool:
        """Clique do mouse. Devolve ``True`` se um arraste começou."""
        sx, sy, w, h = self._layout.slot_rect(STOCK_REF)
        if sx <= x < sx + w and sy <= y < sy + h:
            self._game.draw()          # comprar; com o monte vazio, nova partida (RF01)
            return False
        placed = self._layout.card_at(x, y)
        if placed is None or self._game.location_of(placed.card) is None:
            return False               # nada aí, ou carta não acessível (oculta, etc.)
        payload = serialize_cards(self._game.sequence_from(placed.card))
        self.state = DragState(
            payload=payload,
            cards=deserialize_cards(payload),
            origin=placed.ref,
            x=x, y=y,
            grab_dx=x - placed.x,
            grab_dy=y - placed.y,
        )
        self.motion(x, y)
        return True

    def motion(self, x: int, y: int) -> None:
        state = self.state
        if state is None:
            return
        state.x, state.y = x, y
        state.target = self._layout.location_at(x, y)
        cards = deserialize_cards(state.payload)
        state.valid = state.target is not None and self._game.can_move(cards[0], state.target)

    def release(self, x: int, y: int) -> bool:
        """Soltar o botão. Devolve ``True`` se a jogada foi feita."""
        if self.state is None:
            return False
        self.motion(x, y)
        state, self.state = self.state, None
        if not state.valid:
            return False
        cards = deserialize_cards(state.payload)
        self._game.move(cards[0], state.target)   # o jogo valida de novo (RF21)
        return True

    def cancel(self) -> None:
        self.state = None
