import mysql.connector
import pandas as pd
import numpy as np
import datetime
import yfinance as yf
import sys
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline

# MySQLに接続
mydb = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='Tozawa311@',
    database='stock_predictions'
)

# カーソルを取得
mycursor = mydb.cursor()

# コマンドライン引数からティッカーシンボルを取得
ticker = sys.argv[1]

# データを収集
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=3650)  # 最新の10年間のデータを取得
data = yf.download(ticker, start=start_date, end=end_date, interval='1mo')
df = data.drop("Volume", axis=1)

# 月次データに変換
df_monthly = df.resample('M').last()

# 時間インデックスを準備
X = np.arange(len(df_monthly)).reshape(-1, 1)  # 時間を独立変数として整形
y = df_monthly['Close'].values  # 終値を従属変数として使用

# 線形、2次、3次回帰モデルをフィッティング
linear_model = LinearRegression()
linear_model.fit(X, y)
linear_prediction = linear_model.predict([[len(df_monthly) + 12]])[0]

quad_model = make_pipeline(PolynomialFeatures(2), LinearRegression())
quad_model.fit(X, y)
quad_prediction = quad_model.predict([[len(df_monthly) + 12]])[0]

cubic_model = make_pipeline(PolynomialFeatures(3), LinearRegression())
cubic_model.fit(X, y)
cubic_prediction = cubic_model.predict([[len(df_monthly) + 12]])[0]

# 最新価格を取得
latest_price = df_monthly['Close'].iloc[-1]

# MySQLにデータを書き込む
sql = """
INSERT INTO predictions (ticker, latest_price, linear_predicted_price, quad_predicted_price, cubic_predicted_price) 
VALUES (%s, %s, %s, %s, %s)
"""
val = (ticker, float(latest_price), float(linear_prediction), float(quad_prediction), float(cubic_prediction))
mycursor.execute(sql, val)
mydb.commit()

# データベース内の行数を確認し、10行を超えていたら最も古い行を削除
mycursor.execute("SELECT COUNT(*) FROM predictions")
row_count = mycursor.fetchone()[0]

if row_count > 10:
    mycursor.execute("DELETE FROM predictions ORDER BY id ASC LIMIT 1")
    mydb.commit()

# データベース接続を閉じる
mydb.close()
