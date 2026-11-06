import unittest

from solitaire.board import Board, COLUMN_COUNT, FOUNDATION_COUNT
from solitaire.card import Card, Rank, Suit
from solitaire.location import Column, LocationKind, Stock, Waste

KH = Card.of(Rank.KING, Suit.HEARTS)
QC = Card.of(Rank.QUEEN, Suit.CLUBS)
JD = Card.of(Rank.JACK, Suit.DIAMONDS)
AS = Card.of(Rank.ACE, Suit.SPADES)


class BoardTests(unittest.TestCase):
    def test_rf10_structure(self):
        b = Board()
        self.assertEqual(len(b.columns), COLUMN_COUNT)
        self.assertEqual(len(b.foundations), FOUNDATION_COUNT)
        self.assertEqual(len(b.locations), 13)
        kinds = [loc.kind for loc in b.locations]
        self.assertEqual(kinds.count(LocationKind.COLUMN), 7)
        self.assertEqual(kinds.count(LocationKind.FOUNDATION), 4)
        self.assertIsInstance(b.stock, Stock)
        self.assertIsInstance(b.waste, Waste)

    def test_rf10_uniform_treatment(self):
        b = Board()
        self.assertTrue(all(loc.is_empty() for loc in b.locations))
        b.stock.push(AS, face_up=False)
        b.foundations[0].push(KH)
        self.assertEqual([loc.is_empty() for loc in b.locations].count(False), 2)

    def test_rf10_location_of_accessible(self):
        b = Board()
        col = b.columns[2]
        col.push(KH, face_up=False)
        col.push(QC, face_up=True)
        col.push(JD, face_up=True)
        b.waste.push(AS, face_up=True)
        self.assertIs(b.location_of(AS), b.waste)
        self.assertIs(b.location_of(QC), col)       # visível no meio da coluna
        self.assertIs(b.location_of(JD), col)
        self.assertIsNone(b.location_of(KH))        # oculta: inacessível
        self.assertIs(b.location_of(KH, accessible_only=False), col)

    def test_non_column_only_top_is_accessible(self):
        b = Board()
        b.waste.push(QC)
        b.waste.push(JD)
        self.assertIsNone(b.location_of(QC))
        self.assertIs(b.location_of(JD), b.waste)
        b.stock.push(AS, face_up=False)
        self.assertIsNone(b.location_of(AS))        # topo do monte está virado

    def test_card_not_on_board(self):
        self.assertIsNone(Board().location_of(AS))
        self.assertIsNone(Board().location_of(AS, accessible_only=False))


class ColumnQueryTests(unittest.TestCase):
    def setUp(self):
        self.col = Column(0)
        self.col.push(KH, face_up=False)
        self.col.push(QC, face_up=True)
        self.col.push(JD, face_up=True)

    def test_rf20_cards_and_sequence(self):
        self.assertEqual(self.col.cards, (KH, QC, JD))
        self.assertEqual(self.col.sequence_from(QC), (QC, JD))

    def test_rf20_visibility_queries(self):
        self.assertFalse(self.col.is_face_up(KH))
        self.assertTrue(self.col.is_face_up(QC))
        self.assertTrue(self.col.is_bottom_most_face_up(QC))
        self.assertFalse(self.col.is_bottom_most_face_up(JD))
        self.assertFalse(self.col.is_bottom_most_face_up(KH))

    def test_rf20_king_already_at_base(self):
        self.assertFalse(self.col.is_king_already_at_base(KH))   # oculto
        self.col.set_top_face_up(True)
        col2 = Column(1)
        col2.push(KH, face_up=True)
        self.assertTrue(col2.is_king_already_at_base(KH))
        col3 = Column(2)
        col3.push(AS, face_up=False)
        col3.push(KH, face_up=True)
        self.assertFalse(col3.is_king_already_at_base(KH))        # rei sobre outra carta

    def test_queries_do_not_change_state(self):
        before = (self.col.cards, [self.col.is_face_up(c) for c in self.col.cards])
        self.col.sequence_from(QC)
        self.col.is_bottom_most_face_up(QC)
        self.col.is_king_already_at_base(KH)
        after = (self.col.cards, [self.col.is_face_up(c) for c in self.col.cards])
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
