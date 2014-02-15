# Python Website Screenshots

A simple python script creating a bunch of screenshots of webpages using the [wkhtmltopdf](http://wkhtmltopdf.org/) utility.

## Setup

At the very least, [download wkhtmltopdf](http://wkhtmltopdf.org/) and change the `WKHTMLTOIMAGE_PATH` in `url_to_image.py` to the location of the `wkhtmltoimage` binary.  The current location is the default installation directory for Windows installs.

## Usage

    # Process a file that is a list of urls
    python url_to_image.py process urls.txt
    
    # Search for already processed images whose urls contain a given search term
    python url_to_image.py search term
