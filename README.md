# Open Gazettes SN Scraper

## Installation
- Clone repo and cd into it
- Make virtual environment
- pip install -r requirements.txt
- Set ENV variables
    - `SCRAPY_AWS_ACCESS_KEY_ID` - Get this from AWS
    - `SCARPY_AWS_SECRET_ACCESS_KEY` - Get this from AWS
    - `SCRAPY_FEED_URI=s3://name-of-bucket-here/gazettes/data.jsonlines` - Where you want the `jsonlines` output for crawls to be saved. This can also be a local location
    - `SCRAPY_FILES_STORE=s3://name-of-bucket-here/gazettes` - Where you want scraped gazettes to be stored. This can also be a local location

## Running it Locally
- To run the spider locally, you can choose to store the scraped files locally to do this set the  ENV variable
- `SCRAPY_FILES_STORE=/directory/to/store/the/files` which should point to a local folder
- Then run the command  `scrapy crawl sn_gazettes -a year=2016 -o sn_gazettes.jsonlines`          
   where year is the year you want to scrape gazettes from
- `sn_gazettes.jsonlines` is the file where crawls are saved, this too can be a directory

## Deploying to [Scraping Hub](https://scrapinghub.com)

It is recommended that you deploy your crawler to scrapinghub for easy management. Follow these steps to do this:

- Sign up for free scraping hub account [here](https://app.scrapinghub.com)
- Install shub locally using `pip install shub`. Further instructions [here](https://shub.readthedocs.io/en/stable/quickstart.html#installation)
- `shub login`
- `shub deploy`
- Login to scrapinghub and set up the above ENV variables
Note that on scraping hub, environment variables should not have `SCRAPY_` prefix

## Installing scrapy-deltafetch on MacOS
- `brew install berkeley-db`
- `export YES_I_HAVE_THE_RIGHT_TO_USE_THIS_BERKELEY_DB_VERSION=1`
- `BERKELEYDB_DIR=$(brew --cellar)/berkeley-db/6.2.23 pip install bsddb3`. Replace `6.2.23` with the version of berkeley-db that you installed
- `pip install scrapy-deltafetch`
