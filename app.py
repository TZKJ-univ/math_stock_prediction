import numpy as np
import pandas as pd
import sys
import datetime
import yfinance as yf
import mysql.connector
from sklearn.linear_model import LinearRegression
from sklearn.svm import SVR
from sklearn.ensemble import GradientBoostingRegressor
from statsmodels.tsa.arima.model import ARIMA

# .env ファイルから環境変数を読み込む
from dotenv import load_dotenv
import os
load_dotenv()

# MySQLに接続
mydb = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

# カーソルを取得
mycursor = mydb.cursor()

# コマンドライン引数からティッカーシンボルを取得
ticker = sys.argv[1]
ticker_obj = yf.Ticker(ticker)

# ティッカーから会社名を取得
company_info = ticker_obj.info
company_name = company_info.get('longName', 'Unknown')
company_name = company_name.replace(" Inc.", "").replace(" Corporation", "").replace(" Co.,Ltd.", "").replace(" Holdings", "").replace("'s", "").replace(" Co., Ltd.", "")

# データを収集
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=3650)
data = yf.download(ticker, start=start_date, end=end_date, interval='1mo')
df = data.drop("Volume", axis=1)

# 月次データに変換
df_monthly = df.resample('MS').last()

# 時間インデックスを準備
X = np.arange(len(df_monthly)).reshape(-1, 1)
y = df_monthly['Close'].values

# 各種モデルを訓練
linear_model = LinearRegression()
linear_model.fit(X, y)
linear_prediction = linear_model.predict([[len(df_monthly) + 12]])

svr_model = SVR(kernel='rbf', C=1e3, gamma=0.1)
svr_model.fit(X, y)
svr_prediction = svr_model.predict([[len(df_monthly) + 12]])

gb_model = GradientBoostingRegressor(n_estimators=100)
gb_model.fit(X, y)
gb_prediction = gb_model.predict([[len(df_monthly) + 12]])

# ARIMAモデルの設定と予測
arima_model = ARIMA(y, order=(1,1,1))
arima_fitted = arima_model.fit()
arima_prediction = arima_fitted.forecast(steps=12)[0]

# 最新価格を取得
latest_price = df_monthly['Close'].iloc[-1]

# 同じティッカーのデータを削除する
delete_sql = "DELETE FROM predictions WHERE ticker = %s"
delete_val = (ticker,)
mycursor.execute(delete_sql, delete_val)
mydb.commit()

# MySQLにデータを書き込む
sql = """
INSERT INTO predictions (ticker, company_name, latest_price, linear_predicted_price, svr_predicted_price, gradient_boosting_predicted_price, cubic_predicted_price) 
VALUES (%s, %s, %s, %s, %s, %s, %s)
"""
val = (ticker, company_name, float(latest_price), float(linear_prediction), float(svr_prediction), float(gb_prediction), float(arima_prediction))
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
