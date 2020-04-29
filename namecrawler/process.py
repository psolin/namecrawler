from nameparser import HumanName


def fl_parse(name):
    name = HumanName(name)
    return(name.first, name.last)