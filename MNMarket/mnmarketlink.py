# Database connection settings are stored in db_config.py

import streamlit as st
import mysql.connector
from mysql.connector import Error
from db_config import DB_CONFIG   # <-- you provide this locally

# DATABASE CONNECTION
def get_connection():
    """Create and return a new DB connection using DB_CONFIG."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        st.error(f"Error connecting to database: {e}")
        return None


# DATA ACCESS FUNCTIONS
def get_markets():
    """Return all markets ordered by name."""
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT MarketID, Name, Location
        FROM Market
        ORDER BY Name;
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_vendors_for_market(market_id: int):
    """Return vendors that attend a specific market."""
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT Vendor.VendorID, Vendor.BusinessName
        FROM VendorMarket
        JOIN Vendor ON VendorMarket.VendorID = Vendor.VendorID
        WHERE VendorMarket.MarketID = %s;
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(query, (market_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def search_products(keyword: str):
    """Search for products across all markets by name."""
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT 
            Product.ProductID,
            Product.Name AS ProductName,
            Product.Price,
            Vendor.BusinessName,
            Market.Name AS MarketName,
            Market.Location
        FROM Product
        JOIN Vendor ON Product.VendorID = Vendor.VendorID
        JOIN VendorMarket ON Vendor.VendorID = VendorMarket.VendorID
        JOIN Market ON VendorMarket.MarketID = Market.MarketID
        WHERE Product.Name LIKE %s;
    """
    like_param = f"%{keyword}%"
    cur = conn.cursor(dictionary=True)
    cur.execute(query, (like_param,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_customers():
    """Return all customers."""
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT CustomerID, Name, Email
        FROM Customer
        ORDER BY Name;
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_orders_for_customer(customer_id: int):
    """Return all orders for a specific customer."""
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT OrderID, OrderDate, PickupDate, TotalPrice
        FROM Orders
        WHERE CustomerID = %s
        ORDER BY OrderDate DESC;
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(query, (customer_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_order_items(order_id: int):
    """Return all items for a specific order."""
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT 
            OrderItems.OrderItemID,
            Product.Name AS ProductName,
            OrderItems.Quantity,
            OrderItems.Price
        FROM OrderItems
        JOIN Product ON OrderItems.ProductID = Product.ProductID
        WHERE OrderItems.OrderID = %s;
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(query, (order_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows



# MARKET SEARCH PAGE
def page_market_search():
    st.header("Find a Farmers Market")

    markets = get_markets()
    if not markets:
        st.info("No markets found.")
        return

    # Let the user pick a market
    labels = [f"{m['Name']} ({m['Location']})" for m in markets]
    selected_label = st.selectbox("Choose a market:", labels)
    selected_market = markets[labels.index(selected_label)]

    st.subheader("Market Details")
    st.write(f"**Name:** {selected_market['Name']}")
    st.write(f"**Location:** {selected_market['Location']}")

    # Show vendors at this market (user-friendly table)
    st.subheader("Vendors at this Market")
    vendors = get_vendors_for_market(selected_market["MarketID"])
    if vendors:
        pretty_rows = []
        for v in vendors:
            pretty_rows.append({
                "Vendor Name": str(v["BusinessName"])
            })
        st.dataframe(pretty_rows, use_container_width=True)
    else:
        st.write("No vendors are currently listed for this market.")



# PRODUCT SEARCH PAGE
def page_product_search():
    st.header("Search for Products")

    keyword = st.text_input("Search by product name:", value="Tomato")

    if st.button("Search"):
        if not keyword.strip():
            st.warning("Please enter a product name to search.")
            return

        results = search_products(keyword.strip())
        st.write(f"Found **{len(results)}** result(s).")

        if results:
            pretty_rows = []
            for r in results:
                pretty_rows.append({
                    "Product": str(r["ProductName"]),
                    "Price": f"${float(r['Price']):.2f}",
                    "Vendor": str(r["BusinessName"]),
                    "Market": str(r["MarketName"]),
                    "Location": str(r["Location"])
                })
            st.dataframe(pretty_rows, use_container_width=True)
        else:
            st.info("No products matched your search.")



# PAGE: CUSTOMERS & ORDERS
def page_customers_orders():
    st.header("Customer Orders")

    customers = get_customers()
    if not customers:
        st.info("No customers found.")
        return

    cust_labels = [f"{c['Name']} ({c['Email']})" for c in customers]
    selected_label = st.selectbox("Choose a customer:", cust_labels)
    selected_customer = customers[cust_labels.index(selected_label)]

    st.subheader("Customer Info")
    st.write(f"**Name:** {selected_customer['Name']}")
    st.write(f"**Email:** {selected_customer['Email']}")

    orders = get_orders_for_customer(selected_customer["CustomerID"])
    st.subheader("Orders")

    if not orders:
        st.info("This customer has not placed any orders yet.")
        return

    pretty_orders = []
    order_option_map = {}
    for o in orders:
        order_date = o["OrderDate"].strftime("%Y-%m-%d %H:%M") if o["OrderDate"] else "N/A"
        pickup_date = o["PickupDate"].strftime("%Y-%m-%d %H:%M") if o["PickupDate"] else "N/A"
        label = f"Order {o['OrderID']} ({order_date})"

        order_option_map[label] = o["OrderID"]
        pretty_orders.append({
            "Order": f"#{o['OrderID']}",
            "Order Date": order_date,
            "Pickup Time": pickup_date,
            "Total": f"${float(o['TotalPrice']):.2f}"
        })

    st.dataframe(pretty_orders, use_container_width=True)

    # Let user choose one order to inspect items
    st.subheader("View Order Items")
    selected_order_label = st.selectbox(
        "Select an order:", list(order_option_map.keys())
    )
    selected_order_id = order_option_map[selected_order_label]

    items = get_order_items(selected_order_id)
    if items:
        pretty_items = []
        for i in items:
            pretty_items.append({
                "Item": str(i["ProductName"]),
                "Quantity": str(i["Quantity"]),
                "Price per Item": f"${float(i['Price']):.2f}"
            })
        st.dataframe(pretty_items, use_container_width=True)
    else:
        st.info("No items found for this order.")



# MAIN APP ENTRY POINT
def main():
    st.set_page_config(page_title="MN MarketLink", layout="wide")

    st.title("MN MarketLink")
    st.write("Browse local farmers markets, discover products, and review customer pre-orders.")

    page = st.sidebar.radio(
        "Navigation",
        ["Markets", "Product Search", "Customers & Orders"]
    )

    if page == "Markets":
        page_market_search()
    elif page == "Product Search":
        page_product_search()
    else:
        page_customers_orders()


if __name__ == "__main__":
    main()
