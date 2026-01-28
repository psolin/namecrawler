# namecrawler

A Python library for finding names in strings and estimating demographic information.

## Installation

```bash
pip install -r requirements.txt
```

The database is distributed as a zip file (exceeds GitHub's file size limit). It will be automatically extracted on first use.

## Features

### Name Finder (`crawler`)

Finds potential names in arbitrary text by:
1. Matching words against a database of first names (US Social Security Administration data, 1920-2017)
2. Matching words against a database of surnames (US Census Bureau 2010)
3. Scoring matches by name popularity and word proximity

```python
from namecrawler.process import crawler

text = "The report was filed by John Smith and reviewed by Mary Johnson."
results = crawler(text, min_score=0.5, max_distance=5)

for r in results:
    print(f"{r['name']} (score: {r['score']})")
```

### Demographic Estimation

#### Age

Estimates age based on when a first name peaked in popularity.

```python
from namecrawler.process import age

estimated_age, peak_year = age("Mildred Smith")
# Returns: (100+, 1920) - Mildred peaked in 1920

# With normalization (adjusts for life expectancy)
estimated_age, peak_year = age("Mildred Smith", normalize=True)
# Returns adjusted age accounting for mortality
```

#### Race/Ethnicity

Returns the most likely race/ethnicity based on surname from Census data.

```python
from namecrawler.process import race

result, probability = race("John Smith")
# Returns: ('White', '73.35%')

result, probability = race("Carlos Garcia")
# Returns: ('Hispanic', '...%')
```

#### Sex

Determines likely sex based on historical first name usage.

```python
from namecrawler.process import sex

result, probability = sex("John Smith")
# Returns: ('M', '99.x%')

result, probability = sex("Taylor Brown")
# Returns: ('F', '~55%') - more neutral name
```

#### Popularity

Shows when a name peaked and its trend over time.

```python
from namecrawler.process import popularity

info = popularity("Emma")
# Returns: {
#   'name': 'Emma',
#   'peak_year': 2003,
#   'peak_count': 22741,
#   'first_year': 1920,
#   'last_year': 2017,
#   'total': 535123,
#   'trend': 'stable',  # or 'rising', 'falling', 'historic'
#   'decades': {1920: 46729, 1930: 30229, ...}
# }
```

## Data Sources

The database (`names.sqlite.zip`) is compiled from US government sources:

### First Names
- **Source:** US Social Security Administration - Baby Names from Social Security Card Applications
- **Download:** https://www.ssa.gov/oact/babynames/names.zip
- **Documentation:** https://www.ssa.gov/oact/babynames/background.html
- **Coverage:** 1920-2017 (98 years, 1.75M records)
- **Format:** Name, sex (M/F), occurrence count per year
- **Notes:** Only includes names with 5+ occurrences per year for privacy

### Surnames
- **Source:** US Census Bureau 2010 Decennial Census
- **Compiled by:** FiveThirtyEight
- **Download:** https://github.com/fivethirtyeight/data/tree/master/most-common-name
- **API:** https://api.census.gov/data/2010/surname
- **Coverage:** 151,670 surnames with racial/ethnic distribution
- **Fields:** Name, rank, count, percentages for White, Black, Asian/Pacific Islander, American Indian/Alaska Native, Two or More Races, Hispanic
- **Notes:** 2020 Census surname data not yet available from Census Bureau

### Actuarial Data (for normalization)
- **Source:** SSA Period Life Table 2022
- **URL:** https://www.ssa.gov/oact/STATS/table4c6.html
- **Used for:** `normalize=True` parameter in `age()` function

## Updating Data

To add newer years of SSA data:

```bash
# Download latest data
curl -O https://www.ssa.gov/oact/babynames/names.zip
unzip names.zip -d /tmp/ssa_names

# Update database
python scripts/update_ssa_data.py /tmp/ssa_names
```

## Database Optimization

The database can be optimized to reduce size (~40% reduction):

```bash
# Full optimization (keeps yearly data)
python scripts/rebuild_database.py

# Aggressive optimization (aggregates by name, loses yearly granularity)
python scripts/rebuild_database.py --aggregate
```

## Limitations

- **US-centric:** Data comes from US government sources; non-US names may not be found or may have inaccurate demographic estimates
- **Historical bias:** Name popularity reflects historical US naming patterns
- **Age estimation:** Based on peak popularity year, which is a rough approximation. The `normalize=True` flag provides a better estimate for older names by accounting for mortality.
- **Race/ethnicity:** Based on surname only; represents population averages, not individual identity

## Running Tests

```bash
pytest tests/ -v
```

## License

MIT License - see [license](license) file.

## Acknowledgments

- US Social Security Administration
- US Census Bureau
- FiveThirtyEight (for compiling Census surname data)
