# Database connection settings are stored in db_config.py

import streamlit as st
import mysql.connector
from mysql.connector import Error
from db_config import DB_CONFIG   # <-- you provide this locally
from datetime import datetime, date, time


# Allowed pickup times (8:00 am to 1:00 pm)
ALLOWED_PICKUP_TIMES = []
for hour in range(8, 13):
    ALLOWED_PICKUP_TIMES.append(time(hour, 0))
    ALLOWED_PICKUP_TIMES.append(time(hour, 30))
ALLOWED_PICKUP_TIMES.append(time(13, 0))


def time_to_label(t: time) -> str:
    """Format a time like 08:30 as '8:30 AM'."""
    if not hasattr(t, "strftime"):
        return str(t)
    return t.strftime("%I:%M %p").lstrip("0")


st.set_page_config(page_title="MN MarketLink", layout="wide")


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
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT
            Vendor.VendorID,
            Vendor.BusinessName,
            COUNT(Product.ProductID) AS ProductCount,
            VendorMarket.DateAvailable,
            VendorMarket.StartTime,
            VendorMarket.EndTime
        FROM VendorMarket
        JOIN Vendor ON VendorMarket.VendorID = Vendor.VendorID
        LEFT JOIN Product ON Vendor.VendorID = Product.VendorID
        WHERE VendorMarket.MarketID = %s
        GROUP BY
            Vendor.VendorID,
            Vendor.BusinessName,
            VendorMarket.DateAvailable,
            VendorMarket.StartTime,
            VendorMarket.EndTime
        ORDER BY Vendor.BusinessName;
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
        LEFT JOIN VendorMarket ON Vendor.VendorID = VendorMarket.VendorID
        LEFT JOIN Market ON VendorMarket.MarketID = Market.MarketID
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


def create_customer(name: str, email: str):
    """Create a new customer and return (True, new_id) or (False, error_message)."""
    conn = get_connection()
    if not conn:
        return False, "Could not connect to database."

    try:
        query = """
            INSERT INTO Customer (Name, Email)
            VALUES (%s, %s);
        """
        cur = conn.cursor()
        cur.execute(query, (name, email))
        customer_id = cur.lastrowid
        conn.commit()
        cur.close()
        conn.close()
        return True, customer_id
    except Error as e:
        conn.rollback()
        try:
            cur.close()
        except Exception:
            pass
        conn.close()
        return False, str(e)


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


def update_pickup_datetime(order_id: int, pickup_dt: datetime):
    """Update the pickup date/time for an order."""
    conn = get_connection()
    if not conn:
        return False, "Could not connect to database."

    try:
        query = """
            UPDATE Orders
            SET PickupDate = %s
            WHERE OrderID = %s;
        """
        cur = conn.cursor()
        cur.execute(query, (pickup_dt, order_id))
        conn.commit()
        cur.close()
        conn.close()
        return True, None
    except Error as e:
        conn.rollback()
        try:
            cur.close()
        except Exception:
            pass
        conn.close()
        return False, str(e)


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


