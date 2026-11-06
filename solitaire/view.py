"""Visão somente leitura do jogo (RF27, RF31, RNF04).

É o único acesso que a estratégia automática recebe: só consultas, nenhum método
que altere o estado. Assim, "decidir" nunca pode virar "executar" por acidente.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional, Tuple

from .card import Card
from .location import LocationRef

if TYPE_CHECKING:  # evita importação circular
    from .game import Game


class GameView:
    __slots__ = ("_game",)

    def __init__(self, game: "Game") -> None:
        self._game = game

    def locations(self) -> Tuple[LocationRef, ...]:
        return self._game.locations()

    def cards_at(self, ref: LocationRef) -> Tuple[Card, ...]:
        return self._game.cards_at(ref)

    def is_empty(self, ref: LocationRef) -> bool:
        return self._game.is_empty(ref)

    def top_card(self, ref: LocationRef) -> Optional[Card]:
        return self._game.top_card(ref)

    def can_draw(self) -> bool:
        return self._game.can_draw()

    def can_move(self, card: Card, destination: LocationRef) -> bool:
        return self._game.can_move(card, destination)

    def location_of(self, card: Card) -> Optional[LocationRef]:
        return self._game.location_of(card)

    def is_face_up(self, card: Card) -> bool:
        return self._game.is_face_up(card)

    def sequence_from(self, card: Card) -> Tuple[Card, ...]:
        return self._game.sequence_from(card)

    def is_bottom_most_face_up(self, card: Card) -> bool:
        return self._game.is_bottom_most_face_up(card)

    def is_king_already_at_base(self, card: Card) -> bool:
        return self._game.is_king_already_at_base(card)

    @property
    def score(self) -> int:
        return self._game.score
