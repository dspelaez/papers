#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8

"""
Copyright © 2019 Daniel Santiago <http://github.com/dspelaez>
Distributed under terms of the GNU/GPL 3.0 license.

@author: Daniel Santiago
@github: http://github.com/dspelaez
@created: 2019-09-09
"""

import os
import re
import sys
import glob
import colorama
import logging
import requests
import webbrowser
import yaml
#
import bibtexparser.customization as bibcustomization
import bibtexparser.bparser as bibparser
#
from papers.config import PapersConfig

# config logging
# logging.basicConfig(level=logging.DEBUG)
cfg = PapersConfig()


# get bibtex from doi {{{
def bibtex_from_doi(doi):
    """
    Return a bibTeX string of metadata for a given DOI.

    Taken from 'jrsmith3/doi2bib.py'

    Args:
        doi (string): String with doi

    Returns: bibtex entry as a string
    """

    url = "http://dx.doi.org/" + doi

    headers = {"accept": "application/x-bibtex"}
    r = requests.get(url, headers=headers)

    return r.text
# }}}

# get pdf filename {{{
def get_pdf_filename(entry):
    """Generate the file name of the PDF corresponding to the entry"""

    # TODO: check if file exist
    basepath = cfg.config["folders"]["library"]
    return os.path.join(basepath, f"{entry['ID']}.pdf")

# }}}

# clean bibtex entry {{{
def clean_bibtex_entry(entry):
    """Try to clean the bibtex entries when possible"""

    # add filename field when the file is located or downloaded
    entry["file"] = get_pdf_filename(entry)

    # remove link field if exist
    if "link" in entry:
        entry.pop("link")

    # add url given by the doi
    if "url" not in entry:
        if entry["ENTRYTYPE"] == ["article"]:
            try:
                entry["url"] = "https://doi.org/" + entry["doi"]
            except KeyError:
                logging.error("Entry does not have a valid DOI")
                entry["url"] = ""

    # split authors
    authors = entry["author"].replace('\n', ' ').split(" and ")
    entry["author"] = [author.strip() for author in authors]

    # modify the key according to the number of authors
    # number_of_authors = len(authors)
    # if number_of_authors == 2:
        # pass
    # if number_of_authors >= 3:
        # name, year = entry["ID"].split("_")
        # entry["ID"] = f"{name}_etal_{year}"

    return entry

# }}}

# convert bibtex to python dictionay {{{
def bibtex_to_dict(bib):
    """Convertst the bibtex text entry to a rea

    Args:
        bib (string): Bibtex entry

    Returns: dictionary

    """

    # define customization function
    parser = bibparser.BibTexParser()
    parser.common_strings = True
    parser.homogenise_fields = True
    parser.interpolate_strings = True
    parser.ignore_nonstandard_types = True
    parser.customization = bibcustomization.homogenize_latex_encoding
    parser.customization = bibcustomization.convert_to_unicode

    # check if bib is a list of entries
    if os.path.exists(bib):
        logging.error("Trying to load a bibtex file")
        raise NotImplementedError("bibtex files are not implemented yet")

    # get entries as a list of dictionaries
    entry = parser.parse(bib, partial=True).entries[0]

    return clean_bibtex_entry(entry)

# }}}

# write entry to yaml file {{{
def write_to_yaml(entry):
    """Export entry or entries to a bibtex file"""
    
    metadata_path = cfg.config["folders"]["metadata"]
    filename = os.path.join(metadata_path, f"{entry['ID']}.yaml")
    with open(filename, "w") as f:
        yaml.dump(entry, f, default_flow_style=False)

# }}}

# add entry from doi {{{
def add_entry_from_doi(doi):
    """Add new entry to the database for a given doi"""

    # check if doi can be retrieved from the internet
    try:
        bib = bibtex_from_doi(doi)
    except:
        logging.error(f"DOI: {doi} could not be retreived")
        raise Exception("DOI could not be retrieved")
    
    # parse to a python dictionary
    try:
        dic = bibtex_to_dict(bib)
    except:
        logging.error(f"DOI: {doi} could not be parsed")
        raise Exception("DOI could not be parsed")

    # write metadata to yaml file
    try:
        write_to_yaml(dic)
    except:
        logging.error(f"DOI: {doi} could not be written to YAML")
        raise Exception("DOI could not be written to YAML")

    return dic
# }}}

# download from sci-hub {{{
def download_from_scihub(entry):
    """Try to download PDF from sci-hub"""

    doi = entry["doi"]
    scihub_url = "https://sci-hub.tw/"
    scihub_request = requests.get(f"{scihub_url}{doi}")
    
    for line in scihub_request.iter_lines():
        if b"iframe" in line and b"pdf" in line:
            pdflink = line.decode().split()[3].replace('"', '')

    link_request = requests.get(pdflink)
    if b"adobe" in link_request.content:
        filename = get_pdf_filename(entry)
        with open(filename, "bw") as f:
            f.write(link_request.content)
    else:
        logging.warning("File could not be dowloaded automatically.")
        webbrowser.open_new_tab(pdflink) 

# }}}

# display entry on screen {{{
def display_entry(entry, plain=False):
    """Returns a list with a pretty representation of the entry data."""

    # TODO: validate the required fields

    # shorcuts to access colors quickly
    if plain:
        RED, BLUE, GREEN, WHITE = "", "", "", ""
    else:
        RED = colorama.Fore.RED
        BLUE = colorama.Fore.BLUE
        GREEN = colorama.Fore.GREEN
        WHITE = colorama.Fore.WHITE

    key_str = BLUE + f"{entry['ID']}:\n" 
    author_str = GREEN + ", ".join(entry["author"]) + " "
    author_str += GREEN + f"({entry['year']})\n"
    title_str = WHITE + f"{entry['title']}\n"
    try:
        journal_str = RED + f"{entry['journal']}\n"
    except:
        journal_str = RED + f"{entry['booktitle']}\n"

    return key_str + author_str + title_str + journal_str 
# }}}

if __name__ == "__main__":
    pass
