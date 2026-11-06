import unittest

from solitaire.card import Card, Rank, Suit
from solitaire.stack import CardStack, EmptyStackError

AS = Card.of(Rank.ACE, Suit.SPADES)
KH = Card.of(Rank.KING, Suit.HEARTS)
QC = Card.of(Rank.QUEEN, Suit.CLUBS)
JD = Card.of(Rank.JACK, Suit.DIAMONDS)


class CardStackTests(unittest.TestCase):
    def test_rf08_preserves_order_base_to_top(self):
        s = CardStack()
        for c in (KH, QC, JD):
            s.push(c)
        self.assertEqual(s.cards, (KH, QC, JD))
        self.assertIs(s.pop(), JD)
        self.assertIs(s.pop(), QC)
        self.assertEqual(s.cards, (KH,))

    def test_rf09_empty_and_peek_do_not_alter(self):
        s = CardStack()
        self.assertTrue(s.is_empty())
        with self.assertRaises(EmptyStackError):
            s.peek()
        with self.assertRaises(EmptyStackError):
            s.pop()
        s.push(AS)
        self.assertFalse(s.is_empty())
        self.assertIs(s.peek(), AS)
        self.assertIs(s.peek(), AS)
        self.assertEqual(len(s), 1)

    def test_cards_view_is_a_copy(self):
        s = CardStack()
        s.push(AS)
        self.assertIsInstance(s.cards, tuple)
        list(s)  # iterar não altera
        self.assertEqual(len(s), 1)

    def test_no_duplicates(self):
        s = CardStack()
        s.push(AS)
        with self.assertRaises(ValueError):
            s.push(AS)

    def test_sequence_from_and_remove(self):
        s = CardStack()
        for c in (KH, QC, JD):
            s.push(c)
        self.assertEqual(s.sequence_from(QC), (QC, JD))
        self.assertEqual(s.cards, (KH, QC, JD))  # consulta não altera
        self.assertEqual(s.remove_sequence_from(QC), (QC, JD))
        self.assertEqual(s.cards, (KH,))
        with self.assertRaises(ValueError):
            s.sequence_from(AS)

    def test_push_sequence_keeps_order_and_is_atomic(self):
        s = CardStack()
        s.push(AS)
        s.push_sequence([KH, QC])
        self.assertEqual(s.cards, (AS, KH, QC))
        with self.assertRaises(ValueError):
            s.push_sequence([JD, KH])  # KH já existe: nada deve entrar
        self.assertEqual(s.cards, (AS, KH, QC))

    def test_rnf01_visibility_follows_position_not_card(self):
        a, b = CardStack(), CardStack()
        a.push(KH, face_up=True)
        a.pop()
        b.push(KH, face_up=False)
        self.assertFalse(b.is_face_up(KH))      # sem estado "vazado" da jogada anterior
        b.pop()
        b.push(KH)                               # padrão: virada para cima
        self.assertTrue(b.is_face_up(KH))

    def test_rnf01_visibility_stays_aligned_after_sequence_removal(self):
        s = CardStack()
        s.push(KH, face_up=False)
        s.push(QC, face_up=True)
        s.push(JD, face_up=True)
        s.remove_sequence_from(QC)
        self.assertFalse(s.is_face_up(KH))
        s.set_top_face_up(True)
        self.assertTrue(s.is_face_up(KH))
        s.set_top_face_up(False)
        self.assertFalse(s.is_face_up(KH))

    def test_set_top_face_up_on_empty(self):
        with self.assertRaises(EmptyStackError):
            CardStack().set_top_face_up(True)


if __name__ == "__main__":
    unittest.main()
