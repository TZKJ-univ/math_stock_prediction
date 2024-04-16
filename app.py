import mysql.connector
import pandas as pd
import numpy as np
import datetime
import yfinance as yf

# MySQLに接続
mydb = mysql.connector.connect(
    host='127.0.0.1',
    user='root',
    password='Tozawa311@',
    database='stock_predictions'
)

# カーソルを取得
mycursor = mydb.cursor()

# ターゲットを指定
ticker = input("Enter the ticker of the stock you want to predict: ")

# データを収集
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=3650)  # 最新の10年間のデータを取得
data = yf.download(ticker, start=start_date, end=end_date, interval='1mo')  # データを取得
df = data
df = df.drop("Volume", axis=1)

# 年次データに変換
df = df.resample('Y').last()  # 'YE' ではなく 'Y' を使用

# 最新の10年間のデータを使用して回帰モデルを構築
coefficients = np.polyfit(np.arange(len(df)), df['Close'], 3)
p = np.poly1d(coefficients)

# 10年後のインデックスを取得
future_index = len(df) + 1

# 1年後の株価を予測
predicted_price = p(future_index)
print("Predicted price for 1 year later:", predicted_price)

# 最新価格を取得
latest_price = df['Close'].iloc[-1]

# 差額を計算
price_difference = predicted_price - latest_price

# MySQLにデータを書き込む
sql = "INSERT INTO predictions (ticker, predicted_price, latest_price, price_difference) VALUES (%s, %s, %s, %s)"
val = (ticker, float(predicted_price), float(latest_price), float(price_difference))  # float型に変換
mycursor.execute(sql, val)

# データベースへの変更を確定
mydb.commit()

# 最も古いIDの行を削除
delete_sql = "DELETE FROM predictions ORDER BY id ASC LIMIT 1"
mycursor.execute(delete_sql)
mydb.commit()

# データベース接続を閉じる
mydb.close()
