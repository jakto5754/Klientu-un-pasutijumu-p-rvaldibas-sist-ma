from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
app = Flask(__name__)
app.secret_key = "supersecretkey"

def get_db_connection():
	return sqlite3.connect("projektsdatabase.db", check_same_thread=False)

def execute_query(query, params=(), fetch=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, params)

    if fetch:
        data = cursor.fetchall()
    else:
        data=None

    conn.commit()
    conn.close()
    return data

@app.route("/")
def index():
	return render_template("index.html")

@app.route("/customers")
def customers():
    sort_by = request.args.get("sort_by")
    order = request.args.get("order")
    if sort_by not in ["Customer_ID", "Full_Name", "Email"]:
        sort_by = "Customer_ID"
    if order not in ["ASC", "DESC"]:
        order = "ASC"
    query = f"""
    SELECT Customer_ID, Full_Name, Email
    FROM Customers
    ORDER BY {sort_by} {order}
    """
    customers = execute_query(query, fetch=True)
    return render_template("customers.html", customers=customers)

@app.route("/add_customer", methods=["GET", "POST"])
def add_customer():
    if request.method == "POST":
        fullname = request.form["fullname"]
        email = request.form["email"]
        execute_query(
        "INSERT INTO Customers (Full_Name, Email) VALUES (?, ?)",
        (fullname, email)
)
        return redirect(url_for("customers"))
    return render_template("add_customer.html")

@app.route("/remove_customer", methods=["GET", "POST"])
def remove_customer():
    if request.method == "POST":
        customer_id = request.form.get("customer_id")
        execute_query(
            "DELETE FROM Customers WHERE Customer_ID = ?",
            (customer_id,)
        )
        return redirect(url_for("customers"))
    customers = execute_query(
        "SELECT Customer_ID, Full_Name FROM Customers",
        fetch=True
    )
    return render_template("remove_customer.html", customers=customers)

@app.route("/edit_customer")
def edit_customer():
    customers = execute_query(
        "SELECT Customer_ID, Full_Name FROM Customers",
        fetch=True
    )
    customer_id = request.args.get("customer_id")
    customer = None
    if customer_id:
        result = execute_query(
            "SELECT Customer_ID, Full_Name, Email FROM Customers WHERE Customer_ID = ?",
            (customer_id,),
            fetch=True
        )
        if result:
            customer = result[0]
    return render_template(
        "edit_customer.html",
        customers=customers,
        customer=customer
    )

@app.route("/update_customer", methods=["POST"])
def update_customer():
    execute_query(
        """
        UPDATE Customers
        SET Full_Name = ?, Email = ?
        WHERE Customer_ID = ?
        """,
        (
            request.form.get("fullname"),
            request.form.get("email"),
            request.form.get("customer_id")
        )
    )
    return redirect(url_for("customers"))

@app.route("/orders")
def orders():
    sort_by = request.args.get("sort_by")
    order = request.args.get("order")
    if sort_by not in ["Order_ID", "Date", "Time", "Customer_ID"]:
        sort_by = "Order_ID"
    if order not in ["ASC", "DESC"]:
        order = "ASC"
    query = f"""
    SELECT Order_ID, Date, Time, Customer_ID
    FROM Orders
    ORDER BY {sort_by} {order}
    """
    orders = execute_query(query, fetch=True)
    return render_template("orders.html", orders=orders)

@app.route("/add_order", methods=["GET", "POST"])
def add_order():
    customers = execute_query(
        "SELECT Customer_ID, Full_Name FROM Customers",
        fetch=True
    )
    if request.method == "POST":
        execute_query(
            """
            INSERT INTO Orders (Date, Time, Customer_ID)
            VALUES (?, ?, ?)
            """,
            (
                request.form.get("date"),
                request.form.get("time"),
                request.form.get("customer_id")
            )
        )
        return redirect(url_for("orders"))
    return render_template("add_order.html", customers=customers)

@app.route("/add_order_detail", methods=["GET", "POST"])
def add_order_detail():
    orders = execute_query(
        "SELECT Order_ID FROM Orders",
        fetch=True
    )
    products = execute_query(
        "SELECT Product_ID, Name FROM Products",
        fetch=True
    )
    if request.method == "POST":
        execute_query(
            """
            INSERT INTO Order_Details (Order_ID, Product_ID, Quantity)
            VALUES (?, ?, ?)
            """,
            (
                request.form.get("order_id"),
                request.form.get("product_id"),
                request.form.get("quantity")
            )
        )
        return redirect(url_for("orders"))
    return render_template(
        "add_order_detail.html",
        orders=orders,
        products=products
    )

