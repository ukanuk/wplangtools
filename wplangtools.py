"""
Get Wikipedia page titles across languages.
"""

import datetime
import json
import time
import requests


class WpLangTools:
    """
    Get Wikipedia page titles across languages.
    """

    # Be considerate and don't flood requests
    # https://www.mediawiki.org/wiki/API:Etiquette
    request_min_period = datetime.timedelta(seconds=1.0)
    request_last_datetime = datetime.datetime.now()

    # All disambiguation categories on Wikipedia ought to be in this category
    disambiguation_category_name = 'Category:All disambiguation pages'

    # Map from ISO language codes to Wikipedia language codes
    lang_map = {
        # ISO: Wikipedia
        'no': 'nb'  # Norwegian (bokmal)
    }

    @staticmethod
    def requests_get_polite(url):
        """requests.get() but not exceeding request_min_period."""

        tdelta = datetime.datetime.now() - WpLangTools.request_last_datetime
        if tdelta < WpLangTools.request_min_period:
            wait_seconds = (WpLangTools.request_min_period
                            - tdelta).total_seconds()
            time.sleep(wait_seconds)
        WpLangTools.request_last_datetime = datetime.datetime.now()

        req = requests.get(url)

        return req

    @staticmethod
    def url_to_json(url):
        """Load JSON from a URL."""

        req = WpLangTools.requests_get_polite(url)
        return json.loads(req.content)

    @staticmethod
    def resolve_title(*titles, site='en'):
        """Get page title after redirects (if any). Unknown page returns None.

        OpenSearch is the API used by Wikipedia's search box. It's less case
        sensitive, correctly redirecting lowercase "capital of tonga" when
        action=parse and action=query both fail. However it only accepts one
        search at a time
        https://en.wikipedia.org/w/api.php?action=opensearch&format=json&
        redirects=resolve&limit=1&search=capital of tonga

        OpenSearch API can handle redirects, see redirects=resolve in
        https://www.mediawiki.org/wiki/API:Opensearch

        Query API can handle redirects, see redirects parameter in
        https://www.mediawiki.org/wiki/API:Query#API_documentation

        Action API can handle redirects, see srprop=redirecttitle in
        https://www.mediawiki.org/wiki/API:Search

        """

        urlbase = (r'https://' + site + '.wikipedia.org/w/api.php' +
                   r'?action=opensearch&format=json')

        urlargs = (r'&redirects=resolve&limit=1' + r'&search=')
        WpLangTools.b = titles

        urls = [urlbase + urlargs + x for x in titles]
        WpLangTools.urls = urls
        pages = [WpLangTools.url_to_json(url) for url in urls]
        WpLangTools.pagess = pages
        titles = [(page[1][0] if len(page[1]) > 0 else None) for page in pages]

        # if len(titles) == 1:
        #     return titles[0]

        return titles

    def is_disambiguation(self, *pages):
        """Check page categories to find if it's a disambiguation page.

        https://en.wikipedia.org/w/api.php?action=query&prop=categories&clcate
        gories=Category:All disambiguation pages&titles=Georgia|Papeete

        Query API can get categories, see prop=categories in
        https://www.mediawiki.org/wiki/API:Query#API_documentation

        """
        if not pages:
            pages = self.pages

        truth_list = []
        for page in pages:
            this_truth = False
            if page is not None:
                try:
                    cat = page['categories'][0]['title']
                except KeyError:
                    pass
                else:
                    if WpLangTools.disambiguation_category_name in cat:
                        this_truth = True

            truth_list.append(this_truth)

        #if len(truth_list) == 1:
        #    return truth_list[0]

        return truth_list

    def translate_title_noresolve(self, languages=None, pages=None):
        """Use interwiki language links to find page title.

        Query API can get language links, see prop=langlinks in
        https://www.mediawiki.org/wiki/API:Query#API_documentation

        """

        if languages is None:
            languages = []
        elif isinstance(languages, str):
            languages = [languages]

        # If ISO language codes are given, convert to Wikipedia codes
        languages = [WpLangTools.lang_map[lang]
                     if lang in WpLangTools.lang_map.keys() else lang
                     for lang in languages]

        if pages is None:
            pages = self.pages
        elif isinstance(pages, dict):
            pages = [pages]

        title_translations = []
        for page in pages:
            langlinks = None
            if page is not None:
                try:
                    langlinks_json = page['langlinks']
                except KeyError:
                    pass
                else:
                    # Convert JSON to dict
                    langlinks = {}
                    for item in langlinks_json:
                        if (item['lang'] in languages) or not languages:
                            langlinks[item['lang']] = item['title']

            title_translations.append(langlinks)

        return title_translations

    def translate_title(self, languages=None, pages=None, resolve=True):
        """Use interwiki language links to find (and optionally resolve) page title."""

        if languages is None:
            languages = []
        elif isinstance(languages, str):
            languages = [languages]

        if pages is None:
            pages = self.pages
        elif isinstance(pages, dict):
            pages = [pages]

        title_translations = self.translate_title_noresolve(languages, pages)

        if not resolve:
            return title_translations

        for i, page in enumerate(title_translations):
            if page is not None:
                for lang in page:
                    if self.verbose:
                        print('Resolving ' + lang + ':' + page[lang])
                    elif not self.silent:
                        print('.', end='')
                    resolved_title = WpLangTools.resolve_title(
                        page[lang],
                        site=lang)
                    title_translations[i][lang] = resolved_title

        if not self.silent:
            print('')

        return title_translations

    def __init__(self, *page_titles, **kwargs):
        """Fetch page(s) info from Wikimedia API.

        If it is known certain parameters will not be used, reduce load by
        skipping those parameters.

        Wikimedia limits regular users to 50 titles per request.

        """

        # Process kwargs (keyword arguments)
        languages = []
        if 'languages' in kwargs.keys():
            languages = kwargs['languages']
            if isinstance(languages, str):
                languages = [languages]
        self.silent = False
        if 'silent' in kwargs.keys():
            self.silent = True
        self.verbose = False
        if 'verbose' in kwargs.keys() and not self.silent:
            self.verbose = True

        # For now, only support fetching one language
        if len(languages) > 1:
            print('MediaWiki API currently only supports returning all ' +
                  'languages or only one language, see ' +
                  'https://www.mediawiki.org/wiki/API_talk:Langlinks')
            print('Only fetching results in language ' + languages[0])
            languages = [languages[0]]

        # Wikimedia limits regular users to 50 titles per request.
        if len(page_titles) > 50:
            print('Wikimedia limits regular users to 50 titles per request' +
                  ', ignoring last ' + str(len(page_titles)-50) + ' titles.')
            page_titles = page_titles[:50]

        # Resolve titles using OpenSearch API to get fully valid titles
        # (pointing to articles without redirects, typos, invalid titles, etc.)
        # for easier understanding with Parse API and Query API
        self.titles = WpLangTools.resolve_title(*page_titles)

        urlbase = (r'https://en.wikipedia.org/w/api.php' +
                   r'?action=query&format=json&formatversion=2')

        urlargs = r'&prop=categories|langlinks'
        urlargs += r'&cllimit=max&lllimit=max'
        if languages:
            urlargs += '&lllang=' + '|'.join(languages)
        urlargs += r'&clcategories=' + WpLangTools.disambiguation_category_name
        urlargs += r'&titles='

        self.url = urlbase + urlargs + '|'.join(filter(None, self.titles))
        self.json = WpLangTools.url_to_json(self.url)
        self.json_pages = self.json['query']['pages']

        # Sort pages to follow order provided in initialization arguments
        # (including potential duplicates)
        #
        # Sorting can be accomplished more efficiently with
        # a.sort(key=lambda (x,y): b.index(x)), but this is good enough for
        # list where max length is 50 anyway
        # https://stackoverflow.com/q/12814667/6047827
        self.pages = []
        for title in self.titles:
            if title is None:
                self.pages.append(None)
            else:
                for page in self.json_pages:
                    if page['title'] == title:
                        self.pages.append(page)
