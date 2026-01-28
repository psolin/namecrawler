"""Tests for namecrawler process functions."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'namecrawler'))

import pytest
from process import race, age, sex, crawler, name_parsing, popularity


class TestNameParsing:
    """Test the name parsing helper."""

    def test_basic_name(self):
        result = name_parsing("John Smith")
        assert result.first == "John"
        assert result.last == "Smith"

    def test_name_with_title(self):
        result = name_parsing("Dr. Jane Doe")
        assert result.first == "Jane"
        assert result.last == "Doe"
        assert result.title == "Dr."

    def test_name_with_suffix(self):
        result = name_parsing("Robert Jones Jr.")
        assert result.first == "Robert"
        assert result.last == "Jones"
        assert result.suffix == "Jr."


class TestRace:
    """Test the race estimation function."""

    def test_common_white_surname(self):
        result, prob = race("John Smith")
        assert result == "White"
        assert float(prob.replace('%', '')) > 50

    def test_common_black_surname(self):
        result, prob = race("Michael Washington")
        assert result == "Black"
        assert float(prob.replace('%', '')) > 50

    def test_hispanic_surname(self):
        result, prob = race("Carlos Garcia")
        assert result == "Hispanic"
        assert float(prob.replace('%', '')) > 50


class TestAge:
    """Test the age estimation function."""

    def test_old_name(self):
        # Mildred peaked around 1920
        estimated_age, peak_year = age("Mildred Smith")
        assert estimated_age > 80
        assert peak_year < 1940

    def test_modern_name(self):
        # Emma peaked in recent years
        estimated_age, peak_year = age("Emma Johnson")
        assert estimated_age < 30
        assert peak_year > 2000

    def test_normalize_reduces_old_age(self):
        # Normalization should reduce estimates for very old names
        # because it weights by survival probability
        raw_age, _ = age("Mildred Smith", normalize=False)
        normalized_age, peak_year = age("Mildred Smith", normalize=True)
        # Normalized age might be None if name is too old, or much lower
        if normalized_age is not None:
            assert normalized_age < raw_age
        else:
            # Name peaked so long ago that virtually no one is alive
            assert peak_year < 1930

    def test_normalize_no_effect_modern(self):
        # Normalization should have minimal effect on recent names
        # since survival probability is high for young people
        raw_age, _ = age("Emma Johnson", normalize=False)
        normalized_age, _ = age("Emma Johnson", normalize=True)
        # Should be close (within ~10 years due to weighting)
        assert normalized_age is not None
        assert abs(raw_age - normalized_age) < 15


class TestPopularity:
    """Test the popularity trend function."""

    def test_historic_name(self):
        result = popularity("Mildred")
        assert result['trend'] == 'historic'
        assert result['peak_year'] < 1940

    def test_rising_name(self):
        result = popularity("Liam")
        assert result['trend'] == 'rising'
        assert result['peak_year'] > 2010

    def test_decades_present(self):
        result = popularity("Paul")
        assert result['decades'] is not None
        assert 1950 in result['decades']
        assert result['decades'][1950] > result['decades'][2010]


class TestSex:
    """Test the sex estimation function."""

    def test_male_name(self):
        result, prob = sex("John Smith")
        assert result == "M"
        assert float(prob.replace('%', '')) > 95

    def test_female_name(self):
        result, prob = sex("Mary Johnson")
        assert result == "F"
        assert float(prob.replace('%', '')) > 95

    def test_neutral_name(self):
        # Taylor is used for both but slightly more female
        result, prob = sex("Taylor Brown")
        assert result in ('M', 'F')
        # Probability should be lower for neutral names
        assert float(prob.replace('%', '')) < 90

    def test_alex_mostly_male(self):
        result, prob = sex("Alex Williams")
        assert result == "M"


class TestCrawler:
    """Test the name finder/crawler function."""

    def test_find_single_name(self):
        text = "The report was filed by John Smith."
        results = crawler(text)
        names = [r['name'] for r in results]
        assert "John Smith" in names

    def test_find_multiple_names(self):
        text = "John Smith and Mary Johnson attended the meeting."
        results = crawler(text)
        names = [r['name'] for r in results]
        assert "John Smith" in names
        assert "Mary Johnson" in names

    def test_reversed_name(self):
        text = "Contact Williams, Sarah for more information."
        results = crawler(text)
        # Should find Sarah Williams (reversed format)
        first_names = [r['first'] for r in results]
        last_names = [r['last'] for r in results]
        assert "Sarah" in first_names
        assert "Williams" in last_names

    def test_no_false_positives_on_gibberish(self):
        text = "xyz qwerty asdfgh zxcvbn"
        results = crawler(text, min_score=0.3)
        assert len(results) == 0

    def test_min_score_filter(self):
        text = "John Smith works here."
        high_threshold = crawler(text, min_score=0.9)
        low_threshold = crawler(text, min_score=0.3)
        assert len(low_threshold) >= len(high_threshold)

    def test_max_distance_filter(self):
        text = "John wrote a very long sentence before mentioning Smith."
        close_only = crawler(text, max_distance=2)
        far_allowed = crawler(text, max_distance=10)
        # With larger distance, we might find more matches
        assert len(far_allowed) >= len(close_only)

    def test_score_ordering(self):
        text = "John Smith and some random text with Bob also mentioned."
        results = crawler(text, min_score=0.3)
        if len(results) > 1:
            # Results should be ordered by score descending
            scores = [r['score'] for r in results]
            assert scores == sorted(scores, reverse=True)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
