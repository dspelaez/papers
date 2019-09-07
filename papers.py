#! /usr/bin/env python
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# =============================================================
#  Copyright © 2017 Daniel Santiago <dpelaez@cicese.edu.mx>
#  Distributed under terms of the GNU/GPL license.
# =============================================================


"""
Author: Daniel Santiago
Email: dspelaez@gmail.com
Github: https://github.com/dspelaez
Description: 
"""

import click
import colorama
import glob
import inquirer
import logging
import os
import re
import requests
import subprocess
import sys
import webbrowser
import yaml
#
import bibtexparser.customization as bibcustomization
import bibtexparser.bparser as bibparser

# config logging
logging.basicConfig(level=logging.DEBUG)

# --- configuration class ---
# class to handle configuration {{{
basepath = "/Users/danielsantiago/Dropbox/Library/papers/"
if os.path.exists(basepath):
    # 
    # create path of metadata
    metadata_path = os.path.join(basepath, ".metadata")
    if not os.path.exists(metadata_path):
        os.mkdir(metadata_path)

    # create path of metadata
    notes_path = os.path.join(basepath, ".notes")
    if not os.path.exists(notes_path):
        os.mkdir(notes_path)

    
class Papers(object):

    """
    Papers is a homemade bibliography manager.
    """

    def __init__(self):
        """Constructor"""
        
        # initial folder
        self.home_path = os.path.expanduser("~")
        self.config_path = os.path.join(self.home_path, ".config/papers")
        self._create_folder(self.config_path)

        # default configuration
        self.default_conf = {
            "folders":
                {
                "library": os.path.join(self.home_path, "library/papers"),
                "metadata": os.path.join(self.home_path, "library/papers/.metadata"),
                "notes": os.path.join(self.home_path, "library/papers/.notes"),
                }
            }

        # create or read config file
        self.config_file = os.path.join(self.config_path, "papers.yml")
        if os.path.isfile(self.config_file):
            #
            logging.debug(f"Reading configuration file at {self.config_file}.")
            self.config = self._read_config_file()
        else:
            #
            # create a new file
            with open(self.config_file, "w") as f:
                #
                logging.debug("Writing new configuration file.")
                #
                f.write("# papers configuration file\n\n")
                yaml.safe_dump(self.default_conf, f)
                self.config = self.default_conf


    def _read_config_file(self):
        """Read config file."""
        with open(self.config_file, "r") as f:
            return yaml.safe_load(f)


    def _create_folder(self, folder):
        """Create folder if dont exist."""

        if not os.path.isdir(folder):
            logging.debug(f"Creating folder {folder}.")
            os.mkdir(folder)
        else:
            logging.debug(f"Folder {folder} already exists.")
        
# }}}


# --- functions to handle data ---
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

    # TODO: checl if file exist
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
    """Export entry or entrys to a bibtex file"""
    
    filename = os.path.join(metadata_path, f"{entry['ID']}.yaml")
    with open(filename, "w") as f:
        yaml.dump(entry, f, default_flow_style=False)

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
    journal_str = RED + f"{entry['journal']}\n"

    return key_str + author_str + title_str + journal_str 
# }}}


# --- command line interfase ---
# group {{{
@click.group()
def cli():
    pass
# }}}

# add {{{
@cli.command("add")
@click.argument("doi")
def add(doi):
    """Add entry to the library.
    
    This functions takes one or two arguments. The doi and the pdf file path.
    If the doi is given, the program will try to download the pdf file. If the
    pdf is given but not the doi, the program will ask you the doi, if not is
    given again, the program will open the editor will empty fields.
    """

    # if doi was passed as an argument
    if doi:
        doi = str(doi)
        
        # check if doi can be retrieved from the internet
        click.echo("Looking for DOI in the internet\n")
        try:
            bib = bibtex_from_doi(doi)
        except:
            logging.error(f"DOI: {doi} could not be retreived")
            raise Exception("DOI could not be retrieved")
        
        # parse to a python dictionary
        try:
            dic = bibtex_to_dict(bib)
            click.echo(display_entry(dic))
        except:
            logging.error(f"DOI: {doi} could not be parsed")
            raise Exception("DOI could not be parsed")

        # write metadata to yaml file
        write_to_yaml(dic)
        # 
        question = [
                # inquirer.Confirm('edit_yaml', 
                # message="Do you want to edit the entry?"),
                # #
                inquirer.Confirm('download_pdf', 
                message="Do you want to download the PDF?")
                ]
        answer = inquirer.prompt(question)

        # if answer["edit_yaml"]:
            # edit(dic["ID"])

        if answer["download_pdf"]:
            download_from_scihub(dic)


# }}}

# open {{{
@cli.command("open")
@click.argument("key")
def openpdf(key):
    """Open the PDF file.""" 
   
    # check the opener according to the os
    if sys.platform.startswith('darwin'):
        opener = "open"
    elif os.name == 'nt':
        opener = "start"
    elif os.name == 'posix':
        opener = "xdg-open"

    # get the filename
    filename = os.path.join(basepath, f"{key}.pdf")
    if os.path.isfile(filename):
        subprocess.call(["open", filename])
    else:
        logging.error(f"File {filename} not found")
# }}}

# edit {{{
@cli.command("edit")
@click.argument("key")
def edit(key):
    """Edit the metadata.""" 
    
    # get the editor varible name
    editor = os.environ.get('EDITOR', 'vim')

    # get the filename
    filename = os.path.join(basepath, ".metadata", f"{key}.yaml")
    if os.path.isfile(filename):
        subprocess.call([editor, filename])
    else:
        logging.error(f"File {filename} not found")

    # TODO: check if ID remain the same, if not, update the entry
    logging.warning("FILE UPDATED")
# }}}

# list {{{
@cli.command("list")
def list():
    """List all entries.""" 
    
    # TODO: implement inquirer

    click.echo("")
    
    # open every yaml file
    entries = []
    list_of_files = glob.glob(metadata_path + "/*.yaml")
    for fname in list_of_files:
        with open(fname, "r") as f:
            entry = yaml.safe_load(f)
            entries += [entry]
        #
        click.echo(display_entry(entry))
    # }}}


if __name__ == "__main__":
    
    p = Papers()
    cli()
