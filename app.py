"""Streamlit UI for the library‑management system"""

from __future__ import annotations

import streamlit as st
from typing import Any, Dict, List, Optional, Tuple

from db import fetchone, fetchall, execute

Row = Dict[str, Any]


def db_get_user(name: str) -> Optional[Row]:
    return fetchone("SELECT * FROM users WHERE name=%s", (name.lower(),))

def db_create_user(name: str, role: str) -> int:
    return execute("INSERT INTO users (name, user_type) VALUES (%s,%s)", (name.lower(), role))


def db_inventory() -> List[Row]:
    return fetchall("SELECT id,title,author,qty FROM books ORDER BY author,title")

def db_book_upsert(title: str, author: str, delta: int) -> None:
    execute(
        """
        INSERT INTO books (title,author,qty)
        VALUES (%s,%s,%s)
        ON DUPLICATE KEY UPDATE qty = GREATEST(qty + VALUES(qty),0)
        """,
        (title.lower(), author.lower(), delta),
    )
    #clean up rows with 0 qty
    execute("DELETE FROM books WHERE qty<=0")


def db_member_loans(user_id: int) -> List[Row]:
    return fetchall(
        """
        SELECT b.id, b.title, b.author, bb.borrowed_at
        FROM borrowed_books bb
        JOIN books b ON b.id = bb.book_id
        WHERE bb.user_id = %s
        ORDER BY bb.borrowed_at DESC
        """,
        (user_id,),
    )

def db_checkout(user_id: int, book_id: int) -> Optional[str]:
    book: Optional[Row] = fetchone("SELECT qty,title,author FROM books WHERE id=%s", (book_id,))
    if not book:
        return "Book not found."
    if book["qty"] == 0:
        return "No available copies."
    # check loan limit (5)
    loans = db_member_loans(user_id)
    if len(loans) >= 5:
        return "You already have 5 books checked out."

    execute("UPDATE books SET qty = qty - 1 WHERE id=%s", (book_id,))
    execute("INSERT INTO borrowed_books (user_id, book_id) VALUES (%s,%s)", (user_id, book_id))
    return None  # success

def db_return(user_id: int, book_id: int) -> Optional[str]:
    loan = fetchone(
        "SELECT id FROM borrowed_books WHERE user_id=%s AND book_id=%s LIMIT 1",
        (user_id, book_id),
    )
    if not loan:
        return "You did not borrow this book."
    execute("DELETE FROM borrowed_books WHERE id=%s", (loan["id"],))
    execute("UPDATE books SET qty = qty + 1 WHERE id=%s", (book_id,))
    return None  # success

# Streamlit app
st.set_page_config(page_title="Library System", page_icon="📚", layout="wide")

if "user" not in st.session_state:
    st.session_state.user = None  # type: ignore[attr-defined]

#sidebar – sign in / sign up / logout
with st.sidebar:
    st.title("📚 Library")
    if st.session_state.user is None:
        st.subheader("Login or Sign‑up")
        form_mode = st.radio("I am a …", ["Member", "Librarian"], horizontal=True)
        name_input = st.text_input("Full Name")
        if st.button("Sign‑in / Sign‑up", disabled=not name_input):
            row = db_get_user(name_input)
            role_lower = form_mode.lower()
            if row is None:
                # create
                db_create_user(name_input, role_lower)
                row = db_get_user(name_input)
                st.success("Account created.")
            if row["user_type"] != role_lower:
                st.error("Role mismatch for this name. Try the other option.")
            else:
                st.session_state.user = row
                st.experimental_rerun()
    else:
        st.markdown(f"**Logged in as:** {st.session_state.user['name'].title()}  ")
        st.markdown(f"**Role:** {st.session_state.user['user_type'].title()}")
        if st.button("Logout"):
            st.session_state.user = None
            st.experimental_rerun()

user = st.session_state.user 

# Main area – dashboards
if user is None:
    st.header("Welcome to the Public Library")
    st.write("Use the sidebar to log in or create an account.")
    st.stop()

role = user["user_type"]  # "member" | "librarian"

st.header("Library Inventory")
inv_rows = db_inventory()
inv_df = [{"ID": r["id"], "Title": r["title"].title(), "Author": r["author"].title(), "Qty": r["qty"]} for r in inv_rows]
st.dataframe(inv_df, hide_index=True)


#member dashboard
if role == "member":
    st.subheader("My Borrowed Books")
    loans = db_member_loans(user["id"])
    if loans:
        loan_df = [{"ID": r["id"], "Title": r["title"].title(), "Author": r["author"].title(), "Borrowed": r["borrowed_at"].strftime("%Y-%m-%d")} for r in loans]
        st.dataframe(loan_df, hide_index=True)
    else:
        st.info("No books borrowed yet.")

    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Checkout a Book")
        checkout_selection = {f"{r['title'].title()} – {r['author'].title()} (qty: {r['qty']})": r["id"] for r in inv_rows if r["qty"] > 0}
        sel_label = st.selectbox(
            "Choose a book", list(checkout_selection.keys()),
            index=None, placeholder="Select…"
        )
        if st.button("Checkout", disabled=sel_label is None):
            err = db_checkout(user["id"], checkout_selection[sel_label])  # type: ignore[arg-type]
            if err:
                st.error(err)
            else:
                st.success("Book checked out! 📖")
                st.experimental_rerun()

    with col2:
        st.subheader("Return a Book")
        loan_selection = {f"{r['title'].title()} – {r['author'].title()}": r["id"] for r in loans}
        loan_label = st.selectbox("Borrowed book", list(loan_selection.keys()), index=None, placeholder="Select…")
        if st.button("Return", disabled=loan_label is None):
            err = db_return(user["id"], loan_selection[loan_label])  # type: ignore[arg-type]
            if err:
                st.error(err)
            else:
                st.success("Returned. Thank you!")
                st.experimental_rerun()

# librarian dashboard
else: 
    st.subheader("Maintenance")
    tabs = st.tabs(["Add New", "Add Copies", "Remove Copies"])

    with tabs[0]:
        st.write("Add a brand‑new title")
        new_title = st.text_input("Title", key="new_title")
        new_author = st.text_input("Author", key="new_author")
        if st.button("Add book", key="add_new", disabled=not (new_title and new_author)):
            db_book_upsert(new_title, new_author, 1)
            st.success("Added.")
            st.experimental_rerun()

    with tabs[1]:
        add_sel = {f"{r['title'].title()} – {r['author'].title()}": (r["title"], r["author"]) for r in inv_rows}
        sel = st.selectbox("Choose title", list(add_sel.keys()), index=None, placeholder="Select…")
        qty = st.number_input("Copies to add", min_value=1, step=1, value=1)
        if st.button("Add copies", disabled=sel is None):
            t, a = add_sel[sel]
            db_book_upsert(t, a, int(qty))
            st.success("Copies added.")
            st.experimental_rerun()

    with tabs[2]:
        rem_sel = {f"{r['title'].title()} – {r['author'].title()} (qty: {r['qty']})": (r["title"], r["author"], r["qty"]) for r in inv_rows}
        sel = st.selectbox("Choose title", list(rem_sel.keys()), index=None, placeholder="Select…")
        if sel:
            _, _, max_qty = rem_sel[sel]
            qty_rm = st.number_input("Copies to remove", min_value=1, max_value=max_qty, step=1,value=1)
            if st.button("Remove copies"):
                t, a, _ = rem_sel[sel]
                db_book_upsert(t, a, -int(qty_rm))
                st.success("Removed copies.")
                st.experimental_rerun()
