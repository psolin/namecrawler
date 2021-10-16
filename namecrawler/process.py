from nameparser import HumanName
import zipfile
import os.path
import sqlite3
import operator
from datetime import date


def database_unzip():
    file_path = "data/names.sqlite"
    if not os.path.isfile(file_path):
        with zipfile.ZipFile(file_path + ".zip", 'r') as zip_ref:
            zip_ref.extractall("data/")


# Returns .first and .last
def name_parsing(name_str):
    name_processed = HumanName(name_str)
    return name_processed


def race(name_str):
    database_unzip()
    last_name = name_parsing(name_str).last.upper()
    conn = sqlite3.connect('data/names.sqlite')
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


def age(name_str):
    database_unzip()
    first_name = name_parsing(name_str).first.capitalize()
    conn = sqlite3.connect('data/names.sqlite')
    cursor = conn.cursor()
    cursor.execute(
        'SELECT year, max(occurences) FROM first WHERE first=?', [first_name])
    age_lookup = cursor.fetchone()
    cursor.close()
    conn.close()
    print(age_lookup[0])
    age = int(date.today().year) - int(age_lookup[0])
    return age, int(age_lookup[0])


def sex():
    database_unzip()
    return 0


def crawler():
    database_unzip()
    return 0
