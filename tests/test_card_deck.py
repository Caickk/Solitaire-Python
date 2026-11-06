import copy
import pickle
import random
import unittest

from solitaire.card import Card, Color, Rank, Suit
from solitaire.deck import Deck


class CardTests(unittest.TestCase):
    def test_rf04_52_unique_cards(self):
        cards = list(Card.all_cards())
        self.assertEqual(len(cards), 52)
        self.assertEqual(len(set(cards)), 52)
        for suit in Suit:
            self.assertEqual(len([c for c in cards if c.suit is suit]), 13)
        for rank in Rank:
            self.assertEqual(len([c for c in cards if c.rank is rank]), 4)

    def test_rf04_single_entity(self):
        self.assertIs(Card.of(Rank.ACE, Suit.SPADES), Card.of(Rank.ACE, Suit.SPADES))

    def test_direct_construction_is_blocked(self):
        with self.assertRaises(TypeError):
            Card(Rank.ACE, Suit.SPADES)

    def test_rf05_rank_order(self):
        order = [Rank.ACE, Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX,
                 Rank.SEVEN, Rank.EIGHT, Rank.NINE, Rank.TEN, Rank.JACK,
                 Rank.QUEEN, Rank.KING]
        self.assertEqual(sorted(Rank), order)
        self.assertEqual(list(Rank), order)

    def test_rf05_immediately_above_below(self):
        seven = Card.of(Rank.SEVEN, Suit.HEARTS)
        six = Card.of(Rank.SIX, Suit.CLUBS)
        self.assertTrue(seven.is_immediately_above(six))
        self.assertTrue(six.is_immediately_below(seven))
        self.assertFalse(six.is_immediately_above(seven))
        king = Card.of(Rank.KING, Suit.CLUBS)
        ace = Card.of(Rank.ACE, Suit.CLUBS)
        self.assertFalse(ace.is_immediately_above(king))
        self.assertFalse(king.is_immediately_below(ace))

    def test_rf06_colors(self):
        self.assertIs(Suit.HEARTS.color, Color.RED)
        self.assertIs(Suit.DIAMONDS.color, Color.RED)
        self.assertIs(Suit.CLUBS.color, Color.BLACK)
        self.assertIs(Suit.SPADES.color, Color.BLACK)
        self.assertTrue(Suit.HEARTS.has_same_color_as(Suit.DIAMONDS))
        self.assertFalse(Suit.HEARTS.has_same_color_as(Suit.SPADES))
        a = Card.of(Rank.TWO, Suit.CLUBS)
        b = Card.of(Rank.NINE, Suit.SPADES)
        self.assertTrue(a.has_same_color_as(b))
        self.assertFalse(a.has_same_suit_as(b))

    def test_rnf05_id_roundtrip_preserves_identity(self):
        for card in Card.all_cards():
            self.assertIs(Card.from_id(card.id), card)
        self.assertEqual(Card.of(Rank.TEN, Suit.HEARTS).id, "10H")

    def test_rnf05_copy_and_pickle_preserve_identity(self):
        card = Card.of(Rank.QUEEN, Suit.DIAMONDS)
        self.assertIs(copy.copy(card), card)
        self.assertIs(copy.deepcopy(card), card)
        self.assertIs(pickle.loads(pickle.dumps(card)), card)
        seq = [Card.of(Rank.EIGHT, Suit.HEARTS), Card.of(Rank.SEVEN, Suit.CLUBS)]
        clone = pickle.loads(pickle.dumps(seq))
        self.assertTrue(all(a is b for a, b in zip(seq, clone)))

    def test_invalid_ids(self):
        for bad in ("", "A", "1H", "AX", "11H"):
            with self.assertRaises(ValueError):
                Card.from_id(bad)


class DeckTests(unittest.TestCase):
    def test_standard_deck(self):
        deck = Deck.standard()
        self.assertEqual(len(deck), 52)
        self.assertEqual(len(set(deck)), 52)

    def test_rf07_shuffle_is_permutation(self):
        deck = Deck.standard()
        before = deck.cards
        deck.shuffle(random.Random(1))
        self.assertEqual(sorted(c.id for c in deck), sorted(c.id for c in before))
        self.assertNotEqual(deck.cards, before)

    def test_rf07_shuffle_varies_and_is_reproducible(self):
        d1, d2, d3 = Deck(), Deck(), Deck()
        d1.shuffle(random.Random(1))
        d2.shuffle(random.Random(1))
        d3.shuffle(random.Random(2))
        self.assertEqual(d1.cards, d2.cards)
        self.assertNotEqual(d1.cards, d3.cards)

    def test_shuffle_without_rng(self):
        deck = Deck()
        deck.shuffle()
        self.assertEqual(len(set(deck)), 52)

    def test_cards_view_is_immutable(self):
        deck = Deck()
        self.assertIsInstance(deck.cards, tuple)


if __name__ == "__main__":
    unittest.main()
