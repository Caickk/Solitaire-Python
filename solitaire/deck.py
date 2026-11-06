"""Baralho completo e embaralhamento (RF04, RF07)."""

from __future__ import annotations

import random
from typing import Iterator, List, Optional, Tuple

from .card import Card


class Deck:
    """Sequência ordenada de cartas, da base ao topo.

    O gerador de números aleatórios pode ser injetado, o que permite partidas
    reprodutíveis (por exemplo, nas simulações automáticas e nos testes).
    """

    def __init__(self, cards: Optional[List[Card]] = None) -> None:
        self._cards: List[Card] = list(Card.all_cards()) if cards is None else list(cards)

    @classmethod
    def standard(cls) -> "Deck":
        return cls()

    def shuffle(self, rng: Optional[random.Random] = None) -> None:
        (rng or random).shuffle(self._cards)

    @property
    def cards(self) -> Tuple[Card, ...]:
        """Visão imutável das cartas (a ordem importa)."""
        return tuple(self._cards)

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(self._cards)
