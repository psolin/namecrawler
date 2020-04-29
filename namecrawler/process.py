from nameparser import HumanName
import zipfile
import os.path


def database_unzip():
    file_path = "data/names.sqlite"
    if not os.path.isfile(file_path):
        with zipfile.ZipFile(file_path + ".zip", 'r') as zip_ref:
            zip_ref.extractall("data/")


def name_parsing(name_str):
    name_processed = HumanName(name_str)
    return name_processed.first, name_processed.last


def race(last_name):
    database_unzip()
    return last_name


def age(first_name):
    database_unzip()
    return 0


def sex(first_name):
    database_unzip()
    return 0


def crawler(str):
    database_unzip()
    return 0
