import os
import requests
import urllib.request
import re
from urllib.parse import urlparse

class FetcherInterface:
    def __init__(self, url='', id=None, name=''):
        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        target_dir = os.path.join(parent_dir, 'images')
        os.makedirs(target_dir, exist_ok=True)
        self.path = target_dir
        if id:
             self.persistance_manager = self.build_persistance_manager()
             if not self.persistance_manager:
                 raise ValueError("Persistance Manager nie został zdefiniowany w klasie podobnej: missing build_persistance_manager")
             data = self.persistance_manager.get(id)
             if not data:
                 raise ValueError("Nie udało się załadować obiektu o wskazanym ID")
             self.id = data["id"]
             self.img_path = data["image_path"]
             self.description = data["description"]
             self.price = data["price"]
             self.is_available = data["is_available"]
             self.name = data["name"]
             self.saved = False
        elif self.url_validator(url):
            content = self.get_page(url)
            self.is_content_correct = True
            self.id = None
            self.img_path = self._download(self.get_image_url(content), name)
            self.description = self.get_description(content)
            self.price = self.get_price(content)
            self.is_available = self.get_availability(content)
            self.name = name
            if not self.is_content_correct:
                raise ValueError("Brak możliwości parsowania podanego URL")
            self.saved = False
        else:
            raise ValueError("Podano nieobsługiwany URL")
            
    def build_persistance_manager(self):
        self.persistance_manager = None
        #persistance manager musi posiadać metody get, save, delete
        return False
    
    def url_validator(self, url):
        raise ValueError("Proszę zaimplementuj validator dla fetchera")
        return False

    def is_created(self):
        return not self.id

    def is_saved(self):
        return self.saved
    
    def get_page(self, url):
        response = requests.get(
            url,
            timeout=30,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        response.raise_for_status()
        return response.text

    def get_description(self, content):
        self.is_content_correct = False
        return ''

    def get_image_url(self, content):
        self.is_content_correct = False
        return ''

    def get_price(self, content):
        self.is_content_correct = False
        return ''

    def get_availability(self, content):
        self.is_content_correct = False
        return ''

    def _download(self, url, name):
        ext = url[-4:]
        target_path = os.path.join(self.path, f"{name}.{ext}")
        urllib.request.urlretrieve(url, target_path)
        return target_path

    def _get_template(self, content, pattern):
        if not content:
            self.is_content_correct = False
            return ''

        match = pattern.search(content)
        print(match)
        if not match:
            self.is_content_correct = False
            return ''

        raw_description = match.group(1)

        cleaned = re.sub(r'<[^>]+>', '', raw_description)
        cleaned = cleaned.strip()

        if not cleaned:
            self.is_content_correct = False
            return ''

        return cleaned


class Ceneo(FetcherInterface):
    def url_validator(self, url):
        return (url[0:20]=="https://www.ceneo.pl")

    def get_image_url(self, content):
        pattern = re.compile(
            r'<img[^>]*class="js_gallery-media gallery-carousel__media"[^>]*src="([^"]*)"',
            re.IGNORECASE | re.DOTALL
        )
        return "https:" + self._get_template(content, pattern)

    def get_price(self, content):
        pattern = re.compile(
            r'googletag.pubads...setTargeting."basketPrice","([^"]*?)".;',
            re.IGNORECASE | re.DOTALL
        )
        return self._get_template(content, pattern)

    def get_availability(self, content):
        return (int(self.get_price(content)) > 0)
    
    def get_description(self, content: str) -> str:
        pattern = re.compile(
            r'<h1[^>]*class="[^"]*product-top__product-info__name[^"]*"[^>]*>(.*?)</h1>',
            re.IGNORECASE | re.DOTALL
        )
        return self._get_template(content, pattern)
