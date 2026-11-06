import random
import unittest

from solitaire.card import Card, Rank, Suit
from solitaire.deck import Deck
from solitaire.serialization import deserialize_cards, serialize_cards


class SerializationTests(unittest.TestCase):
    def test_rnf05_full_deck_roundtrip_keeps_identity_and_order(self):
        deck = Deck()
        deck.shuffle(random.Random(11))
        restored = deserialize_cards(serialize_cards(deck.cards))
        self.assertEqual(len(restored), 52)
        self.assertTrue(all(a is b for a, b in zip(deck.cards, restored)))

    def test_rnf05_sequence_example(self):
        seq = (Card.of(Rank.EIGHT, Suit.HEARTS), Card.of(Rank.SEVEN, Suit.SPADES), Card.of(Rank.SIX, Suit.HEARTS))
        self.assertEqual(serialize_cards(seq), "8H,7S,6H")
        back = deserialize_cards("8H,7S,6H")
        self.assertTrue(all(a is b for a, b in zip(seq, back)))

    def test_empty(self):
        self.assertEqual(serialize_cards(()), "")
        self.assertEqual(deserialize_cards(""), ())

    def test_invalid_payloads(self):
        for bad in ("8H,8H", "XX", "8H,", ",8H", "8H;7S"):
            with self.assertRaises(ValueError):
                deserialize_cards(bad)


if __name__ == "__main__":
    unittest.main()
