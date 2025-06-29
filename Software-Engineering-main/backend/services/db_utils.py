import pymysql

def get_db():
    return pymysql.connect(
        host='localhost',
        user='root',
        password='123456',
        db='ocean_farm',
        cursorclass=pymysql.cursors.DictCursor
    )
