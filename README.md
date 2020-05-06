[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=ukanuk_wplangtools&metric=alert_status)](https://sonarcloud.io/dashboard?id=ukanuk_wplangtools)

# wplangtools
 Wikipedia langauge tools: easily extract article titles from Wikipedia across languages

See [siznax/wptools](https://github.com/siznax/wptools) for more comprehensive tools, although that's intended for humans whereas this project is more suitable for automation.

# Install

1. Download `wplangtools.py` and add it to your python path.
  1. One method is opening the Python IDLE interactive interpreter and executing the following commands, changing the directory to wherever you downloaded the file:
  ```python
  >>>import os
  >>>os.chdir(r'D:\Downloads')
  ```
  1. I hear using virtual environments is more secure, so if you know how to set that up please [create an issue and/or pull request](https://github.com/ukanuk/wplangtools/issues).
  
# Example

On the English Wikipedia, load Korean langauge information for the countries *Artsakh* and *Georgia* and the capital *Nukuʻalofa*. Note that *Republic of Artsakh* is used, as only *Artsakh* forwards to a disambiguation page which does not have the correct translations. The `languages=[]` parameter is optional, but makes the raw pages easier to understand at a glance. Here's a very simple example:

```python
>>> from wplangtools import WpLangTools
>>> WpLangTools('Republic of Artsakh').translate_title(languages=['fr'])
.
[{'fr': ['Haut-Karabagh']}]
```

A more complex example checking multiple pages at once. This is the preferred method as it reduces load on Wikimedia servers by bundling requests together.
```python
>>> test_titles = ['Republic of Artsakh','georgia','a nonexistent title','capital of tonga','georgia']
>>> results = WpLangTools(*test_titles, languages=['ko'])
>>> for page in results.pages:
	print(page)
	
{'pageid': 1000530, 'ns': 0, 'title': 'Republic of Artsakh', 'langlinks': [{'lang': 'ko', 'title': '아르차흐 공화국'}]}
{'pageid': 17238515, 'ns': 0, 'title': 'Georgia', 'categories': [{'ns': 14, 'title': 'Category:All disambiguation pages'}], 'langlinks': [{'lang': 'ko', 'title': '조지아'}]}
None
{'pageid': 57356, 'ns': 0, 'title': 'Nukuʻalofa', 'langlinks': [{'lang': 'ko', 'title': '누쿠알로파'}]}
{'pageid': 17238515, 'ns': 0, 'title': 'Georgia', 'categories': [{'ns': 14, 'title': 'Category:All disambiguation pages'}], 'langlinks': [{'lang': 'ko', 'title': '조지아'}]}
```

Check whether page(s) are disambiguation pages instead of regular articles.
```python
>>> results.is_disambiguation()
[False, True, False, False, True]
```

Show loaded translations for each title. This function automatically checks for redirects, so for example the `fr` interwiki language link of `Republic of Artsakh` automatically returns *Haut-Karabagh* rather than *République d'Artsakh* directly form the interwiki language link.
```python
>>> results.translate_title()
....
[{'ko': ['아르차흐 공화국']}, {'ko': ['조지아']}, None, {'ko': ['누쿠알로파']}, {'ko': ['조지아']}]
```

To increase performance, you can disable resolving title translations with `resolve=False`.
```python
>>> WpLangTools('Republic of Artsakh').translate_title(languages=['fr'], resolve=False)
[{'fr': "République d'Artsakh"}]
```
