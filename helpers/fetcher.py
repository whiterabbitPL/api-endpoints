import os
import requests
import urllib.request
from urllib.parse import urlparse
from datetime import datetime
import time
import re
import mysql.connector
import base64

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'localhost'),
        user=os.getenv('MYSQL_USER', 'dummy'),
        password=os.getenv('MYSQL_PASSWORD', ''),
        database=os.getenv('MYSQL_DATABASE', 'lab')
    )

class ManagerInterface:
    def __init__(self, place):
        # Place will be a place where data will be stored, it will be a table for mysql and file path for files
        self.place = place
    def save(self, product_name, product_description, product_price, product_available, product_img_path, product_id, product_url):
        raise ValueError("Save method not implemented in Manager Class")
    def get(self, product_id):
        raise ValueError("Get method not implemented in Manager Class")
    def delete(self, product_id):
        raise ValueError("Delete method not implemented in Manager Class")

# Struktura tabeli do stworzenia w bazie:
#CREATE TABLE products (
#    id BIGINT PRIMARY KEY,
#    url VARCHAR(2048) NOT NULL,
#    name VARCHAR(255),
#    description LONGTEXT,
#    price DECIMAL(7,2),
#    is_available BOOLEAN,
#    img_path VARCHAR(255),
#    last_checked DATETIME NOT NULL
#);

class MySQLManager(ManagerInterface):

    def __init__(self, place=None):
        super().__init__(place)

    def save(self, product_name, product_description, product_price, product_available, product_img_path, product_id, product_url):
        name = product_name[:255]
        description = product_description
        price = product_price
        is_available = product_available
        img_path = product_img_path
        last_checked = datetime.now()

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Sprawdzamy czy rekord istnieje
            cursor.execute(
                "SELECT 1 FROM products WHERE id = %s",
                (product_id,)
            )
            exists = cursor.fetchone() is not None

            if exists:
                cursor.execute(
                    """
                    UPDATE products
                    SET
                        url = %s,
                        name = %s,
                        description = %s,
                        price = %s,
                        is_available = %s,
                        last_checked = %s,
                        img_path = %s
                    WHERE id = %s
                    """,
                    (
                        product_url,
                        name,
                        description,
                        price,
                        is_available,
                        last_checked,
                        img_path,
                        product_id
                    )
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO products (
                        id, url, name, description, price, is_available, last_checked, img_path
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        product_id,
                        product_url,
                        name,
                        description,
                        price,
                        is_available,
                        last_checked,
                        img_path
                    )
                )

            conn.commit()

        finally:
            cursor.close()
            conn.close()

    def get(self, product_id) -> dict | None:

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        try:
            cursor.execute(
                "SELECT * FROM products WHERE id = %s",
                (product_id,)
            )
            return cursor.fetchone()
        finally:
            cursor.close()
            conn.close()

    def delete(self, product_id):

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(
                "DELETE FROM products WHERE id = %s",
                (product_id,)
            )
            conn.commit()
        finally:
            cursor.close()
            conn.close()



class FetcherInterface:
    def __init__(self, url='', id=None, name=''):
        current_dir = os.getcwd()
        parent_dir = os.path.dirname(current_dir)
        target_dir = os.path.join(parent_dir, 'images')
        os.makedirs(target_dir, exist_ok=True)
        self.path = target_dir
        self.url = url
        if id:
             self.persistance_manager = self.build_persistance_manager()
             if not self.persistance_manager:
                 raise ValueError("Persistance Manager nie został zdefiniowany w klasie podobnej: missing build_persistance_manager")
             data = self.persistance_manager.get(id)
             if not data:
                 raise ValueError("Nie udało się załadować obiektu o wskazanym ID")
             self.id = data["id"]
             self.img_path = data["img_path"]
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
        return self.id is not None

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

    def get_name(self, content):
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
        target_path = os.path.join(self.path, f"{name}{ext}")
        urllib.request.urlretrieve(url, target_path)
        return target_path

    def _get_template(self, content, pattern):
        if not content:
            self.is_content_correct = False
            return ''

        match = pattern.search(content)

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

    def normalize_url(self, url: str) -> str:
        """Zwraca URL obcięty do znaku '?'."""
        return url.split('?', 1)[0]

    def extract_product_id(self, url: str) -> int:
        raise ValueError("Product id extractor not implemented")
    
    def save(self):
        if self.persistance_manager:
            self.id = self.extract_product_id(self.url)
            response = self.persistance_manager.save(
                self.name, 
                self.description, 
                self.price, 
                self.is_available, 
                self.img_path,
                self.id, 
                self.url
                )
            if response:
                self.saved = True
                return self.id
        return None

    def delete(self):
        if self.persistance_manager:
            return self.persistance_manager.delete(self.extract_product_id(self.url))
        else:
            return None
        
    def get_persistant_state(self):
        if self.persistance_manager:
            return self.persistance_manager.get(self.extract_product_id(self.url))
        else:
            return None


