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
import colorama
import shutil
import yaml
import glob
import sys
import os
#
from papers import utils
from papers import getdoi
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
    given again, the program will open the editor with empty fields.
    """

    # if doi was passed as an argument
    if doi:
        # add entry to the database
        entry = utils.add_entry_from_doi(doi)
        click.echo(utils.display_entry(entry))

        # if pdf was passed
        if pdf:
            try:
                click.echo("Copying PDF file to the database")
                shutil.copy(pdf, dic["file"])
            except:
                click.echo(f"source: {pdf}")
                click.echo(f"destination: {dic['file']}")
                raise Exception("PDF file could not be copied")
            
        # if pdf was not passed we try to download from scihub
        else:
            utils.download_from_scihub(entry)
        
        # TODO: check if valid and edit

    # if doi was not passed as an argument
    else:
        # try to get the doi from the pdf
        doi = getdoi.pdf_to_doi(pdf)
        try:
            getdoi.validate_doi(doi)
            entry = utils.add_entry_from_doi(doi)
            print(utils.display_entry(entry))
        except:
            logging.error("DOI not found")

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
        opener = "zathura"

    # get the filename
    library_path = cfg.config["folders"]["library"]
    filename = os.path.join(library_path, f"{key}.pdf")
    if os.path.isfile(filename):
        subprocess.call([opener, filename])
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
    for fname in sorted(list_of_files):
        with open(fname, "r") as f:
            entry = yaml.safe_load(f)
            entries += [entry]
        #
        click.echo(utils.display_entry(entry))
# }}}

# remove {{{
@cli.command("remove")
@click.argument("key")
def remove(key):
    """Remove the given entry."""

    library_path = cfg.config["folders"]["library"]
    pdf_file = os.path.join(library_path, f"{key}.pdf")
    meta_file = os.path.join(library_path, f".metadata/{key}.yaml")

    msg = "Do you want to remove entry " + colorama.Fore.BLUE + f"{key}?" + \
            colorama.Style.RESET_ALL + " [Y/n] " 

    for filename in [pdf_file, meta_file]:
        if os.path.isfile(filename):
            ans = input(msg)
            if ans in ["", "Y", "y", "yes"]:
                os.remove(filename)
                click.echo(f"{key} succesfully removed")
            else:
                click.echo("Aborted!")


# }}}

# search {{{
@cli.command("search")
def search():
    pass
# }}}

# doctor {{{
@cli.command("doctor")
def doctor():
    pass
# }}}


if __name__ == "__main__":
    cli()
