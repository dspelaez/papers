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


import logging
import glob
import re
import PyPDF2 as pypdf

logger = logging.getLogger("doi")


# pdf to doi {{{
def pdf_to_doi(pdf):
    """Try to get doi from a filepath
    
    It uses the PyPDF2 to convert the pdf to text and then try to extrack the
    doi using a regex math taken from papis/papis project.
    """

    try:
        pdfReader = pypdf.PdfFileReader(pdf)
        page = pdfReader.getPage(0)
        text = page.extractText()
        doi = find_doi_in_text(text)
        try:
            validate_doi(doi)
            return doi
        except:
            logger.debug(f"Invalid DOI={doi}")
    except:
        logger.debug("DOI could not be parsed")

# }}}

# validate doi {{{
def validate_doi(doi):
    """We check that the DOI can be resolved by official means.  If so, we
    return the resolved URL, otherwise, we return None (which means the DOI is
    invalid).

    http://www.doi.org/factsheets/DOIProxy.html

    :param doi: Doi identificator
    :type  doi: str

    :raises ValueError: Whenever the doi is not valid
    """
    from urllib.error import HTTPError
    import urllib.request
    import urllib.parse
    import json
    url = "https://doi.org/api/handles/{doi}".format(doi=doi)
    logger.debug('handle url %s' % url)
    request = urllib.request.Request(url)

    try:
        result = json.loads(urllib.request.urlopen(request).read().decode())
    except HTTPError:
        raise ValueError('HTTP 404: DOI not found')

    response_code = int(result["responseCode"])
    if response_code in [1, 200]:
        # HTTP 200 all ok
        logger.debug('HTTP 200: valid doi')
    elif response_code == 2:
        raise ValueError('HTTP 500: Interal DOI server error')
    elif response_code == 100:
        raise ValueError('HTTP 404: DOI not found')
    else:
        raise ValueError('Something unexpected happened')
# }}}

# get clean doi {{{
def get_clean_doi(doi):
    """Check if doi is actually a url and in that case just get
    the exact doi.

    :doi: String containing a doi
    :returns: The pure doi
    """
    doi = re.sub(r'%2F', '/', doi)
    # For pdfs
    doi = re.sub(r'\)>', ' ', doi)
    doi = re.sub(r'\)/S/URI', ' ', doi)
    doi = re.sub(r'(/abstract)', '', doi)
    doi = re.sub(r'\)$', '', doi)
    return doi
# }}}

# find doi in text {{{
def find_doi_in_text(text):
    """Try to find a doi in a text."""

    text = get_clean_doi(text)
    forbidden_doi_characters = r'"\s%$^\'<>@,;:#?&'
    # Sometimes it is in the javascript defined
    var_doi = re.compile(
        r'doi(.org)?'
        r'\s*(=|:|/|\()\s*'
        r'("|\')?'
        r'(?P<doi>[^{fc}]+)'
        r'("|\'|\))?'
        .format(
            fc=forbidden_doi_characters
        ), re.I
    )

    for regex in [var_doi]:
        miter = regex.finditer(text)
        try:
            m = next(miter)
            if m:
                doi = m.group('doi')
                return get_clean_doi(doi)
        except StopIteration:
            pass
    return None
# }}}


if __name__ == "__main__":
   pass 
