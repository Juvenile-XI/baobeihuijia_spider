from PySide2.QtWidgets import QApplication, QWidget, QTableWidgetItem
from PySide2.QtGui import QIcon
from PySide2.QtCore import *
from mainwin import *
from sqlwin import *
import requests
import sqlite3
import json
import time
import ctypes  # 修复任务栏图标设置失效问题

ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")


class sqlshow(QWidget, Ui_Widget):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        sql = 'select id,姓名,性别,年龄,生日,失踪时间,失踪类型,失踪地址,注册时间 from 宝贝回家 '
        data = c.execute(sql)
        n = 0
        for i in data:
            self.tableWidget.insertRow(n)
            m = 0
            for j in i:
                item = QTableWidgetItem()
                item.setText(str(j))
                item.setTextAlignment(Qt.AlignCenter)  # 使文字居中
                self.tableWidget.setItem(n, m, item)
                item.setFlags(Qt.ItemIsEnabled)
                m += 1
            n += 1


class Mainwindow(QWidget):
    def __init__(self):
        super().__init__()
        self.ui = Ui_Form()
        self.ui.setupUi(self)
        self.ui.pushButton_2.clicked.connect(self.runing)
        self.ui.progressBar.setValue(0)
        self.ui.pushButton.clicked.connect(self.sqllite)

    def sqllite(self):
        self.sqll = sqlshow()
        self.sqll.showMaximized()

    def runing(self):
        self.thread_1 = Worker()
        self.thread_1.begin = int(self.ui.lineEdit_2.text())
        self.thread_1.end = int(self.ui.lineEdit_3.text()) + 1
        x = self.ui.comboBox.currentText()
        self.thread_1.index = self.indexs(x)
        self.thread_1.t = self.ui.lineEdit_4.text()
        self.ui.progressBar.setRange(0, self.thread_1.end - self.thread_1.begin)
        self.ui.textBrowser.append(
            '开始爬取%s的%s到%s页间隔%s秒' % (x, self.thread_1.begin, self.thread_1.end, self.thread_1.t))
        self.thread_1.text.connect(self.uptextBrowser)
        self.thread_1.Value.connect(self.upprogressBar)
        self.thread_1.start()

    def indexs(self, s):
        if s == '全部':
            return 0
        elif s == '家寻宝贝':
            return 1
        elif s == '宝贝寻家':
            return 2
        elif s == '其他寻人':
            return 4
        elif s == '海外寻亲':
            return 5
        elif s == '烈士寻根':
            return 6

    def upprogressBar(self, i):
        self.ui.progressBar.setValue(i)

    def uptextBrowser(self, i):
        self.ui.textBrowser.append(i)


class Worker(QThread):
    Value = Signal(int)  # 更新进度条
    text = Signal(str)
    begin = 0
    end = 0
    index = 0
    t = 0

    def __init__(self):
        super(Worker, self).__init__()

    def run(self):
        a = time.time()
        wins.ui.pushButton.setEnabled(False)
        wins.ui.pushButton_2.setEnabled(False)
        url = 'https://so.baobeihuijia.com/api/search/contents/actions/list'
        h = {
            'Content-Type': 'application/json;charset=UTF-8',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36',
        }
        for x in range(self.begin, self.end):
            self.text.emit('正在爬取第%s页' % x)
            data = json.loads(
                '{"siteId":1,"channelId":1,"page":' + str(x) + ',"searchType":' + str(
                    self.index) + ',"searchText":"","isAdvanced":false,"checkedStates":[],"sex":"9","isPhotos":false,"isSample":false,"isReport":false,"isDna":false,"birthdayRange":null,"lostdayRange":null,"adddayRange":null,"lostAddressCode":null,"liveAddressCode":null,"lostAddress":null,"liveAddress":null,"lowerHeight":0,"higherHeight":0}')
            d = json.dumps(data)
            try:
                request = requests.post(url, headers=h, data=d)
                req = request.text
            except:
                wins.ui.textBrowser.append(request.status_code)
                return False
            data = json.loads(req)['pageContents']
            for i in data:
                if i['sex']:
                    i['sex'] = '男'
                else:
                    i['sex'] = '女'
                if i['birthDay'].split('-')[0] != '':
                    i['age'] = 2022 - int(i['birthDay'].split('-')[0])
                else:
                    i['age'] = ''
                sql = '''
                            insert into 宝贝回家 (id,姓名,性别,年龄,生日,失踪类型,失踪地址,失踪时间,注册时间)
                                values('{0}','{1}','{2}','{3}','{4}','{5}','{6}','{7}','{8}')
                        '''.format(i['publishId'], i['name'], i['sex'], i['age'], i['birthDay'], i['lostPass'],
                                   i['lostAddress'], i['lostDay'],
                                   i['addDate'])
                c.execute(sql)
                conn.commit()
            time.sleep(float(self.t))
            self.Value.emit(x)
        self.text.emit('本次爬取共用时%s秒' % (time.time() - a))
        wins.ui.pushButton.setEnabled(True)
        wins.ui.pushButton_2.setEnabled(True)


app = QApplication([])
app.setWindowIcon(QIcon("./img/hj.ico"))
wins = Mainwindow()
wins.show()
wins.ui.textBrowser.append('正在创建数据库....')
try:
    # check_same_thread=False 允许数据库被子线程使用
    conn = sqlite3.connect('bbhj.sql', check_same_thread=False)
    c = conn.cursor()
    # insert into 宝贝回家 #添加数据
    # create table 宝贝回家 #创建表
    sql = '''
                    create table 宝贝回家(id int,姓名 varchar,性别 char,年龄 int,生日 varchar,失踪类型 text,失踪地址 text,失踪时间 varchar,注册时间 varchar);
                 '''
    c.execute(sql)
    conn.commit()
except sqlite3.OperationalError:
    wins.ui.textBrowser.append('数据库已存在')
else:
    wins.ui.textBrowser.append('数据库创建成功....')
app.exec_()
