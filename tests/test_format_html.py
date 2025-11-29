import pytest
from main import format_html   # <-- zmień na właściwą ścieżkę


def test_format_html_basic():
    data = [
        {"user-name": "Agnieszka"},
        {"account_type": "standard"},
        {"description": "To jest moje wspaniałe konto"},
        {"avatar": "http://x.y.z/pic.jpg"}
    ]

    configuration = {
        "headers": "<h3>{value}</h3>",
        "pictures": "<a href=\"{value}\">{key}</a>",
        "default": "<p>{value}</p>"
    }

    form_id = 42
    headers = ["user-name"]
    pictures = ["avatar"]

    expected = (
        '<div class="api-form-42">\n'
        '<h3>Agnieszka</h3>\n'
        '<p>standard</p>\n'
        '<p>To jest moje wspaniałe konto</p>\n'
        '<a href="http://x.y.z/pic.jpg">avatar</a>\n'
        '</div>'
    )

    result = format_html(
        data=data,
        configuration=configuration,
        id=form_id,
        headers=headers,
        pictures=pictures
    )

    assert result == expected
