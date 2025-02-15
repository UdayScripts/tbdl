import re
from pprint import pp
from urllib.parse import parse_qs, urlparse

import requests

from tools import get_formatted_size


def check_url_patterns(url):
    patterns = [
        r"ww\.mirrobox\.com",
        r"www\.nephobox\.com",
        r"freeterabox\.com",
        r"www\.freeterabox\.com",
        r"1024tera\.com",
        r"1024terabox\.com",
        r"terafileshare\.com",
        r"4funbox\.co",
        r"www\.4funbox\.com",
        r"mirrobox\.com",
        r"nephobox\.com",
        r"terabox\.app",
        r"terabox\.com",
        r"www\.terabox\.ap",
        r"www\.terabox\.com",
        r"www\.1024tera\.co",
        r"www\.momerybox\.com",
        r"teraboxapp\.com",
        r"momerybox\.com",
        r"tibibox\.com",
        r"www\.tibibox\.com",
        r"www\.teraboxapp\.com",
    ]

    for pattern in patterns:
        if re.search(pattern, url):
            return True

    return False


def get_urls_from_string(string: str) -> list[str]:
    """
    Extracts URLs from a given string.

    Args:
        string (str): The input string from which to extract URLs.

    Returns:
        list[str]: A list of URLs extracted from the input string. If no URLs are found, an empty list is returned.
    """
    pattern = r"(https?://\S+)"
    urls = re.findall(pattern, string)
    urls = [url for url in urls if check_url_patterns(url)]
    if not urls:
        return []
    return urls[0]


def find_between(data: str, first: str, last: str) -> str | None:
    """
    Searches for the first occurrence of the `first` string in `data`,
    and returns the text between the two strings.

    Args:
        data (str): The input string.
        first (str): The first string to search for.
        last (str): The last string to search for.

    Returns:
        str | None: The text between the two strings, or None if the
            `first` string was not found in `data`.
    """
    try:
        start = data.index(first) + len(first)
        end = data.index(last, start)
        return data[start:end]
    except ValueError:
        return None


def extract_surl_from_url(url: str) -> str | None:
    """
    Extracts the surl parameter from a given URL.

    Args:
        url (str): The URL from which to extract the surl parameter.

    Returns:
        str: The surl parameter, or False if the parameter could not be found.
    """
    parsed_url = urlparse(url)
    query_params = parse_qs(parsed_url.query)
    surl = query_params.get("surl", [])

    if surl:
        return surl[0]
    else:
        return False


def get_data(url: str):
    r = requests.Session()
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Connection": "keep-alive",
        "Cookie": "PANWEB=1; csrfToken=0W9rLLGHht0u1rzDrtWInUw9; browserid=ebfy5EY8dBUmKoXRB2o-uMjaPjlC5oMG5H6b_UqXjA0dXJyUXcC_YLouopE=; lang=en; TSID=KF3pKjn0NkXVQRheSyL7YuNMEHvxXo8P; __bid_n=1939fec84c56d044a24207; ndus=YdSMlCxteHuibExjI03RVAFAxd6CWzrItwlEs51k; ndut_fmt=2E05BB77580D8F419AF729200A1EB19B781A64B1A7B0C73F0FDEAAB7E567661A",
        "DNT": "1",
        "Host": "www.terabox.app",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
    }

    payload = ""

    response = r.get(url, data=payload, headers=headers)
    response = r.get(response.url, data=payload, headers=headers)
    default_thumbnail = find_between(response.text, 'og:image" content="', '"')
    jsToken = find_between(response.text, "fn%28%22", "%22%29")
    surl = extract_surl_from_url(response.url)
    if not surl:
        return False

    reqUrl = f"https://www.terabox.app/share/list?app_id=250528&web=1&channel=dubox&jsToken={jsToken}&page=1&num=20&by=name&order=asc&site_referer=&shorturl={surl}&root=1"
    response = r.get(
        reqUrl,
        data=payload,
        headers=headers,
    )
    if not response.status_code == 200:
        return False
    r_j = response.json()
    if r_j["errno"]:
        return False
    if "list" not in r_j and not r_j["list"]:
        return False
    list = r_j.get("list", [])[0]
    response = r.head(r_j["list"][0]["dlink"], headers=headers)


    direct_link = response.headers.get("location")
    data = {
        "file_name": list.get("server_filename"),
        "link": list.get("dlink"),
        "direct_link": direct_link,
        "thumb": list.get("thumbs", {}).get("url3") or default_thumbnail,
        "size": get_formatted_size(int(list["size"])),
        "sizebytes": int(list["size"]),
    }

    return data
