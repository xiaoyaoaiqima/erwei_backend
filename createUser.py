import sqlite3

# 连接到 SQLite3 数据库
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('DROP TABLE IF EXISTS user')
# 创建表
cursor.execute('''CREATE TABLE IF NOT EXISTS user
                  (
                    name TEXT,
                    pwd text
                  )''')

# 插入数据
cursor.execute('''INSERT INTO user (name, pwd)
                  VALUES (?, ?)''', ('admin', '123'))

# 提交事务
conn.commit()

# 关闭数据库连接
conn.close()
