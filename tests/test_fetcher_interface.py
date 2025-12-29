import pytest
from unittest.mock import Mock
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))
import helpers.fetcher as fetcher_module

# ====== POMOCNICZA KLASA TESTOWA ======
class DummyFetcher(fetcher_module.FetcherInterface):
    def url_validator(self, url):
        return url.startswith("http")

    def get_description(self, content):
        return "Opis produktu"

    def get_image_url(self, content):
        return "http://example.com/image.jpg"

    def get_price(self, content):
        return "100 PLN"

    def get_availability(self, content):
        return True

    def build_persistance_manager(self):
        pm = Mock()
        pm.get.return_value = {
            "id": 1,
            "image_path": "/tmp/img.jpg",
            "description": "Zapisany opis",
            "price": "50 PLN",
            "is_available": True,
            "name": "Produkt"
        }
        return pm


# ====== FIXTURES ======
@pytest.fixture(autouse=True)
def mock_requests(monkeypatch):
    response = Mock()
    response.text = "<html>content</html>"
    response.raise_for_status = Mock()

    monkeypatch.setattr(
        fetcher_module.requests,
        "get",
        Mock(return_value=response)
    )


@pytest.fixture(autouse=True)
def mock_download(monkeypatch):
    monkeypatch.setattr(
        fetcher_module.FetcherInterface,
        "_download",
        lambda self, url, name: f"/fake/path/{name}.jpg"
    )


# ====== TESTY ======
def test_invalid_url():
    with pytest.raises(ValueError, match="Podano nieobsługiwany URL"):
        DummyFetcher(url="ftp://example.com")


def test_valid_url_creates_object(mock_requests, mock_download):
    fetcher = DummyFetcher(
        url="http://example.com",
        name="produkt"
    )

    assert fetcher.id is None
    assert fetcher.name == "produkt"
    assert fetcher.description == "Opis produktu"
    assert fetcher.price == "100 PLN"
    assert fetcher.is_available is True
    assert fetcher.img_path.endswith("produkt.jpg")
    assert fetcher.is_saved() is False
    assert fetcher.is_created() is True


def test_load_from_persistence():
    fetcher = DummyFetcher(id=1)

    assert fetcher.id == 1
    assert fetcher.name == "Produkt"
    assert fetcher.description == "Zapisany opis"
    assert fetcher.price == "50 PLN"
    assert fetcher.is_available is True
    assert fetcher.is_saved() is False
    assert fetcher.is_created() is False


def test_missing_persistence_manager():
    class BrokenFetcher(fetcher_module.FetcherInterface):
        def build_persistance_manager(self):
            return None

        def url_validator(self, url):
            return True

    with pytest.raises(ValueError, match="Persistance Manager nie został zdefiniowany"):
        BrokenFetcher(id=1)


def test_template_parser_success():
    import re
    fetcher = DummyFetcher(url="http://example.com", name="x")

    content = "<div>Opis <b>testowy</b></div>"
    pattern = re.compile(r"<div>(.*?)</div>")

    result = fetcher._get_template(content, pattern)

    assert result == "Opis testowy"


def test_template_parser_fail():
    import re
    fetcher = DummyFetcher(url="http://example.com", name="x")

    result = fetcher._get_template("", re.compile(".*"))

    assert result == ""
    assert fetcher.is_content_correct is False
