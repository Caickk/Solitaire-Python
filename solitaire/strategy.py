"""Estratégias de jogo automático (RF28-RF31, RNF04).

Padrão Strategy: ``Game`` conhece apenas a interface ``Strategy``. Trocar por
``NullStrategy`` desativa o recurso sem nenhum tratamento especial no jogo,
porque ela também responde com uma ``Play`` (a ``NoPlay``).

A estratégia só DECIDE: recebe uma ``GameView`` (consultas) e devolve uma
``Play``. Quem valida e executa é o ``Game`` (RF31).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from .location import WASTE_REF, LocationKind, LocationRef
from .play import DrawPlay, MovePlay, NoPlay, Play
from .view import GameView


class Strategy(ABC):
    @abstractmethod
    def suggest(self, view: GameView) -> Play:
        """Sugere uma jogada usando apenas consultas somente leitura."""


class NullStrategy(Strategy):
    """Estratégia desativada: nunca sugere jogada (RF28, RNF02)."""

    def suggest(self, view: GameView) -> Play:
        return NoPlay()


class AutoStrategy(Strategy):
    """Avalia as prioridades do RF29 na ordem e devolve a primeira possível.

    Desempate dentro de uma mesma prioridade: determinístico, pela ordem dos
    locais (fundações e colunas por índice; cartas da base ao topo).
    """

    def __init__(self) -> None:
        # Uma regra por item do RF29, na ordem de prioridade.
        self._rules = (
            self._draw_when_waste_is_empty,      # 1
            self._waste_to_foundation,           # 2
            self._waste_to_tableau,              # 3
            self._column_top_to_foundation,      # 4
            self._tableau_move_with_gain,        # 5
            self._draw_when_nothing_else,        # 6
        )

    def suggest(self, view: GameView) -> Play:
        for rule in self._rules:
            play = rule(view)
            if play is not None:
                return play
        return NoPlay()                          # 7

    # --- auxiliares -----------------------------------------------------------

    @staticmethod
    def _refs(view: GameView, kind: LocationKind) -> Tuple[LocationRef, ...]:
        return tuple(ref for ref in view.locations() if ref.kind is kind)

    def _first_move(self, view: GameView, card, kind: LocationKind) -> Optional[Play]:
        for destination in self._refs(view, kind):
            if view.can_move(card, destination):
                return MovePlay(card, destination)
        return None

    # --- prioridades ----------------------------------------------------------

    def _draw_when_waste_is_empty(self, view: GameView) -> Optional[Play]:
        if view.is_empty(WASTE_REF) and view.can_draw():
            return DrawPlay()
        return None

    def _waste_to_foundation(self, view: GameView) -> Optional[Play]:
        top = view.top_card(WASTE_REF)
        return None if top is None else self._first_move(view, top, LocationKind.FOUNDATION)

    def _waste_to_tableau(self, view: GameView) -> Optional[Play]:
        top = view.top_card(WASTE_REF)
        return None if top is None else self._first_move(view, top, LocationKind.COLUMN)

    def _column_top_to_foundation(self, view: GameView) -> Optional[Play]:
        for column in self._refs(view, LocationKind.COLUMN):
            top = view.top_card(column)
            if top is None:
                continue
            play = self._first_move(view, top, LocationKind.FOUNDATION)
            if play is not None:
                return play
        return None

    def _tableau_move_with_gain(self, view: GameView) -> Optional[Play]:
        """Só move se revelar uma carta ou esvaziar a coluna (RF30).

        Só a carta visível mais próxima da base pode trazer esse ganho: mover
        qualquer outra não revela nem esvazia nada. Um Rei que já está na base
        não é movido (RF20, RF30), o que impede idas e voltas sem progresso.
        """
        columns = self._refs(view, LocationKind.COLUMN)
        for source in columns:
            for card in view.cards_at(source):
                if not view.is_bottom_most_face_up(card):
                    continue
                if view.is_king_already_at_base(card):
                    continue
                for destination in columns:
                    if destination != source and view.can_move(card, destination):
                        return MovePlay(card, destination)
        return None

    def _draw_when_nothing_else(self, view: GameView) -> Optional[Play]:
        return DrawPlay() if view.can_draw() else None
