# namecrawler beta

A Python library for finding names in strings and approximating other data.

## Getting Started
Install the requirements:

    >>> pip install -r requirements.txt

Since the database  reaches the file size limit of Github, the script will make an attempt to unzip with every function, if the database was not unzipped previously.

## Algorithm

### Finder Function
1) The code looks for first names in a string. It compares against a list of the most popular baby names by year (1920-2017). Text files from the social security database were turned into a proper data set which can be queried.

2) The code then looks for last names in the same string, notes their positions, and applies the rank from data from the US Census Bureau gathered in 2010.

3) The algorithm matches the distance between the two. It ranks each name for probability based on popularity as well as distance between the two words.

When found, the names can be further manipulated with the nameparser Python library.

### Probability Functions

#### Age
Age is calculated by taking the most occurences of that name in a given year and subtracting the current year from it. The function will return the age and the number of occurences for the year with the highest value.

#### Race
The probabilities for race come from the US Census Bureau last names and are simply looked up. Thanks to FiveThirtyEight for compiling this data and making it available. The function will return the race with the probability.

#### Sex
This is found by looking up a first name, and seeing which of M/F is higher in rank.

## Use
Example code:

```

```

## Limitations
Since the data comes from US Social Security Administration and the US Census Bureau, it will have a hard time with non-US names, and may not find them at all. As more data sources become available, they will be integrated into the library. Right now, all data is US-specific.

There may be a way to normalize age distribution based on data showing what years most people have been alive.

The library is not perfect; it misses unique names, those with abbreviations, and often finds matches where there aren’t any. First names and last names are often interchangeable, too, where the rankings help. An “exclusions” modifier could be written to take a list of non-matches to be avoided.

The code is generally slow since it has to do a great deal of lookups, and has the potential to be optimized further.

## License
This project is licensed under the MIT License - see the [license](license) file for details.

## Acknowledgments
* Social Security Administration
* US Census Bureau / FiveThirtyEight
