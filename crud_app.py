import sqlite3

def connect():
    return sqlite3.connect("students.db")

def create_table():
    conn = connect()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students(id INTEGER PRIMARY KEY AUTOINCREMENT, 
        name TEXT NOT NULL, course TEXT NOT NULL) """)
    conn.commit()
    conn.close()

#Create
def add_student(name, course):
    conn = connect()
    cur = conn.cursor()
    cur.execute("INSERT INTO students (name, course) VALUES (?, ?)", (name, course))
    conn.commit()
    conn.close()

# READ
def get_students():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT id, name, course FROM students")
    rows = cur.fetchall()
    conn.close()
    return rows

# Update
def update_student(student_id, name, course):
    conn = connect()
    cur = conn.cursor()
    cur.execute("UPDATE students SET name = ?, course = ? WHERE id = ?",
     (name, course, student_id), )
    conn.commit()
    conn.close()

# DELETE
def delete_student(student_id):
    conn = connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
    conn.commit()
    conn.close()


import tkinter as tk
from tkinter import ttk, messagebox

create_table()

root = tk.Tk()
root.title("Student Management System")

# input fields
tk.Label(root, text="Name").grid(row=0, column=0, padx=5, pady=5)
name_entry = tk.Entry(root)
name_entry.grid(row=0, column=1, padx=5, pady=5)

tk.Label(root, text="Course").grid(row=1, column=0, padx=5, pady=5)
course_entry = tk.Entry(root)
course_entry.grid(row=1, column=1, padx=5, pady=5)

# table that displays the data
columns = ("id", "name", "course")
table = ttk.Treeview(root, columns=columns, show= "headings")
for col in columns:
    table.heading(col, text=col.title())
table.grid(row=3, column=0, columnspan=4, padx=10, pady=10)


def refresh():
    for row in table.get_children():
        table.delete(row)
    for student in get_students():
        table.insert("", tk.END, values=student)

def clear_fields():
    name_entry.delete(0, tk.END)
    course_entry.delete(0, tk.END)

def add():
    name = name_entry.get().strip()
    course = course_entry.get().strip()
    if not name or not course:
        messagebox.showwarning("Missing Data", "Please Fill in both fields.")
        return
    add_student(name, course)
    clear_fields()
    refresh()

def on_select(event):
    selected = table.selection()
    if not selected:
        return
    values = table.item(selected[0])["values"]
    clear_fields()
    name_entry.insert(0, values[1])
    course_entry.insert(0, values[2])

def update():
    selected = table.selection()
    if not selected:
        messagebox.showwarning("no Selecteion", "click a row first")
        return
    student_id = table.item(selected[0])["values"][0]
    update_student(student_id, name_entry.get().strip(), course_entry.get().strip())
    clear_fields()
    refresh()

def delete():
    selected = table.selection()
    if not selected:
        messagebox.showwarning("no selection", "click a rwo first")
        return
    if messagebox.askyesno("confirm", "delete this student?"):
        student_id = table.item(selected[0])["values"][0]
        delete_student(student_id)
        clear_fields()
        refresh()


# buttons
tk.Button(root, text="Add", width=10, command=add).grid(row=2, column=0, pady=5)
tk.Button(root, text="Update", width=10, command=update).grid(row=2, column=1, pady=5)
tk.Button(root, text="Delete", width=10, command=delete).grid(row=2, column=2, pady=5)

table.bind("<<TreeviewSelect>>", on_select)

refresh()
root.mainloop()
    
    