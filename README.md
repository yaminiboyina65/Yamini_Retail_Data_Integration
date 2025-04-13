The DataFoundation project integrates multiple retail data sources, including retail sales data, product catalogs from the Fake Store API, and cart data. 
The process starts by fetching and cleaning data through an ETL pipeline, which loads the transformed data into Google BigQuery for scalable storage. 
Interactive dashboards are created using Streamlit to visualize sales, products, and cart data, with filtering capabilities. 
The project supports historical data tracking with Slowly Changing Dimensions (SCD Type 2). 
Unit tests ensure proper functionality of API responses, data transformations, and Streamlit components, providing a robust solution for retail data analysis and visualization.

Key Features:
Data Integration: Combines multiple data sources (Retail Sales, Fake Store API, Cart data).

ETL Process: Transforms and loads data into BigQuery.

Streamlit Dashboards: Interactive dashboards for visualizing sales and product data.

SCD Type 2: Tracks historical changes in data.

Testing: Unit tests with pytest for API response, data transformation, and Streamlit components.
