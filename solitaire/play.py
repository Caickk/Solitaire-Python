"""Jogadas: pedidos de ação, de quem quer que venham (RF21, RF29, RF31, RNF02).

Uma ``Play`` descreve o que se quer fazer, sem alterar nada. Tanto a interface
(jogador) quanto a estratégia automática produzem ``Play``; o ``Game`` as valida
e executa pelo mesmo caminho. Cada tipo sabe dizer se é legal e construir a ação
correspondente, então o ``Game`` não precisa de verificações por tipo (RNF02).
``NoPlay`` é o Null Object: usado quando não há jogada ou a estratégia está
desativada.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from .action import Action, CompositeAction, NullAction
from .board import Board
from .card import Card
from .location import LocationRef
from .moves import DrawAction, MoveAction, RevealAction


class Play(ABC):
    @abstractmethod
    def is_legal(self, board: Board) -> bool:
        """Consulta somente leitura."""

    @abstractmethod
    def build_action(self, board: Board) -> Action:
        """Monta a ação (ainda não executada). Só é chamada se a jogada é legal."""


@dataclass(frozen=True)
class DrawPlay(Play):
    """Comprar a carta do topo do monte (RF11)."""

    def is_legal(self, board: Board) -> bool:
        return not board.stock.is_empty()

    def build_action(self, board: Board) -> Action:
        return DrawAction(board.stock, board.waste)


@dataclass(frozen=True)
class MovePlay(Play):
    """Mover uma carta (e o que está sobre ela) para um local (RF18, RF21)."""

    card: Card
    destination: LocationRef

    def is_legal(self, board: Board) -> bool:
        return board.can_move(self.card, self.destination)

    def build_action(self, board: Board) -> Action:
        source = board.location_of(self.card)
        target = board.get(self.destination)
        move = MoveAction(self.card, source, target)
        position = source.index_of(self.card)
        # RF19/RF23: se a saída deixa uma carta oculta no topo da origem, ela é
        # revelada como parte da MESMA jogada.
        if position > 0 and not source.is_face_up(source.cards[position - 1]):
            return CompositeAction([move, RevealAction(source)])
        return move


@dataclass(frozen=True)
class NoPlay(Play):
    """Nenhuma jogada (RF24, RF28)."""

    def is_legal(self, board: Board) -> bool:
        return True

    def build_action(self, board: Board) -> Action:
        return NullAction()
