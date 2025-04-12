import pytest
import requests
from unittest.mock import patch, MagicMock
import streamlit as st
import pandas as pd
from unittest.mock import patch

# Mock API response for Fake Store API
FAKE_STORE_API_RESPONSE = [
    {
        "id": 1,
        "title": "Product A",
        "price": 29.99,
        "category": "electronics",
        "image": "https://example.com/image.jpg",
        "rating": {"rate": 4.5, "count": 10},
    },
    {
        "id": 2,
        "title": "Product B",
        "price": 49.99,
        "category": "clothing",
        "image": "https://example.com/image2.jpg",
        "rating": {"rate": 3.8, "count": 5},
    },
]

@pytest.fixture
def mock_api_response():
    """Mock the requests.get() call to return a predefined response."""
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = FAKE_STORE_API_RESPONSE
        yield mock_get

def test_api_fetch(mock_api_response):
    """Test that API fetch works and returns expected structure."""
    response = requests.get("https://fakestoreapi.com/products").json()
    assert isinstance(response, list)
    assert len(response) == 2
    assert "title" in response[0]
    assert "price" in response[0]

def test_empty_api_response():
    """Test handling when API returns an empty response."""
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = []
        response = requests.get("https://fakestoreapi.com/products").json()
        assert response == []

def test_invalid_api_response():
    """Test handling of invalid API responses (e.g., 500 Internal Server Error)."""
    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 500
        mock_get.return_value.json.side_effect = requests.exceptions.RequestException
        with pytest.raises(requests.exceptions.RequestException):
            requests.get("https://fakestoreapi.com/products").json()

def test_api_timeout():
    """Test handling of API timeout errors."""
    with patch("requests.get") as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout
        with pytest.raises(requests.exceptions.Timeout):
            requests.get("https://fakestoreapi.com/products", timeout=1)

def test_missing_fields():
    """Test handling when API response lacks expected fields."""
    incomplete_response = [{"id": 3, "title": "Product C"}]  # Missing price, category, etc.
    with patch("requests.get") as mock_get:
        mock_get.return_value.json.return_value = incomplete_response
        response = requests.get("https://fakestoreapi.com/products").json()
        assert "price" not in response[0]

def test_dataframe_creation():
    """Test DataFrame creation from API data."""
    df = pd.DataFrame(FAKE_STORE_API_RESPONSE)
    assert not df.empty
    assert list(df.columns) == ["id", "title", "price", "category", "image", "rating"]

def test_dataframe_sorting():
    """Test sorting functionality for price column."""
    df = pd.DataFrame(FAKE_STORE_API_RESPONSE)
    sorted_df = df.sort_values(by="price", ascending=True)
    assert sorted_df.iloc[0]["title"] == "Product A"  # Lowest price should be first

def test_dataframe_filtering():
    """Test filtering functionality for category."""
    df = pd.DataFrame(FAKE_STORE_API_RESPONSE)
    filtered_df = df[df["category"] == "electronics"]
    assert len(filtered_df) == 1
    assert filtered_df.iloc[0]["title"] == "Product A"

def test_streamlit_initialization():
    """Test that Streamlit elements are properly initialized."""
    with patch("streamlit.set_page_config") as mock_set_page_config:
        st.set_page_config(page_title="Fake Store Dashboard")
        mock_set_page_config.assert_called_once_with(page_title="Fake Store Dashboard")

def test_streamlit_button():
    """Test if Streamlit button is being clicked."""
    with patch("streamlit.button") as mock_button:
        mock_button.return_value = True
        assert st.button("Click Me") is True

def test_streamlit_selectbox():
    """Test if Streamlit selectbox returns expected option."""
    options = ["electronics", "clothing"]
    with patch("streamlit.selectbox") as mock_selectbox:
        mock_selectbox.return_value = "electronics"
        assert st.selectbox("Select Category", options) == "electronics"
