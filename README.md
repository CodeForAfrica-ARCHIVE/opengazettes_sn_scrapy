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


## Deploying to [Scraping Hub](https://scrapinghub.com)

It is recommended that you deploy your crawler to scrapinghub for easy management. Follow these steps to do this:

- Sign up for free scraping hub account [here](https://app.scrapinghub.com)
- Install shub locally using `pip install shub`. Further instructions [here](https://shub.readthedocs.io/en/stable/quickstart.html#installation)
- `shub login`
- `shub deploy`

Note that on scraping hub, environment variables don't need the `SCRAPY_` prefix

## Installing scrapy-deltafetch on MacOS
- `brew install berkeley-db`
- `export YES_I_HAVE_THE_RIGHT_TO_USE_THIS_BERKELEY_DB_VERSION=1`
- `BERKELEYDB_DIR=$(brew --cellar)/berkeley-db/6.2.23 pip install bsddb3`. Replace `6.2.23` with the version of berkeley-db that you installed
- `pip install scrapy-deltafetch`
