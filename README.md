# Facebook Marketplace Images Scraper
This tool lets you download all of the Facebook marketplace photos. It keeps track of the dates that each photo was uploaded to Facebook so that your photos will still be organized by date when they are added to a photo management platform like Google Photos or iPhoto.

## Installation
You'll need to have python, pip3, and [Google Chrome WebDriver](http://chromedriver.chromium.org/downloads) installed to use this tool. Once that's all set up:

1. Clone this repository
1. `cd` into the cloned folder 
1. Run `pip install -r requirements.txt`

## Usage
To download marketplace photos, run this:

`python fb-marketplace-images-scraper.py args`

### Args
* `-u`: username (default '')
* `-p`: password (default '')
* `-l`: location (default 'algiers')
* `-c`: category (default 'vehicles')

You should see Chrome open, access to Facebook, navigate to marketplace page. Download all of the photos to a `photos` folder that should appear in the same folder as the script.
Note:
If you want to set marketplace filters (example: radius distance) or save the credentials of who uploaded the photo,  you need to log in to your Facebook.

## References
* [Facebook Photo Downloader](https://github.com/jcontini/facebook-photos-download/)

## Thanks
Wanted to give a shoult to the good folks who contribute pull requests to improve this project. Thank you!






