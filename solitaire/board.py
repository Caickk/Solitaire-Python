"""Tabuleiro: conjunto de locais e regras de movimentação entre eles (RF10, RF21)."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .card import Card
from .location import Column, Foundation, Location, LocationRef, Stock, Waste

COLUMN_COUNT = 7
FOUNDATION_COUNT = 4


class Board:
    def __init__(self) -> None:
        self.stock = Stock()
        self.waste = Waste()
        self.foundations: Tuple[Foundation, ...] = tuple(
            Foundation(i) for i in range(FOUNDATION_COUNT)
        )
        self.columns: Tuple[Column, ...] = tuple(Column(i) for i in range(COLUMN_COUNT))
        self._by_ref: Dict[LocationRef, Location] = {loc.ref: loc for loc in self.locations}

    @property
    def locations(self) -> Tuple[Location, ...]:
        return (self.stock, self.waste, *self.foundations, *self.columns)

    def get(self, ref: LocationRef) -> Location:
        try:
            return self._by_ref[ref]
        except KeyError:
            raise ValueError(f"Local inexistente: {ref!r}") from None

    def all_cards(self) -> Tuple[Card, ...]:
        return tuple(card for loc in self.locations for card in loc.cards)

    def clear(self) -> None:
        for loc in self.locations:
            while not loc.is_empty():
                loc.pop()

    def location_of(self, card: Card, *, accessible_only: bool = True) -> Optional[Location]:
        """Local onde a carta está.

        Com ``accessible_only`` (padrão), só responde se a carta estiver acessível
        para movimentação; caso contrário, devolve ``None``.
        """
        for loc in self.locations:
            if card in loc:
                if accessible_only and not loc.is_accessible(card):
                    return None
                return loc
        return None

    def can_move(self, card: Card, destination: LocationRef) -> bool:
        """Regras de legalidade (RF21): a carta (com o que está sobre ela) pode ir ao destino?"""
        source = self.location_of(card)
        if source is None:
            return False
        target = self.get(destination)
        if source is target:
            return False
        return target.can_accept(source.sequence_from(card))
