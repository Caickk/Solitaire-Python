import random
import unittest

from solitaire.action import Action, ActionError, CompositeAction, NullAction
from solitaire.board import Board
from solitaire.card import Card, Rank, Suit
from solitaire.deck import Deck
from solitaire.moves import DrawAction, MoveAction, RevealAction


def snapshot(board):
    return tuple(
        tuple((c.id, loc.is_face_up(c)) for c in loc.cards) for loc in board.locations
    )


def deal(board, seed=0):
    deck = Deck()
    deck.shuffle(random.Random(seed))
    cards = list(deck.cards)
    for i, col in enumerate(board.columns):
        for j in range(i + 1):
            col.push(cards.pop(), face_up=(j == i))
    for c in cards:
        board.stock.push(c, face_up=False)


C = lambda r, s: Card.of(r, s)
KH, QC, JD, TS = C(Rank.KING, Suit.HEARTS), C(Rank.QUEEN, Suit.CLUBS), C(Rank.JACK, Suit.DIAMONDS), C(Rank.TEN, Suit.SPADES)


class DrawTests(unittest.TestCase):
    def test_rf11_draw_moves_top_to_waste_face_up(self):
        b = Board()
        b.stock.push(KH, False)
        b.stock.push(QC, False)
        a = DrawAction(b.stock, b.waste)
        a.do()
        self.assertIs(b.waste.peek(), QC)
        self.assertTrue(b.waste.is_face_up(QC))
        self.assertEqual(b.stock.cards, (KH,))

    def test_rf12_undo_returns_same_card_to_stock(self):
        b = Board()
        b.stock.push(KH, False)
        b.stock.push(QC, False)
        a = DrawAction(b.stock, b.waste)
        a.do()
        a.undo()
        self.assertIs(b.stock.peek(), QC)
        self.assertFalse(b.stock.is_face_up(QC))
        self.assertTrue(b.waste.is_empty())

    def test_draw_from_empty_stock_fails_without_change(self):
        b = Board()
        with self.assertRaises(ActionError):
            DrawAction(b.stock, b.waste).do()
        self.assertEqual(snapshot(b), snapshot(Board()))


class MoveTests(unittest.TestCase):
    def setUp(self):
        self.b = Board()
        self.src, self.dst = self.b.columns[0], self.b.columns[1]
        self.src.push(TS, False)
        self.src.push(KH, True)
        self.src.push(QC, True)
        self.src.push(JD, True)

    def test_rf18_moves_sequence_in_order(self):
        MoveAction(KH, self.src, self.dst).do()
        self.assertEqual(self.dst.cards, (KH, QC, JD))
        self.assertEqual(self.src.cards, (TS,))
        self.assertTrue(all(self.dst.is_face_up(c) for c in self.dst.cards))

    def test_move_single_top_card(self):
        MoveAction(JD, self.src, self.dst).do()
        self.assertEqual(self.dst.cards, (JD,))
        self.assertEqual(self.src.cards, (TS, KH, QC))

    def test_rf22_undo_restores_exact_state(self):
        before = snapshot(self.b)
        a = MoveAction(KH, self.src, self.dst)
        a.do()
        a.undo()
        self.assertEqual(snapshot(self.b), before)

    def test_hidden_card_cannot_move_and_state_is_kept(self):
        before = snapshot(self.b)
        with self.assertRaises(ActionError):
            MoveAction(TS, self.src, self.dst).do()
        with self.assertRaises(ActionError):
            MoveAction(KH, self.src, self.src).do()
        with self.assertRaises(ActionError):
            MoveAction(C(Rank.ACE, Suit.CLUBS), self.src, self.dst).do()
        self.assertEqual(snapshot(self.b), before)

    def test_lifecycle_errors(self):
        a = MoveAction(JD, self.src, self.dst)
        with self.assertRaises(ActionError):
            a.undo()
        a.do()
        with self.assertRaises(ActionError):
            a.do()
        a.undo()
        self.assertFalse(a.is_done)


class RevealTests(unittest.TestCase):
    def test_reveal_and_undo(self):
        b = Board()
        col = b.columns[0]
        col.push(KH, False)
        a = RevealAction(col)
        a.do()
        self.assertTrue(col.is_face_up(KH))
        a.undo()
        self.assertFalse(col.is_face_up(KH))

    def test_reveal_preconditions(self):
        col = Board().columns[0]
        with self.assertRaises(ActionError):
            RevealAction(col).do()
        col.push(KH, True)
        with self.assertRaises(ActionError):
            RevealAction(col).do()


