try:
    from urllib.parse import unquote_plus
except ImportError:
    from urllib import unquote_plus
import time, re, requests
from bs4 import BeautifulSoup

class Scraper:

    def __init__(self):
        self.base_url = 'http://fanfiction.net/'
        self.rate_limit = 1
        self.parser = "html.parser"
        self.genres = [
            'Adventure','Angst','Crime','Drama','Family','Fantasy',
            'Friendship','General','Horror','Humor','Hurt/Comfort',
            'Mystery','Parody','Poetry','Romance','Sci-Fi','Spiritual',
            'Supernatural','Suspense','Tragedy','Western'
        ]

    def get_genres(self, genre_text):
        genres = genre_text.split('/')
        # Hurt/Comfort is annoying because of the '/'
        return ['Hurt/Comfort' if g == 'Hurt' else g for g in genres
                if g != 'Comfort']

    def scrape_story_metadata(self, story_id):
        """
        Returns a dictionary with the metadata for the story.
        Attributes:
            -id: the id of the story
            -canon_type: the type of canon
            -canon: the name of the canon
            -author_id: the user id of the author
            -title: the title of the story
            -updated: the timestamp of the last time the story was updated
            -published: the timestamp of when the story was originally published
            -lang: the language the story is written in
            -genres: a list of the genres that the author categorized the story as
            -num_reviews
            -num_favs
            -num_follows
            -num_words: total number of words in all chapters of the story
            -rated: the story's rating
            -characters: characters noted as being in the story
            -completed: whether the story is completed or not
        """
        url = '{0}/s/{1}'.format(self.base_url, story_id)
        result = requests.get(url)
        html = result.content
        soup = BeautifulSoup(html, self.parser)
        if soup.find(id='pre_story_links'):
          author_id = int(re.search(r"var userid = (.*);", str(soup)).groups()[0]);
          title = re.search(r"var title = (.*);", str(soup)).groups()[0];
          title = unquote_plus(title)[1:-1]
          pre_story_links = soup.find(id='pre_story_links').find_all('a')
          metadata = {
            'id': story_id,
            'author_id': author_id,
            'title': title,
          }
          metadata_div = soup.find(id='profile_top')
          times = metadata_div.find_all(attrs={'data-xutime':True})
          if (len(times) == 1):
              metadata['published'] = int(times[0]['data-xutime'])
              metadata['updated'] = -1
          else:
              metadata['published'] = int(times[1]['data-xutime'])
              metadata['updated'] = int(times[0]['data-xutime'])

          metadata_text = metadata_div.find(class_='xgray xcontrast_txt').text
          metadata_parts = metadata_text.split(' - ')
          keyed, unkeyed = [], []
          for p in metadata_parts:
              (keyed if ':' in p else unkeyed).append(p)
          metadata['lang'] = unkeyed.pop(0).strip()
          if unkeyed:
              next = unkeyed.pop(0).strip()
              genres = self.get_genres(next)
              if genres[0] in ''.join(self.genres):
                  metadata['genres'] = genres
              else:
                  unkeyed.insert(0, next)
              if unkeyed:
                  next = unkeyed.pop(0).strip()
                  chars = [char.strip() for char in next.split(',')]
                  metadata['characters'] = chars
          if (len(pre_story_links) == 1):
            metadata['canon'] = pre_story_links[0].text
            metadata['canon_type'] = "Crossover"
          else:
            metadata['canon'] = pre_story_links[1].text
            metadata['canon_type'] = pre_story_links[0].text
          for part in keyed:
              part = part.strip()
              tag, val = part.split(':')
              tag = tag.strip().lower()
              if tag not in metadata:
                  val = val.strip()
                  try:
                      val = int(val.replace(',', ''))
                      metadata['num_'+tag] = val
                  except:
                      metadata[tag] = val
          metadata['complete'] = 'status' in metadata
          metadata.pop('status', None)
          return metadata
        return None

    def scrape_story(self, story_id, keep_html=False):
        metadata = self.scrape_story_metadata(story_id)
        metadata['chapters'] = {}
        metadata['reviews'] = {}
        if ('num_chapters' in metadata.keys()):
            num_chapters = metadata['num_chapters']
        else:
            num_chapters = 1
        # rate limit to follow fanfiction.net TOS
        time.sleep(self.rate_limit)
        for chapter_id in range(1, num_chapters + 1):
            time.sleep(self.rate_limit)
            chapter = self.scrape_chapter(story_id, chapter_id)
            time.sleep(self.rate_limit)
            chapter_reviews = self.scrape_reviews_for_chapter(
                story_id, chapter_id)
            metadata['chapters'][chapter_id] = chapter
            metadata['reviews'][chapter_id] = chapter_reviews
        return metadata

    def scrape_chapter(self, story_id, chapter_id, keep_html=False):
        url = '{0}/s/{1}/{2}'.format(self.base_url, story_id, chapter_id)
        result = requests.get(url)
        html = result.content
        soup = BeautifulSoup(html, self.parser)
        chapter = soup.find(class_='storytext')
        if not keep_html:
            chapter_text = chapter.get_text(' ').encode('utf8')
        return chapter_text

    def scrape_reviews_for_chapter(self, story_id, chapter_id):
        """
        Scrape reviews for chapter in story.
        Returns:
            Array of review dicts.
            Each review dict contains the user id of the reviewer if it exists,
            the timestamp of the review, and the text of the review.
        """
        url = '{0}/r/{1}/{2}'.format(self.base_url, story_id, chapter_id)
        result = requests.get(url)
        html = result.content
        soup = BeautifulSoup(html, self.parser)
        reviews_table = soup.find(class_='table-striped').tbody
        reviews_tds = reviews_table.find_all('td')
        reviews = []
        for review_td in reviews_tds:
            match = re.search(r'href="/u/(.*)/.*">.*</a>', str(review_td))
            if match is not None:
                user_id = int(match.groups()[0])
            else:
                user_id = None
            time = review_td.find('span', attrs={'data-xutime':True})
            time = int(time['data-xutime'])
            review = {
                'time': time,
                'user_id': user_id,
                'text': review_td.div.text.encode('utf8')
            }
            reviews.append(review)
        return reviews
