"""Creates images from websites.

Usage:
    
    Process a file that is a list of urls
    > python url_to_image.py process urls.txt
    
    Search for already processed images for a given search term
    > python url_to_image.py search term    

If PIL is available, a thumbnail version of the image is also created.

"""

import csv
import sys
import subprocess
import uuid

WKHTMLTOIMAGE_PATH = "C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltoimage.exe"
OUTFILE = 'image_key.csv'
RESOLUTION = (1024, 768)  # width, height: 4/3
THUMB_SIZE = (128, 128)
IMAGE_FILE_FORMAT = 'jpg'

def create_images(url, Image = None):
    """Create both images for a given URL """
    try:
        fullsize_name= create_image_from_url(url)
        if Image:
            thumb_name = create_thumbnail_from_image(fullsize_name, Image)
    except IOError:
        print "Cannot create image for '%s'" % url
    return (url, fullsize_name, thumb_name)

def create_image_from_url(url):
    """Create an image for the url
    Returns the name of the file created
    """
    fullsize_name = "{}.{}".format(uuid.uuid4(), IMAGE_FILE_FORMAT)
    subprocess.call([WKHTMLTOIMAGE_PATH,
        '--width', str(RESOLUTION[0]),
        '--height', str(RESOLUTION[1]),
        '--format', IMAGE_FILE_FORMAT,
        url, fullsize_name])    
    return fullsize_name
    
def create_thumbnail_from_image(fullsize_name, Image):
    """Create a thumbnail version of the image 'fullsize_name'
    Returns name of created image
    """
    outfile = fullsize_name.replace('.' + IMAGE_FILE_FORMAT,
                                '.thumb.' + IMAGE_FILE_FORMAT)
    im = Image.open(fullsize_name)
    im.thumbnail(THUMB_SIZE, Image.ANTIALIAS)
    im.save(outfile)
    return outfile

def search(term):
    """Return a list of urls and their images matching a search term """
    # Open output file
    print term
    with open(OUTFILE, 'r') as image_key:
        keyreader = csv.reader(image_key)
        for row in keyreader:
            # Print any line where the search term is in the url
            if term in row[0]:
                print row

def get_processed_urls():
    """Returns a list of (url, filename) pairs """
    with open(OUTFILE, 'r') as image_key:
        keyreader = csv.reader(image_key)
        return [row[0] for row in keyreader]

def process_file(filename):
    """The main function for processing mode """
    processed_urls = get_processed_urls()
    url_list = []
    with open(filename, 'r') as urls:
        for url in urls:
            url = url.rstrip()  # clean up spaces
            # Ignore urls we've already processed
            if url not in processed_urls:
                url_list.append(url)

    if not url_list:
        print "No new urls to process.  Exiting."
        sys.exit(0)
        
    # Check if PIL is available, if it is we will make thumbnails
    try:
        Image = __import__('Image')
    except ImportError:
        print "PIL not available.  Thumbnails will not be created."

    # Process urls, keeping track of their names as we go
    with open(OUTFILE, 'ab+') as image_key:
        keywriter = csv.writer(image_key)
        for url in url_list:
            keywriter.writerow(create_images(url, Image))

if __name__ == "__main__":
    try:
        mode = sys.argv[1]
        if mode == 'process':
            try:
                filename = sys.argv[2]
                process_file(filename)
            except IndexError:
                print "Please provide the name of the file to process."
                sys.exit(0)
        elif mode == 'search':
            try:
                term = sys.argv[2]
                search(term)
            except IndexError:
                print "Please provide the search term to use to find matching processed urls and their associated files."
                sys.exit(0)
        else:
            print "Invalid operation mode.  Choices are: 'process' or 'search'"
            sys.exit(0)
    except IndexError:
        print "Please supply the mode of use ('process' or 'search')"
        sys.exit(0)
    
