# namecrawler

A Python library for finding names in strings and approximating other data.

## Getting Started
Download the repository and use the following command:

```
sudo python setup.py install
```
## Algorithm

### Finder Function
1) The code looks for first names in a string. It compares against a list of the most popular baby names by year (1880 onwards). Text files from the social security database were turned into a proper data set which can be queried.

2) The code then looks for last names in the same string, notes their positions, and applies the rank from data from the US Census Bureau gathered in 2010.

3) The algorithm matches the distance between the two. It ranks each name for probability based on popularity as well as distance between the two words.

When found, the names can be further manipulated with the nameparser Python Library (installed separately).

### Guessing Functions

#### Age

To guess the age of one person is difficult; when used in a large dataset, you could potentially guess average age of everyone in it much more accurately.

#### Race

The probabilities for race come from the US Census Bureau.

#### Sex

This is compared by the rankings of each instance of the name, and is shown as a percentage.

## Use

Example code:

```
goes here
```

## Issues

Since the data comes from US Social Security Administration and the US Census Bureau, it will have a hard time with non-US names, and may not find them at all. As more data sources become available, they will be integrated into the library. Right now, all data is US-specific.

There may be a way to normalize age distribution based on data showing what years most people have been alive.

The library is not perfect; it misses unique names, those with abbreviations, and often finds matches where there aren’t any. First names and last names are often interchangeable, too, where the rankings help. An “exclusions” modifier could be written to take a list of non-matches to be avoided.

The code is generally slow since it has to do a great deal of lookups, and has the potential to be optimized further.

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details.

## Acknowledgments

* Social Security
* US Census Bureau