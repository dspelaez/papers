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

import click
import logging
import subprocess
import glob
import sys
import os
#
from papers import utils
from papers.config import PapersConfig

# config logging
# logging.basicConfig(level=logging.DEBUG)
cfg = PapersConfig()


# group {{{
@click.group()
def cli():
    pass
# }}}

# add {{{
@cli.command("add")
@click.option("--doi", type=click.STRING, help="Document Object Identifier")
@click.option("--pdf", type=click.STRING, help="PDF filepath")
def add(doi, pdf=None):
    """Add entry to the library.
    
    This functions takes one or two arguments. The doi and the pdf file path.
    If the doi is given, the program will try to download the pdf file. If the
    pdf is given but not the doi, the program will ask you the doi, if not is
    given again, the program will open the editor will empty fields.
    """

    # check if doi can be retrieved from the internet
    click.echo("Looking for DOI in the internet\n")
    try:
        bib = utils.bibtex_from_doi(doi)
    except:
        logging.error(f"DOI: {doi} could not be retreived")
        raise Exception("DOI could not be retrieved")
    
    # parse to a python dictionary
    try:
        dic = utils.bibtex_to_dict(bib)
        click.echo(utils.display_entry(dic))
    except:
        logging.error(f"DOI: {doi} could not be parsed")
        raise Exception("DOI could not be parsed")

    # write metadata to yaml file
    utils.write_to_yaml(dic)
    # # 
    # question = [
            # # inquirer.Confirm('edit_yaml', 
            # # message="Do you want to edit the entry?"),
            # # #
            # inquirer.Confirm('download_pdf', 
            # message="Do you want to download the PDF?")
            # ]
    # answer = inquirer.prompt(question)

    # # if answer["edit_yaml"]:
        # # edit(dic["ID"])

    # if answer["download_pdf"]:
        # utils.download_from_scihub(dic)

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
    library_path = cfg.config["folders"]["library"]
    filename = os.path.join(library_path, f"{key}.pdf")
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
    metadata_path = cfg.config["folders"]["metadata"]
    filename = os.path.join(metadata_path, f"{key}.yaml")
    if os.path.isfile(filename):
        subprocess.call([editor, filename])
    else:
        logging.error(f"File {filename} not found")

    # TODO: check if ID remain the same, if not, update the entry
    logging.warning(f"Fiile {filename} was updated")
# }}}

# list {{{
@cli.command("list")
def list():
    """List all entries.""" 
    
    # TODO: implement inquirer

    click.echo("")

    # metadata path
    metadata_path = cfg.config["folders"]["metadata"]
    
    # open every yaml file
    entries = []
    list_of_files = glob.glob(metadata_path + "/*.yaml")
    for fname in list_of_files:
        with open(fname, "r") as f:
            entry = yaml.safe_load(f)
            entries += [entry]
        #
        click.echo(utils.display_entry(entry))
    # }}}

if __name__ == "__main__":
    cli()