def get_all_products():
    """Return a list of all products."""
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT ProductID, Name
        FROM Product
        ORDER BY Name;
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_all_vendors():
    """Return all vendors (for pre-order page)."""
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT VendorID, BusinessName
        FROM Vendor
        ORDER BY BusinessName;
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(query)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def get_products_for_vendor(vendor_id: int):
    """Return products for a specific vendor."""
    conn = get_connection()
    if not conn:
        return []

    query = """
        SELECT ProductID, Name, Price
        FROM Product
        WHERE VendorID = %s
        ORDER BY Name;
    """
    cur = conn.cursor(dictionary=True)
    cur.execute(query, (vendor_id,))
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def place_order_transaction(customer_id: int, vendor_id: int, pickup_dt: datetime, cart_items: list):
    """
    Create an order with multiple items using a database transaction.

    - Inserts one row into Orders
    - Inserts multiple rows into OrderItems (one per product in cart)
    - Commits if everything succeeds
    - Rolls back if anything fails
    """
    if not cart_items:
        return False, "Cart is empty."

    conn = get_connection()
    if not conn:
        return False, "Could not connect to database."

    try:
        conn.start_transaction()
        cur = conn.cursor()

        # order total
        total_price = 0.0
        for item in cart_items:
            total_price += float(item["unit_price"]) * int(item["quantity"])

        order_date = datetime.now()

        # insert into Orders
        order_sql = """
            INSERT INTO Orders (CustomerID, VendorID, OrderDate, PickupDate, TotalPrice)
            VALUES (%s, %s, %s, %s, %s);
        """
        cur.execute(order_sql, (customer_id, vendor_id, order_date, pickup_dt, total_price))
        order_id = cur.lastrowid

        # insert into OrderItems
        item_sql = """
            INSERT INTO OrderItems (OrderID, ProductID, Quantity, Price)
            VALUES (%s, %s, %s, %s);
        """
        for item in cart_items:
            cur.execute(
                item_sql,
                (
                    order_id,
                    item["product_id"],
                    int(item["quantity"]),
                    float(item["unit_price"]),
                ),
            )

        conn.commit()
        cur.close()
        conn.close()
        return True, order_id

    except Error as e:
        conn.rollback()
        try:
            cur.close()
        except Exception:
            pass
        conn.close()
        return False, str(e)


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
    

    # vendors time at market
    st.subheader("Vendors at this Market")
    vendors = get_vendors_for_market(selected_market["MarketID"])

    if vendors:
        pretty_rows = []

        # time formatting
        def safe_time_format(t):
            if not t:
                return "N/A"
            if hasattr(t, "strftime"):
                # datetime.time from MySQL
                return time_to_label(t)
            # handle timedelta converted from TIME
            try:
                total_seconds = int(t.total_seconds())
                hrs = (total_seconds // 3600) % 24
                mins = (total_seconds % 3600) // 60
                as_time = time(hrs, mins)
                return time_to_label(as_time)
            except:
                return str(t)

        for v in vendors:
            # handle date safely too
            if v["DateAvailable"] and hasattr(v["DateAvailable"], "strftime"):
                date_avail = v["DateAvailable"].strftime("%Y-%m-%d")
            else:
                date_avail = "N/A"

            pretty_rows.append({
                "Vendor Name": v["BusinessName"],
                # cast to string so Streamlit left-aligns this column
                "Number of Products": str(v["ProductCount"]),
                "Date Available": date_avail,
                "Start Time": safe_time_format(v["StartTime"]),
                "End Time": safe_time_format(v["EndTime"]),
            })

        st.dataframe(pretty_rows, use_container_width=True)

    else:
        st.write("No vendors are currently listed for this market.")


# PRODUCT SEARCH PAGE
def page_product_search():
    st.header("Search for Products")

    all_products = get_all_products()
    product_names_unique = []
    if all_products:
        # build unique product name list for dropdown search
        product_names_unique = sorted({p["Name"] for p in all_products})
    else:
        st.info("No products found in the database.")

    # search by selecting from dropdown
    if product_names_unique:
        st.subheader("Quick Search by Selecting a Product")
        selected_product_name = st.selectbox(
            "Select a product to see where it's available:",
            ["(Choose a product)"] + product_names_unique,
            index=0
        )

        if selected_product_name != "(Choose a product)":
            results = search_products(selected_product_name)
            st.write(f"Results for **{selected_product_name}** ({len(results)} result(s)):")
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
                st.info("No locations found for that product.")

    #pressing Enter in the text box submits the search
    st.subheader("Search by Typing a Product Name")
    with st.form("product_search_form"):
        keyword = st.text_input("Search by product name:", value="Tomato")
        submitted = st.form_submit_button("Search")

    if submitted:
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


# PAGE: MY ORDERS (ONLY CURRENT CUSTOMER)
def page_my_orders():
    st.header("My Orders")

    # only show orders for the current customer (if any)
    customer_id = st.session_state.get("customer_id")
    customer_name = st.session_state.get("customer_name")
    customer_email = st.session_state.get("customer_email")

    if not customer_id:
        st.info("To view orders, please place a pre-order first.")
        return

    st.subheader("Customer Info")
    st.write(f"**Name:** {customer_name}")
    st.write(f"**Email:** {customer_email}")

    orders = get_orders_for_customer(customer_id)
    st.subheader("Orders")

    if not orders:
        st.info("You have not placed any orders yet.")
        return

    pretty_orders = []
    order_option_map = {}
    for o in orders:
        order_date = o["OrderDate"].strftime("%Y-%m-%d %H:%M") if o["OrderDate"] else "N/A"
        pickup_date = o["PickupDate"].strftime("%Y-%m-%d %H:%M") if o["PickupDate"] else "N/A"
        label = f"Order {o['OrderID']} ({order_date})"

        order_option_map[label] = o
        pretty_orders.append({
            "Order": f"#{o['OrderID']}",
            "Order Date": order_date,
            "Pickup Time": pickup_date,
            "Total": f"${float(o['TotalPrice']):.2f}"
        })

    st.dataframe(pretty_orders, use_container_width=True)

    # choose one order to view/edit
    st.subheader("View or Edit an Order")
    selected_order_label = st.selectbox(
        "Select an order:", list(order_option_map.keys())
    )
    selected_order = order_option_map[selected_order_label]
    selected_order_id = selected_order["OrderID"]

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

    # allow the user to update pickup date/time for this order
    st.subheader("Update Pickup Time")
    current_pickup = selected_order["PickupDate"]
    if current_pickup:
        default_date = current_pickup.date()
        default_time = current_pickup.time()
    else:
        default_date = date.today()
        default_time = time(11, 0)

    if default_time not in ALLOWED_PICKUP_TIMES:
        default_time = time(11, 0)

    time_labels = [time_to_label(t) for t in ALLOWED_PICKUP_TIMES]
    default_index = ALLOWED_PICKUP_TIMES.index(default_time)
    new_date = st.date_input("New pickup date:", value=default_date)
    selected_time_label = st.selectbox("New pickup time:", time_labels, index=default_index)
    new_time = ALLOWED_PICKUP_TIMES[time_labels.index(selected_time_label)]
    new_pickup_dt = datetime.combine(new_date, new_time)

    if st.button("Save Pickup Time"):
        ok, err = update_pickup_datetime(selected_order_id, new_pickup_dt)
        if ok:
            st.success("Pickup time updated successfully.")
        else:
            st.error(f"Could not update pickup time: {err}")


# PAGE: PLACE PRE-ORDER (MULTIPLE PRODUCTS, TRANSACTION, CUSTOMER-FACING)
def page_place_preorder():
    st.header("Place a Pre-Order")

    # initialize cart in session state
    if "cart" not in st.session_state:
        st.session_state.cart = []

    vendors = get_all_vendors()
    if not vendors:
        st.info("Need at least one vendor in the database to place orders.")
        return

    # customer info
    st.subheader("Your Information")
    default_name = st.session_state.get("customer_name", "")
    default_email = st.session_state.get("customer_email", "")
    name = st.text_input("Your Name", value=default_name)
    email = st.text_input("Your Email", value=default_email)

    # select vendor
    st.subheader("Vendor & Products")
    vendor_labels = [v["BusinessName"] for v in vendors]
    selected_vendor_label = st.selectbox("Select vendor:", vendor_labels)
    selected_vendor = vendors[vendor_labels.index(selected_vendor_label)]

    # products for vendor
    products = get_products_for_vendor(selected_vendor["VendorID"])
    if not products:
        st.warning("This vendor has no products listed.")
        return

    product_labels = [f"{p['Name']} (${float(p['Price']):.2f})" for p in products]
    selected_product_label = st.selectbox("Select product to add:", product_labels)
    selected_product = products[product_labels.index(selected_product_label)]

    quantity = st.number_input("Quantity:", min_value=1, value=1, step=1)

    if st.button("Add to Cart"):
        found = False
        for item in st.session_state.cart:
            if item["product_id"] == selected_product["ProductID"]:
                item["quantity"] += int(quantity)
                found = True
                break
        if not found:
            st.session_state.cart.append({
                "product_id": selected_product["ProductID"],
                "product_name": selected_product["Name"],
                "unit_price": float(selected_product["Price"]),
                "quantity": int(quantity),
            })
        st.success(f"Added {quantity} x {selected_product['Name']} to cart.")

    st.subheader("Current Cart")
    if st.session_state.cart:
        cart_pretty = []
        total = 0.0
        for item in st.session_state.cart:
            line_total = float(item["unit_price"]) * int(item["quantity"])
            total += line_total
            cart_pretty.append({
                "Item": item["product_name"],
                "Quantity": str(item["quantity"]),
                "Unit Price": f"${float(item['unit_price']):.2f}",
                "Line Total": f"${line_total:.2f}",
            })
        st.dataframe(cart_pretty, use_container_width=True)
        st.write(f"**Order Total:** ${total:.2f}")
    else:
        st.info("Cart is currently empty.")

    # pickup date/time
    st.subheader("Pickup Details")
    pickup_date = st.date_input("Pickup date:", value=date.today())
    time_labels = [time_to_label(t) for t in ALLOWED_PICKUP_TIMES]
    default_pickup_index = ALLOWED_PICKUP_TIMES.index(time(11, 0))
    selected_time_label = st.selectbox("Pickup time:", time_labels, index=default_pickup_index)
    pickup_time_val = ALLOWED_PICKUP_TIMES[time_labels.index(selected_time_label)]

    # place order
    if st.button("Place Order"):
        if not st.session_state.cart:
            st.warning("Cart is empty. Add at least one product before placing an order.")
            return

        if not name.strip() or not email.strip():
            st.warning("Please enter your name and email before placing an order.")
            return

        pickup_dt = datetime.combine(pickup_date, pickup_time_val)

        # if we don't already have a customer in this session, create one
        if not st.session_state.get("customer_id"):
            ok, result = create_customer(name.strip(), email.strip())
            if not ok:
                st.error(f"Could not create customer: {result}")
                return
            st.session_state["customer_id"] = result
            st.session_state["customer_name"] = name.strip()
            st.session_state["customer_email"] = email.strip()
        else:
            # reuse existing session customer_id, update name/email in session
            st.session_state["customer_name"] = name.strip()
            st.session_state["customer_email"] = email.strip()

        customer_id = st.session_state["customer_id"]

        success, info = place_order_transaction(
            customer_id=customer_id,
            vendor_id=selected_vendor["VendorID"],
            pickup_dt=pickup_dt,
            cart_items=st.session_state.cart,
        )
        if success:
            order_id = info
            st.success(f"Order placed successfully! Your Order ID is {order_id}.")
            st.session_state.cart = []
        else:
            st.error(f"Failed to place order: {info}")


# MAIN APP ENTRY POINT
def main():
    st.title("MN MarketLink")
    st.write("Browse local farmers markets, discover products, search across all markets, and place pre-orders.")

    page = st.sidebar.radio(
        "Navigation",
        ["Markets", "Product Search", "My Orders", "Place Pre-Order"]
    )

    if page == "Markets":
        page_market_search()
    elif page == "Product Search":
        page_product_search()
    elif page == "My Orders":
        page_my_orders()
    else:
        page_place_preorder()


if __name__ == "__main__":
    main()
