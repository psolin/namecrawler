from nameparser import HumanName
import zipfile
import os
import sqlite3
import operator
from datetime import date

# Get the directory where this module lives
_MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
_DATA_DIR = os.path.join(_MODULE_DIR, 'data')
_DB_PATH = os.path.join(_DATA_DIR, 'names.sqlite')
_ZIP_PATH = os.path.join(_DATA_DIR, 'names.sqlite.zip')


def database_unzip():
    if not os.path.isfile(_DB_PATH):
        with zipfile.ZipFile(_ZIP_PATH, 'r') as zip_ref:
            zip_ref.extractall(_DATA_DIR)


# Returns .first and .last
def name_parsing(name_str):
    name_processed = HumanName(name_str)
    return name_processed


def race(name_str):
    database_unzip()
    last_name = name_parsing(name_str).last.upper()
    conn = sqlite3.connect(_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT pctwhite, pctblack, pctapi, pctaian, pct2prace, pcthispanic FROM surnames WHERE name=?', [last_name])
    race = cursor.fetchone()
    cursor.close()
    conn.close()
    race_prob = {'White': race[0],
                 'Black': race[1],
                 'Asian/Pacific Islander': race[2],
                 'American Indian / Alaskan Native': race[3],
                 'Two or More Races': race[4],
                 'Hispanic': race[5]}
    max_race = max(race_prob.items(), key=operator.itemgetter(1))[0]
    return max_race, race_prob[max_race] + "%"


# Survival probability by age (proportion of birth cohort still alive)
# Based on SSA 2022 Period Life Table (average of male and female)
# Source: Social Security Administration Actuarial Life Tables
# https://www.ssa.gov/oact/STATS/table4c6.html
# Values are (male_survivors + female_survivors) / 200000
_SURVIVAL_BY_AGE = {
    0: 1.0000, 1: 0.9944, 2: 0.9940, 3: 0.9937, 4: 0.9935,
    5: 0.9933, 10: 0.9927, 15: 0.9918, 20: 0.9890, 25: 0.9839,
    30: 0.9770, 35: 0.9681, 40: 0.9573, 45: 0.9439, 50: 0.9266,
    55: 0.9025, 60: 0.8675, 65: 0.8182, 70: 0.7537, 75: 0.6679,
    80: 0.5491, 85: 0.3951, 90: 0.2217, 95: 0.0801, 100: 0.0196,
    105: 0.0011, 110: 0.0000, 115: 0.0000, 119: 0.0000
}


def _get_survival_probability(age):
    """Interpolate survival probability for any age."""
    if age <= 0:
        return 1.0
    if age >= 115:
        return 0.0

    ages = sorted(_SURVIVAL_BY_AGE.keys())
    for i, a in enumerate(ages):
        if a >= age:
            if a == age:
                return _SURVIVAL_BY_AGE[a]
            # Linear interpolation
            prev_age = ages[i - 1]
            prev_surv = _SURVIVAL_BY_AGE[prev_age]
            curr_surv = _SURVIVAL_BY_AGE[a]
            ratio = (age - prev_age) / (a - prev_age)
            return prev_surv - (prev_surv - curr_surv) * ratio
    return 0.0


def _detect_db_schema(cursor):
    """Detect whether database uses full yearly data or aggregated schema."""
    cursor.execute("PRAGMA table_info(first)")
    columns = [row[1] for row in cursor.fetchall()]
    return 'aggregated' if 'peak_year' in columns else 'full'


def age(name_str, normalize=False):
    """
    Estimate age based on first name popularity.

    Args:
        name_str: Full name string (first name will be extracted)
        normalize: If True, adjust estimate using actuarial survival data.
                   The estimate is weighted by the probability that someone
                   born in each year is still alive today, giving a more
                   realistic expected age for living people with this name.
                   (Only fully supported with full yearly database schema)

    Returns:
        Tuple of (estimated_age, peak_year)
        If normalize=True and survival probability is ~0, returns (None, peak_year)
    """
    database_unzip()
    first_name = name_parsing(name_str).first.capitalize()
    conn = sqlite3.connect(_DB_PATH)
    cursor = conn.cursor()

    schema = _detect_db_schema(cursor)

    if schema == 'aggregated':
        # Aggregated database: use pre-computed peak year
        cursor.execute(
            'SELECT peak_year, peak_occurences, first_year, last_year FROM first WHERE first=?',
            [first_name])
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result or not result[0]:
            return None, None

        peak_year = int(result[0])
        current_year = int(date.today().year)
        raw_age = current_year - peak_year

        if normalize:
            # With aggregated data, we can only do approximate normalization
            # using the year range the name was used
            first_year = int(result[2]) if result[2] else peak_year
            last_year = int(result[3]) if result[3] else peak_year
            survival_at_peak = _get_survival_probability(raw_age)

            if survival_at_peak < 0.01:
                # Almost no one from peak year alive, estimate from last usage
                estimated_age = current_year - last_year
                if _get_survival_probability(estimated_age) < 0.01:
                    return None, peak_year
                return estimated_age, peak_year
            return raw_age, peak_year
        else:
            return raw_age, peak_year

    # Full yearly database
    if normalize:
        # Get all years and occurrences for this name to compute weighted average
        cursor.execute(
            'SELECT year, SUM(occurences) FROM first WHERE first=? GROUP BY year',
            [first_name])
        year_data = cursor.fetchall()
        cursor.close()
        conn.close()

        if not year_data:
            return None, None

        current_year = int(date.today().year)

        # Weight each year's occurrences by survival probability
        weighted_sum = 0
        total_weight = 0
        peak_year = None
        peak_count = 0

        for year_str, count in year_data:
            year = int(year_str)
            age_if_born = current_year - year
            survival_prob = _get_survival_probability(age_if_born)

            # Track peak year
            if count > peak_count:
                peak_count = count
                peak_year = year

            # Weight by (occurrences * survival probability)
            weight = count * survival_prob
            weighted_sum += age_if_born * weight
            total_weight += weight

        if total_weight < 1:
            # Almost no one with this name is likely still alive
            return None, peak_year

        estimated_age = int(round(weighted_sum / total_weight))
        return estimated_age, peak_year
    else:
        cursor.execute(
            'SELECT year, max(occurences) FROM first WHERE first=?', [first_name])
        age_lookup = cursor.fetchone()
        cursor.close()
        conn.close()

        if not age_lookup or not age_lookup[0]:
            return None, None

        peak_year = int(age_lookup[0])
        raw_age = int(date.today().year) - peak_year
        return raw_age, peak_year


def popularity(name_str):
    """
    Get popularity trend data for a first name.

    Returns:
        Dict with:
        - peak_year: Year with highest occurrences
        - peak_count: Number of births in peak year
        - first_year: First year name appears in data
        - last_year: Last year name appears in data
        - total: Total occurrences across all years
        - trend: 'rising', 'falling', 'stable', or 'historic'
        - decades: Dict of occurrence counts by decade
    """
    database_unzip()
    first_name = name_parsing(name_str).first.capitalize()
    conn = sqlite3.connect(_DB_PATH)
    cursor = conn.cursor()

    schema = _detect_db_schema(cursor)

    if schema == 'aggregated':
        cursor.execute(
            '''SELECT total_occurences, peak_year, peak_occurences, first_year, last_year
               FROM first WHERE first=?''',
            [first_name])
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return None

        return {
            'name': first_name,
            'peak_year': int(result[1]),
            'peak_count': int(result[2]),
            'first_year': int(result[3]) if result[3] else None,
            'last_year': int(result[4]) if result[4] else None,
            'total': int(result[0]),
            'trend': None,  # Can't determine without yearly data
            'decades': None
        }

    # Full schema - get detailed data
    cursor.execute(
        'SELECT year, SUM(occurences) FROM first WHERE first=? GROUP BY year ORDER BY year',
        [first_name])
    year_data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not year_data:
        return None

    # Process data
    years = [(int(y), int(c)) for y, c in year_data]
    total = sum(c for _, c in years)
    peak_year, peak_count = max(years, key=lambda x: x[1])
    first_year = years[0][0]
    last_year = years[-1][0]

    # Group by decade
    decades = {}
    for year, count in years:
        decade = (year // 10) * 10
        decades[decade] = decades.get(decade, 0) + count

    # Determine trend (compare last decade to peak decade)
    peak_decade = (peak_year // 10) * 10
    last_decade = (last_year // 10) * 10

    if last_decade == peak_decade:
        trend = 'rising'
    elif decades.get(last_decade, 0) < decades.get(peak_decade, 0) * 0.1:
        trend = 'historic'  # Name has largely fallen out of use
    elif decades.get(last_decade, 0) < decades.get(peak_decade, 0) * 0.5:
        trend = 'falling'
    else:
        trend = 'stable'

    return {
        'name': first_name,
        'peak_year': peak_year,
        'peak_count': peak_count,
        'first_year': first_year,
        'last_year': last_year,
        'total': total,
        'trend': trend,
        'decades': decades
    }


def sex(name_str):
    """
    Determine the most likely sex based on first name.
    Returns (sex, probability%) where sex is 'M' or 'F'.
    """
    database_unzip()
    first_name = name_parsing(name_str).first.capitalize()
    conn = sqlite3.connect(_DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        'SELECT sex, SUM(occurences) FROM first WHERE first=? GROUP BY sex', [first_name])
    results = cursor.fetchall()
    cursor.close()
    conn.close()

    if not results:
        return None, "Name not found"

    sex_counts = {row[0]: row[1] for row in results}
    male_count = sex_counts.get('M', 0)
    female_count = sex_counts.get('F', 0)
    total = male_count + female_count

    if total == 0:
        return None, "No data"

    if male_count > female_count:
        probability = round((male_count / total) * 100, 2)
        return 'M', f"{probability}%"
    else:
        probability = round((female_count / total) * 100, 2)
        return 'F', f"{probability}%"


def crawler(text, min_score=0.5, max_distance=5):
    """
    Find potential names in arbitrary text.

    Algorithm:
    1. Find words that match first names in database
    2. Find words that match last names in database
    3. Match first names with nearby last names (within max_distance words)
    4. Score matches by name popularity and proximity

    Args:
        text: String to search for names
        min_score: Minimum normalized score (0-1) to include in results
        max_distance: Maximum word distance between first and last name

    Returns:
        List of dicts with 'name', 'first', 'last', 'score', 'position'
        sorted by score descending
    """
    import re

    database_unzip()

    # Common words that happen to match name databases but aren't names
    STOP_WORDS = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
        'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
        'we', 'they', 'who', 'which', 'what', 'where', 'when', 'why', 'how',
        'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other', 'some',
        'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
        'very', 'just', 'also', 'now', 'here', 'there', 'then', 'once', 'any',
        'if', 'into', 'out', 'up', 'down', 'about', 'over', 'under', 'again',
        'further', 'after', 'before', 'during', 'while', 'because', 'through',
        'between', 'real', 'new', 'old', 'like', 'words', 'random', 'names'
    }

    # Tokenize text into words with positions
    words = re.findall(r'\b[A-Za-z]+\b', text)
    word_positions = [(i, w.capitalize()) for i, w in enumerate(words) if w.lower() not in STOP_WORDS]

    conn = sqlite3.connect(_DB_PATH)
    cursor = conn.cursor()

    # Find first names with their total occurrences (popularity)
    first_matches = {}
    for pos, word in word_positions:
        cursor.execute(
            'SELECT SUM(occurences) FROM first WHERE first=?', [word])
        result = cursor.fetchone()
        if result and result[0]:
            first_matches[pos] = {'word': word, 'popularity': result[0]}

    # Find last names with their rank
    last_matches = {}
    for pos, word in word_positions:
        cursor.execute(
            'SELECT rank, count FROM surnames WHERE name=?', [word.upper()])
        result = cursor.fetchone()
        if result:
            rank = int(result[0]) if result[0] else 999999
            count = int(result[1]) if result[1] else 0
            last_matches[pos] = {'word': word, 'rank': rank, 'count': count}

    cursor.close()
    conn.close()

    # Match first and last names by proximity
    matches = []

    # Get max values for normalization
    max_first_pop = max((m['popularity'] for m in first_matches.values()), default=1)
    max_last_count = max((m['count'] for m in last_matches.values()), default=1)

    for first_pos, first_data in first_matches.items():
        for last_pos, last_data in last_matches.items():
            distance = abs(last_pos - first_pos)

            # Skip if too far apart or same word
            if distance == 0 or distance > max_distance:
                continue

            # Calculate score components (all normalized to 0-1)
            # Closer = better (1 for adjacent, decreasing with distance)
            distance_score = 1 - ((distance - 1) / max_distance)

            # More popular first name = better
            first_pop_score = first_data['popularity'] / max_first_pop

            # More common last name = better
            last_pop_score = last_data['count'] / max_last_count

            # Combined score (weighted average)
            score = (distance_score * 0.4) + (first_pop_score * 0.3) + (last_pop_score * 0.3)

            if score >= min_score:
                # Determine order (first name should come before last)
                if first_pos < last_pos:
                    full_name = f"{first_data['word']} {last_data['word']}"
                else:
                    full_name = f"{last_data['word']}, {first_data['word']}"

                matches.append({
                    'name': full_name,
                    'first': first_data['word'],
                    'last': last_data['word'],
                    'score': round(score, 3),
                    'position': min(first_pos, last_pos),
                    'distance': distance
                })

    # Sort by score descending, then by position
    matches.sort(key=lambda x: (-x['score'], x['position']))

    # Remove duplicates (same name found at different positions)
    seen_names = set()
    unique_matches = []
    for m in matches:
        name_key = (m['first'].lower(), m['last'].lower())
        if name_key not in seen_names:
            seen_names.add(name_key)
            unique_matches.append(m)

    return unique_matches