@app.route("/remove_order", methods=["GET", "POST"])
def remove_order():
    if request.method == "POST":
        order_id = request.form.get("order_id")
        execute_query("DELETE FROM Order_Details WHERE Order_ID = ?", (order_id,))
        execute_query("DELETE FROM Orders WHERE Order_ID = ?", (order_id,))
        return redirect(url_for("orders"))
    orders = execute_query("SELECT Order_ID FROM Orders", fetch=True)
    return render_template("remove_order.html", orders=orders)

@app.route("/remove_order_detail", methods=["GET", "POST"])
def remove_order_detail():
    if request.method == "POST":
        execute_query(
            "DELETE FROM Order_Details WHERE Order_Detail_ID = ?",
            (request.form.get("detail_id"),)
        )
        return redirect(url_for("orders"))
    details = execute_query(
        """
        SELECT od.Order_Detail_ID, od.Order_ID, p.Name, od.Quantity
        FROM Order_Details od
        JOIN Products p ON od.Product_ID = p.Product_ID
        """,
        fetch=True
    )
    return render_template("remove_order_detail.html", details=details)

@app.route("/edit_order")
def edit_order():
    orders = execute_query(
        "SELECT Order_ID FROM Orders",
        fetch=True
    )
    customers = execute_query(
        "SELECT Customer_ID, Full_Name FROM Customers",
        fetch=True
    )
    order = None
    order_id = request.args.get("order_id")
    if order_id:
        result = execute_query(
            """
            SELECT Order_ID, Date, Time, Customer_ID
            FROM Orders
            WHERE Order_ID = ?
            """,
            (order_id,),
            fetch=True
        )
        if result:
            order = result[0]
            date_value = order[1]
            if "/" in date_value:
                d, m, y = date_value.split("/")
                date_value = f"{y}-{m}-{d}"
            order = (order[0], date_value, order[2], order[3])
    return render_template(
        "edit_order.html",
        orders=orders,
        order=order,
        customers=customers
    )

@app.route("/update_order", methods=["POST"])
def update_order():
    execute_query(
        """
        UPDATE Orders
        SET Date = ?, Time = ?, Customer_ID = ?
        WHERE Order_ID = ?
        """,
        (
            request.form.get("date"),
            request.form.get("time"),
            request.form.get("customer_id"),
            request.form.get("order_id")
        )
    )
    return redirect(url_for("orders"))

@app.route("/edit_order_detail")
def edit_order_detail():
    details = execute_query(
        """
        SELECT od.Order_Detail_ID, od.Order_ID, p.Name, od.Quantity
        FROM Order_Details od
        JOIN Products p ON od.Product_ID = p.Product_ID
        """,
        fetch=True
    )
    products = execute_query(
        "SELECT Product_ID, Name FROM Products",
        fetch=True
    )
    detail = None
    detail_id = request.args.get("detail_id")
    if detail_id:
        result = execute_query(
            """
            SELECT Order_Detail_ID, Order_ID, Product_ID, Quantity
            FROM Order_Details
            WHERE Order_Detail_ID = ?
            """,
            (detail_id,),
            fetch=True
        )

        if result:
            detail = result[0]
    return render_template(
        "edit_order_detail.html",
        details=details,
        detail=detail,
        products=products
    )

@app.route("/update_order_detail", methods=["POST"])
def update_order_detail():
    execute_query(
        """
        UPDATE Order_Details
        SET Product_ID = ?, Quantity = ?
        WHERE Order_Detail_ID = ?
        """,
        (
            request.form.get("product_id"),
            request.form.get("quantity"),
            request.form.get("detail_id")
        )
    )
    return redirect(url_for("orders"))

@app.route("/products")
def products():
    sort_by = request.args.get("sort_by")
    order = request.args.get("order")
    if sort_by not in ["Product_ID", "Name", "Price", "Stock", "Supplier_ID"]:
        sort_by = "Product_ID"
    if order not in ["ASC", "DESC"]:
        order = "ASC"
    query = f"""
    SELECT Product_ID, Name, Price, Stock, Supplier_ID
    FROM Products
    ORDER BY {sort_by} {order}
    """
    products = execute_query(query, fetch=True)
    return render_template("products.html", products=products)

