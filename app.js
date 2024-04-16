const express = require('express');
const mysql = require('mysql');
const path = require('path');

const app = express();

// MySQL接続設定
const mydb = mysql.createConnection({
    host: '127.0.0.1',
    user: 'root',
    password: 'Tozawa311@',
    database: 'stock_predictions'
});

// MySQL接続
mydb.connect((err) => {
    if (err) throw err;
    console.log('Connected to MySQL');
});

// EJSをテンプレートエンジンとして設定し、viewsディレクトリの場所を指定
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'public', 'views'));

// ルートでのクエリ処理
app.get('/', (req, res) => {
    // クエリ処理
    mydb.query('SELECT * FROM predictions', (err, rows) => {
        if (err) throw err;
        res.render('index', { predictions: rows });
    });
});

// サーバー起動
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
