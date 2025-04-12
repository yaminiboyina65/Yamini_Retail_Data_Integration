import streamlit as st
import pandas as pd
import requests
import os
import logging
import matplotlib.pyplot as plt
import altair as alt
from google.cloud import bigquery

# Configure Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configure Streamlit page
st.set_page_config(page_title="Retail Data Explorer", layout="wide")

# Sidebar Navigation
st.sidebar.title("📊 Dashboard Navigation")
selected_dashboard = st.sidebar.selectbox("Select Dashboard:", ["Retail Dashboard", "Fake Store API Dashboard"])


# Fetch Retail Sales Data from BigQuery
@st.cache_data
def fetch_retail_sales():
    try:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = r"C:\Users\boyin\Downloads\symbolic-surf-454106-v9-e6347c5dcb60.json"
        client = bigquery.Client()
        query = "SELECT * FROM symbolic-surf-454106-v9.Retail_Data.Retail_Sales"
        logging.info("Fetching Retail Sales data from BigQuery...")
        return client.query(query).to_dataframe()
    except Exception as e:
        logging.error(f"Error fetching Retail Sales data: {e}")
        st.error("Failed to fetch retail sales data. Check logs for details.")
        return pd.DataFrame()

# Fetch Fake Store API Product Data
@st.cache_data
def fetch_product_data():
    try:
        url = "https://fakestoreapi.com/products"
        logging.info("Fetching Fake Store API product data...")
        response = requests.get(url)
        response.raise_for_status()
        products = response.json()
        df = pd.DataFrame(products)
        df.rename(columns={"id": "Product ID", "title": "Product Name", "category": "Category", "price": "Price", "image": "Product Image"}, inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Fake Store API data: {e}")
        st.error("Failed to fetch product data from Fake Store API. Check logs for details.")
        return pd.DataFrame()

@st.cache_data
def fetch_cart_data():
    try:
        url = "https://fakestoreapi.com/carts"
        logging.info("Fetching Fake Store API cart data...")
        response = requests.get(url)
        response.raise_for_status()
        carts = response.json()
        df = pd.DataFrame(carts)

        # Normalize the 'products' column to create individual product rows
        products_df = pd.json_normalize(df['products'].explode())

        # Merge the 'products' DataFrame back to the cart DataFrame
        df = df.drop(columns=['products']).join(products_df)

        # Rename columns to match product data
        df.rename(columns={"id": "Cart ID", "userId": "User ID", "quantity": "Quantity", "price": "Product Price", 
                           "title": "Product Name"}, inplace=True)

        # Ensure 'Product ID' column exists
        df["Product ID"] = df["Cart ID"]  # Or adjust based on how 'Product ID' is identified

        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Fake Store API cart data: {e}")
        st.error("Failed to fetch cart data from Fake Store API. Check logs for details.")
        return pd.DataFrame()

# Fetch Fake Store User Data
@st.cache_data
def fetch_user_data():
    try:
        url = "https://fakestoreapi.com/users"
        logging.info("Fetching Fake Store API user data...")
        response = requests.get(url)
        response.raise_for_status()
        users = response.json()
        df = pd.DataFrame(users)
        df.rename(columns={"id": "User ID", "name": "Name", "email": "Email", "address": "Address"}, inplace=True)
        return df
    except requests.exceptions.RequestException as e:
        logging.error(f"Error fetching Fake Store API user data: {e}")
        st.error("Failed to fetch user data from Fake Store API. Check logs for details.")
        return pd.DataFrame()

# Load Data Based on Selected Dashboard
if selected_dashboard == "Retail Dashboard":
    st.title("🚀 Retail Data Explorer")
    st.subheader("Retail Analytics Dashboard for Sales, Marketing, and Performance Optimization")

    sales_data = fetch_retail_sales()
    if sales_data.empty:
        st.stop()

    # Sidebar Buttons for Retail Graphs
    graph_button = st.sidebar.radio("Select Graph", [
        "Total Sales Revenue",
        "Sales Trend Over Time",
        "Sales Revenue by Product ID",
        "Category-wise Sales by Location",
        "Marketing Spend vs. Units Sold",
        "Marketing Spend Distribution",
        "Sales Distribution by Day of the Week",
        "Filtered Data Preview"
    ])

    # Total Sales Revenue
    if graph_button == "Total Sales Revenue":
        st.subheader("💰 Total Sales Revenue")
        col1, col2 = st.columns(2)

        try:
            with col1:
                selected_store = st.selectbox("Filter by Store Location", sales_data["store_location"].unique())

            with col2:
                search_category = st.text_input("Search by Category").strip().lower()

            total_sales_filtered = sales_data[sales_data["store_location"] == selected_store]
            if search_category:
                total_sales_filtered = total_sales_filtered[total_sales_filtered["category"].str.lower().str.contains(search_category, na=False)]

            total_sales = total_sales_filtered["sales_revenue"].sum()
            st.metric(label="Total Revenue", value=f"${total_sales:,.2f}")
        except Exception as e:
            logging.error(f"Error calculating total sales revenue: {e}")
            st.error("Failed to calculate total revenue.")

    # Sales Trend Over Time
    elif graph_button == "Sales Trend Over Time":
        st.subheader("📈 Sales Trend Over Time")
        try:
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("Select Start Date", pd.to_datetime(sales_data["date"]).min())
            with col2:
                end_date = st.date_input("Select End Date", pd.to_datetime(sales_data["date"]).max())

            sales_data["date"] = pd.to_datetime(sales_data["date"])
            sales_trend_filtered = sales_data[(sales_data["date"] >= pd.to_datetime(start_date)) & (sales_data["date"] <= pd.to_datetime(end_date))]

            time_series = sales_trend_filtered.groupby("date")["sales_revenue"].sum().reset_index()
            time_chart = alt.Chart(time_series).mark_line().encode(x="date:T", y="sales_revenue:Q").properties(width=700)
            st.altair_chart(time_chart, use_container_width=True)
        except Exception as e:
            logging.error(f"Error generating sales trend chart: {e}")
            st.error("Failed to generate sales trend chart.")

    # New: Sales Revenue by Product ID
    elif graph_button == "Sales Revenue by Product ID":
        st.subheader("🏷️ Sales Revenue by Product ID")
        selected_store_product = st.selectbox("Filter by Store Location for Product Sales", sales_data["store_location"].unique(), key="product_store")

        product_filtered = sales_data[sales_data["store_location"] == selected_store_product]
        product_sales = product_filtered.groupby("product_id")["sales_revenue"].sum().reset_index()

        product_chart = alt.Chart(product_sales).mark_bar().encode(
            x="sales_revenue:Q",
            y=alt.Y("product_id:N", sort="-x"),
            color=alt.Color("product_id:N", legend=None),
            tooltip=["product_id", "sales_revenue"]
        ).properties(width=700, height=400)

        st.altair_chart(product_chart, use_container_width=True)

    # Category-wise Sales by Location (Pie Chart)
    elif graph_button == "Category-wise Sales by Location":
        st.subheader("📊 Category-wise Sales by Location")
        selected_store_pie = st.selectbox("Filter Pie Chart by Store Location", sales_data["store_location"].unique(), key="pie_store")

        pie_filtered = sales_data[sales_data["store_location"] == selected_store_pie]
        category_pie = pie_filtered.groupby("category")["sales_revenue"].sum().reset_index()

        pie_chart = alt.Chart(category_pie).mark_arc().encode(
            theta="sales_revenue:Q",
            color="category:N",
            tooltip=["category", "sales_revenue"]
        ).properties(width=300, height=300)
        
        st.altair_chart(pie_chart, use_container_width=True)

    # Units Sold vs. Marketing Spend Scatter Plot
    elif graph_button == "Marketing Spend vs. Units Sold":
        st.subheader("📢 Marketing Spend vs. Units Sold")

        # Select store for filtering (Only one dropdown)
        selected_store_marketing_units = st.selectbox("Select Store Location", sales_data["store_location"].unique(), key="marketing_units_store")

        # Filter data
        filtered_data = sales_data[sales_data["store_location"] == selected_store_marketing_units]

        # Create scatter plot
        scatter_plot = alt.Chart(filtered_data).mark_circle(size=60).encode(
            x=alt.X("marketing_spend:Q", title="Marketing Spend (USD)"),
            y=alt.Y("units_sold:Q", title="Units Sold"),
            color=alt.Color("category:N", legend=None),
            tooltip=["category", "marketing_spend", "units_sold"]
        ).properties(width=700, height=400)

        st.altair_chart(scatter_plot, use_container_width=True)

    # Marketing Spend Distribution
    elif graph_button == "Marketing Spend Distribution":
        st.subheader("🔄 Marketing Spend Distribution")
        selected_store_marketing = st.selectbox("Filter by Store Location for Marketing Spend", sales_data["store_location"].unique(), key="marketing_store")

        marketing_filtered = sales_data[sales_data["store_location"] == selected_store_marketing]

        fig, ax = plt.subplots(figsize=(8, 4))
        ax.hist(marketing_filtered["marketing_spend"], bins=20, color="skyblue", edgecolor="black")
        ax.set_xlabel("Marketing Spend (USD)")
        ax.set_ylabel("Frequency")
        st.pyplot(fig)

    # Sales Distribution Across Days of the Week with Category Filter
    elif graph_button == "Sales Distribution by Day of the Week":
        st.subheader("📅 Sales Distribution by Day of the Week")

        # Dropdown to select category
        selected_category = st.selectbox("Filter by Category", ["All"] + list(sales_data["category"].unique()), key="day_category")

        # Filter data based on selected category
        if selected_category != "All":
            filtered_sales = sales_data[sales_data["category"] == selected_category]
        else:
            filtered_sales = sales_data.copy()

        # Aggregate sales revenue by day of the week
        sales_by_day = filtered_sales.groupby("day_of_the_week")["sales_revenue"].sum().reset_index()

        # Create bar chart
        sales_by_day_chart = alt.Chart(sales_by_day).mark_bar().encode(
            x=alt.X("day_of_the_week:N", title="Day of the Week", 
                sort=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]),
            y=alt.Y("sales_revenue:Q", title="Total Sales Revenue"),
            color=alt.Color("day_of_the_week:N", legend=None),
            tooltip=["day_of_the_week", "sales_revenue"]
        ).properties(width=700, height=400)

        st.altair_chart(sales_by_day_chart, use_container_width=True)
    
    # Filtered Data Preview with Pagination
    elif graph_button == "Filtered Data Preview":
        st.subheader("📋 Filtered Data Preview")
        selected_store_preview = st.selectbox("Filter Data Preview by Store Location", sales_data["store_location"].unique(), key="preview_store")
        filtered_preview = sales_data[sales_data["store_location"] == selected_store_preview]

        # Pagination Controls
        rows_per_page = st.slider("Rows per Page", min_value=5, max_value=50, value=10, step=5)
        total_pages = (len(filtered_preview) // rows_per_page) + (1 if len(filtered_preview) % rows_per_page != 0 else 0)
        page_number = st.number_input("Page Number", min_value=1, max_value=total_pages, value=1, step=1)

        # Paginate Data
        start_idx = (page_number - 1) * rows_per_page
        end_idx = start_idx + rows_per_page
        paginated_data = filtered_preview.iloc[start_idx:end_idx]

        st.dataframe(paginated_data)
        st.write(f"Page {page_number} of {total_pages} | Total Rows: {len(filtered_preview)}")


elif selected_dashboard == "Fake Store API Dashboard":
    st.title("🛒 Fake Store API Data Explorer")
    st.subheader("Analyze Product, Cart, and User Data from Fake Store API")

    # Fetch Data
    fake_store_data = fetch_product_data() 
    cart_data = fetch_cart_data()
    user_data = fetch_user_data()

    if fake_store_data.empty or cart_data.empty or user_data.empty:
        st.stop()

    # Sidebar for selecting the data type (Products, Cart, Users, Merged Data)
    selected_table = st.sidebar.radio("Select Table", ["Products", "Cart", "Users"])

    if selected_table == "Products":
        st.subheader("📊 Products Data")

        # Define filters upfront for Products
        st.subheader("🔍 Apply Filters")
        col1, col2, col3 = st.columns(3)
        try:
            with col1:
                search_product = st.text_input("Search Product Name").strip().lower()

            with col2:
                selected_categories = st.multiselect("Select Categories", fake_store_data["Category"].unique())

            with col3:
                min_price, max_price = st.slider("Filter by Price Range", 
                                                min_value=float(fake_store_data["Price"].min()), 
                                                max_value=float(fake_store_data["Price"].max()), 
                                                value=(float(fake_store_data["Price"].min()), float(fake_store_data["Price"].max())))

            # Filter data based on user input
            filtered_data = fake_store_data.copy()
            if search_product:
                filtered_data = filtered_data[filtered_data["Product Name"].str.lower().str.contains(search_product, na=False)]
            if selected_categories:
                filtered_data = filtered_data[filtered_data["Category"].isin(selected_categories)]
            filtered_data = filtered_data[(filtered_data["Price"] >= min_price) & (filtered_data["Price"] <= max_price)]

        except Exception as e:
            logging.error(f"Error in applying filters: {e}")
            st.error(f"Error: {e}")
            filtered_data = fake_store_data  # Default to original data if there's an error

        # Graph selection for Products
        graph_button_fs = st.radio("Select Graph", [
            "Price Distribution",
            "Category-wise Average Price",
            "Top Expensive Products Showcase",
            "Filtered Product Catalog"
        ])

        if graph_button_fs == "Price Distribution":
            st.subheader("💰 Price Distribution of Filtered Products")
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.hist(filtered_data["Price"], bins=20, color="skyblue", edgecolor="black")
            ax.set_xlabel("Price")
            ax.set_ylabel("Frequency")
            st.pyplot(fig)

        elif graph_button_fs == "Category-wise Average Price":
            st.subheader("📊 Category-wise Average Price")
            category_avg_price = filtered_data.groupby("Category")["Price"].mean().reset_index()
            avg_price_chart = alt.Chart(category_avg_price).mark_bar().encode(
                x=alt.X("Price:Q", title="Average Price (USD)"),
                y=alt.Y("Category:N", sort="-x"),
                color=alt.Color("Category:N", legend=None),
                tooltip=["Category", "Price"]
            ).properties(width=700, height=400)
            st.altair_chart(avg_price_chart, use_container_width=True)

        elif graph_button_fs == "Top Expensive Products Showcase":
            st.subheader("🏆 Top Expensive Products Showcase")
            top_n = st.slider("Select Number of Top Products", min_value=3, max_value=15, value=5, step=1)
            top_products = filtered_data.sort_values(by="Price", ascending=False).head(top_n)
            cols = st.columns(len(top_products))
            for i, row in top_products.iterrows():
                with cols[i % len(cols)]:
                    st.image(row["Product Image"], width=150, caption=f"{row['Product Name']} \n💲{row['Price']:.2f}")

        elif graph_button_fs == "Filtered Product Catalog":
            st.subheader("📋 Filtered Product Catalog with Pagination")
            rows_per_page_fs = st.slider("Rows per Page", min_value=5, max_value=50, value=10, step=5, key="fs_rows")
            total_pages_fs = (len(filtered_data) // rows_per_page_fs) + (1 if len(filtered_data) % rows_per_page_fs != 0 else 0)
            page_number_fs = st.number_input("Page Number", min_value=1, max_value=total_pages_fs, value=1, step=1, key="fs_page")
            start_idx_fs = (page_number_fs - 1) * rows_per_page_fs
            end_idx_fs = start_idx_fs + rows_per_page_fs
            paginated_data_fs = filtered_data.iloc[start_idx_fs:end_idx_fs]

            st.dataframe(paginated_data_fs)
            st.write(f"Page {page_number_fs} of {total_pages_fs} | Total Rows: {len(filtered_data)}")

    elif selected_table == "Cart":
        st.subheader("🛒 Cart Data")

        # Define filters upfront for Cart
        st.subheader("🔍 Apply Filters")
        col1, col2 = st.columns(2)
        try:
            with col1:
                selected_user = st.selectbox("Select User", cart_data["User ID"].unique())

            with col2:
                min_quantity, max_quantity = st.slider("Filter by Quantity", 
                                                        min_value=int(cart_data["Quantity"].min()), 
                                                        max_value=int(cart_data["Quantity"].max()), 
                                                        value=(int(cart_data["Quantity"].min()), int(cart_data["Quantity"].max())))

            # Filter data based on user input
            filtered_cart_data = cart_data.copy()
            if selected_user:
                filtered_cart_data = filtered_cart_data[filtered_cart_data["User ID"] == selected_user]
            filtered_cart_data = filtered_cart_data[(filtered_cart_data["Quantity"] >= min_quantity) & (filtered_cart_data["Quantity"] <= max_quantity)]

        except Exception as e:
            logging.error(f"Error in applying filters: {e}")
            st.error(f"Error: {e}")
            filtered_cart_data = cart_data  # Default to original data if there's an error

        # Graph selection for Cart
        graph_button_cart = st.radio("Select Graph", [
            "Cart Quantity Distribution",
            "Filtered Cart Data"
        ])

        # Cart Quantity Distribution
        if graph_button_cart == "Cart Quantity Distribution":
            st.subheader("📊 Cart Quantity Distribution")
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.hist(filtered_cart_data["Quantity"], bins=20, color="skyblue", edgecolor="black")
            ax.set_xlabel("Quantity")
            ax.set_ylabel("Frequency")
            st.pyplot(fig)

        # Filtered Cart Data with Pagination
        elif graph_button_cart == "Filtered Cart Data":
            st.subheader("📋 Filtered Cart Data with Pagination")
            rows_per_page_cart = st.slider("Rows per Page", min_value=5, max_value=50, value=10, step=5, key="cart_rows")
            total_pages_cart = (len(filtered_cart_data) // rows_per_page_cart) + (1 if len(filtered_cart_data) % rows_per_page_cart != 0 else 0)
            page_number_cart = st.number_input("Page Number", min_value=1, max_value=total_pages_cart, value=1, step=1, key="cart_page")
            start_idx_cart = (page_number_cart - 1) * rows_per_page_cart
            end_idx_cart = start_idx_cart + rows_per_page_cart
            paginated_cart_data = filtered_cart_data.iloc[start_idx_cart:end_idx_cart]

            st.dataframe(paginated_cart_data)
            st.write(f"Page {page_number_cart} of {total_pages_cart} | Total Rows: {len(filtered_cart_data)}")


    # User Data
    elif selected_table == "Users":
        st.subheader("👤 User Data")
        
        # Filters for User Data (only one filter: User ID)
        st.subheader("🔍 Apply Filter")
        try:
            # Single filter for User ID
            selected_user = st.selectbox("Select User", user_data["User ID"].unique(), index=0)

            # Filter data based on user input
            filtered_user_data = user_data.copy()
            if selected_user:
                filtered_user_data = filtered_user_data[filtered_user_data["User ID"] == selected_user]

        except Exception as e:
            logging.error(f"Error in applying filter: {e}")
            st.error(f"Error: {e}")
            filtered_user_data = user_data  # Default to original data if there's an error

        # Graph selection for User Data
        graph_button_users = st.radio("Select Graph", [
            "User Purchase Frequency",
            "User Cart Value Distribution",  # Added new graph option
        ])

        # User Purchase Frequency
        if graph_button_users == "User Purchase Frequency":
            st.subheader("📊 User Purchase Frequency")
            user_purchase_freq = filtered_user_data.groupby("User ID").size().reset_index(name='Purchase Frequency')
            fig, ax = plt.subplots(figsize=(8, 4))
            ax.bar(user_purchase_freq["User ID"], user_purchase_freq["Purchase Frequency"], color="lightblue")
            ax.set_xlabel("User ID")
            ax.set_ylabel("Purchase Frequency")
            ax.set_title("Purchase Frequency by User")
            ax.tick_params(axis="x", rotation=45)  # Rotate for readability
            st.pyplot(fig)

        # User Cart Value Distribution
        elif graph_button_users == "User Cart Value Distribution":
            st.subheader("💰 User Cart Value Distribution")
            # You would need cart or product data to plot cart values, not user data
            # Placeholder plot for now, replace with actual cart data later
            st.write("Cart value distribution plot would need product/cart data.")
            
        # Pagination for filtered User Data
        st.subheader("📋 Filtered User Data with Pagination")
        rows_per_page_user = st.slider("Rows per Page", min_value=5, max_value=50, value=10, step=5, key="user_rows")
        total_pages_user = (len(filtered_user_data) // rows_per_page_user) + (1 if len(filtered_user_data) % rows_per_page_user != 0 else 0)
        page_number_user = st.number_input("Page Number", min_value=1, max_value=total_pages_user, value=1, step=1, key="user_page")
        start_idx_user = (page_number_user - 1) * rows_per_page_user
        end_idx_user = start_idx_user + rows_per_page_user
        paginated_user_data = filtered_user_data.iloc[start_idx_user:end_idx_user]

        st.dataframe(paginated_user_data)
        st.write(f"Page {page_number_user} of {total_pages_user} | Total Rows: {len(filtered_user_data)}")