@app.route("/add_product", methods=["GET", "POST"])
def add_product():
    suppliers = execute_query(
        "SELECT Supplier_ID, Company_Name FROM Suppliers",
        fetch=True
    )
    if request.method == "POST":
        execute_query(
            """
            INSERT INTO Products (Name, Price, Stock, Supplier_ID)
            VALUES (?, ?, ?, ?)
            """,
            (
                request.form.get("name"),
                request.form.get("price"),
                request.form.get("stock"),
                request.form.get("supplier_id")
            )
        )
        return redirect(url_for("products"))
    return render_template("add_product.html", suppliers=suppliers)

@app.route("/remove_product", methods=["GET", "POST"])
def remove_product():
    if request.method == "POST":
        execute_query(
            "DELETE FROM Products WHERE Product_ID = ?",
            (request.form.get("product_id"),)
        )
        return redirect(url_for("products"))
    products = execute_query(
        "SELECT Product_ID, Name FROM Products",
        fetch=True
    )
    return render_template("remove_product.html", products=products)

@app.route("/edit_product")
def edit_product():
    products = execute_query(
        "SELECT Product_ID, Name FROM Products",
        fetch=True
    )
    suppliers = execute_query(
        "SELECT Supplier_ID, Company_Name FROM Suppliers",
        fetch=True
    )
    product = None
    product_id = request.args.get("product_id")
    if product_id:
        result = execute_query(
            """
            SELECT Product_ID, Name, Price, Stock, Supplier_ID
            FROM Products
            WHERE Product_ID = ?
            """,
            (product_id,),
            fetch=True
        )
        if result:
            product = result[0]
    return render_template(
        "edit_product.html",
        products=products,
        product=product,
        suppliers=suppliers
    )

@app.route("/update_product", methods=["POST"])
def update_product():
    execute_query(
        """
        UPDATE Products
        SET Name = ?, Price = ?, Stock = ?, Supplier_ID = ?
        WHERE Product_ID = ?
        """,
        (
            request.form.get("name"),
            request.form.get("price"),
            request.form.get("stock"),
            request.form.get("supplier_id"),
            request.form.get("product_id")
        )
    )
    return redirect(url_for("products"))

@app.route("/suppliers")
def suppliers():
    sort_by = request.args.get("sort_by")
    order = request.args.get("order")
    if sort_by not in ["Supplier_ID", "Company_Name", "Email"]:
        sort_by = "Supplier_ID"
    if order not in ["ASC", "DESC"]:
        order = "ASC"
    query = f"""
    SELECT Supplier_ID, Company_Name, Email
    FROM Suppliers
    ORDER BY {sort_by} {order}
    """
    suppliers = execute_query(query, fetch=True)
    return render_template("suppliers.html", suppliers=suppliers)

@app.route("/add_supplier", methods=["GET", "POST"])
def add_supplier():
    if request.method == "POST":
        execute_query(
            "INSERT INTO Suppliers (Company_Name, Email) VALUES (?, ?)",
            (
                request.form.get("company_name"),
                request.form.get("email")
            )
        )
        return redirect(url_for("suppliers"))
    return render_template("add_supplier.html")

@app.route("/remove_supplier", methods=["GET", "POST"])
def remove_supplier():
    if request.method == "POST":
        execute_query(
            "DELETE FROM Suppliers WHERE Supplier_ID = ?",
            (request.form.get("supplier_id"),)
        )
        return redirect(url_for("suppliers"))
    suppliers = execute_query(
        "SELECT Supplier_ID, Company_Name FROM Suppliers",
        fetch=True
    )
    return render_template("remove_supplier.html", suppliers=suppliers)

@app.route("/edit_supplier")
def edit_supplier():
    suppliers = execute_query(
        "SELECT Supplier_ID, Company_Name FROM Suppliers",
        fetch=True
    )
    supplier = None
    supplier_id = request.args.get("supplier_id")
    if supplier_id:
        result = execute_query(
            "SELECT Supplier_ID, Company_Name, Email FROM Suppliers WHERE Supplier_ID = ?",
            (supplier_id,),
            fetch=True
        )
        if result:
            supplier = result[0]
    return render_template(
        "edit_supplier.html",
        suppliers=suppliers,
        supplier=supplier
    )

@app.route("/update_supplier", methods=["POST"])
def update_supplier():
    execute_query(
        """
        UPDATE Suppliers
        SET Company_Name = ?, Email = ?
        WHERE Supplier_ID = ?
        """,
        (
            request.form.get("company_name"),
            request.form.get("email"),
            request.form.get("supplier_id")
        )
    )
    return redirect(url_for("suppliers"))

if __name__ == "__main__":
	app.run(debug=True)