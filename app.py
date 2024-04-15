import sqlite3
from datetime import datetime
from flask import Flask, request,Response, jsonify, g,render_template
from flask_cors import CORS
import qrcode
import base64
from cryptography.fernet import Fernet
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
CORS(app)
DATABASE = 'test.db'

# 设置 JWT Secret Key
app.config['JWT_SECRET_KEY'] = 'admin123'  # 请换成一个安全的密钥
jwt = JWTManager(app)
# 需要修改ip地址
ipaddress = 'localhost:5173'

users = {
    "admin": "123"
}

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username', None)
    password = request.json.get('password', None)

    # 验证用户名和密码
    if username in users and users[username] == password:
        # 创建JWT token
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token), 200
    return jsonify({"msg": "Bad username or password"}), 401

@app.route('/protected', methods=['GET'])
@jwt_required()
def protected():
    # 访问受保护的路由
    current_user = get_jwt_identity()
    return jsonify(logged_in_as=current_user), 200

@app.route('/')
def home():
    return render_template('index.html')


@app.route("/pic/<name>")
def get_frame(name):
    # 图片上传保存的路径
    try:
        with open(r'./pic/{}'.format(name), 'rb') as f:
            image = f.read()
            result = Response(image, mimetype="image/jpg")
            return result
    except BaseException as e:
        return {"code": '503', "data": str(e), "message": "图片不存在"}

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def check_db(name):
    query = "SELECT COUNT(*) FROM table2 WHERE name = ?"
    result = query_db(query, (name,), one=True)
    return result[0] > 0

def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    if one:
        rv = cur.fetchone()
    else:
        rv = cur.fetchall()
    cur.close()
    return rv

def insert_db(name, gender, id, exam_address, exam_date, number, token,img_url):
    if not check_db(name):
        query = '''INSERT INTO table2 (name, gender, id, exam_address, exam_date, number, token,img_url)
                   VALUES (?, ?, ?, ?, ?, ?, ?,?)'''
        args = (name, gender, id, exam_address, exam_date, number, token,img_url)
        query_db(query, args)
        get_db().commit() 
    else:
        return {"code":0,"message": "Error: Name already exists in the database"}

    
# 首页
@app.route('/')
def hello_world():
    return 'hello'

# http://localhost:5173/userinfo1?token=123123
@app.route('/get', methods=["GET"])
def getinfo():
    token = str(request.args.get("token"))
    print("查询token: " + token)

    result = query_db('SELECT * FROM table2 WHERE token=?', (token,), one=True)
    print(result)
    
    if result:
        # 获取当前日期
        today = datetime.now().date()
        # 获取 exam_date
        exam_date = datetime.strptime(result[4], "%Y-%m-%d").date()
        # 计算 exam_date 距离今天的天数
        days_difference = (today - exam_date).days
        
        # 如果距离今天已经过了一年（365天），passed 为 0；否则为 1
        passed = 0 if days_difference > 365 else 1
        
        info = {
            "name": result[0],
            "gender": result[1],
            "id": result[2],
            "exam_address": result[3],
            "exam_date": result[4],
            "passed": passed,
            "number": result[5]
        }
        return jsonify(info)
    else:
        return "未找到对应的人员信息"


@app.route('/insert', methods=["POST"])
def setinfo():
    data = request.get_json()
    print(data)
    name = data['name']
    gender = data['gender']
    id = data['id']
    number = data['number']
    exam_date = data['exam_date']
    exam_address = data['exam_address']
    # 如果有空数据
    if if_NoEmpty_data(data):
    # 如果有违规数据
        if validate_form_data(exam_address):
    # 如果插入失败
            if create_qr_and_insert_db(name,gender,id,number,exam_date,exam_address): 
                return jsonify({'code': 0, 'message': '成功录入'}), 200
        else:
            return jsonify({'code': 1, 'message': '，错误数据'}), 400
    else:
        return jsonify({'code': 2, 'message': '数据不完整'}), 400

def create_qr_and_insert_db(name,gender,id,number,exam_date,exam_address):
    user_info = f"{name},{gender},{id},{number},{exam_date},{exam_address}"
    key = Fernet.generate_key()
    cipher_suite = Fernet(key)
    cipher_text = cipher_suite.encrypt(user_info.encode())
    token = base64.urlsafe_b64encode(cipher_text).decode()
    img_url = f"http://127.0.0.1:5001/pic/{name}.png" 
    insert_db(name,gender,id,exam_address,exam_date,number,token,img_url)

    # 生成二维码图片携带网络地址和token信息
    url = f"http://{ipaddress}/infoView/"
    # url = "http://10.106.200.98:5173/infoView/"
    user_info_with_token = f"{url}?token={token}"
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(user_info_with_token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    img_path = f"pic/{name}.png"
    img.save(img_path)

    return True       


@app.route('/getAll', methods=["GET"])
def getinfo_all():
    results = query_db('SELECT * FROM table2')
    all_data = []
    today = datetime.now().date()

    for row in results:
        exam_date = datetime.strptime(row[4], "%Y-%m-%d").date()
        days_difference = (today - exam_date).days
        passed = 0 if days_difference > 365 else 1

        info = {
            "name": row[0],
            "gender": row[1],
            "id": row[2],
            "exam_address": row[3],
            "exam_date": row[4],
            "number": row[5],
            "img_url":row[7],
            "passed": passed
        }
        all_data.append(info)

    if all_data:
        return jsonify(all_data)
    else:
        return "未找到对应的人员信息", 404  # 返回404状态码表示没有找到资源
    
@app.route('/getInfoByTime', methods=['GET'])
def getinfo_by_time():
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    query = "SELECT * FROM table2 WHERE exam_date BETWEEN ? AND ?"
    results = query_db(query, [start_date, end_date])
    data = []
    for row in results:
        data.append({
            "name": row[0],
            "gender": row[1],
            "id": row[2],
            "exam_address": row[3],
            "exam_date": row[4],
            "number": row[5],
            "passed": 0 if (datetime.now().date() - datetime.strptime(row[4], "%Y-%m-%d").date()).days > 365 else 1
        })
    return jsonify(data)
    
# 删除
@app.route('/delete/<string:name>', methods=['DELETE'])
def delete_record(name):
    # query = 'DELETE FROM table2 WHERE id = ? AND number = ?'
    query = 'DELETE FROM table2 WHERE name = ?' 
    try:
        query_db(query, (name,))
        get_db().commit()
        return jsonify({'code': 0, 'message': 'Record deleted successfully'}), 200
    except Exception as e:
        print(f"Error deleting record: {e}")
        return jsonify({'code': 1, 'message': 'Failed to delete the record'}), 500

# 判断传输的数据是否有问题
def validate_form_data(exam_address):
    if exam_address == '1':
        return False
    else:
        return True
def if_NoEmpty_data(data):
    # Check if any field is empty
    for key in data:
        if not data[key]:  # This will check for empty strings, None, etc.
            return False
    return True


if __name__ == "__main__":
    app.run(host='127.0.0.1', port=5001, debug=True)
