"""Creates images from websites.

Usage:
    
    Process a file that is a list of urls
    > python url_to_image.py process urls.txt
    
    Search for already processed images for a given search term
    > python url_to_image.py search term    

If PIL is available, a thumbnail version of the image is also created.

"""

import os
import csv
import sys
import subprocess
import threading
import uuid
from Queue import Queue

WKHTMLTOIMAGE_PATH = "wkhtmltoimage"
OUTFILE = 'image_key.csv'  # The file that keeps track of image files that have been created
RESOLUTION = (1024, 768)  # width, height: 4/3
THUMB_SIZE = (128, 128)
IMAGE_FILE_FORMAT = 'jpg'
QUEUE_LENGTH = 3  # The number of threads to use to run wkhtmltopdf / PIL functions

# Check if PIL is available, if it is we will make thumbnails
try:
    Image = __import__('Image')
except ImportError:
    Image = None

def create_image_from_url(url):
    """Create an image for the url
    Returns the name of the file created
    """
    fullsize_name = "{}.{}".format(uuid.uuid4(), IMAGE_FILE_FORMAT)
    DEVNULL = open(os.devnull, 'wb')  # Ignore output
    subprocess.call([WKHTMLTOIMAGE_PATH,
        '--width', str(RESOLUTION[0]),
        '--height', str(RESOLUTION[1]),
        '--format', IMAGE_FILE_FORMAT,
        url, fullsize_name],
        stdout=DEVNULL,
        stderr=DEVNULL)
    return fullsize_name
    
def create_thumbnail_from_image(fullsize_name):
    """Create a thumbnail version of the image 'fullsize_name'
    Returns name of created image
    """
    outfile = fullsize_name.replace('.' + IMAGE_FILE_FORMAT,
                                '.thumb.' + IMAGE_FILE_FORMAT)
    im = Image.open(fullsize_name)
    im.thumbnail(THUMB_SIZE, Image.ANTIALIAS)
    im.save(outfile)
    return outfile


class ScreenshotMaker(threading.Thread):
    """Container for managing separate worker threads """
    def __init__(self, url):
        self.url = url
        self.result = None
        threading.Thread.__init__(self)
 
    def run(self):
        """Create both images for a given URL
        Return the url processed and the names of the file(s) created """
        try:
            fullsize_name = create_image_from_url(self.url)
            if Image:
                thumb_name = create_thumbnail_from_image(fullsize_name)
                self.result = (self.url, fullsize_name, thumb_name)
            else:
                self.result = (self.url, fullsize_name)
            print "SUCCESS: Created screenshot for: '{}'".format(self.url)
        except IOError:
            print "ERROR: Cannot create screenshot for {}".format(self.url)

def get_processed_urls():
    """Returns a list of urls from the OUTFILE """
    try:
        with open(OUTFILE, 'r') as image_key:
            keyreader = csv.reader(image_key)
            return [row[0] for row in keyreader if len(row)]
    except IOError:
        # File doesn't exist yet
        return []

def process_file_queue(q, expected_total, keywriter):
    """Runs in a thread to process the results from the
    download queue as they come in """
    nfinished = 0
    while nfinished < expected_total:
        thread = q.get(True)
        thread.join()
        nfinished += 1
        if thread.result:
            keywriter.writerow(thread.result)

def process_file(filename):
    """The main function for 'process' mode """
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

    # Process urls, keeping track of their names as we go
    q = Queue(QUEUE_LENGTH)
    with open(OUTFILE, 'ab+') as image_key:
        keywriter = csv.writer(image_key)
        # Start a thread to consume queue results as they come in
        writer_thread = threading.Thread(target=process_file_queue,
                                        args=(q, len(url_list), keywriter))
        writer_thread.start()
        for url in url_list:
            worker_thread = ScreenshotMaker(url)
            worker_thread.start()
            q.put(worker_thread, block=True)  # Block until space is open in the queue

        # Give the thread time to finish before exiting
        writer_thread.join()

def search(term):
    """The main function for 'search' mode.
    Return a comma separated list of urls and their images matching a search term """
    with open(OUTFILE, 'r') as image_key:
        keyreader = csv.reader(image_key)
        for row in keyreader:
            # Print any line where the search term is in the url
            if len(row) and term in row[0]:
                print ", ".join(row)

if __name__ == "__main__":
    nargs = len(sys.argv)
    if nargs < 2:
        print "ERROR: Please supply the mode of use.  Choices are: 'process' or 'search'"
        sys.exit(0)
    mode = sys.argv[1]
    if mode == 'process':
        if nargs < 3:
            print "ERROR: Please provide the name of the file to process."
            sys.exit(0)
        filename = sys.argv[2]
        if not Image:
            print "WARNING: PIL not available.  Thumbnails will not be created."
        process_file(filename)
    elif mode == 'search':
        if nargs < 3:
            print "ERROR: Please provide the search term to use to find matching processed urls and their associated files."
            sys.exit(0)
        term = sys.argv[2]
        search(term)
    else:
        print "ERROR: Invalid operation mode.  Choices are: 'process' or 'search'"
        sys.exit(0)
