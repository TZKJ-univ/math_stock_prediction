const express = require('express');
const mysql = require('mysql');
const path = require('path');
const { spawn } = require('child_process');

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
    mydb.query('SELECT * FROM predictions ORDER BY id DESC', (err, rows) => {
        if (err) {
            console.error(err);
            return res.status(500).send("Error retrieving data from database.");
        }
        console.log("Rendering index with rows:", rows); // これにより送られるデータを確認
        res.render('index', { predictions: rows });
    });
});


// Pythonスクリプトを実行する新しいルート
app.get('/run-python', (req, res) => {
    const input = req.query.input;  // URLクエリパラメータから入力を受け取る
    const pythonProcess = spawn('python3', ['./app.py', input]);

    let dataToSend = '';
    pythonProcess.stdout.on('data', (data) => {
        dataToSend += data.toString();
    });

    pythonProcess.stderr.on('data', (data) => {
        console.error(`stderr: ${data}`);
    });

    pythonProcess.on('close', (code) => {
        console.log(`child process exited with code ${code}`);
        if (code !== 0) {
            return res.status(500).send("Python script failed to execute.");
        }
        res.send(dataToSend); // ここで一度だけレスポンスを送信
    });
});

// サーバー起動
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
