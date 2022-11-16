from urllib.request import Request, urlopen
from bs4 import BeautifulSoup
from notion_client import Client

secret_key = 'secret_Te6NxO4UQbPlJngCLWvFrzJjgsrLrUkFdLsg2EdgwSU'
page_id = 'd6553af86a5a4b4391053dbca7344eec'


def main():
    hikes_urls = get_all_hikes_urls()
    hikes_to_notion = {}
    scrap_hikes(hikes_urls, hikes_to_notion)
    send_data_to_notion(hikes_to_notion)


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


def scrap_hikes(hikes, hikes_to_notion):
    for hike_url in hikes:
        soup = create_soup(hike_url)
        title = soup.body.find("h1", {"class": "omc-post-heading-standard"}).text
        article = soup.body.find("article", {"id": "omc-full-article"})
        hike_info = article.find("ul")
        info_as_json = {'url': hike_url}
        for li in hike_info:
            line_info = li.text.split(':')
            if len(line_info) > 1:
                info_as_json[line_info[0]] = line_info[1].strip()
            info_as_json['Comment'] = line_info[0]
        hikes_to_notion[title] = info_as_json


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
                                        "Art": {"rich_text": {}},
                                        "Comment": {"rich_text": {}},
                                        "H\u00f6henmeter": {"rich_text": {}},
                                        "Gehzeit": {"rich_text": {}},
                                        "Kondition": {"rich_text": {}},
                                        "Technik": {"rich_text": {}},
                                        "Rundtour": {"rich_text": {}},
                                        "Ausr\u00fcstung": {"rich_text": {}},
                                        "Link": {"url": {}}})
    for hike in hikes:
        hike_data = {'Hike': {'type': 'title', 'title': [{'type': 'text', 'text': {'content': hike}}]}}
        hike_data['Art'] = {'rich_text': [{'text': {'content': hikes[hike]['Art']}}]} if 'Art' in hikes[hike] else {'rich_text': [{'text': {'content': ''}}]}
        hike_data['Ausr\u00fcstung'] = {'rich_text': [{'text': {'content': hikes[hike]['Ausr\u00fcstung']}}]} if 'Ausr\u00fcstung' in hikes[hike] else {'rich_text': [{'text': {'content': ''}}]}
        hike_data['Comment'] = {'rich_text': [{'text': {'content': hikes[hike]['Comment']}}]} if 'Comment' in hikes[hike] else {'rich_text': [{'text': {'content': ''}}]}
        hike_data['Gehzeit'] = {'rich_text': [{'text': {'content': hikes[hike]['Gehzeit']}}]} if 'Gehzeit' in hikes[hike] else {'rich_text': [{'text': {'content': ''}}]}
        hike_data['H\u00f6henmeter'] = {'rich_text': [{'text': {'content': hikes[hike]['H\u00f6henmeter']}}]} if 'H\u00f6henmeter' in hikes[hike] else {'rich_text': [{'text': {'content': ''}}]}
        hike_data['Kondition'] = {'rich_text': [{'text': {'content': hikes[hike]['Kondition']}}]} if 'Kondition' in hikes[hike] else {'rich_text': [{'text': {'content': ''}}]}
        hike_data['Link'] = {'url': hikes[hike]['url']}
        hike_data['Rundtour'] = {'rich_text': [{'text': {'content': hikes[hike]['Rundtour']}}]} if 'Rundtour' in hikes[hike] else {'rich_text': [{'text': {'content': ''}}]}
        hike_data['Technik'] = {'rich_text': [{'text': {'content': hikes[hike]['Technik']}}]} if 'Technik' in hikes[hike] else {'rich_text': [{'text': {'content': ''}}]}

        notion.pages.create(parent={
            "database_id": hikes_db['id']
        }, properties=hike_data)


main()