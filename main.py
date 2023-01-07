import re
from re import search
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notion_client import Client

secret_key = 'XXXXXX'
page_id = 'XXXXXXX'


def main():
    hikes_urls = get_all_hikes_urls()
    hikes_to_notion = {}
    scrap_hikes(hikes_urls, hikes_to_notion)
    send_data_to_notion(hikes_to_notion)


# Get all the hikes urls. Go to the main page, build the url for all the possible pages and scrap all hikes urls
def get_all_hikes_urls():
    hikes_urls = []
    url = 'https://www.bergtour-online.de/suchergebnisse/?slg=post&mdf_cat=231&page_mdf=ad6f7ebcb07233055155f8945d15e184'
    pages_number = get_number_of_pages(create_soup(url))
    get_hikes_from_page(create_soup(url), hikes_urls)
    for i in range(2, pages_number + 1, 1):
        temp_url = 'https://www.bergtour-online.de/suchergebnisse/page/%s/?slg=post&mdf_cat=231&page_mdf=ad6f7ebcb07233055155f8945d15e184' % i
        get_hikes_from_page(create_soup(temp_url), hikes_urls)

    return hikes_urls


def get_hikes_from_page(soup, hikes_urls):
    articles = soup.body.find("article", {"id": "omc-full-article"})
    article = articles.find_all("div", {"class": "omc-resize-290"})
    for tag in article:
        hikes_urls.append(tag.find("a")['href'])


def get_number_of_pages(soup):
    articles = soup.body.find("article", {"id": "omc-full-article"})
    return len(articles.find("div", {"class": "pagination"}))


def create_soup(url):
    req = Request(
        url=url,
        headers={'User-Agent': 'Mozilla/5.0'}
    )
    soup = BeautifulSoup(urlopen(req), features="html.parser")
    return soup


# Go to each hike and scrap its info. First the title, then the contents regarding the hike.
def scrap_hikes(hikes, hikes_to_notion):
    for hike_url in hikes:
        try:
            soup = create_soup(hike_url)
            title = soup.body.find("h1", {"class": "omc-post-heading-standard"}).text
            article = soup.body.find("article", {"id": "omc-full-article"})
            hike_info = article.find("ul")
            info_as_json = {'url': hike_url}
            for li in hike_info:
                line_info = li.text.split(':')
                if len(line_info) > 1:
                    info_as_json[line_info[0]] = line_info[1].strip()
            hikes_to_notion[title] = info_as_json
        except:
            continue


# Beautify the fields of each hike
def beautify_hike_data(hike_title, hike_data):
    print(hike_title)
    try:
        hike_name = format_hike_name(hike_title)
        hike_formatted = {'Hike': {'title': [{'type': 'text', 'text': {'content': hike_name}}]}}
        hike_formatted['Art'] = {'select': format_art(hike_data['Art'])}
        hike_formatted['Ausr\u00fcstung'] = {'rich_text': [{'type': 'text', 'text': {'content': hike_data['Ausr\u00fcstung']}}]}
        hike_formatted['Gehzeit'] = {'rich_text': [{'type': 'text', 'text': {'content': calculate_number_of_hours(hike_title)}}]}
        # Change from String to number
        hike_formatted['H\u00f6henmeter'] = {'number': int(calculate_height(hike_title))}
        hike_formatted['Rundtour'] = {'select': format_rundtour(hike_data['Rundtour'])}
        hike_formatted['Link'] = {'url': hike_data['url']}
    except:
        hike_formatted = {}
    return hike_formatted


def format_hike_name(hike_name):
    return hike_name.split(' (')[0]


def format_art(art):
    if art is None:
        return {"name": "N/A"}
    elif search('.*mittel.*', art, flags=re.IGNORECASE) or search('.*mittle.*', art, flags=re.IGNORECASE):
        return {"name": "Mittel"}
    elif search('.*einfache.*', art, flags=re.IGNORECASE) or search('.*leichte.*', art, flags=re.IGNORECASE):
        return {"name": "Einfache"}
    elif search('.*schwere.*', art, flags=re.IGNORECASE) or search('.*schwarz.*', art, flags=re.IGNORECASE):
        return {"name": "Schwere"}
    else:
        return {"name": art.split(" (")[0]}


def calculate_number_of_hours(title):
    return search('.?.?:.?.?h', title, flags=re.IGNORECASE).group(0).strip()


def calculate_height(title):
    return search('\d*hm', title, flags=re.IGNORECASE).group(0).split('hm')[0].strip()


def format_rundtour(rundtour):
    if rundtour is None:
        return {"name": "N/A"}
    elif search('.*ja.*', rundtour, flags=re.IGNORECASE):
        return {"name": "Ja"}
    elif search('.*nein.*', rundtour, flags=re.IGNORECASE):
        return {"name": "Nein"}
    else:
        return {"name": rundtour.split(" (")[0]}


def send_data_to_notion(hikes):
    notion = Client(auth=secret_key)
    hikes_db = notion.databases.create(parent={"type": "page_id", "page_id": page_id},
                                       title=[{
                                           "type": "text",
                                           "text": {
                                               "content": "Hikes List"
                                           }
                                       }],
                                       properties={"Hike": {"title": {}},
                                                   "Art": {"select": {}},
                                                   "H\u00f6henmeter": {"number": {}},
                                                   "Gehzeit": {"rich_text": {}},
                                                   "Rundtour": {"select": {}},
                                                   "Ausr\u00fcstung": {"rich_text": {}},
                                                   "Link": {"url": {}}})

    for hike in hikes:
        try:
            hike_beautified = beautify_hike_data(hike, hikes[hike])
            if len(hike_beautified) != 0:
                notion.pages.create(parent={
                    "database_id": hikes_db['id']
                }, properties=hike_beautified)
        except:
            print("Error formatting hike {hike}".format(hike=hike))


main()