class Ceneo(FetcherInterface):
    def url_validator(self, url):
        return url.startswith("https://www.ceneo.pl/")

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
        raw = self._get_template(content, pattern)
        return float(raw.replace(' ', '').replace(',', '.'))

    def get_availability(self, content):
        return self.get_price(content) > 0
    
    def get_name(self, content: str) -> str:
        pattern = re.compile(
            r'<h1[^>]*class="[^"]*product-top__product-info__name[^"]*"[^>]*>(.*?)</h1>',
            re.IGNORECASE | re.DOTALL
        )
        return self._get_template(content, pattern)
    
    def get_description(self, content):
        pattern = re.compile(
            r'<div class="lnd_content">.*</h2>(.*?)</div>', 
            re.IGNORECASE | re.DOTALL
        )
        return self._get_template(content, pattern)

    def extract_product_id(self, url: str) -> int:
        """
        Wyciąga ID produktu z URL:
        https://www.ceneo.pl/162849793?... -> 162849793
        """
        base = self.normalize_url(url)
        parsed = urlparse(base)
        return int(parsed.path.strip('/').split('/')[-1])
    

def with_mysql_persistence(place: str):
    def decorator(cls):
        if not issubclass(cls, FetcherInterface):
            raise TypeError("Decorator can be used only with FetcherInterface subclasses")

        original_build = getattr(cls, "build_persistance_manager", None)

        def build_persistance_manager(self):
            self.persistance_manager = MySQLManager(place)
            return self.persistance_manager

        cls.build_persistance_manager = build_persistance_manager
        return cls
    return decorator

class AllegroClient:
    AUTH_URL = "https://allegro.pl/auth/oauth/token"
    API_URL = "https://api.allegro.pl"

    def __init__(self, client_id: str, client_secret: str):
        self.client_id = client_id
        self.client_secret = client_secret
        self._token = None
        self._token_expiry = 0

    def _get_token(self) -> str:
        auth = base64.b64encode(
            f"{self.client_id}:{self.client_secret}".encode()
        ).decode()

        response = requests.post(
            self.AUTH_URL,
            headers={
                "Authorization": f"Basic {auth}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={"grant_type": "client_credentials"},
            timeout=10
        )
        response.raise_for_status()

        data = response.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 30
        return self._token

    def _get_valid_token(self) -> str:
        if not self._token or time.time() >= self._token_expiry:
            return self._get_token()
        return self._token

    def get(self, path: str, params: dict | None = None) -> dict:
        token = self._get_valid_token()

        response = requests.get(
            f"{self.API_URL}{path}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.allegro.public.v1+json"
            },
            params=params,
            timeout=10
        )
        response.raise_for_status()
        return response.json()


class AllegroFetcher(FetcherInterface):
    def __init__(self, allegro_client: AllegroClient, url: str, name: str = ""):
        self.client = allegro_client
        super().__init__(url=url, name=name)

    # ========================
    # Walidacja URL
    # ========================
    def url_validator(self, url: str) -> bool:
        return url.startswith("https://allegro.pl/oferta/")

    # ========================
    # ID oferty z URL
    # ========================
    def extract_product_id(self, url: str) -> str:
        """
        https://allegro.pl/oferta/...-17115537557?... -> 17115537557
        """
        base = url.split("?", 1)[0]
        offer_id = base.rsplit("-", 1)[-1]

        if not offer_id.isdigit():
            raise ValueError("Nie udało się wyciągnąć ID oferty Allegro")

        return offer_id

    # ========================
    # Nadpisujemy pobieranie danych
    # ========================
    def get_page(self, url):
        """
        Nie pobieramy HTML – pobieramy JSON z Allegro API
        """
        offer_id = self.extract_product_id(url)
        return self.client.get(f"/offers/{offer_id}")

    # ========================
    # Mapowanie JSON → pola Fetchera
    # ========================
    def get_image_url(self, data: dict) -> str:
        images = data.get("images", [])
        return images[0]["url"] if images else ""

    def get_description(self, data: dict) -> str:
        return data.get("description", {}).get("plainText", "")

    def get_price(self, data: dict) -> float:
        return float(data["sellingMode"]["price"]["amount"])

    def get_availability(self, data: dict) -> bool:
        return data["stock"]["available"] > 0

    def get_name(self, data: dict) -> str:
        return data["name"]
