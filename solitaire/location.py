"""Locais do jogo (RF10, RF13, RF15, RF17, RF20).

Um local é uma pilha com identidade (tipo + índice). Todos os locais herdam de
``CardStack`` e, portanto, respondem de forma equivalente a "está vazio?",
"qual o topo?" etc. (RF10). O que depende do tipo (regras de empilhamento,
acessibilidade) fica em métodos polimórficos das subclasses, evitando cadeias de
``if tipo == ...``.

``LocationRef`` é uma referência imutável a um local. É o que o mundo externo
(interface, estratégia) usa para falar de locais, sem acesso às pilhas mutáveis.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Sequence

from .card import Card, Rank
from .stack import CardStack


class LocationKind(Enum):
    STOCK = "stock"            # monte
    WASTE = "waste"            # descarte
    FOUNDATION = "foundation"  # fundação
    COLUMN = "column"          # coluna do tableau


@dataclass(frozen=True)
class LocationRef:
    kind: LocationKind
    index: int = 0


STOCK_REF = LocationRef(LocationKind.STOCK)
WASTE_REF = LocationRef(LocationKind.WASTE)


def foundation_ref(index: int) -> LocationRef:
    return LocationRef(LocationKind.FOUNDATION, index)


def column_ref(index: int) -> LocationRef:
    return LocationRef(LocationKind.COLUMN, index)


class Location(CardStack, ABC):
    kind: LocationKind

    def __init__(self, index: int = 0) -> None:
        super().__init__()
        self._index = index

    @property
    def index(self) -> int:
        return self._index

    @property
    def ref(self) -> LocationRef:
        return LocationRef(self.kind, self._index)

    @abstractmethod
    def can_accept(self, cards: Sequence[Card]) -> bool:
        """Este local aceitaria receber ``cards`` (na ordem, base -> topo)?

        Só trata das regras de empilhamento do destino (RF13, RF15, RF17).
        """

    def is_accessible(self, card: Card) -> bool:
        """A carta está acessível para movimentação direta?

        Padrão: apenas a carta do topo, se estiver visível.
        """
        return (
            not self.is_empty()
            and card is self.peek()
            and self.is_face_up(card)
        )

    # Consultas específicas do tableau: nos demais locais, não se aplicam.
    def is_bottom_most_face_up(self, card: Card) -> bool:
        return False

    def is_king_already_at_base(self, card: Card) -> bool:
        return False

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self._index}, {len(self)} cartas)"


class Stock(Location):
    kind = LocationKind.STOCK

    def can_accept(self, cards: Sequence[Card]) -> bool:
        return False  # o monte só perde cartas, pela compra


class Waste(Location):
    kind = LocationKind.WASTE

    def can_accept(self, cards: Sequence[Card]) -> bool:
        return False  # RF13: o descarte só recebe cartas pela compra


class Foundation(Location):
    kind = LocationKind.FOUNDATION

    def can_accept(self, cards: Sequence[Card]) -> bool:
        # RF15: uma carta por vez; vazia só aceita Ás; senão, mesmo naipe e rank acima.
        if len(cards) != 1:
            return False
        card = cards[0]
        if self.is_empty():
            return card.rank is Rank.ACE
        top = self.peek()
        return card.has_same_suit_as(top) and card.is_immediately_above(top)


class Column(Location):
    """Coluna do tableau, com as consultas do RF20 (todas somente leitura)."""

    kind = LocationKind.COLUMN

    def can_accept(self, cards: Sequence[Card]) -> bool:
        # RF17: vazia só aceita Rei; senão, rank imediatamente inferior e cor diferente.
        if not cards:
            return False
        first = cards[0]
        if self.is_empty():
            return first.rank is Rank.KING
        top = self.peek()
        return (
            self.is_face_up(top)
            and first.is_immediately_below(top)
            and not first.has_same_color_as(top)
        )

    def is_accessible(self, card: Card) -> bool:
        # Na coluna, qualquer carta visível pode ser movida (com o que está sobre ela).
        return card in self and self.is_face_up(card)

    def is_bottom_most_face_up(self, card: Card) -> bool:
        """A carta é a visível mais próxima da base da coluna?"""
        if card not in self or not self.is_face_up(card):
            return False
        return all(not self.is_face_up(c) for c in self.cards[: self.index_of(card)])

    def is_king_already_at_base(self, card: Card) -> bool:
        """Rei visível na base da coluna (movê-lo para coluna vazia não traz ganho)."""
        return (
            card in self
            and card.rank is Rank.KING
            and self.index_of(card) == 0
            and self.is_face_up(card)
        )
