const { exec, spawn } = require('child_process')
const express = require('express')
const app = express()

app.use(express.urlencoded({ extended: false }))
app.set('view engine', 'ejs')

app.get('/', (req, res) => {
    return res.render('index')
})

app.post('/convert', (req, res) => {
    let result = ''
    const { query } = req.body
    const conda_exec = "/Users/khanhnguyen/opt/anaconda3/bin/conda"
    const env_name = "base"
    const file_exec = 'script.py'
        // const cmd = [conda_exec, env_name, 'python', file_exec].join(' ')

    // var process = spawn(cmd, [query]);

    const command = `conda run -n ${env_name} python ${file_exec} "${query.replace(/"/g, '\\"')}"`

    // process.on('close', () => {
    //         result = result.split('Sents/s')
    //         return res.json({
    //             result: result[result.length - 1].trim()
    //         })
    //     })

    const start = performance.now()

    exec(command,
        function(error, stdout, stderr) {
            return res.json({
                error,
                stdout,
                stderr,
                runtime: performance.now() - start
            })
        }
    );
})

app.listen(8080, () => console.log('Online'))