"""
projekt_3.py: třetí projekt do Engeto Online Python Akademie

author: Martin Schwarz
email: svarmartin@gmail.com
"""
import argparse
import csv
import re
import sys
import time

from bs4 import BeautifulSoup
import requests

def launch() -> tuple[str]:
    """
    Command line launcher with 2 positional args: "url", "filename".
    Return:
    - link to the main page,
    - .csv filename for data export.
    """
    parser = argparse.ArgumentParser(
        description="Scrape election results from volby.cz."
    )
    parser.add_argument(
        "url",
        help="Input a valid 'volby.cz' elections result URL for scraping:\n\
        Select one URL from column 'Výběr obce' at\n\
        https://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ",
    )
    parser.add_argument(
        "filename",
        help="Input a valid .csv export filename e.g. election_results.csv",
    )
    input_args = parser.parse_args()
    url = input_args.url
    filename = input_args.filename
    validate_input(url, filename)

    return url, filename


def validate_input(url: str, filename: str) -> None:
    """
    Validate input arguments.
    If not valid: exit program and give feedback.
    """
    if filename.startswith("https://") and not url.startswith("https://"):
        sys.exit(
            "ERROR: Arguments appear to be swapped. Expected format:\n"
            "python main.py <URL> <CSV_FILENAME>"
        )
    valid_url_pattern = r"https://www\.volby\.cz/pls/ps2017nss/ps3[26]\?"
    
    if not re.match(valid_url_pattern, url):
        sys.exit(
            "ERROR: Invalid URL.\
        \nSelect one URL from column 'Výběr obce' at:\
        \nhttps://www.volby.cz/pls/ps2017nss/ps3?xjazyk=CZ"
        )
    if not filename.endswith(".csv"):
        sys.exit("ERROR: Invalid filename. The export filename must end with '.csv'.")

    return None


def scrape(base_url: str, href: str = "") -> BeautifulSoup:
    """
    Get server response and scrape full html.
    Return parsed bs4 text.
    - href = Use if scraping lower level URLs.
    """
    full_url = base_url + href
    server_response = requests.get(full_url)
    if server_response.status_code != 200:
        print(f"Status: {server_response.status_code} \nurl: {full_url}")
        sys.exit("Server not responding.")
    return BeautifulSoup(server_response.text, "html.parser")


def get_mainpg(soup: BeautifulSoup, url: str, *, filter: str) -> tuple[list]:
    """
    Get only relevant html snippets:
    (1) IDs, (2) municipal names.
    Returns unfiltered html snippets (text in html soup).
    - url = launcher url
    - filter = distinct element in CZ districts URLs
    """
    selection = soup.find("div", {"id": "content"})
    ids = selection.find_all("td", {"class": "cislo"})
    
    if filter in url:
        muni_names = [td.next_sibling.next_sibling for td in ids]
    else:
        muni_names = [td.previous_sibling.previous_sibling for td in ids]

    return ids, muni_names


def filter_mainpg(snippets: list, *, keyword: str) -> list[dict]:
    """
    Extract text data from html snippets.
    Return labelled text data.
    - keyword = data label
    """
    return [{keyword: snippet.get_text()} for snippet in snippets]


def get_href(soup: BeautifulSoup) -> list[str]:
    """
    Get main page href links to access low level URLs.
    """
    link_lst = []
    for td in soup.find_all("td", class_="cislo"):
        a_tag = td.find("a", href=True)
        if a_tag:
            link_lst.append(a_tag["href"])

    return link_lst


def get_top_table(soup: BeautifulSoup) -> tuple[dict]:
    """
    Scrape and process municipality results: top table.
    Return data:
    - registred (=voliči v seznamu)
    - envelopes (=vydané obálky)
    - valid (=platné hlasy)
    """
    top_table = soup.find("table", {"class": "table"})

    voters_scrap, envelopes_scrap, votes_scrap = (
        top_table.find("td", {"class": "cislo", "headers": "sa2"}),
        top_table.find("td", {"class": "cislo", "headers": "sa3"}),
        top_table.find("td", {"class": "cislo", "headers": "sa6"}),
    )
    voters, envelopes, votes = (
        {"registred": int(voters_scrap.get_text().replace("\xa0", ""))},
        {"envelopes": int(envelopes_scrap.get_text().replace("\xa0", ""))},
        {"valid": int(votes_scrap.get_text().replace("\xa0", ""))},
    )

    return voters, envelopes, votes


def get_bottom_table(soup: BeautifulSoup) -> dict:
    """
    Scrape and process municipality results: bottom table.
    Return data:
    - "party_name": no. of votes (jméno strany: počet hlasů)
    """
    party_results = {}

    for td in soup.find_all("td", {"class": "overflow_name"}):
        name = td.get_text()
        vote = (td.next_sibling.next_sibling).get_text().replace("\xa0", "")
        party_results.update({name: int(vote)})

    return party_results


def iter_scrape(base_url: str, hrefs_lst: list[str]) -> tuple[dict] | dict:
    """
    Perform all scraping tasks on each municipality from selected main page.
    Return all voter and party results data.
    """
    voter_data = []
    party_data = []
    for href in hrefs_lst:
        soup_low = scrape(base_url, href)
        voter_data.append(get_top_table(soup_low))
        party_data.append(get_bottom_table(soup_low))

    return voter_data, party_data


def wrap_data(*args: dict | list[dict] | tuple[dict]) -> list[dict]:
    """
    Prepare all collected data for export.
    Return data ready for csv.DictWriter.
    """
    all_result_data = []
    ids_data, muni_name_data, voter_data, *party_and_misc_data = args

    for ids, muni, voters, *party_and_misc in zip(
        ids_data, muni_name_data, voter_data, *party_and_misc_data
    ):
        new_dict = {**ids, **muni}
        for key_value in voters:
            new_dict.update(key_value)

        for key_value in party_and_misc:
            new_dict.update(key_value)
        all_result_data.append(new_dict)

    return all_result_data


def export_data(all_data: list[dict], csv_filename: str):
    with open(csv_filename, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=all_data[0].keys())
        writer.writeheader()
        writer.writerows(all_data)
    return None


def main():
    base_url = "https://www.volby.cz/pls/ps2017nss/"

    # Launch scraper from console; validate input args
    url, export_filename = launch()

    # Main page soup 'cooking' (main page scrape + href links to low level URLs)
    soup = scrape(url)
    hrefs_lst = get_href(soup)

    # Main page data scraping & filtering
    ids_snippets, muni_name_snippets = get_mainpg(soup, url, filter="ps32?")
    ids_data = filter_mainpg(ids_snippets, keyword="id")
    muni_name_data = filter_mainpg(muni_name_snippets, keyword="municipality")

    # Low level URL: Municipal data scraping & filtering
    print("Scraping municipal data...")
    voter_data, party_data = iter_scrape(base_url, hrefs_lst)
    print("OK")

    # Wrap and export data
    all_data = wrap_data(ids_data, muni_name_data, voter_data, party_data)
    export_data(all_data, export_filename)
    print(f"Export successfully completed: {export_filename}")


if __name__ == "__main__":
    start_time = time.time()
    main()
    end_time = time.time()

    print(f"Execution time: {end_time - start_time:.3f} sec")