from unittest import TestCase
from namecrawler.process import race

class Test(TestCase):
    def test_race(self):
        names = ["John Smith", "John Jackson"]
        for name in names:
            print(name, race(name))