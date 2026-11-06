"""Infraestrutura de ações reversíveis (RF22, RF23, RF24, RNF02).

Padrões usados:
- Command: cada jogada é um objeto com ``do()`` e ``undo()``.
- Template Method: ``Action`` controla o ciclo de vida (não executar duas vezes,
  não desfazer o que não foi feito); as subclasses só implementam ``_apply`` e
  ``_revert``.
- Composite: ``CompositeAction`` trata várias ações como uma única jogada.
- Null Object: ``NullAction`` é uma ação sem efeito. Para o resto do jogo, ela é
  uma ação como qualquer outra, sem verificações especiais (RNF02).

As ações NÃO decidem se uma jogada é legal (isso é do ``Game``, RF21); elas só
verificam pré-condições estruturais, para falhar de forma explícita se o estado
estiver inconsistente.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, Tuple


class ActionError(Exception):
    """Ação executada ou desfeita em estado inadequado."""


class Action(ABC):
    def __init__(self) -> None:
        self._done = False

    @property
    def is_done(self) -> bool:
        return self._done

    @property
    def has_effect(self) -> bool:
        """Esta ação muda o estado do jogo? (``False`` para a ação nula.)"""
        return True

    def do(self) -> None:
        if self._done:
            raise ActionError("A ação já foi executada.")
        self._apply()
        self._done = True

    def undo(self) -> None:
        if not self._done:
            raise ActionError("A ação ainda não foi executada.")
        self._revert()
        self._done = False

    @abstractmethod
    def _apply(self) -> None:
        """Executa. Se falhar, deve deixar o estado como estava."""

    @abstractmethod
    def _revert(self) -> None:
        """Restaura exatamente o estado anterior a ``_apply``."""


class NullAction(Action):
    """Ação sem efeito (RF24): jogo automático sem jogada ou estratégia desativada."""

    @property
    def has_effect(self) -> bool:
        return False

    def _apply(self) -> None:
        pass

    def _revert(self) -> None:
        pass

    def __repr__(self) -> str:
        return "NullAction()"


class CompositeAction(Action):
    """Conjunto de ações tratado como uma única jogada (RF23).

    Executa na ordem e desfaz na ordem inversa. Se alguma falhar ao executar,
    as já executadas são desfeitas, então a jogada composta é "tudo ou nada".
    """

    def __init__(self, actions: Iterable[Action]) -> None:
        super().__init__()
        self._actions: Tuple[Action, ...] = tuple(actions)

    @property
    def actions(self) -> Tuple[Action, ...]:
        return self._actions

    @property
    def has_effect(self) -> bool:
        return any(a.has_effect for a in self._actions)

    def _apply(self) -> None:
        executed = []
        try:
            for action in self._actions:
                action.do()
                executed.append(action)
        except Exception:
            for action in reversed(executed):
                action.undo()
            raise

    def _revert(self) -> None:
        for action in reversed(self._actions):
            action.undo()

    def __repr__(self) -> str:
        return f"CompositeAction({list(self._actions)!r})"
