import pandas as pd
csv_file=r"C:\Users\boyin\Downloads\Retail_Sales_Data.xls"
df=pd.read_csv(csv_file)

df.columns = df.columns.str.strip()
df.drop_duplicates(inplace=True)
df.dropna(inplace=True)  # Remove rows with missing values

df.rename(columns={
    "Product_ID": "Product ID",
    "Product_Name": "Product Name",
    "Category": "Category",
    "Price": "Price",
    "Description": "description",
    "Image_URL": "image",
    "Rating": "rating",
    "product_category":"category",
    "sales_revenue_(usd)": "sales_revenue",
    "marketing_spend_(usd)": "marketing_spend"
}, inplace=True)

retail_cols = df.columns.tolist()

df.to_csv('Retail_Sales.csv', index=False)

# Show link to download the file
import shutil
from IPython.display import FileLink

# Display download link
FileLink('Retail_Sales.csv')