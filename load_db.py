import pymysql
conn = pymysql.connect(host="localhost", user="root", password="NewPassword")
cur = conn.cursor()
cur.execute("ALTER USER 'root'@'localhost' IDENTIFIED BY 'MyNewOne123'")
conn.commit()
conn.close()
print("changed")