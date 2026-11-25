import os
import time
import sqlite3
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("expenses.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""CREATE TABLE IF NOT EXISTS expenses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        amount REAL,
        category TEXT,
        date TEXT,
        note TEXT)""")
    conn.commit()
    conn.close()

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        conn = get_db()
        conn.execute(
            "INSERT INTO expenses (amount, category, date, note) VALUES (?, ?, ?, ?)",
            (request.form["amount"], request.form["category"],
             request.form["date"], request.form["note"]))
        conn.commit()
        conn.close()
        return redirect("/expenses")
    return render_template("add.html")

@app.route("/expenses")
def expenses():
    conn = get_db()
    rows = conn.execute("SELECT * FROM expenses ORDER BY date DESC").fetchall()
    conn.close()
    return render_template("expenses.html", expenses=rows)

@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit(id):
    conn = get_db()
    if request.method == "POST":
        conn.execute(
            "UPDATE expenses SET amount=?, category=?, date=?, note=? WHERE id=?",
            (request.form["amount"], request.form["category"],
             request.form["date"], request.form["note"], id))
        conn.commit()
        conn.close()
        return redirect("/expenses")
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (id,)).fetchone()
    conn.close()
    return render_template("edit.html", e=row)

@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect("/expenses")

@app.route("/summary")
def summary():
    conn = get_db()
    df = pd.read_sql_query("SELECT * FROM expenses", conn)
    conn.close()

    if df.empty:
        return render_template("summary.html", total=0, rows=[], has_chart=False, v=0)

    total = float(df["amount"].sum())
    by_cat = df.groupby("category")["amount"].sum().sort_values(ascending=False)
    rows = [(cat, float(amt)) for cat, amt in by_cat.items()]

    os.makedirs("static", exist_ok=True)
    colors = ["#4157d8", "#ff9f43", "#1dd1a1", "#ee5a6f"]
    fig, ax = plt.subplots(figsize=(6, 6))
    wedges, texts, autotexts = ax.pie(
        by_cat,
        labels=by_cat.index,
        autopct="%1.1f%%",
        colors=colors[:len(by_cat)],
        startangle=90,
        pctdistance=0.75,
        wedgeprops={"edgecolor": "white", "linewidth": 3},
        textprops={"fontsize": 14, "fontweight": "bold"})
    for t in autotexts:
        t.set_color("white")
        t.set_fontsize(13)
        t.set_fontweight("bold")
    ax.set_title("Spending by Category", fontsize=18,
                 fontweight="bold", color="#2d3a8c")
    plt.savefig("static/chart.png", dpi=150, bbox_inches="tight")
    plt.close()

    return render_template("summary.html", total=total, rows=rows,
                           has_chart=True, v=int(time.time()))

init_db()

if __name__ == "__main__":
    app.run(debug=True)