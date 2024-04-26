const express = require('express');
const mysql = require('mysql');
const path = require('path');
const { spawn } = require('child_process');
require('dotenv').config();

const app = express();

// MySQLデータベース接続設定
const mydb = mysql.createConnection({
    host: process.env.DB_HOST,
    user: process.env.DB_USER,
    password: process.env.DB_PASSWORD,
    database: process.env.DB_NAME
});

// MySQLデータベースへの接続
mydb.connect((err) => {
    if (err) throw err;
    console.log('Connected to MySQL');
});

// EJSをテンプレートエンジンとして設定し、viewsディレクトリの場所を指定
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'public', 'views'));

// スタティックファイルのルートを設定
app.use(express.static(path.join(__dirname, 'public')));

// ルートディレクトリでのデータベースクエリ処理
app.get('/', (req, res) => {
    mydb.query('SELECT * FROM predictions ORDER BY id DESC', (err, rows) => {
        if (err) {
            console.error(err);
            return res.status(500).send("Error retrieving data from database.");
        }
        res.render('index', { predictions: rows });
    });
});

// 詳細ページのルート
app.get('/details/:id', (req, res) => {
    const predictionId = req.params.id;
    mydb.query('SELECT * FROM predictions WHERE id = ?', [predictionId], (err, result) => {
        if (err) {
            console.error(err);
            return res.status(500).send("Error retrieving prediction details.");
        }
        res.render('details', { prediction: result[0] });
    });
});

// Pythonスクリプトを実行するルート
app.get('/run-python', (req, res) => {
    const input = req.query.input;
    const pythonProcess = spawn('python3', ['./app.py', input]);

    let dataToSend = '';
    pythonProcess.stdout.on('data', (data) => {
        dataToSend += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`Child process exited with code ${code}`);
        if (code !== 0) {
            return res.status(500).send("Python script failed to execute.");
        }
        res.send(dataToSend);
    });
});

// サーバー起動
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
