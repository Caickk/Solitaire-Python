"""Pilha de cartas (RF08, RF09) e visibilidade por posição (RNF01).

``CardStack`` é a estrutura única usada por monte, descarte, fundações e
colunas do tableau. Ela preserva a ordem de colocação (base -> topo).

Visibilidade: cada posição da pilha guarda se a carta nela está virada para
cima. A informação acompanha a POSIÇÃO e é informada explicitamente a cada
``push``; ao sair da pilha, a carta não leva consigo o estado antigo. Assim, a
visibilidade sempre reflete a carta que está de fato na posição (RNF01).
"""

from __future__ import annotations

from typing import Iterable, Iterator, List, Tuple

from .card import Card


class EmptyStackError(IndexError):
    """Operação que exige ao menos uma carta, feita em pilha vazia."""


class CardStack:
    def __init__(self) -> None:
        self._cards: List[Card] = []
        self._face_up: List[bool] = []

    # --- consultas (somente leitura: RF09, RF27) ------------------------------

    def is_empty(self) -> bool:
        return not self._cards

    def peek(self) -> Card:
        """Carta do topo, sem removê-la."""
        if not self._cards:
            raise EmptyStackError("A pilha está vazia.")
        return self._cards[-1]

    @property
    def cards(self) -> Tuple[Card, ...]:
        """Cartas da base ao topo (cópia imutável)."""
        return tuple(self._cards)

    def __len__(self) -> int:
        return len(self._cards)

    def __iter__(self) -> Iterator[Card]:
        return iter(tuple(self._cards))

    def __contains__(self, card: object) -> bool:
        return any(c is card for c in self._cards)

    def index_of(self, card: Card) -> int:
        """Posição da carta (0 = base). ``ValueError`` se não estiver na pilha."""
        for i, c in enumerate(self._cards):
            if c is card:
                return i
        raise ValueError(f"{card!r} não está nesta pilha.")

    def is_face_up(self, card: Card) -> bool:
        return self._face_up[self.index_of(card)]

    def sequence_from(self, card: Card) -> Tuple[Card, ...]:
        """Cartas de ``card`` até o topo, na ordem da pilha."""
        return tuple(self._cards[self.index_of(card):])

    # --- modificações -----------------------------------------------------------

    def push(self, card: Card, face_up: bool = True) -> None:
        """Coloca ``card`` no topo, com a visibilidade informada."""
        if card in self:
            raise ValueError(f"{card!r} já está nesta pilha.")
        self._cards.append(card)
        self._face_up.append(face_up)

    def pop(self) -> Card:
        """Remove e devolve a carta do topo (única remoção direta, RF08)."""
        if not self._cards:
            raise EmptyStackError("A pilha está vazia.")
        self._face_up.pop()
        return self._cards.pop()

    def push_sequence(self, cards: Iterable[Card], face_up: bool = True) -> None:
        """Coloca uma sequência (na ordem dada) no topo, como uma unidade."""
        cards = tuple(cards)
        if len({id(c) for c in cards}) != len(cards) or any(c in self for c in cards):
            raise ValueError("A sequência repete cartas ou contém carta já presente.")
        for card in cards:
            self.push(card, face_up)

    def remove_sequence_from(self, card: Card) -> Tuple[Card, ...]:
        """Remove e devolve ``card`` e tudo que está sobre ela (RF18).

        É a exceção à regra de que só o topo sai da pilha.
        """
        index = self.index_of(card)
        removed = tuple(self._cards[index:])
        del self._cards[index:]
        del self._face_up[index:]
        return removed

    def set_top_face_up(self, face_up: bool) -> None:
        """Altera a visibilidade da carta do topo (usado ao revelar/ocultar)."""
        if not self._cards:
            raise EmptyStackError("A pilha está vazia.")
        self._face_up[-1] = face_up
