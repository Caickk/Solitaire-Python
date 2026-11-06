"""Ações concretas do jogo: comprar, mover e revelar (RF11, RF12, RF18, RF19)."""

from __future__ import annotations

from typing import Optional, Tuple

from .action import Action, ActionError
from .card import Card
from .location import Location


class DrawAction(Action):
    """Compra: a carta do topo do monte vai, visível, para o topo do descarte.

    Desfazer devolve exatamente a mesma carta ao topo do monte (RF12), virada
    para baixo, e a remove do descarte.
    """

    def __init__(self, stock: Location, waste: Location) -> None:
        super().__init__()
        self._stock = stock
        self._waste = waste
        self._card: Optional[Card] = None

    @property
    def card(self) -> Optional[Card]:
        return self._card

    def _apply(self) -> None:
        if self._stock.is_empty():
            raise ActionError("O monte está vazio.")
        card = self._stock.peek()
        self._waste.push(card, face_up=True)
        self._stock.pop()
        self._card = card

    def _revert(self) -> None:
        if self._waste.is_empty() or self._waste.peek() is not self._card:
            raise ActionError("O topo do descarte não é a carta comprada.")
        self._waste.pop()
        self._stock.push(self._card, face_up=False)

    def __repr__(self) -> str:
        return f"DrawAction({self._card!r})"


class MoveAction(Action):
    """Move uma carta e tudo o que está sobre ela, na mesma ordem (RF18).

    As cartas movidas sempre estão visíveis (cartas ocultas não são acessíveis).
    """

    def __init__(self, card: Card, source: Location, destination: Location) -> None:
        super().__init__()
        self._card = card
        self._source = source
        self._destination = destination
        self._moved: Tuple[Card, ...] = ()

    @property
    def moved_cards(self) -> Tuple[Card, ...]:
        return self._moved

    def _apply(self) -> None:
        if self._source is self._destination:
            raise ActionError("Origem e destino são o mesmo local.")
        if self._card not in self._source:
            raise ActionError(f"{self._card!r} não está na origem.")
        if not self._source.is_face_up(self._card):
            raise ActionError(f"{self._card!r} está oculta.")
        sequence = self._source.sequence_from(self._card)
        self._destination.push_sequence(sequence, face_up=True)  # valida antes de alterar
        self._source.remove_sequence_from(self._card)
        self._moved = sequence

    def _revert(self) -> None:
        first = self._moved[0]
        if first not in self._destination or self._destination.sequence_from(first) != self._moved:
            raise ActionError("O destino não termina com a sequência movida.")
        self._destination.remove_sequence_from(first)
        self._source.push_sequence(self._moved, face_up=True)

    def __repr__(self) -> str:
        return f"MoveAction({self._card!r}: {self._source!r} -> {self._destination!r})"


class RevealAction(Action):
    """Revela a carta oculta do topo de um local (RF19). Desfazer a oculta de novo."""

    def __init__(self, location: Location) -> None:
        super().__init__()
        self._location = location
        self._card: Optional[Card] = None

    @property
    def card(self) -> Optional[Card]:
        return self._card

    def _apply(self) -> None:
        if self._location.is_empty():
            raise ActionError("Não há carta para revelar.")
        card = self._location.peek()
        if self._location.is_face_up(card):
            raise ActionError("A carta do topo já está visível.")
        self._location.set_top_face_up(True)
        self._card = card

    def _revert(self) -> None:
        if (
            self._location.is_empty()
            or self._location.peek() is not self._card
            or not self._location.is_face_up(self._card)
        ):
            raise ActionError("O topo não é a carta revelada por esta ação.")
        self._location.set_top_face_up(False)

    def __repr__(self) -> str:
        return f"RevealAction({self._card!r})"
