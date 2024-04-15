import sqlite3

# 连接到 SQLite3 数据库
conn = sqlite3.connect('test.db')
cursor = conn.cursor()
cursor.execute('DROP TABLE IF EXISTS table2')
# 创建表
cursor.execute('''CREATE TABLE IF NOT EXISTS table2
                  (
                    name TEXT,
                    gender TEXT,
                    id INTEGER,
                    exam_address TEXT,
                    exam_date DATE,
                    number INTEGER,
                    token TEXT,
                    img_url TEXT,
                    passed INTEGER default 1
                  )''')

# 插入数据
cursor.execute('''INSERT INTO table2 (name, gender, id,exam_address, exam_date, number, token,img_url)
                  VALUES (?, ?, ?, ?, ?,?,?,?)''', ('王三', '男', 1,'杭州', '2023-04-19', 1, '123123',"http://picsum.photos/500"))

# 提交事务
conn.commit()

# 关闭数据库连接
conn.close()
