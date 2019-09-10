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
import yaml
import logging

# class to handle configuration
class PapersConfig(object):

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
                "library": os.path.join(self.home_path, "Library/papers"),
                "metadata": os.path.join(self.home_path, "Library/papers/.metadata"),
                "notes": os.path.join(self.home_path, "Library/papers/.notes"),
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
        
        # create library, notes and metadata folders
        self._create_folder(self.config["folders"]["library"])
        self._create_folder(self.config["folders"]["metadata"])
        self._create_folder(self.config["folders"]["notes"])


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


if __name__ == "__main__":
    pass