class CompositeAndNullTests(unittest.TestCase):
    def test_rf23_move_plus_reveal_and_reverse_order_undo(self):
        b = Board()
        src, dst = b.columns[0], b.columns[1]
        src.push(TS, False)
        src.push(KH, True)
        before = snapshot(b)
        composite = CompositeAction([MoveAction(KH, src, dst), RevealAction(src)])
        composite.do()
        self.assertTrue(src.is_face_up(TS))
        self.assertEqual(dst.cards, (KH,))
        composite.undo()
        self.assertEqual(snapshot(b), before)
        self.assertFalse(src.is_face_up(TS))

    def test_composite_order_is_recorded(self):
        log = []

        class Spy(Action):
            def __init__(self, name):
                super().__init__()
                self.name = name
            def _apply(self): log.append(("do", self.name))
            def _revert(self): log.append(("undo", self.name))

        c = CompositeAction([Spy("a"), Spy("b"), Spy("c")])
        c.do()
        c.undo()
        self.assertEqual(log, [("do", "a"), ("do", "b"), ("do", "c"),
                               ("undo", "c"), ("undo", "b"), ("undo", "a")])

    def test_composite_is_all_or_nothing(self):
        b = Board()
        src, dst = b.columns[0], b.columns[1]
        src.push(KH, True)
        before = snapshot(b)
        composite = CompositeAction([MoveAction(KH, src, dst), RevealAction(src)])  # src vazia: falha
        with self.assertRaises(ActionError):
            composite.do()
        self.assertEqual(snapshot(b), before)
        self.assertFalse(composite.is_done)

    def test_rf24_null_action(self):
        b = Board()
        deal(b)
        before = snapshot(b)
        n = NullAction()
        n.do()
        n.undo()
        self.assertEqual(snapshot(b), before)
        self.assertFalse(n.has_effect)

    def test_has_effect(self):
        self.assertFalse(CompositeAction([NullAction(), NullAction()]).has_effect)
        self.assertTrue(CompositeAction([NullAction(), RevealAction(Board().columns[0])]).has_effect)

    def test_rnf02_uniform_treatment(self):
        b = Board()
        src, dst = b.columns[0], b.columns[1]
        src.push(TS, False)
        src.push(KH, True)
        b.stock.push(QC, False)
        before = snapshot(b)
        actions = [
            DrawAction(b.stock, b.waste),
            NullAction(),
            CompositeAction([MoveAction(KH, src, dst), RevealAction(src)]),
            CompositeAction([]),
        ]
        for a in actions:            # o mesmo código serve para todos os tipos
            a.do()
        for a in reversed(actions):
            a.undo()
        self.assertEqual(snapshot(b), before)


class LongSequenceTests(unittest.TestCase):
    def test_rf22_random_long_sequence_undo_all_restores_initial_state(self):
        for seed in range(5):
            rng = random.Random(seed)
            b = Board()
            deal(b, seed)
            initial = snapshot(b)
            all_cards = sorted(c.id for c in b.all_cards())
            history = []
            for _ in range(300):
                kind = rng.choice(["draw", "move", "move", "move_reveal"])
                if kind == "draw":
                    if b.stock.is_empty():
                        continue
                    action = DrawAction(b.stock, b.waste)
                else:
                    src = rng.choice(b.columns)
                    face_up = [c for c in src.cards if src.is_face_up(c)]
                    if not face_up:
                        continue
                    card = rng.choice(face_up)
                    dst = rng.choice([c for c in b.columns if c is not src])
                    action = MoveAction(card, src, dst)
                    if kind == "move_reveal":
                        parts = [action]
                        remaining = src.cards.index(card)
                        if remaining > 0 and not src.is_face_up(src.cards[remaining - 1]):
                            parts.append(RevealAction(src))
                        action = CompositeAction(parts)
                action.do()
                history.append(action)
                self.assertEqual(sorted(c.id for c in b.all_cards()), all_cards)
            self.assertGreater(len(history), 50)
            while history:
                history.pop().undo()
            self.assertEqual(snapshot(b), initial)


if __name__ == "__main__":
    unittest.main()
